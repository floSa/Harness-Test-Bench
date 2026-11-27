#!/usr/bin/env bash
# Lance un essai : un harnais, une recette, dans la cage, avec collecte des journaux.
#
#   banc-essai/cage/lancer.sh <harnais> <recette> [--essai NOM] [--duree S] [--message "..."]
#
# <harnais> : dossier harnais/<harnais>/ (lot 4), ou « sonde » (banc-essai/cage/sonde/, preuves
# du lot 3), ou « factice » (banc-essai/cage/factice/, vérification du lanceur sur l'extraction). Le harnais est lancé dans la cage par /opt/harnais/lancer.sh "<message>".
# <recette> : sans-aide, avec-aide, dossiers, goldset ou jouet. goldset : jeu importé par
# banc-essai/corpus/importer_goldset.py, dans $BANC_GOLDSET (banc-essai/corpus/goldset par défaut),
# avec un schéma validé et des consignes générées (banc-essai/corpus/consignes_goldset.py).
#
# Étapes : espace de travail neuf (hors du dépôt, dans $BANC_ESPACES, ~/banc-espaces par défaut),
# clé virtuelle propre à l'essai (alias = nom de l'essai, plafond de 2 $, dépense relevée puis clé
# supprimée dès la sortie du harnais), API de soumission vérifiée, cage, puis collecte dans
# banc-essai/resultats/<essai>/ : essai.json, harnais/ (sorties), traces/appels.jsonl (appels au
# modèle de la clé de l'essai), traces/reseau.jsonl (demandes au mandataire PyPI),
# evaluation/ (journaux de l'API). Ensuite, pour l'extraction, relance du workflow déclaré sur le
# jeu « relance », dans la cage, sans le harnais (relance/, clé <essai>-relance) ; enfin le
# rapport d'essai (rapport.json, rapport.md).
set -euo pipefail
RACINE="$(cd "$(dirname "$0")/../.." && pwd)"
CAGE="$RACINE/banc-essai/cage"
EVAL="$RACINE/banc-essai/evaluation"
TRACES="$RACINE/banc-essai/traces"
[ $# -ge 2 ] || { sed -n '2,17p' "$0" >&2; exit 2; }
NOM=$1 RECETTE=$2 GOLDSET=; shift 2
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
  dossiers) TACHE=dossiers JEU="$RACINE/banc-essai/corpus/dossiers/test-cache" ;;
  goldset) TACHE=goldset GOLDSET=$(realpath -m "${BANC_GOLDSET:-$RACINE/banc-essai/corpus/goldset}") JEU="$GOLDSET/test-cache"
    python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("valide") else 1)' "$GOLDSET/schema.json" 2>/dev/null \
      || { echo "goldset : $GOLDSET/schema.json absent ou non validé (banc-essai/documentation/goldset.md)" >&2; exit 1; }
    [ -f "$GOLDSET/recette/consignes.md" ] || { echo "goldset : consignes absentes (banc-essai/corpus/consignes_goldset.py)" >&2; exit 1; } ;;
  jouet) TACHE=jouet JEU="$EVAL/taches/jouet" ;; *) echo "recette inconnue : $RECETTE" >&2; exit 2 ;; esac
case "$NOM" in sonde|factice) HARNAIS="$CAGE/$NOM" ;; *) HARNAIS="$RACINE/harnais/$NOM" ;; esac
[ -x "$HARNAIS/lancer.sh" ] || { echo "$HARNAIS/lancer.sh introuvable" >&2; exit 1; }

RES="$RACINE/banc-essai/resultats/$ESSAI"
ESPACES="${BANC_ESPACES:-$HOME/banc-espaces}"
ESPACE="$ESPACES/$ESSAI/travail" MAISON="$ESPACES/$ESSAI/maison" TMP_ESSAI="$ESPACES/$ESSAI/tmp"
# Cadre de ressources (protocole, section 5), annoncé dans les consignes.
MEMOIRE=16G DISQUE_MAX=$((30 * 1000 * 1000 * 1000)) TELECHARGEMENT_MAX=$((10 * 1000 * 1000 * 1000))

