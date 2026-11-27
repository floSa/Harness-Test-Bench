# Goose

Goose est un agent d'IA open source en ligne de commande : il reçoit une consigne, appelle un modèle de langage et exécute lui-même les outils proposés par le modèle (commandes, lecture et écriture de fichiers) jusqu'à la fin de la tâche. Sur le banc, il tourne sans interaction dans la cage et n'appelle le modèle que par le relais LiteLLM local.

| Élément | Valeur |
|---|---|
| Version figée | 1.60.1 (fichier [`version`](version), variable `VERSION` de [`installer.sh`](installer.sh)) |
| Licence | Apache-2.0 (API GitHub du dépôt officiel, consultée le 27/11/2026) |
| Forme | binaire unique pour Linux x86_64 (204 Mo), sans dépendance hors des bibliothèques du système ; une application de bureau existe aussi, non utilisée sur le banc |
| Dépôt officiel | <https://github.com/aaif-goose/goose> ; documentation : <https://goose-docs.ai/> |
| Mode utilisé | `goose run` sans interaction, extension intégrée `developer`, sortie en événements JSON (`stream-json`) |
| Fichiers du dossier | `installer.sh` (téléchargement et vérification du binaire), `configurer.sh` (écriture de `config.yaml`), `lancer.sh` (lancement dans la cage), `version` (version relevée dans chaque essai), `installe/` (binaire, hors git), `documentation/` (pages détaillées) |

## En trois commandes

Depuis la racine du dépôt, une fois le banc prêt (relais LiteLLM démarré, cage vérifiée : voir la documentation du banc).

Installer le binaire (version figée, empreinte SHA-256 vérifiée) :

```bash
harnais/goose/installer.sh
```

Vérifier l'installation (doit afficher `1.60.1`) :

```bash
harnais/goose/installe/goose --version
```

Lancer un essai, ici la tâche jouet (22 s, 8 appels et 0,0014 $ lors de l'essai du 19/11/2026, `banc-essai/resultats/goose-jouet-1/`) :

```bash
banc-essai/cage/lancer.sh goose jouet
```

Les résultats sont écrits dans `banc-essai/resultats/goose-jouet-<date>-<heure>/` (`rapport.md` pour la lecture).

## Documentation détaillée

| Page | Contenu |
|---|---|
| [Installation](documentation/installation.md) | prérequis, étapes de `installer.sh`, hôtes réseau à autoriser, mandataire et certificat d'entreprise, vérification, changement de version, désinstallation |
| [Configuration](documentation/configuration.md) | fichier écrit par `configurer.sh`, variables lues, lien avec `banc-essai/modele.env`, mode autonome, télémétrie, emplacement de la clé, fenêtre de contexte |
| [Lancement](documentation/lancement.md) | lancer un essai et le suivre, ce qui se passe dans la cage, sorties produites et format de la trace, arrêt propre, essai à la main |
| [Fonctionnement](documentation/fonctionnement.md) | capacités du harnais avec leurs sources, résultats des essais réels, problèmes connus et dépannage, limites |

## Voir aussi

- [Vue d'ensemble des harnais](../README.md) : comparaison des cinq harnais du banc.
- [Documentation du banc](../../banc-essai/documentation/) : relais du modèle, cage, recettes, goldset, résultats.
