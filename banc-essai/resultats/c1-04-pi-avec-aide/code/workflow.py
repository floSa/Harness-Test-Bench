#!/usr/bin/env python3
"""Extraction des 15 champs des rapports d'intervention (PDF) vers des JSON.

Usage : python workflow.py {entree} {sortie}

Le workflow lit les variables BANC_MODELE_URL, BANC_MODELE et BANC_CLE_MODELE.
Il combine le texte extractible des PDF, le rendu image de chaque page (pour les
pages scannées, plaques, tampons, cases cochées et corrections manuscrites) et
l'ontologie fournie. Aucune réponse n'est codée en dur.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent
KEYS = [
    "machine", "constructeur", "numero_serie", "site", "reference_rapport",
    "date_intervention", "date_validation", "volume_dose_ml",
    "volume_nominal_ml", "tolerance_ml", "debit_ml_min", "pression_bar",
    "reference_piece", "technicien", "statut",
]
NUM_KEYS = {"volume_dose_ml", "volume_nominal_ml", "tolerance_ml",
            "debit_ml_min", "pression_bar"}
DATE_KEYS = {"date_intervention", "date_validation"}

RULES = r"""
Points de vigilance (à appliquer impérativement) :
1. VALEURS APRÈS RÉGLAGE : dans la section « Réglages et résultats » / « Adjustments and results », les phrases du type « L'équipement débite alors X », « the equipment then delivers X », « La pression s'est stabilisée à Y », « pressure settled at Y » donnent les valeurs mesurées APRÈS réglage. Utilise-les pour debit_ml_min / pression_bar même si le tableau des mesures indique « — », « n.c. » ou « n.m. » pour la ligne après réglage. Ne prends jamais le débit maximal, la pression maximale, le tarage de soupape, le réseau d'air, ni un équipement voisin.
2. CONSTRUCTEUR : le prestataire (en-tête, pied de page, logo du rapport) n'est JAMAIS le constructeur. Si la case Constructeur/Manufacturer est vide, « n.c. », « — » ou ne contient qu'un logo, lis le logo de la case constructeur (image) et/ou cherche dans le texte « sortie des ateliers X », « built by X », « manufactured by X », « fabricant X ». Le constructeur du moteur ou des instruments n'est pas celui de l'équipement.
3. TECHNICIEN : ne retiens que la personne explicitement responsable côté prestataire : « technicien responsable », « lead technician », « X (responsable) », « X a conduit/led the visit ». Si le texte dit seulement « X a participé à l'intervention, à la demande de Y » ou « X took part in the visit, at the request of Y », alors X est accompagnant et Y demandeur : technicien = null. Les personnes « rédigé par / vérifié par / approuvé par », « prepared/checked/approved by », les signatures et les accompagnants ne sont pas le technicien responsable. Si la ligne « Le technicien : » est vide ou ne porte qu'une signature, mets null.
4. NUMÉRO DE SÉRIE : lis les plaques signalétiques photographiées (images). Prends le n° de série de l'équipement, pas du moteur, pas le n° d'inventaire/asset. Si la case est vide, « — », « illisible » ou « plaque absente », cherche le numéro dans une phrase du type « dont la plaque porte le numéro X », « whose plate reads X », « la plaque signalétique indique X » : ce X est le numéro de série de l'équipement. Ne mets null que si aucune plaque ni phrase ne donne le numéro.
5. PIÈCE : reference_piece = uniquement la pièce effectivement REMPLACÉE. Une pièce contrôlée/conservée, commandée, proposée au devis, ou « aucune pièce remplacée » => null. La référence peut être donnée dans une note (« P/N of the replaced part », « pour mémoire »).
6. VOLUME DE DOSE : dose moyenne après réglage, toutes têtes et tous essais. Si seuls des essais après réglage sont donnés, fais leur moyenne. Si une valeur est barrée/corrigée à la main, prends la valeur manuscrite corrigée. Ne prends ni le volume avant réglage, ni le réservoir, ni le volume du circuit, ni l'incertitude.
7. TOLÉRANCE : une tolérance en % se convertit par nominal × % / 100. L'incertitude élargie (k=2) n'est pas la tolérance. « n.c. » => null.
8. DATES : date_intervention = jour de l'intervention sur site (pas demande, émission, impression, prochaine visite). date_validation = approbation finale (case Approuvé, tampon APPROUVÉ, « Validation date », « approved on », « approuvé … le ») ; pas la rédaction, la vérification, la relecture ni l'impression. Case d'approbation vide => null.
9. STATUT : décision FINALE ; ignore le statut à l'arrivée. « remis en production sans réserve » / « compliant » => conforme ; « ne peut pas être remis en production » / « non-compliant » => non_conforme ; « sous réserve d'une nouvelle visite » / « to be reviewed » / « à revoir » => a_revoir.
10. SITE : site du client où l'équipement est installé, en entier ; pas le siège social ni l'adresse du prestataire. « Ligne 2 », « Line 2 », « atelier », « installation » ne sont jamais le site. Si la case Site est « n.c. »/« — » et qu'aucun autre lieu d'installation (usine, site, établissement, plant, facility) n'est donné, mets null.
11. RÉFÉRENCE RAPPORT : référence en vigueur ; ignore « annule et remplace » / « supersedes ».
12. Réponds uniquement par le JSON, en respectant les types : nombres JSON (pas de chaînes), dates ISO, null pour absent.
"""


# ---------------------------------------------------------------------------
# Utilitaires de normalisation et de conversion
# ---------------------------------------------------------------------------

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def norm(s) -> str:
    return re.sub(r"\s+", " ", strip_accents(str(s))).strip().lower()


NULLISH = {
    "", "null", "none", "n/a", "na", "n.c", "n.c.", "nc", "n.m", "n.m.", "nm",
    "-", "--", "—", "–", "illisible", "plaque absente", "non communique",
    "non communiquee", "non mesure", "non mesuree", "non applicable",
    "aucune", "aucun", "sans objet", "not applicable", "not measured",
    "illegible", "missing", "unreadable", "plate missing",
    "plaque manquante", "absent", "absente", "non lisible",
}


def clean_text_value(v):
    if v is None:
        return None
    if not isinstance(v, str):
        v = str(v)
    v = re.sub(r"\s+", " ", v).strip()
    if norm(v) in NULLISH:
        return None
    return v


def parse_number(v):
    """Convertit une valeur (nombre, ou chaîne avec unité) en float."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("\u00a0", " ").replace("\u202f", " ")
    if norm(s) in NULLISH:
        return None
    # Une plage "5 – 500 ml" n'est pas une valeur unique.
    if re.search(r"\d\s*[-–—]\s*\d", s) and not re.match(r"^\s*[-+]?\d", s):
        return None
    m = re.search(r"[-+]?\d+(?:[ .,'’]\d+)*", s)
    if not m:
        return None
    raw = m.group(0).replace(" ", "").replace("'", "").replace("’", "")
    # Déterminer le séparateur décimal (le dernier . ou , s'il est suivi de 1-4 chiffres).
    if "." in raw and "," in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        # virgule décimale, sauf groupes de milliers 1,250 (3 chiffres) répétés
        parts = raw.split(",")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3):
            raw = raw.replace(",", "")
        else:
            raw = raw.replace(",", ".")
    elif raw.count(".") > 1:
        # points de milliers
        raw = raw.replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return None


MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12, "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}


def parse_date(v):
    if v is None:
        return None
    s = str(v).strip()
    if norm(s) in NULLISH:
        return None
    # Année d'abord
    m = re.search(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    # Jour/mois/année (les rapports utilisent le format européen, même en anglais)
    m = re.search(r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})(?!\d)", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        return f"{y:04d}-{mo:02d}-{d:02d}"
    # 14 mars 2026 / March 14, 2026
    m = re.search(r"(?<!\d)(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})", s)
    if m and norm(m.group(2)) in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[norm(m.group(2))]:02d}-{int(m.group(1)):02d}"
    m = re.search(r"([A-Za-zÀ-ÿ]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m and norm(m.group(1)) in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[norm(m.group(1))]:02d}-{int(m.group(2)):02d}"
    return None


def parse_status(v):
    if v is None:
        return None
    s = norm(v)
    if not s or s in NULLISH:
        return None
    if "non" in s and ("conform" in s or "compliant" in s):
        return "non_conforme"
    if "revoir" in s or "review" in s or "sous reserve" in s or "reserve" in s:
        return "a_revoir"
    if "conform" in s or "compliant" in s:
        return "conforme"
    return None


def convert_flow(value, unit):
    n = parse_number(value)
    if n is None:
        return None
    u = norm(unit).replace(" ", "")
    if u in {"ml/min", "mlmn", "ml/mn"}:
        return n
    if u in {"ml/s", "mls"}:
        return n * 60.0
    if u in {"l/h", "lh"}:
        return n * 1000.0 / 60.0
    if u in {"l/min", "lmn", "l/mn"}:
        return n * 1000.0
    return n


def convert_pressure(value, unit):
    n = parse_number(value)
    if n is None:
        return None
    u = norm(unit).replace(" ", "")
    if u == "bar":
        return n
    if u == "mbar":
        return n * 0.001
    if u == "kpa":
        return n * 0.01
    if u == "psi":
        return n * 0.06894757
    return n


# ---------------------------------------------------------------------------
# Extraction LLM
# ---------------------------------------------------------------------------

def load_ontology() -> str:
    p = ROOT / "ontologie.md"
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def render_pdf(pdf_path: Path):
    doc = pymupdf.open(pdf_path)
    texts, images = [], []
    for page in doc:
        texts.append(page.get_text())
        pix = page.get_pixmap(dpi=200, colorspace=pymupdf.csRGB, alpha=False)
        images.append(pix.tobytes("jpeg", jpg_quality=80))
    doc.close()
    return texts, images


def api_call(body: dict, timeout: int = 600) -> dict:
    url = os.environ["BANC_MODELE_URL"].rstrip("/") + "/v1/chat/completions"
    key = os.environ["BANC_CLE_MODELE"]
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def extract_json_from_content(content: str):
    if not content:
        return None
    # Retire les éventuelles clôtures markdown.
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(content[start:end + 1])
        except json.JSONDecodeError:
            return None
    return None


def make_messages(texts, images):
    ontology = load_ontology()
    parts = []
    for i, t in enumerate(texts):
        parts.append(
            f"\n===== PAGE {i + 1} (texte extrait) =====\n"
            + (t.strip() if t.strip() else "[aucun texte extractible: page image]")
        )
    content = [{
        "type": "text",
        "text": f"""Tu es un expert en extraction de données de rapports d'intervention d'équipements de dosage.
Applique STRICTEMENT l'ontologie et les points de vigilance ci-dessous.

{ontology}

{RULES}

Réponds UNIQUEMENT par un objet JSON valide, avec exactement ces 15 clés, sans commentaire ni markdown:
{json.dumps(KEYS, ensure_ascii=False)}
""",
    }]
    for i, b in enumerate(images):
        content.append({"type": "text", "text": f"Image de la page {i + 1}:"})
        content.append({
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()},
        })
    content.append({"type": "text", "text": "TEXTE EXTRAIT:\n" + "\n".join(parts)})
    return [{"role": "user", "content": content}]


