# Cline (CLI)

Cline CLI est un agent de code en ligne de commande : il reçoit une consigne, appelle un modèle d'IA, lit et modifie des fichiers et lance des commandes jusqu'à ce que la tâche soit faite. Sur le banc, il tourne sans interaction (`cline --json -y`), dans la cage, et n'atteint le modèle que par le relais LiteLLM du banc (fournisseur « openai-compatible »).

| Élément | Valeur |
|---|---|
| Version figée | 3.0.74 (`installer.sh`, `version`), publiée sur npm le 26/10/2026 ; dernière version publiée le 27/11/2026 : 3.0.76 (non utilisée) ([registre npm](https://registry.npmjs.org/cline), consulté le 27/11/2026) |
| Licence | Apache 2.0 (champ `license` du paquet et fichier `LICENSE` installé) |
| Forme | paquet npm `cline` : un petit lanceur Node (`bin/cline`) qui exécute un binaire Linux x86-64 autonome (moteur Bun embarqué) fourni par le paquet `@cline/cli-linux-x64` ; Node.js 26.13.1 propre au harnais |
| Dépôt officiel | <https://github.com/cline/cline> (dossier `apps/cli`, champ `repository` du paquet) |
| Documentation officielle | <https://docs.cline.bot/cline-cli/cli-reference.md> (décrit la dernière version, pas forcément la 3.0.74) ; README de la version figée : <https://unpkg.com/cline@3.0.74/README.md> |
| `installer.sh` | installe Node.js (`harnais/commun/installer-node.sh`) puis le paquet npm dans `installe/` (hors git) |
| `configurer.sh` | `cline auth` : fournisseur compatible OpenAI = relais du banc, modèle et clé de l'essai, écrits dans `$HOME/.cline` |
| `lancer.sh` | lancé dans la cage : `configurer.sh`, puis `cline --json -y "<message>"` |
| `version` | texte relevé dans `essai.json` (`version_harnais`) : `cline 3.0.74` |
| `installe/` | Node (230 Mo) et paquet npm (415 Mo, dont 155 Mo de binaire), ignorés par git (`.gitignore` : `harnais/*/installe/`) |

## En trois commandes

Depuis la racine du dépôt, relais du banc démarré (`banc-essai/traces/demarrer.sh`) :

```bash
harnais/cline/installer.sh
```

```bash
PATH="$PWD/harnais/cline/installe/node/bin:$PATH" CLINE_NO_AUTO_UPDATE=1 \
  harnais/cline/installe/cline/node_modules/cline/bin/cline --version     # attendu : 3.0.74
```

```bash
banc-essai/cage/lancer.sh cline jouet      # tâche courte : vérifie le branchement harnais-relais-modèle
```

Le rapport de l'essai est écrit dans `banc-essai/resultats/<essai>/rapport.md` (recette `jouet`) ou `banc-essai/resultats-goldset/<essai>/rapport.md` (recette `goldset`, voir [lancement](documentation/lancement.md)).

## Documentation détaillée

| Page | Contenu |
|---|---|
| [Installation](documentation/installation.md) | prérequis, étapes de `installer.sh`, hôtes réseau à autoriser, mandataire et certificat d'entreprise, vérification, mise à jour de la version figée, désinstallation |
| [Configuration](documentation/configuration.md) | ce qu'écrit `cline auth` (fichier réel commenté), variables lues, lien avec `banc-essai/modele.env`, autonomie (`-y`), télémétrie et mise à jour automatique, emplacement de la clé, fenêtre de contexte |
| [Lancement](documentation/lancement.md) | lancer un essai (recettes `jouet` et `goldset`), ce qui se passe dans la cage, sorties et format de la trace NDJSON, suivi, arrêt, essai à la main |
| [Fonctionnement](documentation/fonctionnement.md) | capacités de Cline (sources citées), comportements constatés lors des essais de mise au point du banc, dépannage, limites |

## Voir aussi

- [Vue d'ensemble des harnais](../README.md)
- [Documentation du banc](../../banc-essai/documentation/) : modèle servi par le portail compatible OpenAI, lancer un essai, goldset
- [Cage](../../banc-essai/cage/README.md) : ce que voit un harnais, réseau, ressources
