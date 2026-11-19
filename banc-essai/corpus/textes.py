"""Textes fixes : phrases de remplissage (sans aucun nombre) et titres de sections.

Les titres évoquent la clé sans la nommer exactement ; les valeurs sont insérées par la base
des styles (base.py), avec ou sans libellé selon l'emplacement prévu au plan.
"""

REMPLISSAGE = {
    "fr": [
        "L'équipement est exploité en deux postes, cinq jours par semaine, pour le conditionnement "
        "de produits liquides.",
        "La dernière intervention préventive avait donné lieu à un simple nettoyage du circuit.",
        "L'accès à la machine a été rendu possible après consignation électrique et pneumatique "
        "par le responsable de ligne.",
        "Les produits dosés sur cette ligne sont aqueux et peu visqueux ; aucun produit dangereux "
        "n'était présent dans le circuit au moment de la visite.",
        "Le plan de prévention a été relu avec le service sécurité du site avant le début des travaux.",
        "Un balisage de la zone a été mis en place pendant toute la durée de l'intervention.",
        "Les contrôles ont été réalisés avec des instruments étalonnés, dont les certificats sont "
        "tenus à disposition du client.",
        "L'historique de maintenance a été consulté sur le registre tenu par le client.",
        "Le technicien a vérifié l'absence de bulles d'air dans le circuit avant chaque série de "
        "mesures.",
        "Les fixations du bâti et l'état des flexibles ont été contrôlés visuellement ; aucune trace "
        "de corrosion n'a été relevée.",
        "Le produit utilisé pour les essais est de l'eau déminéralisée à température ambiante.",
        "Le responsable de production a été informé du déroulement de l'intervention à chaque étape.",
        "Les capots de protection ont été remontés et leurs sécurités vérifiées avant la remise en "
        "service.",
        "Les consignes de nettoyage en place ont été rappelées à l'équipe de production.",
        "Le poste de travail a été laissé propre et dégagé à la fin de la visite.",
        "Aucun bruit anormal ni échauffement n'a été constaté pendant les essais à vide.",
        "La documentation du constructeur était disponible sur place et à jour.",
        "Les raccords rapides ont été démontés, nettoyés et remontés avec un lubrifiant compatible.",
        "Le paramétrage de l'automate n'a pas été modifié au cours de la visite.",
        "Les opérateurs ont signalé des arrêts brefs en début de poste, sans message d'alarme.",
        "La ventilation de l'armoire électrique a été dépoussiérée et son filtre contrôlé.",
        "Les données de production des dernières semaines ont été examinées avec le client.",
        "Le câblage des capteurs a été inspecté et les connecteurs resserrés.",
        "Les filtres d'aspiration ont été démontés, rincés et remis en place.",
        "Un essai de fonctionnement en mode manuel a précédé la reprise en automatique.",
        "Les étiquettes de sécurité de la machine sont lisibles et complètes.",
        "La purge du circuit a été réalisée jusqu'à obtention d'un écoulement régulier.",
        "Le client a été informé des points de vigilance relevés pendant la visite.",
        "Les arrêts d'urgence ont été testés et fonctionnent correctement.",
        "Les traces de produit séché sur le bâti ont été nettoyées.",
        "La lubrification des guidages a été complétée selon la notice.",
        "L'équipe de nuit a été prévenue des réglages effectués.",
        "Aucune fuite n'a été constatée sur les raccords après remise en pression.",
        "Le relevé des compteurs de cycles a été reporté dans le carnet de la machine.",
        "Les réglages ont été effectués machine arrêtée puis vérifiés en production.",
        "Le niveau sonore de la machine en fonctionnement est resté habituel.",
        "Le capotage transparent présente quelques rayures sans incidence sur la sécurité.",
    ],
    "en": [
        "The equipment runs on two shifts, five days a week, for liquid product packaging.",
        "The previous preventive visit only involved cleaning the fluid circuit.",
        "Access to the machine was granted after electrical and pneumatic lock-out by the line "
        "manager.",
        "Products dosed on this line are aqueous and of low viscosity; no hazardous product was in "
        "the circuit during the visit.",
        "The prevention plan was reviewed with the site safety department before work started.",
        "The work area was cordoned off for the whole duration of the visit.",
        "Checks were carried out with calibrated instruments; certificates are available to the "
        "customer.",
        "The maintenance history was reviewed in the customer's logbook.",
        "The technician checked that no air bubbles were present in the circuit before each series "
        "of measurements.",
        "Frame fixings and hoses were visually inspected; no corrosion was found.",
        "Demineralised water at room temperature was used for all tests.",
        "The production manager was kept informed at each step of the visit.",
        "Guards were refitted and their interlocks checked before restart.",
        "Cleaning-in-place instructions were reminded to the production team.",
        "The work station was left clean and clear at the end of the visit.",
        "No abnormal noise or heating was observed during dry runs.",
        "The manufacturer's documentation was available on site and up to date.",
        "Quick couplings were dismantled, cleaned and refitted with a compatible lubricant.",
        "PLC settings were not changed during the visit.",
        "Operators reported short stoppages at shift start, with no alarm message.",
        "The electrical cabinet ventilation was dusted and its filter checked.",
        "Production data from recent weeks was reviewed with the customer.",
        "Sensor wiring was inspected and connectors tightened.",
        "Suction filters were removed, rinsed and refitted.",
        "A manual-mode test run preceded the return to automatic operation.",
        "Machine safety labels are legible and complete.",
        "The circuit was purged until a steady flow was obtained.",
        "The customer was briefed on the points of attention noted during the visit.",
        "Emergency stops were tested and work correctly.",
        "Dried product residue on the frame was cleaned off.",
        "Guide lubrication was topped up as per the manual.",
        "The night shift was informed of the adjustments made.",
        "No leak was found on the fittings after repressurisation.",
        "Cycle counter readings were entered in the machine logbook.",
        "Adjustments were made with the machine stopped, then checked in production.",
        "Machine noise level in operation remained as usual.",
        "The transparent guard shows minor scratches with no effect on safety.",
    ],
}

# Titres de sections en texte libre : ils évoquent les clés sans les nommer.
TITRES = {
    "fr": {"equipement": "Contexte et équipement concerné", "lieu": "Déroulement de la visite",
           "reglages": "Réglages et résultats", "pieces": "Remplacements effectués",
           "equipe": "Équipe d'intervention", "avis": "Avis du technicien",
           "validation": "Circuit de validation"},
    "en": {"equipement": "Background and equipment", "lieu": "Course of the visit",
           "reglages": "Adjustments and results", "pieces": "Replacements",
           "equipe": "Field team", "avis": "Technician's opinion",
           "validation": "Approval workflow"},
}

# Statut écrit sans libellé : la phrase porte le sens, pas le code.
AVIS = {
    ("fr", "conforme"): "l'équipement peut être remis en production sans réserve",
    ("fr", "non_conforme"): "l'équipement ne peut pas être remis en production en l'état",
    ("fr", "a_revoir"): "l'équipement peut être remis en production sous réserve d'une nouvelle "
                        "visite rapprochée",
    ("en", "conforme"): "the equipment may return to production without restriction",
    ("en", "non_conforme"): "the equipment must not return to production as it stands",
    ("en", "a_revoir"): "the equipment may return to production subject to an early follow-up visit",
}
STATUTS = {"fr": ["Conforme", "Non conforme", "À revoir"],
           "en": ["Compliant", "Non-compliant", "To be reviewed"]}
CODES_STATUT = ["conforme", "non_conforme", "a_revoir"]
