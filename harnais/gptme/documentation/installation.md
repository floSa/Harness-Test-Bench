# gptme : installation

Retour à la [page d'entrée](../README.md). Toutes les commandes se lancent depuis la racine du dépôt.

## 1. Prérequis

| Élément | Exigence | Pourquoi | Preuve |
|---|---|---|---|
| Système | Linux, WSL2 compris | la cage repose sur bubblewrap | [`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md) |
| Python | `/usr/bin/python3`, version 3.11.5 à 3.15 | gptme 0.37.0 exige `>=3.11.5,<3.16` ; le Python géré par uv vit dans le dossier personnel, invisible dans la cage | métadonnées du paquet (`installe/lib/python3.12/site-packages/gptme-0.37.0.dist-info/METADATA`) ; en-tête de [`installer.sh`](../installer.sh) |
| uv | dans le `PATH` | crée l'environnement virtuel et installe le paquet | [`installer.sh`](../installer.sh) |
| Disque | environ 200 Mo | 78 paquets installés, 194 Mo relevés pour `installe/` | relevé `du -sh harnais/gptme/installe` du 27/11/2026 |
| Réseau | accès HTTPS à PyPI, direct ou par un mandataire | téléchargement du paquet et de ses dépendances | section 3 |

Vérifier les deux premiers points :

```bash
/usr/bin/python3 --version
uv --version
```

Pour faire tourner un essai, il faut en plus le relais du modèle et la cage : voir [lancement.md](lancement.md) et la [documentation du banc](../../../banc-essai/documentation/README.md).

## 2. Ce que fait `installer.sh`, pas à pas

```bash
harnais/gptme/installer.sh
```

| Étape | Commande dans le script | Effet |
|---|---|---|
| 1 | `cd "$(dirname "$0")"` | travaille dans `harnais/gptme/`, quel que soit le dossier courant |
| 2 | test de `installe/bin/gptme` et de la version du paquet installé | si gptme 0.37.0 est déjà là : message `gptme 0.37.0 déjà installé`, arrêt sans rien changer |
| 3 | `rm -rf installe` | supprime une installation précédente (autre version, installation incomplète) |
| 4 | `uv venv -q --python /usr/bin/python3 installe` | crée l'environnement virtuel `harnais/gptme/installe/` sur le Python du système, sans téléchargement de Python |
| 5 | `uv pip install -q --python installe/bin/python "gptme==0.37.0"` | installe le paquet à la version figée et ses dépendances, résolues au moment de l'installation |
| 6 | lecture de la version installée | message `gptme 0.37.0 installé dans harnais/gptme/installe/` |

Points à connaître :

- Emplacement : `harnais/gptme/installe/`, ignoré par git (règle `harnais/*/installe/` de `.gitignore`). Dans la cage, ce dossier apparaît sous `/opt/harnais/installe/`, en lecture seule ([`banc-essai/cage/cage.sh`](../../../banc-essai/cage/cage.sh), montage `--ro-bind "$HARNAIS" /opt/harnais`).
- Vérification : seule la version de gptme est figée. Aucune empreinte n'est vérifiée et les dépendances ne sont pas figées (pas de fichier de verrouillage) : deux installations à des dates différentes peuvent donner des dépendances différentes. Ce point diffère de ce qu'annonce [`harnais/README.md`](../../README.md) (« empreinte ou intégrité vérifiée »).
- Aucune extension facultative (`gptme[browser]`, `gptme[telemetry]`, etc.) n'est installée : les outils `browser`, `morph`, `precommit`, `rag` et `screenshot` sont indisponibles (relevé `gptme-util tools list` du 27/11/2026, voir [fonctionnement.md](fonctionnement.md)).
- Le script `installe/bin/gptme` désigne son interpréteur par le chemin absolu de l'hôte (`#!/home/.../harnais/gptme/installe/bin/python`), invisible dans la cage ; c'est pourquoi [`lancer.sh`](../lancer.sh) appelle `installe/bin/python` et le module `gptme.cli.main` (constaté lors des essais de mise au point du banc : appeler `installe/bin/gptme` dans la cage fait échouer l'essai immédiatement, code 127). Conséquence pratique : déplacer le dépôt après l'installation casse aussi le script `installe/bin/gptme` sur l'hôte ; réinstaller.

## 3. Sources réseau contactées à l'installation

| Hôte | Port | Usage | Preuve |
|---|---|---|---|
| `pypi.org` | 443 | index des paquets (`https://pypi.org/simple`, index par défaut de uv) | `uv pip install --help` (uv 0.12.17) |
| `files.pythonhosted.org` | 443 | téléchargement des fichiers des paquets | hôte des fichiers de PyPI, vu dans les demandes de paquets (`traces/reseau.jsonl`) lors des essais de mise au point du banc |

Aucun téléchargement de Python : `--python /usr/bin/python3` désigne un interpréteur déjà présent. Sur un poste d'entreprise, ce sont les deux hôtes à autoriser dans le mandataire, ou à remplacer par un miroir interne de PyPI (section 4). La liste exacte des fichiers téléchargés n'a pas été relevée pendant l'installation du banc (non vérifié sur le banc).

Au fonctionnement, gptme peut contacter d'autres hôtes ; le banc les coupe (voir [configuration.md](configuration.md), section 5).

## 4. Derrière un mandataire et un certificat d'entreprise

`installer.sh` ne passe que par uv, qui lit les variables d'environnement suivantes ; il suffit de les exporter avant de lancer le script. Le script lui-même ne lit ni `BANC_MANDATAIRE` ni `BANC_CERTIFICAT` du `.env` (ces réglages ne servent qu'au relais et au filtre de la cage, voir [modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md)).

| Besoin | Variable | Exemple | Source |
|---|---|---|---|
| Mandataire HTTPS | `HTTPS_PROXY` (et `HTTP_PROXY`) | `export HTTPS_PROXY=http://identifiant:mot-de-passe@mandataire:8080` | référence des variables de uv |
| Hôtes à joindre sans mandataire | `NO_PROXY` | `export NO_PROXY=127.0.0.1,localhost` | référence des variables de uv |
| Autorité de certification interne (fichier PEM) | `SSL_CERT_FILE` | `export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt` | référence des variables et page des certificats de uv |
| Utiliser le magasin de certificats du système | `UV_SYSTEM_CERTS=true` (remplace `UV_NATIVE_TLS`, dépréciée) | `export UV_SYSTEM_CERTS=true` | référence des variables de uv |
| Miroir interne de PyPI | `UV_DEFAULT_INDEX` (remplace `UV_INDEX_URL`, dépréciée) | `export UV_DEFAULT_INDEX=https://miroir.interne/simple` | référence des variables de uv |
| Connexion lente | `UV_HTTP_TIMEOUT` (30 s par défaut) | `export UV_HTTP_TIMEOUT=120` | référence des variables de uv |

Exemple complet :

```bash
export HTTPS_PROXY=http://mandataire:8080 HTTP_PROXY=http://mandataire:8080
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
harnais/gptme/installer.sh
```

`SSL_CERT_FILE` remplace la liste d'autorités par défaut de uv : le fichier doit contenir l'autorité interne et les autorités publiques nécessaires (le fichier du système le fait en général quand l'autorité interne y a été ajoutée). Ne jamais désactiver la vérification des certificats.

`pip` n'est pas utilisé par l'installation. Il peut l'être dans la cage par l'agent (environnement virtuel de son espace de travail) : `pip` accepte `--cert` ou `PIP_CERT`, ainsi que `REQUESTS_CA_BUNDLE`, et utilise les certificats du système en plus de certifi depuis la version 24.2. Dans la cage, les téléchargements passent par le filtre du banc, qui ouvre un tunnel TLS de bout en bout et utilise lui-même `BANC_MANDATAIRE` ; les autorités vues par l'agent sont celles de `/etc` du poste, en lecture seule ([modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 4). Ni mandataire ni certificat d'entreprise n'ont été essayés avec ce harnais (non vérifié sur le banc).

Sources :

- uv, variables d'environnement : <https://docs.astral.sh/uv/reference/environment/> (consulté le 27/11/2026)
- uv, certificats : <https://docs.astral.sh/uv/concepts/authentication/certificates/> (consulté le 27/11/2026)
- pip, certificats HTTPS : <https://pip.pypa.io/en/stable/topics/https-certificates/> (consulté le 27/11/2026)

## 5. Vérifier l'installation

```bash
harnais/gptme/installe/bin/python -c 'import importlib.metadata as m; print(m.version("gptme"))'
harnais/gptme/installe/bin/python -c 'import sys; from gptme.cli.main import main; sys.argv[0] = "gptme"; sys.exit(main())' --version
```

Les deux commandes affichent `0.37.0` (relevé du 27/11/2026). La seconde passe par le même point d'entrée que [`lancer.sh`](../lancer.sh). Le fichier [`version`](../version) contient `gptme 0.37.0` : il est écrit à la main, pas par `installer.sh`.

Vérification de bout en bout, dans la cage, avec le modèle (quelques appels au modèle) : la tâche jouet, voir [lancement.md](lancement.md).

```bash
banc-essai/cage/lancer.sh gptme jouet --essai test-gptme
```

Pour lister les outils disponibles sans toucher au dossier personnel réel (gptme crée sinon `~/.config/gptme/config.toml` au premier lancement sur l'hôte ; commande essayée le 27/11/2026) :

```bash
HOME=$(mktemp -d) GPTME_NO_LOCAL_DISCOVERY=1 GPTME_TIKTOKEN_TIMEOUT=0 \
  harnais/gptme/installe/bin/python -c 'import sys; from gptme.cli.util import main; sys.argv[0] = "gptme-util"; sys.exit(main())' tools list
```

## 6. Mettre à jour la version figée

1. Relever la nouvelle version et sa date sur PyPI (<https://pypi.org/project/gptme/>) et lire les notes de version du dépôt officiel (<https://github.com/gptme/gptme/releases>) : options de ligne de commande, format de `config.toml`, format de la sortie JSON.
2. Changer `VERSION=` dans [`installer.sh`](../installer.sh) et le contenu du fichier [`version`](../version) (`gptme <version>`), les deux à la même valeur.
3. Réinstaller : `harnais/gptme/installer.sh` (le script supprime l'ancien `installe/`).
4. Vérifier `--help` : présence de `--non-interactive`, `--output-format json`, `--tool-format tool`, `--name`, `-m`.
5. Lancer la tâche jouet et comparer avec un essai jouet fait avec la version précédente (score, nombre d'appels, jetons, outils appelés).
6. Mettre à jour la [page d'entrée](../README.md) et [fonctionnement.md](fonctionnement.md).

Les essais déjà faits gardent la version utilisée dans leur `essai.json` (champ `version_harnais`).

## 7. Désinstaller

```bash
rm -rf harnais/gptme/installe
```

Restent hors du dépôt, à supprimer à la main si besoin :

| Emplacement | Contenu | Origine |
|---|---|---|
| `~/banc-espaces/<essai>/maison/.config/gptme/` et `.../.local/share/gptme/` | configuration et journaux de conversation de chaque essai (dossier `$BANC_ESPACES` s'il est défini) | [lancement.md](lancement.md), section 4 |
| `~/.config/gptme/`, `~/.local/share/gptme/` | configuration et conversations créées par un lancement de gptme sur l'hôte, hors cage | gptme écrit une configuration par défaut si le fichier n'existe pas (fonction `_load_config_doc` de `installe/lib/python3.12/site-packages/gptme/config/user.py`) ; constaté lors de la mise au point du banc : le fichier apparaît sur l'hôte dès les premières commandes de gptme lancées hors cage |
| cache de uv (`~/.cache/uv`) | paquets téléchargés | uv |

Après un essai sur un goldset, le dossier `maison/` de l'essai contient des extraits des documents (conversation de l'agent) : le traiter comme les résultats goldset (voir [securite-et-donnees.md](../../../banc-essai/documentation/securite-et-donnees.md)).
