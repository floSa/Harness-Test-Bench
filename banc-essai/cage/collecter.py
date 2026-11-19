"""Collecte d'un essai, appelée par lancer.sh (bibliothèque standard seulement).

    collecter.py repartir ESSAI RES      lignes du journal (entrée standard) réparties par alias :
                                         ESSAI -> RES/traces/appels.jsonl,
                                         ESSAI-relance -> RES/relance/appels.jsonl (si RES/relance existe)
    collecter.py essai RES ESSAI NOM RECETTE TACHE DEBUT FIN DUREE CODE ESPACE GARDE DEPENSE
                       DEPENSE_RELANCE HARNAIS
                                         écrit RES/essai.json
"""
import datetime
import json
import os
import sys


def repartir(essai, res):
    sorties = {essai: open(f"{res}/traces/appels.jsonl", "w")}
    if os.path.isdir(f"{res}/relance"):
        sorties[essai + "-relance"] = open(f"{res}/relance/appels.jsonl", "w")
    for ligne in sys.stdin:
        try:
            f = sorties.get(json.loads(ligne).get("cle"))
        except json.JSONDecodeError:
            continue
        if f:
            f.write(ligne)
    for f in sorties.values():
        f.close()


def horodatage(x):
    return datetime.datetime.fromisoformat(x).timestamp() if x else None


def est_429(a):
    e = a.get("erreur") or {}
    return e.get("code") == 429 or "RateLimit" in (e.get("type") or "")


def temps_union(appels):
    """Temps dans le modèle : union des intervalles d'appel (des appels parallèles comptent une fois)."""
    iv = sorted((horodatage(a["debut"]), horodatage(a["fin"])) for a in appels if a.get("debut") and a.get("fin"))
    total, cour = 0.0, None
    for d, f in iv:
        if cour and d <= cour[1]:
            cour[1] = max(cour[1], f)
        else:
            total += (cour[1] - cour[0]) if cour else 0
            cour = [d, f]
    return total + ((cour[1] - cour[0]) if cour else 0)


def attente_429(appels):
    """Attente due aux quotas : de la fin de chaque refus 429 au début de l'appel suivant."""
    ordre = sorted((a for a in appels if a.get("debut")), key=lambda a: horodatage(a["debut"]))
    total = 0.0
    for k, a in enumerate(ordre):
        if est_429(a) and k + 1 < len(ordre) and a.get("fin"):
            total += max(0.0, horodatage(ordre[k + 1]["debut"]) - horodatage(a["fin"]))
    return total


def essai(res, essai, nom, recette, tache, debut, fin, duree, code, espace, garde, depense, depense_relance,
          harnais):
    appels = [json.loads(l) for l in open(f"{res}/traces/appels.jsonl")]
    reseau = [json.loads(l) for l in open(f"{res}/traces/reseau.jsonl")]
    version = None
    if os.path.isfile(f"{harnais}/version"):
        version = open(f"{harnais}/version").read().strip()[:200]
    cout = sum(a.get("cout") or 0 for a in appels)
    dep = json.loads(depense or "null")
    e = {"essai": essai, "harnais": nom, "version_harnais": version, "recette": recette, "tache": tache,
         "debut": debut, "fin": fin, "duree_s": round(float(duree), 1), "code_retour": int(code),
         "garde_fou_s": int(garde), "garde_fou_atteint": int(code) == 124, "espace": espace,
         "modeles": sorted({a["modele"] for a in appels if a.get("modele")}),
         "fournisseurs": sorted({a["fournisseur"] for a in appels if a.get("fournisseur")}),
         "appels_modele": len(appels), "appels_echoues": sum(a["statut"] != "succes" for a in appels),
         "appels_429": sum(est_429(a) for a in appels), "attente_429_s": round(attente_429(appels), 1),
         "appels_avec_image": sum(a["images"] > 0 for a in appels),
         "jetons_entree": sum(a["jetons_entree"] or 0 for a in appels),
         "jetons_cache": sum(a.get("jetons_cache") or 0 for a in appels),
         "jetons_sortie": sum(a["jetons_sortie"] or 0 for a in appels),
         "cout_usd": round(cout, 6),
         "cout_openrouter_usd": round(sum(a.get("cout_openrouter") or 0 for a in appels), 6),
         "depense_cle_usd": dep,
         "ecart_depense_journal_usd": round(dep - cout, 6) if isinstance(dep, (int, float)) else None,
         "depense_cle_relance_usd": json.loads(depense_relance or "null"),
         "temps_modele_s": round(temps_union(appels), 1),
         "demandes_reseau": len(reseau), "demandes_reseau_refusees": sum(not r["accepte"] for r in reseau)}
    with open(f"{res}/essai.json", "w") as f:
        json.dump(e, f, ensure_ascii=False, indent=2)
    print(json.dumps(e, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1:2] == ["repartir"]:
        repartir(*sys.argv[2:4])
    elif sys.argv[1:2] == ["essai"]:
        essai(*sys.argv[2:])
    else:
        raise SystemExit(__doc__)
