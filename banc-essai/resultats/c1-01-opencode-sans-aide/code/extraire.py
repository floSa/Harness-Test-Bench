#!/usr/bin/env python3
"""Extraction des 15 champs des rapports d'intervention (PDF -> JSON).

Usage: extraire.py {entree} {sortie}
"""
import base64
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pymupdf

KEYS = [
    "machine", "constructeur", "numero_serie", "site", "reference_rapport",
    "date_intervention", "date_validation", "volume_dose_ml", "volume_nominal_ml",
    "tolerance_ml", "debit_ml_min", "pression_bar", "reference_piece",
    "technicien", "statut",
]

DATE_KEYS = {"date_intervention", "date_validation"}
NUM_KEYS = {"volume_dose_ml", "volume_nominal_ml", "tolerance_ml",
            "debit_ml_min", "pression_bar"}

PROMPT = r"""Tu extrais des données d'un rapport d'intervention (équipement de dosage). Les images de toutes les pages sont fournies, ainsi que le texte brut. Lis ATTENTIVEMENT les images, y compris les textes dessinés/dans les schémas, les plaques moteur, les tampons, les signatures et les notes ; le texte brut peut en manquer.

Rends UNIQUEMENT un objet JSON valide avec exactement ces 15 clés:
machine, constructeur, numero_serie, site, reference_rapport, date_intervention, date_validation, volume_dose_ml, volume_nominal_ml, tolerance_ml, debit_ml_min, pression_bar, reference_piece, technicien, statut.

Règles précises:
- machine = modèle de l'ÉQUIPEMENT CONTRÔLÉ ("Equipment", "Machine", "Équipement", "Désignation"...). PAS le moteur d'entraînement, PAS un convoyeur amont, PAS un instrument. Si le champ vaut —/n.c./n/a/vide, cherche le modèle dans le texte (ex. "l'équipement de dosage ... Saruldor 85", "la pompe/l'pipette ... X 85") ou une note ("machine : X").
- constructeur = fabricant de l'ÉQUIPEMENT CONTRÔLÉ. PAS la marque du moteur d'entraînement (souvent différente), PAS un instrument, PAS un convoyeur. Champs possibles: Manufacturer, Constructeur, Marque, Brand, OEM, FABRICANT. Une note "manufacturer: X"/"sortie des ateliers X" peut le donner. Recopie l'orthographe exacte, sans la corriger. Absent => null.
- numero_serie = n° de série de l'ÉQUIPEMENT (pas l'inventaire, pas la plaque du moteur). Peut être dans une note ("N° de série : ..."), le texte ("plate reads ..."), ou un schéma. —/plate missing/illisible/n.c. => null.
- site = site/lieu/établissement du CLIENT où l'équipement est installé (PAS le siège). Recopie la valeur TELLE QU'ÉCRITE avec son préfixe éventuel: "Usine de Cholet", "Établissement d'Issoire", "Plateforme de Guingamp", "Kendal Facility", etc. Champs: Site, Établissement, Lieu d'intervention, Location, Plant, Implantation. Si absent/—, cherche une note ("lieu d'intervention : X") ou "déplacement chez le client, X" / "The visit to the customer, X". Si vraiment absent: null.
- reference_rapport = référence du rapport en vigueur (celle du document; PAS "annule et remplace"/supersedes).
- date_intervention = date réelle de l'intervention. Champs: Date d'intervention, Date of intervention, Date de passage, Service date. Si —/n.c./n/a, cherche une note ou le texte ("a eu lieu le ...", "visit took place on ...", "Date d'intervention: ..."). Format AAAA-MM-JJ.
- date_validation = date de l'approbation FINALE du rapport. Sources: "Date de validation", "Validation date", "Date d'approbation", "Approval date", "approved ... on", "approuvé ... le", date de la colonne "Approuvé par" du tableau des visas, ou TAMPON "APPROVED" (souvent dessiné sur la dernière page ou la 1re). "Relu le/reviewed on/Relu" seul n'est PAS une validation. Si aucune approbation datée: null. Format AAAA-MM-JJ.
- volume_dose_ml = volume de dose MOYEN mesuré APRÈS réglage. IMPORTANT: si les essais après réglage E1/E2/E3 sont donnés, calcule leur moyenne toi-même (ne fais pas confiance à une "moyenne après" imprimée qui peut être fausse/incohérente). Sinon utilise "moyenne après"/"mean as left", une note/diagramme "volume ... après réglage"/"as left", ou le texte "s'est stabilisée autour de ...". Convertis µL, L, cm³, cl en ml. Si seule la valeur "avant réglage"/"as found" existe, ne la prends pas: null.
- volume_nominal_ml = volume de CONSIGNE/nominal de l'équipement: "Volume nominal", "Nominal volume", "Volume de consigne", "Contenance" si c'est la consigne, ou texte "la valeur visée ... est de X". Convertis µL/L/cm³/cl en ml. Ne confonds pas avec une mesure.
- tolerance_ml = tolérance admise sur le volume de dose, en ml: "± 0,25 cm³", "± 125 µL", "Tol. ±2 %". Un pourcentage s'applique au volume nominal (ex. ±2 % de 5 ml = 0,1 ml). Si non mentionnée: null.
- debit_ml_min = débit MESURÉ APRÈS réglage, en ml/min. Sources: "Débit après réglage", "Flow rate as left", note "débit ... après réglage", schéma, ou texte "L'équipement débite alors X" / "delivers X". Convertir: L/h ×1000/60; L/min ×1000; ml/s ×60; ml/h /60. Ne prends PAS le débit maximal, le débit avant réglage, ni le débit d'un convoyeur amont. Si absent/n.m./—/n.c.: null.
- pression_bar = pression de service MESURÉE APRÈS réglage, en bar. Sources: "Pression de service après réglage", "Operating pressure as left", note/schéma ("Operating pressure as left: 0.2 bar"), ou texte "La pression s'est stabilisée à X". Convertir psi /14.5038, kPa /100, mbar /1000, MPa ×10. Ne prends PAS la pression maximale admissible, le tarage de la soupape, la pression avant réglage, ni celle d'un convoyeur. Si absent: null.
- reference_piece = référence de la pièce RÉELLEMENT REMPLACÉE pendant l'intervention: action "remplacée/replaced" dans le tableau des pièces, ou texte "a été remplacé par un élément neuf portant la référence X", ou note "part reference of the replaced part: X". PAS une pièce inspectée/conservée, commandée non posée, proposée au devis/quoted. Si aucune pièce remplacée: null.
- technicien = technicien RESPONSABLE de l'intervention côté prestataire. Sources fiables: "Technicien responsable", "Lead technician", "Intervenant principal", "Chargé d'intervention", "Responsible technician", "X (responsable)", "X (lead)", ou texte "X a conduit/led the visit/intervention". IGNORE totalement les noms après "à la demande de"/"at the request of", et ceux qui "ont participé/took part/assisté/accompagné/avec l'appui/support of/assistant/accompagnant". Si aucun rôle responsable explicite: null (même si un nom apparaît ailleurs).
- statut = décision FINALE sur l'équipement: "conforme", "non_conforme" ou "a_revoir". Traduire Compliant/Satisfactory=>conforme; Non-compliant=>non_conforme; To be reviewed/À revoir=>a_revoir. Regarde le statut/conclusion final, les cases cochées, le tampon. Ne prends PAS le statut d'arrivée ("On arrival..."). Si aucun statut final explicite, déduis de la conclusion: "peut être remis en production sans réserve"/"may return to production without reserve" => conforme; "sous réserve d'une nouvelle visite rapprochée"/"subject to an early follow-up" => a_revoir; "ne doit pas être remis en production"/"must not return to production" => non_conforme. Si vraiment indéterminable: null.

Dates au format AAAA-MM-JJ. Nombres en nombres JSON (pas de chaînes), unités converties. Absent => null. Ne rends AUCUN commentaire, aucun texte hors du JSON.
"""


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn")


