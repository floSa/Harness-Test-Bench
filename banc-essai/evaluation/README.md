# Évaluation

API de soumission, notation, préparation des essais, relance du workflow livré et rapports d'essai. Python 3.12 par uv ; le serveur et le client n'utilisent que la bibliothèque standard, pytest sert aux tests.

Commandes lancées depuis la racine du dépôt (`E=banc-essai/evaluation`).

## Déroulement d'un essai

| Étape | Commande |
|---|---|
| 1. Espace de travail neuf | `uv run --project $E python $E/preparer.py --recette sans-aide --destination <espace>` |
| 2. API (une par essai) | `uv run --project $E python $E/api.py --tache extraction --jeu banc-essai/corpus/test-cache --sortie banc-essai/resultats/<essai>/evaluation` |
| 3. Harnais | travaille dans `<espace>`, suit `consignes.md`, soumet par `soumettre.py` |
| 4. Relance du workflow livré | `uv run --project $E python $E/relancer.py --espace <espace> --essai banc-essai/resultats/<essai>` |
| 5. Rapport | `uv run --project $E python $E/rapport.py --essai banc-essai/resultats/<essai>` |

Tâche jouet : `--recette jouet` à l'étape 1, `--tache jouet --jeu $E/taches/jouet` à l'étape 2, pas d'étape 4.

## Fichiers

| Fichier | Rôle |
|---|---|
| `notation.py` | format attendu, comparaison (texte normalisé, nombre à 0,01 près, date ISO, `null`), scores par clé, étiquette, famille de pièges, emplacement, style, prestataire, langue, nom vu ou inédit ; taux d'invention |
| `jouet.py` | tâche jouet : seuls les `.py` du paquet `dosage/` sont acceptés ; la cage (sans réseau) exécute les appels des cas cachés par `executant_jouet.py`, sans les valeurs attendues ; comparaison hors de la cage ; score = part des cas réussis ; refus de noter sans bubblewrap |
| `api.py` | serveur sur `127.0.0.1` : `/etat`, `/documents`, `/documents/<id>.pdf`, `/soumissions`, `/fin` |
| `client/soumettre.py` | client copié dans chaque espace de travail |
| `preparer.py` | espace neuf : recette, client, `fourni/` (35 PDF et réponses, sans vérité ni annotations) |
| `relancer.py` | relance de la commande déclarée sur le jeu « relance » (PDF seuls), dans la cage seulement ; seuls les fichiers ordinaires de la sortie sont lus (liens et fichiers spéciaux refusés) ; notation |
| `rapport.py` | `rapport.json` et `rapport.md` (scores agrégés, aucun détail par document) |
| `essai_factice.py` | essai complet avec de fausses solutions (extraction et jouet) |
| `taches/jouet/` | cas cachés de la tâche jouet (`cas_caches.json` : appel, valeur ou exception attendue), jamais montés dans la cage |
| `tests/` | tests automatiques (`uv run --project $E python -m pytest -q -p no:cacheprovider $E/tests`) |

## Journaux d'un essai

| Fichier | Contenu | Git |
|---|---|---|
| `evaluation/soumissions.jsonl` | chaque soumission : heure, statut (`acceptee`, `refusee_format`, `refusee_limite`, `refusee_fin`), score, scores agrégés | versionné |
| `evaluation/contenus-cache.jsonl` | contenu de chaque soumission (peut révéler la vérité) | hors git |
| `evaluation/erreurs.jsonl` | erreurs internes de l'API (réponse 500, soumission non décomptée) | versionné |
| `evaluation/acces.jsonl` | chaque requête : heure, méthode, chemin, code | versionné |
| `evaluation/fin.json` | déclaration de fin : soumission finale, score de validation annoncé, commande du workflow | versionné |
| `evaluation/detail-cache.jsonl` | justesse de chaque champ de chaque document du test | hors git |
| `relance/` | résultat, sorties et journaux de la commande relancée | versionné |

L'état de l'API (soumissions utilisées, fin déclarée) est relu depuis ces journaux à chaque démarrage : un redémarrage ne remet pas le compteur à zéro.
