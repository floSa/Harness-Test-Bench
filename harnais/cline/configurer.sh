#!/usr/bin/env bash
# Configure Cline CLI pour le banc : fournisseur compatible OpenAI (« openai-compatible ») = LiteLLM
# du banc ($BANC_MODELE_URL/v1), modèle $BANC_MODELE, clé $BANC_CLE_MODELE. `cline auth` enregistre
# la clé dans son dossier de configuration ($HOME/.cline) : dans la cage, c'est la clé de l'essai,
# supprimée du relais à la fin de l'essai, dans le dossier personnel de l'essai (hors du dépôt).
#
#   harnais/cline/configurer.sh
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
: "${BANC_MODELE_URL:?}" "${BANC_MODELE:?}" "${BANC_CLE_MODELE:?}"
export PATH="$ICI/installe/node/bin:$PATH"
"$ICI/installe/cline/node_modules/cline/bin/cline" auth -p openai-compatible -k "$BANC_CLE_MODELE" \
  -m "$BANC_MODELE" -b "${BANC_MODELE_URL%/}/v1"
