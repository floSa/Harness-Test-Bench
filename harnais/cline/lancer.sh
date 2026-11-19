#!/usr/bin/env bash
# Lance Cline CLI sans interaction, dans la cage (banc-essai/cage/lancer.sh cline <recette>).
#
#   /opt/harnais/lancer.sh "<message>"
#
# Configuration par `cline auth` (configurer.sh), puis `cline --json -y` : outils approuvés
# automatiquement (mode « yolo », prévu pour le travail sans surveillance ; la cage borne ce qu'ils
# peuvent toucher), sortie standard = événements NDJSON (trace complète, dont run_result), sessions
# dans $HOME/.cline/data/sessions/.
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
"$ICI/configurer.sh" >&2
export PATH="$ICI/installe/node/bin:$PATH"
exec "$ICI/installe/cline/node_modules/cline/bin/cline" --json -y "$*"
