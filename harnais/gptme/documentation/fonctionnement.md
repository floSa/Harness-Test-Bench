# gptme : fonctionnement, constats et dépannage

Retour à la [page d'entrée](../README.md). Les chemins `gptme/...` désignent les sources du paquet installé (version 0.37.0), sous `harnais/gptme/installe/lib/python3.12/site-packages/` (hors git).

## 1. Capacités du harnais

Ce que gptme 0.37.0 sait faire, d'après sa documentation et ses sources ; ce qui a servi sur le banc est dans la section 2.

| Capacité | Présente | Détail | Source |
|---|---|---|---|
| Mode sans interaction | oui | `-n`, `--non-interactive` : traite le message et s'arrête, implique `--no-confirm` ; codes de retour 0 (terminé), 1 (échec), 2 (arguments invalides) | `gptme --help` ; <https://gptme.org/docs/automation.html> |
| Sortie structurée | oui | `--output-format json` : un objet JSON par message | `gptme --help` |
| Fournisseur compatible OpenAI | oui | table `[[providers]]` de `config.toml` | <https://gptme.org/docs/providers-custom.html> |
| Mode plan | non | aucune option de mode plan dans `--help` ; approchants : profils d'agent `explorer` et `isolated` (lecture seule, sans réseau) par `--agent-profile`, ou jeu d'outils `-t read-only` | `gptme --help` ; `gptme-util profile list` (relevé du 27/11/2026) |
| Sous-agents | oui, non chargés par défaut | outil `subagent` (avec `progress`, `clarify`) ; s'active par `-t +subagent` | `gptme --help` ; `gptme-util tools list` ; <https://gptme.org/docs/tools.html> |
| Liste de tâches | oui, chargée par défaut | outil `todo`, liste propre à la conversation | <https://gptme.org/docs/tools.html> ; config de conversation des essais |
| Compaction du contexte | oui, active par défaut | rappel à 90 % du budget, puis point de reprise résumé et vue compactée au budget ; budget par défaut `min(0,9 × fenêtre, fenêtre − sortie max − marge, 256 000)` ; commande `/compact` | <https://gptme.org/docs/context-compression.html> ; `gptme/util/context_budget.py` |
| Outils chargés sur le banc | 20 | `append`, `autocommit`, `autocompact`, `chats`, `complete`, `convert`, `gh`, `ipython`, `lessons`, `mcp`, `memory`, `patch`, `patch_many`, `recall`, `save`, `shell`, `tmux`, `todo`, `vent`, `vision` | `config.toml` de conversation des essais (`~/banc-espaces/<essai>/maison/.local/share/gptme/logs/essai/`) |
| Outils non chargés par défaut | | `choice`, `clarify`, `computer`, `elicit`, `form`, `hashline_edit`, `progress`, `read`, `request_tool_change`, `restart`, `subagent`, `watch`, `yield` | `gptme-util tools list` (relevé du 27/11/2026) |
| Outils indisponibles | | `browser`, `morph`, `precommit`, `rag`, `screenshot` (dépendances ou extensions absentes) | même relevé |
| Serveurs MCP | outil présent | outil `mcp` chargé ; aucun serveur déclaré sur le banc | config de conversation ; <https://gptme.org/docs/config.html> |
| Fin de session déclarée | oui | outil `complete` | <https://gptme.org/docs/tools.html> |
| Nouvelles tentatives | oui | 11 tentatives par appel, attente 1, 2, 4, 8, 16, 32 puis 60 s (environ 5 min) ; `GPTME_LLM_MAX_RETRIES` | `gptme/llm/retry_policy.py` ; <https://gptme.org/docs/config.html> |
| Plafonds de session | oui, non utilisés | `GPTME_SESSION_BUDGET_USD`, `GPTME_SESSION_BUDGET_TOKENS` ; limite de pas `GPTME_MAX_STEPS` | <https://gptme.org/docs/config.html> ; `gptme/chat.py` |
| Garde-fous | oui, en observation | `GPTME_GUARDRAILS` : `shadow` (défaut, journalise), `enforce` (bloque), `off` | `gptme/hooks/guardrails.py` |
| Restriction des sites des outils web | oui | `--allow-hosts` ; sans effet utile ici (`browser` indisponible, réseau filtré par la cage) | `gptme --help` |
| Reprise d'une conversation | oui | `--name <id>`, `-r` | `gptme --help` |
| Fichiers de configuration | oui | utilisateur (`config.toml`, `config.local.toml`), projet (`gptme.toml`, `gptme.local.toml`), conversation | <https://gptme.org/docs/config.html> |
| Télémétrie | oui, désactivée par défaut | OpenTelemetry, seulement si `GPTME_TELEMETRY_ENABLED` vaut `true`, `1` ou `yes` | `gptme/util/_telemetry.py` |
| Déclaration du contexte et des prix d'un modèle inconnu | partielle | contexte : `GPTME_CONTEXT_LENGTH` (posé par `lancer.sh` si `BANC_CONTEXTE` est inférieur à 128 000) ; budget de compaction : `--context-budget`, `GPTME_CONTEXT_BUDGET`, `[models."..."] context_budget` ; prix et vision : seulement par un greffon de fournisseur | [configuration.md](configuration.md), section 4 |

Pages de la documentation officielle citées : consultées le 27/11/2026.

## 2. Constats sur le banc

Constatés lors des essais de mise au point du banc, avec gptme 0.37.0 et le modèle servi par le relais, sur la tâche jouet et sur une tâche d'extraction de données de rapports PDF. Les résultats chiffrés de ces essais ne font pas partie du kit.

- Les essais vont au bout seuls, sans intervention : code de retour 0, fin déclarée par l'outil `complete`, garde-fou de durée jamais atteint.
- Sur l'extraction, l'agent a écrit un programme d'extraction qui appelle lui-même le modèle avec la clé de l'essai, en lui envoyant les pages sous forme d'images ; ces appels (sans outil, sans flux) formaient la majorité des appels de l'essai. Avec un modèle sans vision (`BANC_VISION=0`), cette voie n'est pas ouverte à l'agent (non vérifié avec gptme).
- Quelques erreurs ponctuelles du fournisseur sont survenues ; les nouvelles tentatives de gptme les ont absorbées sans effet sur l'essai.
- Le coût affiché par gptme (`Session cost reached $…`, `metadata.cost`) est sans rapport avec la dépense mesurée par le relais : prix empruntés à un modèle d'OpenAI et cache compté à part ([configuration.md](configuration.md), section 4).
- gptme a compacté le contexte vers 115 000 jetons (rappel vers 103 000), soit 90 % de la fenêtre générique de 128 000 jetons retenue pour un fournisseur personnalisé, bien que le modèle accepte davantage ([configuration.md](configuration.md), section 4). Le résultat n'en a pas souffert.
- Outils les plus appelés : `shell`, de loin, puis `save` et `patch` ; `ipython` rarement ; `complete` pour finir.
- Réseau : aucune demande refusée par la cage ; les seules demandes au filtre sont celles de l'agent vers PyPI pour installer des paquets.

Aucun essai de gptme sur la recette `goldset`, ni avec le portail d'entreprise, ni derrière un mandataire d'entreprise.

## 3. Problèmes connus et dépannage

| Symptôme | Cause | Correction |
|---|---|---|
| Essai en échec immédiat, code 127, si l'on appelle `installe/bin/gptme` dans la cage | ce script désigne l'interpréteur par le chemin de l'hôte, invisible dans la cage (constaté lors de la mise au point du banc) | appeler `installe/bin/python` et `gptme.cli.main`, comme [`lancer.sh`](../lancer.sh) |
| `<chemin>/harnais/gptme/lancer.sh introuvable` au lancement | script absent ou non exécutable (message de `banc-essai/cage/lancer.sh`) | vérifier `ls -l harnais/gptme/lancer.sh` ; le bit d'exécution est versionné (mode 100755) |
| Essai terminé aussitôt, `stderr.log` qui signale `installe/bin/python` introuvable | gptme non installé, ou `installe/` supprimé : `lancer.sh` ne le vérifie pas | `harnais/gptme/installer.sh` |
| `LiteLLM du banc arrêté : banc-essai/traces/demarrer.sh` | relais du modèle arrêté | `banc-essai/traces/demarrer.sh` |
| `BANC_MODELE: parameter null or not set` | `configurer.sh` lancé hors cage sans les variables | les exporter, voir [configuration.md](configuration.md) |
| Échec de `uv pip install` sur une erreur de certificat | inspection TLS par une autorité d'entreprise (non rencontré sur le banc) | `SSL_CERT_FILE` ou `UV_SYSTEM_CERTS=true`, voir [installation.md](installation.md), section 4 |
| `uv pip install` sans réponse ou connexion refusée | sortie Internet par un mandataire | `HTTPS_PROXY`, ou miroir interne par `UV_DEFAULT_INDEX` |
| uv refuse l'installation (version de Python exigée par le paquet) | `/usr/bin/python3` antérieur à 3.11.5 (non rencontré sur le banc) | Python 3.11.5 à 3.15 dans `/usr` du poste (le Python de uv, dans le dossier personnel, est invisible dans la cage) |
| `gptme 0.37.0 déjà installé` alors qu'une réinstallation est voulue | le script s'arrête si la version est déjà là | `rm -rf harnais/gptme/installe` puis réinstaller |
| `WARNING Unknown model openai/banc/<modèle>: using closest match metadata` | modèle inconnu de gptme | aucune : sans effet sur le travail ; coût affiché faux |
| `Session cost reached $…` très supérieur à la dépense réelle | prix empruntés au modèle d'OpenAI le plus proche | lire le coût du relais (`essai.json`, `suivi.py`) |
| `WARNING Parallel agent detected: gptme PID 1` | détection d'agents voisins de gptme (`gptme/hooks/workspace_agents.py`) ; cause exacte dans la cage non établie | aucune : présent lors des essais de mise au point du banc, sans effet constaté |
| `Guardrail (shadow): would block — Credential output blocked` | l'agent a lancé une commande qui afficherait des variables ; garde-fous en observation | aucune pour l'essai ; les clés de la forme `sk-…` sont masquées dans les résultats par `masquer.py` ; `GPTME_GUARDRAILS=enforce` bloquerait la commande (non essayé) |
| `Discarding failed LLM attempt N/11 after InternalServerError; retrying in …` | erreur du fournisseur ou du relais | aucune si l'appel finit par passer ; si les 11 tentatives échouent, vérifier le relais (`banc-essai/traces/journaux/appels.jsonl`, champ `erreur`) ; `GPTME_LLM_MAX_RETRIES` change le nombre |
| `Auto-summarize triggered`, `Switched to view: compacted-NNN` | budget de compaction atteint (115 200 jetons, 90 % de la fenêtre générique de 128 000) | normal ; budget réglable par `GPTME_CONTEXT_BUDGET` (piste non appliquée) |
| Erreur de longueur de contexte renvoyée par le portail | fenêtre du modèle inférieure à la valeur connue de gptme : `BANC_CONTEXTE` absent, laissé à 128 000 ou supérieur à la fenêtre réelle | déclarer la fenêtre réelle dans `BANC_CONTEXTE` (`banc-essai/modele.env`) ; si elle est inférieure à 128 000, `lancer.sh` la transmet par `GPTME_CONTEXT_LENGTH` ([configuration.md](configuration.md), section 4 ; non vérifié avec un modèle réel) ; gptme tente aussi une récupération après dépassement ([documentation](https://gptme.org/docs/context-compression.html)) |
| `WARNING Failed shlex parsing command, using raw command: No closing quotation` | commande du modèle mal citée | aucune : la commande est exécutée telle quelle |
| `stdout.log` illisible par un lecteur JSON ligne à ligne | sorties brutes des commandes mêlées aux messages | filtrer `grep '^{"type": "message"'` ([lancement.md](lancement.md), section 5) |
| `un autre essai tourne déjà` | verrou du banc (un essai à la fois) | attendre ou arrêter l'essai en cours ([lancement.md](lancement.md), section 7) |

## 4. Limites

- Sortie maximale, vision et prix du modèle ne sont pas transmis à gptme, et le contexte ne l'est que s'il est inférieur à 128 000 jetons : sinon fenêtre supposée de 128 000 jetons ; coût affiché faux ; la prise en compte des images par l'outil `vision` de gptme avec un fournisseur personnalisé n'a pas été vérifiée (les métadonnées génériques ne déclarent pas la vision, `gptme/llm/models/types.py`).
- Sans tiktoken, le compte des jetons par gptme est approché (environ 4 caractères par jeton), ce qui déplace le moment des compactions.
- Installation sans vérification d'empreinte ni dépendances figées ; dépend du Python du système.
- Les journaux de conversation de gptme restent dans `~/banc-espaces/<essai>/maison/` et ne sont pas recopiés dans les résultats.
- Autonomie complète dans la cage : aucune confirmation, garde-fous en observation seulement ; la sécurité repose sur la cage.
- Essais de mise au point limités à la tâche jouet et à une tâche d'extraction de PDF ; aucun sur la recette `goldset`, ni sur un poste d'entreprise.
- Mode plan absent ; sous-agents disponibles mais non activés sur le banc.
