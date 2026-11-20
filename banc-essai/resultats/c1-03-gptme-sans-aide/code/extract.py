import pymupdf, os, base64, json, urllib.request, sys, re, time

URL = os.environ['BANC_MODELE_URL'].rstrip('/') + '/v1/chat/completions'
KEY = os.environ['BANC_CLE_MODELE']
MODEL = os.environ['BANC_MODELE']

CLES = ["machine", "constructeur", "numero_serie", "site", "reference_rapport",
        "date_intervention", "date_validation", "volume_dose_ml", "volume_nominal_ml",
        "tolerance_ml", "debit_ml_min", "pression_bar", "reference_piece",
        "technicien", "statut"]

SYSTEM = """Tu es un expert en extraction de données depuis des rapports d'intervention technique (équipements de dosage : doseuses, pompes doseuses, remplisseuses, pipettes automatiques), en français ou en anglais.

Tu reçois le texte extrait d'un PDF et les images des pages. Tu dois produire un objet JSON avec exactement 15 clés.

RÈGLES CRITIQUES (à appliquer strictement)
1. TOLÉRANCE : tolerance_ml ne vient QUE d'un champ explicite "Tolérance / Tolerance / EMT / MPE / Écart maximal toléré / tolérance admise". Si le document ne contient qu'une "Incertitude élargie (k = 2)" ou "Expanded uncertainty" et aucun champ de tolérance, alors tolerance_ml = null. L'incertitude n'est JAMAIS la tolérance.
2. DÉBIT : si la ligne "Débit / Flow rate" du tableau a "—", "n.c." ou "n.m." en après réglage, prends la valeur de la phrase de la section réglages/résultats ("L'équipement débite alors 447 ml/min", "flow rate as left: X"). Cette phrase donne la valeur APRÈS réglage même si elle commence par "À l'arrivée" / "On arrival". Convertis : 1 ml/s = 60 ml/min ; 1 L/h = 16,6667 ml/min ; 1 L/min = 1000 ml/min.
3. PRESSION : si la ligne "Pression / Pressure" a "—" en après réglage, prends la phrase ("la pression s'est stabilisée à 400 mbar", "Pressure settled at X"). L'unité du tableau peut être bar, kPa, psi ou mbar : utilise la note d'unités si elle existe ; sinon choisis l'unité qui donne une valeur plausible, c'est-à-dire INFÉRIEURE à la "pression maximale admissible" (typiquement 0,1 à 16 bar). Exemple : tableau sans unité, valeur 27,56, pression max admissible 4,0 bar → c'est du psi → 27,56 × 0,0689476 = 1,9002 bar. Convertis : 1 kPa = 0,01 bar ; 1 psi = 0,0689476 bar ; 1 mbar = 0,001 bar.
4. SITE : recopie la désignation COMPLÈTE, sans jamais retirer le préfixe : "Établissement d'Issoire" (pas "Issoire"), "Site d'Issoire" (pas "Issoire"), "Établissement de Saumur", "Plateforme d'Oyonnax", "Usine de Guingamp", "Dundee Facility". Si le champ Site vaut "—", "n.c." ou est absent, cherche dans la prose : "Le déplacement chez le client, X" / "déplacement chez le client, X" / "The visit to the customer, X". Si vraiment absent → null. Jamais le nom du client ni son siège.
5. TECHNICIEN : le technicien responsable est la personne marquée comme responsable/lead :
   - champ explicite "Technicien / Technician / Technicien responsable / Responsible technician / Lead technician / Chargé d'intervention / Intervenant principal" suivi d'un nom ;
   - ou "(responsable)" dans la liste INTERVENANTS ;
   - ou la personne qui "a conduit l'intervention" / "led the visit" / "a mené l'intervention".
   Ne prends JAMAIS : un participant ("a participé" / "took part"), un accompagnant, le demandeur ("à la demande de" / "at the request of"), "Approbation client", "Checked by", "Requested by", "Prepared by". Si le champ "Le technicien :" est vide et que personne n'est désigné comme lead → null.
6. RÉFÉRENCE : reference_rapport sans suffixe de révision : "DM-RI-2026-9253 Rev. B" → "DM-RI-2026-9253" ; "ST-RI-2025-8531 Indice B" → "ST-RI-2025-8531".
7. TOLÉRANCE EN POURCENTAGE : si la colonne Tolérance du tableau vaut "—" mais que la prose dit "The deviation allowed by the customer's specification is ± X %" (ou "l'écart autorisé par la spécification client est de ± X %"), alors tolerance_ml = X % × volume_nominal_ml. Exemples : ± 2,5 % avec volume nominal 1000 ml → 25 ml ; ± 8 % avec volume nominal 1 ml → 0,08 ml ; ± 2,5 % avec volume nominal 250 ml → 6,25 ml.
8. NE JAMAIS utiliser la valeur "avant réglage" / "as found" pour volume_dose_ml, debit_ml_min ou pression_bar. Si l'après réglage vaut "—", "n.m." ou "n.c." et qu'aucune phrase ne donne la valeur après réglage, mets null (ne recopie pas l'avant réglage).
9. RÉFÉRENCE ANNULÉE : "ANNULE ET REMPLACE X" / "Annule et remplace : X" / "Supersedes : X" désigne l'ANCIENNE référence (remplacée) : ne l'utilise JAMAIS. La référence en vigueur est celle du champ "Référence du rapport / Report reference / Report no. / Réf. document / Document no.". Si ce champ est absent et que le document ne donne que "ANNULE ET REMPLACE X", cherche la référence en vigueur ailleurs ("Pour mémoire, N° de compte rendu : Y", "Report no. Y").

RÈGLES GÉNÉRALES
- Les documents contiennent des pièges : valeurs provisoires vs valeurs faisant foi, valeurs "avant réglage" (as found) vs "après réglage" (as left), statut initial vs statut final, ancienne référence vs référence en vigueur, marque du moteur vs marque de l'équipement, participant vs technicien responsable.
- Quand un tableau de mesures dit que ses valeurs font foi et qu'une synthèse est provisoire, utilise le tableau.
- Les valeurs "après réglage" / "as left" sont celles à retenir pour volume_dose_ml, debit_ml_min, pression_bar.
- Les images peuvent contenir des informations essentielles : volume nominal sur le schéma, date d'approbation sur le tampon, pages entières scannées, logo du constructeur de l'équipement, nom du technicien sur un visa.

DÉFINITIONS
- machine : modèle exact de l'équipement contrôlé (ex. "Juvelpax 250"). Pas le moteur, pas le convoyeur amont.
- constructeur : fabricant de l'équipement contrôlé. Peut être dans un champ (Constructeur/Manufacturer/BRAND/MARQUE) ou dans le texte ("sortie des ateliers X", "built by X", "Note, manufacturer: X", "À noter, constructeur : X") ou sur un logo/image. Pas la marque du moteur ni des instruments. Recopie l'orthographe exacte.
- numero_serie : numéro de série de l'équipement. Peut être dans le texte ("dont la plaque porte le numéro X", "whose plate reads X"). Si "—", "illisible", "plate missing", "unreadable", "n.c." → null.
- date_intervention : jour de l'intervention (champ ou texte ou tableau des étapes). Format AAAA-MM-JJ.
- date_validation : date de l'approbation finale (date du visa "Approuvé/Approved by", tampon d'approbation, ou texte "approuvé le"). Si absente ou "____________" → null. Format AAAA-MM-JJ.
- volume_dose_ml : volume de dose moyen mesuré après réglage, en ml. Si plusieurs essais après réglage, fais la moyenne. Si "—", prends la valeur citée dans le texte ("settled at X on average", "volume délivré après réglage : X"). Convertis en ml.
- volume_nominal_ml : volume de consigne/nominal de l'équipement, en ml. Convertis en ml (1 cl = 10 ml ; 1 µL = 0,001 ml ; 1 cm³ = 1 ml ; 1 L = 1000 ml).
- reference_piece : référence de la pièce remplacée pendant l'intervention (action "remplacée/replaced"). Si aucune pièce remplacée → null.
- statut : décision finale sur l'équipement : "conforme", "non_conforme" ou "a_revoir". Utilise le statut final (case cochée avec une croix, section Statut/Verdict/Status/RESULT, ou texte "statut : X"), pas le statut initial "à l'arrivée ... non conforme".

SORTIE
Réponds UNIQUEMENT par un objet JSON valide, sans texte autour, avec exactement ces 15 clés. Les nombres sont des nombres JSON (pas des chaînes). Les dates sont "AAAA-MM-JJ". Une valeur absente est null."""


