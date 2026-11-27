# Installation de Goose

Retour : [page d'entrée du harnais](../README.md). Pages voisines : [configuration](configuration.md), [lancement](lancement.md), [fonctionnement](fonctionnement.md).

Toutes les commandes s'exécutent depuis la racine du dépôt.

## 1. Prérequis

### Système

| Critère | Exigence | Preuve |
|---|---|---|
| Système | Linux x86_64 : l'archive installée est `goose-x86_64-unknown-linux-gnu.tar.gz`, sans choix d'architecture dans le script | [`installer.sh`](../installer.sh) |
| Bibliothèque C | glibc 2.28 ou plus récente | symboles du binaire 1.60.1 (`objdump -T`, version la plus haute demandée : `GLIBC_2.28`), relevé le 27/11/2026 |
| Autres bibliothèques | `libstdc++.so.6` (au moins `GLIBCXX_3.4.25`), `libgcc_s.so.1`, `libm`, `libdl`, `libpthread` | `ldd harnais/goose/installe/goose`, relevé le 27/11/2026 |
| Droits | aucun droit administrateur ; rien n'est écrit hors de `harnais/goose/installe/` | en-tête de [`installer.sh`](../installer.sh) |
| Disque | 64 Mo pour l'archive pendant l'installation, 204 Mo pour le binaire | taille annoncée par GitHub (`content-length`) et `du -h`, relevées le 27/11/2026 |
| Système vérifié | WSL2, Ubuntu 24.04, glibc 2.39 : installation et essais réussis | constaté lors des essais de mise au point du banc |

### Outils

| Outil | Usage | Paquet Ubuntu |
|---|---|---|
| `bash` | interprète du script | `bash` |
| `curl` | téléchargement de l'archive | `curl` |
| `sha256sum`, `rm`, `mkdir`, `mv` | vérification d'empreinte, fichiers | `coreutils` |
| `tar` (avec gzip) | extraction | `tar`, `gzip` |
| `find` | recherche du binaire si l'archive change de structure | `findutils` |

Pour lancer un essai, le banc demande en plus bubblewrap, `uv`, Python 3 et le relais LiteLLM : voir la [documentation du banc](../../../banc-essai/documentation/) et [`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md).

## 2. Ce que fait `installer.sh`, pas à pas

```bash
harnais/goose/installer.sh
```

| Étape | Action | Détail |
|---|---|---|
| 1 | se place dans `harnais/goose/` | `cd "$(dirname "$0")"` : le script fonctionne depuis n'importe quel dossier courant |
| 2 | fixe la version et l'empreinte | `VERSION=1.60.1`, `ARCHIVE=goose-x86_64-unknown-linux-gnu.tar.gz`, `SHA256=0327b185…635a` |
| 3 | sort sans rien faire si la bonne version est déjà là | `installe/goose --version` doit contenir `1.60.1` ; message `Goose 1.60.1 déjà installé` |
| 4 | vide le dossier d'installation | `rm -rf installe` puis `mkdir -p installe` |
| 5 | télécharge l'archive officielle | `curl -fsSL` depuis `https://github.com/aaif-goose/goose/releases/download/v1.60.1/goose-x86_64-unknown-linux-gnu.tar.gz` |
| 6 | vérifie l'empreinte SHA-256 | `sha256sum -c --quiet` : arrêt du script (code non nul) si l'archive diffère |
| 7 | extrait puis supprime l'archive | `tar -xzf` dans `installe/`, puis `rm` de l'archive |
| 8 | place le binaire | si `installe/goose` n'existe pas, le premier fichier nommé `goose` trouvé dans `installe/` y est déplacé (pour la 1.60.1, l'archive contient `./goose` à sa racine) |
| 9 | affiche la version installée | `1.60.1 installé dans harnais/goose/installe/` |

L'empreinte figée dans le script est identique à celle que GitHub publie pour cette archive (champ `digest` de l'API des versions : `sha256:0327b1857f8030343f59b77503e0455629bbf472c2901cb94b88389d6278635a`, relevé le 27/11/2026).

Le dossier `harnais/goose/installe/` est hors git : règle `harnais/*/installe/` du [`.gitignore`](../../../.gitignore). Vérification :

