# Banc des harnais

Comparer des harnais d'agents open source (OpenCode, Pi, gptme, Goose, Cline) avec le même modèle d'IA, sur une tâche d'extraction de données dans des PDF.

Ce dépôt contient les harnais à installer (`harnais/`), le banc d'essai (`banc-essai/`) et la documentation : protocole, prise en main de chaque harnais, résultats (`documentations/`).

```text
Harness-Test-Bench/
├── README.md
├── LICENSE
├── harnais/              installer, configurer et lancer chaque harnais
│   ├── opencode/
│   ├── pi/
│   ├── gptme/
│   ├── goose/
│   └── cline/
├── banc-essai/           rejouer les essais
│   ├── corpus/           50 rapports d'intervention fictifs (test caché hors git)
│   ├── evaluation/       API de soumission (5 essais) et notation
│   ├── cage/             lancement d'un harnais isolé (bubblewrap)
│   ├── traces/           journal de chaque appel au modèle
│   ├── recettes/         consignes de départ : sans aide, avec aide
│   └── resultats/        résultat brut de chaque essai
└── documentations/       lire
    ├── protocole.md
    ├── cahier-des-charges-corpus.md
    └── journal.md
```

État : cadrage terminé ; corpus généré (60 rapports, vérité terrain annotée) ; évaluation prête (API de soumission, notation, recettes, tâche jouet) ; cage et harnais à construire.

| Besoin | Page |
|---|---|
| Méthode | [Protocole](documentations/protocole.md) |
| Corpus | [Cahier des charges](documentations/cahier-des-charges-corpus.md) |
| Avancement | [Journal](documentations/journal.md) |
