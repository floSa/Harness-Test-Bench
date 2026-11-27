# Harnais

Un harnais d'agent est le programme qui fait travailler un modèle d'IA : il lui donne des outils (lire et écrire des fichiers, lancer des commandes), enchaîne ses appels et gère sa mémoire de travail. Le banc compare cinq harnais open source avec le même modèle.

## Les cinq harnais

| | OpenCode | Pi | gptme | Goose | Cline |
|---|---|---|---|---|---|
| Version figée | voir `opencode/version` | voir `pi/version` | voir `gptme/version` | voir `goose/version` | voir `cline/version` |
| Forme installée | binaire officiel | paquet npm et son Node | paquet PyPI dans un environnement virtuel | binaire officiel | paquet npm et son Node |
| Lancement sans interaction | `opencode run` | `pi --mode json` | `gptme --non-interactive` | `goose run` | `cline --json -y` |
| Page d'entrée | [opencode/](opencode/README.md) | [pi/](pi/README.md) | [gptme/](gptme/README.md) | [goose/](goose/README.md) | [cline/](cline/README.md) |

Chaque dossier contient le même jeu de fichiers, et une documentation détaillée :

| Fichier | Rôle |
|---|---|
| `README.md` | page d'entrée : ce qu'est le harnais, installer, vérifier, lancer en trois commandes |
| `version` | version figée, relevée dans chaque essai |
| `installer.sh` | installation dans `installe/` (hors git), version figée ; empreinte SHA-256 (binaires) ou intégrité npm vérifiée ; gptme : paquet PyPI sans empreinte figée |
| `configurer.sh` | écrit la configuration du harnais à partir des variables données par la cage |
| `lancer.sh` | lance le harnais sans interaction, dans la cage ; sa sortie standard est la trace de la session |
| `documentation/installation.md` | prérequis, étapes, sources réseau, mandataire et certificat d'entreprise, mise à jour |
| `documentation/configuration.md` | fichiers écrits, variables, modèle, autonomie, clé |
| `documentation/lancement.md` | essai dans la cage, sorties, trace, suivi, arrêt |
| `documentation/fonctionnement.md` | capacités, constats sur le banc, dépannage |

## Installer et essayer un harnais

Depuis la racine du dépôt, relais du modèle démarré (`banc-essai/traces/demarrer.sh`) :

```bash
. outils/env-mandataire.sh          # poste d'entreprise : mandataire et certificat de .env
harnais/<harnais>/installer.sh
banc-essai/cage/lancer.sh <harnais> jouet --essai jouet-<harnais>
cat banc-essai/resultats/jouet-<harnais>/rapport.md
```

La tâche jouet (quelques minutes) prouve que le harnais tourne dans la cage, joint le modèle, soumet et déclare sa fin.

## Contrat entre un harnais et le banc

Le banc ne connaît d'un harnais que trois scripts et un fichier. Dans la cage, le dossier du harnais est monté en lecture seule sur `/opt/harnais`, et le lanceur appelle :

```bash
/opt/harnais/lancer.sh "Suis les consignes de consignes.md."
```

| Variable reçue dans la cage | Contenu |
|---|---|
| `BANC_MODELE_URL` | `http://127.0.0.1:4100` : relais du modèle, API compatible OpenAI sous `/v1` |
| `BANC_MODELE` | nom du modèle à demander |
| `BANC_CLE_MODELE` | clé de l'essai (en-tête `Authorization: Bearer`) |
| `BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION` | fenêtre de contexte, sortie maximale, lecture d'images (`banc-essai/modele.env`) |
| `BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE` | prix en dollars par million de jetons |
| `BANC_API` | API de soumission de l'essai |
| `HOME` | `/home/banc`, dossier personnel propre à l'essai (configuration du harnais, sessions) |
| `HTTPS_PROXY` | filtre réseau de la cage (PyPI, Hugging Face, GitHub seulement) |

Ce que le harnais doit respecter :

| Exigence | Raison |
|---|---|
| tourner sans aucune interaction (entrée standard fermée) | le banc n'a personne pour répondre |
| exécuter outils et commandes sans demander de confirmation | même raison ; la cage borne ce qu'il peut toucher |
| appeler le modèle uniquement par `BANC_MODELE_URL` avec `BANC_CLE_MODELE` | journal, plafond et clé supprimée à la fin |
| n'écrire sa configuration que dans `$HOME` | le dossier du harnais est en lecture seule ; `$HOME` est propre à l'essai |
| ne jamais écrire la clé dans un fichier versionné | elle change à chaque essai, et la relance en reçoit une autre |
| écrire la trace de session sur la sortie standard (ou l'exporter dans `$HOME`) | relecture après l'essai : `harnais/stdout.log` |
| ne dépendre d'aucun service extérieur au démarrage (télémétrie, catalogue de modèles, mise à jour) | le réseau de la cage les refuse ; il faut les couper par configuration ou variable d'environnement |

## Ajouter un harnais

1. **Vérifier qu'il convient** : licence open source, mode sans interaction, fournisseur compatible OpenAI configurable (adresse, clé et nom de modèle libres), exécution des outils sans confirmation. Chercher chaque point dans sa documentation officielle et citer la source.
2. **Créer `harnais/<nom>/`** en partant du harnais le plus proche : binaire (`goose/`, `opencode/`), paquet npm (`pi/`, `cline/`, avec `commun/installer-node.sh`) ou paquet PyPI (`gptme/`).
3. **`installer.sh`** : version figée dans une variable ; téléchargement depuis la source officielle ; vérification d'empreinte SHA-256 (binaire) ou d'intégrité (npm, pip) ; installation dans `harnais/<nom>/installe/` (déjà ignoré par git) ; sortie immédiate si la bonne version est déjà là.
4. **`configurer.sh`** : lit les variables `BANC_*` du tableau ci-dessus, écrit la configuration dans `$HOME`, n'écrit jamais la clé si le harnais sait la lire dans une variable d'environnement ; coupe télémétrie, mises à jour et catalogues en ligne ; déclare contexte, sortie maximale et vision si le harnais les demande.
5. **`lancer.sh`** : appelle `configurer.sh`, puis lance le harnais en mode sans interaction avec `"$@"` comme message ; trace complète sur la sortie standard ; code de retour du harnais rendu au lanceur.
6. **`version`** : une ligne, par exemple `nom 1.2.3`.
7. **Essais, dans l'ordre** :

   ```bash
   harnais/<nom>/installer.sh
   banc-essai/cage/lancer.sh <nom> jouet --essai jouet-<nom>
   ```

   Lire `stderr.log` du harnais et `traces/reseau.jsonl` : un démarrage qui tente de joindre un site refusé doit être coupé par configuration ; un appel au modèle doit apparaître dans `traces/appels.jsonl`.
8. **Documenter** : `README.md` et les quatre pages de `documentation/`, sur le modèle des autres harnais, avec les constats de l'essai jouet.
9. **Ajouter le harnais** au tableau de cette page et au tableau du README racine.

Le banc lui-même ne change pas : aucun nom de harnais n'est écrit dans la cage, l'API ou la notation.