def norm(s):
    if s is None:
        return ""
    s = strip_accents(s).lower().replace("’", "'").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip()


def is_blank(v):
    return v is None or norm(v) in {
        "", "-", "--", "—", "n/a", "n.c.", "nc", "n.m.", "nm", "non communique",
        "non communiquee", "plate missing", "plaque manquante", "illisible",
        "inconnu", "unknown", "none", "null",
    }


def parse_number(s):
    if s is None:
        return None
    s = str(s).strip().replace("\u00a0", " ").replace("'", "").replace("’", "").replace(" ", "")
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) == 3 and 1 <= len(parts[0]) <= 3:
            s = s.replace(",", "")  # thousands separator
        else:
            s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def convert_num(value, unit):
    unit = norm(unit)
    if unit in ("ml", "millilitre", "millilitres", "cm3", "cm³", "cc"):
        return value
    if unit in ("µl", "μl", "ul", "microlitre", "microlitres"):
        return value / 1000.0
    if unit in ("l", "litre", "litres"):
        return value * 1000.0
    if unit in ("cl", "centilitre", "centilitres"):
        return value * 10.0
    if unit in ("ml/min", "ml / min"):
        return value
    if unit in ("l/h", "l / h", "lh"):
        return value * 1000.0 / 60.0
    if unit in ("l/min", "l / min"):
        return value * 1000.0
    if unit in ("ml/s", "ml / s"):
        return value * 60.0
    if unit in ("ml/h", "ml / h"):
        return value / 60.0
    if unit == "bar":
        return value
    if unit == "psi":
        return value / 14.5037738
    if unit == "kpa":
        return value / 100.0
    if unit == "mbar":
        return value / 1000.0
    if unit == "mpa":
        return value * 10.0
    return None


MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12, "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}


def to_iso_date(value):
    if value is None:
        return None
    s = str(value).strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = map(int, m.groups())
        return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", s)
    if m:
        d, mo, y = map(int, m.groups())
        if y < 100:
            y += 2000
        return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.fullmatch(r"(\d{1,2})(?:er)?\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})", s)
    if m:
        d = int(m.group(1)); mo = MONTHS.get(strip_accents(m.group(2)).lower()); y = int(m.group(3))
        if mo:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.fullmatch(r"([A-Za-zÀ-ÿ]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m:
        mo = MONTHS.get(strip_accents(m.group(1)).lower()); d = int(m.group(2)); y = int(m.group(3))
        if mo:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.fullmatch(r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+),?\s+(\d{4})", s)
    if m:
        d = int(m.group(1)); mo = MONTHS.get(strip_accents(m.group(2)).lower()); y = int(m.group(3))
        if mo:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


def clean_date(value):
    if value is None or is_blank(value):
        return None
    iso = to_iso_date(value)
    return iso


def map_status(value):
    if value is None:
        return None
    s = norm(value)
    if not s or is_blank(value):
        return None
    if "non" in s and ("conforme" in s or "compliant" in s):
        return "non_conforme"
    if "revoir" in s or "review" in s or "follow" in s or "reserve" in s:
        return "a_revoir"
    if "conforme" in s or "compliant" in s or "satisfactory" in s:
        return "conforme"
    return None


def lines_of(text):
    return [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]


LABEL_WORDS = {norm(x) for x in [
    "équipement", "equipment", "machine", "constructeur", "manufacturer",
    "marque", "brand", "oem", "fabricant", "n° de série", "n° de serie",
    "serial number", "s/n", "numéro de série", "site", "établissement",
    "etablissement", "lieu d'intervention", "location", "plant", "implantation",
    "installation", "référence du rapport", "reference du rapport",
    "report reference", "n° de compte rendu", "document no.", "date d'intervention",
    "date of intervention", "date de passage", "service date", "date de validation",
    "validation date", "date d'approbation", "approval date", "volume nominal",
    "nominal volume", "volume de consigne", "tolérance", "tolerance", "objet",
    "client", "n° de commande", "n° d'affaire", "n° d'inventaire", "page",
    "visas", "rédigé par", "vérifié par", "approuvé par", "date", "nom",
]}


def field_from_lines(text, labels, max_next=2):
    """Cherche 'Label : valeur' ou 'Label' suivi de la valeur sur la ligne suivante."""
    lines = lines_of(text)
    nlabels = [norm(l).rstrip(":") for l in labels]
    for i, line in enumerate(lines):
        nline = norm(line)
        for label in nlabels:
            if nline == label or nline.rstrip(":") == label:
                for j in range(i + 1, min(len(lines), i + 1 + max_next)):
                    cand = lines[j].strip(" :")
                    if not cand or is_blank(cand):
                        continue
                    ncand = norm(cand).rstrip(":")
                    if ncand in LABEL_WORDS:
                        return None
                    if len(cand) <= 45 and cand.upper() == cand and re.fullmatch(r"[A-ZÀ-Ý0-9 .'’/-]+", cand):
                        return None
                    return cand
                return None
            if nline.startswith(label + " :") or nline.startswith(label + ":"):
                cand = line.split(":", 1)[1].strip()
                if cand and not is_blank(cand):
                    return cand
    return None


def first_regex(text, patterns, flags=re.I):
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            return m.group(1).strip()
    return None


def deterministic_fields(text):
    t = text
    d = {}
    # machine
    v = field_from_lines(t, ["Équipement", "Equipment", "Machine", "MACHINE",
                             "Désignation", "DESIGNATION", "ÉQUIPEMENT"])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:pour mémoire|for the record|note|à noter)[^\n]{0,25}(?:machine|équipement|equipment)\s*:\s*([^\n.]+)",
            r"(?:l'équipement de dosage|la pompe doseuse|la pipette|the dosing equipment|the pump|the pipette)[^\n.]{0,50}?\b([A-Z][\w-]+\s+\d{2,4})\b",
            r"(?:utilise|concerns)\s+(?:la|le|the)?\s*(?:pompe|pipette|remplisseuse|doseuse)?[^\n.]{0,25}?\b([A-Z][\w-]+\s+\d{2,4})\b",
        ])
    if not is_blank(v):
        d["machine"] = v
    # constructeur
    v = field_from_lines(t, ["Constructeur", "Manufacturer", "Marque", "Brand",
                             "FABRICANT", "OEM", "CONSTRUCTEUR"])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:for the record|pour mémoire|note|à noter)[^\n]{0,30}manufacturer\s*:\s*([^\n.]+)",
            r"(?:sortie des ateliers|sorti des ateliers|made by)\s+([A-Z][\w-]+)",
        ])
    if not is_blank(v):
        d["constructeur"] = v
    # serial
    v = field_from_lines(t, ["N° de série", "N° DE SÉRIE", "Serial number",
                             "SERIAL NUMBER", "S/N", "Numéro de série"])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:plate reads|plaque (?:signalétique )?(?:indique|porte))\s*([A-Z0-9][A-Z0-9./-]{4,})",
            r"(?:à noter|pour mémoire|note|for the record)[^\n]{0,25}(?:n° de série|serial)\s*:\s*([A-Z0-9][A-Z0-9./-]{4,})",
        ])
    if not is_blank(v):
        d["numero_serie"] = v
    # site
    v = field_from_lines(t, ["Site", "Établissement", "Lieu d'intervention",
                             "Location", "Plant", "PLANT", "Implantation", "SITE"])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:lieu d'intervention|site)\s*:\s*([^\n.]+)",
            r"(?:déplacement chez le client|visite chez le client|the visit to the customer)[,\s]+([^\n,.;]+)",
        ])
    if not is_blank(v):
        d["site"] = v
    # reference
    v = field_from_lines(t, ["Référence du rapport", "RÉFÉRENCE DU RAPPORT",
                             "Report reference", "REPORT REFERENCE",
                             "N° de compte rendu", "N° DE COMPTE RENDU",
                             "Document no.", "Document ref.", "Report no."])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:référence du rapport|report reference|n° de compte rendu)\s*:?\s*([A-Z]{2,4}-[A-Z]{2}-\d{4}-\d{3,5})",
            r"(?:pour mémoire|note|for the record)[^\n]{0,25}n° de document\s*:\s*([A-Z]{2,4}-[A-Z]{2}-\d{4}-\d{3,5})",
        ])
    if not is_blank(v):
        d["reference_rapport"] = v
    # dates
    v = field_from_lines(t, ["Date d'intervention", "Date of intervention",
                             "Date de passage", "Service date", "DATE D'INTERVENTION",
                             "DATE OF INTERVENTION"])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:l'intervention|l'intervention a eu lieu|le déplacement a eu lieu|the visit took place|the visit to the customer)[^\n]{0,80}?(?:le|on)\s+(\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})",
            r"(?:à noter|note|for the record|information complémentaire)[^\n]{0,30}date d'intervention\s*:\s*([^\n.]+)",
        ])
    iso = clean_date(v)
    if iso:
        d["date_intervention"] = iso
    v = field_from_lines(t, ["Date de validation", "Validation date",
                             "Date d'approbation", "Approval date",
                             "DATE DE VALIDATION", "Approuvé le", "Approved on"])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:date de validation|validation date|date d'approbation|approval date)\s*:\s*([^\n.]+)",
            r"(?:approuvé par|approved by)[^\n.]{0,80}?\s+le\s+(\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})",
            r"(?:approuvé par|approved by)[^\n.]{0,80}?\s+on\s+(\d{1,2}\s+[A-Za-zÀ-ÿ]+,?\s+\d{4})",
        ])
    iso = clean_date(v)
    if iso:
        d["date_validation"] = iso
    # volume nominal
    v = field_from_lines(t, ["Volume nominal", "Nominal volume", "Volume de consigne",
                             "VOLUME DE CONSIGNE", "VOLUME NOMINAL"])
    if is_blank(v):
        v = first_regex(t, [
            r"(?:volume nominal|nominal volume|volume de consigne)\s*:\s*([0-9][0-9\s.,'’]*\s*(?:µl|μl|ul|ml|l|cl|cm3|cm³))",
            r"(?:la valeur visée par le client est de|the customer's target value is)\s*([0-9][0-9\s.,'’]*\s*(?:µl|μl|ul|ml|l|cl|cm3|cm³))",
        ])
    if v:
        m = re.match(r"([0-9][0-9\s.,'’]*)\s*(µl|μl|ul|ml|l|cl|cm3|cm³)", v, re.I)
        n = parse_number(m.group(1)) if m else None
        c = convert_num(n, m.group(2)) if n is not None else None
        if c is not None:
            d["volume_nominal_ml"] = c
    # tolerance
    v = first_regex(t, [
        r"(?:tolérance|tolerance|tol\.)\s*(?:admise)?\s*:?\s*(±\s*[0-9][0-9\s.,'’]*\s*(?:%|µl|μl|ul|ml|l|cl|cm3|cm³))",
        r"(?:l'écart admis par le cahier des charges du client est de|the deviation allowed by the customer's specification is)\s*(±\s*[0-9][0-9\s.,'’]*\s*(?:%|µl|μl|ul|ml|l|cl|cm3|cm³))",
    ])
    if v:
        m = re.match(r"±\s*([0-9][0-9\s.,'’]*)\s*(%|µl|μl|ul|ml|l|cl|cm3|cm³)", v, re.I)
        if m:
            n = parse_number(m.group(1)); unit = m.group(2)
            if n is not None:
                if unit == "%":
                    nom = d.get("volume_nominal_ml")
                    if nom is not None:
                        d["tolerance_ml"] = nom * n / 100.0
                else:
                    c = convert_num(n, unit)
                    if c is not None:
                        d["tolerance_ml"] = c
    # volume dose fallback
    v = first_regex(t, [
        r"(?:volume(?: de dose)?|contenance|dose volume|delivered volume|fill volume)[^\n:]{0,35}(?:après réglage|as left)\s*:\s*([0-9][0-9\s.,'’]*\s*(?:µl|μl|ul|ml|l|cl|cm3|cm³))",
        r"(?:quantité délivrée|delivered quantity|dose volume)[^\n.]{0,60}?s'est stabilisée autour de\s*([0-9][0-9\s.,'’]*\s*(?:µl|μl|ul|ml|l|cl|cm3|cm³))",
        r"(?:quantité délivrée|delivered quantity|dose volume)[^\n.]{0,60}?settled at\s*([0-9][0-9\s.,'’]*\s*(?:µl|μl|ul|ml|l|cl|cm3|cm³))",
    ])
    if v:
        m = re.match(r"([0-9][0-9\s.,'’]*)\s*(µl|μl|ul|ml|l|cl|cm3|cm³)", v, re.I)
        n = parse_number(m.group(1)) if m else None
        c = convert_num(n, m.group(2)) if n is not None else None
        if c is not None:
            d["volume_dose_ml"] = c
    # reference piece fallback
    v = first_regex(t, [
        r"(?:référence pièce de la pièce remplacée|part reference of the replaced part|référence de la pièce remplacée)\s*:\s*([A-Z0-9][A-Z0-9./-]{3,})",
        r"(?:remplacé par un élément neuf portant la référence|replaced (?:by|with) (?:a )?new (?:item|part)[^.]{0,30}(?:reference|référence))\s*([A-Z0-9][A-Z0-9./-]{3,})",
    ])
    if not is_blank(v):
        d["reference_piece"] = v
    # technician fallback
    v = first_regex(t, [
        r"(?:technicien responsable|lead technician|intervenant principal|chargé d'intervention|responsible technician|technicien)\s*:\s*([A-ZÀ-Ý][^\n:;]{2,60})",
        r"(?:pour mémoire|note|for the record|information complémentaire)[^\n]{0,30}(?:technicien responsable|responsible technician)\s*:\s*([A-ZÀ-Ý][^\n:;]{2,60})",
    ])
    if not is_blank(v):
        d["technicien"] = v.strip(" .")
    # status fallback
    v = first_regex(t, [
        r"(?:statut|status|décision|decision|verdict|outcome)\s*:?\s*(conforme|non[- ]conforme|à revoir|a revoir|compliant|non[- ]compliant|to be reviewed|satisfactory)",
        r"(?:à noter|note|pour mémoire|for the record|information complémentaire)[^\n]{0,25}(?:statut|status|verdict)\s*:\s*([^\n.]+)",
    ])
    st = map_status(v)
    if st:
        d["statut"] = st
    return d


