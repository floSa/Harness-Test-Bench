"""Entités fictives du corpus : constructeurs, prestataires, personnes, sites, vocabulaire.

Tous les noms sont inventés. Recherche web du 19/11/2026 : aucune entreprise trouvée
sous les noms Vexilor, Pumanis, Corvalis, Mikropal, Techmaint Loire, Calibro Services,
Atelier Bréval, Tessaly Field Services.
"""

CLES = [
    "machine", "constructeur", "numero_serie", "site", "date_intervention",
    "volume_dose_ml", "volume_nominal_ml", "debit_ml_min", "pression_bar",
    "reference_piece", "technicien", "statut",
]
CLES_NUMERIQUES = ["volume_dose_ml", "volume_nominal_ml", "debit_ml_min", "pression_bar"]
CLES_VOLUME = ["volume_dose_ml", "volume_nominal_ml"]

# Plages de valeurs par type de machine. Volumes en ml, débits en ml/min, pressions en bar,
# réservoir en L, circuit en ml.
TYPES = {
    "doseuse": {
        "fr": "doseuse volumétrique à piston", "en": "piston filler",
        "nominal": [5, 10, 25, 50, 100, 250, 500],
        "debit": (400, 4000, 10), "pression": (1.5, 4.5), "reservoir": [20, 30, 50, 80],
        "circuit": (120, 900),
    },
    "pompe": {
        "fr": "pompe doseuse à membrane", "en": "diaphragm metering pump",
        "nominal": [0.5, 1, 2, 2.5, 5, 10, 20],
        "debit": (20, 600, 1), "pression": (2.0, 12.0), "reservoir": [60, 100, 200],
        "circuit": (40, 300),
    },
    "remplisseuse": {
        "fr": "remplisseuse rotative", "en": "rotary filling machine",
        "nominal": [100, 200, 250, 330, 500, 750, 1000, 1500],
        "debit": (3000, 24000, 50), "pression": (0.5, 3.0), "reservoir": [150, 300, 500, 1000],
        "circuit": (800, 5000),
    },
    "pipette": {
        "fr": "pipette automatique", "en": "automatic pipette",
        "nominal": [0.5, 1, 2, 5],
        "debit": (1, 60, 1), "pression": (0.2, 1.5), "reservoir": [0.25, 0.5, 1, 2],
        "circuit": (2, 20),
    },
}

CONSTRUCTEURS = [
    {
        "nom": "Vexilor", "type": "doseuse",
        "modeles": ["Vexidose 120", "Vexidose 250", "Vexidose 600"],
        "serie": "VX-{an}-{n5}",
        "pieces": [("JT-{n3}", "joint de piston", "piston seal"),
                   ("RS-{n3}", "ressort de rappel", "return spring"),
                   ("BZ-{n3}", "buse de dosage", "dosing nozzle")],
        "couleur": (0.10, 0.20, 0.45), "style": "cercle",
    },
    {
        "nom": "Pumanis", "type": "pompe",
        "modeles": ["PMX 40", "PMX 85", "PMX 160"],
        "serie": "PMN/{an2}/{n5}",
        "pieces": [("PMN-{n4}-K", "membrane", "diaphragm"),
                   ("PMN-{n4}-V", "clapet d'aspiration", "suction valve"),
                   ("PMN-{n4}-R", "clapet de refoulement", "discharge valve")],
        "couleur": (0.05, 0.45, 0.25), "style": "hexagone",
    },
    {
        "nom": "Corvalis", "type": "remplisseuse",
        "modeles": ["Corvafill 6", "Corvafill 12", "Corvafill Duo"],
        "serie": "CV-{an2}-{n4}-{lettre}",
        "pieces": [("CVF/{n4}", "électrovanne de tête", "head solenoid valve"),
                   ("CVJ/{n4}", "joint de bec", "spout seal"),
                   ("CVS/{n4}", "sonde de niveau", "level probe")],
        "couleur": (0.70, 0.12, 0.12), "style": "cartouche",
    },
    {
        "nom": "Mikropal", "type": "pipette",
        "modeles": ["MP-Auto 200", "MP-Auto 1000", "Mikrostep 50"],
        "serie": "MKP{n7}",
        "pieces": [("MK.{n2}.{n3}", "cône porte-pointe", "tip cone"),
                   ("MK.{n2}.{n3}", "joint torique de piston", "piston O-ring"),
                   ("MK.{n2}.{n3}", "filtre d'aspiration", "aspiration filter")],
        "couleur": (0.42, 0.18, 0.55), "style": "goutte",
    },
]

