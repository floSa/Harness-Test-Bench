#!/usr/bin/env bash
# Installe Cline CLI (paquet npm « cline », version figée, intégrité vérifiée par npm ; binaire
# Linux x64 fourni par le paquet facultatif @cline/cli-linux-x64) et sa propre copie de Node.js
# dans harnais/cline/installe/ (hors git), scripts d'installation désactivés.
#
#   harnais/cline/installer.sh
set -euo pipefail
cd "$(dirname "$0")"
VERSION=3.0.74
if [ -x installe/node/bin/node ] && grep -q "\"version\": \"$VERSION\"" installe/cline/node_modules/cline/package.json 2>/dev/null; then
  echo "Cline $VERSION déjà installé"; exit 0
fi
rm -rf installe && mkdir -p installe/cline
../commun/installer-node.sh "$PWD/installe/node"
PATH="$PWD/installe/node/bin:$PATH" npm install --silent --no-audit --no-fund --ignore-scripts \
  --prefix installe/cline "cline@$VERSION"
echo "Cline $VERSION installé dans harnais/cline/installe/"
