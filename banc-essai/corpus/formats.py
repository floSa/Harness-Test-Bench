"""Écriture des nombres, unités et dates.

Principe : la vérité terrain est recalculée à partir de ce qui est écrit dans le document
(valeur affichée × facteur de l'unité), jamais l'inverse.
"""
import datetime as dt

# Séparateur décimal, séparateur de milliers.
STYLES_NOMBRE = {
    "fr": (",", " "), "fr_colle": (",", ""), "de": (",", "."),
    "en": (".", ","), "en_colle": (".", ""), "ch": (".", "'"),
}

# Facteur vers l'unité de la clé (ml, ml/min, bar).
# psi : 1 psi = 6,894757 kPa (NIST SP 811, B.8) = 0,06894757 bar.
UNITES = {
    "volume": {"ml": 1, "mL": 1, "cm³": 1, "cc": 1, "µl": 0.001, "µL": 0.001, "ul": 0.001,
               "cl": 10, "L": 1000, "l": 1000},
    "debit": {"ml/min": 1, "mL/min": 1, "L/h": 1000 / 60, "l/h": 1000 / 60, "ml/s": 60,
              "L/min": 1000},
    "pression": {"bar": 1, "mbar": 0.001, "kPa": 0.01, "psi": 0.06894757},
}
FACTEURS_DECIMAUX = {1, 0.001, 10, 1000, 0.01}

MOIS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}


def nombre(x, style, min_dec=0, max_dec=6):
    dec_sep, mil_sep = STYLES_NOMBRE[style]
    dec = min_dec
    while dec < max_dec and abs(round(x, dec) - x) > 1e-9:
        dec += 1
    s = f"{abs(x):,.{dec}f}"
    entier, _, frac = s.partition(".")
    entier = entier.replace(",", mil_sep)
    s = entier + (dec_sep + frac if frac else "")
    return ("-" if x < 0 else "") + s


def convertir(x, grandeur, unite, dec=2):
    """Valeur affichée dans l'unité demandée, et vérité recalculée depuis l'affichage."""
    f = UNITES[grandeur][unite]
    if f in FACTEURS_DECIMAUX:
        affiche = round(x / f, 9)
    else:
        affiche = round(x / f, dec)
    verite = round(affiche * f, 4)
    return affiche, verite


def date(iso, forme):
    d = dt.date.fromisoformat(iso) if isinstance(iso, str) else iso
    if forme == "jj/mm/aaaa":
        return d.strftime("%d/%m/%Y")
    if forme == "aaaa-mm-jj":
        return d.isoformat()
    if forme == "jj.mm.aa":
        return d.strftime("%d.%m.%y")
    if forme == "long_fr":
        jour = "1er" if d.day == 1 else str(d.day)
        return f"{jour} {MOIS['fr'][d.month - 1]} {d.year}"
    if forme == "long_en":
        return f"{d.day} {MOIS['en'][d.month - 1]} {d.year}"
    if forme == "abr_en":
        return f"{d.day} {MOIS['en'][d.month - 1][:3]} {d.year}"
    if forme == "us":
        return f"{MOIS['en'][d.month - 1]} {d.day}, {d.year}"
    if forme == "us_num":
        return d.strftime("%m/%d/%Y")
    raise ValueError(forme)


FORMES_DATE = {"fr": ["jj/mm/aaaa", "long_fr", "jj.mm.aa", "aaaa-mm-jj"],
               "en": ["long_en", "abr_en", "jj/mm/aaaa", "aaaa-mm-jj"]}
