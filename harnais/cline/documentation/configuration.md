# Cline : configuration

[Retour à la page d'entrée](../README.md)

Cline ne lit pas de fichier de configuration écrit par le banc : il est configuré par sa propre commande `cline auth`, que `configurer.sh` appelle au début de chaque essai, dans la cage. Rien n'est à régler à la main pour un essai normal.

## 1. Ce que fait `configurer.sh`

Source : [`harnais/cline/configurer.sh`](../configurer.sh). Le script exige trois variables (arrêt avec un message si l'une manque), met le Node du harnais en tête du `PATH`, puis lance :

```bash
cline auth -p openai-compatible -k "$BANC_CLE_MODELE" -m "$BANC_MODELE" -b "${BANC_MODELE_URL%/}/v1"
```

| Option de `cline auth` | Valeur sur le banc | Sens ([CLI reference](https://docs.cline.bot/cline-cli/cli-reference.md), consulté le 27/11/2026) |
|---|---|---|
| `-p` | `openai-compatible` | fournisseur : tout service compatible OpenAI à adresse personnalisée. La documentation cite plutôt l'identifiant `openai` ; sur la 3.0.74, `openai` et `openai-compatible` donnent le même fournisseur enregistré (constat du journal, 19/11/2026) |
| `-k` | clé virtuelle de l'essai | clé d'API, enregistrée par Cline |
| `-m` | `BANC_MODELE` (`deepseek-v4.1-flash` dans `modele.env`) | nom du modèle tel que le relais l'expose |
| `-b` | `http://127.0.0.1:4100/v1` | adresse de base ; Cline y ajoute `/chat/completions` |

Sortie (sur l'erreur standard de l'essai, `harnais/stderr.log`) :

```text
Provider configured: openai-compatible (deepseek-v4.1-flash)
```

`cline auth` n'appelle ni le relais ni le modèle : lancé hors cage avec des valeurs factices (`BANC_MODELE=essai`, `BANC_CLE_MODELE=sk-factice`) et un dossier personnel temporaire, il répond « Provider configured » sans erreur.

## 2. Variables lues

| Variable | Origine | Lue par Cline |
|---|---|---|
| `BANC_MODELE_URL` | `cage.sh` (`--setenv`), toujours `http://127.0.0.1:4100` dans la cage | oui (`-b`) |
| `BANC_MODELE` | `banc-essai/modele.env`, transmis par `cage.sh` | oui (`-m`) |
| `BANC_CLE_MODELE` | `/run/banc/cle.env`, écrit par `banc-essai/traces/cles.py` et chargé par `interieur.sh` | oui (`-k`) |
| `BANC_CONTEXTE` | `modele.env` | non (voir section 7) |
| `BANC_SORTIE_MAX` | `modele.env` | non |
| `BANC_VISION` | `modele.env` | non |
| `BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE` | `modele.env` | non ; le coût que Cline affiche dans sa trace (0,00157593 $ sur l'essai jouet) est pourtant égal à la dépense relevée par le relais (`banc-essai/resultats/cline-jouet-1/essai.json`, `depense_cle_usd`) |
| `HTTPS_PROXY`, `NO_PROXY` | `cage.sh` : filtre de la cage sur `127.0.0.1:3128`, relais local exclu | oui : les sorties vers `data.cline.bot` et `registry.npmjs.org` passent par le filtre (`traces/reseau.jsonl` de l'essai jouet) |
| `HOME` | `cage.sh` : `/home/banc`, dossier `~/banc-espaces/<essai>/maison` de l'hôte | oui : dossier de configuration `~/.cline` |

## 3. Fichiers écrits dans `$HOME/.cline`

Relevés dans le dossier personnel de l'essai jouet (`~/banc-espaces/cline-jouet-1/maison/.cline/`) et avec un dossier personnel temporaire :

| Fichier | Écrit par | Contenu |
|---|---|---|
| `data/settings/providers.json` | `cline auth` | fournisseur, modèle, adresse, **clé en clair** ; droits `600` |
| `cli-node-extra-ca-certs.pem` | le lanceur `bin/cline`, à chaque commande | autorités du magasin du système (et de `NODE_EXTRA_CA_CERTS`), voir [installation](installation.md#5-derrière-un-mandataire-et-un-certificat-dentreprise) |
| `data/sessions/<id>/<id>.json` | l'essai | résumé de la session : modèle, dossier, consigne, outils de sous-agents et d'équipe actifs ou non, jetons, coût |
| `data/sessions/<id>/<id>.messages.json` | l'essai | conversation complète avec le modèle |
| `data/db/sessions.db` | l'essai | index SQLite des sessions |
| `data/logs/cline.log` | l'essai | journal d'exécution, une ligne JSON par événement (dont les événements de télémétrie, `telemetrySink: TelemetryLoggerSink`) |
| `data/logs/hooks.jsonl` | l'essai | événements des points d'accroche (début d'agent, outils) |
| `data/cache/feature-flags.json` | l'essai | indicateurs de fonctionnalités, vides dans la cage (`data.cline.bot` injoignable) |

Exemple réel de `providers.json`, produit par `configurer.sh` avec des valeurs factices (clé remplacée) :

```json
{
  "version": 1,
  "lastUsedProvider": "openai-compatible",
  "modes": {},
  "providers": {
    "openai-compatible": {
      "settings": {
        "provider": "openai-compatible",
        "apiKey": "<CLE>",
        "model": "essai",
        "baseUrl": "http://127.0.0.1:4100/v1"
      },
      "updatedAt": "2026-11-27T08:54:02.746Z",
      "tokenSource": "manual"
    }
  }
}
```

Autres emplacements reconnus par Cline, inutilisés par le banc ([config](https://docs.cline.bot/getting-started/config.md), consulté le 27/11/2026) : `data/settings/global-settings.json` (réglages globaux), `data/settings/cline_mcp_settings.json` (serveurs MCP), dossiers `rules/`, `skills/`, `hooks/`, `agents/`, `plugins/` sous `~/.cline/` ou `.cline/` du projet ; variables `CLINE_DIR` (remplace `~/.cline`) et `CLINE_DATA_DIR` (remplace `~/.cline/data`). Le dossier personnel de l'essai part vide : aucune règle ni compétence n'y est installée.

## 4. Changer de modèle ou de portail sans toucher au harnais

Le harnais ne connaît que le relais du banc. Le choix du fournisseur (OpenRouter ou portail compatible OpenAI), de son adresse et de sa clé se fait hors du harnais :

1. Modifier `banc-essai/modele.env` (`BANC_FOURNISSEUR`, `BANC_MODELE_FOURNISSEUR`, `BANC_MODELE`…) et, pour un portail, `PORTAIL_URL` et `PORTAIL_CLE` dans `.env` ([modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md)).
2. `banc-essai/traces/demarrer.sh` (le relais relit sa configuration).
3. Lancer l'essai : `configurer.sh` reprend le nouveau `BANC_MODELE`, avec une clé neuve.

L'adresse et la clé du portail n'entrent jamais dans la cage (sonde de la cage : `banc-essai/resultats/piag-sonde-portail/`, journal du 27/11/2026). Cline n'a pas été essayé par le relais branché sur un portail ; seul le chemin harnais-relais, identique dans les deux cas, l'a été.

## 5. Autonomie, télémétrie, mise à jour automatique et réseau

### Autonomie : `-y`

`lancer.sh` lance `cline --json -y`. D'après l'aide de la 3.0.74 et son README :

| Point | Effet de `-y` (`--yolo`) | Source |
|---|---|---|
| Approbations | aucune demande : les outils sont approuvés automatiquement | `cline --help` : « Auto-approve a limited tool set for unsupervised runs (benchmarks, CI). DANGEROUS: use only in sandboxed environments. » |
| Fin de tâche | outil `submit_and_exit` activé : l'agent déclare la fin et la commande se termine | README 3.0.74, tableau des options |
| Sous-agents et équipes | outils de sous-agents (`spawn_agent`) et d'équipe désactivés par défaut | README 3.0.74 ; confirmé sur le banc : `"enable_spawn": false`, `"enable_teams": false` dans le résumé de session de l'essai jouet |
| Commandes du shell | aucune liste d'autorisation ou d'interdiction : « The CLI has no allow or deny list for shell commands » ; un point d'accroche `PreToolUse` est le seul moyen de bloquer | [CLI reference](https://docs.cline.bot/cline-cli/cli-reference.md), consulté le 27/11/2026 |

La cage borne ce que les outils peuvent toucher : écriture dans `/travail`, `/home/banc` et `/tmp` seulement, réseau limité au relais, à l'API de soumission et au filtre ([cage](../../../banc-essai/cage/README.md)). Sans cage, `-y` donne au modèle les droits de l'utilisateur sur tout le poste.

### Sorties réseau propres à Cline

| Sortie | Origine | Dans la cage | Pour la couper (non appliqué sur le banc) |
|---|---|---|---|
| `registry.npmjs.org` | mise à jour automatique : `npm update --global cline --tag latest`, lancé à chaque commande (journal de npm relevé le 27/11/2026) | refusée par le filtre (2 demandes sur l'essai jouet) ; de toute façon, `/opt/harnais` est en lecture seule | `CLINE_NO_AUTO_UPDATE=1` : vérifié le 27/11/2026, aucun appel à npm avec la variable, un appel sans elle. Le réglage `autoUpdateEnabled` de `global-settings.json` existe aussi dans le schéma de la 3.0.74 (lecture du binaire), effet non vérifié sur le banc |
| `data.cline.bot` | télémétrie et indicateurs de fonctionnalités (hôte du client PostHog dans le binaire) ; la télémétrie est active par défaut dans la CLI | refusée par le filtre (1 demande sur l'essai jouet) | `"telemetryOptOut": true` dans `~/.cline/data/settings/global-settings.json` ([télémétrie](https://docs.cline.bot/enterprise-solutions/monitoring/telemetry.md), consulté le 27/11/2026 ; clé présente dans le binaire 3.0.74) ; non vérifié sur le banc. La même page cite `DO_NOT_TRACK=1` et `CLINE_TELEMETRY_DISABLED=1` : `CLINE_TELEMETRY_DISABLED` est absent du binaire 3.0.74, donc probablement sans effet sur cette version |

D'après la page de télémétrie, celle-ci ne contient ni code, ni contenu de fichiers, ni consignes, hors fournisseurs Cline et ClinePass (non utilisés ici). Sur un poste d'entreprise hors cage, couper les deux sorties est recommandé : `CLINE_NO_AUTO_UPDATE=1` dans l'environnement, et `global-settings.json` écrit avant le premier lancement.

## 6. Où est la clé, et pourquoi c'est acceptable dans le banc

La clé du modèle se trouve, pendant et après l'essai, en clair dans `~/banc-espaces/<essai>/maison/.cline/data/settings/providers.json` (droits `600`). Elle passe aussi en argument de la commande `cline auth` (`-k`), visible un court instant dans la liste des processus de l'utilisateur.

Acceptable sur le banc parce que :

| Protection | Preuve |
|---|---|
| ce n'est pas la clé du fournisseur mais une clé virtuelle du relais, propre à l'essai, limitée au modèle du banc, aux routes d'appel du modèle et à un plafond de dépense (`BANC_BUDGET_ESSAI`, 2 $) | [`banc-essai/traces/README.md`](../../../banc-essai/traces/README.md), `banc-essai/modele.env` |
| la clé est supprimée du relais dès la sortie du harnais : la copie de `providers.json` devient inutilisable | `banc-essai/cage/lancer.sh` (`cles.py --supprimer`) |
| le dossier personnel de l'essai est hors du dépôt (`~/banc-espaces/`) : il n'est jamais commité | `banc-essai/cage/lancer.sh` (`MAISON`) |
| les résultats copiés dans le dépôt sont passés au masque des chaînes qui ressemblent à une clé | `banc-essai/cage/masquer.py`, appelé par `lancer.sh` |

À surveiller hors du banc :

- Cline branché directement sur un portail (sans relais) écrirait la vraie clé du portail en clair dans `~/.cline/data/settings/providers.json`, sans expiration ; lisible par tout programme lancé par le même utilisateur, y compris les commandes que l'agent exécute.
- Le dossier `~/.cline` persiste d'une tâche à l'autre : il garde clé, sessions complètes (`*.messages.json`, qui recopient le texte des documents lus) et journaux. Sur des données d'entreprise, le traiter comme les données elles-mêmes.
- La clé passée par `-k` apparaît dans la liste des processus ; `cline auth` sans argument (saisie interactive) l'évite.
- `~/banc-espaces/<essai>/maison/` reste sur le disque après l'essai : le supprimer après un essai goldset (sessions avec le texte des documents).

## 7. Fenêtre de contexte (piste, non appliquée)

Cline ne lit pas `BANC_CONTEXTE` et `cline auth` n'a pas d'option pour la fenêtre de contexte (`cline auth --help`). Pour un modèle inconnu de Cline, il ignore donc que le relais annonce 1 000 000 jetons ; c'est la compaction (`--compaction agentic`, par défaut) qui dépend de cette valeur.

| Source | Ce qu'elle dit |
|---|---|
| [OpenAI Compatible](https://docs.cline.bot/provider-config/openai-compatible.md), consulté le 27/11/2026 | dans le panneau de réglages (extension), « Model Configuration » permet de régler « Max Output Tokens », « Context Window size », « Image Support », prix d'entrée et de sortie ; rien sur la CLI |
| [Auto Compact](https://docs.cline.bot/features/auto-compact.md), consulté le 27/11/2026 | le résumé se déclenche à l'approche de la limite de la fenêtre de contexte du modèle |
| schéma des réglages de fournisseur du binaire 3.0.74 (lecture par `grep -a`) | les réglages d'un fournisseur acceptent `contextWindow`, `maxTokens`, `headers`, `timeout` et `capabilities` (`vision`, `prompt-cache`, `tools`…), à côté de `apiKey`, `model` et `baseUrl` |

Piste : après `cline auth`, ajouter `"contextWindow": <BANC_CONTEXTE>` et `"maxTokens": <BANC_SORTIE_MAX>` (et `"capabilities": ["vision", "tools", "streaming"]` si `BANC_VISION=1`) dans `providers.openai-compatible.settings` de `providers.json`. Non documenté pour la CLI, non vérifié sur le banc : à essayer, puis à contrôler dans la trace (pas de compaction prématurée) avant de modifier `configurer.sh`. Le champ `headers` pourrait aussi servir à un portail qui attend la clé dans un autre en-tête, mais sur le banc c'est le relais, pas Cline, qui parle au portail.
