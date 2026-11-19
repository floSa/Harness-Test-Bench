#!/usr/bin/env bash
# Écrit la configuration de gptme pour le banc dans $HOME/.config/gptme/config.toml : fournisseur
# compatible OpenAI « banc » = LiteLLM du banc ($BANC_MODELE_URL/v1), clé lue dans
# $BANC_CLE_MODELE au lancement (jamais écrite), modèle par défaut banc/$BANC_MODELE.
#
#   harnais/gptme/configurer.sh [DOSSIER]     (défaut : $HOME/.config/gptme)
set -euo pipefail
DOSSIER=${1:-$HOME/.config/gptme}
: "${BANC_MODELE_URL:?}" "${BANC_MODELE:?}"
mkdir -p "$DOSSIER"
cat > "$DOSSIER/config.toml" <<TOML
[[providers]]
name = "banc"
base_url = "${BANC_MODELE_URL%/}/v1"
api_key_env = "BANC_CLE_MODELE"
default_model = "$BANC_MODELE"

[env]
MODEL = "banc/$BANC_MODELE"
TOML
echo "configuration écrite : $DOSSIER/config.toml"
