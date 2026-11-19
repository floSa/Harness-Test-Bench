"""Notation de la tâche jouet : le paquet soumis est passé aux tests cachés.

Les tests tournent dans la cage du banc (banc-essai/cage/cage.sh, sans réseau, pytest monté en
lecture seule depuis banc-essai/cage/outils/) ; sans bubblewrap ni outils, dans un simple
sous-processus, et le résultat le signale (`"cage": false`).

Seuls les fichiers Python du paquet déclaré dans `tache.json` sont acceptés (pas de conftest,
pas de configuration pytest, pas de sitecustomize) : les tests cachés ne peuvent pas être
contournés par un fichier de configuration soumis.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

CAGE = Path(__file__).resolve().parents[1] / "cage"
PYTEST_CAGE = CAGE / "outils" / "pytest"
TAILLE_MAX = 256 * 1024
DUREE_MAX = 120


def config(dossier):
    return json.loads((Path(dossier) / "tache.json").read_text())


def valider(fichiers, dossier):
    paquet = config(dossier)["paquet"]
    if not isinstance(fichiers, dict) or not fichiers:
        return ["les fichiers doivent être un objet {chemin: contenu} non vide"]
    err = []
    taille = 0
    for chemin, contenu in fichiers.items():
        p = PurePosixPath(chemin)
        if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0] != paquet or p.suffix != ".py":
            err.append(f"{chemin} : seuls les fichiers .py du dossier {paquet}/ sont acceptés")
        if not isinstance(contenu, str):
            err.append(f"{chemin} : contenu texte attendu")
        else:
            taille += len(contenu.encode())
    if taille > TAILLE_MAX:
        err.append(f"soumission trop lourde ({taille} octets, maximum {TAILLE_MAX})")
    if f"{paquet}/__init__.py" not in fichiers:
        err.append(f"{paquet}/__init__.py manquant")
    return err


def noter(fichiers, dossier):
    """Lance les tests cachés sur les fichiers soumis ; score = part des tests réussis."""
    caches = Path(dossier) / "tests_caches"
    with tempfile.TemporaryDirectory(prefix="jouet-") as tmp:
        t = Path(tmp)
        for chemin, contenu in fichiers.items():
            f = t / chemin
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(contenu)
        (t / "tests_caches").mkdir()
        for f in caches.glob("test_*.py"):
            (t / "tests_caches" / f.name).write_text(f.read_text())
        (t / "pytest.ini").write_text("[pytest]\n")
        sortie = Path(tempfile.mkdtemp(prefix="jouet-sortie-"))
        maison = Path(tempfile.mkdtemp(prefix="jouet-maison-"))
        try:
            cage = shutil.which("bwrap") is not None and PYTEST_CAGE.is_dir()
            opts = ["-q", "-p", "no:cacheprovider", "-c", "pytest.ini", "tests_caches"]
            if cage:
                cmd = [str(CAGE / "cage.sh"), "--espace", tmp, "--maison", str(maison), "--sortie", str(sortie),
                       "--sans-reseau", "--lecture", f"{PYTEST_CAGE}:/opt/pytest", "--duree", str(DUREE_MAX), "--",
                       "env", "PYTHONPATH=/opt/pytest:/travail", "PYTHONDONTWRITEBYTECODE=1", "python3", "-m",
                       "pytest", "--rootdir", "/travail", "--junitxml=/sortie/resultat.xml", *opts]
                env = None
            else:
                cmd = [sys.executable, "-m", "pytest", "--rootdir", tmp, f"--junitxml={sortie / 'resultat.xml'}", *opts]
                env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": tmp}
            try:
                subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, timeout=DUREE_MAX + 60)
            except subprocess.TimeoutExpired:
                return {"score": 0.0, "tests": None, "reussis": 0, "echecs": ["délai dépassé"], "cage": cage}
            xml = sortie / "resultat.xml"
            if not xml.exists():
                return {"score": 0.0, "tests": None, "reussis": 0, "echecs": ["tests non exécutés"], "cage": cage}
            racine = ET.parse(xml).getroot()
        finally:
            shutil.rmtree(sortie, ignore_errors=True)
            shutil.rmtree(maison, ignore_errors=True)
        echecs, reussis = [], 0
        for c in racine.iter("testcase"):
            if any(e.tag in ("failure", "error", "skipped") for e in c):
                echecs.append(c.get("name"))
            else:
                reussis += 1
    # Un test caché non collecté (erreur d'import, par exemple) compte comme échoué.
    n = max(config(dossier)["tests"], reussis + len(echecs))
    return {"score": round(reussis / n, 4), "tests": n, "reussis": reussis, "echecs": echecs, "cage": cage}
