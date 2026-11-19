#!/usr/bin/env bash
# Installe gptme (version figée, PyPI, sans extension facultative) dans un environnement virtuel
# harnais/gptme/installe/ (hors git), sur le Python du système (/usr/bin/python3, visible dans la
# cage ; le Python géré par uv vit dans le dossier personnel, invisible dans la cage).
#
#   harnais/gptme/installer.sh
set -euo pipefail
cd "$(dirname "$0")"
VERSION=0.37.0
if [ -x installe/bin/gptme ] && installe/bin/python -c "import importlib.metadata as m; assert m.version('gptme') == '$VERSION'" 2>/dev/null; then
  echo "gptme $VERSION déjà installé"; exit 0
fi
rm -rf installe
uv venv -q --python /usr/bin/python3 installe
uv pip install -q --python installe/bin/python "gptme==$VERSION"
echo "gptme $(installe/bin/python -c 'import importlib.metadata as m; print(m.version("gptme"))') installé dans harnais/gptme/installe/"
