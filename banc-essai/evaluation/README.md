# Évaluation

API de soumission, notation, préparation des essais, relance du workflow livré et rapports d'essai. Python 3.12 par uv ; le serveur et le client n'utilisent que la bibliothèque standard, pytest sert aux tests.

Le lanceur `banc-essai/cage/lancer.sh` enchaîne tout cela ; les commandes ci-dessous servent à comprendre ou à dépanner. Depuis la racine du dépôt (`E=banc-essai/evaluation`) :

## Déroulement d'un essai

| Étape | Commande |
|---|---|
| 1. Espace de travail neuf | `uv run --project $E python $E/preparer.py --recette goldset --destination <espace>` |
| 2. API (une par essai) | `uv run --project $E python $E/api.py --tache goldset --jeu banc-essai/corpus/goldset/test-cache --sortie <résultats>/evaluation` |
| 3. Harnais | travaille dans `<espace>`, suit `consignes.md`, soumet par `soumettre.py` |
| 4. Relance du workflow livré | `uv run --project $E python $E/relancer.py --espace <espace> --essai <résultats> --tache goldset --jeu banc-essai/corpus/goldset/relance` |
| 5. Rapport | `uv run --project $E python $E/rapport.py --essai <résultats>` |

Tâche jouet : `--recette jouet` à l'étape 1, `--tache jouet --jeu $E/taches/jouet` à l'étape 2, pas d'étape 4.

## Fichiers

| Fichier | Rôle |
|---|---|
| `notation_goldset.py` | notation d'un goldset, lue dans `schema.json` : texte normalisé, nombre à la tolérance du champ, date, booléen, liste fermée, liste sans ordre (crédit partiel) ; documents entièrement justes, taux d'invention et d'omission, score par champ |
| `notation.py` | notation à 15 clés fixes des rapports fictifs de `banc-essai/corpus/fourni/` : sert aux tests automatiques de l'API et de la relance |
| `jouet.py` | tâche jouet : seuls les `.py` du paquet `dosage/` sont acceptés ; la cage (sans réseau) exécute les appels des cas cachés par `executant_jouet.py`, sans les valeurs attendues ; comparaison hors de la cage ; score = part des cas réussis ; refus de noter sans bubblewrap |
| `api.py` | serveur sur `127.0.0.1` : `/etat`, `/documents`, `/documents/<id>.pdf`, `/soumissions`, `/fin` |
| `client/soumettre.py` | client copié dans chaque espace de travail |
| `preparer.py` | espace neuf : consignes, client, `schema.json`, `fourni/` (PDF et réponses) ; rien du test caché ni de la relance |
| `relancer.py` | relance de la commande déclarée sur le jeu de relance (PDF seuls), dans la cage seulement ; seuls les fichiers ordinaires de la sortie sont lus (liens et fichiers spéciaux refusés) ; notation |
| `rapport.py` | `rapport.json` et `rapport.md` (scores agrégés et par champ, aucun détail par document) |
| `index_resultats.py` | index des essais d'un dossier de résultats, régénéré à la fin de chaque essai |
| `taches/jouet/` | cas cachés de la tâche jouet, jamais montés dans la cage |
| `tests/` | tests automatiques : `uv run --project banc-essai/evaluation pytest` |

## Journaux d'un essai

| Fichier | Contenu |
|---|---|
| `evaluation/soumissions.jsonl` | chaque soumission : heure, statut (`acceptee`, `refusee_format`, `refusee_limite`, `refusee_fin`), score, scores agrégés |
| `evaluation/contenus-cache.jsonl` | contenu de chaque soumission (révèle les réponses du test caché) |
| `evaluation/erreurs.jsonl` | erreurs internes de l'API (réponse 500, soumission non décomptée) |
| `evaluation/acces.jsonl` | chaque requête : heure, méthode, chemin, code |
| `evaluation/fin.json` | déclaration de fin : soumission finale, score de validation annoncé, commande du workflow |
| `evaluation/detail-cache.jsonl` | justesse de chaque champ de chaque document du test |
| `relance/` | résultat, sorties et journaux de la commande relancée |

L'état de l'API (soumissions utilisées, fin déclarée) est relu depuis ces journaux à chaque démarrage : un redémarrage ne remet pas le compteur à zéro.
