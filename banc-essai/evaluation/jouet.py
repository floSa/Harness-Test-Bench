"""Notation de la tâche jouet : le paquet soumis est passé aux cas cachés.

Les cas cachés (`tache.json` désigne le paquet ; `cas_caches.json` : appel, valeur attendue ou
exception attendue) ne sont jamais montés dans la cage. Dans la cage (banc-essai/cage/cage.sh,
sans réseau) ne tournent que le paquet soumis et `executant_jouet.py`, qui reçoit les appels sans
les valeurs attendues et renvoie les valeurs obtenues ; la comparaison se fait ici, hors de la
cage. Le code soumis ne peut donc pas réécrire son propre résultat. Sans bubblewrap, la notation
refuse de tourner.

Seuls les fichiers Python du paquet déclaré sont acceptés.
"""
import json
import math
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

ICI = Path(__file__).resolve().parent
CAGE = ICI.parent / "cage"
EXECUTANT = ICI / "executant_jouet.py"
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


def proche(v, attendu):
    """Égalité à la manière de pytest.approx (écart relatif 1e-6, absolu 1e-12)."""
    return isinstance(v, float) and math.isfinite(v) and abs(v - attendu) <= max(1e-6 * abs(attendu), 1e-12)


def noter(fichiers, dossier):
    """Exécute les cas cachés sur les fichiers soumis ; score = part des cas réussis."""
    if shutil.which("bwrap") is None or not (CAGE / "cage.sh").exists():
        raise RuntimeError("notation refusée : bubblewrap ou banc-essai/cage/cage.sh absent")
    cas = json.loads((Path(dossier) / "cas_caches.json").read_text())
    marque = "RESULTAT-" + secrets.token_hex(8)
    with tempfile.TemporaryDirectory(prefix="jouet-") as tmp:
        t = Path(tmp)
        travail, outils, maison = t / "travail", t / "outils", t / "maison"
        for d in (travail, outils, maison):
            d.mkdir()
        for chemin, contenu in fichiers.items():
            f = travail / chemin
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(contenu)
        shutil.copy2(EXECUTANT, outils / "executant.py")
        (outils / "appels.json").write_text(json.dumps({
            "marque": marque, "paquet": config(dossier)["paquet"],
            "appels": [{"fonction": c["fonction"], "args": c["args"]} for c in cas]}, ensure_ascii=False))
        cmd = [str(CAGE / "cage.sh"), "--espace", str(travail), "--maison", str(maison), "--sans-reseau",
               "--lecture", f"{outils}:/opt/jouet", "--duree", str(DUREE_MAX), "--",
               "python3", "-I", "-B", "/opt/jouet/executant.py"]
        try:
            p = subprocess.run(cmd, cwd=travail, capture_output=True, text=True, timeout=DUREE_MAX + 60)
            sortie = p.stdout
        except subprocess.TimeoutExpired:
            sortie = ""
    # Une seule ligne de résultat est attendue : une ligne en plus (écrite par le code soumis) annule tout.
    lignes = [l for l in sortie.splitlines() if l.startswith(marque + " ")]
    obtenus = None
    if len(lignes) == 1:
        try:
            obtenus = json.loads(lignes[0][len(marque) + 1:])
        except json.JSONDecodeError:
            obtenus = None
    if not isinstance(obtenus, list) or len(obtenus) != len(cas):
        return {"score": 0.0, "tests": len(cas), "reussis": 0, "echecs": ["cas non exécutés"], "cage": True}
    echecs, reussis = [], 0
    for c, o in zip(cas, obtenus):
        ok = isinstance(o, dict) and (
            c["exception"] in (o.get("exception") or []) if "exception" in c
            else proche(o.get("valeur"), c["attendu"]))
        if ok:
            reussis += 1
        else:
            echecs.append(c["nom"])
    return {"score": round(reussis / len(cas), 4), "tests": len(cas), "reussis": reussis, "echecs": echecs,
            "cage": True}