```bash
git check-ignore -v harnais/goose/installe/goose
```

## 3. Sources réseau contactées

### À l'installation

| Hôte | Port | Rôle | Preuve |
|---|---|---|---|
| `github.com` | 443 | adresse de l'archive, qui répond par une redirection (HTTP 302) | `curl -sI` sur l'adresse de l'archive, 27/11/2026 |
| `release-assets.githubusercontent.com` | 443 | hôte de stockage vers lequel pointe la redirection, qui sert l'archive (HTTP 200, 63 554 620 octets) | même relevé |

Sur un poste d'entreprise, ces deux hôtes sont à autoriser dans le mandataire ou le pare-feu. Aucun autre hôte n'est contacté par `installer.sh` ; la commande de vérification `goose --version` ne contacte rien.

### À l'exécution (pour mémoire)

| Hôte | Rôle | Sur le banc |
|---|---|---|
| `127.0.0.1:4100` | relais LiteLLM du banc (appels au modèle) | seul accès utile ; voir [configuration](configuration.md) |
| `models.dev` | catalogue de modèles que Goose tente de rafraîchir au démarrage (journal de Goose : `failed to refresh remote model catalog … https://models.dev/api.json`) | refusé par la cage, sans effet sur l'essai (constaté lors des essais de mise au point du banc : champ `hotes_refuses` de `essai.json`) |

Ces accès à l'exécution sont détaillés dans [fonctionnement](fonctionnement.md).

## 4. Derrière un mandataire et un certificat d'entreprise

`installer.sh` ne lit pas le `.env` du banc : la variable `BANC_MANDATAIRE` (utilisée par le relais et le filtre de la cage) ne s'applique pas au téléchargement. Le mandataire et l'autorité de certification se donnent à `curl` par des variables d'environnement, au moment de l'appel.

| Variable | Lue par | Effet | Source |
|---|---|---|---|
| `HTTPS_PROXY` ou `https_proxy` | `curl` | mandataire pour les adresses `https://` ; forme `http://hote:port` ou `http://identifiant:mot-de-passe@hote:port` ; la forme en minuscules l'emporte si les deux existent | page de manuel de curl 8.5.0, section ENVIRONMENT |
| `NO_PROXY` | `curl` | hôtes contactés sans mandataire | idem |
| `SSL_CERT_FILE` | `curl` | fichier PEM des autorités de confiance (équivaut à `--cacert`) | idem |
| `CURL_CA_BUNDLE` | `curl` | même effet que `SSL_CERT_FILE` | idem |
| `SSL_CERT_DIR` | `curl` | dossier d'autorités (équivaut à `--capath`) | idem |

Exemple (adresse et chemin à adapter ; le fichier PEM doit contenir l'autorité interne et, si le mandataire inspecte le trafic, les autorités publiques nécessaires) :

```bash
HTTPS_PROXY=http://mandataire.exemple:8080 \
SSL_CERT_FILE=/chemin/vers/autorites-entreprise.pem \
harnais/goose/installer.sh
```

La vérification des certificats n'est jamais désactivée (pas d'option `-k`) : en cas d'erreur de certificat, corriger le fichier PEM.

