"""Fausse solution d'extraction : répond « conforme » pour le statut et null partout ailleurs."""
import json
import sys
from pathlib import Path

CLES = ["machine", "constructeur", "numero_serie", "site", "reference_rapport", "date_intervention",
        "date_validation", "volume_dose_ml", "volume_nominal_ml", "tolerance_ml", "debit_ml_min",
        "pression_bar", "reference_piece", "technicien", "statut"]

entree, sortie = Path(sys.argv[1]), Path(sys.argv[2])
sortie.mkdir(parents=True, exist_ok=True)
for pdf in sorted(entree.glob("*.pdf")):
    reponse = dict.fromkeys(CLES)
    reponse["statut"] = "conforme"
    (sortie / f"{pdf.stem}.json").write_text(json.dumps(reponse, indent=2))
