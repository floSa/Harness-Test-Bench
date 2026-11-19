#!/usr/bin/env python3
"""Workflow d'extraction des rapports d'intervention.

Usage: python run.py {entree} {sortie}
Lit tous les PDF de {entree}, ecrit {sortie}/<identifiant>.json (15 cles).
Variables BANC_MODELE_URL / BANC_MODELE / BANC_CLE_MODELE lues a l'execution.
"""
import os, sys, json, glob, re, time, tempfile, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

import pymupdf
from rapidocr_onnxruntime import RapidOCR

KEYS = ["machine", "constructeur", "numero_serie", "site", "reference_rapport",
        "date_intervention", "date_validation", "volume_dose_ml", "volume_nominal_ml",
        "tolerance_ml", "debit_ml_min", "pression_bar", "reference_piece",
        "technicien", "statut"]
NUMKEYS = {"volume_dose_ml", "volume_nominal_ml", "tolerance_ml", "debit_ml_min", "pression_bar"}
NULLISH = {"", "-", "--", "n.c.", "n.c", "nc", "n.m.", "n.m", "nm", "n/a", "na", "none",
           "null", "non communique", "non communiquee", "non mesure", "non mesurable",
           "inconnu", "unknown", "not applicable", "not measured", "illisible", "absent",
           "plaque absente", "plaque illisible", "missing", "illegible", "—", "–", "…"}

# ---------------------------------------------------------------- extraction
_ocr = None


def ocr():
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


def ocr_png(png):
    res, _ = ocr()(png)
    if not res:
        return []
    return [t for _, t, s in res if s > 0.35]


def ocr_xref(doc, xref):
    try:
        pix = pymupdf.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        return ocr_png(pix.tobytes("png"))
    except Exception:
        return []


def extract(pdf):
    doc = pymupdf.open(pdf)
    out = []
    for pno, page in enumerate(doc, 1):
        out.append("\n\n===== PAGE %d =====" % pno)
        text = page.get_text()
        out.append(text)
        for i, info in enumerate(page.get_image_info(xrefs=True)):
            b = info["bbox"]
            lines = ocr_xref(doc, info["xref"])
            if lines:
                out.append("\n[IMAGE p%d #%d bbox=(%.0f,%.0f,%.0f,%.0f) texte OCR:]"
                           % (pno, i + 1, b[0], b[1], b[2], b[3]))
                out.append(" | ".join(lines))
        # page scannee / couche texte pauvre : OCR de la page entiere rastérisée
        if len(text.strip()) < 400:
            try:
                png = page.get_pixmap(dpi=250).tobytes("png")
                lines = ocr_png(png)
                if lines:
                    out.append("\n[PAGE %d OCR PAGE ENTIERE:]" % pno)
                    out.append(" | ".join(lines))
            except Exception:
                pass
    doc.close()
    return "\n".join(out)


# ---------------------------------------------------------- statut (cases)
STATUS_LABELS = [
    ("non_conforme", ["non-conforme", "non conforme", "noncompliant", "non compliant"]),
    ("a_revoir", ["a revoir", "a revu", "to be reviewed", "to be review", "review"]),
    ("conforme", ["conforme", "compliant"]),
]


