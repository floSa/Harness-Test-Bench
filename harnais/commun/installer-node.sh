#!/usr/bin/env bash
# Installe Node.js (version LTS figée, archive officielle de nodejs.org, empreinte SHA-256 vérifiée
# sur SHASUMS256.txt) dans le dossier donné. Utilisé par les harnais écrits en JavaScript (Pi,
# Cline) : chacun a sa copie dans son dossier, seul dossier du harnais visible dans la cage.
#
#   harnais/commun/installer-node.sh DOSSIER
set -euo pipefail
VERSION=v26.13.1
DEST=${1:?dossier de destination}
if [ -x "$DEST/bin/node" ] && [ "$("$DEST/bin/node" --version)" = "$VERSION" ]; then exit 0; fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
ARCHIVE="node-$VERSION-linux-x64.tar.xz"
curl -fsSL -o "$TMP/SHASUMS256.txt" "https://nodejs.org/dist/$VERSION/SHASUMS256.txt"
curl -fsSL -o "$TMP/$ARCHIVE" "https://nodejs.org/dist/$VERSION/$ARCHIVE"
(cd "$TMP" && grep " $ARCHIVE\$" SHASUMS256.txt | sha256sum -c --quiet -)
rm -rf "$DEST" && mkdir -p "$DEST"
tar -xJf "$TMP/$ARCHIVE" -C "$DEST" --strip-components=1
echo "Node $("$DEST/bin/node" --version) installé dans $DEST"
