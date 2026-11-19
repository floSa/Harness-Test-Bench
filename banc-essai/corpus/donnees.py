"""Tirage d'un document : valeurs attendues, leurres et choix de présentation.

Les valeurs numériques sont tirées dans l'unité de la clé ; la vérité terrain définitive est
recalculée au rendu à partir de ce qui est écrit (unité et arrondi d'affichage).
"""
import datetime as dt
import random

import univers

CLES = ["machine", "constructeur", "numero_serie", "site", "reference_rapport",
        "date_intervention", "date_validation", "volume_dose_ml", "volume_nominal_ml",
        "tolerance_ml", "debit_ml_min", "pression_bar", "reference_piece", "technicien",
        "statut"]
CLES_NUMERIQUES = ["volume_dose_ml", "volume_nominal_ml", "tolerance_ml", "debit_ml_min",
                   "pression_bar"]

TYPES = {
    "doseuse": {"fr": "doseuse volumétrique à piston", "en": "piston filler",
                "nominal": [5, 10, 25, 50, 100, 250, 500], "debit": (400, 4000, 10),
                "pression": (1.5, 4.5), "reservoir": [20, 30, 50, 80], "circuit": (120, 900),
                "tetes": [1]},
    "pompe": {"fr": "pompe doseuse à membrane", "en": "diaphragm metering pump",
              "nominal": [1, 2, 2.5, 5, 10, 20], "debit": (20, 600, 1), "pression": (2.0, 12.0),
              "reservoir": [60, 100, 200], "circuit": (40, 300), "tetes": [1]},
    "remplisseuse": {"fr": "remplisseuse rotative", "en": "rotary filling machine",
                     "nominal": [100, 200, 250, 330, 500, 750, 1000], "debit": (3000, 24000, 50),
                     "pression": (0.5, 3.0), "reservoir": [150, 300, 500, 1000],
                     "circuit": (800, 5000), "tetes": [2, 3, 4]},
    "pipette": {"fr": "pipette automatique", "en": "automatic pipette",
                "nominal": [0.5, 1, 2, 5], "debit": (1, 60, 1), "pression": (0.2, 1.5),
                "reservoir": [0.25, 0.5, 1, 2], "circuit": (2, 20), "tetes": [1]},
}
PIECES = {
    "doseuse": [("joint de piston", "piston seal"), ("ressort de rappel", "return spring"),
                ("buse de dosage", "dosing nozzle"), ("clapet anti-retour", "check valve")],
    "pompe": [("membrane", "diaphragm"), ("clapet d'aspiration", "suction valve"),
              ("clapet de refoulement", "discharge valve"), ("joint de tête", "head gasket")],
    "remplisseuse": [("électrovanne de tête", "head solenoid valve"), ("joint de bec", "spout seal"),
                     ("sonde de niveau", "level probe"), ("canule", "filling cannula")],
    "pipette": [("cône porte-pointe", "tip cone"), ("joint torique de piston", "piston O-ring"),
                ("filtre d'aspiration", "aspiration filter"), ("éjecteur", "tip ejector")],
}
INSTRUMENTS = [("balance de précision", "precision balance"),
               ("manomètre étalon", "reference pressure gauge"),
               ("débitmètre étalon", "reference flow meter"),
               ("thermomètre à sonde", "probe thermometer")]
CLIENTS = {"fr": ["Laboratoires {m}", "{m} Cosmétiques", "{m} Agroalimentaire", "{m} Pharma",
                  "Fromageries {m}"],
           "en": ["{m} Laboratories", "{m} Foods", "{m} Pharma", "{m} Beverages"]}