def norm(s):
    s = str(s).lower()
    for a, b in [("à", "a"), ("é", "e"), ("è", "e"), ("ê", "e"), ("ç", "c"),
                 ("û", "u"), ("ô", "o"), ("î", "i"), ("ï", "i")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def page_status(page):
    words = page.get_text("words")
    drawings = page.get_drawings()
    boxes = []
    for dr in drawings:
        r = dr["rect"]
        if dr["type"] in ("s", "f") and 5 <= r.width <= 14 and 5 <= r.height <= 14:
            items = dr.get("items", [])
            if any(it[0] == "re" for it in items) or dr["type"] == "f":
                boxes.append(r)
    res = []
    for r in boxes:
        nlines = 0
        for d2 in drawings:
            r2 = d2["rect"]
            if (abs(r2.x0 - r.x0) < 1.5 and abs(r2.y0 - r.y0) < 1.5
                    and abs(r2.x1 - r.x1) < 1.5 and abs(r2.y1 - r.y1) < 1.5):
                nlines += len([it for it in d2.get("items", []) if it[0] in ("l", "c")])
        if nlines < 2:
            continue
        cand = []
        for w in words:
            x0, y0, x1, y1, t = w[:5]
            if abs((y0 + y1) / 2 - (r.y0 + r.y1) / 2) < 7 and r.x1 - 1 < x0 < r.x1 + 160:
                cand.append((x0, t))
        cand.sort()
        label = " ".join(t for _, t in cand)
        if label:
            ln = norm(label)
            for status, pats in STATUS_LABELS:
                if any(p in ln for p in pats):
                    res.append(status)
                    break
    return res


def doc_status(pdf):
    try:
        d = pymupdf.open(pdf)
        found = []
        for page in d:
            found += page_status(page)
        d.close()
        if found:
            # cas ou une seule case est cochee : c'est la decision
            uniq = []
            for s in found:
                if s not in uniq:
                    uniq.append(s)
            if len(uniq) == 1:
                return uniq[0]
        return None
    except Exception:
        return None


# ---------------------------------------------------------------- appel LLM
SYSTEM = (
    "Tu es un expert en metrologie industrielle charge d'extraire des donnees de "
    "rapports d'intervention (equipements de dosage : doseuses, pompes doseuses, "
    "remplisseuses, pipettes automatiques). Les rapports sont en francais ou en anglais. "
    "Tu reponds uniquement par un objet JSON valide, sans commentaire."
)

RULES = """REGLES GENERALES
- Le document fourni est le texte integral du PDF (couche texte) suivi, pour chaque page, du texte OCR des images (logos, plaques signaletiques, schemas, signatures) et parfois de l'OCR d'une page entiere scannee. L'OCR peut comporter des erreurs de casse ou d'accents : retablis l'orthographe normale.
- Une information absente du document vaut null. N'invente jamais une valeur.
- Les valeurs d'en-tete peuvent etre remplacees par « — », « n.c. » ou etre vides : la vraie valeur se trouve alors dans le corps du texte, les notes, les observations, les tableaux, les schemas ou les images. Lis TOUT le document.
- Une synthese marquee « provisoire » ne fait pas foi quand le tableau des mesures ou une phrase dit le contraire. « Les valeurs du tableau des mesures font foi ».
- Une correction explicite (« Erratum : dans le tableau des mesures, lire X au lieu de Y ») remplace la valeur du tableau.
- Texte : recopie la valeur telle qu'ecrite dans le document (sans etiquette). Site : nom complet (« Usine de Cholet », « Etablissement d'Issoire », « Telford Plant »). Machine : modele seul (« Kaltis 85 »), sans prefixe.
- Dates : format AAAA-MM-JJ. Annees a 2 chiffres : 20xx.
- Nombres : nombres JSON (pas de chaine), convertis dans l'unite de la cle.

CLES ET PIEGES
1. machine : modele de l'equipement controle (pas le moteur, pas un equipement voisin).
2. constructeur : fabricant de l'equipement. Ce n'est JAMAIS le prestataire (en-tete, pied de page, logo du rapport, « X Services », « X Techniques », « X Calibration Ltd », « X Metrology », « X Mesure et Controle », « X Ingenierie »). Il peut n'apparaitre que dans un logo d'image OCR : un logo situe a cote des champs Equipement/Constructeur (souvent au milieu de la page 1), distinct du logo du prestataire en haut de page, meme si le nom est proche de celui du prestataire. Peut aussi etre dans une phrase (« sortie des ateliers X », « il est entraine par un moteur X » n'est pas le constructeur de l'equipement) ou une note (« Note, manufacturer: X »). Pas le fabricant du moteur ni des instruments.
3. numero_serie : n° de serie de l'equipement (pas moteur, instruments, ni n° d'inventaire INV-…). Peut se lire sur la plaque signaletique photographiee (OCR) OU etre cite dans une phrase du corps (« dont la plaque porte le numero X », « whose plate reads X », « la plaque indique X », « For the record, serial number: X »). « illisible », « plaque absente », « — », « plate missing » : null.
4. site : site du client ou l'equipement est installe, en entier, tel qu'ecrit. Pas le siege social du client, pas l'adresse du prestataire, ni l'installation/ligne (« Line 4, pompe doseuse » n'est pas un site). Si aucune valeur de site/etablissement/location/plant n'existe, null. Si l'en-tete est vide, cherche « Etablissement », « Usine de… », « Site », « Plateforme de… », « lieu d'intervention » dans le corps.
5. reference_rapport : reference du rapport en vigueur. Pas la version annulee/remplacee (« Annule et remplace »), ni commande/affaire.
6. date_intervention : jour de l'intervention sur site. Pas la date de demande, d'emission, d'impression, de prochaine visite. Peut etre dans une phrase (« la visite a eu lieu le 18 juin 2025 ») ou un tableau.
7. date_validation : date de l'approbation finale. Pas redaction, verification/relecture, impression, etalonnage. Peut etre « Approuve par X le DATE », « Date de validation : », case « Approuve par » (pas « Redige par » ni « Verifie par »), tampon « APPROVED ».
8. volume_dose_ml : dose moyenne mesuree APRES reglage, toutes tetes/essais confondus, en ml. Si plusieurs tetes/essais, moyenne generale. Ne pas confondre avec : dose avant reglage, une seule tete, le reservoir (L), le volume du circuit, l'incertitude, ni la valeur d'une synthese provisoire. Peut etre dans un schema (« Contenance apres reglage : 50,4 ml » a l'OCR, « Dose volume as left:0.2584 L », « Set point: 0.5 mL ») ou une note.
9. volume_nominal_ml : volume de consigne de l'equipement en ml. Pas la gamme du modele (« 5 – 500 ml »), pas la capacite du reservoir. Conversions : 1 µl = 0,001 ml ; 1 cl = 10 ml ; 1 L = 1000 ml ; 1 cm³ = 1 ml. Si aucune consigne n'est ecrite nulle part et que les doses mesurees (avant et apres reglage) sont groupees autour d'une valeur ronde (1, 5, 20, 50, 100… ml) a ±10 %, alors volume_nominal_ml = cette valeur ronde.
10. tolerance_ml : tolerance admise sur la dose en ml. Une tolerance en % se convertit : volume nominal × % / 100. L'incertitude elargie (k = 2) n'est pas la tolerance. « n.c. » : null. Peut etre exprimee en cm³ (= ml), µl, etc.
11. debit_ml_min : debit mesure apres reglage en ml/min. Pas le debit maximal, ni celui d'un equipement voisin. « n.m. »/« n.c. » : null. Conversions : 1 L/h = 16,6667 ml/min ; 1 ml/s = 60 ml/min ; 1 L/min = 1000 ml/min. Si la colonne apres reglage est vide ou vaut « — », prends la valeur du paragraphe « Reglages et resultats »/« Adjustments and results » (« L'equipement debite alors 2430 ml/min », « flow rate as left: 54 mL/min », « delivery rate as left: 3'730 mL/min », « Additional information, flow rate as left: 22.98 L/h ») ou d'un schema OCR. Dans un tableau Avant/Apres, si la zone « apres reglage » ne contient qu'un chiffre suivi de « — » pour les essais suivants, ce chiffre est la valeur apres reglage (ex. « Debit volumique 21 | 25 | — | — » : 25).
12. pression_bar : pression de service mesuree apres reglage en bar. Pas la pression maximale admissible, le tarage de la soupape, le reseau d'air de l'atelier, ni un equipement voisin. « n.m. »/« n.c. » : null. Conversions : 1 mbar = 0,001 bar ; 1 kPa = 0,01 bar ; 1 psi = 0,06894757 bar. Si la colonne apres reglage est vide, prends la valeur du paragraphe « Reglages et resultats » (« La pression s'est stabilisee a 2,9 bar ») ou d'une note (« operating pressure as left: 1.8 bar »).
13. reference_piece : reference de la piece EFFECTIVEMENT REMPLACEE (action « remplacee »/« replaced »), pas controlee, conservee, commandee, proposee au devis. « Aucune piece remplacee », « No part was replaced » : null. Peut etre dans une phrase (« remplace par un element neuf portant la reference X ») ou une note (« P/N of the replaced part: X »).
14. technicien : intervenant responsable cote prestataire, prenom nom. Pas l'accompagnant, l'assistant, le redacteur, le verificateur, ni le client. Cherche une mention EXPLICITE : « technicien responsable », « Intervenant principal », « Charge d'intervention » (« Charge d'intervention : Sophie Vasseur »), « lead technician », « Lead technician:SarahStroud », « Lead engineer », « responsible technician », « X led the visit », « Pour memoire, technicien responsable : … », ou la signature sous « Le technicien : ». Une personne qui a seulement « participe a l'intervention, a la demande de Y », « accompagne », « assiste » n'est PAS le technicien responsable : si aucune mention explicite n'existe, null.
15. statut : exactement « conforme », « non_conforme » ou « a_revoir ». Decision FINALE : case cochee, libelle (« Conforme », « A revoir », « Compliant », « To be reviewed »), ou phrase. « remis en production sans reserve » = conforme ; « ne peut pas etre remis en production » = non_conforme ; « sous reserve d'une nouvelle visite » = a_revoir. Le statut a l'arrivee (« etait juge non conforme ») n'est PAS le statut final.

Reponds avec un objet JSON contenant exactement ces 15 cles, dans cet ordre, et rien d'autre."""


def chat(messages, max_tokens=16000, temperature=0):
    url = os.environ["BANC_MODELE_URL"].rstrip("/") + "/v1/chat/completions"
    model = os.environ["BANC_MODELE"]
    key = os.environ["BANC_CLE_MODELE"]
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature, "response_format": {"type": "json_object"}}
    data = json.dumps(body, ensure_ascii=False).encode()
    for attempt in range(5):
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + key})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            m = d["choices"][0]["message"]
            if m.get("content"):
                return m["content"]
            print("  (reponse vide, finish=%s)" % d["choices"][0].get("finish_reason"), flush=True)
            if d["choices"][0].get("finish_reason") == "length" and max_tokens < 32000:
                max_tokens = min(32000, max_tokens * 2)
                body["max_tokens"] = max_tokens
                data = json.dumps(body, ensure_ascii=False).encode()
                print("  (max_tokens -> %d)" % max_tokens, flush=True)
            time.sleep(1)
        except urllib.error.HTTPError as e:
            print("  HTTP", e.code, e.read()[:200], flush=True)
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            print("  ERR", e, flush=True)
            time.sleep(2 * (attempt + 1))
    return None


