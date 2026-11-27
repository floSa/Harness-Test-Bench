"""Clé virtuelle par essai sur le LiteLLM du banc (plafond par clé : BANC_BUDGET_ESSAI).

    python3 banc-essai/traces/cles.py <alias> [<alias> ...]             crée
    python3 banc-essai/traces/cles.py --supprimer <alias> [<alias> ...]  supprime
    python3 banc-essai/traces/cles.py --depense <alias>                  dépense en dollars (ou null)

L'alias est le nom de l'essai (ou <essai>-relance) : chaque essai a son propre plafond.
Écrit secrets/cle-<alias>.env (BANC_CLE_MODELE=...), jamais affichée. Une clé existante est
gardée. La suppression retire la clé du LiteLLM et son fichier. Modèle permis et plafond en dollars :
BANC_MODELE et BANC_BUDGET_ESSAI de banc-essai/modele.env. Bibliothèque standard seulement.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
URL = "http://127.0.0.1:4100"


def _modele():
    v = {}
    for ligne in (ICI.parent / "modele.env").read_text().splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, valeur = ligne.split("=", 1)
            v[cle.strip()] = valeur.strip().strip('"').strip("'")
    return v


BUDGET = float(_modele().get("BANC_BUDGET_ESSAI", "2"))
MODELES = [_modele()["BANC_MODELE"]]
# Routes permises à une clé d'essai : appels au modèle seulement (ni transfert direct vers un
# fournisseur, ni gestion des clés).
ROUTES = ["/v1/chat/completions", "/chat/completions", "/v1/responses", "/responses", "/v1/models", "/models"]


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
    corps = {"key_alias": harnais, "models": MODELES, "max_budget": BUDGET, "allowed_routes": ROUTES,
             "metadata": {"banc": "essai"}}
    cle = appel("/key/generate", corps)["key"]
    old = os.umask(0o077)
    try:
        f.write_text(f"BANC_CLE_MODELE={cle}\n")
    finally:
        os.umask(old)
    return "créée"


def lire(alias):
    return (ICI / "secrets" / f"cle-{alias}.env").read_text().split("=", 1)[1].strip()


def depense(alias):
    """Dépense enregistrée par LiteLLM pour la clé (dollars), lue avec la clé maître."""
    req = urllib.request.Request(URL + "/key/info?key=" + urllib.parse.quote(lire(alias)),
                                 headers={"Authorization": f"Bearer {maitre()}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["info"].get("spend") or 0.0


def supprimer(alias):
    f = ICI / "secrets" / f"cle-{alias}.env"
    if not f.exists():
        return "absente"
    appel("/key/delete", {"keys": [lire(alias)]})
    f.unlink()
    return "supprimée"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--depense":
        try:
            print(json.dumps(depense(sys.argv[2])))
        except Exception as e:
            print(f"dépense illisible ({type(e).__name__})", file=sys.stderr)
            print("null")
        raise SystemExit(0)
    if sys.argv[1] == "--supprimer":
        echecs = 0
        for a in sys.argv[2:]:
            try:
                print(f"{a} : clé {supprimer(a)}")
            except Exception as e:  # une clé non supprimée n'empêche pas de traiter les suivantes
                echecs += 1
                print(f"{a} : suppression échouée ({type(e).__name__})", file=sys.stderr)
        raise SystemExit(1 if echecs else 0)
    for h in sys.argv[1:]:
        print(f"{h} : clé {creer(h)} (plafond {BUDGET} $, modèles {MODELES})")
