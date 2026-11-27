"""Prépare l'espace de travail neuf d'un essai à partir d'une recette.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/preparer.py \
        --recette sans-aide|avec-aide|dossiers|goldset|jouet --destination DOSSIER [--goldset DOSSIER]

Contenu : la recette (`consignes.md`, et `ontologie.md` pour « avec aide ») ; le client
`soumettre.py` ; pour l'extraction, `fourni/` avec les 35 PDF et leurs réponses seulement (ni la
vérité détaillée, ni les annotations) ; pour les dossiers, `fourni/dos-XXX/` (pièces) et
`fourni/reponses/`. Pour un goldset importé (banc-essai/corpus/importer_goldset.py ; dossier
--goldset, ou variable BANC_GOLDSET, ou banc-essai/corpus/goldset) : ses consignes générées
(`recette/consignes.md`), `schema.json`, `fourni/` (PDF et réponses). Rien du test caché ni de la relance.
"""
import os
import argparse
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
BANC = ICI.parent
RECETTES = ["sans-aide", "avec-aide", "dossiers", "goldset", "jouet"]


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
    if recette == "goldset":
        shutil.copytree(g / "recette", dest, dirs_exist_ok=True)
        shutil.copy2(g / "schema.json", dest / "schema.json")
    else:
        shutil.copytree(BANC / "recettes" / recette, dest, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    shutil.copy2(ICI / "client" / "soumettre.py", dest / "soumettre.py")
    if recette == "dossiers":
        source = BANC / "corpus" / "dossiers" / "fourni"
        (dest / "fourni" / "reponses").mkdir(parents=True)
        for d in sorted(p for p in source.glob("dos-*") if p.is_dir()):
            shutil.copytree(d, dest / "fourni" / d.name)
            shutil.copy2(source / "reponses" / f"{d.name}.json", dest / "fourni" / "reponses")
    elif recette != "jouet":
        source = dossier_goldset(goldset) / "fourni" if recette == "goldset" else BANC / "corpus" / "fourni"
        (dest / "fourni" / "reponses").mkdir(parents=True)
        for pdf in sorted(source.glob("doc-*.pdf")):
            shutil.copy2(pdf, dest / "fourni" / pdf.name)
            shutil.copy2(source / "reponses" / f"{pdf.stem}.json", dest / "fourni" / "reponses")
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