# ------------------------------------------------------------ post-traitement
def parse_json(txt):
    if not txt:
        return {}
    txt = txt.strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.M).strip()
    m = re.search(r"\{.*\}", txt, re.S)
    if m:
        txt = m.group(0)
    try:
        return json.loads(txt)
    except Exception:
        try:
            return json.loads(txt.replace("\n", " "))
        except Exception:
            return {}


def clean_text(v):
    if v is None:
        return None
    if not isinstance(v, str):
        v = str(v)
    v = re.sub(r"\s+", " ", v).strip().strip('".;')
    if norm(v) in NULLISH or v.strip().lower() in NULLISH:
        return None
    return v or None


def clean_num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return None if v != v else float(v)
    s = str(v).strip().lower()
    if s in NULLISH:
        return None
    s = s.replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    s = s.replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def clean_date(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in NULLISH:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.search(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})", s)
    if m:
        d, mo, y = m.groups()
        y = ("20" + y) if len(y) == 2 else y
        return "%s-%02d-%02d" % (y, int(mo), int(d))
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
              "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
              "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
              "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
              "decembre": 12}
    n = norm(s)
    m = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", n)
    if m and m.group(2)[:3] in months:
        return "%s-%02d-%02d" % (m.group(3), months[m.group(2)[:3]], int(m.group(1)))
    m = re.search(r"([a-z]+)\s+(\d{1,2}),?\s+(\d{4})", n)
    if m and m.group(1)[:3] in months:
        return "%s-%02d-%02d" % (m.group(3), months[m.group(1)[:3]], int(m.group(2)))
    return None


