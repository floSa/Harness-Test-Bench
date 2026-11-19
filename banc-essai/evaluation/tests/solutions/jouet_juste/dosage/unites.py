"""Conversion des volumes en millilitres, lecture des nombres écrits à la française."""

FACTEURS_ML = {
    "ml": 1.0,
    "cm3": 1.0,
    "cl": 10.0,
    "l": 1000.0,
    "µl": 0.001,
}


def normaliser_unite(unite):
    u = unite.strip().lower().replace("³", "3")
    if u in ("ul", "μl"):
        u = "µl"
    return u


def vers_ml(valeur, unite):
    """Convertit un volume exprimé dans `unite` en millilitres."""
    u = normaliser_unite(unite)
    if u not in FACTEURS_ML:
        raise ValueError(f"unité inconnue : {unite}")
    return valeur * FACTEURS_ML[u]


def lire_nombre(texte):
    """Lit un nombre écrit avec une virgule décimale et des espaces de milliers (« 1 250,5 »)."""
    t = texte.replace(" ", "").replace(" ", "").replace(" ", "")
    return float(t.replace(",", "."))


def moyenne(valeurs):
    """Moyenne arithmétique d'une liste non vide de relevés."""
    if not valeurs:
        raise ValueError("liste vide")
    return sum(valeurs) / len(valeurs)
