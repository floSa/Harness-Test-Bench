"""Tirage des valeurs attendues et répartition des pièges.

Les réponses sont tirées avant tout rendu : elles sont connues sans erreur.
"""
import datetime as dt
import random

from entites import (CLES, CLES_NUMERIQUES, CLES_VOLUME, CONSTRUCTEURS, LIBELLES, LIGNES_CLIENT,
                     NOMS, PRENOMS, PRESTATAIRES, SITES, TYPES)

LANGUE = {1: "fr", 2: "en", 3: "fr", 4: "en"}

# Pièges tirés au sort (comptent dans la limite de 2 par valeur).
P_VALEURS = {"champ_absent": 0.05, "schema_seul": 0.10, "recit_seul": 0.15, "synonyme_cle": 0.30}
P_VOLUMES = {"unite_a_convertir": 0.20}
P_DOCUMENTS = {"logo_seul": 0.20, "deux_logos": 0.30, "correction": 0.05, "scan": 0.20}
MAX_PIEGES_TIRES = 2

ELIGIBLES = {
    "champ_absent": ["numero_serie", "site", "debit_ml_min", "pression_bar", "reference_piece",
                     "technicien"],
    "schema_seul": CLES_NUMERIQUES,
    "recit_seul": ["site", "date_intervention", "numero_serie", "volume_dose_ml",
                   "volume_nominal_ml", "debit_ml_min", "pression_bar", "reference_piece"],
    "unite_a_convertir": CLES_VOLUME,
    "synonyme_cle": CLES,
    "correction": CLES_NUMERIQUES,
}
EMPLACEMENT_DEFAUT = {
    "machine": "garde", "constructeur": "garde", "numero_serie": "garde", "site": "garde",
    "date_intervention": "garde", "volume_dose_ml": "tableau", "volume_nominal_ml": "tableau",
    "debit_ml_min": "tableau", "pression_bar": "tableau", "reference_piece": "tableau",
    "technicien": "conclusion", "statut": "conclusion",
}


def cible(p, n):
    """Nombre visé, arrondi au plus proche (0,5 vers le haut)."""
    return int(p * n + 0.5)


def _motif(motif, r):
    return motif.format(
        an=r.randint(2018, 2025), an2=r.randint(18, 25), n2=r.randint(10, 99),
        n3=r.randint(100, 999), n4=r.randint(1000, 9999), n5=r.randint(10000, 99999),
        n7=r.randint(1000000, 9999999), lettre=r.choice("ABCDEFGH"))


def _arrondi(x, pas):
    return round(round(x / pas) * pas, 6)


def _pas_volume(nominal):
    if nominal < 1:
        return 0.001
    if nominal < 10:
        return 0.01
    return 0.1


def _personne(r, langue, exclus=()):
    while True:
        nom = f"{r.choice(PRENOMS[langue])} {r.choice(NOMS[langue])}"
        if nom not in exclus:
            return nom


