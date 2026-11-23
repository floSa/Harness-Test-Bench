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
├── livrables/           document Word à distribuer (sécuriser un harnais) et sa source
└── documentations/       lire
    ├── protocole.md
    ├── protocole-explique.md
    ├── cahier-des-charges-corpus.md
    └── journal.md
```

État : cadrage terminé ; corpus généré (60 rapports, vérité terrain annotée) ; évaluation prête (API de soumission, notation, recettes, tâche jouet) ; cage et traces prêtes (preuve complète, modèle DeepSeek V4.1 Flash) ; 5 harnais installés et validés sur la tâche jouet ; manuels de prise en main à écrire.

| Besoin | Page |
|---|---|
| Comprendre le banc (schémas, plusieurs niveaux de lecture) | [Protocole expliqué](documentations/protocole-explique.md) |
| Méthode (référence) | [Protocole](documentations/protocole.md) |
| Tester un harnais en sécurité avec un portail compatible OpenAI, avec Docker, Podman ou sans conteneur | document Word : [livrables/sharepoint](livrables/sharepoint) (source : [livrables/word](livrables/word)) |
| Corpus | [Cahier des charges](documentations/cahier-des-charges-corpus.md) |
| Avancement | [Journal](documentations/journal.md) |
