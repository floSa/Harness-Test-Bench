#!/usr/bin/env bash
# Lance Goose sans interaction, dans la cage (banc-essai/cage/lancer.sh goose <recette>).
#
#   /opt/harnais/lancer.sh "<message>"
#
# Configuration écrite dans $HOME, clé du modèle passée par OPENAI_API_KEY, trousseau système
# désactivé. `goose run` avec l'extension intégrée « developer » (commandes, édition de fichiers) ;
# sortie standard = événements JSON de la session (trace complète), sortie d'erreur = messages de
# Goose. Ensuite, export de la session en JSON dans $HOME/goose-session.json.
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
"$ICI/configurer.sh" >&2
export GOOSE_DISABLE_KEYRING=1 GOOSE_TELEMETRY_ENABLED=false GOOSE_DISABLE_SESSION_NAMING=true GOOSE_MODE=auto
export OPENAI_API_KEY="${BANC_CLE_MODELE:?}"
set +e
"$ICI/installe/goose" run --with-builtin developer -n essai --output-format stream-json -t "$*"
code=$?
set -e
"$ICI/installe/goose" session export -n essai --format json -o "$HOME/goose-session.json" >&2 2>/dev/null || true
exit "$code"