LIBELLES = {
    "fr": {
        "machine": ("Équipement", ["Machine", "Modèle", "Désignation"]),
        "constructeur": ("Constructeur", ["Fabricant", "Marque"]),
        "numero_serie": ("N° de série", ["N° de fabrication", "Identifiant machine", "S/N"]),
        "site": ("Site", ["Lieu d'intervention", "Établissement", "Implantation"]),
        "reference_rapport": ("Référence du rapport", ["N° de document", "Réf. document",
                                                       "N° de compte rendu"]),
        "date_intervention": ("Date d'intervention", ["Date de visite", "Intervenu le",
                                                      "Date de passage"]),
        "date_validation": ("Date de validation", ["Approuvé le", "Date d'approbation"]),
        "volume_dose_ml": ("Volume de dose", ["Dose", "Volume délivré", "Capacité utile",
                                              "Contenance"]),
        "volume_nominal_ml": ("Volume nominal", ["Consigne", "Volume de consigne"]),
        "tolerance_ml": ("Tolérance", ["Écart maximal toléré", "EMT", "Tolérance admise"]),
        "debit_ml_min": ("Débit", ["Cadence volumique", "Débit volumique"]),
        "pression_bar": ("Pression de service", ["Pression de travail", "Pression ligne"]),
        "reference_piece": ("Référence pièce", ["Réf. article", "Code pièce"]),
        "technicien": ("Technicien responsable", ["Intervenant principal", "Chargé d'intervention"]),
        "statut": ("Statut", ["Avis", "Verdict", "Décision"]),
    },
    "en": {
        "machine": ("Equipment", ["Machine", "Model", "Unit"]),
        "constructeur": ("Manufacturer", ["Make", "OEM", "Brand"]),
        "numero_serie": ("Serial number", ["S/N", "Unit ID"]),
        "site": ("Site", ["Location", "Plant"]),
        "reference_rapport": ("Report reference", ["Document no.", "Report ID"]),
        "date_intervention": ("Date of intervention", ["Visit date", "Service date"]),
        "date_validation": ("Validation date", ["Approved on", "Approval date"]),
        "volume_dose_ml": ("Dose volume", ["Fill volume", "Dose", "Delivered volume"]),
        "volume_nominal_ml": ("Nominal volume", ["Set point", "Target volume"]),
        "tolerance_ml": ("Tolerance", ["Max. permissible error", "MPE", "Acceptance limit"]),
        "debit_ml_min": ("Flow rate", ["Throughput", "Delivery rate"]),
        "pression_bar": ("Operating pressure", ["Line pressure", "Working pressure"]),
        "reference_piece": ("Part reference", ["Part number", "P/N", "Item code"]),
        "technicien": ("Lead technician", ["Lead engineer", "Responsible technician"]),
        "statut": ("Status", ["Outcome", "Result"]),
    },
}

# Emplacement par défaut de chaque valeur dans le style « grille ».
EMPLACEMENT_DEFAUT = {
    "machine": "grille", "constructeur": "grille", "numero_serie": "grille", "site": "grille",
    "reference_rapport": "grille", "date_intervention": "grille", "date_validation": "visas",
    "volume_dose_ml": "tableau", "volume_nominal_ml": "tableau", "tolerance_ml": "tableau",
    "debit_ml_min": "tableau", "pression_bar": "tableau", "reference_piece": "tableau",
    "technicien": "visas", "statut": "cases",
}


def _arr(x, pas):
    return round(round(x / pas) * pas, 6)


def _pas(nominal):
    return 0.001 if nominal < 1 else (0.01 if nominal < 10 else 0.1)


def _jours(d, a, b, r):
    return d + dt.timedelta(days=r.randint(a, b))


