# gptme : configuration

Retour à la [page d'entrée](../README.md). Toutes les commandes se lancent depuis la racine du dépôt.

## 1. Principe

gptme ne parle jamais directement au fournisseur du modèle. Il est déclaré auprès d'un « fournisseur personnalisé » compatible OpenAI, nommé `banc`, qui est le relais LiteLLM du banc (`http://127.0.0.1:4100/v1` dans la cage). Le relais détient la clé du portail compatible OpenAI ; gptme ne reçoit qu'une clé virtuelle propre à l'essai. La configuration est réécrite au début de chaque essai par [`configurer.sh`](../configurer.sh), appelé par [`lancer.sh`](../lancer.sh) : elle n'est jamais éditée à la main.

## 2. Ce que `configurer.sh` écrit

```bash
harnais/gptme/configurer.sh [DOSSIER]     # défaut : $HOME/.config/gptme
```

Dans la cage, `HOME` vaut `/home/banc` : le fichier est `/home/banc/.config/gptme/config.toml`, soit sur l'hôte `~/banc-espaces/<essai>/maison/.config/gptme/config.toml` (montage du dossier `maison` de l'essai, [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh)).

Exemple réel, produit le 27/11/2026 hors cage vers un dossier temporaire, avec le nom de modèle par défaut de `banc-essai/modele.env` :

```bash
BANC_MODELE_URL=http://127.0.0.1:4100 BANC_MODELE=modele-banc \
  harnais/gptme/configurer.sh /tmp/essai-config
```

```toml
[[providers]]
name = "banc"
base_url = "http://127.0.0.1:4100/v1"
api_key_env = "BANC_CLE_MODELE"
default_model = "modele-banc"

[env]
MODEL = "banc/modele-banc"
```

| Clé | Valeur | Rôle |
|---|---|---|
| `[[providers]]` `name` | `banc` | nom du fournisseur personnalisé ; les modèles s'écrivent `banc/<modèle>` |
| `base_url` | `$BANC_MODELE_URL` sans barre finale, suivi de `/v1` | adresse de l'API compatible OpenAI (une barre finale dans `BANC_MODELE_URL` est retirée : vérifié avec `http://127.0.0.1:4100/`) |
| `api_key_env` | `BANC_CLE_MODELE` | nom de la variable d'environnement qui contient la clé ; la clé elle-même n'est pas écrite |
| `default_model` | `$BANC_MODELE` | modèle utilisé si seul `banc` est demandé |
| `[env]` `MODEL` | `banc/$BANC_MODELE` | modèle par défaut ; redondant avec l'option `-m` de `lancer.sh`, qui prime |

Les clés de `[[providers]]` sont celles de la documentation officielle (`name`, `base_url`, `api_key`, `api_key_env`, `default_model` ; ordre de recherche de la clé : `api_key`, puis `api_key_env`, puis `<NOM>_API_KEY`) : <https://gptme.org/docs/providers-custom.html> (consulté le 27/11/2026).

Sans `BANC_MODELE_URL` ou `BANC_MODELE`, le script s'arrête (code 1) avec `BANC_MODELE: parameter null or not set` (essayé le 27/11/2026).

### Autres fichiers de configuration de gptme

| Fichier | Portée | Sur le banc | Source |
|---|---|---|---|
| `~/.config/gptme/config.toml` | utilisateur | écrit par `configurer.sh` | <https://gptme.org/docs/config.html> (consulté le 27/11/2026) |
| `~/.config/gptme/config.local.toml` | utilisateur, secrets, prime sur le précédent | absent | même source |
| `gptme.toml`, `gptme.local.toml` à la racine de l'espace de travail | projet | absents des recettes ; l'agent pourrait en créer un dans `/travail` | même source |
| `~/.local/share/gptme/logs/<conversation>/config.toml` | conversation, écrit par gptme au démarrage | constaté lors des essais de mise au point du banc : modèle, liste d'outils, `interactive = false`, `no_confirm = true`, `workspace = "/travail"`, section `[env]` vide | `~/banc-espaces/<essai>/maison/.local/share/gptme/logs/essai/config.toml` |

