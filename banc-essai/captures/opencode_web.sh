#!/usr/bin/env bash
# Captures de l'interface web d'OpenCode (chapitre 07 du manuel).
#
#   banc-essai/captures/opencode_web.sh
#
# `opencode web` ouvre le navigateur par défaut au démarrage (appel à `xdg-open`) ; sous WSL, cela
# ouvre une fenêtre du navigateur de Windows. Le serveur tourne donc ici dans bubblewrap, sans les
# lecteurs Windows (/mnt) ni la passerelle WSL vers Windows (/run/WSL), avec un faux `xdg-open` qui
# note l'appel. Clé du modèle : clé temporaire « manuel-opencode-web », supprimée à la fin.
set -euo pipefail
RACINE="$(cd "$(dirname "$0")/../.." && pwd)"
ESPIONS=/tmp/manuel-espions
mkdir -p "$ESPIONS"
for c in xdg-open wslview sensible-browser x-www-browser; do
  printf '#!/bin/sh\necho "$(date +%%T) %s $*" >> %s/appels.log\n' "$c" "$ESPIONS" > "$ESPIONS/$c"; chmod +x "$ESPIONS/$c"
done
python3 "$RACINE/banc-essai/traces/cles.py" manuel-opencode-web >/dev/null
CLE=$(sed -n 's/^BANC_CLE_MODELE=//p' "$RACINE/banc-essai/traces/secrets/cle-manuel-opencode-web.env")
cd /tmp/manuel/dosage
env -i HOME=/tmp/manuel/home PATH="$ESPIONS:/usr/bin:/bin" BANC_CLE_MODELE="$CLE" \
  bwrap --dev-bind / / --tmpfs /mnt --tmpfs /run --die-with-parent \
  "$RACINE/harnais/opencode/installe/opencode" web --port 4321 --hostname 127.0.0.1 > /tmp/manuel/web.log 2>&1 &
SERVEUR=$!
trap 'kill $SERVEUR 2>/dev/null || true; python3 "$RACINE/banc-essai/traces/cles.py" --supprimer manuel-opencode-web >/dev/null' EXIT
for _ in $(seq 1 60); do curl -fs -o /dev/null http://127.0.0.1:4321/ && break; sleep 0.5; done
"$RACINE/banc-essai/captures/lancer.sh" banc-essai/captures/opencode_web.py
echo "appels de navigateur interceptés : $(cat "$ESPIONS/appels.log" 2>/dev/null | wc -l)"