def tirer(doc_id, jeu, prestataire, marque, part_univers, graine, pieges=None, pieges_doc=None):
    """Un document. pieges : {cle: [noms]} imposés ; pieges_doc : {nom: valeur}."""
    r = random.Random(f"{graine}/{doc_id}/valeurs")
    langue = prestataire["langue"]
    typ = TYPES[marque["type"]]

    # Volumes, tolérance et statut.
    statut = r.choices(["conforme", "non_conforme", "a_revoir"], weights=[65, 20, 15])[0]
    nominal = float(r.choice(typ["nominal"]))
    pas = _pas(nominal)
    pct = r.choice([0.5, 1, 1.5, 2, 2.5, 3])
    while nominal * pct / 100 < 0.06:
        pct = {0.5: 1, 1: 2, 1.5: 2, 2: 3, 2.5: 3, 3: 5, 5: 8, 8: 10, 10: 15}[pct]
    tolerance = round(nominal * pct / 100, 6)
    if statut == "non_conforme":
        ecart = _arr(tolerance * r.uniform(1.25, 1.9), pas)
    else:
        ecart = _arr(max(0.02, tolerance * r.uniform(0.3, 0.75)), pas)
    ecart = max(ecart, _arr(0.02, pas) if pas < 0.02 else pas)
    dose = _arr(nominal + r.choice([-1, 1]) * ecart, pas)
    tetes = r.choice(typ["tetes"])
    # Moyennes par tête centrées sur la dose, essais centrés sur la moyenne de la tête.
    offs = [_arr(r.uniform(-0.6, 0.6) * ecart, pas) for _ in range(tetes - 1)]
    offs.append(-round(sum(offs), 6))
    essais_apres, essais_avant = [], []
    avant = _arr(nominal * (1 + r.choice([-1, 1]) * r.uniform(0.03, 0.08)), pas)
    if abs(avant - dose) < max(0.03, 0.02 * nominal):
        avant = _arr(dose + max(0.03, 0.03 * nominal), pas)
    for o in offs:
        m = _arr(dose + o, pas)
        d1 = _arr(r.uniform(-0.4, 0.4) * ecart, pas)
        d2 = _arr(r.uniform(-0.4, 0.4) * ecart, pas)
        essais_apres.append([_arr(m + d1, pas), _arr(m + d2, pas), _arr(m - d1 - d2, pas)])
        essais_avant.append([_arr(avant + r.uniform(-0.6, 0.6) * ecart, pas) for _ in range(3)])
    incertitude = _arr(max(pas, tolerance * r.uniform(0.15, 0.35)), pas)

    dmin, dmax, dpas = typ["debit"]
    debit = _arr(r.uniform(dmin, dmax), dpas)
    pmin, pmax = typ["pression"]
    pression = round(r.uniform(pmin, pmax), 1)

    # Dates.
    intervention = dt.date(2025, 2, 3) + dt.timedelta(days=r.randint(0, 600))
    demande = intervention - dt.timedelta(days=r.randint(2, 12))
    incident = demande - dt.timedelta(days=r.randint(0, 4))
    emission = _jours(intervention, 1, 5, r)
    verification = _jours(emission, 0, 3, r)
    validation = _jours(verification, 1, 6, r)
    impression = _jours(validation, 1, 12, r)
    prochaine = intervention + dt.timedelta(days=r.choice([182, 365]))
    arrivee = r.choice(["7 h 30", "8 h 00", "8 h 15", "9 h 00", "13 h 30"])

    # Personnes.
    tech = univers.personne(r, langue)
    accomp = univers.personne(r, langue, (tech,))
    verif = univers.personne(r, langue, (tech, accomp))
    approb = univers.personne(r, langue, (tech, accomp, verif))
    demandeur = univers.personne(r, langue, (tech, accomp, verif, approb))

    # Lieux et client.
    site, ville_site = univers.site(r, langue)
    _, ville_siege = univers.site(r, langue, (ville_site,))
    mot_client = r.choice(univers.DEBUTS) + r.choice(univers.FINS)
    client = r.choice(CLIENTS[langue]).format(m=mot_client)

    # Références.
    an = intervention.year
    ref = f"{prestataire['prefixe']}-RI-{an}-{r.randint(1000, 9999)}"
    ref_ancienne = f"{prestataire['prefixe']}-RI-{an}-{r.randint(1000, 9999)}"
    pref = marque["prefixe_serie"]
    serie = r.choice([f"{pref}-{r.randint(2016, 2024)}-{r.randint(10000, 99999)}",
                      f"{pref}{r.randint(100000, 999999)}",
                      f"{pref}/{r.randint(16, 24)}/{r.randint(1000, 9999)}"])
    pieces = r.sample(PIECES[marque["type"]], 4)
    refs_pieces = [f"{pref}-{r.randint(100, 999)}-{r.choice('ABCDEKR')}" for _ in pieces]

    # Leurres des zones ambiguës.
    autres_marques = [m["nom"] for m in part_univers["marques"] if m["nom"] != marque["nom"]]
    moteur = {"marque": r.choice(autres_marques), "type": f"{r.choice('KLMT')}{r.randint(63, 112)}"
              f"-{r.choice([2, 4])}P", "serie": f"M{r.randint(1000000, 9999999)}",
              "kw": r.choice([0.37, 0.55, 0.75, 1.1, 1.5, 2.2]), "trmin": r.choice([1380, 1420, 2850, 2890]),
              "tension": r.choice(["230/400 V", "400 V"])}
    instruments = []
    for nom_fr, nom_en in r.sample(INSTRUMENTS, 2):
        instruments.append({"nom": nom_fr if langue == "fr" else nom_en,
                            "marque": r.choice(autres_marques),
                            "serie": f"{r.choice(['IN', 'EQ', 'ET'])}-{r.randint(10000, 99999)}",
                            "etalonnage": (intervention - dt.timedelta(days=r.randint(30, 300))).isoformat()})
    voisin = {"modele": f"{r.choice([f for m in part_univers['marques'] for f in m['familles']])} "
                        f"C{r.randint(10, 90)}",
              "debit": _arr(debit * r.uniform(1.3, 2.5), dpas),
              "pression": round(pression + r.uniform(0.8, 3), 1)}

    valeurs = {
        "machine": f"{r.choice(marque['familles'])} {r.choice([40, 85, 120, 160, 250, 300, 600])}",
        "constructeur": marque["nom"], "numero_serie": serie, "site": site,
        "reference_rapport": ref, "date_intervention": intervention.isoformat(),
        "date_validation": validation.isoformat(), "volume_dose_ml": dose,
        "volume_nominal_ml": nominal, "tolerance_ml": tolerance, "debit_ml_min": debit,
        "pression_bar": pression, "reference_piece": refs_pieces[0], "technicien": tech,
        "statut": statut,
    }
    leurres = {
        "essais_apres": essais_apres, "essais_avant": essais_avant, "avant": avant,
        "tetes": tetes, "pct": pct, "incertitude": incertitude, "pas": pas,
        "debit_avant": _arr(debit * r.uniform(0.82, 0.95), dpas),
        "debit_max": _arr(debit * r.uniform(1.6, 2.6), max(dpas, 10)),
        "pression_avant": round(pression * r.uniform(0.75, 0.92), 1),
        "pression_max": round(pression * r.uniform(2.0, 3.5) * 2) / 2,
        "tarage": round(pression * r.uniform(1.3, 1.8), 1), "air": r.choice([6.0, 7.0, 8.0]),
        "reservoir_l": float(r.choice(typ["reservoir"])),
        "circuit_ml": float(r.randint(*typ["circuit"])),
        "temperature": round(r.uniform(16, 32), 1),
        "gamme": (min(typ["nominal"]), max(typ["nominal"])),
        "demande": demande.isoformat(), "incident": incident.isoformat(),
        "emission": emission.isoformat(), "verification": verification.isoformat(),
        "impression": impression.isoformat(), "prochaine": prochaine.isoformat(),
        "arrivee": arrivee, "duree_h": r.choice([2, 2.5, 3, 3.5, 4, 5]),
        "accompagnant": accomp, "verificateur": verif, "approbateur": approb,
        "demandeur": demandeur, "client": client, "ville_siege": ville_siege,
        "ref_ancienne": ref_ancienne, "commande": f"{'CDE' if langue == 'fr' else 'PO'}-{r.randint(100000, 999999)}",
        "affaire": f"AFF-{r.randint(10000, 99999)}", "inventaire": f"INV-{r.randint(10000, 99999)}",
        "pieces": [(ref_p, p[0] if langue == "fr" else p[1]) for ref_p, p in zip(refs_pieces, pieces)],
        "prix": [round(r.uniform(18, 640), 2) for _ in pieces],
        "moteur": moteur, "instruments": instruments, "voisin": voisin,
        "type_machine": typ[langue],
        "ligne": f"{'Ligne' if langue == 'fr' else 'Line'} {r.randint(1, 4)}",
    }
    doc = {"id": doc_id, "jeu": jeu, "langue": langue, "prestataire": prestataire,
           "marque": marque, "valeurs": valeurs, "leurres": leurres,
           "pieges": {k: list((pieges or {}).get(k, [])) for k in CLES},
           "pieges_doc": dict(pieges_doc or {})}
    _presentation(doc, r)
    return doc


