# Cline : installation

[Retour à la page d'entrée](../README.md)

Toutes les commandes se lancent depuis la racine du dépôt. Aucune ne demande de droits administrateur ; `installer.sh` n'écrit que dans `harnais/cline/installe/` (et dans le cache npm du dossier personnel, voir section 3).

## 1. Prérequis

| Élément | Exigence | Vérification |
|---|---|---|
| Système | Linux x86-64 avec glibc : l'archive Node installée est `node-v26.13.1-linux-x64.tar.xz`, et le lanceur de Cline cherche le paquet `@cline/cli-<système>-<architecture>`, ici `@cline/cli-linux-x64` (lecture de `bin/cline` du paquet) | `uname -m` (attendu : `x86_64`) |
| Shell | bash | `bash --version` |
| Téléchargement | curl (archive Node et liste d'empreintes) | `curl --version` |
| Vérification d'empreinte | `sha256sum` (coreutils) | `sha256sum --version` |
| Décompression | tar avec xz | `tar --version`, `xz --version` |
| Node et npm | aucun à installer : `installer.sh` installe sa propre copie de Node.js 26.13.1 (avec npm 11.20.0, relevé dans un journal de npm) ; le `npm` éventuellement présent sur le poste n'est pas utilisé. Sous WSL, le `npm` trouvé dans le `PATH` peut être celui de Windows (constat du journal, 19/11/2026) : raison de cette copie propre | |
| Disque | 230 Mo pour Node, 415 Mo pour le paquet npm (dont 155 Mo pour le binaire Linux), plus l'archive Node le temps de l'installation | `df -h harnais/` |
| Pour lancer un essai | prérequis du banc : bubblewrap, systemd de l'utilisateur, uv, Docker, relais démarré | [lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section 1 |

La documentation officielle demande « Node.js 20+ (22 recommended) » ([installation](https://docs.cline.bot/cline-cli/installation.md), consulté le 27/11/2026). Le lanceur de la version 3.0.74 avertit en dessous de Node 22.15, qui ne sait pas lire le magasin de certificats du système (message de `bin/cline`). La copie installée (26.13.1) satisfait les deux.

## 2. Installer

```bash
harnais/cline/installer.sh
```

Sortie attendue à la première installation :

```text
Node v26.13.1 installé dans <racine>/harnais/cline/installe/node
Cline 3.0.74 installé dans harnais/cline/installe/
```

et, si la version figée est déjà en place :

```text
Cline 3.0.74 déjà installé
```

## 3. Ce que fait `installer.sh`, pas à pas

Sources : [`harnais/cline/installer.sh`](../installer.sh), [`harnais/commun/installer-node.sh`](../../commun/installer-node.sh).

| Étape | Commande du script | Détail |
|---|---|---|
| 1. Version figée | `VERSION=3.0.74` | écrite en dur dans `installer.sh` ; celle de Node (`VERSION=v26.13.1`) dans `installer-node.sh` |
| 2. Déjà installé ? | `installe/node/bin/node` exécutable et `"version": "3.0.74"` dans `installe/cline/node_modules/cline/package.json` | si oui : message et sortie, sans réseau |
| 3. Dossier neuf | `rm -rf installe && mkdir -p installe/cline` | l'installation précédente est supprimée avant tout téléchargement |
| 4. Node : téléchargement | `curl -fsSL` de `https://nodejs.org/dist/v26.13.1/SHASUMS256.txt` puis de `https://nodejs.org/dist/v26.13.1/node-v26.13.1-linux-x64.tar.xz`, dans un dossier temporaire supprimé à la sortie | `-f` : échec sur une erreur HTTP |
| 5. Node : intégrité | `grep " node-v26.13.1-linux-x64.tar.xz$" SHASUMS256.txt \| sha256sum -c --quiet -` | arrêt (`set -euo pipefail`) si l'empreinte diffère. La liste d'empreintes vient du même site que l'archive : la vérification protège d'un fichier abîmé, pas d'un site compromis |
| 6. Node : décompression | `tar -xJf … -C installe/node --strip-components=1` | donne `installe/node/bin/node`, `npm`, `npx` |
| 7. Paquet npm | `npm install --silent --no-audit --no-fund --ignore-scripts --prefix installe/cline "cline@3.0.74"` avec le npm de l'étape 6 en tête du `PATH` | version exacte ; `--ignore-scripts` : aucun script d'installation exécuté (voir ci-dessous) ; `--no-audit --no-fund` : pas d'appel au service d'audit |
| 8. Intégrité du paquet | faite par npm : chaque paquet téléchargé est comparé à l'empreinte `integrity` (sha512) annoncée par le registre et inscrite dans `installe/cline/package-lock.json` (325 paquets, tous avec `integrity`) | l'empreinte du binaire `@cline/cli-linux-x64@3.0.74` du fichier de verrouillage est identique à celle du registre (vérifié le 27/11/2026) |

Ce que contient le résultat :

| Chemin | Contenu |
|---|---|
| `installe/node/` | Node.js 26.13.1 complet |
| `installe/cline/node_modules/cline/bin/cline` | lanceur Node : lit le magasin de certificats du système, puis exécute le binaire de la plateforme |
| `installe/cline/node_modules/@cline/cli-linux-x64/bin/cline` | binaire autonome (moteur Bun embarqué, d'après l'en-tête de `bin/cline`) : c'est lui qui fait le travail |
| `installe/cline/node_modules/@cline/{sdk,core,agents,llms,shared}` et autres | dépendances JavaScript installées par npm ; le lanceur ne les charge pas (il n'exécute que le binaire) |
| `installe/cline/package-lock.json` | versions et empreintes réellement installées (hors git) |

Effet de `--ignore-scripts` : le script `postinstall.mjs` du paquet n'est pas exécuté. Il crée seulement un lien `bin/.cline` vers le binaire pour un démarrage plus rapide (en-tête du script) ; sans lui, le lanceur retrouve le binaire en parcourant `node_modules` (vérifié : `--version` répond 3.0.74).

Écritures hors de `installe/` : npm utilise son cache et ses journaux dans `~/.npm/` et lit `~/.npmrc` s'il existe (ligne `config load:file:<HOME>/.npmrc` d'un journal de npm). Le dépôt n'est pas touché : `installe/` est ignoré par git.

## 4. Sources réseau contactées

À autoriser sur un poste d'entreprise (pare-feu, liste blanche du mandataire) :

| Moment | Hôte | Port | Pour |
|---|---|---|---|
| Installation | `nodejs.org` | 443 | `SHASUMS256.txt` et archive de Node |
| Installation | `registry.npmjs.org` | 443 | description des paquets et 325 archives (tous les champs `resolved` de `package-lock.json` pointent vers cet hôte) |
| Utilisation hors cage (facultatif) | `registry.npmjs.org` | 443 | mise à jour automatique : à chaque commande, Cline lance `npm update --global cline --tag latest` (vu dans un journal de npm) ; à couper, voir [configuration](configuration.md#5-autonomie-télémétrie-mise-à-jour-automatique-et-réseau) |
| Utilisation hors cage (facultatif) | `data.cline.bot` | 443 | télémétrie et indicateurs de fonctionnalités (hôte associé au client PostHog dans le binaire) ; à couper, même page |
| Utilisation | le relais du banc, `127.0.0.1:4100` | | le modèle ; jamais le portail ni OpenRouter directement |

Dans la cage, `registry.npmjs.org` et `data.cline.bot` sont refusés par le filtre, sans effet sur l'essai (`banc-essai/resultats/cline-jouet-1/traces/reseau.jsonl`, champ `hotes_refuses` de `essai.json`).

Un miroir interne du registre npm peut remplacer `registry.npmjs.org` par le réglage `registry` de npm (variable `npm_config_registry`) ([npm config](https://docs.npmjs.com/cli/v11/using-npm/config), consulté le 27/11/2026). L'adresse de `nodejs.org` est écrite en dur dans `installer-node.sh` : un miroir de Node demanderait de modifier ce script.

## 5. Derrière un mandataire et un certificat d'entreprise

`installer.sh` ne lit pas `BANC_MANDATAIRE` ni `BANC_CERTIFICAT` du `.env` (ces réglages servent au relais et au filtre de la cage : [modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 4). Il hérite des variables du shell qui le lance. Les variables respectées par chaque outil, d'après leur documentation :

| Outil | Mandataire | Autorité de certification interne | Source |
|---|---|---|---|
| curl (`installer-node.sh`) | `HTTPS_PROXY` (ou `https_proxy`), `NO_PROXY` ; `http_proxy` n'existe qu'en minuscules | `CURL_CA_BUNDLE` ou `SSL_CERT_FILE` (fichier PEM, remplace la liste d'autorités) ; à défaut, magasin du système | [curl, page de manuel](https://curl.se/docs/manpage.html), section ENVIRONMENT, consulté le 27/11/2026 |
| npm (`installer.sh`) | réglage `https-proxy`, rempli par défaut depuis `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` ou `http_proxy` ; `noproxy` depuis `NO_PROXY` | réglage `cafile` (fichier PEM), par exemple par la variable `npm_config_cafile` ; ne pas couper `strict-ssl` | [npm config](https://docs.npmjs.com/cli/v11/using-npm/config), consulté le 27/11/2026 |
| Node (moteur de npm) | `NODE_USE_ENV_PROXY=1` fait lire `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` à Node lui-même (ajouté en 24.0.0) | `NODE_EXTRA_CA_CERTS=<fichier PEM>` ajoute des autorités aux autorités connues ; `NODE_USE_SYSTEM_CA=1` fait lire le magasin du système | [Node.js 26, options et variables](https://nodejs.org/docs/latest-v26.x/api/cli.html), consulté le 27/11/2026 |
| Cline à l'exécution | « standard HTTP proxy environment variables » ; mandataires HTTP seulement (ni SOCKS, ni PAC), authentification de base au plus | magasin du système lu automatiquement par le lanceur ; `NODE_EXTRA_CA_CERTS` fusionné avec lui | [réseau et mandataires](https://docs.cline.bot/troubleshooting/networking-and-proxies.md), README de la version 3.0.74 (section « Certificate trust »), consultés le 27/11/2026 |

Exemple d'installation derrière un mandataire avec une autorité interne (adresses fictives) :

```bash
HTTPS_PROXY=http://mandataire.exemple:3128 NO_PROXY=127.0.0.1,localhost \
CURL_CA_BUNDLE=/chemin/ac-entreprise.pem npm_config_cafile=/chemin/ac-entreprise.pem \
  harnais/cline/installer.sh
```

Non vérifié sur le banc (aucun mandataire d'entreprise disponible). Le fichier donné à `CURL_CA_BUNDLE` et à `cafile` doit contenir aussi les autorités publiques si le mandataire n'inspecte pas tout le trafic ; le fichier du système (`/etc/ssl/certs/ca-certificates.crt` sur Ubuntu) les contient déjà si l'administrateur y a ajouté l'autorité interne. Si l'autorité interne est dans le magasin du système, curl la trouve sans réglage.

À l'exécution, le lanceur de Cline écrit dans `$HOME/.cline/cli-node-extra-ca-certs.pem` les autorités du système, plus celles de `NODE_EXTRA_CA_CERTS` si la variable est définie, et fait pointer la variable du binaire vers ce fichier. Vérifié sur le poste :

```bash
HOME=$(mktemp -d) CLINE_NO_AUTO_UPDATE=1 CLINE_DEBUG=1 PATH="$PWD/harnais/cline/installe/node/bin:$PATH" \
  harnais/cline/installe/cline/node_modules/cline/bin/cline --version
```

```text
[cline] Trust: 360 OS + 0 user CAs (unchanged) -> <HOME>/.cline/cli-node-extra-ca-certs.pem
3.0.74
```

Dans la cage, `/etc` du poste est monté en lecture seule : une autorité ajoutée au magasin du système du poste y est donc visible. Le harnais n'y a pas besoin de mandataire pour le modèle (relais local, `NO_PROXY=127.0.0.1,localhost` posé par `cage.sh`).

## 6. Vérifier l'installation

```bash
export PATH="$PWD/harnais/cline/installe/node/bin:$PATH"
node --version                                                                  # attendu : v26.13.1
CLINE_NO_AUTO_UPDATE=1 harnais/cline/installe/cline/node_modules/cline/bin/cline --version   # attendu : 3.0.74
grep '"version"' harnais/cline/installe/cline/node_modules/@cline/cli-linux-x64/package.json # attendu : "3.0.74"
```

`CLINE_NO_AUTO_UPDATE=1` évite la tentative de mise à jour par npm à chaque commande (section 4). Les commandes `--version`, `--help`, `auth --help` n'appellent pas le modèle. Éviter `cline history` et la plupart des sous-commandes pour un simple contrôle : `cline history` a démarré un service d'arrière-plan (« hub », port `127.0.0.1:25463` par défaut) qui survit à la commande ; il s'arrête par `cline hub stop` avec le même `HOME` (constaté le 27/11/2026 avec un dossier personnel temporaire).

Vérification de bout en bout : l'essai jouet (`banc-essai/cage/lancer.sh cline jouet`, voir [lancement](lancement.md)).

## 7. Mettre à jour la version figée

1. Lire les changements de la nouvelle version (versions publiées : `curl -s https://registry.npmjs.org/cline | python3 -c "import json,sys; print(json.load(sys.stdin)['dist-tags'])"` ; notes de version sur le [dépôt officiel](https://github.com/cline/cline)).
2. Remplacer `VERSION=3.0.74` dans `harnais/cline/installer.sh` et le contenu de `harnais/cline/version` (`cline <version>`).
3. Lancer `harnais/cline/installer.sh` : la version lue dans `package.json` ne correspond plus, l'ancien dossier `installe/` est supprimé et tout est réinstallé (Node compris).
4. Vérifier (section 6), puis relancer l'essai jouet. Contrôler que `cline auth -p openai-compatible … -b …` et les options `--json -y` existent toujours (`cline --help`, `cline auth --help`), et que la trace garde la forme décrite dans [lancement](lancement.md#4-format-de-la-trace).
5. Noter le changement dans `documentations/journal.md`.

Pour changer la version de Node : `VERSION` dans `harnais/commun/installer-node.sh` (partagé avec Pi). `installer.sh` de Cline ne contrôle que la présence de `installe/node/bin/node`, pas sa version : supprimer `harnais/cline/installe/` pour forcer la réinstallation.

## 8. Désinstaller

```bash
rm -rf harnais/cline/installe
```

Restes éventuels, hors du dépôt :

| Emplacement | Origine | Action |
|---|---|---|
| `~/banc-espaces/<essai>/maison/.cline/` | dossier personnel de chaque essai (configuration, sessions, journaux, clé de l'essai déjà supprimée du relais) | supprimer `~/banc-espaces/<essai>/` quand l'essai n'est plus utile |
| `~/.npm/` | cache de npm pendant l'installation | `npm cache clean --force` (avec le npm installé) ou laisser |
| `~/.cline/` | seulement si Cline a été lancé hors cage avec le vrai dossier personnel | supprimer après `cline hub stop` |
