from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import pymupdf

PROMPT = r"""Tu es un expert en extraction de données de dossiers d'intervention sur des équipements de dosage industriels (doseuse, pompe doseuse, remplisseuse, pipette automatique). On te fournit UN document (plusieurs pages) sous forme de texte extrait ET d'images de chaque page. Le texte peut être incomplet ou absent (page scannée) ; les images peuvent contenir des tableaux, des annotations de schéma, des tampons et des cases à cocher.

Analyse l'ENSEMBLE du document (texte + images) et renvoie UNIQUEMENT un objet JSON valide, sans texte autour, sans balises Markdown.

Détermine d'abord le type de document :
- "report" : rapport d'intervention / service report / compte rendu d'intervention.
- "rectification" : rectificatif / erratum / courrier corrigeant une valeur d'un rapport.
- "cancellation" : avis d'annulation d'un rapport.
- "other" : tout autre courrier.

Schéma de sortie :
{
  "type": "report" | "rectification" | "cancellation" | "other",
  "report_reference": "référence du rapport de CE document, ou null",
  "supersedes": ["références que ce rapport annule et remplace", ...],
  "cancels": ["références annulées par ce courrier", ...],
  "rectifies": "référence du rapport visé par le rectificatif, ou null",
  "corrections": [{"field": "clé parmi les 11 champs d'intervention", "value_normalized": valeur corrigée déjà convertie dans l'unité de la clé, "raw": "texte exact de la correction"}],
  "equipment": {"machine": null, "constructeur": null, "numero_serie": null, "site": null},
  "intervention": {
    "reference_rapport": null,
    "date_intervention": null,
    "date_validation": null,
    "volume_dose_ml": null,
    "volume_nominal_ml": null,
    "tolerance_ml": null,
    "debit_ml_min": null,
    "pression_bar": null,
    "reference_piece": null,
    "technicien": null,
    "statut": null
  }
}

Règles d'extraction (très importantes) :
1. Dates au format AAAA-MM-JJ. date_intervention = date réelle de l'intervention (pas la date de demande, d'émission, d'impression ni de prochaine visite). date_validation = date de l'approbation FINALE du rapport (champ "Validation date"/"Date de validation", "Approved ... on"/"Approuvé le", ou tampon "APPROVED ... <date>"). Ne pas confondre avec "report reviewed on" (relecture) sauf si c'est la seule date d'approbation. Une date absente, vide, "____", "n.c.", "n.m.", "—" ou "n/a" donne null. ATTENTION au tableau des visas : les dates "Rédigé par"/"Vérifié par" ne sont PAS des dates de validation ; ne prends la date que dans la colonne/ligne "Approuvé par"/"Approved by" si elle est remplie, ou dans une mention/tampon d'approbation explicite. Si seule la date de rédaction ou de vérification est remplie, date_validation = null.
2. Pour les nombres, renvoie un nombre JSON (pas une chaîne) dans l'unité demandée :
   - volume_dose_ml : volume de dose MOYEN mesuré APRÈS réglage (as left / après réglage / moyenne après / moyen des essais). Si plusieurs têtes et pas de moyenne générale, fais la moyenne de toutes les valeurs après réglage des têtes. IMPORTANT : les valeurs après réglage sont souvent annotées SUR LE SCHÉMA (ex. "Dose volume as left: 25.2 mL", "Fill volume as left: 19.3 mL", "Volume de dose après réglage: ..."), ou dans une note ("Note, dose as left: ...", "À noter, volume délivré après réglage : ...", "Pour mémoire, ..."). Utilise aussi ces annotations. Ignore les valeurs "avant réglage"/"as found". Convertis L, cl, µl, cm³ en mL.
   - volume_nominal_ml : volume de consigne / nominal / cible (target volume, "valeur visée", consigne, "Volume nomin."). Convertis en mL.
   - tolerance_ml : tolérance admise sur le volume de dose ("Tolérance", "MPE", "EMT", "écart admis"). Si exprimée en %, calcule % × volume nominal. Si exprimée en µl/cl/L, convertis en mL. Si "n.c."/"n.m."/absent, null.
   - debit_ml_min : débit mesuré APRÈS réglage (as left / après réglage), dans le tableau, une note ("débit après réglage : ...", "À noter, débit après réglage : ...", "throughput as left: ...") ou une annotation du schéma ("Débit volumique après réglage : ..."). Si le tableau après réglage est vide/absent ("n.c.", "n.m.", "—") mais que le texte narratif donne un débit ("L'équipement débite alors X", "the equipment then delivers X", "débit après réglage"), utilise cette valeur narrative. Convertis L/h, L/min, ml/s, ml/min en mL/min. Si vraiment aucun débit après réglage ni narratif, null (ne prends pas la simple ligne "avant réglage/as found" du tableau).
   - pression_bar : pression de service mesurée APRÈS réglage, dans le tableau, une note ("pression de service après réglage : ...", "Pour mémoire, pression ligne après réglage : ...") ou le texte de réglage ("Pressure settled at X", "La pression s'est stabilisée à X", "operating pressure as left"). Convertis kPa, mbar, psi en bar. Si le tableau après réglage est vide/absent ("n.m.", "n.c.", "—") mais que le texte narratif donne une pression après réglage, utilise cette valeur. Si vraiment aucune, null (ne prends pas la simple ligne "avant réglage/as found").
3. report_reference : si l'en-tête n'a pas de référence explicite mais qu'une note/observation donne "réf. document", "report reference", "reference", "Réf. document : X" (et que X n'est pas une référence d'un autre rapport remplacé), utilise-la comme référence de CE rapport. De même pour reference_rapport.
4. reference_piece : référence de la pièce réellement REMPLACÉE pendant l'intervention ("remplacée", "replaced", "a été remplacé par", "remplacé par un élément neuf portant la référence X", "part reference of the replaced part", "référence pièce de la pièce remplacée"). Ne prends pas une pièce contrôlée/conservée, commandée (non posée) ou proposée au devis. S'il n'y a aucune pièce remplacée, null. Si une note donne explicitement la référence de la pièce remplacée, elle prime sur la liste des pièces.
5. technicien : technicien responsable côté prestataire. Prends-le UNIQUEMENT si le document l'identifie explicitement comme responsable : "Lead technician", "Responsible technician", "Technicien responsable", "Intervenant principal", "Responsable technicien", "lead engineer", "X (responsable)", "X (lead)", ou une phrase "X a conduit/lédé l'intervention"/"X led the visit". Ne prends JAMAIS : l'approbation client, un "assistant"/"accompagnant", une personne qui "a participé"/"took part"/"était présent", le demandeur/"requested by", ni le rédacteur du rapport ("Report prepared by", "Rapport rédigé par") sauf s'il est aussi désigné responsable. Si aucun responsable explicite, null.
6. statut : décision FINALE sur l'équipement : "conforme", "non_conforme" ou "a_revoir". Utilise le statut de conclusion, le tampon, la case cochée, ou une note "For the record, status/outcome". "À l'arrivée l'équipement était jugé non conforme" n'est PAS le statut final. En cas de contradiction entre une case cochée et le texte de conclusion, privilégie la conclusion/tampon le plus explicite. Mapping : Compliant/Conforme -> conforme ; Non-compliant/Non conforme -> non_conforme ; To be reviewed/À revoir -> a_revoir. Si aucune décision explicite mais que l'avis du technicien dit "peut être remis en production sans réserve/without restriction" -> conforme ; "sous réserve d'une nouvelle visite rapprochée"/"subject to an early follow-up visit" -> a_revoir ; "ne peut pas être remis en production en l'état" -> non_conforme. Sinon null.
7. L'équipement du document : utilise les champs d'en-tête (Équipement/Machine/Unit/Equipment/Désignation, Constructeur/Manufacturer/Make/Fabricant/Brand, N° de série/Serial/Unit ID/Identifiant machine, Site/Location/Implantation) et aussi les notes ("Additional information, equipment: ...", "serial number: ...", "équipement : ...", "implantation : ..."). Le "Siège" du client n'est PAS le site, et l'"Installation"/"Ligne"/"Line" n'est PAS le site. Pour le site, utilise aussi "visit to the customer, X" / "déplacement chez le client, X". Les valeurs "—", "n.c.", "n.m.", "n/a", "—" donnent null.
8. Ignore totalement les données du "convoyeur amont"/"upstream conveyor", du réseau d'air, des instruments de mesure, des moteurs, et des autres équipements, qui sont des distracteurs.
9. Pour un rectificatif : "rectifies" = référence du rapport visé ; "corrections" contient la ou les valeurs corrigées. Le champ doit être l'une des 11 clés d'intervention. Convertis la valeur dans l'unité de la clé et normalise le statut. N'invente pas d'autres corrections.
10. Pour un avis d'annulation : "cancels" = liste des références annulées.
11. Si le document est un rapport qui "annule et remplace"/"supersedes" un autre rapport, mets la référence de l'ancien rapport dans "supersedes".
12. N'invente JAMAIS de valeur. Une valeur absente est null."""


