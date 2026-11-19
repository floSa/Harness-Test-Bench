#!/usr/bin/env bash
# Écrit la configuration de Goose pour le banc dans $HOME/.config/goose/config.yaml : fournisseur
# « openai » pointé sur le LiteLLM du banc ($BANC_MODELE_URL, /v1/chat/completions), modèle
# $BANC_MODELE, mode « auto » (outils exécutés sans confirmation : la cage borne ce que le harnais
# peut toucher), télémétrie et nommage automatique des sessions coupés. La clé n'est jamais écrite :
# Goose ignore une clé placée dans config.yaml, elle vient de OPENAI_API_KEY (voir lancer.sh).
#
#   harnais/goose/configurer.sh [DOSSIER]     (défaut : $HOME/.config/goose)
set -euo pipefail
DOSSIER=${1:-$HOME/.config/goose}
: "${BANC_MODELE_URL:?}" "${BANC_MODELE:?}"
mkdir -p "$DOSSIER"
cat > "$DOSSIER/config.yaml" <<YAML
GOOSE_PROVIDER: openai
GOOSE_MODEL: $BANC_MODELE
OPENAI_HOST: $BANC_MODELE_URL
OPENAI_BASE_PATH: v1/chat/completions
GOOSE_MODE: auto
GOOSE_TELEMETRY_ENABLED: false
GOOSE_DISABLE_SESSION_NAMING: true
YAML
echo "configuration écrite : $DOSSIER/config.yaml"
