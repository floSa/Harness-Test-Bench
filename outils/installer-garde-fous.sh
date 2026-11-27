#!/usr/bin/env bash
# Installe les garde-fous git du banc (outils/git/pre-commit et pre-push) pour ce clone.
#
#   outils/installer-garde-fous.sh [--poste-entreprise]
#
# --poste-entreprise : crée .poste-entreprise à la racine (hors git) : tout push est alors refusé.
# Vérification : git config core.hooksPath (doit afficher outils/git).
set -euo pipefail
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
chmod +x "$RACINE/outils/git/pre-commit" "$RACINE/outils/git/pre-push"
git -C "$RACINE" config core.hooksPath outils/git
if [ "${1:-}" = --poste-entreprise ]; then
  echo "Poste d'entreprise : aucun push vers GitHub depuis ce clone." > "$RACINE/.poste-entreprise"
fi
echo "garde-fous installés (core.hooksPath = $(git -C "$RACINE" config core.hooksPath))$([ -e "$RACINE/.poste-entreprise" ] && echo ' ; poste d entreprise : push refusé')"
