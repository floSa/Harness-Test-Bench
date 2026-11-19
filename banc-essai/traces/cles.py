"""Clé virtuelle par essai sur le LiteLLM du banc (protocole, section 5 : plafond de 2 $ par clé).

    python3 banc-essai/traces/cles.py <alias> [<alias> ...]             crée
    python3 banc-essai/traces/cles.py --supprimer <alias> [<alias> ...]  supprime

L'alias est le nom de l'essai (ou <essai>-relance) : chaque essai a son propre plafond.
Écrit secrets/cle-<alias>.env (BANC_CLE_MODELE=...), jamais affichée. Une clé existante est
gardée. La suppression retire la clé du LiteLLM et son fichier. Bibliothèque standard seulement.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
URL = "http://127.0.0.1:4100"
BUDGET = 2.0
MODELES = ["deepseek-v4.1-flash"]


def maitre():
    for ligne in (ICI / "secrets" / "maitre.env").read_text().splitlines():
        if ligne.startswith("LITELLM_MASTER_KEY="):
            return ligne.split("=", 1)[1]
    raise SystemExit("clé maître absente : lancer d'abord demarrer.sh")


def appel(chemin, corps):
    req = urllib.request.Request(URL + chemin, data=json.dumps(corps).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {maitre()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def creer(harnais):
    f = ICI / "secrets" / f"cle-{harnais}.env"
    if f.exists():
        return "gardée"
    corps = {"key_alias": harnais, "models": MODELES, "max_budget": BUDGET, "metadata": {"banc": "essai"}}
    cle = appel("/key/generate", corps)["key"]
    old = os.umask(0o077)
    try:
        f.write_text(f"BANC_CLE_MODELE={cle}\n")
    finally:
        os.umask(old)
    return "créée"


def supprimer(alias):
    f = ICI / "secrets" / f"cle-{alias}.env"
    if not f.exists():
        return "absente"
    cle = f.read_text().split("=", 1)[1].strip()
    appel("/key/delete", {"keys": [cle]})
    f.unlink()
    return "supprimée"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--supprimer":
        for a in sys.argv[2:]:
            print(f"{a} : clé {supprimer(a)}")
        raise SystemExit(0)
    for h in sys.argv[1:]:
        print(f"{h} : clé {creer(h)} (plafond {BUDGET} $, modèles {MODELES})")