# Un seul essai à la fois sur la machine : verrou tenu jusqu'à la fin du script.
mkdir -p "$ESPACES"
exec 9> "$ESPACES/.verrou"
flock -n 9 || { echo "un autre essai tourne déjà (verrou $ESPACES/.verrou)" >&2; exit 1; }

[ -e "$RES" ] && { echo "$RES existe déjà" >&2; exit 1; }
mkdir -p "$RES/harnais" "$RES/traces" "$MAISON" "$TMP_ESSAI"

# Relais du modèle et clé de l'essai.
curl -fs http://127.0.0.1:4100/health/liveliness >/dev/null || { echo "LiteLLM du banc arrêté : banc-essai/traces/demarrer.sh" >&2; exit 1; }
API_PID=
fin_de_script() {
  if [ -n "$API_PID" ]; then kill "$API_PID" 2>/dev/null || true; fi
  python3 "$TRACES/cles.py" --supprimer "$ESSAI" "$ESSAI-relance" >/dev/null 2>&1 || true
}
trap fin_de_script EXIT
python3 "$TRACES/cles.py" "$ESSAI" >/dev/null
CLE="$TRACES/secrets/cle-$ESSAI.env"

# Espace neuf et API de l'essai (port 8765 libre sur toute adresse, API vérifiée avant de lancer).
uv run -q --project "$EVAL" python "$EVAL/preparer.py" --recette "$RECETTE" --destination "$ESPACE" \
  ${GOLDSET:+--goldset "$GOLDSET"} >/dev/null
if [ -n "$(ss -ltnH 'sport = :8765')" ]; then echo "port 8765 déjà pris" >&2; exit 1; fi
uv run -q --project "$EVAL" python "$EVAL/api.py" --tache "$TACHE" --jeu "$JEU" --sortie "$RES/evaluation" \
  > "$RES/evaluation-api.log" 2>&1 9>&- &
API_PID=$!
for _ in $(seq 1 100); do curl -fs http://127.0.0.1:8765/etat >/dev/null 2>&1 && break; sleep 0.1; done
curl -fs http://127.0.0.1:8765/etat >/dev/null 2>&1 || { echo "API de soumission non démarrée : $RES/evaluation-api.log" >&2; exit 1; }

JOURNAL="$TRACES/journaux/appels.jsonl"
LIGNE0=$(wc -l < "$JOURNAL")
DEBUT=$(date --iso-8601=seconds) T0=$(date +%s.%N)
echo "essai $ESSAI : harnais $NOM, recette $RECETTE, espace $ESPACE"
# Carte graphique : mémoire occupée avant l'essai (autres usages de la machine), puis relevé toutes
# les 5 s ; disque (espace, dossier personnel, /tmp) relevé toutes les 30 s, essai arrêté au-delà
# de DISQUE_MAX.
GPU_AVANT=$( (nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null || echo 0) | head -1)
echo "$GPU_AVANT" > "$RES/traces/gpu.txt"
( while kill -0 "$$" 2>/dev/null; do sleep 5; nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 >> "$RES/traces/gpu.txt"; done ) < /dev/null > /dev/null 2>&1 9>&- &
GPU_PID=$!
set +e
"$CAGE/cage.sh" --espace "$ESPACE" --maison "$MAISON" --harnais "$HARNAIS" --cle "$CLE" --api --gpu \
  --tmp "$TMP_ESSAI" --memoire "$MEMOIRE" --memoire-pic "$RES/traces/memoire.json" \
  --telechargement "$TELECHARGEMENT_MAX" \
  --journal-reseau "$RES/traces/reseau.jsonl" --duree "$DUREE" -- /opt/harnais/lancer.sh "$MESSAGE" \
  < /dev/null > "$RES/harnais/stdout.log" 2> "$RES/harnais/stderr.log" 9>&- &   # entrée fermée : aucun harnais n'attend de texte
