set -a; . ./.env; set +a
systemd-run --user --scope --quiet -p MemoryMax=8G -p MemorySwapMax=0 -p TasksMax=2048 \
bwrap --die-with-parent --unshare-all --hostname cage \
  --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 --symlink usr/sbin /sbin \
  --ro-bind /etc /etc --proc /proc --dev /dev --tmpfs /tmp --tmpfs /home --tmpfs /run \
  --bind "$PWD/espace" /travail --bind "$PWD/maison" /home/agent --ro-bind "$PWD/harnais" /opt/harnais \
  --ro-bind "$XDG_RUNTIME_DIR/harnais" /run/relais \
  --remount-ro / --chdir /travail --clearenv \
  --setenv HOME /home/agent --setenv TERM "$TERM" --setenv PATH /opt/harnais/bin:/usr/bin:/bin \
  --setenv OPENAI_BASE_URL http://127.0.0.1:8080/v1 --setenv OPENAI_API_KEY "$CLE_LOCALE" --setenv MODELE "$IAG_MODELE" \
  bash -c 'socat TCP-LISTEN:8080,bind=127.0.0.1,fork,reuseaddr UNIX-CONNECT:/run/relais/relais.sock & exec bash'
