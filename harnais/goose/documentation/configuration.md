# Configuration de Goose

Retour : [page d'entrée du harnais](../README.md). Pages voisines : [installation](installation.md), [lancement](lancement.md), [fonctionnement](fonctionnement.md).

Sur le banc, la configuration n'est jamais écrite à la main ni par `goose configure` (assistant interactif) : elle est produite à chaque essai, dans la cage, par [`configurer.sh`](../configurer.sh) (appelé par [`lancer.sh`](../lancer.sh)), puis complétée par des variables d'environnement. Configuration entièrement non interactive vérifiée hors cage puis dans la cage lors des essais de mise au point du banc.

## 1. Le fichier écrit

```bash
harnais/goose/configurer.sh [DOSSIER]     # défaut : $HOME/.config/goose
```

Le script écrit `DOSSIER/config.yaml` (il crée le dossier, et remplace le fichier s'il existe). Dans la cage, `HOME` vaut `/home/banc`, qui est le dossier `~/banc-espaces/<essai>/maison/` de la machine : le fichier se trouve donc, après l'essai, dans `~/banc-espaces/<essai>/maison/.config/goose/config.yaml`. La première ligne de `harnais/stderr.log` de chaque essai le confirme : `configuration écrite : /home/banc/.config/goose/config.yaml`.

Exemple, avec le nom de modèle par défaut de `banc-essai/modele.env`, vers un dossier temporaire (aucun effet sur le banc) :

```bash
BANC_MODELE_URL=http://127.0.0.1:4100 BANC_MODELE=modele-banc \
  harnais/goose/configurer.sh "$(mktemp -d)"
```

```yaml
GOOSE_PROVIDER: openai
GOOSE_MODEL: modele-banc
OPENAI_HOST: http://127.0.0.1:4100
OPENAI_BASE_PATH: v1/chat/completions
GOOSE_MODE: auto
GOOSE_TELEMETRY_ENABLED: false
GOOSE_DISABLE_SESSION_NAMING: true
```

Le fichier écrit dans la cage pendant un essai est identique (constaté lors des essais de mise au point du banc), avec la valeur de `BANC_MODELE` lue dans `banc-essai/modele.env`.

| Clé | Valeur sur le banc | Signification | Source |
|---|---|---|---|
| `GOOSE_PROVIDER` | `openai` | fournisseur intégré « OpenAI », utilisable avec tout point d'accès compatible | [fournisseurs](https://goose-docs.ai/docs/getting-started/providers) |
| `GOOSE_MODEL` | `$BANC_MODELE` (`modele-banc` par défaut) | nom du modèle envoyé dans chaque requête : le nom exposé par le relais | idem |
| `OPENAI_HOST` | `$BANC_MODELE_URL` | adresse de base du point d'accès (défaut : `api.openai.com`) | idem |
| `OPENAI_BASE_PATH` | `v1/chat/completions` | chemin ajouté à l'adresse ; c'est aussi la valeur par défaut, écrite ici pour être explicite | idem |
| `GOOSE_MODE` | `auto` | outils exécutés sans demande de confirmation (voir section 5) | [variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables), [modes de permission](https://goose-docs.ai/docs/guides/managing-tools/goose-permissions) |
| `GOOSE_TELEMETRY_ENABLED` | `false` | collecte anonyme d'usage coupée (c'est aussi la valeur par défaut) | [variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables), [données d'usage](https://goose-docs.ai/docs/guides/usage-data) |
| `GOOSE_DISABLE_SESSION_NAMING` | `true` | pas d'appel supplémentaire au modèle pour nommer la session | [variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables) |

Sources consultées le 27/11/2026.

Le fichier ne déclare aucune extension : Goose y ajoute ses extensions intégrées par défaut (section 6).

## 2. Variables lues

### Par `configurer.sh`

| Variable | Obligatoire | Fournie par | Effet si absente |
|---|---|---|---|
| `BANC_MODELE_URL` | oui | `banc-essai/cage/cage.sh`, valeur fixe `http://127.0.0.1:4100` (adresse du relais dans la cage) | arrêt : `BANC_MODELE_URL: parameter null or not set` |
| `BANC_MODELE` | oui | `banc-essai/cage/cage.sh`, lue dans `banc-essai/modele.env` | arrêt : `BANC_MODELE: parameter null or not set` (relevé le 27/11/2026) |

`BANC_MODELE_URL` ne doit pas contenir `/v1` : le chemin est ajouté par `OPENAI_BASE_PATH`.

### Par `lancer.sh` (dans la cage)

| Variable exportée | Valeur | Rôle |
|---|---|---|
| `OPENAI_API_KEY` | `$BANC_CLE_MODELE` (obligatoire, sinon arrêt) | clé virtuelle de l'essai (section 4) |
| `GOOSE_DISABLE_KEYRING` | `1` | trousseau système désactivé : il n'existe pas dans la cage ; toute valeur le désactive ([variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables)) |
| `GOOSE_TELEMETRY_ENABLED` | `false` | doublon du fichier |
| `GOOSE_DISABLE_SESSION_NAMING` | `true` | doublon du fichier |
| `GOOSE_MODE` | `auto` | doublon du fichier |
| `GOOSE_CONTEXT_LIMIT` | `$BANC_CONTEXTE`, seulement s'il est inférieur à 128 000 | fenêtre de contexte déclarée à Goose (section 7) |

Les variables d'environnement l'emportent sur `config.yaml` ([fichiers de configuration](https://goose-docs.ai/docs/guides/config-files), consulté le 27/11/2026) : les doublons garantissent le réglage même si le fichier était mal lu.

### Non lues

Goose n'utilise ni `BANC_SORTIE_MAX`, ni `BANC_VISION`, ni `BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE`, que la cage transmet pourtant (lus par OpenCode et Pi). `BANC_CONTEXTE` n'est utilisé que s'il est inférieur à 128 000 jetons : `lancer.sh` l'exporte alors en `GOOSE_CONTEXT_LIMIT` (section 7).

## 3. Lien avec `banc-essai/modele.env` : changer de modèle ou de portail

Chaîne complète, sans rien de propre à Goose :

| Étape | Fichier | Ce qui s'y décide |
|---|---|---|
| 1 | [`banc-essai/modele.env`](../../../banc-essai/modele.env) | nom du modèle chez le portail (`BANC_MODELE_FOURNISSEUR`), nom exposé aux harnais (`BANC_MODELE`, `modele-banc` par défaut), capacités (`BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION`), prix (`BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE`), plafond par essai (`BANC_BUDGET_ESSAI`) |
| 2 | `.env` à la racine (hors git) | adresse et clé du portail compatible OpenAI (`PORTAIL_URL`, `PORTAIL_CLE`), mandataire et certificat d'entreprise facultatifs (`BANC_MANDATAIRE`, `BANC_CERTIFICAT` ; modèle : [`.env.exemple`](../../../.env.exemple)) |
| 3 | `banc-essai/traces/demarrer.sh` | le relais relit sa configuration |
| 4 | [`banc-essai/cage/cage.sh`](../../../banc-essai/cage/cage.sh) | transmet `BANC_MODELE` et les autres `BANC_*` de `modele.env`, et fixe `BANC_MODELE_URL=http://127.0.0.1:4100` |
| 5 | [`configurer.sh`](../configurer.sh) | écrit `GOOSE_MODEL` et `OPENAI_HOST` à partir de ces variables |

Pour changer de modèle sur le portail compatible OpenAI, ou de portail : modifier `banc-essai/modele.env` et `.env`, relancer `banc-essai/traces/demarrer.sh`, puis lancer la tâche jouet. Aucun fichier de `harnais/goose/` n'est à modifier. Goose ne voit jamais l'adresse ni la clé du portail : il ne parle qu'au relais. Guide du banc : [`banc-essai/documentation/modele-et-fournisseur.md`](../../../banc-essai/documentation/modele-et-fournisseur.md).

Le nom exposé doit être accepté par le relais tel quel ; Goose l'envoie sans transformation (constaté lors des essais de mise au point du banc : champ `requestedModel` des événements de la trace, égal à `BANC_MODELE`).

## 4. Où est la clé, et où elle n'est pas

| Emplacement | Clé présente | Preuve |
|---|---|---|
| `banc-essai/traces/secrets/cle-<essai>.env` (hors git) | oui, sous le nom `BANC_CLE_MODELE`, créée par `banc-essai/traces/cles.py` au début de l'essai, supprimée du relais à la sortie du harnais | [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh), `banc-essai/traces/cles.py` |
| `/run/banc/cle.env` dans la cage | oui, copie en lecture seule | [`banc-essai/cage/cage.sh`](../../../banc-essai/cage/cage.sh) |
| environnement du harnais | oui : `interieur.sh` charge `cle.env`, puis `lancer.sh` la recopie dans `OPENAI_API_KEY` | [`banc-essai/cage/interieur.sh`](../../../banc-essai/cage/interieur.sh), [`lancer.sh`](../lancer.sh) |
| `config.yaml` | non : Goose ignore une clé placée dans ce fichier | [fichiers de configuration](https://goose-docs.ai/docs/guides/config-files), consulté le 27/11/2026 ; en-tête de [`configurer.sh`](../configurer.sh) |
| trousseau système, `secrets.yaml` | non : trousseau désactivé, aucun `goose configure` | [`lancer.sh`](../lancer.sh) |
| clé du portail (`PORTAIL_CLE`) | jamais dans la cage | vérifié par la sonde de la cage (`banc-essai/cage/sonde/`, 42 vérifications, 41 si `BANC_VISION=0`), dont l'absence de cette clé dans l'environnement du harnais |
| résultats de l'essai | masquée : toute chaîne qui ressemble à une clé est remplacée par `banc-essai/cage/masquer.py` | [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh) |

Dans la documentation officielle, la variable d'environnement du fournisseur (`OPENAI_API_KEY`) l'emporte sur les secrets enregistrés ([fichiers de configuration](https://goose-docs.ai/docs/guides/config-files)).

## 5. Autonomie

`GOOSE_MODE: auto` correspond au mode « Completely Autonomous » : Goose modifie, crée et supprime des fichiers et lance des commandes sans demander d'approbation. C'est le mode par défaut ([modes de permission](https://goose-docs.ai/docs/guides/managing-tools/goose-permissions), consulté le 27/11/2026). Sur le banc, la cage borne ce que Goose peut toucher : écriture seulement dans `/travail`, `/home/banc`, `/tmp` ; réseau limité au relais, à l'API de soumission et au filtre PyPI, Hugging Face, GitHub ([`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md)).

| Mode | Comportement documenté | Usage sur le banc |
|---|---|---|
| `auto` | aucune confirmation | utilisé |
| `approve` | confirmation avant chaque outil | inutilisable : l'entrée standard est fermée pendant un essai ; sous-agents désactivés ([sous-agents](https://goose-docs.ai/docs/guides/context-engineering/subagents)) |
| `smart_approve` | confirmation seulement pour les actions jugées risquées | idem |
| `chat` | conversation sans outil (commande `/mode`, [commandes de la CLI](https://goose-docs.ai/docs/guides/goose-cli-commands)) | sans intérêt pour l'extraction |

Hors de la cage, le mode `auto` exécute des commandes sur la machine réelle sans confirmation : ne pas lancer `goose run` avec l'extension `developer` en dehors de la cage (voir [lancement, section 9](lancement.md#9-essai-à-la-main)).

## 6. Télémétrie, réseau et extensions

| Point | Réglage ou constat | Preuve |
|---|---|---|
| Télémétrie de Goose | coupée (`GOOSE_TELEMETRY_ENABLED=false`) | [`configurer.sh`](../configurer.sh), [`lancer.sh`](../lancer.sh) |
| Nommage automatique des sessions | coupé (pas d'appel au modèle en tâche de fond) | idem |
| Catalogue `models.dev` | Goose tente de le joindre au démarrage ; la demande passe par le mandataire de la cage (`HTTPS_PROXY`) et est refusée, sans effet | constaté lors des essais de mise au point du banc (`hotes_refuses` de `essai.json`, `traces/reseau.jsonl`) |
| Mandataire | Goose respecte `HTTPS_PROXY` (la demande vers `models.dev` arrive au filtre de la cage) et `NO_PROXY` (les appels au relais `127.0.0.1:4100` réussissent) | constaté lors des mêmes essais (`traces/reseau.jsonl`, `traces/appels.jsonl`) |
| Extensions | `config.yaml` n'en déclare aucune ; `lancer.sh` ajoute `--with-builtin developer` ; les extensions intégrées activées par défaut restent chargées | voir ci-dessous |

Extensions activées par défaut dans la version 1.60.1, relevées le 27/11/2026 par `goose info -v` (dossier personnel temporaire) et dans les sessions exportées lors des essais de mise au point du banc :

| Extension | Activée | Outils présentés au modèle (`advertised_tools` de la trace) |
|---|---|---|
| `developer` | oui | `shell`, `write`, `edit`, `tree`, `read_image` |
| `analyze` | oui | `analyze` |
| `summon` | oui | `delegate` (sous-agents), `load`, `load_skill` |
| `apps` | oui | `apps__create_app`, `apps__iterate_app`, `apps__list_apps`, `apps__delete_app` |
| `extensionmanager` | oui | `extensionmanager__search_available_extensions`, `extensionmanager__manage_extensions`, `extensionmanager__list_resources`, `extensionmanager__read_resource` |
| `tom` (Top of Mind) | oui | aucun outil (instructions injectées à chaque tour) |
| `scheduler` | oui | aucun outil listé dans la trace |
| `todo` | non | |
| `chatrecall` | non | |
| `summarize` | non | |
| `code_execution` | non | |

Au total, 17 outils sont présentés au modèle, et non les seuls outils de `developer` (constaté lors des essais de mise au point du banc). L'option `--no-profile` de `goose run` (« Don't load your default extensions, only use CLI-specified extensions », `goose run --help` de la 1.60.1) permettrait de ne garder que `developer` ; elle n'est pas utilisée sur le banc.

## 7. Fenêtre de contexte

Constat : sans déclaration, Goose suppose une fenêtre de 128 000 jetons pour un modèle qu'il ne connaît pas (c'est le cas de `modele-banc`, nom propre au relais), et compacte la conversation à 80 % de cette valeur. Lors des essais longs de mise au point du banc, avec un modèle dont la fenêtre réelle dépassait largement 128 000 jetons, la trace contient le message `Exceeded auto-compact threshold of 102k tokens. Performing auto-compaction...`.

Documentation officielle (consultée le 27/11/2026) :

| Réglage | Effet documenté | Source |
|---|---|---|
| `GOOSE_CONTEXT_LIMIT` (entier, en jetons) | remplace la fenêtre de contexte du modèle principal ; « particulièrement utile » derrière un mandataire LiteLLM ou pour un nom de modèle inconnu ; défaut : valeur propre au modèle, sinon 128 000 | [variables d'environnement, « Model Context Limit Overrides »](https://goose-docs.ai/docs/guides/environment-variables) |
| ordre de priorité | 1. `GOOSE_CONTEXT_LIMIT` ; 2. fournisseur personnalisé déclaré ; 3. découverte auprès du fournisseur ; 4. métadonnées connues du modèle ; 5. 128 000. Ces remplacements ne marchent que par variable d'environnement, pas dans le fichier de configuration | [gestion du contexte](https://goose-docs.ai/docs/guides/sessions/smart-context-management) |
| `GOOSE_AUTO_COMPACT_THRESHOLD` | part de la fenêtre qui déclenche la compaction (défaut 0,8 ; 0 la désactive) | idem |
| `GOOSE_AUTO_COMPACT_TOKEN_LIMIT` | seuil absolu (défaut 225 000) ; le déclencheur est le plus petit des deux seuils | idem |
| fournisseur personnalisé | fichier JSON dans `~/.config/goose/custom_providers/`, champ `context_limit` par modèle | [fournisseurs, « custom providers »](https://goose-docs.ai/docs/getting-started/providers) |

Les chaînes `GOOSE_CONTEXT_LIMIT` et `GOOSE_AUTO_COMPACT_TOKEN_LIMIT` figurent dans le binaire 1.60.1 (`strings`, relevé le 27/11/2026).

Appliqué depuis le 27/11/2026, dans `lancer.sh`, pour un modèle plus petit que la fenêtre supposée : si `BANC_CONTEXTE` est inférieur à 128 000, il est exporté en `GOOSE_CONTEXT_LIMIT`, sans quoi Goose dépasserait la fenêtre du modèle avant de compacter. Au-delà de 128 000, rien n'est changé : Goose garde sa fenêtre supposée de 128 000 jetons et compacte vers 102 000. Effet de `GOOSE_CONTEXT_LIMIT` non vérifié avec un modèle réel.

Piste non appliquée, pour déclarer aussi une grande fenêtre :

```bash
export GOOSE_CONTEXT_LIMIT="${BANC_CONTEXTE:-128000}"
```

Avec la documentation actuelle, la compaction se déclencherait alors au plus petit de 0,8 × `BANC_CONTEXTE` et de 225 000 jetons, sauf à relever aussi `GOOSE_AUTO_COMPACT_TOKEN_LIMIT`. Effet réel sur la version 1.60.1 : non vérifié sur le banc. De même, `GOOSE_MAX_TOKENS` (longueur maximale d'une réponse, [fichiers de configuration](https://goose-docs.ai/docs/guides/config-files)) pourrait recevoir `BANC_SORTIE_MAX` : non vérifié sur le banc.

Tout changement de ce type modifie le comportement du harnais et rend les essais déjà faits non comparables : à décider et à consigner avant une série d'essais.

## 8. Usage hors du banc (non vérifié sur le banc)

Pour viser directement un portail compatible OpenAI (sans relais), les mêmes clés suffisent en principe : `OPENAI_HOST` = adresse du portail sans le chemin, `OPENAI_BASE_PATH` = chemin complet de l'appel (par exemple `v1/chat/completions`), `GOOSE_MODEL` = nom donné par `GET <portail>/models`, clé dans `OPENAI_API_KEY`. Toujours écrire la configuration dans un dossier jetable plutôt que dans `~/.config/goose` :

```bash
export GOOSE_PATH_ROOT=$(mktemp -d)     # racine de config/, data/, state/ (documentation : variables d'environnement)
```

`GOOSE_PATH_ROOT` est documentée ([variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables), consultée le 27/11/2026) ; son effet n'a pas été essayé sur le banc.
