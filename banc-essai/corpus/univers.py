"""Univers de noms fictifs, généré à partir de la graine.

Marques, familles de modèles et prestataires sont tirés d'un même réservoir de mots
inventés : un mot peut être une marque dans un document, une famille de machines ou le
nom d'un prestataire dans un autre. Le jeu de test reçoit surtout des noms jamais vus
dans le jeu fourni, et quelques mots du jeu fourni dans un autre rôle.
"""
import random

DEBUTS = ["Vex", "Kal", "Dor", "Mir", "Tel", "Bra", "Quen", "Sol", "Var", "Cor", "Lum", "Pra",
          "Zen", "Ost", "Fen", "Gal", "Hel", "Ril", "Tor", "Nev", "Sar", "Pol", "Mak", "Ver",
          "Dra", "Bel", "Cal", "Ner", "Tal", "Ory", "Juv", "Kes", "Lor", "Mab", "Pyr", "Ulv"]
MILIEUX = ["a", "i", "o", "e", "ae", "io", "ar", "el", "in", "or", "an", "ul"]
FINS = ["lor", "nis", "vex", "dra", "mos", "tik", "van", "rel", "ton", "lix", "ra", "gen",
        "pax", "mar", "dor", "net", "sol", "bel", "rix", "vane", "quin", "dal", "zor", "tis"]

SUFFIXES_PRESTATAIRE = {
    "fr": ["Maintenance", "Services", "Métrologie", "Techniques", "Assistance Industrielle",
           "Mesure et Contrôle", "Ingénierie"],
    "en": ["Services Ltd", "Field Services", "Engineering", "Calibration Ltd", "Metrology",
           "Technical Services"],
}
TYPES = ["doseuse", "pompe", "remplisseuse", "pipette"]

PRENOMS = {
    "fr": ["Claire", "Julien", "Sophie", "Nicolas", "Camille", "Thomas", "Élodie", "Mathieu",
           "Laure", "Antoine", "Manon", "Romain", "Inès", "Hugo", "Pauline", "Yann", "Margot",
           "Bastien", "Agathe", "Loïc", "Céline", "Damien", "Noémie", "Gaël"],
    "en": ["Emma", "James", "Olivia", "Liam", "Sarah", "Daniel", "Chloe", "Ryan", "Hannah",
           "Owen", "Grace", "Ethan", "Megan", "Callum", "Erin", "Rhys", "Aoife", "Declan"],
}
NOMS = {
    "fr": ["Morvan", "Le Goff", "Barbier", "Fontaine", "Guérin", "Roussel", "Perrin", "Mercier",
           "Lemaire", "Chevalier", "Garnier", "Faure", "Gauthier", "Robin", "Carré", "Tanguy",
           "Le Bihan", "Marchal", "Vasseur", "Lacombe", "Delmas", "Prigent", "Royer", "Joly"],
    "en": ["Whitfield", "Harlow", "Brennan", "Ashby", "Calloway", "Pryce", "Hollis", "Marsh",
           "Redding", "Thornley", "Keane", "Doyle", "Kerrigan", "Stroud", "Fenwick", "Gallagher",
           "Ainsley", "Mahon"],
}
VILLES = {
    "fr": ["Cholet", "Vierzon", "Lisieux", "Romans", "Lamballe", "Saint-Avold", "Fougères",
           "Châteaubriant", "Montargis", "Issoire", "Vitré", "Saumur", "Dole", "Mazamet",
           "Redon", "Guingamp", "Tulle", "Oyonnax", "Péronne", "Sablé-sur-Sarthe"],
    "en": ["Telford", "Wexford", "Livingston", "Doncaster", "Shannon", "Swindon", "Kendal",
           "Athlone", "Dundee", "Wrexham", "Carlow", "Ipswich", "Tralee", "Hexham"],
}
FORMES_SITE = {
    "fr": ["Usine de {v}", "Site de {v}", "Plateforme de {v}", "Établissement de {v}"],
    "en": ["{v} Plant", "{v} Site", "{v} Works", "{v} Facility"],
}
STYLES_LOGO = ["cercle", "hexagone", "cartouche", "goutte", "vagues", "carre", "monogramme",
               "losange"]


def _mot(r, deja):
    while True:
        m = r.choice(DEBUTS) + (r.choice(MILIEUX) if r.random() < 0.6 else "") + r.choice(FINS)
        if 5 <= len(m) <= 9 and m not in deja:
            deja.add(m)
            return m


def _couleur(r):
    return tuple(round(r.uniform(0.05, 0.75), 2) for _ in range(3))


def construire(graine, n_marques=(10, 8, 6), n_prestataires=(8, 5, 4)):
    """Univers en trois parts : fourni, test, relance.

    Renvoie {part: {"marques": [...], "prestataires": [...]}} ; chaque marque a ses familles
    de modèles, chaque prestataire sa langue, son style de nombres, son logo et la graine de
    sa mise en page (même prestataire, même gabarit dans tous ses documents).
    """
    r = random.Random(f"{graine}/univers")
    deja = set()
    parts = {}
    mots_fourni = []
    for part, nm, npr in zip(["fourni", "test", "relance"], n_marques, n_prestataires):
        marques = []
        for _ in range(nm):
            nom = _mot(r, deja)
            familles = [_mot(r, deja) for _ in range(2)]
            marques.append({"nom": nom, "type": r.choice(TYPES), "familles": familles,
                            "couleur": _couleur(r), "style": r.choice(STYLES_LOGO),
                            "prefixe_serie": nom[:2].upper()})
        prestataires = []
        for i in range(npr):
            langue = "fr" if i % 2 == 0 else "en"
            nom = f"{_mot(r, deja)} {r.choice(SUFFIXES_PRESTATAIRE[langue])}"
            prestataires.append({"nom": nom, "langue": langue, "couleur": _couleur(r),
                                 "style": r.choice(STYLES_LOGO), "graine_page": r.randint(0, 10**6),
                                 "ville": r.choice(VILLES[langue]),
                                 "prefixe": "".join(w[0] for w in nom.split()[:2]).upper()})
        parts[part] = {"marques": marques, "prestataires": prestataires}
        if part == "fourni":
            mots_fourni = [m["nom"] for m in marques] + [f for m in marques for f in m["familles"]]
    # Ambiguïtés de rôle : dans le test, des mots du jeu fourni changent de rôle.
    test = parts["test"]
    for k, m in enumerate(test["marques"][:3]):
        m["familles"][0] = mots_fourni[k]                  # une marque fournie devient une famille
    test["marques"][3]["nom"] = parts["fourni"]["marques"][0]["familles"][0]  # une famille devient une marque
    test["prestataires"][0]["nom"] = (f"{parts['fourni']['marques'][1]['nom']} "
                                      f"{SUFFIXES_PRESTATAIRE[test['prestataires'][0]['langue']][1]}")
    # Dans le jeu fourni aussi, une famille porte le nom d'une autre marque.
    f = parts["fourni"]["marques"]
    f[0]["familles"][1] = f[2]["nom"]
    return parts


def personne(r, langue, exclus=()):
    while True:
        p = f"{r.choice(PRENOMS[langue])} {r.choice(NOMS[langue])}"
        if p not in exclus:
            return p


def site(r, langue, exclus=()):
    while True:
        v = r.choice(VILLES[langue])
        if v not in exclus:
            return r.choice(FORMES_SITE[langue]).format(v=v), v
