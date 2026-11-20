# Image du harnais : Debian 13, Python 3.12, Node 24, uv, git.
# Seule la section « INSTALLATION DU HARNAIS » est à adapter. Les images de base sont figées par
# leur empreinte (sha256) : la même image est reconstruite à l'identique chez chaque testeur.
FROM docker.io/library/node:24-trixie-slim@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0 AS node
FROM ghcr.io/astral-sh/uv:0.12.17@sha256:10787c682e4184e4f290de1171fd4703dc63de99221f10fe1c99002ce7fa9acc AS uv
FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl git ripgrep less procps \
 && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
COPY --from=uv /uv /uvx /usr/local/bin/

# Certificat de l'autorité interne, seulement si le réseau de l'entreprise inspecte le HTTPS
# (fichiers .crt déposés dans certificats/ ; dossier vide sinon).
COPY certificats/ /usr/local/share/ca-certificates/entreprise/
RUN update-ca-certificates
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Utilisateur sans droits, même identifiant que sur la machine (fichiers de l'espace de travail
# lisibles des deux côtés).
ARG UID_AGENT=1000
ARG GID_AGENT=1000
RUN groupadd -g "$GID_AGENT" agent && useradd -m -u "$UID_AGENT" -g agent -d /home/agent -s /bin/bash agent \
 && mkdir -p /travail && chown agent:agent /travail

# ---------------------------------------------------------------------------------------------
# INSTALLATION DU HARNAIS (à adapter). Version figée et, si possible, empreinte vérifiée.
# Exemple : Goose 1.60.1, binaire officiel.
ARG GOOSE_VERSION=1.60.1
ARG GOOSE_SHA256=0327b1857f8030343f59b77503e0455629bbf472c2901cb94b88389d6278635a
RUN curl -fsSL -o /tmp/goose.tar.gz \
      "https://github.com/aaif-goose/goose/releases/download/v${GOOSE_VERSION}/goose-x86_64-unknown-linux-gnu.tar.gz" \
 && echo "${GOOSE_SHA256}  /tmp/goose.tar.gz" | sha256sum -c --quiet \
 && tar -xzf /tmp/goose.tar.gz -C /usr/local/bin ./goose && rm /tmp/goose.tar.gz
# Autres harnais (une ligne à décommenter ; voir guide/05-brancher-un-harnais.md) :
# RUN npm install -g --ignore-scripts cline@3.0.74
# RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.5.2
# RUN pip install --no-cache-dir gptme==0.37.0
# ---------------------------------------------------------------------------------------------

USER agent
WORKDIR /travail
ENV HOME=/home/agent PATH=/home/agent/.local/bin:$PATH
CMD ["bash"]
