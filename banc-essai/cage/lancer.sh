#!/usr/bin/env bash
# Lance un essai : un harnais, une recette, dans la cage, avec collecte des journaux.
#
#   banc-essai/cage/lancer.sh <harnais> <recette> [--essai NOM] [--duree S] [--message "..."]
#
# <harnais> : dossier harnais/<harnais>/ (lot 4), ou « sonde » (banc-essai/cage/sonde/, preuves
# du lot 3), ou « factice » (banc-essai/cage/factice/, vérification du lanceur sur l'extraction). Le harnais est lancé dans la cage par /opt/harnais/lancer.sh "<message>".
# <recette> : sans-aide, avec-aide ou jouet.
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
case "$NOM" in sonde|factice) HARNAIS="$CAGE/$NOM" ;; *) HARNAIS="$RACINE/harnais/$NOM" ;; esac
[ -x "$HARNAIS/lancer.sh" ] || { echo "$HARNAIS/lancer.sh introuvable" >&2; exit 1; }

RES="$RACINE/banc-essai/resultats/$ESSAI"
ESPACES="${BANC_ESPACES:-$HOME/banc-espaces}"
ESPACE="$ESPACES/$ESSAI/travail" MAISON="$ESPACES/$ESSAI/maison"
[ -e "$RES" ] && { echo "$RES existe déjà" >&2; exit 1; }
mkdir -p "$RES/harnais" "$RES/traces" "$MAISON"

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
uv run -q --project "$EVAL" python "$EVAL/preparer.py" --recette "$RECETTE" --destination "$ESPACE" >/dev/null
if [ -n "$(ss -ltnH 'sport = :8765')" ]; then echo "port 8765 déjà pris" >&2; exit 1; fi
uv run -q --project "$EVAL" python "$EVAL/api.py" --tache "$TACHE" --jeu "$JEU" --sortie "$RES/evaluation" \
  > "$RES/evaluation-api.log" 2>&1 &
API_PID=$!
for _ in $(seq 1 100); do curl -fs http://127.0.0.1:8765/etat >/dev/null 2>&1 && break; sleep 0.1; done
curl -fs http://127.0.0.1:8765/etat >/dev/null 2>&1 || { echo "API de soumission non démarrée : $RES/evaluation-api.log" >&2; exit 1; }

JOURNAL="$TRACES/journaux/appels.jsonl"
LIGNE0=$(wc -l < "$JOURNAL")
DEBUT=$(date --iso-8601=seconds) T0=$(date +%s.%N)
echo "essai $ESSAI : harnais $NOM, recette $RECETTE, espace $ESPACE"
set +e
"$CAGE/cage.sh" --espace "$ESPACE" --maison "$MAISON" --harnais "$HARNAIS" --cle "$CLE" --api \
  --journal-reseau "$RES/traces/reseau.jsonl" --duree "$DUREE" -- /opt/harnais/lancer.sh "$MESSAGE" \
  < /dev/null > "$RES/harnais/stdout.log" 2> "$RES/harnais/stderr.log"   # entrée fermée : aucun harnais n'attend de texte
CODE=$?
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
if [ "$TACHE" = extraction ] && [ -f "$RES/evaluation/fin.json" ]; then
  python3 "$TRACES/cles.py" "$ESSAI-relance" >/dev/null
  uv run -q --project "$EVAL" python "$EVAL/relancer.py" --espace "$ESPACE" --essai "$RES" \
    --cle "$TRACES/secrets/cle-$ESSAI-relance.env" --maison "$MAISON" || true
  sleep 10
  DEPENSE_RELANCE=$(python3 "$TRACES/cles.py" --depense "$ESSAI-relance")
  python3 "$TRACES/cles.py" --supprimer "$ESSAI-relance" >/dev/null || echo "clé $ESSAI-relance non supprimée" >&2
fi

# Journal du modèle lu une seule fois, depuis le début de l'essai : chaque ligne va à l'essai ou à
# sa relance selon l'alias de la clé.
touch "$RES/traces/reseau.jsonl"
tail -n +"$((LIGNE0 + 1))" "$JOURNAL" | python3 "$CAGE/collecter.py" repartir "$ESSAI" "$RES"
python3 "$CAGE/collecter.py" essai "$RES" "$ESSAI" "$NOM" "$RECETTE" "$TACHE" "$DEBUT" "$FIN" "$DUREE_S" \
  "$CODE" "$ESPACE" "$DUREE" "$DEPENSE" "$DEPENSE_RELANCE" "$HARNAIS"
uv run -q --project "$EVAL" python "$EVAL/rapport.py" --essai "$RES" >/dev/null || true
exit "$CODE"
