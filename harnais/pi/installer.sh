#!/usr/bin/env bash
# Installe Pi (paquet npm @earendil-works/pi-coding-agent, version figée, intégrité vérifiée par
# npm) et sa propre copie de Node.js dans harnais/pi/installe/ (hors git). Scripts d'installation
# des paquets désactivés (--ignore-scripts, recommandé par la documentation de Pi).
#
#   harnais/pi/installer.sh
set -euo pipefail
cd "$(dirname "$0")"
VERSION=1.5.2
if [ -x installe/node/bin/node ] && [ -f installe/pi/node_modules/@earendil-works/pi-coding-agent/package.json ] \
   && grep -q "\"version\": \"$VERSION\"" installe/pi/node_modules/@earendil-works/pi-coding-agent/package.json; then
  echo "Pi $VERSION déjà installé"; exit 0
fi
rm -rf installe && mkdir -p installe/pi
../commun/installer-node.sh "$PWD/installe/node"
PATH="$PWD/installe/node/bin:$PATH" npm install --silent --no-audit --no-fund --ignore-scripts \
  --prefix installe/pi "@earendil-works/pi-coding-agent@$VERSION"
echo "Pi $VERSION installé dans harnais/pi/installe/"
