# Goldset : faire tourner le banc sur un jeu de PDF et de réponses attendues

Un goldset est un jeu de documents PDF accompagné, pour chaque document, des valeurs à en extraire. Cette page explique comment le placer, l'importer, valider la façon de le noter, et lancer un essai dessus.

## 1. Forme attendue

À la racine du dépôt, dans un dossier `goldset/` (ignoré par git, jamais commité) :

```text
goldset/
├── ground_truth.json              tous les documents (facultatif : sert au recoupement)
└── split/
    ├── train/*.pdf
    ├── val/*.pdf
    ├── test/*.pdf
    ├── train_ground_truth.json    valeurs attendues des PDF de train/
    ├── val_ground_truth.json
    └── test_ground_truth.json
```

Un fichier de vérité associe à chaque PDF ses valeurs. Formes reconnues par l'importateur :

| Forme | Exemple |
|---|---|
| objet indexé par nom de fichier | `{"facture_12.pdf": {"montant": 120.5, "date": "03/02/2026"}}` |
| même chose sans l'extension | `{"facture_12": {...}}` |
| liste d'objets avec une clé de nom de fichier | `[{"file_name": "facture_12.pdf", "montant": 120.5}]` (clés reconnues : `file_name`, `filename`, `file`, `fichier`, `document`, `pdf`, `name`, `nom`, `id`, `path`, `source`...) |
| liste sous une clé unique | `{"documents": [ ... ]}` |
| valeurs enveloppées | `{"facture_12.pdf": {"fields": {...}}}` (enveloppes reconnues : `fields`, `champs`, `ground_truth`, `labels`, `annotations`, `values`, `data`...) |

Toute autre forme arrête l'import avec un message qui le dit. Il faut alors adapter la fonction `lire_verite()` de [`banc-essai/corpus/importer_goldset.py`](../corpus/importer_goldset.py) (section 7), sans jamais modifier le goldset lui-même.

Les valeurs peuvent être imbriquées (`{"client": {"nom": ..., "ville": ...}}`) : chaque valeur est alors désignée par son chemin pointé (`client.nom`).

## 2. Répartition dans le banc

| Jeu du goldset | Jeu du banc | Rôle | Visible par le harnais |
|---|---|---|---|
| `train` | `fourni` | PDF et réponses donnés au harnais pour construire son workflow | oui |
| `val` | `fourni` | PDF et réponses donnés au harnais, pour valider son workflow | oui |
| `test` | `test-cache`, puis `relance` | test caché, noté par l'API de soumission (5 soumissions) ; après la fin de l'essai, le workflow livré y est relancé sans le harnais : note de référence | PDF seulement, réponses jamais |

