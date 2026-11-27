#!/usr/bin/env bash
# Démarre (ou redémarre) le LiteLLM du banc sur 127.0.0.1:4100.
#
#   banc-essai/traces/demarrer.sh
#
# 1. Écrit config.yaml depuis banc-essai/modele.env (generer_config.py : fournisseur, modèle, prix).
# 2. Lit dans .env (racine du dépôt) la clé du fournisseur choisi, et elle seule :
#      openrouter : OPENROUTER_API_KEY
#      portail    : PORTAIL_URL (adresse de base, avec le /v1 final) et PORTAIL_CLE
#    Facultatif : BANC_MANDATAIRE (mandataire HTTP sortant de l'entreprise, http://hote:port) et
#    BANC_CERTIFICAT (chemin d'un fichier PEM des autorités de confiance, autorité interne comprise).
# 3. Crée au premier lancement le mot de passe de la base et la clé maître (secrets/, hors git).
# Aucune clé n'est affichée. Guide : banc-essai/documentation/modele-et-fournisseur.md.
set -euo pipefail
cd "$(dirname "$0")"
umask 077
mkdir -p secrets journaux certificats
ENV=../../.env
[ -f "$ENV" ] || { echo "fichier .env absent à la racine du dépôt (modèle : .env.exemple)" >&2; exit 1; }
# Valeur d'une variable du .env, sans charger tout le fichier (rien d'autre n'entre dans le conteneur).
lire() { grep -m1 "^$1=" "$ENV" | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//' || true; }

python3 generer_config.py
FOURNISSEUR=$(grep -m1 '^BANC_FOURNISSEUR=' ../modele.env | cut -d= -f2- | tr -d '"'\'' ')
case "$FOURNISSEUR" in
  openrouter)
    CLE=$(lire OPENROUTER_API_KEY)
    [ -n "$CLE" ] || { echo "OPENROUTER_API_KEY absente de .env" >&2; exit 1; }
    printf 'BANC_FOURNISSEUR_CLE=%s\n' "$CLE" > secrets/fournisseur.env ;;
  portail)
    URL=$(lire PORTAIL_URL) CLE=$(lire PORTAIL_CLE)
    [ -n "$URL" ] && [ -n "$CLE" ] || { echo "PORTAIL_URL et PORTAIL_CLE doivent figurer dans .env" >&2; exit 1; }
    case "$URL" in */chat/completions|*/chat/completions/) echo "PORTAIL_URL : adresse de base seulement (sans /chat/completions)" >&2; exit 1 ;; esac
    printf 'BANC_FOURNISSEUR_CLE=%s\nBANC_FOURNISSEUR_URL=%s\n' "$CLE" "${URL%/}" > secrets/fournisseur.env ;;
esac
unset CLE

# Mandataire sortant et certificat de l'entreprise (vérification TLS jamais désactivée).
MANDATAIRE=$(lire BANC_MANDATAIRE)
if [ -n "$MANDATAIRE" ]; then
  printf 'HTTPS_PROXY=%s\nHTTP_PROXY=%s\nNO_PROXY=localhost,127.0.0.1,harness-litellm-db\nAIOHTTP_TRUST_ENV=True\n' \
    "$MANDATAIRE" "$MANDATAIRE" >> secrets/fournisseur.env
fi
CERTIFICAT=$(lire BANC_CERTIFICAT)
rm -f certificats/ca.pem
if [ -n "$CERTIFICAT" ]; then
  [ -f "$CERTIFICAT" ] || { echo "BANC_CERTIFICAT : fichier introuvable ($CERTIFICAT)" >&2; exit 1; }
  install -m 644 "$CERTIFICAT" certificats/ca.pem
  printf 'SSL_CERT_FILE=/certificats/ca.pem\nREQUESTS_CA_BUNDLE=/certificats/ca.pem\n' >> secrets/fournisseur.env
fi

alea() { python3 -c 'import secrets; print(secrets.token_urlsafe(32))'; }
if [ ! -f secrets/base.env ]; then
  mdp=$(alea)
  printf 'POSTGRES_PASSWORD=%s\nDATABASE_URL=postgresql://litellm:%s@harness-litellm-db:5432/litellm\n' "$mdp" "$mdp" > secrets/base.env
fi
[ -f secrets/maitre.env ] || printf 'LITELLM_MASTER_KEY=sk-%s\n' "$(alea)" > secrets/maitre.env
touch journaux/appels.jsonl
docker compose up -d --force-recreate harness-litellm >/dev/null 2>&1 || docker compose up -d
for _ in $(seq 1 90); do
  if curl -fs http://127.0.0.1:4100/health/liveliness >/dev/null 2>&1; then echo "LiteLLM du banc prêt : http://127.0.0.1:4100 (fournisseur $FOURNISSEUR)"; exit 0; fi
  sleep 2
done
echo "LiteLLM ne répond pas ; voir : docker logs harness-litellm" >&2
exit 1
