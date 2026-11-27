"""Prépare l'espace de travail neuf d'un essai à partir d'une recette.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/preparer.py \
        --recette goldset|jouet --destination DOSSIER [--goldset DOSSIER]

Contenu : le client `soumettre.py`, et
- goldset : goldset importé (banc-essai/corpus/importer_goldset.py ; dossier --goldset, ou variable
  BANC_GOLDSET, ou banc-essai/corpus/goldset) : ses consignes générées (`recette/consignes.md`),
  `schema.json`, `fourni/` (PDF et réponses) ; rien du test caché ni de la relance ;
- jouet : la recette `banc-essai/recettes/jouet/` (consignes, paquet Python et ses tests visibles).
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
BANC = ICI.parent
RECETTES = ["goldset", "jouet"]


def dossier_goldset(goldset=None):
    return Path(goldset or os.environ.get("BANC_GOLDSET") or BANC / "corpus" / "goldset").resolve()


def preparer(recette, destination, goldset=None):
    dest = Path(destination)
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} existe et n'est pas vide : un essai part d'un dossier vierge")
    if recette == "goldset":
        g = dossier_goldset(goldset)
        if not (g / "recette" / "consignes.md").exists():
            raise SystemExit(f"{g / 'recette' / 'consignes.md'} absent : lancer banc-essai/corpus/consignes_goldset.py")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ICI / "client" / "soumettre.py", dest / "soumettre.py")
    if recette == "jouet":
        shutil.copytree(BANC / "recettes" / "jouet", dest, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        return dest
    shutil.copytree(g / "recette", dest, dirs_exist_ok=True)
    shutil.copy2(g / "schema.json", dest / "schema.json")
    (dest / "fourni" / "reponses").mkdir(parents=True)
    for pdf in sorted((g / "fourni").glob("doc-*.pdf")):
        shutil.copy2(pdf, dest / "fourni" / pdf.name)
        shutil.copy2(g / "fourni" / "reponses" / f"{pdf.stem}.json", dest / "fourni" / "reponses")
    return dest


def main():
    a = argparse.ArgumentParser(description="Prépare l'espace de travail d'un essai")
    a.add_argument("--recette", choices=RECETTES, required=True)
    a.add_argument("--destination", required=True)
    a.add_argument("--goldset", help="goldset importé (défaut : $BANC_GOLDSET ou banc-essai/corpus/goldset)")
    o = a.parse_args()
    d = preparer(o.recette, o.destination, o.goldset)
    print(f"espace prêt : {d} ({sum(1 for _ in d.rglob('*') if _.is_file())} fichiers)")


if __name__ == "__main__":
    sys.exit(main())
