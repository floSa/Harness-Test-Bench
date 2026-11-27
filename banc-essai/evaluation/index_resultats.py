"""Index des résultats : banc-essai/resultats/README.md (affiché par GitHub à l'ouverture du dossier).

    uv run --project banc-essai/evaluation python banc-essai/evaluation/index_resultats.py [--dossier DOSSIER]

DOSSIER : banc-essai/resultats (défaut) ou banc-essai/resultats-goldset (essais sur un goldset de
l'entreprise, hors git).

Une ligne par essai, à partir de essai.json, rapport.json et relance/resultat.json. Appelé à la fin
de chaque essai par banc-essai/cage/lancer.sh.
"""
import argparse
import json
from pathlib import Path

RESULTATS = Path(__file__).resolve().parents[1] / "resultats"
NATURES = [("preuve-cage", "preuve de la cage (sonde)"), ("verif-", "vérification du lanceur (faux harnais)"),
           ("essai-factice", "essai factice (fausses solutions)"), ("jouet-factice", "essai factice (fausses solutions)")]


def lire(f):
    try:
        return json.loads(f.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def pc(x):
    return "" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def nature(nom, e):
    for prefixe, texte in NATURES:
        if nom.startswith(prefixe):
            return texte
    if e and e.get("tache") == "jouet":
        return "tâche jouet (mise au point)"
    return "essai de campagne"


def ligne(d):
    e, r = lire(d / "essai.json"), lire(d / "rapport.json") or {}
    rl = r.get("relance") or {}
    cout = e.get("cout_usd") if e else None
    return {
        "essai": d.name, "nature": nature(d.name, e),
        "debut": (e or {}).get("debut", "")[:16].replace("T", " "),
        "harnais": (e or {}).get("harnais", ""), "recette": (e or {}).get("recette", ""),
        "score": pc(r.get("score_final")), "relance": pc((rl.get("note") or {}).get("score")),
        "duree": f"{e['duree_s']:.0f} s" if e and e.get("duree_s") is not None else "",
        "appels": (e or {}).get("appels_modele", ""),
        "cout": f"{cout:.4f} $".replace(".", ",") if cout is not None else "",
    }


def main():
    a = argparse.ArgumentParser(description="Index des résultats")
    a.add_argument("--dossier", default=str(RESULTATS))
    resultats = Path(a.parse_args().dossier)
    dossiers = sorted((d for d in resultats.iterdir() if d.is_dir()), key=lambda d: (lire(d / "essai.json") or {}).get("debut", ""))
    lignes = [ligne(d) for d in dossiers]
    L = ["# Résultats des essais", "",
         "Un dossier par essai. Dans chaque dossier : `rapport.md` (synthèse lisible), `essai.json` (mesures de "
         "construction : durée, appels, jetons, coût, ressources), `harnais/stdout.log` (trace de la session), "
         "`traces/` (appels au modèle, réseau), `evaluation/` (soumissions), `relance/` (workflow relancé). "
         "Explication du banc : [protocole expliqué](../../documentations/protocole-explique.md).", "",
         "Page régénérée à la fin de chaque essai (`banc-essai/evaluation/index_resultats.py`).", "",
         "| Essai | Nature | Début | Harnais | Recette | Score final | Score de relance | Durée | Appels au modèle | Coût |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for x in lignes:
        L.append(f"| [{x['essai']}]({x['essai']}/rapport.md) | {x['nature']} | {x['debut']} | {x['harnais']} | "
                 f"{x['recette']} | {x['score']} | {x['relance']} | {x['duree']} | {x['appels']} | {x['cout']} |")
    L += ["", "Score final : part des champs justes sur le test caché (tâche jouet : part des cas cachés réussis). "
          "Score de relance : même mesure, workflow relancé sans le harnais sur le jeu de relance (documents neufs).", ""]
    (resultats / "README.md").write_text("\n".join(L))
    print(f"index écrit : {resultats / 'README.md'} ({len(lignes)} essais)")


if __name__ == "__main__":
    main()