CAGE_PID=$!
( pic=0
  while kill -0 "$CAGE_PID" 2>/dev/null; do
    t=$(du -sb "$ESPACE" "$MAISON" "$TMP_ESSAI" 2>/dev/null | awk '{s+=$1} END {print s+0}')
    [ "$t" -gt "$pic" ] && pic=$t && echo "$pic" > "$RES/traces/disque.txt"
    if [ "$t" -gt "$DISQUE_MAX" ]; then echo depasse >> "$RES/traces/disque.txt"; pkill -TERM -P "$CAGE_PID" 2>/dev/null; kill "$CAGE_PID" 2>/dev/null; break; fi
    sleep 30
  done ) < /dev/null > /dev/null 2>&1 9>&- &
DISQUE_PID=$!
wait "$CAGE_PID"
CODE=$?
kill "$GPU_PID" "$DISQUE_PID" 2>/dev/null || true
wait "$GPU_PID" "$DISQUE_PID" 2>/dev/null || true
set -e
FIN=$(date --iso-8601=seconds) DUREE_S=$(python3 -c "import sys,time; print(time.time() - float(sys.argv[1]))" "$T0")
kill "$API_PID" 2>/dev/null || true

# Clé de l'essai : dépense lue puis clé supprimée dès la sortie du harnais, avant la relance (un
# workflow qui aurait gardé cette clé ne peut plus appeler le modèle avec elle).
sleep 10   # le LiteLLM écrit la dépense (par lots, 1 à 6 s) et le journal après la réponse
DEPENSE=$(python3 "$TRACES/cles.py" --depense "$ESSAI")
python3 "$TRACES/cles.py" --supprimer "$ESSAI" >/dev/null || echo "clé $ESSAI non supprimée" >&2

# Relance du workflow déclaré (extraction), avec une clé neuve. Sans déclaration de fin : pas de
# relance (protocole, section 7).
DEPENSE_RELANCE=null
if [ "$TACHE" != jouet ] && [ -f "$RES/evaluation/fin.json" ]; then
  python3 "$TRACES/cles.py" "$ESSAI-relance" >/dev/null
  uv run -q --project "$EVAL" python "$EVAL/relancer.py" --espace "$ESPACE" --essai "$RES" \
    --cle "$TRACES/secrets/cle-$ESSAI-relance.env" --maison "$MAISON" --tache "$TACHE" \
    ${GOLDSET:+--jeu "$GOLDSET/relance"} || true
  sleep 10
  DEPENSE_RELANCE=$(python3 "$TRACES/cles.py" --depense "$ESSAI-relance")
  python3 "$TRACES/cles.py" --supprimer "$ESSAI-relance" >/dev/null || echo "clé $ESSAI-relance non supprimée" >&2
fi

# Journal du modèle lu une seule fois, depuis le début de l'essai : chaque ligne va à l'essai ou à
# sa relance selon l'alias de la clé.
touch "$RES/traces/reseau.jsonl"
tail -n +"$((LIGNE0 + 1))" "$JOURNAL" | python3 "$CAGE/collecter.py" repartir "$ESSAI" "$RES"
python3 "$CAGE/collecter.py" essai "$RES" "$ESSAI" "$NOM" "$RECETTE" "$TACHE" "$DEBUT" "$FIN" "$DUREE_S" \
  "$CODE" "$ESPACE" "$DUREE" "$DEPENSE" "$DEPENSE_RELANCE" "$HARNAIS" "$MEMOIRE" "$DISQUE_MAX" "$TELECHARGEMENT_MAX"
# Code écrit par le harnais archivé pour la relecture (ni PDF ni JSON), puis toute chaîne qui ressemble
# à une clé masquée dans les résultats (un harnais peut afficher ses variables d'environnement).
python3 "$CAGE/archiver_code.py" "$ESPACE" "$RES" >/dev/null || true
python3 "$CAGE/masquer.py" "$RES" >/dev/null || true
uv run -q --project "$EVAL" python "$EVAL/rapport.py" --essai "$RES" >/dev/null || true
python3 "$CAGE/compresser.py" "$RES" >/dev/null || true   # traces de plus de 20 Mo en gzip (limite GitHub)
uv run -q --project "$EVAL" python "$EVAL/index_resultats.py" >/dev/null || true
exit "$CODE"
