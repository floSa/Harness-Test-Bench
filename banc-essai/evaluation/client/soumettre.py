"""Client de l'API de soumission du banc (bibliothèque standard seulement).

Adresse : variable d'environnement BANC_API (par défaut http://127.0.0.1:8765).

    python3 soumettre.py etat
    python3 soumettre.py documents DOSSIER        télécharge les PDF du test caché dans DOSSIER
                                                 (dossiers : un sous-dossier par dossier)
    python3 soumettre.py soumettre DOSSIER        extraction, goldset : un fichier <id>.json par document
                                                 dossiers : un fichier <dossier>.json par dossier
                                                 jouet : le dossier du paquet Python
    python3 soumettre.py fin --soumission N [--score-validation X] [--commande "..."]
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("BANC_API", "http://127.0.0.1:8765").rstrip("/")


def appel(methode, chemin, corps=None, brut=False):
    donnees = None if corps is None else json.dumps(corps, ensure_ascii=False).encode()
    req = urllib.request.Request(API + chemin, data=donnees, method=methode,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            contenu = r.read()
            return r.status, contenu if brut else json.loads(contenu)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def afficher(code, obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return 0 if code == 200 else 1


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = a.add_subparsers(dest="cmd", required=True)
    sp.add_parser("etat")
    sp.add_parser("documents").add_argument("dossier")
    sp.add_parser("soumettre").add_argument("dossier")
    f = sp.add_parser("fin")
    f.add_argument("--soumission", type=int, required=True)
    f.add_argument("--score-validation", type=float)
    f.add_argument("--commande")
    f.add_argument("--commentaire")
    o = a.parse_args()

    if o.cmd == "etat":
        return afficher(*appel("GET", "/etat"))
    if o.cmd == "documents":
        d = Path(o.dossier)
        _, etat = appel("GET", "/etat")
        if etat["tache"] == "dossiers":
            code, r = appel("GET", "/dossiers")
            if code != 200:
                return afficher(code, r)
            for i, pieces in r["dossiers"].items():
                (d / i).mkdir(parents=True, exist_ok=True)
                for p in pieces:
                    _, pdf = appel("GET", f"/dossiers/{i}/{p}", brut=True)
                    (d / i / p).write_bytes(pdf)
            print(f"{len(r['dossiers'])} dossiers écrits dans {d}")
            return 0
        code, r = appel("GET", "/documents")
        if code != 200:
            return afficher(code, r)
        d.mkdir(parents=True, exist_ok=True)
        for i in r["documents"]:
            _, pdf = appel("GET", f"/documents/{i}.pdf", brut=True)
            (d / f"{i}.pdf").write_bytes(pdf)
        print(f"{len(r['documents'])} documents écrits dans {d}")
        return 0
    if o.cmd == "soumettre":
        d = Path(o.dossier)
        _, etat = appel("GET", "/etat")
        if etat["tache"] in ("extraction", "dossiers", "goldset"):
            reponses = {}
            for f in sorted(d.glob("*.json")):
                try:
                    reponses[f.stem] = json.loads(f.read_text())
                except json.JSONDecodeError as e:
                    print(f"{f.name} : JSON illisible ({e})", file=sys.stderr)
                    return 1
            return afficher(*appel("POST", "/soumissions", {"reponses": reponses}))
        fichiers = {f"{d.name}/{p.relative_to(d).as_posix()}": p.read_text()
                    for p in sorted(d.rglob("*.py")) if "__pycache__" not in p.parts}
        return afficher(*appel("POST", "/soumissions", {"fichiers": fichiers}))
    if o.cmd == "fin":
        return afficher(*appel("POST", "/fin", {"soumission_finale": o.soumission,
                                                "score_validation": o.score_validation,
                                                "commande": o.commande, "commentaire": o.commentaire}))


if __name__ == "__main__":
    sys.exit(main())
