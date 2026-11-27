# Banc des harnais

Comparer des harnais d'agents open source (OpenCode, Pi, gptme, Goose, Cline) avec le même modèle d'IA, sur l'extraction de données dans des documents PDF : chaque harnais construit un workflow d'extraction, isolé dans une cage, avec une clé du modèle plafonnée ; le banc le note sur un test caché, puis relance son workflow sur des documents qu'il n'a jamais vus.

## Deux usages

| | Banc d'origine | Poste d'entreprise (branche `PIAG`) |
|---|---|---|
| Modèle | DeepSeek V4.1 Flash par OpenRouter | modèle d'un portail compatible OpenAI (une adresse, une clé) |
| Documents | corpus public de rapports fictifs (`banc-essai/corpus/`) | goldset de l'équipe : PDF et réponses attendues, jamais versionnés |
| Point de départ | [Protocole expliqué](documentations/protocole-explique.md) | [piag/README.md](piag/README.md), puis la consigne d'amorçage [piag/AMORCAGE.md](piag/AMORCAGE.md) pour un agent de code |

Passer de l'un à l'autre ne change que deux fichiers : `banc-essai/modele.env` (quel modèle) et `.env` (ses secrets).

## Lire la documentation, du général au détail

| Niveau | Où | Contenu |
|---|---|---|
| 1. Vue d'ensemble | ce README | à quoi sert le dépôt, où aller |
| 2. Documents communs | [`documentations/`](documentations/README.md) | protocole, protocole expliqué, cahier des charges du corpus, journal |
| 3. Banc d'essai | [`banc-essai/README.md`](banc-essai/README.md) | déroulé d'un essai, contenu de chaque dossier, commandes essentielles |
| 4. Détail du banc | [`banc-essai/documentation/`](banc-essai/documentation/README.md) | modèle et fournisseur, goldset, lancer un essai, sécurité et données |
| 3 bis. Harnais | [`harnais/README.md`](harnais/README.md) | les cinq harnais, contrat avec le banc, ajouter un harnais |
| 4 bis. Détail d'un harnais | `harnais/<harnais>/README.md` et `harnais/<harnais>/documentation/` | installation, configuration, lancement, fonctionnement et dépannage |
| 5. Composants | `banc-essai/cage/README.md`, `banc-essai/traces/README.md`, `banc-essai/evaluation/README.md`, `banc-essai/corpus/README.md` | référence technique, à côté du code |

## Arborescence

```text
Harness-Test-Bench/
├── README.md
├── .env.exemple          modèle du fichier des secrets (.env, jamais commité)
├── piag/                 poste d'entreprise : consigne d'amorçage pour un agent de code
├── outils/               garde-fous git (données, secrets, push depuis un poste d'entreprise)
├── harnais/              installer, configurer et lancer chaque harnais
│   ├── opencode/   pi/   gptme/   goose/   cline/
│   └── commun/           Node.js propre aux harnais JavaScript
├── banc-essai/
│   ├── modele.env        modèle servi aux harnais (fournisseur, nom, capacités, prix)
│   ├── traces/           relais LiteLLM, clés d'essai, journal des appels, vérificateur du portail
│   ├── cage/             lanceur d'essai, cage bubblewrap, filtre réseau, collecte
│   ├── evaluation/       API de soumission, notation, relance, rapports, tests
│   ├── corpus/           corpus public, import et démonstration d'un goldset
│   ├── recettes/         consignes données aux harnais
│   ├── resultats/        résultats des essais sur le corpus public
│   └── documentation/    pages détaillées du banc
├── livrables/            document Word à distribuer (sécuriser un harnais) et sa source
└── documentations/       protocole, protocole expliqué, cahier des charges du corpus, journal
```

## Démarrage rapide

Prérequis : Linux (ou WSL), bubblewrap, Docker, uv. Depuis la racine :

```bash
cp .env.exemple .env && chmod 600 .env      # puis y écrire la clé du fournisseur
banc-essai/traces/demarrer.sh                # relais du modèle
python3 banc-essai/traces/verifier_portail.py
banc-essai/cage/lancer.sh sonde jouet        # preuve de la cage
harnais/pi/installer.sh
banc-essai/cage/lancer.sh pi jouet           # premier essai
```

## État

Corpus, évaluation, cage, traces et cinq harnais validés sur le banc d'origine ; deux campagnes menées (résultats : [`banc-essai/resultats/`](banc-essai/resultats/README.md)). Branche `PIAG` : fournisseur au choix, tâche goldset, garde-fous et consigne d'amorçage ; avancement détaillé dans le [journal](documentations/journal.md).

| Besoin | Page |
|---|---|
| Tester un harnais en sécurité avec un portail compatible OpenAI, avec Docker, Podman ou sans conteneur | document Word : [livrables/sharepoint](livrables/sharepoint) (source : [livrables/word](livrables/word)) |