_DEBIT_PATTERNS = [
    r"(?:l['’]équipement|la machine|le doseur|l['’]installation|il|elle)\s+débite\s+alors\s+([\d\s.,'’]+)\s*(l/h|l/min|ml/s|ml/min|cl/min|m3/h)",
    r"(?:the\s+)?(?:equipment|machine|pump|filler)\s+then\s+deliver(?:s|ing)?\s+([\d.,'’]+)\s*(l/h|l/min|ml/s|ml/min|cl/min|m3/h)",
    r"(?:débit|débit volumique|cadence(?:\s+volumique)?)[^\n]{0,60}?après\s+réglage[^\n]{0,30}?[:=]?\s*([\d\s.,'’]+)\s*(l/h|l/min|ml/s|ml/min|cl/min|m3/h)",
    r"(?:flow\s+rate|throughput|delivery\s+rate)[^\n]{0,40}?as\s+left[^\n]{0,25}?[:=]?\s*([\d.,'’]+)\s*(l/h|l/min|ml/s|ml/min|cl/min|m3/h)",
    r"(?:l['’]équipement|la machine|it|the\s+machine)[^\n]{0,20}?(?:débite|délivre)[^\n]{0,15}?([\d\s.,'’]+)\s*(l/h|l/min|ml/s|ml/min|cl/min)",
]

