#!/usr/bin/env bash
# Lance gptme sans interaction, dans la cage (banc-essai/cage/lancer.sh gptme <recette>).
#
#   /opt/harnais/lancer.sh "<message>"
#
# Configuration écrite dans $HOME ; `gptme --non-interactive` (aucune confirmation), appels d'outils
# natifs (--tool-format tool), sortie standard = un objet JSON par message (trace complète), journal
# de la conversation dans $HOME/.local/share/gptme/logs/essai/. Téléchargement du découpeur
# tiktoken et recherche de serveurs locaux coupés (aucun n'est joignable dans la cage).
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
"$ICI/configurer.sh" >&2
export GPTME_TIKTOKEN_TIMEOUT=0 GPTME_NO_LOCAL_DISCOVERY=1
# Fenêtre de contexte : gptme suppose 128 000 jetons pour un fournisseur personnalisé et compacte vers
# 90 % de cette valeur. Un modèle plus petit (BANC_CONTEXTE, banc-essai/modele.env) est déclaré par
# GPTME_CONTEXT_LENGTH (gptme/init.py), sinon gptme dépasserait la fenêtre avant de compacter. Au-delà
# de 128 000, rien n'est changé : comportement identique aux essais de la campagne 1.
if [ "${BANC_CONTEXTE:-0}" -gt 0 ] && [ "${BANC_CONTEXTE}" -lt 128000 ]; then
  export GPTME_CONTEXT_LENGTH="$BANC_CONTEXTE"
fi
# Appel par le Python de l'environnement virtuel : le script installe/bin/gptme désigne son
# interpréteur par le chemin de l'hôte, invisible dans la cage.
exec "$ICI/installe/bin/python" -c 'import sys; from gptme.cli.main import main; sys.argv[0] = "gptme"; sys.exit(main())' \
  --non-interactive --output-format json --tool-format tool \
  -m "banc/$BANC_MODELE" --name essai "$*"