PRESTATAIRES = {
    1: {"nom": "Techmaint Loire", "langue": "fr", "adresse": "Parc d'activités des Landes, Ancenis",
        "couleur": (0.90, 0.45, 0.10), "style": "vagues", "prefixe": "TL"},
    2: {"nom": "Calibro Services Ltd", "langue": "en", "adresse": "Kestrel Court, Bradford",
        "couleur": (0.05, 0.50, 0.55), "style": "carre", "prefixe": "CS"},
    3: {"nom": "Atelier Bréval Maintenance", "langue": "fr", "adresse": "Zone artisanale du Moulin, Bréval",
        "couleur": (0.45, 0.30, 0.15), "style": "monogramme", "prefixe": "AB"},
    4: {"nom": "Tessaly Field Services", "langue": "en", "adresse": "Unit 9, Harbour Road, Shannon",
        "couleur": (0.35, 0.38, 0.42), "style": "losange", "prefixe": "TFS"},
}

PRENOMS = {
    "fr": ["Claire", "Julien", "Sophie", "Nicolas", "Camille", "Thomas", "Élodie", "Mathieu",
           "Laure", "Antoine", "Manon", "Romain", "Inès", "Hugo", "Pauline", "Yann"],
    "en": ["Emma", "James", "Olivia", "Liam", "Sarah", "Daniel", "Chloe", "Ryan",
           "Hannah", "Owen", "Grace", "Ethan"],
}
NOMS = {
    "fr": ["Morvan", "Le Goff", "Barbier", "Fontaine", "Guérin", "Roussel", "Perrin", "Mercier",
           "Lemaire", "Chevalier", "Garnier", "Faure", "Gauthier", "Robin", "Carré", "Tanguy"],
    "en": ["Whitfield", "Harlow", "Brennan", "Ashby", "Calloway", "Pryce", "Hollis", "Marsh",
           "Redding", "Thornley", "Keane", "Doyle"],
}
SITES = {
    "fr": ["Usine de Cholet", "Site de Vierzon", "Usine de Lisieux", "Plateforme de Romans",
           "Usine de Lamballe", "Site de Saint-Avold", "Usine de Fougères", "Site de Châteaubriant"],
    "en": ["Telford Plant", "Wexford Site", "Livingston Plant", "Doncaster Works",
           "Shannon Facility", "Swindon Plant"],
}
LIGNES_CLIENT = {
    "fr": ["Ligne 1 conditionnement", "Ligne 3 dosage", "Atelier flacons", "Ligne sirops",
           "Salle propre B", "Ligne 2 remplissage"],
    "en": ["Line 1 packaging", "Line 3 dosing", "Vial suite", "Syrup line", "Clean room B",
           "Line 2 filling"],
}

# Libellés des clés : (exact, [synonymes]) par langue.
LIBELLES = {
    "fr": {
        "machine": ("Machine", ["Équipement", "Modèle", "Désignation"]),
        "constructeur": ("Constructeur", ["Fabricant", "Marque"]),
        "numero_serie": ("N° de série", ["N° de fabrication", "Identifiant machine", "S/N"]),
        "site": ("Site", ["Lieu d'intervention", "Établissement"]),
        "date_intervention": ("Date d'intervention", ["Date de visite", "Intervenu le"]),
        "volume_dose_ml": ("Volume de dose", ["Dose", "Volume délivré", "Capacité utile", "Contenance"]),
        "volume_nominal_ml": ("Volume nominal", ["Consigne", "Volume de consigne"]),
        "debit_ml_min": ("Débit", ["Cadence volumique", "Débit volumique"]),
        "pression_bar": ("Pression de service", ["Pression de travail", "Pression ligne"]),
        "reference_piece": ("Référence pièce", ["Réf. article", "Code pièce"]),
        "technicien": ("Technicien", ["Intervenant", "Opérateur de maintenance"]),
        "statut": ("Statut", ["Avis", "Verdict", "Décision"]),
    },
    "en": {
        "machine": ("Machine", ["Equipment", "Model", "Unit"]),
        "constructeur": ("Manufacturer", ["Make", "OEM", "Brand"]),
        "numero_serie": ("Serial number", ["S/N", "Unit ID"]),
        "site": ("Site", ["Location", "Plant"]),
        "date_intervention": ("Date of intervention", ["Visit date", "Service date"]),
        "volume_dose_ml": ("Dose volume", ["Fill volume", "Dose", "Delivered volume"]),
        "volume_nominal_ml": ("Nominal volume", ["Set point", "Target volume"]),
        "debit_ml_min": ("Flow rate", ["Throughput", "Delivery rate"]),
        "pression_bar": ("Operating pressure", ["Line pressure", "Working pressure"]),
        "reference_piece": ("Part reference", ["Part number", "P/N", "Item code"]),
        "technicien": ("Technician", ["Engineer", "Serviced by"]),
        "statut": ("Status", ["Outcome", "Result"]),
    },
}

STATUTS = {
    "fr": {"conforme": "Conforme", "non_conforme": "Non conforme", "a_revoir": "À revoir"},
    "en": {"conforme": "Compliant", "non_conforme": "Non-compliant", "a_revoir": "To be reviewed"},
    "en4": {"conforme": "PASS", "non_conforme": "FAIL", "a_revoir": "REVIEW"},
}

MOIS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}