def _presentation(doc, r):
    langue = doc["langue"]
    p = doc["pieges"]
    lib, emp, unites = {}, {}, {}
    for cle in CLES:
        exact, syn = LIBELLES[langue][cle]
        lib[cle] = r.choice(syn) if "synonyme_cle" in p[cle] else exact
        if "recit_seul" in p[cle]:
            emp[cle] = "recit"
        elif "schema_seul" in p[cle]:
            emp[cle] = "schema"
        elif "tampon_seul" in p[cle]:
            emp[cle] = "tampon"
        else:
            emp[cle] = EMPLACEMENT_DEFAUT[cle]
    v = doc["valeurs"]
    ml = "ml" if langue == "fr" else "mL"
    for cle in ["volume_dose_ml", "volume_nominal_ml", "tolerance_ml"]:
        if "unite_a_convertir" in p[cle]:
            x = v[cle]
            unites[cle] = ("µl" if langue == "fr" else "µL") if x < 20 else ("cl" if x < 200 else "L")
        else:
            unites[cle] = r.choice([ml, ml, ml, "cm³"])
    unites["debit_ml_min"] = (r.choice(["L/h", "ml/s" if langue == "fr" else "L/min"])
                              if "unite_a_convertir" in p["debit_ml_min"]
                              else ("ml/min" if langue == "fr" else "mL/min"))
    unites["pression_bar"] = (r.choice(["kPa", "mbar"] if langue == "fr" else ["psi", "kPa"])
                              if "unite_a_convertir" in p["pression_bar"] else "bar")
    doc["libelles"], doc["emplacements"], doc["unites"] = lib, emp, unites
