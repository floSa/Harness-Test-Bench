# Pi : installation

Retour : [page d'entrée de Pi](../README.md). Pages voisines : [configuration](configuration.md), [lancement](lancement.md), [fonctionnement](fonctionnement.md).

Toutes les commandes se lancent depuis la racine du dépôt. Pi est installé dans le dossier du harnais, avec sa propre copie de Node.js, parce que la cage ne montre au harnais que ce dossier (`/opt/harnais`, en lecture seule ; [`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md)) : un Node.js installé ailleurs sur le poste n'y serait pas visible.

## 1. Prérequis

| Élément | Exigence | Vérification | Source |
|---|---|---|---|
| Système | Linux x86-64 : `harnais/commun/installer-node.sh` télécharge seulement l'archive `linux-x64` de Node.js | `uname -m` doit répondre `x86_64` | [`installer-node.sh`](../../commun/installer-node.sh) |
| curl | téléchargement de Node.js | `curl --version` | idem |
| sha256sum, tar avec xz | contrôle d'empreinte et décompression de l'archive `.tar.xz` | `sha256sum --version`, `tar --version`, `xz --version` | idem |
| python3 | utilisé par `configurer.sh` à chaque lancement (Python du système, visible dans la cage par `/usr`) | `python3 --version` | [`configurer.sh`](../configurer.sh) |
| Node.js du poste | aucun : `installer.sh` installe le sien. Pi exige Node.js 22.19 ou plus récent ; un Node.js 20 de Debian s'est révélé trop ancien (constaté lors des essais de mise au point du banc, hors cage) | | [README de Pi v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md) |
| Accès réseau | sortie HTTPS vers `nodejs.org` et `registry.npmjs.org` (section 3) | | `installer.sh`, `installer-node.sh`, `installe/pi/package-lock.json` |
| Espace disque | environ 390 Mo : 230 Mo pour Node.js, 160 Mo pour Pi et ses dépendances (relevé par `du -sh` le 27/11/2026) | `du -sh harnais/pi/installe/*` | |
| Pour lancer un essai | bubblewrap, systemd de l'utilisateur, uv, Docker et le relais LiteLLM démarré | voir la page du banc | [`banc-essai/documentation/lancer-un-essai.md`](../../../banc-essai/documentation/lancer-un-essai.md), section 1 |

## 2. Installer

```bash
harnais/pi/installer.sh
```

Réponses possibles : `Pi 1.5.2 installé dans harnais/pi/installe/`, ou `Pi 1.5.2 déjà installé` si l'installation est déjà là (le script ne refait rien).

### Ce que fait `installer.sh`, pas à pas

| Étape | Action | Fichier |
|---|---|---|
| 1 | Si `installe/node/bin/node` existe et que `installe/pi/node_modules/@earendil-works/pi-coding-agent/package.json` porte la version 1.5.2 : message « déjà installé », arrêt | [`installer.sh`](../installer.sh) |
| 2 | Suppression de tout `harnais/pi/installe/`, puis création de `installe/pi/` | idem |
| 3 | Node.js v26.13.1 : téléchargement de `SHASUMS256.txt` et de `node-v26.13.1-linux-x64.tar.xz` depuis `https://nodejs.org/dist/v26.13.1/`, dans un dossier temporaire supprimé à la fin | [`installer-node.sh`](../../commun/installer-node.sh) |
| 4 | Contrôle d'empreinte : la ligne de l'archive dans `SHASUMS256.txt` est passée à `sha256sum -c` ; en cas d'écart, le script s'arrête avant toute décompression | idem |
| 5 | Décompression dans `harnais/pi/installe/node/` | idem |
| 6 | `npm install --silent --no-audit --no-fund --ignore-scripts --prefix installe/pi "@earendil-works/pi-coding-agent@1.5.2"`, avec le `npm` du Node.js qui vient d'être installé | `installer.sh` |
| 7 | Message de fin | `installer.sh` |

Détail des options npm :

| Option | Effet |
|---|---|
| `--ignore-scripts` | aucun script d'installation des paquets n'est exécuté ; la documentation de Pi précise que Pi n'en a pas besoin |
| `--no-audit`, `--no-fund` | pas de demande d'audit de sécurité ni de message de financement : moins d'appels réseau |
| `--prefix installe/pi` | tout est écrit dans `harnais/pi/installe/pi/` (paquet, 123 dépendances, `package-lock.json`) |

Vérification d'intégrité : npm compare chaque archive téléchargée à son empreinte `sha512` publiée par le registre ; le `package-lock.json` produit en garde la trace (124 entrées `integrity` relevées le 27/11/2026). Empreinte du paquet Pi 1.5.2 publiée par le registre : `sha512-mUWI04rqF1Vd/m1q+Ps1XeWsTXEVvRUnsmRa83I3Dzua0Tx5bYS93imeqtIfrXf7PkkaR6ERz+AuQhIJlom5yA==` ([registre npm](https://registry.npmjs.org/@earendil-works%2fpi-coding-agent/1.5.2), consulté le 27/11/2026), identique à celle du `package-lock.json` installé.

Limite : ni l'empreinte de Node.js ni le `package-lock.json` ne sont conservés dans git. L'empreinte de Node.js vient du `SHASUMS256.txt` téléchargé au même endroit que l'archive, et les dépendances de Pi sont résolues à chaque installation ; la documentation de Pi signale que l'installation par npm ne fige pas les dépendances indirectes ([README de Pi v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md), consulté le 27/11/2026). Deux installations à des dates différentes peuvent donc différer par une dépendance.

Emplacement : `harnais/pi/installe/` est exclu de git par la règle `harnais/*/installe/` de `.gitignore` (vérifié par `git check-ignore`). Hors de ce dossier, npm écrit seulement son cache, `~/.npm/_cacache` par défaut (`npm config get cache` répond `~/.npm`).

## 3. Sources réseau contactées à l'installation

À autoriser sur un poste d'entreprise (filtrage ou liste blanche du mandataire) :

| Hôte | Port | Contacté par | Contenu |
|---|---|---|---|
| `nodejs.org` | 443 | curl (`installer-node.sh`) | `SHASUMS256.txt` et l'archive de Node.js v26.13.1 (34 093 052 octets, en-tête `content-length` relevé le 27/11/2026) |
| `registry.npmjs.org` | 443 | npm | métadonnées et archives de Pi et de ses dépendances : les 123 adresses `resolved` du `package-lock.json` pointent toutes vers cet hôte |

Aucun autre hôte n'est appelé par les scripts. Après l'installation, Pi ne contacte aucun site dans le banc : il est lancé hors ligne et n'appelle que le relais local (voir [configuration](configuration.md), section 5).

## 4. Derrière un mandataire et un certificat d'entreprise

Le réglage `BANC_MANDATAIRE` de `.env` sert au relais LiteLLM et au filtre de la cage ([`banc-essai/documentation/modele-et-fournisseur.md`](../../../banc-essai/documentation/modele-et-fournisseur.md), section 4) ; `installer.sh` ne le lit pas. Pour l'installation, le mandataire et l'autorité interne se donnent par l'environnement du terminal, avant de lancer le script :

```bash
export HTTPS_PROXY=http://hote:port https_proxy=http://hote:port
export NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost
export NODE_EXTRA_CA_CERTS=/chemin/autorite-interne.pem
harnais/pi/installer.sh
```

| Outil | Mandataire | Autorité interne | Source |
|---|---|---|---|
| curl (Node.js) | `https_proxy` ou `HTTPS_PROXY` ; `NO_PROXY` pour les exceptions | `CURL_CA_BUNDLE` ou `SSL_CERT_FILE` : fichier PEM qui remplace la liste d'autorités, donc à composer avec les autorités publiques (par exemple `/etc/ssl/certs/ca-certificates.crt` une fois l'autorité interne ajoutée au système par l'administrateur du poste) | manuel de curl 8.5.0 du poste (`man curl`, section ENVIRONMENT) ; [curl.se/docs/manpage.html](https://curl.se/docs/manpage.html), consulté le 27/11/2026 |
| npm (Pi) | `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` ou `http_proxy` ; réglages `https-proxy`, `proxy`, `noproxy` (aussi par `npm_config_https_proxy`, etc.) | réglage `cafile` (variable `npm_config_cafile`), fichier PEM d'une ou plusieurs autorités | [npm, config](https://docs.npmjs.com/cli/v11/using-npm/config), consulté le 27/11/2026 |
| Node.js (npm et Pi) | `NODE_USE_ENV_PROXY=1` ou `--use-env-proxy` : Node.js lit alors `HTTP_PROXY`, `HTTPS_PROXY` et `NO_PROXY` | `NODE_EXTRA_CA_CERTS=fichier.pem` : ajoute ces autorités aux autorités publiques ; ignoré quand un programme impose sa propre liste (option `ca`), ce qui est le cas de npm si `cafile` est réglé | manuel de Node.js v26.13.1 installé (`harnais/pi/installe/node/share/man/man1/node.1`) ; [nodejs.org/api/cli.html](https://nodejs.org/api/cli.html#node_extra_ca_certsfile), consulté le 27/11/2026 |
| Pi lui-même (hors banc) | `HTTP_PROXY`, `HTTPS_PROXY` ; réglage `httpProxy` de `~/.pi/agent/settings.json` | | [environment-variables.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/environment-variables.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md), consultés le 27/11/2026 |

Non vérifié sur le banc : installation derrière un vrai mandataire d'entreprise, prise en compte de `NODE_EXTRA_CA_CERTS` par npm 11.20.0 sans `cafile`. En cas de refus de certificat par npm, `npm_config_cafile` est la voie documentée par npm. Ne jamais désactiver la vérification des certificats (`strict-ssl=false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`) : la règle du banc est la même pour le relais (page du banc citée plus haut).

Dans la cage, Pi n'a besoin ni du mandataire ni de l'autorité interne : il n'appelle que le relais du banc en HTTP sur `127.0.0.1:4100`, exclu du mandataire de la cage par `NO_PROXY` (voir [lancement](lancement.md), section 2).

## 5. Vérifier l'installation

Version de Node.js et de Pi :

```bash
harnais/pi/installe/node/bin/node --version
harnais/pi/installe/node/bin/node harnais/pi/installe/pi/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js --version
```

Réponses attendues : `v26.13.1` et `1.5.2` (relevées le 27/11/2026).

Démarrage dans la cage, sans réseau ni appel au modèle (configuration écrite dans un dossier jetable, clé factice) :

```bash
T=$(mktemp -d) && mkdir -p "$T/travail" "$T/maison"
banc-essai/cage/cage.sh --espace "$T/travail" --maison "$T/maison" --harnais harnais/pi \
  --sans-reseau --memoire 0 --duree 60 -- bash -c '
  /opt/harnais/configurer.sh
  export PATH=/opt/harnais/installe/node/bin:$PATH PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 BANC_CLE_MODELE=factice
  node /opt/harnais/installe/pi/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js --list-models'
rm -rf "$T"
```

Sortie relevée le 27/11/2026 avec les valeurs par défaut de `banc-essai/modele.env` (`BANC_MODELE=modele-banc`, `BANC_CONTEXTE=128000`, `BANC_SORTIE_MAX=16384`, `BANC_VISION=0`) :

```text
configuration écrite : /home/banc/.pi/agent/models.json, /home/banc/.pi/agent/settings.json
provider  model        context  max-out  thinking  images
banc      modele-banc  128K     16.4K    no        no
```

La ligne `banc` montre que Pi lit la configuration du banc et le modèle décrit dans `banc-essai/modele.env` ; la colonne `images` passe à `yes` avec `BANC_VISION=1`. Sans clé (`BANC_CLE_MODELE` absente), Pi répond « No models available » : il ignore un fournisseur sans clé.

Vérification complète, avec quelques appels au modèle par le portail : l'essai jouet.

```bash
banc-essai/cage/lancer.sh pi jouet
```

## 6. Mettre à jour la version figée

| Endroit | Contenu à changer |
|---|---|
| [`harnais/pi/installer.sh`](../installer.sh) | `VERSION=1.5.2` |
| [`harnais/pi/version`](../version) | `pi 1.5.2` (repris dans `essai.json` et les rapports) |
| [`harnais/pi/README.md`](../README.md) et ces pages | version citée |
| Empreinte de Pi | aucune à écrire : npm vérifie celle du registre ; commande pour la relever ci-dessous |
| Node.js | `VERSION=v26.13.1` dans [`harnais/commun/installer-node.sh`](../../commun/installer-node.sh), commun à Pi et Cline ; aucune empreinte à écrire (lue dans `SHASUMS256.txt`) |

Versions publiées et empreinte d'une version (le `npm` installé a besoin de son `node` dans `PATH`) :

```bash
PATH="$PWD/harnais/pi/installe/node/bin:$PATH" npm view @earendil-works/pi-coding-agent dist-tags
PATH="$PWD/harnais/pi/installe/node/bin:$PATH" npm view @earendil-works/pi-coding-agent@1.5.2 dist.integrity
```

Le 27/11/2026 : étiquette `latest` à 1.6.1, empreinte de la 1.5.2 conforme à celle de la section 2.

Après la modification de `VERSION` dans `installer.sh`, relancer `harnais/pi/installer.sh` : la version installée ne correspond plus, le script supprime `installe/` et réinstalle Node.js et Pi. Après un changement de la seule version de Node.js, le script répond « déjà installé » sans rien faire (il ne contrôle que la version de Pi) : supprimer d'abord `harnais/pi/installe/`.

Relire le journal des changements avant de passer à une nouvelle version (`CHANGELOG.md` du paquet, ou [CHANGELOG sur GitHub](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/CHANGELOG.md)), puis refaire l'essai jouet : les noms de réglages et de variables de [configuration](configuration.md) ont été vérifiés pour la 1.5.2 seulement.

## 7. Désinstaller

```bash
rm -rf harnais/pi/installe
```

| Emplacement | Contenu | Suppression |
|---|---|---|
| `harnais/pi/installe/` | Node.js et Pi | commande ci-dessus |
| `~/.npm/_cacache` | cache de npm, partagé avec tout npm du compte | facultative : `PATH="$PWD/harnais/pi/installe/node/bin:$PATH" npm cache clean --force` avant de supprimer `installe/` |
| `~/banc-espaces/<essai>/maison/.pi/` | configuration et session de chaque essai (hors dépôt) | avec l'espace de l'essai |

Pi n'écrit rien dans `~/.pi` du compte lors d'un essai : dans la cage, son dossier personnel est `~/banc-espaces/<essai>/maison/`.