## 3. Variables lues

| Variable | Lue par | Usage | Origine dans la cage |
|---|---|---|---|
| `BANC_MODELE_URL` | `configurer.sh` | adresse du relais | `cage.sh` (`http://127.0.0.1:4100`) |
| `BANC_MODELE` | `configurer.sh`, `lancer.sh` | nom du modèle (`-m banc/$BANC_MODELE`) | `banc-essai/modele.env`, transmis par `cage.sh` |
| `BANC_CLE_MODELE` | gptme, au lancement (`api_key_env`) | clé virtuelle de l'essai | `/run/banc/cle.env`, chargé par [`interieur.sh`](../../../banc-essai/cage/interieur.sh) |
| `GPTME_TIKTOKEN_TIMEOUT=0` | gptme | ne télécharge pas le découpeur tiktoken ; compte approché à environ 4 caractères par jeton | posée par `lancer.sh` ; effet dans `gptme/util/tokens.py` |
| `GPTME_NO_LOCAL_DISCOVERY=1` | gptme | pas de recherche de serveurs locaux (Ollama `127.0.0.1:11434`, LM Studio `127.0.0.1:1234`) | posée par `lancer.sh` ; effet dans `gptme/llm/local_discovery.py` |
| `HTTPS_PROXY`, `NO_PROXY` | bibliothèques HTTP de gptme et de l'agent | filtre de la cage pour PyPI, Hugging Face, GitHub ; le relais (`127.0.0.1`) est joint sans mandataire | `cage.sh` |
| `BANC_CONTEXTE` | `lancer.sh` | exporté en `GPTME_CONTEXT_LENGTH` seulement s'il est inférieur à 128 000 jetons (modèle plus petit que la fenêtre supposée par gptme) ; à 128 000 ou au-delà, rien n'est exporté (valeur par défaut de `modele.env` : 128 000) ; voir section 4 | `banc-essai/modele.env` |
| `BANC_SORTIE_MAX`, `BANC_VISION`, `BANC_PRIX_*` | personne | transmises par la cage mais ignorées par le harnais gptme | `banc-essai/modele.env` |

Les chemins `gptme/...` désignent les sources du paquet installé, sous `harnais/gptme/installe/lib/python3.12/site-packages/` (hors git).

## 4. Changer de modèle ou de portail sans toucher au harnais

Le harnais ne connaît que le relais et le nom exposé du modèle. Tout se règle côté banc :

| Critère | Autre modèle du même portail | Autre portail compatible OpenAI | Mandataire, certificat d'entreprise pour joindre le portail |
|---|---|---|---|
| Où | `BANC_MODELE_FOURNISSEUR` (nom rendu par `GET <PORTAIL_URL>/models`) et capacités (`BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION`) dans `banc-essai/modele.env`, puis `banc-essai/traces/demarrer.sh` | `PORTAIL_URL` et `PORTAIL_CLE` dans `.env`, `BANC_MODELE_FOURNISSEUR` dans `modele.env`, vérification par `python3 banc-essai/traces/verifier_portail.py`, puis `demarrer.sh` | `BANC_MANDATAIRE`, `BANC_CERTIFICAT` dans `.env`, puis `demarrer.sh` |
| Effet sur gptme | aucun si `BANC_MODELE` reste `modele-banc` ; sinon le prochain essai écrit `banc/<nouveau nom>` dans `config.toml` ; `BANC_CONTEXTE` inférieur à 128 000 est transmis (ci-dessous) | aucun : gptme parle toujours au relais | aucun : c'est le relais qui sort |

Guide détaillé : [modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md). Le nom exposé doit rester fait de lettres, chiffres, points et tirets (commentaire de `modele.env`) ; gptme le reçoit précédé de `banc/`.

### Contexte, sortie maximale, vision et prix

gptme ne connaît pas le modèle du banc. Constats (sources de gptme 0.37.0 et essais de mise au point du banc) :

