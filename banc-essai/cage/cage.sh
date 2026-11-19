#!/usr/bin/env bash
# Exécute une commande dans la cage du banc (bubblewrap).
#
#   cage.sh --espace DIR --maison DIR [--harnais DIR] [--cle FICHIER] [--api]
#           [--entree DIR] [--sortie DIR] [--journal-reseau FICHIER] [--duree S]
#           [--lecture SOURCE:CIBLE]... [--sans-reseau] [--gpu] [--tmp DIR] [--memoire TAILLE]
#           [--telechargement OCTETS] [--memoire-pic FICHIER] -- COMMANDE...
#
# Dans la cage :
#   - écriture seulement dans l'espace de travail (/travail), le dossier personnel du harnais
#     (/home/banc), la sortie éventuelle (/sortie) et /tmp (sur le disque : --tmp, ou un dossier
#     temporaire supprimé à la sortie) ;
#   - /run/banc (sockets des relais, clé de l'essai) en lecture seule ;
#   - /usr et /etc en lecture seule ; le reste de la machine (dont /home, donc le dépôt et le test
#     caché) invisible ;
#   - aucun réseau, sauf trois relais : modèle (LiteLLM du banc) sur 127.0.0.1:4100, API de
#     soumission sur 127.0.0.1:8765 (si --api), mandataire 127.0.0.1:3128 (PyPI, Hugging Face,
#     GitHub seulement, volume total plafonné par --telechargement, 10 Go par défaut) ;
#   - --memoire : plafond de mémoire vive (systemd-run --user, 16G par défaut ; « 0 » : aucun),
#     pic relevé dans --memoire-pic ;
#   - --sans-reseau : aucun relais (tests cachés de la tâche jouet) ;
#   - --lecture : montage supplémentaire en lecture seule ;
#   - --gpu : carte graphique visible (WSL : /dev/dxg et bibliothèques /usr/lib/wsl) ;
#   - garde-fou de durée (--duree, 7200 s par défaut).
set -euo pipefail
ICI="$(cd "$(dirname "$0")" && pwd)"
ESPACE= MAISON= HARNAIS= CLE= API=0 ENTREE= SORTIE= JOURNAL_RESEAU=/dev/null DUREE=7200 RESEAU=1 GPU=0
TMPDIR_CAGE= MEMOIRE=16G QUOTA=$((10 * 1000 * 1000 * 1000)) MEMOIRE_PIC=/dev/null
DOMAINES=pypi.org,files.pythonhosted.org,huggingface.co,.huggingface.co,.hf.co,github.com,.github.com,.githubusercontent.com
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
    --gpu) GPU=1; shift ;;
    --tmp) TMPDIR_CAGE=$(realpath "$2"); shift 2 ;;
    --memoire) MEMOIRE=$2; shift 2 ;;
    --telechargement) QUOTA=$2; shift 2 ;;
    --memoire-pic) MEMOIRE_PIC=$2; shift 2 ;;
    --) shift; break ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done