def text_postprocess(text, pred):
    t = text
    # debit fallback
    if pred.get("debit_ml_min") is None:
        pats = [
            r"(?:d[ée]bit(?:\s+volum[ée]trique)?[^\n:]{0,40}apr[èe]s r[ée]glage\s*:?\s*)([0-9][0-9\s.,'’]*)\s*(ml/min|mL/min|L/h|l/h|ml/s|mL/s|L/min|l/min)",
            r"(?:flow rate[^\n:]{0,30}(?:as left|after adjustment)\s*:?\s*)([0-9][0-9\s.,'’-]*)\s*(ml/min|mL/min|L/h|l/h|ml/s|mL/s|L/min|l/min)",
            r"(?:l'[ée]quipement\s+d[ée]bite\s+alors|the equipment (?:then )?delivers)\s*([0-9][0-9\s.,'’]*)\s*(ml/min|mL/min|L/h|l/h|ml/s|mL/s|L/min|l/min)",
        ]
        for p in pats:
            m = re.search(p, t, re.I)
            if m:
                n = parse_number(m.group(1))
                v = convert_num(n, m.group(2)) if n is not None else None
                if v is not None:
                    pred["debit_ml_min"] = round(v, 4)
                    break
    # pressure fallback
    if pred.get("pression_bar") is None:
        pats = [
            r"pression(?: de service)?\s+s'est stabilis[ée]e\s+[àa]\s*([0-9][0-9\s.,'’]*)\s*(bar|psi|mbar|kPa|MPa)",
            r"pressure (?:settled|stabilised|stabilized) at\s*([0-9][0-9\s.,'’]*)\s*(bar|psi|mbar|kPa|MPa)",
            r"(?:pression(?: de service)?[^\n:]{0,30}apr[èe]s r[ée]glage\s*:?\s*)([0-9][0-9\s.,'’]*)\s*(bar|psi|mbar|kPa|MPa)",
            r"(?:operating pressure[^\n:]{0,25}(?:as left|after adjustment)\s*:?\s*)([0-9][0-9\s.,'’]*)\s*(bar|psi|mbar|kPa|MPa)",
        ]
        for p in pats:
            m = re.search(p, t, re.I)
            if m:
                n = parse_number(m.group(1))
                v = convert_num(n, m.group(2)) if n is not None else None
                if v is not None:
                    pred["pression_bar"] = round(v, 4)
                    break
    # site correction: full prefix if model gave only the city
    site = pred.get("site")
    if isinstance(site, str) and site.strip():
        ns = norm(site)
        if re.search(r"^(line|ligne|pompe|doseuse|remplisseuse|pipette|filler|pump|machine|installation)\b", ns):
            pred["site"] = None
        elif not (re.match(r"^(usine|etablissement|plateforme|centre|site)\b", ns)
                  or re.search(r"\b(facility|plant|works|site)$", ns)):
            for m in re.finditer(r"\b(?:Usine|Établissement|Etablissement|Plateforme|Centre)\s+(?:(?:de|des|du)\s+|d['’])?[A-ZÀ-Ý][^\n,.;:]{1,60}", t):
                full = m.group(0).strip(" .,:;")
                if norm(site) and norm(site) in norm(full) and norm(full) != norm(site):
                    pred["site"] = full
                    break
            else:
                for m in re.finditer(r"\b[A-ZÀ-Ý][\w'’-]+(?:\s+[A-ZÀ-Ý][\w'’-]+){0,2}\s+(?:Facility|Plant|Works)\b", t):
                    full = m.group(0).strip(" .,:;")
                    if norm(site) and norm(site) in norm(full) and norm(full) != norm(site):
                        pred["site"] = full
                        break
    # serial O/0 heuristic
    s = pred.get("numero_serie")
    if isinstance(s, str):
        m = re.match(r"^([A-Z])0(\d{4,})$", s.strip())
        if m:
            pred["numero_serie"] = m.group(1) + "O" + m.group(2)
    return pred


