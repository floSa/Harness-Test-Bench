from __future__ import annotations

import os
import re
import unicodedata
from collections import Counter

FIELDS = [
    "reference_rapport",
    "date_intervention",
    "date_validation",
    "volume_dose_ml",
    "volume_nominal_ml",
    "tolerance_ml",
    "debit_ml_min",
    "pression_bar",
    "reference_piece",
    "technicien",
    "statut",
]

NUM_FIELDS = {"volume_dose_ml", "volume_nominal_ml", "tolerance_ml", "debit_ml_min", "pression_bar"}

FIELD_ALIASES = {
    "pression": "pression_bar",
    "pression_service": "pression_bar",
    "pression_de_service": "pression_bar",
    "debit": "debit_ml_min",
    "debit_volumique": "debit_ml_min",
    "volume": "volume_dose_ml",
    "volume_dose": "volume_dose_ml",
    "volume_de_dose": "volume_dose_ml",
    "volume_dose_moyen": "volume_dose_ml",
    "volume_nominal": "volume_nominal_ml",
    "consigne": "volume_nominal_ml",
    "tolerance": "tolerance_ml",
    "piece": "reference_piece",
    "reference_piece_remplacee": "reference_piece",
    "technicien_responsable": "technicien",
    "status": "statut",
    "date_de_validation": "date_validation",
    "date_d_intervention": "date_intervention",
    "reference": "reference_rapport",
    "reference_du_rapport": "reference_rapport",
}

MONTHS = {
    "janvier": 1, "january": 1, "jan": 1,
    "fevrier": 2, "février": 2, "february": 2, "feb": 2, "fev": 2,
    "mars": 3, "march": 3, "mar": 3,
    "avril": 4, "april": 4, "apr": 4,
    "mai": 5, "may": 5,
    "juin": 6, "june": 6, "jun": 6,
    "juillet": 7, "july": 7, "jul": 7,
    "aout": 8, "août": 8, "august": 8, "aug": 8,
    "septembre": 9, "september": 9, "sep": 9, "sept": 9,
    "octobre": 10, "october": 10, "oct": 10,
    "novembre": 11, "november": 11, "nov": 11,
    "decembre": 12, "décembre": 12, "december": 12, "dec": 12,
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def canon_serial(s):
    if not s:
        return None
    s = strip_accents(str(s)).upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s.replace("O", "0").replace("I", "1").replace("L", "1")


def clean_machine(m):
    if not m:
        return None
    s = str(m).strip()
    s = re.sub(r"^(?:ligne|line)\s*\d+\s*[,;:\-]\s*", "", s, flags=re.I)
    generic = (
        r"doseuse volumétrique à piston|doseuse volumétrique|doseuse|"
        r"remplisseuse rotative|remplisseuse|pompe doseuse à membrane|pompe doseuse|"
        r"pipette automatique|piston filler|rotary filling machine|filling machine|"
        r"diaphragm metering pump|machine|équipement|equipment|unit"
    )
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"^(?:" + generic + r")\s+", "", s, flags=re.I)
    s = re.sub(r"\s*;\s*.*$", "", s)
    s = re.sub(r"^(?:the\s+)", "", s, flags=re.I)
    return s.strip() or None


def norm_date(d):
    if not d:
        return None
    s = strip_accents(str(d)).strip().lower()
    s = s.replace("1er", "1").replace("1ère", "1")
    m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        y, mo, da = map(int, m.groups())
        return f"{y:04d}-{mo:02d}-{da:02d}"
    m = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", s)
    if m:
        da, mo, y = m.groups()
        y = int(y)
        y = y + 2000 if y < 100 else y
        return f"{y:04d}-{int(mo):02d}-{int(da):02d}"
    # 25 November 2024 / 25 novembre 2024
    m = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", s)
    if m and m.group(2) in MONTHS:
        da, mon, y = int(m.group(1)), MONTHS[m.group(2)], int(m.group(3))
        return f"{y:04d}-{mon:02d}-{da:02d}"
    # November 25, 2024 / 25 Nov 2024
    m = re.search(r"([a-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m and m.group(1) in MONTHS:
        mon, da, y = MONTHS[m.group(1)], int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mon:02d}-{da:02d}"
    return None


