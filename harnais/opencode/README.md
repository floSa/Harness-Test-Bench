# OpenCode

OpenCode est un agent de code en ligne de commande : il reçoit une consigne, appelle un modèle d'IA, lit et modifie des fichiers et lance des commandes jusqu'à ce que la tâche soit faite. Sur le banc, il tourne sans interaction (`opencode run`), dans la cage, et n'atteint le modèle que par le relais LiteLLM du banc.

| Élément | Valeur |
|---|---|
| Version figée | 1.19.6 (`version`, `installer.sh`) ; dernière version publiée au 27/11/2026 : 2.4.2, du 26/11/2026 (non utilisée) |
| Licence | MIT ([dépôt officiel](https://github.com/anomalyco/opencode), champ `license` de l'API GitHub, consulté le 27/11/2026) |
| Forme | binaire autonome pour Linux x86-64 (archive officielle `opencode-linux-x64.tar.gz`, empreinte SHA-256 vérifiée), aucun Node ni npm à installer |
| Dépôt officiel | <https://github.com/anomalyco/opencode> |
| Documentation de la version figée | <https://github.com/anomalyco/opencode/tree/v1.19.6/packages/web/src/content/docs> (le site opencode.ai décrit la version 2, dont la syntaxe de configuration diffère) |
| `installer.sh` | télécharge et vérifie le binaire dans `installe/` (hors git) |
| `configurer.sh` | écrit `opencode.json` (fournisseur = relais du banc, permissions, partage et mise à jour coupés) |
| `lancer.sh` | lancé dans la cage : configuration, `opencode run`, export des sessions |
| `version` | texte relevé dans `essai.json` (`version_harnais`) |
| `installe/` | binaire installé (216 Mo), ignoré par git |

## En trois commandes

Depuis la racine du dépôt, relais du banc démarré (`banc-essai/traces/demarrer.sh`) :

```bash
harnais/opencode/installer.sh
```

```bash
harnais/opencode/installe/opencode --version     # attendu : 1.19.6
```

```bash
banc-essai/cage/lancer.sh opencode jouet         # essai de mise au point : 20 à 30 s, environ 0,001 $
```

Le rapport de l'essai est écrit dans `banc-essai/resultats/<essai>/rapport.md`.

## Documentation détaillée

| Page | Contenu |
|---|---|
| [Installation](documentation/installation.md) | prérequis, étapes de `installer.sh`, hôtes réseau à autoriser, mandataire et certificat d'entreprise, mise à jour de la version figée, désinstallation |
| [Configuration](documentation/configuration.md) | fichier écrit par `configurer.sh` (exemple réel commenté), variables lues, lien avec `banc-essai/modele.env`, permissions, réseau, emplacement de la clé |
| [Lancement](documentation/lancement.md) | lancer un essai et ses recettes, ce qui se passe dans la cage, sorties et format de la trace, suivi, arrêt, essai à la main |
| [Fonctionnement](documentation/fonctionnement.md) | capacités d'OpenCode (sources citées), constats chiffrés des essais du banc, dépannage, limites |

## Voir aussi

- [Vue d'ensemble des harnais](../README.md)
- [Documentation du banc](../../banc-essai/documentation/) : modèle et fournisseur, lancer un essai, goldset
- [Cage](../../banc-essai/cage/README.md) : ce que voit un harnais, réseau, ressources
