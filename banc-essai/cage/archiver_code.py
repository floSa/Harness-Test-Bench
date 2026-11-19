"""Archive le code écrit par le harnais dans les résultats de l'essai, pour la relecture.

    python3 banc-essai/cage/archiver_code.py <espace de travail> <dossier de l'essai>

Copie dans <essai>/code/ les fichiers de code et de documentation de l'espace de travail (.py, .sh,
.md, .toml, .cfg, .ini, .yaml, .yml, .txt, Makefile, Dockerfile), 1 Mo au plus chacun. Jamais :
les PDF, les JSON (réponses produites sur le test caché : avec un bon score, elles révèlent la
vérité), les dossiers de données ou d'environnement (fourni/, test/, sorties, .venv/,
node_modules/, __pycache__/, .git/), ni les fichiers fournis par la recette (consignes.md,
ontologie.md, soumettre.py). Écrit <essai>/code/INDEX.md (fichiers, lignes) et masque les clés.
"""
import shutil
import subprocess
import sys
from pathlib import Path

EXTENSIONS = {".py", ".sh", ".md", ".toml", ".cfg", ".ini", ".yaml", ".yml", ".txt"}
NOMS = {"Makefile", "Dockerfile", "requirements.txt"}
EXCLUS_DOSSIERS = {"fourni", ".venv", "venv", "node_modules", "__pycache__", ".git", ".pytest_cache",
                   ".mypy_cache", ".ruff_cache", ".cache"}
FOURNIS = {"consignes.md", "ontologie.md", "soumettre.py"}
TAILLE_MAX = 1024 * 1024


def garder(f, espace):
    rel = f.relative_to(espace)
    if any(p in EXCLUS_DOSSIERS or p.startswith(("test", "sortie", "output", "resultat", "pred")) for p in rel.parts[:-1]):
        return False
    if rel.as_posix() in FOURNIS or f.is_symlink() or not f.is_file() or f.stat().st_size > TAILLE_MAX:
        return False
    return f.suffix.lower() in EXTENSIONS or f.name in NOMS


def main(espace, essai):
    espace, dest = Path(espace), Path(essai) / "code"
    if dest.exists():
        shutil.rmtree(dest)
    lignes = []
    for f in sorted(espace.rglob("*")):
        if garder(f, espace):
            cible = dest / f.relative_to(espace)
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, cible)
            n = sum(1 for _ in open(f, errors="replace"))
            lignes.append(f"| `{f.relative_to(espace)}` | {n} |")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "INDEX.md").write_text("# Code produit par le harnais\n\nFichiers de code et de documentation de "
                                   "l'espace de travail, copiés à la fin de l'essai (ni PDF, ni JSON, ni données).\n\n"
                                   "| Fichier | Lignes |\n|---|---|\n" + "\n".join(lignes) + "\n")
    subprocess.run([sys.executable, str(Path(__file__).with_name("masquer.py")), str(dest)], check=False,
                   stdout=subprocess.DEVNULL)
    print(f"code archivé : {len(lignes)} fichier(s) dans {dest}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
