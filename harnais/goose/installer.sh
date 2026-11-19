#!/usr/bin/env bash
# Installe Goose (version figée, binaire officiel de GitHub, empreinte SHA-256 vérifiée) dans
# harnais/goose/installe/ (hors git). Aucun droit administrateur, rien hors de ce dossier.
#
#   harnais/goose/installer.sh
set -euo pipefail
cd "$(dirname "$0")"
VERSION=1.60.1
ARCHIVE=goose-x86_64-unknown-linux-gnu.tar.gz
SHA256=0327b1857f8030343f59b77503e0455629bbf472c2901cb94b88389d6278635a
URL="https://github.com/aaif-goose/goose/releases/download/v$VERSION/$ARCHIVE"
if [ -x installe/goose ] && installe/goose --version 2>/dev/null | grep -q "$VERSION"; then
  echo "Goose $VERSION déjà installé"; exit 0
fi
rm -rf installe && mkdir -p installe
curl -fsSL -o "installe/$ARCHIVE" "$URL"
echo "$SHA256  installe/$ARCHIVE" | sha256sum -c --quiet
tar -xzf "installe/$ARCHIVE" -C installe
rm "installe/$ARCHIVE"
[ -x installe/goose ] || mv "$(find installe -type f -name goose | head -1)" installe/goose
echo "$(installe/goose --version) installé dans harnais/goose/installe/"
