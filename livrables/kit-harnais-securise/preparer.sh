#!/usr/bin/env bash
# Prépare le kit : vérifie .env, crée la clé locale du relais et les dossiers.
#
#   bash preparer.sh               première fois, ou après modification de .env
#   bash preparer.sh --nouvelle-cle  remplace la clé du relais (l'ancienne cesse de fonctionner)
#
# Aucune clé n'est affichée.
set -euo pipefail
cd "$(dirname "$0")"
umask 077
if [ ! -f .env ]; then
  cp .env.exemple .env
  echo "Fichier .env créé : y renseigner IAG_URL, IAG_CLE et IAG_MODELE, puis relancer bash preparer.sh"
  exit 1
fi
chmod 600 .env
for v in IAG_URL IAG_CLE IAG_MODELE; do
  grep -q "^$v=." .env || { echo "$v est vide dans .env" >&2; exit 1; }
done
grep -q '^IAG_URL=.*/v1/*$' .env || echo "Attention : IAG_URL ne se termine pas par /v1 ; vérifier l'adresse du portail." >&2
if [ "${1:-}" = --nouvelle-cle ] || ! grep -q '^CLE_RELAIS=.' .env; then
  sed -i '/^CLE_RELAIS=/d' .env
  echo "CLE_RELAIS=relais-$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')" >> .env
  echo "Clé du relais créée (dans .env, non affichée)."
fi
sed -i '/^UID_AGENT=/d;/^GID_AGENT=/d' .env
printf 'UID_AGENT=%s\nGID_AGENT=%s\n' "$(id -u)" "$(id -g)" >> .env
umask 022
mkdir -p espace journaux certificats
echo "Prêt. Suite :"
echo "  docker compose build"
echo "  docker compose up -d relais filtre"
echo "  docker compose run --rm harnais python3 /kit/verifier.py"