def coerce_output(pred):
    out = {}
    for k in KEYS:
        v = pred.get(k) if isinstance(pred, dict) else None
        if k in DATE_KEYS:
            out[k] = clean_date(v)
        elif k in NUM_KEYS:
            if v is None or isinstance(v, bool):
                out[k] = None
            else:
                n = parse_number(v)
                out[k] = n
        elif k == "statut":
            out[k] = map_status(v)
        else:
            if v is None or is_blank(v):
                out[k] = None
            else:
                out[k] = re.sub(r"\s+", " ", str(v)).strip()
    return out


def call_model(pdf_path):
    d = pymupdf.open(pdf_path)
    images = []
    for page in d:
        pix = page.get_pixmap(dpi=130)
        images.append(base64.b64encode(pix.tobytes("png")).decode())
    text = "\n".join(page.get_text() for page in d)
    content = [{"type": "text", "text": PROMPT}]
    for b in images:
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + b}})
    content.append({"type": "text", "text": "TEXTE BRUT (peut manquer des éléments dessinés):\n" + text})

    url = os.environ["BANC_MODELE_URL"].rstrip("/") + "/v1/chat/completions"
    key = os.environ["BANC_CLE_MODELE"]
    model = os.environ["BANC_MODELE"]
    last_err = None
    for attempt in range(3):
        body = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 8000 if attempt < 2 else 12000,
            "temperature": 0,
        }
        try:
            req = urllib.request.Request(
                url, data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + key})
            with urllib.request.urlopen(req, timeout=300) as r:
                rep = json.load(r)
            msg = rep["choices"][0]["message"]
            c = msg.get("content")
            if c:
                m = re.search(r"\{.*\}", c, re.S)
                if m:
                    obj = json.loads(m.group(0))
                    if isinstance(obj, dict):
                        return obj, text
        except Exception as e:
            last_err = e
        time.sleep(2 + attempt * 2)
    return None, text


