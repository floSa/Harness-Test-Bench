#!/usr/bin/env bash
# Écrit la configuration d'OpenCode pour le banc : fournisseur compatible OpenAI = LiteLLM du banc
# ($BANC_MODELE_URL/v1, modèle $BANC_MODELE, clé lue dans $BANC_CLE_MODELE au lancement ; contexte,
# sortie maximale et vision : $BANC_CONTEXTE, $BANC_SORTIE_MAX, $BANC_VISION), mise à
# jour automatique et partage coupés, éditions et commandes permises sans confirmation (la cage
# borne ce que le harnais peut toucher), accès web du harnais refusé.
#
#   harnais/opencode/configurer.sh [DOSSIER]     (défaut : $HOME/.config/opencode)
#
# Syntaxe de configuration de la version 1 (« provider », « npm », « options ») : la version
# 1.19.6 ignore la syntaxe « providers » décrite par la documentation en ligne (vérifié avec
# `opencode debug config`).
set -euo pipefail
DOSSIER=${1:-$HOME/.config/opencode}
: "${BANC_MODELE_URL:?}" "${BANC_MODELE:?}"
mkdir -p "$DOSSIER"
python3 - "$DOSSIER/opencode.json" <<'PY'
import json, os, sys
url, modele = os.environ["BANC_MODELE_URL"].rstrip("/") + "/v1", os.environ["BANC_MODELE"]
# Capacités du modèle : banc-essai/modele.env, transmises par la cage (valeurs par défaut hors cage).
contexte = int(os.environ.get("BANC_CONTEXTE", "1000000"))
sortie = int(os.environ.get("BANC_SORTIE_MAX", "32768"))
vision = os.environ.get("BANC_VISION", "1") == "1"
config = {
    "$schema": "https://opencode.ai/config.json",
    "model": f"banc/{modele}",
    "small_model": f"banc/{modele}",
    "autoupdate": False,
    "share": "disabled",
    "provider": {"banc": {
        "npm": "@ai-sdk/openai-compatible",
        "name": "LiteLLM du banc",
        "options": {"baseURL": url, "apiKey": "{env:BANC_CLE_MODELE}"},
        "models": {modele: {"name": modele, "attachment": vision, "tool_call": True,
                            "modalities": {"input": ["text", "image"] if vision else ["text"], "output": ["text"]},
                            "limit": {"context": contexte, "output": sortie}}},
    }},
    "permission": {"edit": "allow", "bash": "allow", "webfetch": "deny"},
}
json.dump(config, open(sys.argv[1], "w"), indent=2)
PY
echo "configuration écrite : $DOSSIER/opencode.json"