[ -n "$ESPACE" ] && [ -n "$MAISON" ] && [ $# -gt 0 ] || { sed -n '2,7p' "$0" >&2; exit 2; }

PARTAGE=$(mktemp -d /tmp/banc-cage-XXXXXX)
mkdir "$PARTAGE/s"
TMP_A_SUPPRIMER=
if [ -z "$TMPDIR_CAGE" ]; then TMPDIR_CAGE=$(mktemp -d /tmp/banc-tmp-XXXXXX); TMP_A_SUPPRIMER=$TMPDIR_CAGE; fi
mkdir -p "$TMPDIR_CAGE"
cp "$ICI/relais.py" "$ICI/interieur.sh" "$PARTAGE/"
[ -n "$CLE" ] && cp "$CLE" "$PARTAGE/cle.env"
PIDS=()
nettoyer() {
  for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null || true; done
  wait 2>/dev/null || true
  rm -rf "$PARTAGE"
  [ -n "$TMP_A_SUPPRIMER" ] && rm -rf "$TMP_A_SUPPRIMER"
  true
}
trap nettoyer EXIT

if [ "$RESEAU" = 1 ]; then
  python3 "$ICI/relais.py" exterieur "$PARTAGE/s/modele" 127.0.0.1:4100 & PIDS+=($!)
  python3 "$ICI/relais.py" filtre "$PARTAGE/s/pypi" "$JOURNAL_RESEAU" "$DOMAINES" "$QUOTA" & PIDS+=($!)
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
  --proc /proc --dev /dev --bind "$TMPDIR_CAGE" /tmp
  --bind "$ESPACE" /travail --bind "$MAISON" /home/banc --ro-bind "$PARTAGE" /run/banc
  --setenv HOME /home/banc --setenv USER banc --setenv LANG C.UTF-8
  --setenv PATH /opt/harnais/bin:/opt/outils:/home/banc/.local/bin:/usr/local/bin:/usr/bin:/bin
  --setenv HTTPS_PROXY http://127.0.0.1:3128 --setenv HTTP_PROXY http://127.0.0.1:3128
  --setenv https_proxy http://127.0.0.1:3128 --setenv http_proxy http://127.0.0.1:3128
  --setenv NO_PROXY 127.0.0.1,localhost --setenv no_proxy 127.0.0.1,localhost
  --setenv BANC_MODELE_URL http://127.0.0.1:4100 --setenv BANC_MODELE deepseek-v4.1-flash
  --setenv BANC_API http://127.0.0.1:8765 --setenv BANC_API_ACTIVE "$API"
  --chdir /travail)
[ -n "$TERM" ] && ARGS+=(--setenv TERM "$TERM")
[ -x "$HOME/.local/bin/uv" ] && ARGS+=(--ro-bind "$HOME/.local/bin/uv" /opt/outils/uv)
[ -n "$HARNAIS" ] && ARGS+=(--ro-bind "$HARNAIS" /opt/harnais)
[ -n "$ENTREE" ] && ARGS+=(--ro-bind "$ENTREE" /entree)
[ -n "$SORTIE" ] && ARGS+=(--bind "$SORTIE" /sortie)
ARGS+=("${LECTURES[@]}")
if [ "$GPU" = 1 ] && [ -e /dev/dxg ]; then
  ARGS+=(--dev-bind /dev/dxg /dev/dxg --ro-bind /usr/lib/wsl /usr/lib/wsl
    --setenv LD_LIBRARY_PATH /usr/lib/wsl/lib)
fi
ARGS+=(--remount-ro /)   # racine de la cage en lecture seule : seuls les montages ci-dessus sont inscriptibles

# Plafond de mémoire : la cage tourne dans une unité systemd de l'utilisateur (cgroup), dont le pic
# de mémoire est relevé toutes les 2 s ; au-delà du plafond, le noyau arrête le processus fautif.
PREFIXE=()
if [ "$MEMOIRE" != 0 ]; then
  UNITE="banc-cage-$(basename "$PARTAGE")"
  PREFIXE=(systemd-run --user --scope --quiet --unit "$UNITE" -p "MemoryMax=$MEMOIRE" -p MemorySwapMax=0 -p OOMPolicy=continue)
  CG="/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/app.slice/$UNITE.scope"
  if [ "$MEMOIRE_PIC" != /dev/null ]; then
    # Boucle sans sous-processus imbriqué, arrêtée avec la cage, sans sortie héritée.
    ( while kill -0 "$$" 2>/dev/null; do
        sleep 2
        [ -r "$CG/memory.peak" ] || continue
        printf '{"memoire_pic_octets": %s, "memoire_plafond": "%s", "arrets_memoire": %s}\n' \
          "$(cat "$CG/memory.peak")" "$MEMOIRE" "$(awk '$1=="oom_kill"{print $2}' "$CG/memory.events")" \
          > "$MEMOIRE_PIC.tmp" && mv "$MEMOIRE_PIC.tmp" "$MEMOIRE_PIC"
      done ) < /dev/null > /dev/null 2>&1 &
    PIDS+=($!)
  fi
fi
set +e
"${PREFIXE[@]}" timeout --kill-after=30 "$DUREE" bwrap "${ARGS[@]}" /bin/bash /run/banc/interieur.sh "$@"
code=$?
set -e
[ "$code" = 124 ] && echo "cage : garde-fou de durée atteint ($DUREE s)" >&2
exit "$code"