`relance/` est alors une copie de `test-cache/` : la relance juge le workflow seul sur des documents dont le harnais n'a vu que le score global. Autre répartition possible : option `--repartition` de l'importateur, par exemple `train=fourni,val=test-cache,test=relance` (relance sur un jeu jamais vu, au prix d'un jeu fourni plus petit).

## 3. Importer

```bash
python3 banc-essai/corpus/importer_goldset.py
```

Options : `--source` (défaut `goldset/`), `--destination` (défaut `banc-essai/corpus/goldset/`, qui doit être ignoré par git, sinon l'import s'arrête), `--repartition`, `--schema-neuf`.

Étapes de l'import :

| Étape | Ce qui est fait | Effet en cas de problème |
|---|---|---|
| 1. Lecture | trois jeux, fichiers de vérité, forme reconnue | arrêt si forme inconnue ou dossier manquant |
| 2. Appariement | PDF et entrées de vérité par nom (sans extension, sans casse) | PDF sans vérité et vérité sans PDF : écartés et listés |
| 3. Contrôles | fichier qui commence bien comme un PDF ; doublon de nom ou de contenu entre jeux ; recoupement avec `ground_truth.json` | doublon : arrêt (un document du test présent dans le jeu fourni fausserait tout) ; écart avec `ground_truth.json` : signalé |
| 4. Analyse des champs | types rencontrés, formats de date, nombres écrits en texte, valeurs distinctes | schéma proposé |
| 5. Conversion | dates en `AAAA-MM-JJ`, nombres écrits en texte en nombres JSON, booléens, champ absent en `null` | échecs de conversion comptés par champ |
| 6. Écriture | `doc-XXX.pdf` et `reponses/doc-XXX.json` par jeu, `correspondance.json` | identifiants opaques : ni le nom d'origine ni le jeu ne transparaissent |
| 7. Contrôle de la notation | réponses attendues notées contre elles-mêmes : 100 % et aucune erreur de format ; réponse altérée : moins de 100 % | non conforme : à corriger avant tout essai |
| 8. Rapport | `banc-essai/corpus/goldset/rapport-import.md` | à lire en entier |

Code de sortie : 0 si tout est conforme et qu'aucune conversion n'a échoué, 2 sinon, 1 si l'import s'est arrêté.

Résultat :

```text
banc-essai/corpus/goldset/
├── schema.json            description des champs et règles de notation
├── rapport-import.md      constats, analyse des champs, contrôle de la notation
├── correspondance.json    doc-XXX -> jeu et fichier d'origine
├── fourni/                doc-XXX.pdf, reponses/doc-XXX.json
├── test-cache/
└── relance/
```

## 4. Valider le schéma (décision humaine)

L'import écrit un schéma proposé, marqué `"valide": false`. Exemple :

```json
{
  "version": 1,
  "valide": false,
  "description": "À compléter : nature des documents et de l'information recherchée.",
  "champs": {
    "client.nom": {"type": "texte", "description": ""},
    "montant":    {"type": "nombre", "tolerance": 0.01, "description": ""},
    "date":       {"type": "date", "ordre_jour_mois": "jm", "description": ""},
    "statut":     {"type": "enum", "valeurs": ["ouvert", "clos"], "description": ""},
    "lignes":     {"type": "liste", "description": ""}
  }
}
```

| Type | Règle de notation | Forme de la réponse attendue |
|---|---|---|
| `texte` | égal après normalisation (casse, accents, espaces) | chaîne |
| `enum` | une des `valeurs`, égale après normalisation | chaîne de la liste |
| `nombre` | écart au plus égal à `tolerance` (0,01 par défaut) | nombre JSON |
| `date` | chaîne égale | `AAAA-MM-JJ` |
| `booleen` | égal | `true` ou `false` |
| `liste` | éléments comparés sans ordre ; crédit partiel = F1 entre éléments répondus et attendus | liste JSON |
| toute valeur attendue `null` | juste seulement si la réponse est `null` | `null` |

À relire et décider, champ par champ, en s'aidant du tableau « Champs » de `rapport-import.md` :

1. le type : un identifiant fait de chiffres (numéro de contrat, code postal) doit rester `texte`, sinon ses zéros de tête disparaissent ;
2. la tolérance des nombres, selon leur unité (0,01 pour des euros, 0,5 pour des kilogrammes arrondis...) ;
3. l'ordre jour et mois des dates (`ordre_jour_mois` : `jm` ou `mj`), quand le rapport dit qu'il n'a pas pu le déterminer ;
4. la liste des valeurs des `enum`, ou le passage en `texte` si la liste n'est pas fermée ;
5. une `description` par champ, et la `description` générale des documents : elles sont reprises telles quelles dans les consignes données aux harnais.

Puis mettre `"valide": true` et relancer l'import : les valeurs sont alors converties selon le schéma validé, qui n'est plus jamais écrasé (sauf `--schema-neuf`).

## 5. Générer les consignes

```bash
python3 banc-essai/corpus/consignes_goldset.py
```

Remplit [`banc-essai/recettes/goldset/consignes.modele.md`](../recettes/goldset/consignes.modele.md) avec la description, le tableau des champs, la structure de la réponse, les règles de notation, la carte graphique détectée et la vision du modèle (`modele.env`). Résultat : `banc-essai/corpus/goldset/recette/consignes.md`, copié dans l'espace de chaque essai. Refus si le schéma n'est pas validé.

## 6. Lancer un essai

```bash
banc-essai/cage/lancer.sh <harnais> goldset --essai <nom>
```

Le lanceur refuse de partir si le schéma n'est pas validé ou si les consignes manquent. Un autre goldset importé ailleurs se choisit par `BANC_GOLDSET=<dossier importé>`. Les résultats vont dans `banc-essai/resultats-goldset/<nom>/`, hors git : la trace d'un harnais recopie le texte des documents. Déroulé complet : [lancer-un-essai.md](lancer-un-essai.md).

## 7. Adapter l'importateur à une forme non prévue

| Cas | Où intervenir dans `importer_goldset.py` |
|---|---|
| forme du fichier de vérité inconnue | `lire_verite()` : renvoyer `{nom du PDF: objet des valeurs}` |
| clé de nom de fichier non reconnue | ajouter le nom à `CLES_NOM` |
| enveloppe non reconnue | ajouter le nom à `ENVELOPPES` |
| format de date non reconnu | ajouter une ligne à `FORMATS_DATE` |
| arborescence différente (pas de `split/`) | `lire_source()` |

Après toute adaptation : relancer les tests (`uv run --project banc-essai/evaluation pytest`), en ajoutant un cas à `banc-essai/evaluation/tests/test_goldset.py` (fonction `goldset()`, paramètre `forme`), puis relancer l'import.

## 8. Goldset de démonstration

Pour essayer toute la chaîne sans les données de l'entreprise :

```bash
python3 banc-essai/corpus/goldset_demo.py
python3 banc-essai/corpus/consignes_goldset.py --goldset banc-essai/corpus/demo/import
BANC_GOLDSET=banc-essai/corpus/demo/import banc-essai/cage/lancer.sh pi goldset --essai demo-pi
```

Le goldset de démonstration reprend les 35 rapports publics du corpus (15 train, 10 val, 10 test), sous des formes volontairement hétérogènes : équipement en objet imbriqué, dates `JJ/MM/AAAA`, tolérance écrite en texte avec une virgule, vérité en liste d'objets. Vérifié le 27/11/2026 : les 35 réponses importées sont identiques aux réponses d'origine du corpus, les PDF aussi, et le contrôle de la notation est conforme sur les trois jeux.
