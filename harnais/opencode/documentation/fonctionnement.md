# OpenCode : fonctionnement, constats, dépannage

[Retour à la page d'entrée](../README.md)

Les capacités (section 1) viennent de la documentation officielle de la version installée et de relevés sans appel au modèle ; les constats (section 2) viennent des essais de mise au point du banc. Les deux sont séparés : une capacité présente n'a pas forcément servi pendant un essai.

Sources externes, toutes consultées le 27/11/2026, pages de documentation du dépôt officiel au tag de la version installée :

| Repère | Page |
|---|---|
| [agents] | <https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/agents.mdx> |
| [cli] | <https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/cli.mdx> |
| [config] | <https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/config.mdx> |
| [network] | <https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/network.mdx> |
| [permissions] | <https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/permissions.mdx> |
| [tools] | <https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/tools.mdx> |
| [troubleshooting] | <https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/troubleshooting.mdx> |

Relevés locaux (binaire 1.19.6, dossier personnel jetable, réseau coupé par `bwrap --unshare-net`, aucun appel au modèle) : `opencode --help`, `opencode run --help`, `opencode agent list`, `opencode debug agent build`, `opencode debug paths`.

## 1. Capacités

| Capacité | Présente | Sur le banc | Source |
|---|---|---|---|
| Mode sans interaction | oui : `opencode run [message]` | utilisé par `lancer.sh` | [cli], section run |
| Trace structurée | oui : `--format json` (événements JSON) | utilisée : `harnais/stdout.log` | [cli], section run |
| Interface plein écran, serveur (`serve`), interface web (`web`), protocole ACP | oui | non utilisés | `opencode --help` ; [cli] |
| Agent principal `build` (tous les outils) | oui, agent par défaut | utilisé (`"agent": "build"` dans les sessions exportées) | [agents], section Use build |
| Mode plan (agent `plan` : modifications et commandes soumises à confirmation) | oui, en interactif | refusé : permissions `plan_enter` et `plan_exit` à `deny` dans l'agent `build` | [agents], section Use plan ; `opencode agent list` |
| Sous-agents par l'outil `task` | oui : `general` (tous outils sauf liste de tâches), `explore` (lecture seule) ; `scout` décrit par la documentation mais absent de `opencode agent list` (réglage expérimental `OPENCODE_EXPERIMENTAL_SCOUT` dans [cli]) | outil `task` présent dans l'agent `build` ; jamais appelé lors des essais de mise au point | [agents], sections Subagents et Built-in ; `opencode debug agent build` |
| Profondeur des sous-agents | `subagent_depth`, 1 par défaut (un sous-agent ne lance pas d'autre sous-agent) | valeur par défaut | [config], section Subagent depth |
| Liste de tâches | oui : outil `todowrite` (désactivé pour les sous-agents) | présent dans l'agent `build` ; jamais appelé lors des essais de mise au point | [tools], section todowrite |
| Compaction du contexte | oui : automatique quand le contexte est plein (`compaction.auto`, vrai par défaut ; `compaction.prune`, `compaction.reserved`), agent caché `compaction` ; coupure par `OPENCODE_DISABLE_AUTOCOMPACT` | réglages par défaut ; seuil tiré de `limit.context` (`BANC_CONTEXTE`, 128000 par défaut dans `modele.env`) ; aucune compaction relevée lors des essais de mise au point, faits avec une fenêtre déclarée bien plus grande ; avec une fenêtre de 128 000 jetons, compaction possible sur une tâche longue (non vérifié) | [config], section Compaction ; [agents], section Use compaction ; [cli], Environment variables |
| Outils de fichiers et de commandes | `bash`, `read`, `glob`, `grep`, `edit`, `write`, `apply_patch`, `skill` | `build` relevé avec `bash`, `read`, `glob`, `grep`, `edit`, `write`, `task`, `todowrite`, `skill`, `question`, `webfetch` | [tools], section Built-in ; `opencode debug agent build` |
| Lecture d'images | oui : `read` sur une image l'envoie au modèle si le modèle déclare l'entrée image ; images réduites au-delà de 2000 x 2000 pixels | utilisée lors des essais de mise au point avec un modèle à vision : pages rendues en PNG puis lues ; désactivée par `BANC_VISION=0` (valeur par défaut de `modele.env`) | [config], section Image attachments ; `configurer.sh` (`modalities`) |
| Lecture de pages web | outil `webfetch` | refusé (`deny`) | [tools] ; `configurer.sh` |
| Recherche web | outil `websearch`, seulement avec le fournisseur OpenCode ou `OPENCODE_ENABLE_EXA` / `OPENCODE_ENABLE_PARALLEL` | absent | [tools], section websearch |
| Questions à l'utilisateur | outil `question` | refusé (`deny`) dans `build` | [tools] ; `opencode agent list` |
| Outil LSP | expérimental (`OPENCODE_EXPERIMENTAL_LSP_TOOL`) | absent ; journal : « all LSPs are disabled » | [tools], section lsp ; `harnais/stderr.log` des essais |
| Permissions par outil et par motif | `allow`, `ask`, `deny` ; `--auto` approuve les `ask` | voir [configuration.md](configuration.md), section 5 | [permissions] |
| Plafond d'itérations d'un agent | option `steps` ; sans elle, l'agent continue jusqu'à ce que le modèle s'arrête | non posé : seul le garde-fou de durée de la cage borne l'essai | [agents], section Max steps |
| Délais d'attente des requêtes | `timeout`, `headerTimeout`, `chunkTimeout` (300 000 ms par défaut chacun) dans les options du fournisseur | valeurs par défaut | [config], section Models |
| Reprise d'une session | `--continue`, `--session`, `--fork` | non utilisée | [cli], section run |
| Export et import de session | `opencode export <id>` (option `--sanitize`), `opencode import` | export utilisé par `lancer.sh`, sans `--sanitize` | [cli] ; `opencode export --help` |
| Serveurs MCP, extensions, compétences | oui (`mcp`, `plugin`, outil `skill`) | aucun déclaré ; l'installation du paquet d'extensions par défaut échoue (registre npm refusé) | [config] ; `stderr.log` des essais |
| Mandataire et autorité interne | `HTTPS_PROXY`, `NO_PROXY`, `NODE_EXTRA_CA_CERTS` | fournis par la cage (sauf `NODE_EXTRA_CA_CERTS`) | [network] ; [installation.md](installation.md), section 5 |
| Fichiers de configuration | fusion de : configuration distante, globale (`~/.config/opencode/opencode.json`), `OPENCODE_CONFIG`, projet (`opencode.json`), dossiers `.opencode`, `OPENCODE_CONFIG_CONTENT`, configuration gérée | seule la configuration globale du dossier personnel de l'essai existe | [config], section Precedence order |
| Journaux et données | `~/.local/share/opencode/` (`log/`, données des sessions) ; `~/.cache/opencode/` | dans `~/banc-espaces/<essai>/maison/` ; la version 1.19.6 y range ses sessions dans `opencode.db` (relevé), la documentation parle de `project/` | [troubleshooting], sections Logs et Storage ; `opencode debug paths` |

## 2. Constats sur le banc

Comportements constatés lors des essais de mise au point du banc (OpenCode 1.19.6, recettes de correction de code et d'extraction de valeurs dans des PDF). Ils décrivent le harnais, pas un modèle ni un portail particuliers.

| Constat | Où le vérifier dans un essai |
|---|---|
| Fin normale (code de retour 0) sur toutes les recettes essayées, sans intervention | `essai.json` (code de retour) |
| L'agent travaille surtout avec `bash` et `read` ; `glob`, `grep` et `edit` servent ponctuellement | décompte des outils de `harnais/stdout.log` ([lancement.md](lancement.md), section 4.1) |
| Sur une tâche d'extraction, la plupart des appels au modèle viennent du programme écrit par l'agent, pas d'OpenCode : OpenCode déclare ses outils à chaque appel de l'agent, alors que l'appel de titre de session (`agent=title` dans `stderr.log`) et les appels du programme produit n'en déclarent pas | champ `outils` de `traces/appels.jsonl` |
| Lecture des PDF par la vision : pages rendues en PNG (PyMuPDF) dans `/tmp`, puis lues par l'outil `read` (modèle déclaré avec vision) | `filePath` des appels à `read` dans `harnais/stdout.log` |
| Clé de l'essai affichée par l'agent dans sa trace (variables d'environnement) ; masquée depuis par `banc-essai/cage/masquer.py` | `harnais/stdout.log` |
| Catalogue `models.opencode.ai` et paquet `@opencode-ai/plugin` refusés à chaque démarrage, sans effet | `traces/reseau.jsonl` et `essai.json` (`hotes_refuses`) |
| Aucune compaction du contexte relevée, y compris sur des essais de plus d'une heure, avec une fenêtre déclarée bien plus grande que 128 000 jetons | absence de message `compact` dans `harnais/stderr.log` |
| Sous-agents (`task`) et liste de tâches (`todowrite`) jamais utilisés | décompte des outils de `harnais/stdout.log` |
| Erreurs `Cannot connect to API: ECONNRESET` vers `http://127.0.0.1:4100/v1/chat/completions` en fin de trace lors d'un essai de démonstration, cause non établie | événements `error` de `harnais/stdout.log` (voir section 4) |

## 3. Essais non faits

| Situation | État |
|---|---|
| Recette `goldset` | aucun essai d'OpenCode |
| Relais branché sur un portail compatible OpenAI | vérifié avec la sonde de la cage (42 vérifications, 41 si `BANC_VISION=0`), pas avec OpenCode ; la configuration d'OpenCode ne dépend pas du portail (adresse du relais) |
| Poste d'entreprise avec mandataire et inspection TLS | non essayé |
| Modèle à fenêtre de contexte de 128 000 jetons ou moins (compaction) | non essayé |

## 4. Problèmes connus et dépannage

| Symptôme | Cause | Correction |
|---|---|---|
| Essai sans aucun appel au modèle, trace vide, harnais qui ne rend pas la main | `opencode run` attend la fin de l'entrée standard quand elle reste ouverte (constaté lors des essais de mise au point : essai bloqué sans aucun appel au modèle) | entrée fermée : `< /dev/null` (fait par `banc-essai/cage/lancer.sh`) ; à ajouter à toute commande lancée à la main |
| Fournisseur `banc` absent de `opencode debug config`, ou `ProviderModelNotFoundError` | configuration écrite avec la syntaxe de la version 2 (`providers`), ignorée par la 1.19.6 ; ou modèle mal référencé (forme `<fournisseur>/<modèle>`) | garder la syntaxe `provider` / `npm` / `options` de `configurer.sh` ; contrôle : [installation.md](installation.md), section 6 ; [troubleshooting], section Model not available |
| `configurer.sh: … BANC_MODELE: parameter null or not set` | variables absentes (script lancé hors de la cage) | exporter `BANC_MODELE_URL` et `BANC_MODELE` ([lancement.md](lancement.md), section 7) |
| `Failed to fetch models.dev` et `background dependency install failed` dans `stderr.log` | demandes refusées par la cage | rien à faire : sans effet sur l'essai |
| `stream error … Cannot connect to API: ECONNRESET` ou `ECONNREFUSED`, événement `error` dans `stdout.log` | relais du modèle injoignable, arrêté ou redémarré pendant l'essai | `curl -fs http://127.0.0.1:4100/health/liveliness` ; `banc-essai/traces/demarrer.sh` ; relancer l'essai |
| Réponse 401 ou clé refusée | `BANC_CLE_MODELE` vide (une variable absente devient une chaîne vide, [config], section Env vars) ou clé déjà supprimée | vérifier `banc-essai/traces/secrets/cle-<alias>.env` ; recréer la clé avec `banc-essai/traces/cles.py <alias>` |
| Réponse 400 « modèle inconnu » ou refusé par la clé | `BANC_MODELE` changé dans `modele.env` sans redémarrer le relais | `banc-essai/traces/demarrer.sh`, puis nouvelle clé |
| Appels en échec en série en cours d'essai | plafond de dépense de la clé atteint (`max_budget` posé par `banc-essai/traces/cles.py` d'après `BANC_BUDGET_ESSAI` : 40 dans `modele.env`, soit 40 millions de jetons avec les prix conventionnels de 1 ; 2 si la variable est absente ; code d'erreur renvoyé par le relais non relevé), ou limite de débit du portail (429) | `rapport.md` (appels échoués, appels 429, dépense de la clé) ; ajuster `BANC_BUDGET_ESSAI` dans `modele.env` |
| Le modèle ne reçoit pas les images | `BANC_VISION=0`, ou modèle sans vision chez le portail | `modele.env` ; vérificateur du portail ([modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md)) |
| Coût nul dans les sessions OpenCode | prix non déclarés à OpenCode | lire le coût dans `essai.json` (relais) |
| Code de retour 124, « garde-fou de durée atteint » | durée de l'essai supérieure à `--duree` | relancer avec `--duree` plus grand |
| Requête longue interrompue au bout de 5 min (non observé) | délais `headerTimeout` ou `chunkTimeout` de 300 000 ms par défaut, possibles avec un portail lent | ajouter `timeout`, `chunkTimeout` aux `options` du fournisseur dans `configurer.sh` ([config], section Models) ; non vérifié sur le banc |
| `installer.sh` : `sha256sum: WARNING: 1 computed checksum did NOT match` | archive corrompue ou altérée | relancer ; ne jamais retirer la vérification |
| `installer.sh` : erreur curl de connexion ou de certificat | mandataire ou autorité interne non déclarés | `HTTPS_PROXY`, `CURL_CA_BUNDLE` ([installation.md](installation.md), section 5) |
| Outils `glob` ou `grep` en échec sur un poste d'entreprise (non observé) | téléchargement de ripgrep depuis GitHub bloqué par le mandataire de l'entreprise | autoriser `github.com` et `release-assets.githubusercontent.com` ; non vérifié sur le banc |
| `un autre essai tourne déjà` | verrou du lanceur | attendre la fin de l'essai en cours |
| Problème non identifié | | reproduire à la main ([lancement.md](lancement.md), section 7) en ajoutant `--print-logs --log-level DEBUG` à `opencode run` ; lire `~/banc-espaces/<essai>/maison/.local/share/opencode/log/` ; vider `~/.cache/opencode` du dossier personnel concerné ([troubleshooting], sections Logs et AI_APICallError) |

## 5. Limites

| Limite | Conséquence |
|---|---|
| Version figée 1.19.6 ; dernière version publiée : 2.4.2 du 26/11/2026 ([versions](https://github.com/anomalyco/opencode/releases), consulté le 27/11/2026) | la documentation du site opencode.ai décrit la version 2 ; se reporter aux pages du tag v1.19.6 |
| Binaire Linux x86-64 glibc seulement dans `installer.sh` | autre architecture : changer `ARCHIVE` et l'empreinte (non essayé) |
| Prix du modèle non transmis à OpenCode | coûts affichés par OpenCode nuls ; seul le coût du relais fait foi |
| Mode plan et questions refusés en mode sans interaction | l'agent travaille seul du début à la fin, sans étape de validation |
| Aucun plafond d'itérations | seuls le garde-fou de durée et le plafond de dépense de la clé arrêtent un agent qui boucle |
| Sessions exportées et journal interne gardés dans `~/banc-espaces/<essai>/maison/`, hors des résultats | à conserver à part si le dossier des espaces est nettoyé |
| Demandes réseau inutiles à chaque démarrage (`models.opencode.ai`, `registry.npmjs.org`) | refusées par la cage ; hors de la cage, elles sortiraient par le réseau du poste |
| Clé de l'essai dans l'environnement de l'agent | l'agent peut l'afficher ; masquage après coup et suppression de la clé en fin d'essai |
