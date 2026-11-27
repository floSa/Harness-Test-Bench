# OpenCode : fonctionnement, constats, dépannage

[Retour à la page d'entrée](../README.md)

Les capacités (section 1) viennent de la documentation officielle de la version installée et de relevés sans appel au modèle ; les constats (section 2) viennent des essais du banc. Les deux sont séparés : une capacité présente n'a pas forcément servi pendant un essai.

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
| Agent principal `build` (tous les outils) | oui, agent par défaut | utilisé (`"agent": "build"` dans la session exportée de `c1-01`) | [agents], section Use build |
| Mode plan (agent `plan` : modifications et commandes soumises à confirmation) | oui, en interactif | refusé : permissions `plan_enter` et `plan_exit` à `deny` dans l'agent `build` | [agents], section Use plan ; `opencode agent list` |
| Sous-agents par l'outil `task` | oui : `general` (tous outils sauf liste de tâches), `explore` (lecture seule) ; `scout` décrit par la documentation mais absent de `opencode agent list` (réglage expérimental `OPENCODE_EXPERIMENTAL_SCOUT` dans [cli]) | outil `task` présent dans l'agent `build` ; jamais appelé dans les essais | [agents], sections Subagents et Built-in ; `opencode debug agent build` |
| Profondeur des sous-agents | `subagent_depth`, 1 par défaut (un sous-agent ne lance pas d'autre sous-agent) | valeur par défaut | [config], section Subagent depth |
| Liste de tâches | oui : outil `todowrite` (désactivé pour les sous-agents) | présent dans l'agent `build` ; jamais appelé dans les essais | [tools], section todowrite |
| Compaction du contexte | oui : automatique quand le contexte est plein (`compaction.auto`, vrai par défaut ; `compaction.prune`, `compaction.reserved`), agent caché `compaction` ; coupure par `OPENCODE_DISABLE_AUTOCOMPACT` | réglages par défaut ; seuil tiré de `limit.context` (`BANC_CONTEXTE`) ; aucune compaction relevée dans les journaux des essais | [config], section Compaction ; [agents], section Use compaction ; [cli], Environment variables |
| Outils de fichiers et de commandes | `bash`, `read`, `glob`, `grep`, `edit`, `write`, `apply_patch`, `skill` | `build` relevé avec `bash`, `read`, `glob`, `grep`, `edit`, `write`, `task`, `todowrite`, `skill`, `question`, `webfetch` | [tools], section Built-in ; `opencode debug agent build` |
| Lecture d'images | oui : `read` sur une image l'envoie au modèle si le modèle déclare l'entrée image ; images réduites au-delà de 2000 x 2000 pixels | utilisée : pages rendues en PNG puis lues (`c1-01`) | [config], section Image attachments ; `configurer.sh` (`modalities`) |
| Lecture de pages web | outil `webfetch` | refusé (`deny`) | [tools] ; `configurer.sh` |
| Recherche web | outil `websearch`, seulement avec le fournisseur OpenCode ou `OPENCODE_ENABLE_EXA` / `OPENCODE_ENABLE_PARALLEL` | absent | [tools], section websearch |
| Questions à l'utilisateur | outil `question` | refusé (`deny`) dans `build` | [tools] ; `opencode agent list` |
| Outil LSP | expérimental (`OPENCODE_EXPERIMENTAL_LSP_TOOL`) | absent ; journal : « all LSPs are disabled » | [tools], section lsp ; `opencode-jouet-3/harnais/stderr.log` |
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

### 2.1 Essais réels

Modèle : `deepseek-v4.1-flash` (`openrouter/deepseek/deepseek-v4.1-flash-1017`), OpenCode 1.19.6. Chiffres tirés de `essai.json` et `rapport.md` de chaque dossier `banc-essai/resultats/<essai>/` ; part du cache = jetons lus dans le cache / jetons d'entrée.

| Critère | `opencode-jouet-1` | `opencode-jouet-2` | `opencode-jouet-3` | `c1-01-opencode-sans-aide` | `c2-01-opencode-dossiers` |
|---|---|---|---|---|---|
| Date | 19/11/2026 22 h 11 | 19/11/2026 22 h 32 | 19/11/2026 22 h 42 | 19/11/2026 23 h 33 | 24/11/2026 6 h 18 |
| Recette | `jouet` | `jouet` | `jouet` | `sans-aide` | `dossiers` |
| Durée | 21,7 s | 20,5 s | 30,4 s | 1 446 s (24 min) | 3 721 s (62 min) |
| Code de retour du harnais | 0 | 0 | 0 | 0 | 0 |
| Score final (test caché) | 100 % (10 cas sur 10) | 100 % (10 sur 10) | 100 % (10 sur 10) | 100 % | 99,4 % (9 dossiers justes sur 12) |
| Soumissions acceptées | 1 | 1 | 1 | 1 | 4 (98,5 ; 98,5 ; 98,7 ; 99,4 %) |
| Score de validation annoncé | 100 % | 100 % | 100 % | 99,8 % | 99,0 % |
| Score à la relance du workflow | | | | 99,3 % (10 documents) | 99,4 % (6 dossiers justes sur 8) |
| Relance : durée et coût par document | | | | 4,68 s ; 0,001046 $ | 12,29 s ; 0,005644 $ |
| Taux d'invention | | | | 0 % | 0 % |
| Appels au modèle | 11 | 11 | 12 | 286 | 691 |
| dont appels qui déclarent des outils (agent) | 10 | 10 | 11 | 84 | 164 |
| dont appels sans outil (titre de session et programme écrit par l'agent) | 1 | 1 | 1 | 202 | 527 |
| Appels échoués | 0 | 0 | 0 | 1 (erreur 529 du fournisseur) | 0 |
| Appels avec image | 0 | 0 | 0 | 271 | 672 |
| Jetons d'entrée | 96 320 | 90 734 | 104 545 | 8 716 606 | 28 835 629 |
| Part lue dans le cache | 89,7 % | 86,5 % | 90,1 % | 82,1 % | 86,5 % |
| Jetons de sortie | 1 351 | 1 519 | 1 504 | 702 773 | 1 993 926 |
| Coût (relais, égal à la dépense de la clé) | 0,001161 $ | 0,001305 $ | 0,001251 $ | 0,310235 $ | 0,867609 $ |
| Outils appelés par l'agent (`stdout.log`) | `read` 5, `bash` 6, `edit` 1 | `read` 4, `bash` 6, `edit` 1 | `glob` 1, `read` 4, `bash` 6, `edit` 1 | `bash` 64, `read` 19 | `bash` 144, `read` 24 |
| Pic de mémoire | | | 0,62 Go | 1,32 Go | 2,38 Go |
| Pic de disque | | | 35 Mo | 565 Mo | 759 Mo |
| Téléchargements | | | 4,2 Mo | 118 Mo | 143 Mo |
| Demandes réseau refusées | 5 | 5 | 5 | 5 | 8 |

La répartition « avec ou sans outils » est déduite du champ `outils` de `traces/appels.jsonl` : OpenCode déclare ses outils à chaque appel de l'agent ; l'appel de titre (`agent=title` dans `stderr.log`) et les appels du programme d'extraction écrit par l'agent n'en déclarent pas. Le nombre d'appels d'un essai d'extraction compte donc surtout le travail du programme produit, pas celui d'OpenCode.

Dossier `banc-essai/resultats/manuel-opencode-jouet/` : essai de démonstration lié aux captures du manuel (commit `d1b49b1`), sans `essai.json` ni rapport ; sa trace se termine par des erreurs `Cannot connect to API: ECONNRESET` vers `http://127.0.0.1:4100/v1/chat/completions`. Cause non établie dans le journal.

### 2.2 Comportements relevés

| Constat | Preuve |
|---|---|
| Lecture des PDF par la vision : pages rendues en PNG (PyMuPDF) dans `/tmp`, puis lues par l'outil `read` | `c1-01-opencode-sans-aide/harnais/stdout.log` (`filePath":"/tmp/doc-001_p1.png`) ; `documentations/journal.md`, entrée du 19-20/11/2026 |
| Règles de recoupement des dossiers appliquées sans erreur (0 jumeau, 0 rapport annulé, 0 version remplacée retenus à tort ; 6 rectificatifs sur 6) | `c2-01-opencode-dossiers/rapport.md` ; journal, entrée du 24/11/2026 |
| Clé de l'essai affichée par l'agent dans sa trace (variables d'environnement) ; masquée depuis par `banc-essai/cage/masquer.py` | journal, entrée du 19-20/11/2026 |
| Catalogue `models.opencode.ai` et paquet `@opencode-ai/plugin` refusés à chaque démarrage, sans effet | `traces/reseau.jsonl` et `essai.json` (`hotes_refuses`) des essais |
| Aucune compaction du contexte relevée, même sur 62 min | aucun message `compact` dans `c1-01` et `c2-01` `harnais/stderr.log` |
| Sous-agents et liste de tâches jamais utilisés | outils de `stdout.log` (tableau 2.1) |

## 3. Essais non faits

| Situation | État |
|---|---|
| Recettes `avec-aide` et `goldset` | aucun essai d'OpenCode |
| Relais en mode portail (portail compatible OpenAI au lieu d'OpenRouter) | vérifié avec la sonde de la cage, pas avec OpenCode (`documentations/journal.md`, entrée du 27/11/2026) ; la configuration d'OpenCode ne change pas (adresse du relais) |
| Poste d'entreprise avec mandataire et inspection TLS | non essayé |
| Modèle à petite fenêtre de contexte (compaction) | non essayé |

## 4. Problèmes connus et dépannage

| Symptôme | Cause | Correction |
|---|---|---|
| Essai sans aucun appel au modèle, trace vide, harnais qui ne rend pas la main | `opencode run` attend la fin de l'entrée standard quand elle reste ouverte (essai bloqué 17 min, journal du 19/11/2026) | entrée fermée : `< /dev/null` (fait par `banc-essai/cage/lancer.sh`) ; à ajouter à toute commande lancée à la main |
| Fournisseur `banc` absent de `opencode debug config`, ou `ProviderModelNotFoundError` | configuration écrite avec la syntaxe de la version 2 (`providers`), ignorée par la 1.19.6 ; ou modèle mal référencé (forme `<fournisseur>/<modèle>`) | garder la syntaxe `provider` / `npm` / `options` de `configurer.sh` ; contrôle : [installation.md](installation.md), section 6 ; [troubleshooting], section Model not available |
| `configurer.sh: … BANC_MODELE: parameter null or not set` | variables absentes (script lancé hors de la cage) | exporter `BANC_MODELE_URL` et `BANC_MODELE` ([lancement.md](lancement.md), section 7) |
| `Failed to fetch models.dev` et `background dependency install failed` dans `stderr.log` | demandes refusées par la cage | rien à faire : sans effet sur l'essai |
| `stream error … Cannot connect to API: ECONNRESET` ou `ECONNREFUSED`, événement `error` dans `stdout.log` | relais du modèle injoignable, arrêté ou redémarré pendant l'essai | `curl -fs http://127.0.0.1:4100/health/liveliness` ; `banc-essai/traces/demarrer.sh` ; relancer l'essai |
| Réponse 401 ou clé refusée | `BANC_CLE_MODELE` vide (une variable absente devient une chaîne vide, [config], section Env vars) ou clé déjà supprimée | vérifier `banc-essai/traces/secrets/cle-<alias>.env` ; recréer la clé avec `banc-essai/traces/cles.py <alias>` |
| Réponse 400 « modèle inconnu » ou refusé par la clé | `BANC_MODELE` changé dans `modele.env` sans redémarrer le relais | `banc-essai/traces/demarrer.sh`, puis nouvelle clé |
| Appels en échec en série en cours d'essai | plafond de dépense de la clé atteint (`max_budget` posé par `banc-essai/traces/cles.py` d'après `BANC_BUDGET_ESSAI`, 2 $ par défaut ; code d'erreur renvoyé par le relais non relevé), ou limite de débit du fournisseur (429) | `rapport.md` (appels échoués, appels 429, dépense de la clé) ; ajuster `BANC_BUDGET_ESSAI` dans `modele.env` |
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