def call_model(texts, images, attempts: int = 3):
    model = os.environ["BANC_MODELE"]
    last_exc = None
    for attempt in range(attempts):
        try:
            body = {
                "model": model,
                "messages": make_messages(texts, images),
                "max_tokens": 9000,
                "temperature": 0,
                "reasoning_effort": "low",
            }
            r = api_call(body)
            content = (r.get("choices") or [{}])[0].get("message", {}).get("content")
            obj = extract_json_from_content(content or "")
            if isinstance(obj, dict):
                return obj, r
            last_exc = ValueError("réponse JSON invalide: " + repr((content or "")[:300]))
        except Exception as e:  # réseau, 429, 5xx, coupure…
            last_exc = e
        time.sleep(1.5 * (attempt + 1))
    # Repli : texte seul, sans images (si la requête avec images est trop lourde).
    try:
        text_only = [{"type": "text", "text": "\n".join(
            f"===== PAGE {i+1} =====\n{t}" for i, t in enumerate(texts))}]
        body = {
            "model": model,
            "messages": [{"role": "user", "content": text_only[0]["text"] +
                          "\n\n" + RULES +
                          "\nRéponds uniquement par un objet JSON avec les clés: " +
                          json.dumps(KEYS, ensure_ascii=False)}],
            "max_tokens": 9000,
            "temperature": 0,
            "reasoning_effort": "low",
        }
        r = api_call(body, timeout=600)
        content = (r.get("choices") or [{}])[0].get("message", {}).get("content")
        obj = extract_json_from_content(content or "")
        if isinstance(obj, dict):
            return obj, r
    except Exception as e:
        last_exc = e
    raise RuntimeError(f"extraction impossible: {last_exc!r}")