def tirer_document(doc_id, jeu, gabarit, constructeur_idx, graine):
    """Tire les valeurs attendues et les valeurs voisines (leurres) d'un document."""
    r = random.Random(f"{graine}/{doc_id}/valeurs")
    langue = LANGUE[gabarit]
    cons = CONSTRUCTEURS[constructeur_idx]
    typ = TYPES[cons["type"]]

    # Statut d'abord : il fixe l'écart entre dose et nominal.
    statut = r.choices(["conforme", "non_conforme", "a_revoir"], weights=[70, 15, 15])[0]
    nominal = float(r.choice(typ["nominal"]))
    pas = _pas_volume(nominal)
    ecart_min = max(0.02, 0.002 * nominal)
    ecart = _arrondi(max(ecart_min, nominal * r.uniform(0.002, 0.012)), pas)
    ecart = ecart if ecart >= ecart_min - 1e-9 else _arrondi(ecart_min + pas, pas)
    signe = r.choice([-1, 1])
    dose = _arrondi(nominal + signe * ecart, pas)
    if statut == "non_conforme":
        tolerance = _arrondi(max(pas, ecart * r.uniform(0.3, 0.7)), pas)
    else:
        tolerance = _arrondi(ecart * r.uniform(1.4, 3.0) + pas, pas)
    avant = _arrondi(nominal * (1 + r.choice([-1, 1]) * r.uniform(0.03, 0.08)), pas)
    if abs(avant - dose) < max(0.02, 0.02 * nominal):
        avant = _arrondi(dose + (1 if avant >= dose else -1) * max(0.03, 0.03 * nominal), pas)

    dmin, dmax, dpas = typ["debit"]
    debit = _arrondi(r.uniform(dmin, dmax), dpas)
    debit_avant = _arrondi(debit * r.uniform(0.82, 0.95), dpas)
    debit_max = _arrondi(debit * r.uniform(1.6, 2.6), dpas * 10 if dpas >= 10 else 10)
    pmin, pmax = typ["pression"]
    pression = round(r.uniform(pmin, pmax), 1)
    pression_avant = round(pression * r.uniform(0.75, 0.92), 1)
    if pression_avant == pression:
        pression_avant = round(pression - 0.1, 1)
    pression_max = round(pression * r.uniform(2.0, 3.5) * 2) / 2
    reservoir_l = float(r.choice(typ["reservoir"]))
    circuit_ml = float(r.randint(*typ["circuit"]))
    temperature = round(r.uniform(16, 34), 1)

    date = dt.date(2025, 1, 6) + dt.timedelta(days=r.randint(0, 640))
    date_rapport = date + dt.timedelta(days=r.randint(1, 6))
    prochaine = date + dt.timedelta(days=r.choice([182, 183, 365]))

    piece_motif, piece_fr, piece_en = r.choice(cons["pieces"])
    autre = r.choice([p for p in cons["pieces"] if p[1] != piece_fr])
    reference_piece = _motif(piece_motif, r)
    autre_ref = _motif(autre[0], r)
    while autre_ref == reference_piece:
        autre_ref = _motif(autre[0], r)

    technicien = _personne(r, langue)
    valideur = _personne(r, langue, exclus=(technicien,))
    contact = _personne(r, langue, exclus=(technicien, valideur))

    valeurs = {
        "machine": r.choice(cons["modeles"]),
        "constructeur": cons["nom"],
        "numero_serie": _motif(cons["serie"], r),
        "site": r.choice(SITES[langue]),
        "date_intervention": date.isoformat(),
        "volume_dose_ml": dose,
        "volume_nominal_ml": nominal,
        "debit_ml_min": debit,
        "pression_bar": pression,
        "reference_piece": reference_piece,
        "technicien": technicien,
        "statut": statut,
    }
    leurres = {
        "dose_avant": avant, "tolerance_ml": tolerance, "reservoir_l": reservoir_l,
        "circuit_ml": circuit_ml, "debit_avant": debit_avant, "debit_max": debit_max,
        "pression_avant": pression_avant, "pression_max": pression_max,
        "temperature": temperature, "temperature_avant": round(temperature - r.uniform(0.5, 3), 1),
        "date_rapport": date_rapport.isoformat(), "prochaine_visite": prochaine.isoformat(),
        "piece_nom": piece_fr if langue == "fr" else piece_en,
        "autre_ref": autre_ref, "autre_nom": autre[1] if langue == "fr" else autre[2],
        "valideur": valideur, "contact": contact,
        "inventaire": f"INV-{r.randint(10000, 99999)}",
        "reference_rapport": f"{PRESTATAIRES[gabarit]['prefixe']}-{date.year}-{r.randint(100, 9999):04d}",
        "ligne_client": r.choice(LIGNES_CLIENT[langue]),
        "type_machine": typ[langue],
    }
    return {
        "id": doc_id, "jeu": jeu, "gabarit": gabarit, "langue": langue,
        "constructeur_idx": constructeur_idx, "valeurs": valeurs, "leurres": leurres,
        "pieges": {k: [] for k in CLES},           # pièges tirés, par clé
        "pieges_doc": {"logo_seul": False, "deux_logos": False, "correction": None, "scan": False},
    }


def _nb(doc, cle):
    return len(doc["pieges"][cle])


def _compatible(doc, cle, piege):
    p = doc["pieges"][cle]
    if "champ_absent" in p or _nb(doc, cle) >= MAX_PIEGES_TIRES:
        return False
    if piege == "champ_absent":
        return not p
    if piege == "schema_seul":
        return "recit_seul" not in p and "correction" not in p
    if piege == "recit_seul":
        return "schema_seul" not in p and "correction" not in p
    if piege == "correction":
        return "schema_seul" not in p and "recit_seul" not in p
    if piege == "synonyme_cle":
        return "logo_seul" not in p
    return True


