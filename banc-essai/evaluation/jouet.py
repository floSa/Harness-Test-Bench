"""Notation de la tâche jouet : le paquet soumis est passé aux tests cachés.

Seuls les fichiers Python du paquet déclaré dans `tache.json` sont acceptés (pas de conftest,
pas de configuration pytest, pas de sitecustomize) : les tests cachés ne peuvent pas être
contournés par un fichier de configuration soumis.
"""
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

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
        xml = t / "resultat.xml"
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", tmp,
               "-c", str(t / "pytest.ini"), f"--junitxml={xml}", "tests_caches"]
        env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": tmp}
        try:
            subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, timeout=DUREE_MAX)
        except subprocess.TimeoutExpired:
            return {"score": 0.0, "tests": None, "reussis": 0, "echecs": ["délai dépassé"]}
        if not xml.exists():
            return {"score": 0.0, "tests": None, "reussis": 0, "echecs": ["tests non exécutés"]}
        echecs, reussis = [], 0
        for c in ET.parse(xml).getroot().iter("testcase"):
            if any(e.tag in ("failure", "error", "skipped") for e in c):
                echecs.append(c.get("name"))
            else:
                reussis += 1
    # Un test caché non collecté (erreur d'import, par exemple) compte comme échoué.
    n = max(config(dossier)["tests"], reussis + len(echecs))
    return {"score": round(reussis / n, 4), "tests": n, "reussis": reussis, "echecs": echecs}
