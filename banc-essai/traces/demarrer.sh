#!/usr/bin/env bash
# Démarre le LiteLLM du banc (127.0.0.1:4100). Crée au premier lancement le mot de passe de la
# base et la clé maître (secrets/, hors git, jamais affichés). La clé OpenRouter vient de .env.
set -euo pipefail
cd "$(dirname "$0")"
umask 077
mkdir -p secrets journaux
[ -f ../../.env ] && grep -q '^OPENROUTER_API_KEY=.' ../../.env || { echo "OPENROUTER_API_KEY absente de .env" >&2; exit 1; }
alea() { python3 -c 'import secrets; print(secrets.token_urlsafe(32))'; }
if [ ! -f secrets/base.env ]; then
  mdp=$(alea)
  printf 'POSTGRES_PASSWORD=%s\nDATABASE_URL=postgresql://litellm:%s@harness-litellm-db:5432/litellm\n' "$mdp" "$mdp" > secrets/base.env
fi
[ -f secrets/maitre.env ] || printf 'LITELLM_MASTER_KEY=sk-%s\n' "$(alea)" > secrets/maitre.env
touch journaux/appels.jsonl
docker compose up -d
for _ in $(seq 1 90); do
  if curl -fs http://127.0.0.1:4100/health/liveliness >/dev/null 2>&1; then echo "LiteLLM du banc prêt : http://127.0.0.1:4100"; exit 0; fi
  sleep 2
done
echo "LiteLLM ne répond pas ; voir : docker logs harness-litellm" >&2
exit 1
