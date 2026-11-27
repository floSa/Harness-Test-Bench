# Banc des harnais : extraction de données sur un poste d'entreprise

Comparer des harnais d'agents open source (OpenCode, Pi, gptme, Goose, Cline) avec le même modèle d'IA, servi par un portail compatible OpenAI, sur l'extraction de données dans les PDF d'un goldset de l'équipe. Chaque harnais construit un workflow d'extraction, isolé dans une cage, avec une clé du modèle plafonnée ; le banc le note sur un test caché, puis relance son workflow sur des documents qu'il n'a jamais vus.

## Par où commencer

| Situation | Point de départ |
|---|---|
| Mettre le banc en route sur un poste, avec un agent de code | [piag/README.md](piag/README.md), puis la consigne d'amorçage [piag/AMORCAGE.md](piag/AMORCAGE.md) |
| Comprendre le principe du banc | [documentations/principe.md](documentations/principe.md) |
| Faire tourner le banc à la main | [banc-essai/README.md](banc-essai/README.md) |
| Installer ou dépanner un harnais | [harnais/README.md](harnais/README.md) |

## Lire la documentation, du général au détail

| Niveau | Où | Contenu |
|---|---|---|
| 1. Vue d'ensemble | ce README | à quoi sert le dépôt, où aller |
| 2. Documents communs | [`documentations/`](documentations/README.md) | principe du banc, vocabulaire, mesures |
| 3. Banc d'essai | [`banc-essai/README.md`](banc-essai/README.md) | déroulé d'un essai, contenu de chaque dossier, commandes essentielles |
| 4. Détail du banc | [`banc-essai/documentation/`](banc-essai/documentation/README.md) | portail du modèle, goldset, lancer un essai, sécurité et données |
| 3 bis. Harnais | [`harnais/README.md`](harnais/README.md) | les cinq harnais, contrat avec le banc, ajouter un harnais |
| 4 bis. Détail d'un harnais | `harnais/<harnais>/README.md` et `harnais/<harnais>/documentation/` | installation, configuration, lancement, fonctionnement et dépannage |
| 5. Composants | `banc-essai/cage/README.md`, `banc-essai/traces/README.md`, `banc-essai/evaluation/README.md`, `banc-essai/corpus/README.md` | référence technique, à côté du code |

## Arborescence

```text
Harness-Test-Bench/
├── README.md
├── .env.exemple          modèle du fichier des secrets (.env : adresse et clé du portail, jamais commité)
├── goldset/              goldset de l'équipe, à déposer ici (jamais commité)
├── piag/                 consigne d'amorçage pour un agent de code
├── outils/               garde-fous git, mandataire et certificat pour les installations
├── harnais/              installer, configurer et lancer chaque harnais
│   ├── opencode/   pi/   gptme/   goose/   cline/
│   └── commun/           Node.js propre aux harnais JavaScript
├── banc-essai/
│   ├── modele.env        modèle servi aux harnais (nom, capacités, prix, plafond)
│   ├── traces/           relais LiteLLM vers le portail, clés d'essai, journal des appels
│   ├── cage/             lanceur d'essai, cage bubblewrap, filtre réseau, collecte
│   ├── evaluation/       API de soumission, notation, relance, rapports, tests
│   ├── corpus/           import du goldset, consignes, démonstration
│   ├── recettes/         consignes de la tâche jouet, modèle des consignes du goldset
│   └── documentation/    pages détaillées du banc
└── documentations/       documents communs
```

## Démarrage rapide

Prérequis : Linux ou WSL, bubblewrap, Docker, uv. Depuis la racine :

```bash
outils/installer-garde-fous.sh --poste-entreprise
cp .env.exemple .env && chmod 600 .env       # y écrire PORTAIL_URL et PORTAIL_CLE
python3 banc-essai/traces/verifier_portail.py --modele <nom du modèle>
banc-essai/traces/demarrer.sh                 # après avoir rempli banc-essai/modele.env
banc-essai/cage/lancer.sh sonde jouet         # preuve de la cage
```

La suite (harnais, goldset, essais, comparaison) est décrite niveau par niveau dans [piag/AMORCAGE.md](piag/AMORCAGE.md).

## Données

Le goldset, son import, les résultats des essais sur le goldset et les secrets ne sont jamais versionnés ; un garde-fou git refuse leur commit et, sur un poste d'entreprise, tout push. Détail : [banc-essai/documentation/securite-et-donnees.md](banc-essai/documentation/securite-et-donnees.md).
