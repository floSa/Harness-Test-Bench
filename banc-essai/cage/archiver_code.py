"""Archive le code écrit par le harnais dans les résultats de l'essai, pour la relecture.

    python3 banc-essai/cage/archiver_code.py <espace de travail> <dossier de l'essai>

Copie dans <essai>/code/ les fichiers de code et de documentation de l'espace de travail (.py, .sh,
.md, .toml, .cfg, .ini, .yaml, .yml, requirements*.txt, Makefile, Dockerfile), 1 Mo au plus chacun. Jamais :
les fichiers texte extraits des documents (.txt, ou nom contenant « doc-NNN »),
les PDF, les JSON (réponses produites sur le test caché : avec un bon score, elles révèlent la
vérité), les dossiers de données ou d'environnement (fourni/, test/, sorties, .venv/,
node_modules/, __pycache__/, .git/), ni les fichiers fournis par la recette (consignes.md,
ontologie.md, soumettre.py). Un fichier qui cite un document du test caché ou de la relance (par
son identifiant) peut contenir des réponses écrites en dur, donc la vérité : il va dans
<essai>/code-cache/ (hors git) et l'INDEX le signale. Écrit <essai>/code/INDEX.md (fichiers,
lignes) et masque les clés.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXTENSIONS = {".py", ".sh", ".md", ".toml", ".cfg", ".ini", ".yaml", ".yml"}
NOMS = {"Makefile", "Dockerfile"}
# Tout fichier dont le nom évoque un document du corpus (« doc-004 », « doc_004 ») est exclu : il peut
# contenir le texte d'un document du test caché, qui ne doit jamais être versionné.
DOCUMENT = re.compile(r"doc[-_]?\d{2,3}", re.IGNORECASE)
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
    if DOCUMENT.search(f.name) or any(DOCUMENT.search(p) for p in rel.parts[:-1]):
        return False
    return f.suffix.lower() in EXTENSIONS or f.name in NOMS or re.fullmatch(r"requirements.*\.txt", f.name)


RACINE = Path(__file__).resolve().parents[2]


def identifiants_caches():
    ids = set()
    for jeu in ("test-cache", "relance"):
        ids |= {f.stem for f in (RACINE / "banc-essai/corpus" / jeu).glob("*.pdf")}
    return re.compile(r"\b(" + "|".join(sorted(ids)) + r")\b") if ids else None


def main(espace, essai):
    espace, dest, ecart = Path(espace), Path(essai) / "code", Path(essai) / "code-cache"
    for d in (dest, ecart):
        if d.exists():
            shutil.rmtree(d)
    caches = identifiants_caches()
    lignes, ecartes = [], []
    for f in sorted(espace.rglob("*")):
        if garder(f, espace):
            texte = f.read_text(errors="replace")
            if caches and caches.search(texte):
                cible = ecart / f.relative_to(espace)
                cible.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, cible)
                ecartes.append(f"| `{f.relative_to(espace)}` | cite un document du test caché ou de la relance |")
                continue
            cible = dest / f.relative_to(espace)
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, cible)
            n = sum(1 for _ in open(f, errors="replace"))
            lignes.append(f"| `{f.relative_to(espace)}` | {n} |")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "INDEX.md").write_text("# Code produit par le harnais\n\nFichiers de code et de documentation de "
                                   "l'espace de travail, copiés à la fin de l'essai (ni PDF, ni JSON, ni données).\n\n"
                                   "| Fichier | Lignes |\n|---|---|\n" + "\n".join(lignes) + "\n"
                                   + ("\n## Fichiers écartés (hors git, dans code-cache/)\n\n| Fichier | Raison |\n"
                                      "|---|---|\n" + "\n".join(ecartes) + "\n" if ecartes else ""))
    subprocess.run([sys.executable, str(Path(__file__).with_name("masquer.py")), str(dest)], check=False,
                   stdout=subprocess.DEVNULL)
    print(f"code archivé : {len(lignes)} fichier(s) dans {dest}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
