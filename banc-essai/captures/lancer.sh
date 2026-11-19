#!/usr/bin/env bash
# Lance un script de captures Playwright dans le conteneur officiel (rien à installer dans WSL),
# comme dans la série RAG. Réseau de l'hôte (--network host) : les interfaces web des harnais,
# écoutant sur 127.0.0.1, sont joignables ; aucun port n'est publié.
# Le paquet Python playwright (même version que l'image) est installé une fois dans donnees/playwright/site.
#
#   banc-essai/captures/lancer.sh <script.py relatif au dépôt> [arguments]
set -euo pipefail
cd "$(dirname "$0")/../.."
IMAGE="mcr.microsoft.com/playwright/python:v1.65.1-noble@sha256:0ab41a37431309d72b7a26f40ef1fdb464a62740196b2143965a2f59dc090409"
mkdir -p donnees/playwright
if [ ! -d donnees/playwright/site/playwright ]; then
  docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD/donnees/playwright:/pw" "$IMAGE" \
    pip install -q --target /pw/site playwright==1.65.1
fi
docker run --rm --name harnais-captures --network host --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -e PYTHONPATH=/pw/site:/depot/banc-essai/captures -v "$PWD/donnees/playwright:/pw" -v "$PWD:/depot" -w /depot \
  "$IMAGE" python "$@"
