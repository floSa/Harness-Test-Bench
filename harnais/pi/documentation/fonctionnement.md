# Pi : fonctionnement, constats, dépannage

Retour : [page d'entrée de Pi](../README.md). Pages voisines : [installation](installation.md), [configuration](configuration.md), [lancement](lancement.md).

## 1. Principe

Pi enchaîne des tours : il envoie au modèle l'invite système, l'historique et la liste des outils ; le modèle répond par du texte et des appels d'outils ; Pi exécute les outils, ajoute leurs résultats à l'historique et relance le modèle, jusqu'à une réponse sans appel d'outil ([how-pi-works.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/how-pi-works.md), consulté le 27/11/2026). Sur le banc, un tour de Pi correspond à un appel au modèle (section 3).

Le projet revendique un cœur minimal : « Pi ships with powerful defaults but skips features like sub-agents and plan mode » ; ce qui manque s'ajoute par des extensions, des compétences (skills) ou des paquets ([README de Pi v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md), consulté le 27/11/2026).

## 2. Capacités

Capacités de Pi 1.5.2 d'après sa documentation officielle. Les pages citées sont celles de l'étiquette `v1.5.2` du dépôt, consultées le 27/11/2026 ; les mêmes fichiers sont livrés dans le paquet installé (`harnais/pi/installe/pi/node_modules/@earendil-works/pi-coding-agent/docs/`). La colonne « Sur le banc » dit si la capacité sert dans un essai.

| Capacité | Présente | Détail | Sur le banc | Source |
|---|---|---|---|---|
| Mode sans interaction | oui | `-p`/`--print` (réponse finale en texte), `--mode json` (événements JSONL), `--mode rpc` (commandes JSONL sur l'entrée standard), SDK TypeScript | `--mode json` | [cli.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), [json.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/json.md) |
| Mode plan | non intégré | absent par choix ; l'aide de `pi --help` cite `--plan` comme exemple d'option ajoutée par une extension | non | [README](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md) ; `pi --help` relevé le 27/11/2026 |
| Sous-agents | non intégré | absent par choix, à construire par extension | non | [README](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md) |
| Liste de tâches | non intégrée | aucun outil de liste de tâches parmi les outils intégrés | non | [cli.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), section Tools |
| Outils intégrés | oui | actifs par défaut : `read` (fichiers texte et images), `bash`, `edit`, `write` ; disponibles : `grep`, `find`, `ls`, `powershell` ; extensions intégrées inactives par défaut : `codemode` (script JavaScript qui appelle les autres outils), `tool_search` | les quatre outils par défaut | [cli.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Compaction du contexte | oui | automatique quand le contexte dépasse la fenêtre moins 16 384 jetons, en gardant les 20 000 derniers jetons ; manuelle par `/compact` ; une tentative de résumé puis de reprise après un dépassement signalé par le fournisseur | réglages par défaut ; jamais déclenchée lors des essais de mise au point (section 3) | [compaction.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/compaction.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Approbation des actions | non | aucune demande avant un appel d'outil | sans objet | [security.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md) |
| Bac à sable intégré | non | isolement à fournir par un conteneur, une machine virtuelle ou un bac à sable | cage bubblewrap du banc | [security.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md) |
| Confiance de projet | oui | les ressources `.pi/` d'un dossier de travail ne se chargent qu'après accord ; en mode JSON, sans accord enregistré, elles sont ignorées (défaut `ask`) | ignorées | [security.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md) |
| Fichiers de contexte | oui | `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md` du dossier de travail, de ses parents et du dossier de l'agent, chargés sans condition de confiance | aucun dans les recettes | [configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/configuration.md) |
| Fournisseur compatible OpenAI personnalisé | oui | `models.json` : adresse, API (`openai-completions`, etc.), clé lue dans une variable, contexte, vision, prix | fournisseur `banc` | [models-configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/models-configuration.md) |
| Lecture d'images | oui | `read` lit les images ; envoi au modèle si `input` contient `image` ; redimensionnement à 2000 × 2000 pixels au plus par défaut | selon `BANC_VISION` (`0` par défaut dans `modele.env`) | [cli.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Niveaux de réflexion | oui | `off` à `max`, pour un modèle déclaré `reasoning` | `off` : modèle non déclaré `reasoning` | [models-configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/models-configuration.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Nouvelles tentatives | oui | après une erreur passagère, 3 tentatives au plus, délai exponentiel à partir de 2 s | réglages par défaut ; non observé lors des essais de mise au point (section 3) | [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Sessions | oui | fichiers JSONL en arbre, reprise (`--continue`, `--resume`), branches, export HTML, session éphémère (`--no-session`) | enregistrée dans le dossier personnel de la cage | [sessions.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/sessions.md) |
| Suivi du coût | oui | coût de chaque réponse calculé avec les prix de `models.json` | prix de `modele.env` | [models-configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/models-configuration.md) |
| Serveurs MCP | oui | extension intégrée `builtin:mcp`, serveurs déclarés dans `mcp.json` | aucun serveur déclaré | [mcp.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/mcp.md) |
| Extensions, compétences, modèles d'invite, thèmes, paquets | oui | extensions TypeScript chargées dans le processus de Pi ; distribution par npm ou git | aucune | [README](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Fonctionnement hors ligne | oui | `PI_OFFLINE`, `PI_SKIP_VERSION_CHECK`, `PI_TELEMETRY` | les trois | [environment-variables.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/environment-variables.md) |
| Mandataire HTTP | oui | `HTTP_PROXY`, `HTTPS_PROXY`, réglage `httpProxy` | mandataire de la cage, contourné pour `127.0.0.1` | [environment-variables.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/environment-variables.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Recherche sur Internet | non intégrée | aucun outil intégré de recherche ou de lecture de pages | non | [cli.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), section Tools |

## 3. Comportements constatés lors des essais de mise au point du banc

Constats faits avec Pi 1.5.2 derrière le relais du banc, sur la recette `jouet` et sur une tâche d'extraction dans des PDF. Ils décrivent le comportement du harnais, pas une performance : les chiffres d'un essai dépendent du modèle servi par le portail.

| Point | Constat | Conséquence pour un essai |
|---|---|---|
| Tours et appels | un tour de Pi correspond à un appel au modèle, en flux, avec 4 outils déclarés : autant de `turn_end` dans la trace que d'appels de ce type dans `traces/appels.jsonl` | le nombre de tours se lit dans la trace ([lancement](lancement.md), section 5) |
| Appels qui ne viennent pas de Pi | sur la tâche d'extraction, la majorité des appels de la clé étaient sans flux ni outil : ils venaient du programme écrit par Pi et exécuté dans la cage avec la clé de l'essai (`BANC_CLE_MODELE` est héritée par les commandes), et les seuls échecs HTTP 500 du fournisseur se trouvaient parmi eux | ces appels comptent dans le plafond de la clé (`BANC_BUDGET_ESSAI`) ; distinguer les deux familles dans `traces/appels.jsonl` (flux et nombre d'outils) avant d'attribuer un coût ou un échec à Pi |
| Images | avec un modèle à vision et `BANC_VISION=1`, l'outil `read` a transmis au modèle les images de pages lues | avec `BANC_VISION=0` (défaut de `modele.env`), le modèle ne reçoit que du texte ; le comportement de Pi dans ce cas pendant un essai n'a pas été observé |
| Compaction | jamais déclenchée : aucune entrée `compaction` dans les sessions ; la fenêtre déclarée était alors bien plus grande que le plus grand contexte envoyé | avec `BANC_CONTEXTE=128000`, le seuil tombe à 111 616 jetons et peut être atteint sur un essai `goldset` long ; à vérifier dans la session (`grep -c '"type":"compaction"'` sur le fichier de session) |
| Nouvelles tentatives | aucun appel de Pi en échec, donc aucune nouvelle tentative de Pi observée | réglages par défaut (3 tentatives) non éprouvés |
| Réseau | aucune demande refusée par le filtre de la cage, au démarrage comme en cours d'essai ; aucune demande vers `pi.dev` ; seules demandes : installations de paquets Python (`pypi.org`, `files.pythonhosted.org`) | les réglages hors ligne de [configuration](configuration.md), section 5, suffisent ; rien à ouvrir pour Pi dans le filtre |
| Niveau de réflexion | `off` dans toutes les sessions (`thinking_level_change`) | voir les limites (section 5) |
| Taille de la trace | chaque morceau de réponse en flux est un événement `message_update`, soit la grande majorité des lignes ; la trace d'un essai long a dépassé plusieurs dizaines de Mo | le lanceur compresse en gzip toute trace de plus de 20 Mo (`banc-essai/cage/compresser.py`) |
| Sortie d'erreur | `stderr.log` réduit à la ligne de `configurer.sh` | une ligne de plus dans `stderr.log` signale un diagnostic de Pi ou de la cage |

## 4. Problèmes connus et dépannage

| Symptôme | Cause | Correction |
|---|---|---|
| `installer.sh` : `curl: (6) Could not resolve host` ou délai dépassé | poste derrière un mandataire non déclaré au terminal | exporter `HTTPS_PROXY` et `https_proxy` avant le script ([installation](installation.md), section 4) |
| `installer.sh` : `curl: (60) SSL certificate problem` | inspection TLS par une autorité interne inconnue de curl | ajouter l'autorité au magasin du système (administrateur du poste), ou `CURL_CA_BUNDLE` vers un PEM complet ; ne pas désactiver la vérification |
| npm : `SELF_SIGNED_CERT_IN_CHAIN` ou `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` | même cause, côté npm | `NODE_EXTRA_CA_CERTS` ou `npm_config_cafile` (non vérifié sur le banc) |
| `sha256sum: WARNING: 1 computed checksum did NOT match` | archive de Node.js corrompue ou modifiée en route | relancer ; si l'écart persiste, ne pas contourner le contrôle : vérifier le mandataire |
| `cannot execute binary file` au premier `node` | poste autre que x86-64 : l'archive `linux-x64` est la seule prévue | non pris en charge par `installer-node.sh` |
| `Pi 1.5.2 déjà installé` après un changement de version de Node.js | le test d'installation ne regarde que la version de Pi | `rm -rf harnais/pi/installe` puis `harnais/pi/installer.sh` |
| Pi refuse de démarrer avec le Node.js du système | Pi exige Node.js 22.19 ou plus récent (Node.js 20 de Debian trop ancien) | utiliser le Node.js de `harnais/pi/installe/node/bin` |
| `stderr.log` : `BANC_MODELE_URL: parameter null or not set` | `configurer.sh` lancé hors de la cage sans les variables | lancer par `banc-essai/cage/lancer.sh`, ou fournir `BANC_MODELE_URL` et `BANC_MODELE` |
| `No models available` | `BANC_CLE_MODELE` absente : Pi ignore un fournisseur sans clé (vérifié avec `--list-models` le 27/11/2026) | lancer avec `--cle` (le lanceur le fait) ; vérifier que `banc-essai/traces/secrets/cle-<essai>.env` a été créé |
| `lancer.sh` : `LiteLLM du banc arrêté` | relais non démarré | `banc-essai/traces/demarrer.sh` |
| Appels en échec 401 dans `traces/appels.jsonl` | clé de l'essai supprimée (essai arrêté, ou programme lancé après la fin de l'essai) | relancer l'essai ; une clé supprimée ne se réutilise pas |
| Appels refusés, modèle non permis à la clé | `BANC_MODELE` changé sans redémarrer le relais | `banc-essai/traces/demarrer.sh` ([`modele-et-fournisseur.md`](../../../banc-essai/documentation/modele-et-fournisseur.md)) |
| Appels avec image en échec | modèle sans vision déclaré avec `BANC_VISION=1` | `BANC_VISION=0` dans `banc-essai/modele.env` |
| Requêtes refusées pour longueur chez le portail | `BANC_CONTEXTE` plus grand que la fenêtre réelle du modèle : la compaction se déclenche trop tard | mettre la vraie fenêtre dans `BANC_CONTEXTE` (non observé lors des essais de mise au point) |
| Refus lié à la sortie maximale | `BANC_SORTIE_MAX` au-delà de la limite du portail | baisser `BANC_SORTIE_MAX` (non vérifié lors des essais de mise au point) |
| Essai arrêté, code 124, `cage : garde-fou de durée atteint` dans `stderr.log` | durée au-delà de `--duree` (7 200 s par défaut) | relancer avec une durée plus longue si la tâche le justifie |
| `stdout.log` absent, `stdout.log.gz` présent | trace de plus de 20 Mo compressée par `compresser.py` | `zcat banc-essai/resultats/<essai>/harnais/stdout.log.gz \| head` (`resultats-goldset` pour un essai `goldset`) |
| Trace qui ne grossit plus (`suivi.py`) | commande longue lancée par Pi, ou attente du modèle | regarder le dernier `tool_execution_start` de la trace ; arrêter proprement si l'essai est bloqué ([lancement](lancement.md), section 6) |

## 5. Limites

| Limite | Conséquence | Source |
|---|---|---|
| Ni approbation ni bac à sable | toute la sécurité repose sur la cage ; Pi ne se lance pas hors cage sur le poste | [security.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md) |
| Ni mode plan, ni sous-agents, ni liste de tâches intégrés | Pi planifie dans ses messages ; aucune extension n'est chargée sur le banc | [README](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md) |
| Niveau de réflexion `off` | `configurer.sh` ne déclare pas `reasoning` et `modele.env` n'a pas de variable pour le faire : avec un modèle qui raisonne, Pi ne le demande pas | `harnais/pi/configurer.sh` ; sessions des essais (`thinking_level_change` à `off`) |
| Trace volumineuse | un événement par morceau de réponse ; compression au-delà de 20 Mo | `banc-essai/cage/compresser.py` |
| Version figée en retard | 1.5.2 figée, 1.6.1 publiée au 27/11/2026 | registre npm |
| Dépendances non figées dans git | deux installations peuvent différer par une dépendance indirecte | [installation](installation.md), section 2 |
| Linux x86-64 seulement | `installer-node.sh` ne télécharge que `linux-x64` | `harnais/commun/installer-node.sh` |
| Recette `goldset` non éprouvée | aucun essai de Pi terminé sur le goldset au 27/11/2026 ; faire d'abord l'essai `jouet` sur le poste | [lancement](lancement.md), section 1 |
| Compaction non éprouvée | jamais déclenchée lors des essais de mise au point ; avec une fenêtre de 128 000 jetons, elle peut l'être sur un essai long | section 3 |