Pour Goose lui-même (hors du banc, ou pour un usage direct d'un portail en HTTPS), la documentation officielle indique que Goose lit `HTTP_PROXY`, `HTTPS_PROXY` (prioritaire sur `HTTP_PROXY`) et `NO_PROXY` ([variables d'environnement, section « HTTP Proxy »](https://goose-docs.ai/docs/guides/environment-variables) ; [problèmes connus, « Corporate Proxy or Firewall Issues »](https://goose-docs.ai/docs/troubleshooting/known-issues), consultés le 27/11/2026). Pour les certificats, la documentation ne dit rien ; le binaire 1.60.1 contient la bibliothèque `rustls-platform-verifier` et la chaîne `SSL_CERT_FILE`, et cette bibliothèque s'appuie sous Linux sur `rustls-native-certs`, qui lit d'abord `SSL_CERT_FILE` puis le magasin d'autorités du système ([rustls-platform-verifier](https://github.com/rustls/rustls-platform-verifier), [rustls-native-certs](https://github.com/rustls/rustls-native-certs), consultés le 27/11/2026). Prise en compte de `SSL_CERT_FILE` par Goose : non vérifié sur le banc.

Dans la cage, ces réglages sont inutiles pour le modèle : Goose y parle en HTTP simple au relais `127.0.0.1:4100`, que `NO_PROXY=127.0.0.1,localhost` exclut du mandataire filtrant ([`banc-essai/cage/cage.sh`](../../../banc-essai/cage/cage.sh)). C'est le relais, hors de la cage, qui joint le portail compatible OpenAI (`PORTAIL_URL` du `.env`), en passant par `BANC_MANDATAIRE` et `BANC_CERTIFICAT` s'ils sont renseignés.

## 5. Vérifier l'installation

```bash
harnais/goose/installe/goose --version     # attendu : 1.60.1
cat harnais/goose/version                  # attendu : goose 1.60.1
```

Pour voir où Goose range configuration, sessions et journaux sans toucher au dossier personnel réel, utiliser un dossier personnel temporaire :

```bash
HOME=$(mktemp -d) GOOSE_DISABLE_KEYRING=1 harnais/goose/installe/goose info
```

Sortie relevée le 27/11/2026 : `Config yaml: $HOME/.config/goose/config.yaml`, `Sessions DB (sqlite): $HOME/.local/share/goose/sessions/sessions.db`, `Logs dir: $HOME/.local/state/goose/logs`. Cette commande n'appelle pas le modèle mais tente de joindre `models.dev` (échec sans conséquence s'il n'y a pas d'accès réseau).

Un essai de bout en bout se fait avec la tâche jouet : voir [lancement](lancement.md).

## 6. Changer de version figée

Trois endroits sont à modifier ensemble :

| Fichier | Valeur | Remarque |
|---|---|---|
| [`installer.sh`](../installer.sh) | `VERSION=` | numéro sans le `v` |
| [`installer.sh`](../installer.sh) | `SHA256=` | empreinte de `goose-x86_64-unknown-linux-gnu.tar.gz` pour cette version |
| [`version`](../version) | `goose <version>` | recopié dans `essai.json` (`version_harnais`) par `banc-essai/cage/collecter.py` ; s'il n'est pas mis à jour, les essais porteront une version fausse |

Obtenir l'empreinte publiée par GitHub (exemple pour la version 1.61.1, la plus récente au 27/11/2026, publiée le 26/11/2026) :

```bash
gh api repos/aaif-goose/goose/releases/tags/v1.61.1 \
  --jq '.assets[] | select(.name=="goose-x86_64-unknown-linux-gnu.tar.gz") | .digest'
```

À défaut de `gh`, télécharger l'archive, calculer `sha256sum` et comparer à l'empreinte affichée sur la page de la version sur GitHub. Puis :

```bash
harnais/goose/installer.sh
harnais/goose/installe/goose --version
banc-essai/cage/lancer.sh goose jouet
```

La commande intégrée `goose update` (mise à jour vers la dernière version stable, [documentation](https://goose-docs.ai/docs/guides/updating-goose), consultée le 27/11/2026) n'est pas à utiliser sur le banc : elle ne passe pas par l'empreinte figée et ne met pas à jour `version`.

Une nouvelle version peut changer la configuration lue, les extensions activées par défaut ou le format de la trace : refaire la tâche jouet et relire [fonctionnement](fonctionnement.md) avant toute série d'essais sur le goldset.

## 7. Désinstaller

```bash
rm -rf harnais/goose/installe
```

Rien d'autre n'est installé sur la machine par `installer.sh`. Les fichiers créés par Goose pendant les essais (configuration, sessions, journaux) sont dans le dossier personnel de chaque essai, `~/banc-espaces/<essai>/maison/` (voir [lancement](lancement.md)), à supprimer avec l'espace de l'essai si besoin.

Exception : `harnais/goose/configurer.sh` lancé à la main sans argument, hors de la cage, écrit dans `~/.config/goose/config.yaml` du compte réel (et remplace un fichier existant). Le retirer dans ce cas, ou toujours donner un dossier en argument (voir [configuration](configuration.md)).
