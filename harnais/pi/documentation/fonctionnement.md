# Pi : fonctionnement, constats, dépannage

Retour : [page d'entrée de Pi](../README.md). Pages voisines : [installation](installation.md), [configuration](configuration.md), [lancement](lancement.md).

## 1. Principe

Pi enchaîne des tours : il envoie au modèle l'invite système, l'historique et la liste des outils ; le modèle répond par du texte et des appels d'outils ; Pi exécute les outils, ajoute leurs résultats à l'historique et relance le modèle, jusqu'à une réponse sans appel d'outil ([how-pi-works.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/how-pi-works.md), consulté le 27/11/2026). Sur le banc, un tour de Pi correspond à un appel au modèle : 11 tours et 11 appels en flux dans `pi-jouet-1`, 99 et 99 dans `c1-04-pi-avec-aide` (section 3).

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
| Compaction du contexte | oui | automatique quand le contexte dépasse la fenêtre moins 16 384 jetons, en gardant les 20 000 derniers jetons ; manuelle par `/compact` ; une tentative de résumé puis de reprise après un dépassement signalé par le fournisseur | réglages par défaut ; jamais déclenchée (section 3) | [compaction.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/compaction.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Approbation des actions | non | aucune demande avant un appel d'outil | sans objet | [security.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md) |
| Bac à sable intégré | non | isolement à fournir par un conteneur, une machine virtuelle ou un bac à sable | cage bubblewrap du banc | [security.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md) |
| Confiance de projet | oui | les ressources `.pi/` d'un dossier de travail ne se chargent qu'après accord ; en mode JSON, sans accord enregistré, elles sont ignorées (défaut `ask`) | ignorées | [security.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md) |
| Fichiers de contexte | oui | `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md` du dossier de travail, de ses parents et du dossier de l'agent, chargés sans condition de confiance | aucun dans les recettes | [configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/configuration.md) |
| Fournisseur compatible OpenAI personnalisé | oui | `models.json` : adresse, API (`openai-completions`, etc.), clé lue dans une variable, contexte, vision, prix | fournisseur `banc` | [models-configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/models-configuration.md) |
| Lecture d'images | oui | `read` lit les images ; envoi au modèle si `input` contient `image` ; redimensionnement à 2000 × 2000 pixels au plus par défaut | oui (`BANC_VISION=1`) | [cli.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Niveaux de réflexion | oui | `off` à `max`, pour un modèle déclaré `reasoning` | `off` : modèle non déclaré `reasoning` | [models-configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/models-configuration.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Nouvelles tentatives | oui | après une erreur passagère, 3 tentatives au plus, délai exponentiel à partir de 2 s | réglages par défaut ; non observé (aucun échec d'un appel de Pi) | [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Sessions | oui | fichiers JSONL en arbre, reprise (`--continue`, `--resume`), branches, export HTML, session éphémère (`--no-session`) | enregistrée dans le dossier personnel de la cage | [sessions.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/sessions.md) |
| Suivi du coût | oui | coût de chaque réponse calculé avec les prix de `models.json` | prix de `modele.env` | [models-configuration.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/models-configuration.md) |
| Serveurs MCP | oui | extension intégrée `builtin:mcp`, serveurs déclarés dans `mcp.json` | aucun serveur déclaré | [mcp.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/mcp.md) |
| Extensions, compétences, modèles d'invite, thèmes, paquets | oui | extensions TypeScript chargées dans le processus de Pi ; distribution par npm ou git | aucune | [README](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/README.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Fonctionnement hors ligne | oui | `PI_OFFLINE`, `PI_SKIP_VERSION_CHECK`, `PI_TELEMETRY` | les trois | [environment-variables.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/environment-variables.md) |
| Mandataire HTTP | oui | `HTTP_PROXY`, `HTTPS_PROXY`, réglage `httpProxy` | mandataire de la cage, contourné pour `127.0.0.1` | [environment-variables.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/environment-variables.md), [settings.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |
| Recherche sur Internet | non intégrée | aucun outil intégré de recherche ou de lecture de pages | non | [cli.md](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), section Tools |

## 3. Constats sur le banc

Essais réels de Pi 1.5.2, modèle `deepseek-v4.1-flash` (OpenRouter, `deepseek/deepseek-v4.1-flash-1017`) par le relais du banc. Sources : `rapport.md` et `essai.json` de chaque essai, `traces/appels.jsonl` (répartition des appels), `harnais/stdout.log` (outils et tours).

| Critère | [`pi-jouet-1`](../../../banc-essai/resultats/pi-jouet-1/rapport.md) | [`c1-04-pi-avec-aide`](../../../banc-essai/resultats/c1-04-pi-avec-aide/rapport.md) |
|---|---|---|
| Date | 19/11/2026 | 20/11/2026 |
| Recette | `jouet` | `avec-aide` (campagne 1) |
| Score final (soumission déclarée) | 100 % (10 tests cachés sur 10) | 100 % |
| Score de validation annoncé par Pi | 100 % | 100 % |
| Taux d'invention | | 0 % |
| Score sur le style de mise en page jamais vu | | 100 % |
| Relance du workflow (10 documents neufs) | | 99,3 %, 10 JSON sur 10, 8,47 s et 0,000738 $ par document |
| Soumissions acceptées | 1 | 1 |
| Durée | 23,2 s | 1 615,3 s (27 min) |
| Code de retour, garde-fou atteint | 0, non | 0, non |
| Appels au modèle (total de la clé) | 11 | 365 |
| dont appels de Pi (en flux, 4 outils déclarés) | 11 | 99, dont 82 avec image, aucun échec |
| dont appels sans flux ni outil (déduits : code écrit par Pi, exécuté pendant l'essai) | 0 | 266, dont 259 avec image et 10 échecs HTTP 500 |
| Appels refusés pour quota (429) | 0 | 0 |
| Plus grand contexte envoyé par Pi | 7 043 jetons | 167 499 jetons |
| Compactions | 0 | 0 (aucune entrée `compaction` dans la session) |
| Tours de Pi | 11 | 99 |
| Outils appelés | `bash` 9, `read` 5, `edit` 1 | `bash` 77, `read` 21 |
| Jetons envoyés (dont lus dans le cache) | 53 756 (46 336) | 12 676 135 (10 874 752) |
| Jetons produits | 2 584 | 503 684 |
| Temps dans le modèle | 21,2 s | 1 578,3 s |
| Coût total (relais) | 0,001285 $ | 0,273799 $ |
| dont appels de Pi | 0,0013 $ | 0,0741 $ |
| Pic de mémoire | 0,16 Go | 1,25 Go |
| Pic de disque | 7 Ko | 554 Mo |
| Téléchargements (PyPI seulement) | 1,96 Mo | 118 Mo |
| Demandes réseau refusées | 0 | 0 |
| Trace `stdout.log` | 344 Ko | 72 Mo avant compression (journal), 51,7 Mo en gzip |
| Code livré | | `workflow.py`, 532 lignes ([`code/INDEX.md`](../../../banc-essai/resultats/c1-04-pi-avec-aide/code/INDEX.md)) |

Lecture des chiffres :

- Répartition des appels : la trace de `c1-04-pi-avec-aide` compte 99 tours de Pi, autant que d'appels en flux avec 4 outils déclarés dans `traces/appels.jsonl`. Les 266 autres appels, sans flux ni outil, ne viennent donc pas de Pi mais d'un programme lancé dans la cage avec la clé de l'essai, vraisemblablement le `workflow.py` écrit par Pi pendant ses essais. Les 10 échecs HTTP 500 notés au journal (« 10 échecs du fournisseur absorbés ») sont tous parmi ces appels.
- Contexte : Pi n'a jamais dépassé 167 499 jetons envoyés, loin de la fenêtre déclarée (1 000 000) ; la compaction n'a donc jamais servi. Son comportement avec un portail à fenêtre plus petite reste à observer.
- Réseau : aucune demande vers `pi.dev` ni vers un autre site que PyPI ; les deux demandes de chaque essai sont des installations de paquets Python ([configuration](configuration.md), section 5).
- Taille de la trace : chaque morceau de réponse en flux est un événement `message_update` (8 684 sur 9 657 lignes dans `c1-04-pi-avec-aide`) ; une trace de 72 Mo a conduit à ajouter la compression des traces de plus de 20 Mo au lanceur ([`documentations/journal.md`](../../../documentations/journal.md), essai 4 de la campagne 1).

Comparaison avec les autres harnais sur la même recette : [`documentations/journal.md`](../../../documentations/journal.md), campagne 1 (19 au 20/11/2026).

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
| Appels refusés, modèle non permis à la clé | `BANC_MODELE` changé sans redémarrer le relais | `banc-essai/traces/demarrer.sh` ([`modele-et-fournisseur.md`](../../../banc-essai/documentation/modele-et-fournisseur.md), section 6) |
| Appels avec image en échec | modèle sans vision déclaré avec `BANC_VISION=1` | `BANC_VISION=0` dans `banc-essai/modele.env` |
| Requêtes refusées pour longueur chez le portail | `BANC_CONTEXTE` plus grand que la fenêtre réelle du modèle : la compaction se déclenche trop tard | mettre la vraie fenêtre dans `BANC_CONTEXTE` (non observé sur le banc) |
| Refus lié à la sortie maximale | `BANC_SORTIE_MAX` au-delà de la limite du portail | baisser `BANC_SORTIE_MAX` (non vérifié sur le banc) |
| Essai arrêté, code 124, `cage : garde-fou de durée atteint` dans `stderr.log` | durée au-delà de `--duree` (7 200 s par défaut) | relancer avec une durée plus longue si la tâche le justifie |
| `stdout.log` absent, `stdout.log.gz` présent | trace de plus de 20 Mo compressée par `compresser.py` | `zcat banc-essai/resultats/<essai>/harnais/stdout.log.gz \| head` |
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
| Recettes essayées | `jouet` et `avec-aide` seulement ; `sans-aide`, `dossiers` et `goldset` sans essai terminé au 27/11/2026 | `banc-essai/resultats/` |
