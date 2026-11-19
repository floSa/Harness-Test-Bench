"""Clé virtuelle par harnais sur le LiteLLM du banc (protocole, section 5 : plafond de 2 $ par clé).

    python3 banc-essai/traces/cles.py <harnais> [<harnais> ...]

Écrit secrets/cle-<harnais>.env (BANC_CLE_MODELE=...), jamais affichée. Une clé existante est
gardée. Bibliothèque standard seulement.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
URL = "http://127.0.0.1:4100"
BUDGET = 2.0
MODELES = ["gemma-4-31b"]


def maitre():
    for ligne in (ICI / "secrets" / "maitre.env").read_text().splitlines():
        if ligne.startswith("LITELLM_MASTER_KEY="):
            return ligne.split("=", 1)[1]
    raise SystemExit("clé maître absente : lancer d'abord demarrer.sh")


def creer(harnais):
    f = ICI / "secrets" / f"cle-{harnais}.env"
    if f.exists():
        return "gardée"
    corps = {"key_alias": harnais, "models": MODELES, "max_budget": BUDGET, "metadata": {"banc": "harnais"}}
    req = urllib.request.Request(URL + "/key/generate", data=json.dumps(corps).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {maitre()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        cle = json.loads(r.read())["key"]
    old = os.umask(0o077)
    try:
        f.write_text(f"BANC_CLE_MODELE={cle}\n")
    finally:
        os.umask(old)
    return "créée"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for h in sys.argv[1:]:
        print(f"{h} : clé {creer(h)} (plafond {BUDGET} $, modèles {MODELES})")
