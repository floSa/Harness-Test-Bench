"""Suivi d'un essai en cours, en une ligne (bibliothèque standard seulement).

    python3 banc-essai/cage/suivi.py <essai>

Lit le journal du LiteLLM (appels de la clé de l'essai), les soumissions de l'API, la trace du
harnais et l'occupation du disque ; n'affiche aucun contenu, seulement des comptes.
"""
import json
import os
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
essai = sys.argv[1]
res = RACINE / "banc-essai/resultats" / essai
appels = []
for l in open(RACINE / "banc-essai/traces/journaux/appels.jsonl"):
    if f'"cle": "{essai}"' in l:
        try:
            appels.append(json.loads(l))
        except json.JSONDecodeError:
            pass
soum = [json.loads(l) for l in open(res / "evaluation/soumissions.jsonl")] if (res / "evaluation/soumissions.jsonl").exists() else []
acceptees = [s for s in soum if s["statut"] == "acceptee"]
trace = res / "harnais/stdout.log"
if not trace.exists() and (res / "harnais/stdout.log.gz").exists():
    trace = res / "harnais/stdout.log.gz"
age = int(time.time() - trace.stat().st_mtime) if trace.exists() else None
debut = (res / "evaluation-api.log").stat().st_mtime if (res / "evaluation-api.log").exists() else time.time()
print(f"{time.strftime('%H:%M')} {essai} : {int((time.time() - debut) / 60)} min, {len(appels)} appels "
      f"({sum(a['statut'] != 'succes' for a in appels)} échecs), {sum(a.get('cout') or 0 for a in appels):.4f} $, "
      f"soumissions {len(acceptees)} acceptées / {len(soum)} ({', '.join(str(s['score']) for s in acceptees)}), "
      f"fin {'oui' if (res / 'evaluation/fin.json').exists() else 'non'}, "
      f"trace {trace.stat().st_size // 1024 if trace.exists() else 0} Ko (dernière écriture il y a {age} s), "
      f"terminé {'oui' if (res / 'essai.json').exists() else 'non'}")
