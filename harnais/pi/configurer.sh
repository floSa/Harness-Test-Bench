#!/usr/bin/env bash
# Écrit la configuration de Pi pour le banc dans $HOME/.pi/agent/ : models.json (fournisseur
# compatible OpenAI « banc » = LiteLLM du banc, clé lue dans $BANC_CLE_MODELE au lancement,
# jamais écrite ; contexte, vision et prix du modèle) et settings.json (modèle par défaut,
# télémétrie d'installation coupée).
#
#   harnais/pi/configurer.sh [DOSSIER]     (défaut : $HOME/.pi/agent)
set -euo pipefail
DOSSIER=${1:-$HOME/.pi/agent}
: "${BANC_MODELE_URL:?}" "${BANC_MODELE:?}"
mkdir -p "$DOSSIER"
python3 - "$DOSSIER" <<'PY'
import json, os, sys
d, url, modele = sys.argv[1], os.environ["BANC_MODELE_URL"].rstrip("/") + "/v1", os.environ["BANC_MODELE"]
models = {"providers": {"banc": {
    "baseUrl": url, "api": "openai-completions", "apiKey": "$BANC_CLE_MODELE",
    "models": [{"id": modele, "name": modele, "input": ["text", "image"], "contextWindow": 1000000,
                "maxTokens": 32768,
                # prix du fournisseur (dollars par million de jetons), relevés le 19/11/2026
                "cost": {"input": 0.05, "output": 0.30, "cacheRead": 0.003, "cacheWrite": 0}}]}}}
settings = {"defaultProvider": "banc", "defaultModel": modele, "enableInstallTelemetry": False,
            "enableAnalytics": False}
json.dump(models, open(f"{d}/models.json", "w"), indent=2)
json.dump(settings, open(f"{d}/settings.json", "w"), indent=2)
PY
echo "configuration écrite : $DOSSIER/models.json, $DOSSIER/settings.json"
