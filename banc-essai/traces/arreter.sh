#!/usr/bin/env bash
# Arrête le LiteLLM du banc (les données et le journal sont conservés).
set -euo pipefail
cd "$(dirname "$0")"
docker compose stop