def clean_status(v):
    if v is None:
        return None
    n = norm(v).replace(" ", "")
    if "nonconforme" in n or "noncompliant" in n:
        return "non_conforme"
    if "arevoir" in n or "revoir" in n or "review" in n:
        return "a_revoir"
    if "conforme" in n or "compliant" in n:
        return "conforme"
    return None


def lev(a, b):
    if abs(len(a) - len(b)) > 2:
        return 9
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def snap_to_text(value, text):
    """Si la valeur predite est une variante OCR d'un mot present dans le texte
    (ex. NERVEX pour NEVVEX), retablit l'orthographe du document."""
    if not value or not text:
        return value
    nv = norm(value)
    if nv and nv in norm(text):
        return value
    cands = {}
    for tok in re.findall(r"[A-Za-z][A-Za-z&.\-]{2,}", text):
        nt = norm(tok)
        if len(nt) < 4 or nt[0:1] != nv[0:1]:
            continue
        if lev(nt, nv) <= 2:
            cands[tok] = cands.get(tok, 0) + 1
    if len(cands) >= 1:
        best = max(cands.items(), key=lambda kv: (kv[1], len(kv[0])))
        if lev(norm(best[0]), nv) < len(nv):
            return best[0]
    return value


def split_alpha_num(value):
    if not value:
        return value
    return re.sub(r"(?<=[a-z])(?=\d)", " ", value)