_PRESSURE_PATTERNS = [
    r"(?:la\s+)?pression\s+s['’]est\s+stabilisée\s+(?:à|a)\s*([\d\s.,'’]+)\s*(bar|kpa|mbar|psi)",
    r"(?:pressure|pression)[^\n]{0,40}?(?:settled|stabilisée|stabilise)[^\n]{0,20}?(?:at|à|a)\s*([\d\s.,'’]+)\s*(bar|kpa|mbar|psi)",
    r"(?:pression(?:\s+ligne)?|pressure)[^\n]{0,40}?après\s+réglage[^\n]{0,20}?[:=]?\s*([\d\s.,'’]+)\s*(bar|kpa|mbar|psi)",
    r"(?:operating\s+pressure|pressure|pression)[^\n]{0,30}?as\s+left[^\n]{0,20}?[:=]?\s*([\d.,'’]+)\s*(bar|kpa|mbar|psi)",
]

_TECH_PATTERNS = [
    r"(?:chargé\s+d['’]intervention|chargé\s+de\s+l['’]intervention)\s*[:=]\s*([A-ZÀ-Ý][^\n,;]{1,60})",
    r"(?:lead\s+engineer|lead\s+technician|technicien\s+responsable|intervenant\s+principal|responsable\s+technicien)\s*[:=]\s*([A-ZÀ-Ý][^\n,;]{1,60})",
    r"(?:for\s+the\s+record|note|information\s+complémentaire|pour\s+mémoire|à\s+noter)[^\n]{0,30}?(?:technicien\s+responsable|lead\s+engineer|lead\s+technician)\s*[:=]\s*([A-ZÀ-Ý][^\n,;]{1,60})",
]


def _first_match(patterns, text):
    import re
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            yield m.group(1), m.group(2) if m.lastindex and m.lastindex >= 2 else ""


def _apply_fallbacks(obj: dict, text: str) -> dict:
    from consolidation import parse_number
    it = obj.get("intervention") or {}
    if obj.get("type") != "report":
        return obj

    if it.get("debit_ml_min") is None:
        for val, unit in _first_match(_DEBIT_PATTERNS, text):
            n = parse_number(f"{val} {unit}", "debit_ml_min")
            if n is not None:
                it["debit_ml_min"] = round(n, 4)
                break

    if it.get("pression_bar") is None:
        for val, unit in _first_match(_PRESSURE_PATTERNS, text):
            n = parse_number(f"{val} {unit}", "pression_bar")
            if n is not None:
                it["pression_bar"] = round(n, 6)
                break

    if not it.get("technicien"):
        for val, _ in _first_match(_TECH_PATTERNS, text):
            v = re.split(r"\s*(?:Approbation|Approval|Customer|Client|Date|Visa|Signature|T[eé]l|Email|Mail)\b", val, flags=re.I)[0]
            v = v.strip().rstrip(".")
            if v:
                it["technicien"] = v
                break

    obj["intervention"] = it
    return obj


def _call(messages: list[dict], max_tokens: int = 20000) -> str:
    base = os.environ["BANC_MODELE_URL"].rstrip("/")
    url = base + "/v1/chat/completions"
    body = {
        "model": os.environ["BANC_MODELE"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ["BANC_CLE_MODELE"],
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        rep = json.loads(r.read())
    return rep["choices"][0]["message"].get("content") or ""


def _parse_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    start = t.find("{")
    end = t.rfind("}")
    if start >= 0 and end > start:
        t = t[start : end + 1]
    return json.loads(t)


def extract_piece(pdf_path: str) -> dict:
    doc = pymupdf.open(pdf_path)
    texts = []
    images = []
    for i, page in enumerate(doc):
        texts.append(f"===== PAGE {i + 1} =====\n{page.get_text()}")
        pix = page.get_pixmap(dpi=140)
        images.append(base64.b64encode(pix.tobytes("png")).decode())

    content = [{"type": "text", "text": PROMPT + "\n\nTEXTE EXTRAIT:\n" + "\n".join(texts)}]
    for j, img in enumerate(images):
        content.append({"type": "text", "text": f"IMAGE PAGE {j + 1}:"})
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + img}})

    last_err = None
    for attempt in range(4):
        try:
            obj = _parse_json(_call([{"role": "user", "content": content}]))
            return _apply_fallbacks(obj, "\n".join(texts))
        except Exception as e:  # network, JSON, empty content
            last_err = e
            time.sleep(2 + attempt * 3)

    # Fallback text-only if the multimodal call keeps failing.
    text_content = PROMPT + "\n\nTEXTE EXTRAIT:\n" + "\n".join(texts)
    for attempt in range(2):
        try:
            obj = _parse_json(_call([{"role": "user", "content": text_content}]))
            return _apply_fallbacks(obj, "\n".join(texts))
        except Exception as e:
            last_err = e
            time.sleep(2)
    raise RuntimeError(f"extraction failed for {pdf_path}: {last_err!r}")
