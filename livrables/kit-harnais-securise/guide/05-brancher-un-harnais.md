# 5. Brancher un harnais

[Retour au sommaire](../README.md)

Chaque harnais s'installe d'une façon qui dépend du mode, puis se configure de la même façon dans tous les modes.

| Mode | Où installer le harnais |
|---|---|
| Docker, Podman | ligne « Docker » ci-dessous, dans la section « INSTALLATION DU HARNAIS » de `harnais/Dockerfile`, puis `docker compose build` (ou `podman compose build`) |
| Sans conteneur | commandes « Sans conteneur » ci-dessous, lancées sur le poste depuis le dossier du kit |

La configuration se fait ensuite dans le terminal du harnais (conteneur ou cage), où `OPENAI_BASE_URL`, `OPENAI_API_KEY` et `MODELE` sont déjà définis. Elle est gardée d'une session à l'autre.

Versions vérifiées avec le kit. En mode sans conteneur, Goose et gptme ont été vérifiés ; Pi et Cline demandent Node.js installé sur le poste.

## Goose 1.60.1

Installation : Docker, déjà présent dans `harnais/Dockerfile` ; sans conteneur, voir [04-installation-sans-conteneur.md](04-installation-sans-conteneur.md), étape 2.

```bash
export GOOSE_PROVIDER=openai OPENAI_HOST="${OPENAI_BASE_URL%/v1}" OPENAI_BASE_PATH=v1/chat/completions \
       GOOSE_MODEL="$MODELE" GOOSE_MODE=auto GOOSE_DISABLE_KEYRING=1
goose session
```

`goose run -t "<consigne>"` lance une tâche sans dialogue.

## OpenCode 1.19.6

Docker :

```dockerfile
RUN curl -fsSL -o /tmp/oc.tgz https://github.com/anomalyco/opencode/releases/download/v1.19.6/opencode-linux-x64.tar.gz \
 && echo "47734e08968b30cc22a0bffb6d9feeed76ad4aa743213a12122040392d09a057  /tmp/oc.tgz" | sha256sum -c --quiet \
 && tar -xzf /tmp/oc.tgz -C /usr/local/bin && rm /tmp/oc.tgz
```

Sans conteneur :

```bash
curl -fsSL -o oc.tgz https://github.com/anomalyco/opencode/releases/download/v1.19.6/opencode-linux-x64.tar.gz
echo "47734e08968b30cc22a0bffb6d9feeed76ad4aa743213a12122040392d09a057  oc.tgz" | sha256sum -c
mkdir -p sans-conteneur/harnais/bin && tar -xzf oc.tgz -C sans-conteneur/harnais/bin && rm oc.tgz
```

Configuration :

```bash
mkdir -p ~/.config/opencode && cat > ~/.config/opencode/opencode.json <<EOF
{"model": "iag/$MODELE", "small_model": "iag/$MODELE", "autoupdate": false, "share": "disabled",
 "provider": {"iag": {"npm": "@ai-sdk/openai-compatible", "name": "Portail IAG",
   "options": {"baseURL": "$OPENAI_BASE_URL", "apiKey": "{env:OPENAI_API_KEY}"},
   "models": {"$MODELE": {"name": "$MODELE", "tool_call": true}}}},
 "permission": {"edit": "allow", "bash": "allow", "webfetch": "deny"}}
EOF
opencode
```

`opencode run --auto "<consigne>"` lance une tâche sans dialogue. Au premier lancement, OpenCode télécharge environ 24 Mo de paquets depuis le registre npm (site autorisé par défaut).

## gptme 0.37.0

Docker :

```dockerfile
RUN pip install --no-cache-dir gptme==0.37.0
```

Sans conteneur (avec uv ; environnement Python « déplaçable », pour fonctionner dans la cage) :

```bash
uv venv --allow-existing --relocatable --python /usr/bin/python3 sans-conteneur/harnais
uv pip install --python sans-conteneur/harnais/bin/python gptme==0.37.0
```

Configuration :

```bash
mkdir -p ~/.config/gptme && cat > ~/.config/gptme/config.toml <<EOF
[[providers]]
name = "iag"
base_url = "$OPENAI_BASE_URL"
api_key_env = "OPENAI_API_KEY"
default_model = "$MODELE"
EOF
export GPTME_TIKTOKEN_TIMEOUT=0 GPTME_NO_LOCAL_DISCOVERY=1
gptme --tool-format tool -m "iag/$MODELE"
```

`--non-interactive "<consigne>"` lance une tâche sans dialogue.

## Pi 1.5.2

Docker :

```dockerfile
RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.5.2
```

Sans conteneur :

```bash
npm install -g --prefix sans-conteneur/harnais --ignore-scripts @earendil-works/pi-coding-agent@1.5.2
```

Configuration :

```bash
mkdir -p ~/.pi/agent && cat > ~/.pi/agent/models.json <<EOF
{"providers": {"iag": {"baseUrl": "$OPENAI_BASE_URL", "api": "openai-completions", "apiKey": "\$OPENAI_API_KEY",
  "models": [{"id": "$MODELE", "name": "$MODELE", "input": ["text"], "contextWindow": 128000, "maxTokens": 8192}]}}}
EOF
export PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0
pi --provider iag --model "$MODELE"
```

`-p "<consigne>"` lance une tâche sans dialogue. `contextWindow` et `maxTokens` sont à ajuster au modèle du portail ; `"input": ["text", "image"]` déclare un modèle qui lit les images.

## Cline CLI 3.0.74

Docker :

```dockerfile
RUN npm install -g --ignore-scripts cline@3.0.74
```

Sans conteneur :

```bash
npm install -g --prefix sans-conteneur/harnais --ignore-scripts cline@3.0.74
```

Configuration :

```bash
cline auth -p openai-compatible -k "$OPENAI_API_KEY" -m "$MODELE" -b "$OPENAI_BASE_URL"
cline
```

`cline -y "<consigne>"` lance une tâche sans dialogue. `cline auth` enregistre la clé locale dans `~/.cline`, sans risque : elle ne vaut rien hors du kit.

## Autre harnais

Chercher dans sa documentation la configuration d'un « fournisseur compatible OpenAI » (souvent nommé `openai-compatible`, `custom` ou `openai` avec une adresse de base). Lui donner l'adresse `$OPENAI_BASE_URL`, la clé `$OPENAI_API_KEY` et le modèle `$MODELE`. Si le harnais utilise la route `/v1/responses`, l'ajouter à `ROUTES_SUPPLEMENTAIRES` dans `.env`.
