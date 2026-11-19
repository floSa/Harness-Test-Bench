#!/usr/bin/env bash
# Outils montés en lecture seule dans la cage pour l'évaluation : pytest (tests cachés de la
# tâche jouet), installé pour le Python du système, version identique à celle de l'évaluateur.
set -euo pipefail
cd "$(dirname "$0")"
[ -d outils/pytest ] && exit 0
uv pip install -q --python /usr/bin/python3 --target outils/pytest pytest==9.2.0
echo "pytest installé dans banc-essai/cage/outils/pytest"
