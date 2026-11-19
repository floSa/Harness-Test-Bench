#!/usr/bin/env bash
# Exécute une commande dans la cage du banc (bubblewrap).
#
#   cage.sh --espace DIR --maison DIR [--harnais DIR] [--cle FICHIER] [--api]
#           [--entree DIR] [--sortie DIR] [--journal-reseau FICHIER] [--duree S]
#           [--lecture SOURCE:CIBLE]... [--sans-reseau] -- COMMANDE...
#
# Dans la cage :
#   - écriture seulement dans l'espace de travail (/travail), le dossier personnel du harnais
#     (/home/banc), la sortie éventuelle (/sortie) et un /tmp en mémoire ;
#   - /usr et /etc en lecture seule ; le reste de la machine (dont /home, donc le dépôt et le test
#     caché) invisible ;
#   - aucun réseau, sauf trois relais : modèle (LiteLLM du banc) sur 127.0.0.1:4100, API de
#     soumission sur 127.0.0.1:8765 (si --api), PyPI par le mandataire 127.0.0.1:3128 (domaines
#     pypi.org et files.pythonhosted.org seulement) ;
#   - --sans-reseau : aucun relais (tests cachés de la tâche jouet) ;
#   - --lecture : montage supplémentaire en lecture seule ;
#   - garde-fou de durée (--duree, 7200 s par défaut).
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
ESPACE= MAISON= HARNAIS= CLE= API=0 ENTREE= SORTIE= JOURNAL_RESEAU=/dev/null DUREE=7200 RESEAU=1
LECTURES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --espace) ESPACE=$(realpath "$2"); shift 2 ;;
    --maison) MAISON=$(realpath "$2"); shift 2 ;;
    --harnais) HARNAIS=$(realpath "$2"); shift 2 ;;
    --cle) CLE=$(realpath "$2"); shift 2 ;;
    --api) API=1; shift ;;
    --entree) ENTREE=$(realpath "$2"); shift 2 ;;
    --sortie) SORTIE=$(realpath "$2"); shift 2 ;;
    --journal-reseau) JOURNAL_RESEAU=$(realpath "$2"); shift 2 ;;
    --duree) DUREE=$2; shift 2 ;;
    --lecture) LECTURES+=(--ro-bind "$(realpath "${2%%:*}")" "${2#*:}"); shift 2 ;;
    --sans-reseau) RESEAU=0; shift ;;
    --) shift; break ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done
[ -n "$ESPACE" ] && [ -n "$MAISON" ] && [ $# -gt 0 ] || { sed -n '2,7p' "$0" >&2; exit 2; }

PARTAGE=$(mktemp -d /tmp/banc-cage-XXXXXX)
mkdir "$PARTAGE/s"
cp "$ICI/relais.py" "$ICI/interieur.sh" "$PARTAGE/"
[ -n "$CLE" ] && cp "$CLE" "$PARTAGE/cle.env"
PIDS=()
nettoyer() {
  for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null || true; done
  wait 2>/dev/null || true
  rm -rf "$PARTAGE"
}
trap nettoyer EXIT

if [ "$RESEAU" = 1 ]; then
  python3 "$ICI/relais.py" exterieur "$PARTAGE/s/modele" 127.0.0.1:4100 & PIDS+=($!)
  python3 "$ICI/relais.py" filtre "$PARTAGE/s/pypi" "$JOURNAL_RESEAU" pypi.org,files.pythonhosted.org & PIDS+=($!)
  if [ "$API" = 1 ]; then
    python3 "$ICI/relais.py" exterieur "$PARTAGE/s/api" 127.0.0.1:8765 & PIDS+=($!)
  fi
  for s in modele pypi $([ "$API" = 1 ] && echo api); do
    for _ in $(seq 1 50); do [ -S "$PARTAGE/s/$s" ] && break; sleep 0.1; done
  done
fi

ARGS=(--die-with-parent --new-session --unshare-all --unshare-user --disable-userns --clearenv
  --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64
  --symlink usr/sbin /sbin --ro-bind /etc /etc
  --proc /proc --dev /dev --tmpfs /tmp
  --bind "$ESPACE" /travail --bind "$MAISON" /home/banc --bind "$PARTAGE" /run/banc
  --setenv HOME /home/banc --setenv USER banc --setenv LANG C.UTF-8
  --setenv PATH /opt/harnais/bin:/opt/outils:/home/banc/.local/bin:/usr/local/bin:/usr/bin:/bin
  --setenv HTTPS_PROXY http://127.0.0.1:3128 --setenv HTTP_PROXY http://127.0.0.1:3128
  --setenv https_proxy http://127.0.0.1:3128 --setenv http_proxy http://127.0.0.1:3128
  --setenv NO_PROXY 127.0.0.1,localhost --setenv no_proxy 127.0.0.1,localhost
  --setenv BANC_MODELE_URL http://127.0.0.1:4100 --setenv BANC_MODELE gemma-4-31b
  --setenv BANC_API http://127.0.0.1:8765 --setenv BANC_API_ACTIVE "$API"
  --chdir /travail)
[ -n "$TERM" ] && ARGS+=(--setenv TERM "$TERM")
[ -x "$HOME/.local/bin/uv" ] && ARGS+=(--ro-bind "$HOME/.local/bin/uv" /opt/outils/uv)
[ -n "$HARNAIS" ] && ARGS+=(--ro-bind "$HARNAIS" /opt/harnais)
[ -n "$ENTREE" ] && ARGS+=(--ro-bind "$ENTREE" /entree)
[ -n "$SORTIE" ] && ARGS+=(--bind "$SORTIE" /sortie)
ARGS+=("${LECTURES[@]}")
ARGS+=(--remount-ro /)   # racine de la cage en lecture seule : seuls les montages ci-dessus sont inscriptibles

set +e
timeout --kill-after=30 "$DUREE" bwrap "${ARGS[@]}" /bin/bash /run/banc/interieur.sh "$@"
code=$?
set -e
[ "$code" = 124 ] && echo "cage : garde-fou de durée atteint ($DUREE s)" >&2
exit "$code"
