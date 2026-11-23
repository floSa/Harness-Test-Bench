# 1. Le principe

Un harnais d'agent (Goose, OpenCode, gptme, Pi, Cline…) exécute les commandes que décide un modèle de langage : lire, écrire, effacer, installer. Le modèle peut se tromper, ou obéir à une consigne cachée dans un document qu'il lit. On ne cherche donc pas à faire confiance au harnais : on borne ce qu'il peut atteindre.

![Le harnais est enfermé ; il ne parle au portail IAG que par le relais.](schema.png){width=15cm}

| Protection | Risque évité | Comment |
|---|---|---|
| Le harnais est enfermé | effacement ou lecture du reste du poste (clés SSH, documents) | conteneur ou cage : seul le dossier `espace/` est visible, le système est en lecture seule |
| Le harnais n'a pas la vraie clé | clé du portail recopiée dans une trace ou un fichier, puis réutilisée | un relais garde la clé et donne au harnais une clé locale, sans valeur ailleurs |
| Le harnais n'a pas Internet | envoi de fichiers vers l'extérieur, téléchargement de code piégé | réseau coupé ; seul le relais vers le portail IAG est joignable |
| Le harnais n'a aucun droit d'administration | modification du système | utilisateur ordinaire, aucun privilège |
| Mémoire et processus plafonnés | poste saturé par un programme qui s'emballe | limites du conteneur ou de systemd |

Trois façons de l'obtenir, au choix selon le poste. Les protections sont les mêmes.

| Mode | À choisir si | Section |
|---|---|---|
| Docker | `docker compose version` répond | 3 |
| Podman | `podman --version` répond, ou Podman peut être installé | 4 |
| Sans conteneur (bubblewrap) | ni Docker ni Podman | 5 |

# 2. Fichiers communs : le relais et les réglages

Créer un dossier de travail et y placer les deux fichiers suivants.

```bash
mkdir -p harnais-securise/espace && cd harnais-securise
```

**`relais.py`** : le seul programme qui connaît la clé du portail IAG. Il vérifie la clé locale du harnais, remplace celle-ci par la vraie clé et transmet l'appel au portail. Il ne relaie que l'appel au modèle.

{{code:relais.py:python}}

**`.env`** : les réglages. La commande crée aussi la clé locale. Ce fichier contient la clé du portail : ne jamais le partager.

```bash
cat > .env <<EOF
IAG_URL=https://<adresse du portail IAG>/v1
IAG_CLE=<clé personnelle du portail>
IAG_MODELE=<nom exact du modèle>
CLE_LOCALE=relais-$(openssl rand -hex 16)
UID_AGENT=$(id -u)
EOF
chmod 600 .env
```

Seul ce que l'on dépose dans `espace/` est visible du harnais, et peut donc partir au portail IAG.

# 3. Avec Docker

**`Dockerfile`** : l'image du harnais. Seule la ligne d'installation change d'un harnais à l'autre (section 7).

{{code:Dockerfile:dockerfile}}

**`compose.yaml`** : le relais et le harnais. Le réseau `interne` n'a aucune route vers l'extérieur ; seul le relais est aussi branché sur le réseau `sortie`.

{{code:compose.yaml:yaml}}

Construire, démarrer le relais, puis ouvrir un terminal dans le harnais :

```bash
docker compose build
docker compose up -d relais
docker compose run --rm harnais
```

Le terminal s'ouvre dans `/travail`, qui est le dossier `espace/` du poste. Faire les contrôles (section 6), puis configurer et lancer le harnais (section 7). Arrêter : `docker compose down`.

# 4. Avec Podman

Installer Podman s'il manque (Ubuntu) :

```bash
sudo apt install podman podman-compose
```

Mêmes fichiers que pour Docker, avec une ligne en plus dans `compose.yaml`, sous `harnais:`. Sans elle, Podman décale les numéros d'utilisateur et le harnais ne peut pas écrire dans `espace/`.

```yaml
  harnais:
    userns_mode: keep-id
```

Puis les mêmes commandes, avec `podman compose` :

```bash
podman compose build
podman compose up -d relais
podman compose run --rm harnais
```

Avec la version de podman-compose fournie par Ubuntu 24.04 (1.0.6), la limite du nombre de processus (`pids_limit`) n'est pas appliquée ; la limite de mémoire l'est.

# 5. Sans conteneur (bubblewrap)

bubblewrap enferme un programme avec les mêmes mécanismes du noyau qu'un conteneur, sans image ni service. socat sert de passage unique entre la cage et le relais.

```bash
sudo apt install bubblewrap socat
```

Créer les dossiers du harnais et y installer le harnais (exemple : Goose ; autres harnais en section 7) :

```bash
mkdir -p maison harnais/bin
curl -fsSL https://github.com/aaif-goose/goose/releases/download/v1.60.1/goose-x86_64-unknown-linux-gnu.tar.gz \
  | tar -xz -C harnais/bin ./goose
```

**Terminal 1 : le relais**, sur une socket privée :

```bash
mkdir -p "$XDG_RUNTIME_DIR/harnais" && chmod 700 "$XDG_RUNTIME_DIR/harnais"
set -a; . ./.env; set +a
ECOUTE="$XDG_RUNTIME_DIR/harnais/relais.sock" python3 relais.py
```