def status_norm(s):
    if not s:
        return None
    t = strip_accents(str(s)).lower().replace("_", " ").replace("-", " ")
    t = re.sub(r"\s+", " ", t)
    if "non" in t and ("conform" in t or "compliant" in t):
        return "non_conforme"
    if "revoir" in t or "review" in t:
        return "a_revoir"
    if "conform" in t or "compliant" in t:
        return "conforme"
    return None


def _unit_convert(value: float, unit: str, kind: str, nominal: float | None = None):
    u = strip_accents(unit or "").lower().replace("³", "3").replace("μ", "u").replace("µ", "u")
    u = re.sub(r"\s+", "", u)
    if not u:
        return value
    if kind in ("volume_dose_ml", "volume_nominal_ml", "tolerance_ml"):
        if "%" in u:
            return value / 100.0 * nominal if nominal else None
        if u.startswith("cl"):
            return value * 10.0
        if u.startswith("ml") or u.startswith("cm3") or u.startswith("cc"):
            return value
        if u.startswith("ul"):
            return value / 1000.0
        if u.startswith("l"):
            return value * 1000.0
    if kind == "debit_ml_min":
        if u.startswith("l/min") or u == "lmn":
            return value * 1000.0
        if u.startswith("l/h") or u.startswith("lh"):
            return value * 1000.0 / 60.0
        if u.startswith("l/s"):
            return value * 60000.0
        if u.startswith("ml/s") or u.startswith("mlsec"):
            return value * 60.0
        if u.startswith("ml/min") or u.startswith("mlmn"):
            return value
        if u.startswith("cl/min"):
            return value * 10.0
    if kind == "pression_bar":
        if u.startswith("kpa"):
            return value / 100.0
        if u.startswith("mbar"):
            return value / 1000.0
        if u.startswith("psi"):
            return value * 0.0689475729
        if u.startswith("pa"):
            return value / 100000.0
        if u.startswith("bar"):
            return value
    return value


def parse_number(v, kind: str, nominal: float | None = None):
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("\u202f", " ").replace("\xa0", " ").replace("−", "-")
    low = strip_accents(s).lower()
    if low in ("", "n.c.", "n.m.", "n/a", "none", "null", "-", "—", "nc", "nm"):
        return None
    m = re.search(r"[-+]?\d[\d\s.,]*", s)
    if not m:
        return None
    numtxt = m.group(0).replace(" ", "")
    if "," in numtxt and "." in numtxt:
        if numtxt.rfind(",") > numtxt.rfind("."):
            numtxt = numtxt.replace(".", "").replace(",", ".")
        else:
            numtxt = numtxt.replace(",", "")
    elif "," in numtxt:
        numtxt = numtxt.replace(",", ".")
    try:
        value = float(numtxt)
    except ValueError:
        return None
    unit = s[m.end():].strip()
    return _unit_convert(value, unit, kind, nominal)


def _canon_field(name) -> str | None:
    n = strip_accents(str(name or "")).lower()
    n = re.sub(r"[^a-z0-9]+", "_", n).strip("_")
    if n in FIELDS:
        return n
    return FIELD_ALIASES.get(n)


