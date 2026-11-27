# OpenCode : installation

[Retour à la page d'entrée](../README.md)

Toutes les commandes se lancent depuis la racine du dépôt. Aucune ne demande de droits administrateur ; rien n'est écrit hors de `harnais/opencode/installe/`.

## 1. Prérequis

| Élément | Exigence | Vérification |
|---|---|---|
| Système | Linux x86-64 avec glibc (l'archive installée est `opencode-linux-x64.tar.gz`, variante glibc ; les variantes `-musl` et `-baseline` existent mais ne sont pas utilisées) | `uname -m` (attendu : `x86_64`) |
| Shell | bash | `bash --version` |
| Téléchargement | curl | `curl --version` |
| Vérification d'empreinte | `sha256sum` (coreutils) | `sha256sum --version` |
| Décompression | tar avec gzip | `tar --version` |
| Configuration et lancement | `python3` du système (utilisé par `configurer.sh` et `lancer.sh`, aussi dans la cage) | `python3 --version` |
| Disque | 80 Mo pour l'archive, 216 Mo pour le binaire décompressé | `df -h harnais/` |
| Pour lancer un essai | prérequis du banc : bubblewrap, systemd de l'utilisateur, uv, Docker, relais démarré | [lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section 1 |

OpenCode n'a besoin ni de Node ni de npm : `installer.sh` n'utilise pas `harnais/commun/installer-node.sh` (réservé à Pi et Cline, voir l'en-tête de ce script). Le binaire embarque son propre environnement d'exécution : il contient la chaîne « Bun v1.4.4 » (relevé par `grep -a` sur `installe/opencode`).

## 2. Installer

```bash
harnais/opencode/installer.sh
```

Sortie attendue à la première installation :

```text
OpenCode 1.19.6 installé dans harnais/opencode/installe/
```

et, si la version figée est déjà en place :

```text
OpenCode 1.19.6 déjà installé
```

## 3. Ce que fait `installer.sh`, pas à pas

Source : [`harnais/opencode/installer.sh`](../installer.sh).

| Étape | Commande du script | Détail |
|---|---|---|
| 1. Version figée | `VERSION=1.19.6`, `ARCHIVE=opencode-linux-x64.tar.gz`, `SHA256=4773…a057` | la version et l'empreinte sont écrites en dur dans le script |
| 2. Déjà installé ? | `installe/opencode --version` comparé à `1.19.6` | si égal : message et sortie, sans réseau |
| 3. Dossier neuf | `rm -rf installe && mkdir -p installe` | l'installation précédente est supprimée avant le téléchargement |
| 4. Téléchargement | `curl -fsSL -o installe/opencode-linux-x64.tar.gz https://github.com/anomalyco/opencode/releases/download/v1.19.6/opencode-linux-x64.tar.gz` | `-f` : échec sur une erreur HTTP ; `-L` : suit la redirection de GitHub |
| 5. Intégrité | `sha256sum -c --quiet` sur l'empreinte du script | le script s'arrête (`set -euo pipefail`) si l'empreinte diffère |
| 6. Décompression | `tar -xzf … -C installe` | produit `installe/opencode` |
| 7. Nettoyage | `rm installe/opencode-linux-x64.tar.gz` | seule reste le binaire |
| 8. Contrôle | `installe/opencode --version` | affiché dans le message final |

L'empreinte du script est celle que GitHub publie pour cette archive : `sha256:47734e08968b30cc22a0bffb6d9feeed76ad4aa743213a12122040392d09a057`, champ `digest` de l'actif `opencode-linux-x64.tar.gz` de la version v1.19.6, publiée le 17/11/2026 ([API GitHub](https://api.github.com/repos/anomalyco/opencode/releases/tags/v1.19.6), consulté le 27/11/2026).

Le dossier `installe/` est exclu de git par la règle `harnais/*/installe/` de `.gitignore` (vérifié avec `git check-ignore -v harnais/opencode/installe/opencode`).

## 4. Sources réseau contactées

### 4.1 À l'installation

| Hôte | Port | Rôle | Constat |
|---|---|---|---|
| `github.com` | 443 | adresse de téléchargement de la version | répond par une redirection 302 (vérifié le 27/11/2026 avec `curl -sI`) |
| `release-assets.githubusercontent.com` | 443 | hébergement réel de l'archive (cible de la redirection) | idem |

Ce sont les deux seuls hôtes à autoriser sur un poste d'entreprise pour installer OpenCode.

### 4.2 Pendant un essai (pour mémoire)

Ces demandes partent de la cage et passent par son filtre réseau ; elles sont journalisées dans `traces/reseau.jsonl` du dossier de résultats de l'essai (`banc-essai/resultats/<essai>/`, ou `banc-essai/resultats-goldset/<essai>/` pour la recette `goldset`). Comportements constatés lors des essais de mise au point du banc.

| Hôte | Origine | Décision du filtre de la cage | Constat |
|---|---|---|---|
| `models.opencode.ai` | catalogue des modèles chargé par OpenCode au démarrage | refusé, sans effet sur l'essai | demande refusée à chaque démarrage ; message `Failed to fetch models.dev` dans `harnais/stderr.log` |
| `registry.npmjs.org` | installation en arrière-plan du paquet `@opencode-ai/plugin` dans le dossier de configuration | refusé, sans effet | idem ; message `background dependency install failed` |
| `github.com`, `release-assets.githubusercontent.com` | téléchargement de ripgrep 15.1.0 (moteur des outils `glob` et `grep` d'OpenCode) dans `~/.cache/opencode/bin`, au premier usage de ces outils dans l'essai (le dossier personnel est neuf à chaque essai) | accepté (quelques mégaoctets) | message `downloading ripgrep` dans `harnais/stderr.log` juste après le premier appel à `glob` ou `grep` ; volume dans `essai.json` (`telechargement_par_hote_octets`) ; aucun téléchargement quand l'agent n'utilise que `bash` et `read` |
| `pypi.org`, `files.pythonhosted.org` | paquets Python installés par le code que l'agent écrit (pas par OpenCode lui-même) | accepté | `traces/reseau.jsonl` |

Sur un poste d'entreprise, les téléchargements acceptés par la cage sortent par le mandataire de l'entreprise si `BANC_MANDATAIRE` est défini dans `.env` (voir [modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 4). GitHub doit alors être autorisé par ce mandataire, sinon ripgrep ne peut pas être téléchargé : comportement des outils `grep` et `glob` d'OpenCode dans ce cas non vérifié sur le banc.

## 5. Derrière un mandataire et un certificat d'entreprise

### 5.1 Installation (curl)

curl lit le mandataire dans l'environnement ; la vérification de l'empreinte garantit l'intégrité de l'archive quel que soit le chemin réseau.

| Besoin | Variable | Source |
|---|---|---|
| Mandataire HTTPS | `HTTPS_PROXY` ou `https_proxy` (« the lower case version has precedence ») | [page de manuel de curl](https://curl.se/docs/manpage.html), section ENVIRONMENT, consulté le 27/11/2026 (texte identique dans `man curl`) |
| Mandataire avec identifiant | `HTTPS_PROXY=http://identifiant:mot-de-passe@hote:port` | idem |
| Autorité de certification interne | `CURL_CA_BUNDLE=/chemin/ac.pem` (« used as the --cacert value ») ; sinon l'autorité doit être dans le magasin du système | idem |

```bash
HTTPS_PROXY=http://hote:port CURL_CA_BUNDLE=/chemin/ac.pem harnais/opencode/installer.sh
```

Le fichier PEM donné à `CURL_CA_BUNDLE` remplace la liste d'autorités de curl : il doit contenir aussi les autorités publiques si le mandataire n'inspecte pas tout le trafic (même remarque que pour `BANC_CERTIFICAT`, [modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 4). Installation derrière un mandataire : non vérifiée sur le banc.

### 5.2 Exécution d'OpenCode hors de la cage

La documentation de la version 1.19.6 ([network.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/network.mdx), consulté le 27/11/2026) indique :

| Besoin | Variable |
|---|---|
| Mandataire | `HTTPS_PROXY` (recommandé) ou `HTTP_PROXY` |
| Exclusion des adresses locales (« required ») | `NO_PROXY=localhost,127.0.0.1` : indispensable pour joindre le relais du banc sur `127.0.0.1:4100` |
| Mandataire avec identifiant | identifiant et mot de passe dans l'URL ; NTLM et Kerberos ne sont pas pris en charge (la documentation renvoie vers une passerelle) |
| Autorité interne | `NODE_EXTRA_CA_CERTS=/chemin/ac.pem` (« works for both proxy connections and direct API access ») |

### 5.3 Exécution dans la cage

La cage efface l'environnement (`--clearenv` dans `banc-essai/cage/cage.sh`) et fixe elle-même `HTTPS_PROXY=http://127.0.0.1:3128` (son filtre) et `NO_PROXY=127.0.0.1,localhost`. Aucun réglage n'est à faire pour OpenCode. `NODE_EXTRA_CA_CERTS` n'est pas transmis dans la cage : si le mandataire de l'entreprise inspecte le TLS, l'autorité interne doit être dans le magasin du système du poste (`/etc`, monté en lecture seule dans la cage), comme pour `uv` et `pip` ([modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 4). Lecture de ce magasin par OpenCode : non vérifié sur le banc.

## 6. Vérifier l'installation

```bash
harnais/opencode/installe/opencode --version          # 1.19.6
cat harnais/opencode/version                          # opencode 1.19.6
git check-ignore -v harnais/opencode/installe/opencode  # règle .gitignore:27
```

Contrôle de la configuration sans réseau ni appel au modèle (dossier personnel jetable, réseau coupé par bubblewrap) :

```bash
T=$(mktemp -d)
BANC_MODELE_URL=http://127.0.0.1:4100 BANC_MODELE=modele-banc harnais/opencode/configurer.sh "$T/.config/opencode"
env -i HOME="$T" PATH=/usr/bin:/bin BANC_CLE_MODELE=factice \
  bwrap --dev-bind / / --unshare-net --die-with-parent harnais/opencode/installe/opencode debug config
rm -rf "$T"
```

`debug config` affiche la configuration résolue (clé masquée en `***`) ; un fournisseur `banc` absent signale une syntaxe que la version ne lit pas (voir [configuration.md](configuration.md), section 2).

## 7. Mettre à jour la version figée

| Étape | Fichier ou commande |
|---|---|
| 1. Choisir la version | <https://github.com/anomalyco/opencode/releases> |
| 2. Relever l'empreinte publiée | `curl -fsSL https://api.github.com/repos/anomalyco/opencode/releases/tags/vX.Y.Z \| python3 -c 'import json,sys; [print(a["digest"]) for a in json.load(sys.stdin)["assets"] if a["name"]=="opencode-linux-x64.tar.gz"]'` |
| 3. Modifier le script | `harnais/opencode/installer.sh` : `VERSION=` et `SHA256=` (sans le préfixe `sha256:`) |
| 4. Modifier le relevé | `harnais/opencode/version` : `opencode X.Y.Z` (texte recopié dans `essai.json`) |
| 5. Installer | `harnais/opencode/installer.sh` (la version installée diffère : réinstallation) |
| 6. Vérifier la configuration | `debug config` comme en section 6 : la version 2 a changé la syntaxe (`providers`, `update`, `permissions` dans la documentation en ligne [opencode.ai/docs/config](https://opencode.ai/docs/config/), consulté le 27/11/2026) ; `configurer.sh` devra peut-être être réécrit |
| 7. Essai de contrôle | `banc-essai/cage/lancer.sh opencode jouet` |

Les essais déjà faits gardent leur version dans `essai.json` (`version_harnais`). Passer à une autre version change le harnais comparé : deux essais de versions différentes ne se comparent pas sans le signaler.

## 8. Désinstaller

```bash
rm -rf harnais/opencode/installe
```

Le harnais n'écrit rien d'autre sur le poste : sa configuration, ses sessions, son cache et ses journaux sont dans le dossier personnel de chaque essai, `~/banc-espaces/<essai>/maison/` (à supprimer avec l'espace de l'essai quand il n'est plus utile). La commande `opencode uninstall` de la documentation officielle ([cli.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/cli.mdx), consulté le 27/11/2026) vise une installation standard dans le dossier personnel de l'utilisateur : elle n'est pas utile ici et n'a pas été essayée.