def normalize(rec, cb_status, text=""):
    out = {}
    for k in KEYS:
        v = rec.get(k)
        if k in NUMKEYS:
            out[k] = clean_num(v)
        elif k.startswith("date"):
            out[k] = clean_date(v)
        elif k == "statut":
            out[k] = clean_status(v)
        else:
            out[k] = clean_text(v)
    if cb_status:
        # la case cochee du document est la decision finale : elle fait foi
        out["statut"] = cb_status
    if out["machine"]:
        out["machine"] = split_alpha_num(out["machine"])
    for k in ("machine", "constructeur"):
        if out[k]:
            out[k] = snap_to_text(out[k], text)
    return out


# ------------------------------------------------------------------ pipeline
def process(args):
    pdf, sortie = args
    name = os.path.splitext(os.path.basename(pdf))[0]
    t0 = time.time()
    try:
        text = extract(pdf)
        cb = doc_status(pdf)
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Voici le rapport :\n\n" + text + "\n\n" + RULES}]
        raw = chat(msgs)
        rec = parse_json(raw)
        out = normalize(rec, cb, text)
    except Exception as e:
        print(name, "ERREUR", e, flush=True)
        out = {k: None for k in KEYS}
    dest = os.path.join(sortie, name + ".json")
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    os.replace(tmp, dest)
    print("%s  %.1fs  statut=%s" % (name, time.time() - t0, out.get("statut")), flush=True)
    return name, out


def main():
    if len(sys.argv) != 3:
        print("usage: run.py {entree} {sortie}", file=sys.stderr)
        sys.exit(2)
    entree, sortie = sys.argv[1], sys.argv[2]
    os.makedirs(sortie, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(entree, "*.pdf")) + glob.glob(os.path.join(entree, "*.PDF")))
    if not pdfs:
        print("aucun PDF dans", entree, file=sys.stderr)
        return
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=min(8, len(pdfs))) as ex:
        list(ex.map(process, [(p, sortie) for p in pdfs]))
    print("TERMINE %d documents en %.0fs -> %s" % (len(pdfs), time.time() - t0, sortie))


if __name__ == "__main__":
    main()
