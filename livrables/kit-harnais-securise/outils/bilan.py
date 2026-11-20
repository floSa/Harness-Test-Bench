"""Bilan d'une session de test, lu dans journaux/ (aucun contenu, seulement des comptes).

    python3 outils/bilan.py
"""
import collections
import json
from pathlib import Path

ICI = Path(__file__).resolve().parents[1] / "journaux"


def lire(nom):
    f = ICI / nom
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []


appels = lire("appels.jsonl")
transmis = [a for a in appels if "refus_du_relais" not in a]
print(f"Appels au modèle : {len(transmis)} transmis au portail, "
      f"{sum(1 for a in transmis if a.get('statut') != 200)} en erreur, "
      f"{len(appels) - len(transmis)} refusés par le relais")
print(f"Jetons : {sum(a.get('jetons_entree') or 0 for a in transmis)} envoyés, "
      f"{sum(a.get('jetons_sortie') or 0 for a in transmis)} produits, "
      f"cumul {appels[-1].get('jetons_cumules') if appels else 0}")
print(f"Durée cumulée des appels : {sum(a.get('duree_s') or 0 for a in transmis) / 60:.1f} min")
for raison, n in collections.Counter(a["refus_du_relais"] for a in appels if "refus_du_relais" in a).items():
    print(f"  refus du relais : {raison} ({n})")
erreurs = collections.Counter(a.get("statut") for a in transmis if a.get("statut") != 200)
for code, n in erreurs.items():
    print(f"  erreur du portail ou du réseau : {code} ({n})")
tele = lire("telechargements.jsonl")
acceptes = [t for t in tele if t.get("verdict") == "accepté"]
print(f"Téléchargements : {len(acceptes)} connexions acceptées, "
      f"{sum(t.get('octets_recus') or 0 for t in acceptes) / 1e6:.1f} Mo reçus")
for hote, n in collections.Counter(t.get("hote") or t.get("demande") for t in tele if t.get("verdict") != "accepté").items():
    print(f"  refusé : {hote} ({n})")