- Fenêtre de contexte : pour un fournisseur personnalisé, gptme retient une fenêtre générique de 128 000 jetons (`gptme/llm/models/resolution.py`, branche des fournisseurs personnalisés). Constaté lors des essais de mise au point du banc : rappel vers 103 000 jetons et compaction vers 115 000 jetons, soit 90 % de 128 000 (journal `compaction.jsonl` de la conversation et jetons d'entrée de `harnais/stdout.log`). Avec un modèle de fenêtre plus grande, gptme compacte donc avant la limite réelle ; avec un modèle de fenêtre inférieure à 128 000 jetons, il dépasserait la fenêtre avant de compacter.
- Ce que fait [`lancer.sh`](../lancer.sh) : si `BANC_CONTEXTE` (`banc-essai/modele.env`) est inférieur à 128 000, il exporte `GPTME_CONTEXT_LENGTH="$BANC_CONTEXTE"`, que gptme lit au démarrage à la place de la fenêtre du modèle (`gptme/init.py`) ; la compaction se cale alors sur la fenêtre déclarée. À 128 000 ou au-delà (128 000 est la valeur par défaut de `modele.env`), rien n'est exporté : fenêtre supposée de 128 000, comportement identique aux essais de mise au point. L'export n'a pas été essayé avec un modèle réel de moins de 128 000 jetons (non vérifié sur le banc). Il suppose une valeur de `BANC_CONTEXTE` exacte : une valeur trop haute ramène l'erreur de longueur de contexte du portail.
- Prix : pour le calcul du coût affiché, gptme emprunte les métadonnées du modèle recommandé d'OpenAI le plus proche (5 $ et 30 $ par million de jetons, fenêtre 1 000 000, dans `gptme/llm/llm_openai_models.py`), d'où l'avertissement `Unknown model openai/banc/modele-banc: using closest match metadata` et un coût affiché sans rapport avec la dépense réelle (constaté lors des essais de mise au point du banc). Le coût qui fait foi est celui du relais (`essai.json`) ; avec les prix conventionnels de 1 de `modele.env`, il se lit en millions de jetons.

Pistes, non appliquées sur le banc et non vérifiées :

| Critère | Fenêtre supérieure à 128 000 exploitée | Seuil de compaction | Prix, sortie maximale, vision |
|---|---|---|---|
| Réglage possible | `GPTME_CONTEXT_LENGTH` exporté sans la condition « inférieur à 128 000 » de `lancer.sh` (laissée pour garder le comportement des essais de mise au point) | `--context-budget 0.85` (fraction) ou `--context-budget 300000` (jetons), variable `GPTME_CONTEXT_BUDGET`, ou table `[models."banc/<modèle>"]` avec `context_budget = ...` dans `config.toml` | aucune clé de configuration dans la documentation consultée ; seule voie documentée : un greffon de fournisseur (point d'entrée `gptme.providers`) qui déclare pour chaque modèle ses métadonnées (`context`, `max_output`, `price_input`, `price_output`, `supports_vision`) |
| Source | code : `gptme/init.py` ; la documentation la présente pour les modèles locaux : <https://gptme.org/docs/context-compression.html> (consulté le 27/11/2026) | <https://gptme.org/docs/context-compression.html> (consulté le 27/11/2026) ; code : `gptme/util/context_budget.py`, `gptme/config/models.py` | <https://gptme.org/docs/providers-custom.html> (consulté le 27/11/2026) ; champs dans `gptme/llm/models/types.py` |

## 5. Autonomie, permissions, télémétrie et réseau

| Réglage | Valeur sur le banc | Effet | Source |
|---|---|---|---|
| Interaction | `--non-interactive` | exécute le message puis s'arrête ; implique `--no-confirm` : aucune confirmation avant une commande ou une écriture | `gptme --help` ; <https://gptme.org/docs/automation.html> (consulté le 27/11/2026) |
| Outils | jeu par défaut (aucune option `-t`) | 20 outils chargés, dont `shell`, `ipython`, `save`, `patch`, `vision`, `todo`, `autocompact`, `complete` (liste dans [fonctionnement.md](fonctionnement.md)) | `config.toml` de conversation, constaté lors des essais de mise au point du banc |
| Garde-fous de gptme | mode par défaut `shadow` (variable `GPTME_GUARDRAILS` non posée) | journalise ce qui serait bloqué sans rien bloquer (exemple constaté lors des essais de mise au point du banc, dans `harnais/stderr.log` : `Guardrail (shadow): would block — Credential output blocked`) | code : `gptme/hooks/guardrails.py` |
| Confinement réel | cage bubblewrap | écriture seulement dans `/travail`, `/home/banc`, `/tmp` ; réseau limité au relais, à l'API et au filtre de téléchargement | [`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md) |
| Télémétrie | inactive | OpenTelemetry n'est initialisé que si `GPTME_TELEMETRY_ENABLED` vaut `true`, `1` ou `yes` ; la cage efface l'environnement (`--clearenv`) et ne la pose pas | code : `gptme/util/_telemetry.py` ; [`banc-essai/cage/cage.sh`](../../../banc-essai/cage/cage.sh) |
| Découpeur tiktoken | téléchargement coupé (`GPTME_TIKTOKEN_TIMEOUT=0`) | sinon téléchargement depuis `openaipublic.blob.core.windows.net`, refusé par la cage | `lancer.sh` ; code : `tiktoken_ext/openai_public.py` |
| Recherche de serveurs locaux | coupée (`GPTME_NO_LOCAL_DISCOVERY=1`) | aucune sonde vers les ports d'Ollama et de LM Studio | `lancer.sh` |
| Outils web | `browser` indisponible (extension non installée) ; `--allow-hosts` non posé | le réseau est de toute façon filtré par la cage | `gptme --help`, `gptme-util tools list` |

Constaté lors des essais de mise au point du banc : les seules demandes au filtre réseau sont `pypi.org` et `files.pythonhosted.org`, acceptées, faites par l'agent pour installer des paquets ; aucune demande refusée (champ `hotes_refuses` vide dans `essai.json`). Les deux coupures posées par `lancer.sh` (tiktoken, recherche de serveurs locaux) évitent les demandes que gptme ferait sinon au démarrage et que la cage refuserait.

## 6. Où est la clé, où elle n'est pas

| Emplacement | Clé présente | Détail |
|---|---|---|
| `.env` à la racine du dépôt | clé du portail (`PORTAIL_CLE`) | jamais vue par la cage |
| `banc-essai/traces/secrets/cle-<essai>.env` | clé virtuelle de l'essai | créée par `cles.py`, copiée dans la cage, supprimée du relais à la fin de l'essai ([`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh)) |
| `/run/banc/cle.env` dans la cage | clé virtuelle | lecture seule ; chargée dans l'environnement par `interieur.sh` |
| Variable `BANC_CLE_MODELE` du processus gptme | clé virtuelle | visible par toute commande lancée par l'agent ; voulu : le programme écrit par l'agent appelle le modèle avec elle (constaté lors des essais de mise au point du banc, sur la tâche d'extraction) |
| `config.toml` écrit par `configurer.sh` | non | seulement le nom de la variable (`api_key_env`) |
| `config.toml` de la conversation | non | section `[env]` vide (constaté dans `gptme-jouet-1`) |
| Trace `stdout.log`, `stderr.log` | possible si l'agent affiche son environnement | `banc-essai/cage/masquer.py` remplace toute chaîne `sk-…` de 20 caractères ou plus par `sk-***` avant le rapport ; aucune clé trouvée dans les sorties des essais de mise au point du banc |

La clé du portail n'entre jamais dans la cage : c'est l'une des vérifications de la sonde de la cage (42 vérifications, 41 si `BANC_VISION=0`), à lancer après le branchement du portail : `banc-essai/cage/lancer.sh sonde jouet --essai sonde-portail` ([modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 3, étape 6).
