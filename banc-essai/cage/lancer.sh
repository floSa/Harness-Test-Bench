#!/usr/bin/env bash
# Lance un essai : un harnais, une recette, dans la cage, avec collecte des journaux.
#
#   banc-essai/cage/lancer.sh <harnais> <recette> [--essai NOM] [--duree S] [--message "..."]
#
# <harnais> : dossier harnais/<harnais>/ (lot 4), ou « sonde » (banc-essai/cage/sonde/, preuves
# du lot 3). Le harnais est lancé dans la cage par /opt/harnais/lancer.sh "<message>".
# <recette> : sans-aide, avec-aide ou jouet.
#
# Étapes : espace de travail neuf (hors du dépôt, dans $BANC_ESPACES, ~/banc-espaces par défaut),
# clé virtuelle du harnais, API de soumission de l'essai, cage, puis collecte dans
# banc-essai/resultats/<essai>/ : essai.json, harnais/ (sorties), traces/appels.jsonl (appels au
# modèle de la clé du harnais pendant l'essai), traces/reseau.jsonl (demandes au mandataire PyPI),
# evaluation/ (journaux de l'API). Ensuite, pour l'extraction, relance du workflow déclaré sur le
# jeu « relance », dans la cage, sans le harnais (relance/, clé <harnais>-relance) ; enfin le
# rapport d'essai (rapport.json, rapport.md).
set -euo pipefail
RACINE="$(cd "$(dirname "$0")/../.." && pwd)"
CAGE="$RACINE/banc-essai/cage"
EVAL="$RACINE/banc-essai/evaluation"
TRACES="$RACINE/banc-essai/traces"
[ $# -ge 2 ] || { sed -n '2,15p' "$0" >&2; exit 2; }
NOM=$1 RECETTE=$2; shift 2
ESSAI="$NOM-$RECETTE-$(date +%Y%m%d-%H%M%S)" DUREE=7200 MESSAGE="Suis les consignes de consignes.md."
while [ $# -gt 0 ]; do
  case "$1" in
    --essai) ESSAI=$2; shift 2 ;;
    --duree) DUREE=$2; shift 2 ;;
    --message) MESSAGE=$2; shift 2 ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done
case "$RECETTE" in sans-aide|avec-aide) TACHE=extraction JEU="$RACINE/banc-essai/corpus/test-cache" ;;
  jouet) TACHE=jouet JEU="$EVAL/taches/jouet" ;; *) echo "recette inconnue : $RECETTE" >&2; exit 2 ;; esac
if [ "$NOM" = sonde ]; then HARNAIS="$CAGE/sonde"; else HARNAIS="$RACINE/harnais/$NOM"; fi
[ -x "$HARNAIS/lancer.sh" ] || { echo "$HARNAIS/lancer.sh introuvable" >&2; exit 1; }

RES="$RACINE/banc-essai/resultats/$ESSAI"
ESPACES="${BANC_ESPACES:-$HOME/banc-espaces}"
ESPACE="$ESPACES/$ESSAI/travail" MAISON="$ESPACES/$ESSAI/maison"
[ -e "$RES" ] && { echo "$RES existe déjà" >&2; exit 1; }
mkdir -p "$RES/harnais" "$RES/traces" "$MAISON"

# Relais du modèle et clé du harnais.
curl -fs http://127.0.0.1:4100/health/liveliness >/dev/null || { echo "LiteLLM du banc arrêté : banc-essai/traces/demarrer.sh" >&2; exit 1; }
python3 "$TRACES/cles.py" "$NOM" >/dev/null
CLE="$TRACES/secrets/cle-$NOM.env"

# Espace neuf et API de l'essai.
uv run -q --project "$EVAL" python "$EVAL/preparer.py" --recette "$RECETTE" --destination "$ESPACE" >/dev/null
if ss -ltnH | awk '{print $4}' | grep -qx '127.0.0.1:8765'; then echo "port 8765 déjà pris" >&2; exit 1; fi
uv run -q --project "$EVAL" python "$EVAL/api.py" --tache "$TACHE" --jeu "$JEU" --sortie "$RES/evaluation" \
  > "$RES/evaluation-api.log" 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT
for _ in $(seq 1 100); do curl -fs http://127.0.0.1:8765/etat >/dev/null 2>&1 && break; sleep 0.1; done

JOURNAL="$TRACES/journaux/appels.jsonl"
LIGNE0=$(wc -l < "$JOURNAL")
DEBUT=$(date --iso-8601=seconds) T0=$(date +%s.%N)
echo "essai $ESSAI : harnais $NOM, recette $RECETTE, espace $ESPACE"
set +e
"$CAGE/cage.sh" --espace "$ESPACE" --maison "$MAISON" --harnais "$HARNAIS" --cle "$CLE" --api \
  --journal-reseau "$RES/traces/reseau.jsonl" --duree "$DUREE" -- /opt/harnais/lancer.sh "$MESSAGE" \
  > "$RES/harnais/stdout.log" 2> "$RES/harnais/stderr.log"
CODE=$?
set -e
FIN=$(date --iso-8601=seconds) DUREE_S=$(python3 -c "import sys,time; print(time.time() - float(sys.argv[1]))" "$T0")
sleep 2   # le journal du LiteLLM est écrit après la réponse

# Appels au modèle de cette clé pendant l'essai.
tail -n +"$((LIGNE0 + 1))" "$JOURNAL" | python3 -c '
import json, sys
nom = sys.argv[1]
for l in sys.stdin:
    if json.loads(l).get("cle") == nom:
        sys.stdout.write(l)' "$NOM" > "$RES/traces/appels.jsonl"
touch "$RES/traces/reseau.jsonl"
python3 - "$RES" "$ESSAI" "$NOM" "$RECETTE" "$TACHE" "$DEBUT" "$FIN" "$DUREE_S" "$CODE" "$ESPACE" "$DUREE" <<'EOF'
import json, sys
res, essai, nom, recette, tache, debut, fin, duree, code, espace, garde = sys.argv[1:]
appels = [json.loads(l) for l in open(f"{res}/traces/appels.jsonl")]
reseau = [json.loads(l) for l in open(f"{res}/traces/reseau.jsonl")]
e = {"essai": essai, "harnais": nom, "recette": recette, "tache": tache, "debut": debut, "fin": fin,
     "duree_s": round(float(duree), 1), "code_retour": int(code), "garde_fou_s": int(garde),
     "garde_fou_atteint": int(code) == 124, "espace": espace,
     "appels_modele": len(appels), "appels_echoues": sum(a["statut"] != "succes" for a in appels),
     "appels_429": sum((a.get("erreur") or {}).get("code") == 429
                       or "RateLimit" in ((a.get("erreur") or {}).get("type") or "") for a in appels),
     "appels_avec_image": sum(a["images"] > 0 for a in appels),
     "jetons_entree": sum(a["jetons_entree"] or 0 for a in appels),
     "jetons_sortie": sum(a["jetons_sortie"] or 0 for a in appels),
     "temps_modele_s": round(sum(a["duree_s"] or 0 for a in appels), 1),
     "demandes_reseau": len(reseau), "demandes_reseau_refusees": sum(not r["accepte"] for r in reseau)}
json.dump(e, open(f"{res}/essai.json", "w"), ensure_ascii=False, indent=2)
print(json.dumps(e, ensure_ascii=False))
EOF
kill $API_PID 2>/dev/null || true

if [ "$TACHE" = extraction ] && [ -f "$RES/evaluation/fin.json" ]; then
  python3 "$TRACES/cles.py" "$NOM-relance" >/dev/null
  LIGNE1=$(wc -l < "$JOURNAL")
  uv run -q --project "$EVAL" python "$EVAL/relancer.py" --espace "$ESPACE" --essai "$RES" \
    --cle "$TRACES/secrets/cle-$NOM-relance.env" --maison "$MAISON" || true
  sleep 2
  tail -n +"$((LIGNE1 + 1))" "$JOURNAL" | python3 -c '
import json, sys
for l in sys.stdin:
    if json.loads(l).get("cle") == sys.argv[1]:
        sys.stdout.write(l)' "$NOM-relance" > "$RES/relance/appels.jsonl" || true
fi
uv run -q --project "$EVAL" python "$EVAL/rapport.py" --essai "$RES" >/dev/null || true
exit "$CODE"