def page_images(pdf_path, dpi=150):
    d = pymupdf.open(pdf_path)
    out = []
    for p in d:
        pix = p.get_pixmap(dpi=dpi)
        out.append(pix.tobytes('png'))
    return out


def embedded_images(pdf_path, min_w=200, min_h=50, max_w=1200):
    """Images embarquées à leur résolution native (upscalées si petites)."""
    d = pymupdf.open(pdf_path)
    out = []
    seen = set()
    for p in d:
        for info in p.get_image_info(xrefs=True):
            xref = info['xref']
            if xref in seen:
                continue
            seen.add(xref)
            w, h = info['width'], info['height']
            if w < min_w or h < min_h or w > max_w:
                continue
            try:
                pix = pymupdf.Pixmap(d, xref)
            except Exception:
                continue
            if pix.n > 4:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if w < 600:
                pix = pymupdf.Pixmap(pix, pix.width * 2, pix.height * 2, None)
            out.append(pix.tobytes('png'))
    return out


def checkbox_hints(pdf_path):
    d = pymupdf.open(pdf_path)
    hints = []
    for pno, p in enumerate(d):
        words = p.get_text('words')
        drs = p.get_drawings()
        rects = [dr['rect'] for dr in drs if 5 < dr['rect'].width < 16 and 5 < dr['rect'].height < 16]
        lines = []
        for dr in drs:
            for it in dr['items']:
                if it[0] == 'l':
                    lines.append((it[1], it[2]))
        for r in rects:
            rr = pymupdf.Rect(r.x0 - 1, r.y0 - 1, r.x1 + 1, r.y1 + 1)
            inside = [(a, b) for a, b in lines if rr.contains(a) and rr.contains(b)]
            if len(inside) >= 2:
                cand = [w for w in words if abs(w[1] - r.y0) < 8 and w[0] > r.x1 - 1 and w[0] < r.x1 + 160]
                cand.sort(key=lambda w: w[0])
                txt = ' '.join(w[4] for w in cand[:4])
                if txt:
                    hints.append(f'[case cochée page {pno+1}] {txt}')
    return hints


