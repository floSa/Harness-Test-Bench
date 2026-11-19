#!/usr/bin/env bash
# Lance OpenCode sans interaction, dans la cage (banc-essai/cage/lancer.sh opencode <recette>).
#
#   /opt/harnais/lancer.sh "<message>"
#
# Configuration écrite dans $HOME (dossier personnel de l'essai), puis `opencode run` dans
# l'espace de travail : sortie standard = événements JSON de la session (trace complète), sortie
# d'erreur = journaux d'OpenCode. Ensuite, export de la session dans $HOME/opencode-sessions/.
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
"$ICI/configurer.sh" >&2
set +e
"$ICI/installe/opencode" run --format json --print-logs --log-level INFO --auto "$@"
code=$?
set -e
mkdir -p "$HOME/opencode-sessions"
for s in $("$ICI/installe/opencode" session list --format json 2>/dev/null \
           | python3 -c 'import json,sys; [print(x["id"]) for x in json.load(sys.stdin)]' 2>/dev/null); do
  "$ICI/installe/opencode" export "$s" > "$HOME/opencode-sessions/$s.json" 2>/dev/null || true
done
exit "$code"
