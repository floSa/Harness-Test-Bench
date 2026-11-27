# À charger avant d'installer un harnais sur un poste d'entreprise (mandataire et certificat) :
#
#   . outils/env-mandataire.sh
#   harnais/<harnais>/installer.sh
#
# Lit BANC_MANDATAIRE et BANC_CERTIFICAT dans .env (racine du dépôt) et exporte les variables que
# respectent curl, npm, Node, pip et uv. Le relais et la cage lisent déjà .env eux-mêmes : ce fichier
# ne sert qu'aux installations faites depuis le terminal. Rien n'est affiché.
_racine="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_lire() { grep -m1 "^$1=" "$_racine/.env" 2>/dev/null | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'; }
_m=$(_lire BANC_MANDATAIRE)
if [ -n "$_m" ]; then
  export HTTPS_PROXY="$_m" HTTP_PROXY="$_m" https_proxy="$_m" http_proxy="$_m"
  export NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1
fi
_c=$(_lire BANC_CERTIFICAT)
if [ -n "$_c" ]; then
  # fichier PEM complet (autorités publiques et interne) : voir banc-essai/documentation/modele-et-fournisseur.md
  export SSL_CERT_FILE="$_c" CURL_CA_BUNDLE="$_c" REQUESTS_CA_BUNDLE="$_c" PIP_CERT="$_c" NODE_EXTRA_CA_CERTS="$_c"
  export npm_config_cafile="$_c"
fi
echo "mandataire : $([ -n "$_m" ] && echo défini || echo aucun) ; certificat : $([ -n "$_c" ] && echo défini || echo aucun)"
unset _racine _m _c
unset -f _lire
