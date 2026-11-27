#!/usr/bin/env bash
# Vérifie qu'un harnais installé se branche bien sur le portail du modèle, dans la cage, sans lui
# faire faire de tâche : un seul message (« Réponds seulement : OK »), puis lecture du journal du relais.
#
#   harnais/verifier-connexion.sh <harnais>        (opencode, pi, gptme, goose, cline)
#
# Prérequis : relais démarré (banc-essai/traces/demarrer.sh), harnais installé. L'essai passe par le
# lanceur du banc (recette jouet, garde-fou de 10 minutes, clé propre supprimée à la fin) ; résultats
# dans banc-essai/resultats/connexion-<harnais>-<date>/. Conforme si : au moins un appel au modèle,
# aucun appel en échec, code de retour 0, garde-fou non atteint. Coût : quelques appels courts.
set -euo pipefail
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
H=${1:?harnais attendu : opencode, pi, gptme, goose ou cline}
[ -x "$RACINE/harnais/$H/lancer.sh" ] || { echo "harnais inconnu : $H" >&2; exit 2; }
ESSAI="connexion-$H-$(date +%Y%m%d-%H%M%S)"
set +e
"$RACINE/banc-essai/cage/lancer.sh" "$H" jouet --essai "$ESSAI" --duree 600 \
  --message "Réponds seulement : OK. N'utilise aucun outil et ne lis aucun fichier." > /dev/null 2>&1
set -e
E="$RACINE/banc-essai/resultats/$ESSAI/essai.json"
[ -f "$E" ] || { echo "KO $H : pas de résultat ($E absent) ; voir banc-essai/resultats/$ESSAI/" >&2; exit 1; }
python3 - "$E" "$H" <<'PY'
import json, sys
e, h = json.load(open(sys.argv[1])), sys.argv[2]
ok = (e["appels_modele"] or 0) >= 1 and e["appels_echoues"] == 0 and e["code_retour"] == 0 and not e["garde_fou_atteint"]
print(f"{'OK' if ok else 'KO'} {h} ({e.get('version_harnais')}) : {e['appels_modele']} appels au modèle, "
      f"{e['appels_echoues']} en échec, code de retour {e['code_retour']}, {e['duree_s']} s ; "
      f"sites refusés au démarrage : {', '.join(e.get('hotes_refuses') or []) or 'aucun'}")
if not ok:
    print(f"  trace : {sys.argv[1].rsplit('/', 1)[0]}/harnais/stdout.log et stderr.log")
sys.exit(0 if ok else 1)
PY
