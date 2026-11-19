"""Prépare l'espace de travail neuf d'un essai à partir d'une recette.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/preparer.py \
        --recette sans-aide|avec-aide|jouet --destination DOSSIER

Contenu : la recette (`consignes.md`, et `ontologie.md` pour « avec aide ») ; le client
`soumettre.py` ; pour l'extraction, `fourni/` avec les 35 PDF et leurs réponses seulement (ni la
vérité détaillée, ni les annotations). Rien du test caché ni de la relance.
"""
import argparse
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
BANC = ICI.parent
RECETTES = ["sans-aide", "avec-aide", "jouet"]


def preparer(recette, destination):
    dest = Path(destination)
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} existe et n'est pas vide : un essai part d'un dossier vierge")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BANC / "recettes" / recette, dest, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    shutil.copy2(ICI / "client" / "soumettre.py", dest / "soumettre.py")
    if recette != "jouet":
        source = BANC / "corpus" / "fourni"
        (dest / "fourni" / "reponses").mkdir(parents=True)
        for pdf in sorted(source.glob("doc-*.pdf")):
            shutil.copy2(pdf, dest / "fourni" / pdf.name)
            shutil.copy2(source / "reponses" / f"{pdf.stem}.json", dest / "fourni" / "reponses")
    return dest


def main():
    a = argparse.ArgumentParser(description="Prépare l'espace de travail d'un essai")
    a.add_argument("--recette", choices=RECETTES, required=True)
    a.add_argument("--destination", required=True)
    o = a.parse_args()
    d = preparer(o.recette, o.destination)
    print(f"espace prêt : {d} ({sum(1 for _ in d.rglob('*') if _.is_file())} fichiers)")


if __name__ == "__main__":
    sys.exit(main())
