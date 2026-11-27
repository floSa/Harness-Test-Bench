# Corpus : goldset de l'équipe et démonstration

| Fichier ou dossier | Rôle | Versionné |
|---|---|---|
| `importer_goldset.py` | importe un goldset (`goldset/` à la racine du dépôt) dans le format du banc, après vérification | oui |
| `consignes_goldset.py` | écrit les consignes données aux harnais à partir du schéma validé | oui |
| `goldset_demo.py` | fabrique un goldset de démonstration à partir de `fourni/` et l'importe | oui |
| `fourni/` | 35 rapports d'intervention fictifs (PDF), leurs réponses attendues (`reponses/`) et leur vérité détaillée (`verite/`) : matière première de la démonstration et des tests automatiques | oui |
| `goldset/` | goldset de l'équipe importé : `schema.json`, `rapport-import.md`, `correspondance.json`, `fourni/`, `test-cache/`, `relance/`, `recette/consignes.md` | jamais |
| `demo/` | goldset de démonstration et son import | jamais |

Guide complet : [banc-essai/documentation/goldset.md](../documentation/goldset.md).

## Commandes

Depuis la racine du dépôt :

| Commande | Effet |
|---|---|
| `python3 banc-essai/corpus/importer_goldset.py` | importe `goldset/` dans `banc-essai/corpus/goldset/` et écrit le rapport d'import |
| `python3 banc-essai/corpus/consignes_goldset.py` | consignes du goldset importé (schéma validé exigé) |
| `python3 banc-essai/corpus/goldset_demo.py` | démonstration : `demo/goldset/` (même arborescence qu'un goldset réel) et `demo/import/` |

Les trois scripts n'utilisent que la bibliothèque standard de Python.
