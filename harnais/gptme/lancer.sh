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
# Appel par le Python de l'environnement virtuel : le script installe/bin/gptme désigne son
# interpréteur par le chemin de l'hôte, invisible dans la cage.
exec "$ICI/installe/bin/python" -c 'import sys; from gptme.cli.main import main; sys.argv[0] = "gptme"; sys.exit(main())' \
  --non-interactive --output-format json --tool-format tool \
  -m "banc/$BANC_MODELE" --name essai "$*"
