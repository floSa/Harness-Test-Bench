# Fonctionnement de Goose

Retour : [page d'entrée du harnais](../README.md). Pages voisines : [installation](installation.md), [configuration](configuration.md), [lancement](lancement.md).

Cette page sépare ce que Goose sait faire (capacités, section 1) de ce qu'il a fait sur le banc (résultats, section 2).

## 1. Capacités du harnais

Sources externes consultées le 27/11/2026. « Banc » signale ce qui a été constaté dans la version 1.60.1 installée ; le reste vient de la documentation officielle et n'est pas vérifié sur le banc.

| Capacité | Présente | Détail | Source |
|---|---|---|---|
| Mode sans interaction | oui | `goose run -t "<texte>"` ou `-i <fichier>` ; `--no-session`, `--max-turns` | `goose run --help` (banc) ; [mode « headless »](https://goose-docs.ai/docs/tutorials/headless-goose) |
| Trace structurée | oui | `--output-format json` (en fin de session) ou `stream-json` (au fil de l'eau) | `goose run --help` (banc) ; [commandes de la CLI](https://goose-docs.ai/docs/guides/goose-cli-commands) |
| Fournisseur compatible OpenAI | oui | fournisseur `openai` avec `OPENAI_HOST`, `OPENAI_BASE_PATH` ; fournisseur `litellm` distinct (`LITELLM_HOST`), non utilisé | [fournisseurs](https://goose-docs.ai/docs/getting-started/providers) ; banc : [configuration](configuration.md) |
| Fournisseurs personnalisés | oui | fichiers JSON dans `~/.config/goose/custom_providers/` (adresse, en-têtes, modèles avec `context_limit`, prix) | [fournisseurs](https://goose-docs.ai/docs/getting-started/providers) |
| Fichiers de configuration | oui | `~/.config/goose/config.yaml` (réglages, extensions), `secrets.yaml` (clés en clair si pas de trousseau), `permission.yaml` ; variables d'environnement prioritaires ; clés ignorées dans `config.yaml` | [fichiers de configuration](https://goose-docs.ai/docs/guides/config-files) |
| Modes d'autonomie | oui | `auto` (défaut), `approve`, `smart_approve`, `chat` (commande `/mode`) | [modes de permission](https://goose-docs.ai/docs/guides/managing-tools/goose-permissions) ; [commandes de la CLI](https://goose-docs.ai/docs/guides/goose-cli-commands) |
| Mode plan | non trouvé dans la 1.60.1 | la documentation a décrit une commande `/plan` et des variables `GOOSE_PLANNER_PROVIDER`, `GOOSE_PLANNER_MODEL` (résultats de recherche) ; la page « creating plans » est vide au 27/11/2026, absente des sources de la documentation sur la branche `main`, et les chaînes `GOOSE_PLANNER` sont absentes du binaire 1.60.1 (`strings`, banc). Présence réelle : non vérifié sur le banc | [page « creating plans »](https://goose-docs.ai/docs/guides/context-engineering/creating-plans) ; dépôt [aaif-goose/goose](https://github.com/aaif-goose/goose), dossier `documentation/docs` |
| Sous-agents | oui | outil `delegate` de l'extension `summon` (activée par défaut) ; 5 sous-agents simultanés au plus (`GOOSE_MAX_CONCURRENT_SUBAGENTS`), délai de 5 min, pas de sous-agent imbriqué, désactivés en modes `approve` et `smart_approve`. Banc : `delegate` présenté au modèle, jamais appelé dans les essais | [sous-agents](https://goose-docs.ai/docs/guides/context-engineering/subagents) ; trace de `c1-02` |
| Recettes | oui | fichiers YAML ou JSON (`title`, `description`, `instructions` ou `prompt`, `extensions`, `parameters`, `settings`, `sub_recipes`, `response.json_schema` validé en fin de session, `retry`) ; sans interaction, `prompt` obligatoire ; `goose run --recipe <fichier> --params clé=valeur`. Non utilisées sur le banc | [référence des recettes](https://goose-docs.ai/docs/guides/recipes/recipe-reference) ; [mode « headless »](https://goose-docs.ai/docs/tutorials/headless-goose) ; `goose run --help` (banc) |
| Liste de tâches | oui, désactivée par défaut | extension `todo` : plan court mis à jour, montré au modèle à chaque tour, conservé à la compaction. Banc : désactivée (`goose info -v`), non activée par `lancer.sh` | [extension Todo](https://goose-docs.ai/docs/mcp/todo-mcp) |
| Compaction du contexte | oui | automatique au plus petit de `GOOSE_AUTO_COMPACT_THRESHOLD` × fenêtre (0,8) et `GOOSE_AUTO_COMPACT_TOKEN_LIMIT` (225 000) ; `/compact` en interactif ; `goose run` résume automatiquement. Banc : une compaction à 102 000 jetons par essai long | [gestion du contexte](https://goose-docs.ai/docs/guides/sessions/smart-context-management) ; trace de `c1-02` |
| Déclaration de la fenêtre de contexte | oui | `GOOSE_CONTEXT_LIMIT` (variable d'environnement seulement), ou `context_limit` d'un fournisseur personnalisé ; défaut 128 000 | [variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables) ; [configuration, section 7](configuration.md#7-fenêtre-de-contexte-piste-non-appliquée-sur-le-banc) |
| Extensions MCP | oui | serveurs MCP en `stdio` ou HTTP (`streamable_http`) : `--with-extension`, `--with-streamable-http-extension`, ou clé `extensions` de `config.yaml` ; extensions intégrées (`--with-builtin`) ; `extensionmanager` active ou désactive des extensions en cours de session | [extensions](https://goose-docs.ai/docs/getting-started/using-extensions) ; `goose run --help` (banc) |
| Compétences (skills) | oui | outil `load_skill`, activé par défaut ; commande `goose skills` | [extensions](https://goose-docs.ai/docs/getting-started/using-extensions) ; `goose --help` et trace de `c1-02` (banc) |
| Lecture d'images | oui | outil `read_image` de l'extension `developer` | trace de `c1-02` (banc) |
| Limite de tours | oui | `GOOSE_MAX_TURNS` ou `--max-turns`, défaut 1000 | [variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables) |
| Sessions | oui | base SQLite ; reprise (`--resume`) ; export Markdown, JSON, YAML ou HTML (`goose session export`) ; rapport de diagnostic (`goose session diagnostics`) | [journalisation](https://goose-docs.ai/docs/guides/logs) ; [commandes de la CLI](https://goose-docs.ai/docs/guides/goose-cli-commands) ; `goose session export --help` (banc) |
| Mandataire HTTP | oui | `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`. Banc : `HTTPS_PROXY` et `NO_PROXY` respectés | [variables d'environnement](https://goose-docs.ai/docs/guides/environment-variables) ; [configuration, section 6](configuration.md#6-télémétrie-réseau-et-extensions) |
| Télémétrie | oui, sur accord | collecte anonyme d'usage, désactivée par défaut (`GOOSE_TELEMETRY_ENABLED`) | [données d'usage](https://goose-docs.ai/docs/guides/usage-data) |
| Mise à jour intégrée | oui | `goose update` (stable ou `--canary`) | [mise à jour](https://goose-docs.ai/docs/guides/updating-goose) |
| Autres | oui | serveur ACP (`goose acp`, `goose serve`), tâches planifiées (`goose schedule`), passerelles (`goose gateway`), modèles locaux (`goose local-models`) ; non utilisés | `goose --help` (banc) |

## 2. Résultats sur le banc

Modèle des trois essais : `deepseek-v4.1-flash` (OpenRouter, `deepseek/deepseek-v4.1-flash-1017`), Goose 1.60.1, mode `auto`, extension `developer` et extensions par défaut.

| Critère | `goose-jouet-1` | `c1-02-goose-avec-aide` | `c2-02-goose-dossiers` |
|---|---|---|---|
| Date | 19/11/2026 | 19-20/11/2026 | 24/11/2026 |
| Recette | jouet | avec-aide (extraction, 15 documents au test caché) | dossiers (tâche 2, 12 dossiers au test caché) |
| Statut | terminé | terminé | arrêté volontairement avant la fin, non compté |
| Durée | 21,7 s | 1 771,9 s (29,5 min) | 7 h 16 à 8 h 45 (89 min) |
| Code de retour | 0 | 0 | |
| Appels au modèle | 8 | 299 | 764 |
| Appels échoués, dont 429 | 0, 0 | 0, 0 | |
| Appels avec image (relais) | 0 | 0 | |
| Jetons d'entrée (dont lus dans le cache) | 58 495 (46 464, 79 %) | 5 065 416 (4 294 272, 85 %) | |
| Jetons de sortie | 2 182 | 854 763 | |
| Temps dans le modèle | 19,7 s | 1 584,0 s | |
| Coût | 0,0014 $ | 0,31 $ | 0,98 $ |
| Score final (test caché) | 100 % (10 tests sur 10) | 99,6 % | F1 97,6 % (seule soumission, 8 dossiers entièrement justes sur 12) |
| Soumissions acceptées | 1 | 1 | 1 |
| Fin déclarée | oui | oui | non |
| Score de validation annoncé | 100 % | 99,5 % | |
| Taux d'invention | | 0,0 % | |
| Style de mise en page jamais vu | | 98,7 % | |
| Relance : score | | 98,7 % (10 JSON sur 10) | |
| Relance : durée et coût par document | | 19,4 s, 0,0020 $ | |
| Outils appelés (trace) | `shell` 6, `edit` 1 | `shell` 93, `write` 1, `read_image` 1 | `shell` 120, `edit` 7, `write` 2, `read_image` 1 (trace partielle) |
| Compactions du contexte | 0 | 1 (seuil 102 000 jetons) | 1 (seuil 102 000 jetons) |
| Pic de mémoire | 0,15 Go | 3,66 Go | 2,41 Go (relevé partiel) |
| Téléchargements (PyPI) | 2,0 Mo | 225 Mo | |
| Hôtes refusés | `models.dev` | `models.dev`, `mobile.events.data.microsoft.com` | `models.dev`, `mobile.events.data.microsoft.com` |

Sources : `banc-essai/resultats/goose-jouet-1/essai.json` et `rapport.md` ; `banc-essai/resultats/c1-02-goose-avec-aide/essai.json` et `rapport.md` ; [`documentations/journal.md`](../../../documentations/journal.md) (entrées du 19/11/2026 lot 4, du 19-20/11/2026 campagne 1, du 24/11/2026 essai c2-02) ; pour `c2-02`, résultats partiels hors dépôt dans `~/banc-espaces/c2-02-goose-dossiers/resultats-partiels/` (trace, `traces/memoire.json`, `traces/reseau.jsonl`, relevés le 27/11/2026). Outils et compactions comptés dans les traces `harnais/stdout.log` (méthode : [lancement, section 6](lancement.md#6-format-de-la-trace-stream-json)).

Constats :

| Constat | Détail | Preuve |
|---|---|---|
| Configuration sans interaction | aucun `goose configure` : fichier écrit plus variables d'environnement suffisent | [journal](../../../documentations/journal.md), 19/11/2026 |
| Méthode d'extraction (c1-02) | texte des PDF extrait par du code, puis lu par le modèle ; programme découpé en 8 modules ; aucun appel avec image compté par le relais | [journal](../../../documentations/journal.md), essai 2 de la campagne 1 |
| Seule clé imparfaite (c1-02) | débit, 93,3 % (14 sur 15) | `banc-essai/resultats/c1-02-goose-avec-aide/rapport.md` |
| Usage des outils | presque tout passe par `shell` ; ni `delegate` (sous-agents), ni `analyze`, ni `apps` n'ont été appelés | traces des trois essais |
| Relais et portail | Goose a réalisé une tâche à travers un relais de type portail (kit de test sécurisé, 20/11/2026) et a reçu ses réponses en flux par le relais dans un conteneur Docker (23/11/2026) | [journal](../../../documentations/journal.md) |
| Comparaison tâche 2 (incomplète) | OpenCode : F1 99,4 %, 9 dossiers justes sur 12, 691 appels, 0,87 $, 62 min ; Goose, à l'arrêt : F1 97,6 %, 8 sur 12, 764 appels, 0,98 $, 89 min, sans déclaration de fin | [journal](../../../documentations/journal.md), 24/11/2026 |

## 3. Problèmes connus et dépannage

| Symptôme | Cause | Correction |
|---|---|---|
| `sha256sum` signale une empreinte différente et `installer.sh` s'arrête | archive modifiée, téléchargement tronqué, ou page d'erreur renvoyée par un mandataire | vérifier le mandataire (`HTTPS_PROXY`) ; ne changer `SHA256` que pour une nouvelle version, avec l'empreinte publiée ([installation, section 6](installation.md#6-changer-de-version-figée)) |
| `curl: (60) SSL certificate problem` à l'installation | mandataire d'entreprise qui présente un certificat d'une autorité interne | `SSL_CERT_FILE=/chemin/autorites.pem harnais/goose/installer.sh` ([installation, section 4](installation.md#4-derrière-un-mandataire-et-un-certificat-dentreprise)) |
| `curl: (6)`, `(7)` ou `(28)` à l'installation | pas d'accès direct à Internet | `HTTPS_PROXY=http://hote:port` ; autoriser `github.com` et `release-assets.githubusercontent.com` |
| `version 'GLIBC_2.28' not found` | système trop ancien | système avec glibc 2.28 ou plus récente |
| `cannot execute binary file: Exec format error` | machine non x86_64 : le script installe toujours l'archive x86_64 | adapter `ARCHIVE` et `SHA256` (archives `aarch64` publiées) ; non vérifié sur le banc |
| `LiteLLM du banc arrêté` au lancement | relais arrêté | `banc-essai/traces/demarrer.sh` |
| `un autre essai tourne déjà` | verrou d'un essai en cours, ou d'une cage restée active | [lancement, section 8](lancement.md#8-arrêter-un-essai-proprement) |
| `BANC_MODELE: parameter null or not set` dans `stderr.log` ou au terminal | `configurer.sh` lancé hors de la cage sans les variables | les donner (exemple dans [configuration](configuration.md)) ou passer par `banc-essai/cage/lancer.sh` |
| `BANC_CLE_MODELE: parameter null or not set` | `lancer.sh` du harnais lancé sans clé (hors du lanceur du banc) | passer par `banc-essai/cage/lancer.sh` |
| Erreurs de trousseau (`keyring`, `secret service`) | pas de service de secrets dans la cage | `GOOSE_DISABLE_KEYRING=1`, déjà posé par `lancer.sh` |
| `failed to refresh remote model catalog … models.dev` dans le journal de Goose ; `models.dev` dans les hôtes refusés | catalogue de modèles injoignable depuis la cage | aucune : sans effet sur l'essai |
| `mobile.events.data.microsoft.com` dans les hôtes refusés | télémétrie d'une bibliothèque Python installée par le code de Goose (le dossier `maison/.cache/Microsoft/DeveloperTools/.onnxruntime/` apparaît dans les essais dont le code importe `onnxruntime`, pas dans la tâche jouet) ; attribution déduite, non vérifiée par capture | aucune : refusé sans effet |
| `Exceeded auto-compact threshold of 102k tokens` dans la trace | fenêtre de contexte inconnue de Goose, 128 000 jetons supposés | piste `GOOSE_CONTEXT_LIMIT` ([configuration, section 7](configuration.md#7-fenêtre-de-contexte-piste-non-appliquée-sur-le-banc)) |
| Appels au modèle en échec (401 ou refus) en cours d'essai | clé de l'essai supprimée (lanceur du banc arrêté) ou plafond `BANC_BUDGET_ESSAI` atteint | lire `traces/appels.jsonl` (champ `erreur`) ; arrêter la cage ; relancer l'essai |
| Goose tourne encore après l'arrêt du lanceur | la cage ne reçoit pas Ctrl+C (tâche de fond, session propre) | [lancement, section 8](lancement.md#8-arrêter-un-essai-proprement) |
| `json.loads` échoue sur les premières lignes de `stdout.log` | bandeau de démarrage de quatre lignes non JSON | ignorer les lignes non JSON ([lancement, section 6](lancement.md#6-format-de-la-trace-stream-json)) |
| `goose-session.json` introuvable dans les résultats | l'export est écrit dans le dossier personnel de l'essai, non collecté | `~/banc-espaces/<essai>/maison/goose-session.json` |

Pour un problème propre à Goose, la commande `goose session diagnostics` produit un rapport JSON (système, messages, configuration, journaux récents) ; il peut contenir des données sensibles ([commandes de la CLI](https://goose-docs.ai/docs/guides/goose-cli-commands), consulté le 27/11/2026). Liste officielle des problèmes connus : [known issues](https://goose-docs.ai/docs/troubleshooting/known-issues).

## 4. Limites

| Limite | Effet | Preuve |
|---|---|---|
| Capacités du modèle non transmises | `BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION` et les prix ne sont pas lus : Goose compacte à 102 000 jetons alors que le modèle en accepte 1 000 000, contrairement à OpenCode et Pi qui reçoivent ces valeurs | [`configurer.sh`](../configurer.sh), trace de `c1-02`, en-tête de [`banc-essai/modele.env`](../../../banc-essai/modele.env) |
| Extensions par défaut chargées | le modèle voit 17 outils (dont sous-agents, applications HTML, gestion d'extensions), pas seulement ceux de `developer` ; consigne système plus longue | `advertised_tools` de la trace de `c1-02` ; `--no-profile` non utilisé |
| Sorties non collectées | session exportée, base des sessions et journaux de Goose restent dans `~/banc-espaces/<essai>/maison/` | [`lancer.sh`](../lancer.sh), [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh) |
| Trace pas entièrement JSON | quatre lignes de bandeau en tête de `stdout.log` | `banc-essai/resultats/goose-jouet-1/harnais/stdout.log` |
| Images non comptées | dans `c1-02`, l'outil `read_image` a renvoyé une image au harnais, mais le relais compte 0 appel avec image : forme d'envoi de l'image au modèle non expliquée | trace et `essai.json` de `c1-02` |
| Architecture unique | archive x86_64 seulement dans `installer.sh` | [`installer.sh`](../installer.sh) |
| Version figée | 1.60.1 ; la 1.61.1 est sortie le 26/11/2026 | API GitHub des versions, 27/11/2026 |
| Mode plan | non disponible ou non trouvé dans la 1.60.1 | section 1 |
| Échantillon | un seul essai complet sur la tâche d'extraction, aucun essai complet sur la tâche 2 ni sur un goldset | section 2 |