**Terminal 2 : la cage**, depuis le même dossier :

{{code:cage.sh:bash}}

Ce que fait chaque partie de la commande :

| Partie | Effet |
|---|---|
| `systemd-run … MemoryMax=8G TasksMax=2048` | plafonne la mémoire et le nombre de processus |
| `--unshare-all` | réseau, processus et utilisateurs propres à la cage : aucun accès à Internet |
| `--ro-bind /usr`, `/etc` | système du poste visible, en lecture seule |
| `--tmpfs /home`, `--bind espace /travail` | dossier personnel du poste invisible ; seul `espace/` est visible et modifiable |
| `--clearenv`, `--setenv` | environnement vide, puis seulement l'adresse du relais, la clé locale et le modèle |
| `socat …` | dans la cage, le port 8080 mène au relais, et à rien d'autre |

Sur Ubuntu 24.04, bubblewrap peut s'arrêter sur `setting up uid map: Permission denied`. Ubuntu fournit l'autorisation nécessaire sans l'activer ; pour l'activer (une fois par poste) :

```bash
sudo apt install apparmor-profiles
sudo cp /usr/share/apparmor/extra-profiles/bwrap-userns-restrict /etc/apparmor.d/
sudo apparmor_parser -r /etc/apparmor.d/bwrap-userns-restrict
```

# 6. Vérifier avant de commencer

Dans le terminal du harnais (conteneur ou cage), coller :

{{code:controles.sh:bash}}

Résultat attendu :

- `OK : pas d'Internet` ;
- `OK : clé du portail absente` ;
- dossiers personnels visibles : `agent` seulement ;
- fausse clé : `401` ;
- une réponse du modèle (JSON avec `"content"`).

Ne pas commencer si une ligne diffère.

# 7. Brancher un harnais

Dans le terminal du harnais, trois variables sont déjà définies : `OPENAI_BASE_URL` (adresse du relais), `OPENAI_API_KEY` (clé locale) et `MODELE`. Il suffit de les donner au harnais. Pour chaque harnais : la ligne d'installation, à placer dans le `Dockerfile` à la place de celle de Goose, puis la configuration, à taper dans le terminal du harnais.

**Goose 1.60.1** (installation : déjà dans le `Dockerfile` d'exemple)

```bash
export GOOSE_PROVIDER=openai OPENAI_HOST="${OPENAI_BASE_URL%/v1}" OPENAI_BASE_PATH=v1/chat/completions \
       GOOSE_MODEL="$MODELE" GOOSE_MODE=auto GOOSE_DISABLE_KEYRING=1
goose session
```

**OpenCode 1.19.6**

```dockerfile
RUN curl -fsSL https://github.com/anomalyco/opencode/releases/download/v1.19.6/opencode-linux-x64.tar.gz \
  | tar -xz -C /usr/local/bin
```

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

**gptme 0.37.0**

```dockerfile
RUN pip install gptme==0.37.0
```

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

**Harnais Node (Cline 3.0.74, Pi 1.5.2).** Ajouter d'abord Node 24 au `Dockerfile` :

```dockerfile
COPY --from=node:24-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:24-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
RUN npm install -g cline@3.0.74
```

```bash
cline auth -p openai-compatible -k "$OPENAI_API_KEY" -m "$MODELE" -b "$OPENAI_BASE_URL"
cline
```

Pour Pi : `RUN npm install -g @earendil-works/pi-coding-agent@1.5.2`, puis :

```bash
mkdir -p ~/.pi/agent && cat > ~/.pi/agent/models.json <<EOF
{"providers": {"iag": {"baseUrl": "$OPENAI_BASE_URL", "api": "openai-completions", "apiKey": "\$OPENAI_API_KEY",
  "models": [{"id": "$MODELE", "name": "$MODELE", "input": ["text"], "contextWindow": 128000, "maxTokens": 8192}]}}}
EOF
export PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0
pi --provider iag --model "$MODELE"
```

**Autre harnais** : configurer un « fournisseur compatible OpenAI » avec `$OPENAI_BASE_URL`, `$OPENAI_API_KEY` et `$MODELE`.

**Sans conteneur**, le harnais s'installe sur le poste dans `harnais/` au lieu du `Dockerfile` : binaire dans `harnais/bin` (Goose, OpenCode) ; pour les harnais Node, Node.js doit être installé sur le poste.

# 8. Ce que ces protections ne couvrent pas

| Limite | Que faire |
|---|---|
| Tout ce que le harnais lit dans `espace/` peut partir au portail IAG | n'y déposer que des données autorisées pour le portail |
| Pas de plafond de consommation dans le relais | s'appuyer sur le quota de la clé côté portail IAG ; une clé personnelle par testeur |
| Pas d'Internet, donc pas d'installation de paquets pendant le test | installer à l'avance ce dont le harnais a besoin (dans l'image, ou dans `harnais/`) |
| Conteneur et cage partagent le noyau du poste | pour des données très sensibles : une machine virtuelle dédiée en plus |
| Le code produit par le harnais peut être faux ou dangereux | le relire avant de l'exécuter hors de l'environnement fermé |
