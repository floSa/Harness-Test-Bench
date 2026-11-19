#!/usr/bin/env bash
# Installe OpenCode (version figée, binaire officiel de GitHub, empreinte SHA-256 vérifiée) dans
# harnais/opencode/installe/ (hors git). Aucun droit administrateur, rien hors de ce dossier.
#
#   harnais/opencode/installer.sh
set -euo pipefail
cd "$(dirname "$0")"
VERSION=1.19.6
ARCHIVE=opencode-linux-x64.tar.gz
SHA256=47734e08968b30cc22a0bffb6d9feeed76ad4aa743213a12122040392d09a057
URL="https://github.com/anomalyco/opencode/releases/download/v$VERSION/$ARCHIVE"
if [ -x installe/opencode ] && [ "$(installe/opencode --version 2>/dev/null)" = "$VERSION" ]; then
  echo "OpenCode $VERSION déjà installé"; exit 0
fi
rm -rf installe && mkdir -p installe
curl -fsSL -o "installe/$ARCHIVE" "$URL"
echo "$SHA256  installe/$ARCHIVE" | sha256sum -c --quiet
tar -xzf "installe/$ARCHIVE" -C installe
rm "installe/$ARCHIVE"
echo "OpenCode $(installe/opencode --version) installé dans harnais/opencode/installe/"