def allouer(docs, r, forcer=None):
    """Répartit les pièges d'un jeu de documents, en nombres exacts.

    forcer : {doc_id: {piege_doc: valeur}} pour les documents d'exemple.
    """
    forcer = forcer or {}
    n = len(docs)
    # Pièges au niveau du document.
    for piege in ["logo_seul", "deux_logos", "scan"]:
        imposes = [d for d in docs if forcer.get(d["id"], {}).get(piege)]
        libres = [d for d in docs if piege not in forcer.get(d["id"], {})]
        k = max(0, cible(P_DOCUMENTS[piege], n) - len(imposes))
        for d in imposes + r.sample(libres, min(k, len(libres))):
            d["pieges_doc"][piege] = True
            if piege in ("logo_seul", "deux_logos"):
                d["pieges"]["constructeur"].append(piege)

    # Pièges par valeur, du plus contraint au plus souple.
    total = n * len(CLES)
    for piege, k in [("champ_absent", cible(P_VALEURS["champ_absent"], total)),
                     ("schema_seul", cible(P_VALEURS["schema_seul"], total)),
                     ("recit_seul", cible(P_VALEURS["recit_seul"], total))]:
        candidats = [(d, c) for d in docs for c in ELIGIBLES[piege] if _compatible(d, c, piege)]
        if len(candidats) < k:
            raise RuntimeError(f"{piege} : {len(candidats)} candidats pour {k}")
        for d, c in r.sample(candidats, k):
            d["pieges"][c].append(piege)

    # Correction : un document sur vingt, une valeur numérique du tableau.
    imposes = [d for d in docs if forcer.get(d["id"], {}).get("correction")]
    libres = [d for d in docs if "correction" not in forcer.get(d["id"], {})]
    k = max(0, cible(P_DOCUMENTS["correction"], n) - len(imposes))
    for d in imposes + r.sample(libres, min(k, len(libres))):
        cles = [c for c in ELIGIBLES["correction"] if _compatible(d, c, "correction")]
        c = r.choice(cles)
        d["pieges"][c].append("correction")
        d["pieges_doc"]["correction"] = c

    k = cible(P_VOLUMES["unite_a_convertir"], n * len(CLES_VOLUME))
    candidats = [(d, c) for d in docs for c in CLES_VOLUME if _compatible(d, c, "unite_a_convertir")]
    for d, c in r.sample(candidats, k):
        d["pieges"][c].append("unite_a_convertir")

    k = cible(P_VALEURS["synonyme_cle"], total)
    candidats = [(d, c) for d in docs for c in CLES if _compatible(d, c, "synonyme_cle")]
    if len(candidats) < k:
        raise RuntimeError(f"synonyme_cle : {len(candidats)} candidats pour {k}")
    for d, c in r.sample(candidats, k):
        d["pieges"][c].append("synonyme_cle")

    for d in docs:
        _decider_presentation(d)


def _decider_presentation(doc):
    """Choix de présentation dépendant des pièges : libellés, unités, emplacement."""
    r = random.Random(f"{doc['id']}/presentation/{doc['valeurs']['numero_serie']}")
    libelles, unites, emplacements = {}, {}, {}
    for cle in CLES:
        p = doc["pieges"][cle]
        exact, synonymes = LIBELLES[doc["langue"]][cle]
        libelles[cle] = r.choice(synonymes) if "synonyme_cle" in p else exact
        if "recit_seul" in p or "correction" in p:
            emplacements[cle] = "recit"
        elif "schema_seul" in p:
            emplacements[cle] = "schema"
        else:
            emplacements[cle] = EMPLACEMENT_DEFAUT[cle]
        if cle in CLES_VOLUME:
            if "unite_a_convertir" in p:
                unites[cle] = "µl" if doc["valeurs"][cle] < 20 else "L"
            else:
                unites[cle] = "ml"
    doc["libelles"], doc["unites"], doc["emplacements"] = libelles, unites, emplacements


def reponse(doc):
    """JSON attendu : 12 clés, null pour un champ absent."""
    return {c: (None if "champ_absent" in doc["pieges"][c] else doc["valeurs"][c]) for c in CLES}
