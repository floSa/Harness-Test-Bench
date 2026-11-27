# Cline : fonctionnement, constats, dépannage

[Retour à la page d'entrée](../README.md)

Cette page sépare ce que Cline sait faire d'après ses sources (section 1) de ce qu'il a fait sur le banc (section 2). La documentation officielle décrit la dernière version publiée (3.0.76 au 27/11/2026), pas forcément la 3.0.74 du banc : un point lu dans la documentation et non retrouvé dans la 3.0.74 est signalé.

Sources citées :

| Repère | Source |
|---|---|
| Aide 3.0.74 | `cline --help`, `cline auth --help`, `cline config --json` lancés le 27/11/2026 sur la version installée, dossier personnel temporaire |
| README 3.0.74 | `harnais/cline/installe/cline/node_modules/cline/README.md` (hors git), identique à <https://unpkg.com/cline@3.0.74/README.md>, consulté le 27/11/2026 |
| CLI reference | <https://docs.cline.bot/cline-cli/cli-reference.md>, consulté le 27/11/2026 |
| Plan & Act | <https://docs.cline.bot/core-workflows/plan-and-act.md>, consulté le 27/11/2026 |
| Subagents | <https://docs.cline.bot/features/subagents.md>, consulté le 27/11/2026 |
| Deprecations | <https://docs.cline.bot/resources/deprecations.md>, consulté le 27/11/2026 |
| Auto Compact | <https://docs.cline.bot/features/auto-compact.md>, consulté le 27/11/2026 |
| Rules | <https://docs.cline.bot/customization/cline-rules.md>, consulté le 27/11/2026 |
| Config | <https://docs.cline.bot/getting-started/config.md>, consulté le 27/11/2026 |
| Telemetry | <https://docs.cline.bot/enterprise-solutions/monitoring/telemetry.md>, consulté le 27/11/2026 |
| Proxies | <https://docs.cline.bot/troubleshooting/networking-and-proxies.md>, consulté le 27/11/2026 |

## 1. Capacités

| Capacité | Présente | Détail | Source |
|---|---|---|---|
| Mode sans interaction | oui | une consigne en argument, `--json` ou sortie redirigée : aucune question ; sans terminal, les appels qui demandent une approbation sont refusés (d'où `-y` sur le banc) | README 3.0.74 |
| Sortie lisible par un programme | oui | `--json` : un objet JSON par ligne (NDJSON), voir [lancement](lancement.md#4-format-de-la-trace) | Aide 3.0.74, CLI reference |
| Approbation automatique | oui | `-y` : approbation des outils, outil `submit_and_exit`, outils de sous-agents et d'équipe coupés par défaut ; `--auto-approve <true\|false>` (vrai par défaut) | Aide 3.0.74, README 3.0.74 |
| Liste blanche de commandes du shell | non | « The CLI has no allow or deny list for shell commands » ; blocage possible par un point d'accroche `PreToolUse` | CLI reference |
| Modes Plan et Act | oui | `-p`, `--plan` : mode Plan ; Act par défaut. En Plan, l'agent lit, cherche et discute mais « cannot modify any files or execute commands » (page écrite pour l'extension) ; un modèle différent par mode est un réglage de l'extension, non documenté pour la CLI ; non vérifié sur le banc | Aide 3.0.74, Plan & Act |
| Sous-agents | oui, coupés par `-y` | outil `spawn_agent` : un agent avec sa propre consigne et sa propre fenêtre de contexte, qui rend un rapport ; disponible dans la CLI ; pas d'outils MCP dans un sous-agent ; coût ajouté à la session | Subagents, `cline config --json` |
| Équipes d'agents | oui, coupées par `-y` | outils `team_*` (coéquipiers, tâches, boîte aux lettres, journal de mission) | `cline config --json`, README 3.0.74 |
| Liste de tâches (« Focus Chain ») | non | fonction de l'extension déclarée obsolète, « No direct replacement » ; aucun outil de liste de tâches dans les outils de la 3.0.74 | Deprecations, `cline config --json` |
| Compaction du contexte | oui | `--compaction agentic` (par défaut : résumé par le modèle), `basic` (troncature locale), `off` ; déclenchée à l'approche de la fenêtre de contexte du modèle, que Cline ne connaît pas pour le modèle du banc ([configuration](configuration.md#7-fenêtre-de-contexte-piste-non-appliquée)) | Aide 3.0.74, README 3.0.74, Auto Compact |
| Niveau de raisonnement | oui | `--thinking none\|low\|medium\|high\|xhigh` ; non utilisé sur le banc (valeur du fournisseur) | Aide 3.0.74 |
| Outils intégrés | oui | `ask_question`, `editor`, `fetch_web_content`, `read_files` (texte et images), `run_commands`, `search_codebase`, `skills`, `spawn_agent`, `teams` ; plus `submit_and_exit` avec `-y` | `cline config --json`, README 3.0.74 |
| Lecture d'images par le modèle | possible | `read_files` lit les fichiers image ; envoi des images à un modèle « openai-compatible » sans capacité `vision` déclarée : non vérifié sur le banc | `cline config --json` |
| Règles du projet | oui | `.clinerules/` ou `.cline/rules/` à la racine du projet, lus par la CLI ; règles globales dans `~/.cline/rules`, `~/Documents/Cline/Rules` ; `AGENTS.md` reconnu ; non vérifié sur le banc (aucune règle dans `/travail`) | Rules, Config |
| Compétences, MCP, extensions | oui | `cline skill`, `cline mcp`, `cline plugin` ; dossiers `skills/`, `plugins/` sous `~/.cline` ou `.cline/` | Aide 3.0.74, Config |
| Points d'accroche | oui | `--hooks-dir`, journal `data/logs/hooks.jsonl` | Aide 3.0.74, CLI reference |
| Reprise d'une session | oui | `--id <session>`, `cline history` | Aide 3.0.74 |
| Délai et nouvelles tentatives | oui | `-t` (0 : aucun délai), `--retries` (3 erreurs consécutives avant sortie) | Aide 3.0.74 |
| Dossier de configuration déplaçable | oui | `--config`, `--data-dir`, `CLINE_DIR`, `CLINE_DATA_DIR` | Aide 3.0.74, Config |
| Mise à jour automatique | oui, active par défaut | `npm update --global cline` à chaque commande ; coupée par `CLINE_NO_AUTO_UPDATE=1` (vérifié le 27/11/2026) | journal de npm, lecture du binaire 3.0.74 |
| Télémétrie | oui, active par défaut | coupée par `telemetryOptOut` dans `global-settings.json` | Telemetry |
| Mandataire et certificats | oui | variables de mandataire usuelles, HTTP seulement ; magasin de certificats du système lu automatiquement, `NODE_EXTRA_CA_CERTS` ajouté | Proxies, README 3.0.74 |

## 2. Constats sur le banc

### Essais réels

Un seul essai de Cline a été fait sur le banc, sur la tâche jouet. Aucun essai d'extraction (`sans-aide`, `avec-aide`, `dossiers`, `goldset`) : la campagne 1 s'est arrêtée après l'essai 4 (journal, entrée du 19-20/11/2026 : essais 1 à 4) et la tâche 2 n'a été essayée qu'avec OpenCode et Goose ; aucun dossier `*cline*` d'extraction dans `banc-essai/resultats/` ni `banc-essai/resultats-goldset/` au 27/11/2026.

| Critère | `cline-jouet-1` |
|---|---|
| Date | 19/11/2026, 23 h 09 |
| Recette | `jouet` |
| Version | `cline 3.0.74` |
| Modèle (journal du relais) | `openrouter/deepseek/deepseek-v4.1-flash-1017` |
| Score final | 100,0 % (10 cas cachés réussis sur 10) |
| Soumissions acceptées | 1 |
| Fin déclarée | oui |
| Code de retour | 0 |
| Durée totale | 28,7 s (26,8 s selon Cline) |
| Temps dans le modèle | 22,2 s |
| Appels au modèle | 8 (0 échec, 0 refus 429) |
| Itérations de Cline | 8 |
| Jetons d'entrée | 57 551, dont 47 360 lus dans le cache (82 %) |
| Jetons de sortie | 3 081 (1 276 selon Cline) |
| Coût | 0,001576 $ (relais, OpenRouter et dépense de la clé identiques) |
| Outils appelés | `run_commands` 7, `editor` 1, `submit_and_exit` 1 |
| Mémoire maximale | 0,44 Go |
| Téléchargements | 1,98 Mo (pytest depuis PyPI) |
| Demandes réseau refusées | 3 : `registry.npmjs.org` (2), `data.cline.bot` (1) |
| Sous-agents, équipes | coupés (`enable_spawn: false`, `enable_teams: false`) |

Sources : `banc-essai/resultats/cline-jouet-1/rapport.md`, `essai.json`, `harnais/stdout.log` (outils, itérations, chiffres de Cline), `traces/reseau.jsonl` ; résumé de session dans `~/banc-espaces/cline-jouet-1/maison/.cline/data/sessions/` (hors dépôt).

### Tâche jouet : les cinq harnais

Même tâche, même modèle, dans la cage, le 19/11/2026 (journal, lot 4) :

| Critère | Cline | OpenCode | Goose | Pi | gptme |
|---|---|---|---|---|---|
| Score | 100 % | 100 % (3 essais) | 100 % | 100 % | 100 % |
| Durée | 29 s | 20 à 30 s | 22 s | 23 s | 48 s |
| Appels | 8 | 11 à 12 | 8 | 11 | 15 |
| Coût | 0,0016 $ | 0,0012 à 0,0013 $ | 0,0014 $ | 0,0013 $ | 0,0022 $ |

La tâche jouet sert à vérifier le branchement ; elle ne classe pas les harnais.

### Autres constats

| Constat | Preuve |
|---|---|
| l'adresse du relais est acceptée comme fournisseur compatible OpenAI : pas besoin d'appeler OpenRouter directement (crainte exprimée dans `documentations/protocole.md`) | journal, 19/11/2026 ; appels de l'essai jouet dans `traces/appels.jsonl` sous la clé de l'essai |
| `openai` et `openai-compatible` donnent le même fournisseur | journal, 19/11/2026 |
| hors banc, Cline a réalisé une tâche par le relais du kit de test sécurisé, et démarre avec le Node 24 de l'image officielle | journal, 20/11 et 23/11/2026 |

## 3. Problèmes connus et dépannage

| Symptôme | Cause | Correction |
|---|---|---|
| `LiteLLM du banc arrêté : banc-essai/traces/demarrer.sh` au lancement | relais arrêté | `banc-essai/traces/demarrer.sh` |
| `…/harnais/cline/lancer.sh introuvable`, ou `installe/…/bin/cline: No such file or directory` dans `stderr.log` | Cline non installé | `harnais/cline/installer.sh` |
| `Could not find the Cline CLI binary for your platform` | paquet facultatif `@cline/cli-linux-x64` absent : machine non x86-64, ou npm réglé pour ignorer les dépendances facultatives (`omit=optional` dans `~/.npmrc`) | vérifier `uname -m` et `~/.npmrc`, supprimer `harnais/cline/installe/`, réinstaller (message lu dans `bin/cline`, non rencontré sur le banc) |
| `[cline] Node … cannot read the OS trust store (needs >= 22.15)` | lanceur exécuté avec un Node trop ancien (autre Node que celui du harnais en tête du `PATH`) | mettre `harnais/cline/installe/node/bin` en tête du `PATH`, comme le font les scripts (message lu dans `bin/cline`) |
| erreur de certificat pendant `installer.sh` (curl ou npm) | autorité interne inconnue de curl ou de npm | `CURL_CA_BUNDLE`, `npm_config_cafile` ([installation](installation.md#5-derrière-un-mandataire-et-un-certificat-dentreprise)) |
| `BANC_MODELE_URL: parameter null or not set` | `configurer.sh` ou `lancer.sh` lancé hors de la cage sans les variables | passer par `banc-essai/cage/lancer.sh`, ou fournir les variables ([lancement](lancement.md#7-essai-à-la-main)) |
| `registry.npmjs.org` et `data.cline.bot` refusés dans `traces/reseau.jsonl` | mise à jour automatique et télémétrie de Cline | rien à faire dans la cage (sans effet sur l'essai) ; hors cage, voir [configuration](configuration.md#5-autonomie-télémétrie-mise-à-jour-automatique-et-réseau) |
| appels refusés en 401 dans `traces/appels.jsonl` | clé de l'essai supprimée ou inexistante (essai à la main après `cles.py --supprimer`) | nouvelle clé (`banc-essai/traces/cles.py <alias>`) |
| appel refusé, modèle non permis à la clé | `BANC_MODELE` changé sans redémarrer le relais ([modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 6) | `banc-essai/traces/demarrer.sh` |
| Cline s'arrête seul après quelques erreurs du modèle | 3 erreurs consécutives (`--retries`) | lire `harnais/stderr.log` et les échecs de `traces/appels.jsonl` ; corriger la cause (portail, quota) plutôt que d'augmenter `--retries` |
| outil refusé faute d'approbation, sans question posée | Cline lancé sans terminal et sans `-y` (« required-approval calls are denied », README 3.0.74) | garder `-y` dans `lancer.sh` |
| processus `cline --cline-hub-daemon` resté actif après une commande hors cage | certaines commandes démarrent le service « hub » (constaté avec `cline history`) | `cline hub stop` avec le même `HOME` |
| résumé du contexte trop tôt ou dépassement de contexte (non rencontré) | fenêtre de contexte du modèle inconnue de Cline | piste de [configuration](configuration.md#7-fenêtre-de-contexte-piste-non-appliquée) |
| codes de couleur (`[32m`) dans `harnais/stderr.log` | message de `cline auth` | sans effet |

## 4. Limites

- Une seule mesure sur le banc (tâche jouet) : rien n'est encore connu de Cline sur l'extraction dans des PDF, sa durée ni son coût sur une vraie tâche.
- La fenêtre de contexte, la sortie maximale, la vision et les prix de `modele.env` ne sont pas transmis à Cline (section 2 de [configuration](configuration.md#2-variables-lues)).
- `-y` coupe les sous-agents et les équipes : sur le banc, Cline travaille en agent seul, alors que la capacité existe.
- Mise à jour automatique et télémétrie ne sont pas coupées par les scripts : sans effet dans la cage, mais à couper pour tout usage hors cage.
- La conversation complète (`*.messages.json`) reste dans `~/banc-espaces/<essai>/maison/` et n'est pas copiée dans les résultats ; la trace `stdout.log` contient toutefois les appels d'outils, leurs sorties et le raisonnement.
- Les jetons de sortie comptés par Cline diffèrent de ceux du relais (1 276 contre 3 081 sur l'essai jouet) : utiliser les chiffres du relais.
- La documentation officielle suit la dernière version : certains réglages qu'elle cite manquent dans la 3.0.74 (par exemple `CLINE_TELEMETRY_DISABLED`, absent du binaire).
- Le binaire est un assemblage compilé (moteur Bun embarqué) : son comportement se vérifie par essai ou dans les sources du [dépôt officiel](https://github.com/cline/cline), pas en lisant le paquet installé.
- `installer.sh` ne prévoit que Linux x86-64.
