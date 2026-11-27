"""Goldset de démonstration, tiré des 35 rapports publics du corpus (banc-essai/corpus/fourni/).

    python3 banc-essai/corpus/goldset_demo.py

Sert à essayer toute la chaîne (import, notation, consignes, essai d'un harnais) avant de toucher aux
données de l'entreprise. Écrit, sous banc-essai/corpus/demo/ (hors git) :

    demo/goldset/                      même arborescence qu'un goldset réel :
        ground_truth.json              objet {nom du PDF: valeurs}
        split/train|val|test/*.pdf     15, 10 et 10 rapports, renommés
        split/<jeu>_ground_truth.json  liste d'objets {"file_name": ..., valeurs}
    demo/schema-valide.json            schéma tel qu'un humain l'aurait validé
    demo/import/                       résultat de l'import (jeux du banc), avec ce schéma

Les valeurs reprennent les réponses du corpus, sous des formes volontairement hétérogènes, comme
dans un goldset réel : équipement en objet imbriqué, dates JJ/MM/AAAA, tolérance écrite en texte
avec une virgule décimale. Bibliothèque standard seulement.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import importer_goldset  # noqa: E402

FOURNI = ICI / "fourni"
DEMO = ICI / "demo"
REPARTITION = {"train": 15, "val": 10, "test": 10}
DESCRIPTIONS = {
    "equipement.machine": "modèle de l'équipement contrôlé",
    "equipement.constructeur": "fabricant de l'équipement contrôlé",
    "equipement.numero_serie": "numéro de série de l'équipement contrôlé",
    "equipement.site": "site du client où l'équipement est installé",
    "reference_rapport": "référence du rapport en vigueur",
    "date_intervention": "jour de l'intervention",
    "date_validation": "date de l'approbation finale du rapport",
    "volume_dose_ml": "volume de dose moyen mesuré après réglage, en ml",
    "volume_nominal_ml": "volume de consigne de l'équipement, en ml",
    "tolerance_ml": "tolérance admise sur le volume de dose, en ml",
    "debit_ml_min": "débit mesuré après réglage, en ml/min",
    "pression_bar": "pression de service mesurée après réglage, en bar",
    "reference_piece": "référence de la pièce remplacée pendant l'intervention",
    "technicien": "technicien responsable de l'intervention, côté prestataire",
    "statut": "décision finale sur l'équipement",
}


def forme_goldset(r):
    """Réponse du corpus (15 clés à plat) -> valeurs du goldset de démonstration."""
    jma = lambda d: None if d is None else "/".join(reversed(d.split("-")))
    tol = r["tolerance_ml"]
    return {
        "equipement": {k: r[k] for k in ("machine", "constructeur", "numero_serie", "site")},
        "reference_rapport": r["reference_rapport"],
        "date_intervention": jma(r["date_intervention"]),
        "date_validation": jma(r["date_validation"]),
        "volume_dose_ml": r["volume_dose_ml"], "volume_nominal_ml": r["volume_nominal_ml"],
        "tolerance_ml": None if tol is None else f"{tol:g}".replace(".", ","),
        "debit_ml_min": r["debit_ml_min"], "pression_bar": r["pression_bar"],
        "reference_piece": r["reference_piece"], "technicien": r["technicien"], "statut": r["statut"],
    }


def construire():
    if DEMO.exists():
        shutil.rmtree(DEMO)
    src = DEMO / "goldset"
    pdfs = sorted(FOURNI.glob("doc-*.pdf"), key=lambda p: hashlib.sha256(p.name.encode()).hexdigest())
    globale, k = {}, 0
    for jeu, n in REPARTITION.items():
        (src / "split" / jeu).mkdir(parents=True)
        liste = []
        for p in pdfs[k:k + n]:
            nom = f"RI_{hashlib.sha256(p.name.encode()).hexdigest()[:8]}.pdf"
            shutil.copy2(p, src / "split" / jeu / nom)
            valeurs = forme_goldset(json.loads((FOURNI / "reponses" / f"{p.stem}.json").read_text()))
            liste.append({"file_name": nom} | valeurs)
            globale[nom] = valeurs
        k += n
        (src / "split" / f"{jeu}_ground_truth.json").write_text(json.dumps(liste, ensure_ascii=False, indent=2))
    (src / "ground_truth.json").write_text(json.dumps(globale, ensure_ascii=False, indent=2))

    # Schéma proposé par l'import, puis « validé » comme le ferait un humain : descriptions, tolérance.
    propose, _ = importer_goldset.proposer(*importer_goldset.analyser(
        importer_goldset.apparier(*importer_goldset.lire_source(src)[:2])[0]))
    for chemin, d in propose["champs"].items():
        d["description"] = DESCRIPTIONS[chemin]
    propose["description"] = ("Rapports d'intervention sur des équipements de dosage (doseuses, pompes doseuses, "
                              "remplisseuses, pipettes automatiques), en français ou en anglais.")
    propose["valide"] = True
    (DEMO / "schema-valide.json").write_text(json.dumps(propose, ensure_ascii=False, indent=2) + "\n")
    (DEMO / "import").mkdir()
    shutil.copy2(DEMO / "schema-valide.json", DEMO / "import" / "schema.json")
    return importer_goldset.importer(src, DEMO / "import")


if __name__ == "__main__":
    print(json.dumps(construire(), ensure_ascii=False, indent=2))
    print(f"goldset de démonstration : {DEMO / 'goldset'} ; import : {DEMO / 'import'}")
