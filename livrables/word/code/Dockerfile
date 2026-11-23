FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git \
 && rm -rf /var/lib/apt/lists/*

# Installation du harnais, version figée (exemple : Goose 1.60.1).
RUN curl -fsSL https://github.com/aaif-goose/goose/releases/download/v1.60.1/goose-x86_64-unknown-linux-gnu.tar.gz \
  | tar -xz -C /usr/local/bin ./goose

# Utilisateur sans droits, même identifiant que sur le poste.
ARG UID_AGENT=1000
RUN useradd -m -u "$UID_AGENT" -d /home/agent agent
USER agent
