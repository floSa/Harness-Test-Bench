#!/bin/bash
# Démarrage dans la cage : relais vers le modèle, PyPI et l'API (ceux qui existent), clé du
# harnais, puis la commande.
set -u
ports=()
for r in modele:4100 pypi:3128 api:8765; do
  s=/run/banc/s/${r%%:*} p=${r#*:}
  if [ -S "$s" ]; then
    python3 /run/banc/relais.py interieur "$p" "$s" &
    ports+=("$p")
  fi
done
for p in "${ports[@]}"; do
  for _ in $(seq 1 50); do
    (echo > /dev/tcp/127.0.0.1/$p) 2>/dev/null && break
    sleep 0.1
  done
done
if [ -f /run/banc/cle.env ]; then
  set -a; . /run/banc/cle.env; set +a
  rm -f /run/banc/cle.env
fi
"$@"