# ---------------------------------------------------------------------------
# Replis déterministes (uniquement si le LLM a laissé null)
# ---------------------------------------------------------------------------

def find_serial(text: str):
    patterns = [
        r"(?:plaque\s+porte\s+le\s+num[eé]ro|plaque\s+signal[eé]tique\s+(?:indique|porte)\s+(?:le\s+num[eé]ro\s+)?|whose\s+plate\s+reads|plate\s+reads|rating\s+plate\s+(?:reads|shows))\s*:?\s*([A-Z0-9][A-Z0-9./_-]{3,})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            val = m.group(1).strip(" .,;:")
            if norm(val) not in NULLISH:
                return val
    return None


def find_manufacturer(text: str):
    patterns = [
        r"sortie\s+des\s+ateliers\s+([A-Z][A-Za-zÀ-ÿ0-9_-]+)",
        r"\b(?:built|manufactured|made)\s+by\s+([A-Z][A-Za-zÀ-ÿ0-9_-]+)",
        r"\bfabricant\s*:?\s*([A-Z][A-Za-zÀ-ÿ0-9_-]+)",
        r"\bconstructeur\s*:?\s*([A-Z][A-Za-zÀ-ÿ0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            val = m.group(1).strip(" .,;:")
            # Éviter les mots génériques et le prestataire.
            if norm(val) not in {"le", "la", "les", "ce", "cette", "son", "sa"}:
                return val
    return None


def find_flow(text: str):
    patterns = [
        r"(?:l['’]?[ée]quipement\s+d[ée]bite\s+alors|the\s+equipment\s+then\s+delivers|equipment\s+then\s+delivers|d[ée]bit\s+(?:volumique\s+)?apr[èe]s\s+r[ée]glage|flow\s+rate\s+(?:as\s+left|after\s+adjustment))\s*:?\s*([-+]?\d+(?:[ .,'’]\d+)*)\s*(mL/min|ml/min|ml/s|mL/s|L/h|l/h|L/min|l/min)?",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            n = convert_flow(m.group(1), m.group(2) or "ml/min")
            if n is not None:
                return n
    return None


def find_pressure(text: str):
    patterns = [
        r"(?:la\s+pression\s+s['’]est\s+stabilis[ée]e\s+[àa]|pressure\s+settled\s+at|pression\s+(?:de\s+service\s+)?apr[èe]s\s+r[ée]glage|operating\s+pressure\s+(?:as\s+left|after\s+adjustment))\s*:?\s*([-+]?\d+(?:[ .,'’]\d+)*)\s*(bar|mbar|kPa|psi)?",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            n = convert_pressure(m.group(1), m.group(2) or "bar")
            if n is not None:
                return n
    return None


def find_validation_date(text: str):
    patterns = [
        r"(?:date\s+de\s+validation|validation\s+date|date\s+d['’]approbation|approved\s+on|approval\s+date)\s*:?\s*([0-3]?\d[./-][01]?\d[./-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            d = parse_date(m.group(1))
            if d:
                return d
    return None


def find_reference_piece(text: str):
    patterns = [
        r"(?:P/N\s+of\s+the\s+replaced\s+part|r[ée]f[ée]rence\s+de\s+la\s+pi[èe]ce\s+remplac[ée]e|part\s+(?:no\.?|reference)\s+of\s+the\s+replaced\s+part)\s*:?\s*([A-Z0-9][A-Z0-9./_-]{2,})",
        r"(?:a\s+[ée]t[ée]\s+remplac[ée]e?\s+par\s+un\s+[ée]l[ée]ment\s+neuf\s+portant\s+la\s+r[ée]f[ée]rence|was\s+replaced\s+by\s+a\s+new\s+part\s+(?:with\s+)?(?:the\s+)?(?:part\s+)?(?:number|reference))\s*:?\s*([A-Z0-9][A-Z0-9./_-]{2,})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1).strip(" .,;:")
    return None


# ---------------------------------------------------------------------------
# Assemblage et post-traitement
# ---------------------------------------------------------------------------

def fallback_from_text(text: str) -> dict:
    return {
        "machine": None, "constructeur": find_manufacturer(text),
        "numero_serie": find_serial(text), "site": None,
        "reference_rapport": None, "date_intervention": None,
        "date_validation": find_validation_date(text),
        "volume_dose_ml": None, "volume_nominal_ml": None,
        "tolerance_ml": None, "debit_ml_min": find_flow(text),
        "pression_bar": find_pressure(text),
        "reference_piece": find_reference_piece(text),
        "technicien": None, "statut": None,
    }


def postprocess(obj: dict, text: str) -> dict:
    out = {k: obj.get(k) for k in KEYS}
    for k in ("machine", "constructeur", "numero_serie", "site",
              "reference_rapport", "reference_piece", "technicien"):
        out[k] = clean_text_value(out[k])
    for k in NUM_KEYS:
        out[k] = parse_number(out[k])
    for k in DATE_KEYS:
        out[k] = parse_date(out[k])
    out["statut"] = parse_status(out["statut"])

    # Replis conservateurs, uniquement sur une valeur manquante.
    if not out["numero_serie"]:
        out["numero_serie"] = find_serial(text)
    if not out["constructeur"]:
        out["constructeur"] = find_manufacturer(text)
    if not out["date_validation"]:
        out["date_validation"] = find_validation_date(text)
    if out["debit_ml_min"] is None:
        out["debit_ml_min"] = find_flow(text)
    if out["pression_bar"] is None:
        out["pression_bar"] = find_pressure(text)
    if not out["reference_piece"]:
        out["reference_piece"] = find_reference_piece(text)

    # Un site qui n'est qu'une ligne/installation n'est pas un site.
    if out["site"]:
        s = norm(out["site"])
        if re.match(r"^(ligne|line|atelier|workshop|installation|poste)\b", s):
            out["site"] = None
        elif s in NULLISH:
            out["site"] = None
    # Une pièce "aucune" ne doit jamais rester.
    if out["reference_piece"]:
        s = norm(out["reference_piece"])
        if "aucune piece" in s or "no part" in s:
            out["reference_piece"] = None
    return out


def extract_pdf(pdf_path: Path) -> dict:
    texts, images = render_pdf(pdf_path)
    try:
        raw, _ = call_model(texts, images)
        obj = postprocess(raw, "\n".join(texts))
    except Exception as e:
        print(f"[{pdf_path.name}] échec LLM: {e}", file=sys.stderr)
        obj = postprocess(fallback_from_text("\n".join(texts)), "\n".join(texts))
    # Sécurité de format : exactement les 15 clés, types corrects.
    return {k: obj.get(k) for k in KEYS}


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python workflow.py {entree} {sortie}", file=sys.stderr)
        return 2
    entry = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(entry.rglob("*.pdf"))
    if not pdfs:
        print(f"Aucun PDF trouvé dans {entry}", file=sys.stderr)
        return 1
    results = {}
    workers = min(6, max(1, len(pdfs)))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(extract_pdf, p): p for p in pdfs}
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                results[p] = fut.result()
                print(f"OK {p.name}", file=sys.stderr)
            except Exception as e:
                print(f"ERREUR {p.name}: {e}", file=sys.stderr)
                results[p] = {k: None for k in KEYS}
    for p, obj in results.items():
        (outdir / (p.stem + ".json")).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(pdfs)} document(s) traité(s) -> {outdir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