def consolidate(pieces: list[dict]) -> dict:
    reports = [p for p in pieces if p.get("type") == "report"]
    for p in reports:
        it = p.setdefault("intervention", {})
        if not it.get("reference_rapport"):
            it["reference_rapport"] = p.get("report_reference")

    serial_counts = Counter()
    for p in reports:
        eq = p.get("equipment") or {}
        s = canon_serial(eq.get("numero_serie") or (p.get("intervention") or {}).get("numero_serie"))
        if s:
            serial_counts[s] += 1
    target_serial = serial_counts.most_common(1)[0][0] if serial_counts else None

    def same_serial(s):
        cs = canon_serial(s)
        if cs is None or target_serial is None:
            return True
        return cs == target_serial

    matching = [p for p in reports if same_serial((p.get("equipment") or {}).get("numero_serie"))] or reports

    mc = Counter()
    for p in matching:
        m = clean_machine((p.get("equipment") or {}).get("machine"))
        if m:
            mc[m] += 1
    machine = mc.most_common(1)[0][0] if mc else None

    cc = Counter()
    for p in matching:
        c = (p.get("equipment") or {}).get("constructeur")
        if c and norm(c) not in ("n.c.", "n.a.", "n/a", "—", "-"):
            cc[str(c).strip()] += 1
    constructeur = cc.most_common(1)[0][0] if cc else None

    sc = Counter()
    for p in matching:
        s = (p.get("equipment") or {}).get("numero_serie")
        if s:
            sc[str(s).strip()] += 1
    if sc:
        cand = [k for k in sc if canon_serial(k) == target_serial] or list(sc)
        raw_serial = max(cand, key=lambda k: (sc[k], k))
    else:
        raw_serial = None

    cancelled = set()
    superseded = set()
    for p in pieces:
        for r in p.get("cancels") or []:
            if r:
                cancelled.add(norm(r))
        for r in p.get("supersedes") or []:
            if r:
                superseded.add(norm(r))

    active = []
    for p in reports:
        it = p.get("intervention") or {}
        ref = norm(it.get("reference_rapport") or p.get("report_reference") or "")
        if ref and (ref in cancelled or ref in superseded):
            continue
        if not same_serial((p.get("equipment") or {}).get("numero_serie")):
            continue
        active.append(p)

    byref = {}
    for p in active:
        it = p.get("intervention") or {}
        ref = norm(it.get("reference_rapport") or p.get("report_reference") or "")
        if ref in byref:
            a = byref[ref].get("intervention") or {}
            b = p.get("intervention") or {}
            if sum(v is not None for v in b.values()) > sum(v is not None for v in a.values()):
                byref[ref] = p
        else:
            byref[ref] = p
    active = list(byref.values())

    corrections = {}
    for p in pieces:
        if p.get("type") == "rectification" and p.get("rectifies"):
            corrections.setdefault(norm(p["rectifies"]), []).extend(p.get("corrections") or [])

    for p in active:
        it = p.setdefault("intervention", {})
        ref = norm(it.get("reference_rapport") or "")
        for corr in corrections.get(ref, []):
            f = _canon_field(corr.get("field"))
            if f not in FIELDS:
                continue
            raw = corr.get("value_normalized")
            if raw is None:
                raw = corr.get("raw")
            if f == "statut":
                it[f] = status_norm(raw)
            elif f.startswith("date"):
                it[f] = norm_date(raw)
            elif f in NUM_FIELDS:
                it[f] = parse_number(raw, f, parse_number(it.get("volume_nominal_ml"), "volume_nominal_ml"))
            else:
                it[f] = str(raw).strip() if raw is not None else None

    for p in active:
        it = p.setdefault("intervention", {})
        nominal = parse_number(it.get("volume_nominal_ml"), "volume_nominal_ml")
        for f in NUM_FIELDS:
            it[f] = parse_number(it.get(f), f, nominal)
        for f in ("date_intervention", "date_validation"):
            it[f] = norm_date(it.get(f))
        it["statut"] = status_norm(it.get("statut")) if it.get("statut") else None
        for f in ("reference_rapport", "reference_piece", "technicien"):
            if it.get(f) is not None:
                it[f] = str(it[f]).strip()

    active.sort(key=lambda p: (p["intervention"].get("date_intervention") or "9999-99-99"))

    sitec = Counter()
    for p in active:
        s = (p.get("equipment") or {}).get("site")
        if s and norm(s) not in ("n.c.", "n.m.", "n/a", "—", "-"):
            sitec[str(s).strip()] += 1
    site = None
    if sitec:
        maxc = max(sitec.values())
        cand = [s for s, c in sitec.items() if c == maxc]
        # On préfère une valeur qui ressemble à un vrai nom de site.
        pref = [s for s in cand if re.search(r"site|usine|établissement|etablissement|plateforme|works|facility", s, re.I)]
        site = max(pref or cand, key=len)

    interventions = []
    for p in active:
        it = p["intervention"]
        interventions.append({f: it.get(f) for f in FIELDS})

    statut_actuel = interventions[-1]["statut"] if interventions else None
    return {
        "machine": machine,
        "constructeur": constructeur,
        "numero_serie": raw_serial,
        "site": site,
        "interventions": interventions,
        "statut_actuel": statut_actuel,
    }
