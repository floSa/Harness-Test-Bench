#!/usr/bin/env bash
# Lance Pi sans interaction, dans la cage (banc-essai/cage/lancer.sh pi <recette>).
#
#   /opt/harnais/lancer.sh "<message>"
#
# Configuration écrite dans $HOME ; `pi --mode json` : sortie standard = événements JSONL de la
# session (trace complète), session enregistrée dans $HOME/.pi/agent/sessions/. Pi n'a pas de
# système d'approbation : ses outils (read, bash, edit, write) s'exécutent sans confirmation, la
# cage borne ce qu'ils peuvent toucher. Vérification de version, catalogue et télémétrie coupés.
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
"$ICI/configurer.sh" >&2
export PATH="$ICI/installe/node/bin:$PATH" PI_SKIP_VERSION_CHECK=1 PI_OFFLINE=1 PI_TELEMETRY=0
exec node "$ICI/installe/pi/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js" \
  --mode json --provider banc --model "$BANC_MODELE" -- "$*"