def deterministic_only(text):
    return deterministic_fields(text)


def process_one(pdf_path, out_dir):
    stem = Path(pdf_path).stem
    pred, text = call_model(pdf_path)
    if pred is None:
        pred = dict(deterministic_fields(text))
    else:
        pred = text_postprocess(text, pred)
    out = coerce_output(pred)
    (Path(out_dir) / (stem + ".json")).write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return stem, out


def main():
    if len(sys.argv) != 3:
        print("Usage: extraire.py {entree} {sortie}", file=sys.stderr)
        return 2
    entree, sortie = Path(sys.argv[1]), Path(sys.argv[2])
    sortie.mkdir(parents=True, exist_ok=True)
    files = sorted(entree.glob("*.pdf"))
    if not files:
        print("Aucun PDF dans " + str(entree), file=sys.stderr)
        return 1
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(process_one, f, sortie): f for f in files}
        for fu in as_completed(futs):
            f = futs[fu]
            try:
                fu.result()
                print("OK " + f.name, flush=True)
            except Exception as e:
                print("ERREUR " + f.name + " : " + repr(e), file=sys.stderr, flush=True)
                text = ""
                try:
                    text = "\n".join(p.get_text() for p in pymupdf.open(f))
                except Exception:
                    pass
                out = coerce_output(deterministic_only(text))
                (sortie / (f.stem + ".json")).write_text(
                    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