def build_content(pdf_path):
    d = pymupdf.open(pdf_path)
    text = '\n'.join(f'--- PAGE {i+1} ---\n' + p.get_text() for i, p in enumerate(d))
    hints = checkbox_hints(pdf_path)
    if hints:
        text += '\n\nINDICES CASES À COCHER:\n' + '\n'.join(hints)
    content = [{'type': 'text', 'text': 'TEXTE DU DOCUMENT:\n' + text}]
    for png in page_images(pdf_path):
        content.append({'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + base64.b64encode(png).decode()}})
    emb = embedded_images(pdf_path)
    if emb:
        content.append({'type': 'text', 'text': 'IMAGES EMBARQUÉES (logos, plaques, schémas) à leur résolution native :'})
        for png in emb:
            content.append({'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + base64.b64encode(png).decode()}})
    content.append({'type': 'text', 'text': 'Extrais les 15 champs et réponds uniquement par le JSON.'})
    return content


def call_model(content, max_tokens=12000):
    body = {'model': MODEL, 'messages': [
        {'role': 'system', 'content': SYSTEM},
        {'role': 'user', 'content': content}], 'max_tokens': max_tokens,
        'temperature': 0}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Bearer ' + KEY})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    return r['choices'][0]['message'].get('content') or ''


def parse_json(txt):
    if not txt:
        return None
    m = re.search(r'\{.*\}', txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def extract(pdf_path):
    content = build_content(pdf_path)
    for attempt in range(5):
        try:
            txt = call_model(content)
            obj = parse_json(txt)
            if obj:
                return obj
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    return None


if __name__ == '__main__':
    print(json.dumps(extract(sys.argv[1]), ensure_ascii=False, indent=2))
