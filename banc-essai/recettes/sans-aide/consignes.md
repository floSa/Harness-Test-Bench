# Extraction de données dans des rapports d'intervention

## Tâche

Construire un workflow qui lit des rapports d'intervention en PDF (équipements de dosage : doseuses, pompes doseuses, remplisseuses, pipettes automatiques ; en français ou en anglais) et écrit, pour chaque document, un fichier JSON avec les 15 valeurs ci-dessous.

Le dossier `fourni/` contient 35 rapports (`fourni/doc-XXX.pdf`) et leurs réponses attendues (`fourni/reponses/doc-XXX.json`). Leur usage est libre : entraînement, validation, découpe au choix.

Un jeu de test caché de 15 autres rapports n'est accessible que par l'API de soumission. Ses noms de prestataires, de marques et de machines, et une partie de ses mises en page, sont absents du dossier `fourni/`.

Aucune contrainte de méthode : bibliothèques au choix (installées depuis PyPI), lecture du texte, OCR, vision du modèle, règles, appels au modèle, en combinaison libre.

## Clés à extraire

| Clé | Type | Définition |
|---|---|---|
| `machine` | texte | modèle de l'équipement contrôlé |
| `constructeur` | texte | fabricant de l'équipement contrôlé |
| `numero_serie` | texte | numéro de série de l'équipement contrôlé |
| `site` | texte | site du client où l'équipement est installé |
| `reference_rapport` | texte | référence du rapport en vigueur |
| `date_intervention` | date | jour de l'intervention |
| `date_validation` | date | date de l'approbation finale du rapport |
| `volume_dose_ml` | nombre, ml | volume de dose moyen mesuré après réglage |
| `volume_nominal_ml` | nombre, ml | volume de consigne de l'équipement |
| `tolerance_ml` | nombre, ml | tolérance admise sur le volume de dose |
| `debit_ml_min` | nombre, ml/min | débit mesuré après réglage |
| `pression_bar` | nombre, bar | pression de service mesurée après réglage |
| `reference_piece` | texte | référence de la pièce remplacée pendant l'intervention |
| `technicien` | texte | technicien responsable de l'intervention, côté prestataire |
| `statut` | `conforme`, `non_conforme` ou `a_revoir` | décision finale sur l'équipement |

## Format de sortie

Un fichier `<identifiant>.json` par document (`doc-061.pdf` donne `doc-061.json`), avec exactement les 15 clés :

- texte : la valeur telle qu'écrite dans le document ;
- date : `AAAA-MM-JJ` ;
- nombre : un nombre JSON (pas une chaîne), converti dans l'unité de la clé ;
- valeur absente du document : `null`.

Exemple : `fourni/reponses/doc-001.json`.

Notation : texte égal après normalisation de la casse, des espaces et des accents ; nombre égal à 0,01 près ; date égale ; quand `null` est attendu, seule la réponse `null` est juste. Le score est la part des champs justes.

## Workflow à livrer

Une commande unique, lancée depuis ce dossier, qui prend un dossier de PDF et un dossier de sortie :

```
<commande> {entree} {sortie}
```

Elle sera relancée telle quelle, hors de cet environnement, sur des rapports neufs. Elle ne doit dépendre d'aucun fichier hors de ce dossier, à part les paquets qu'elle installe elle-même.

## API de soumission

Adresse : variable `BANC_API` (par défaut `http://127.0.0.1:8765`). Le client `soumettre.py` n'utilise que la bibliothèque standard.

| Commande | Effet |
|---|---|
| `python soumettre.py documents test/` | télécharge les 15 PDF du test caché dans `test/` (sans les réponses) |
| `python soumettre.py soumettre sorties/` | envoie un dossier de `<identifiant>.json` (un par document du test) ; renvoie le score global |
| `python soumettre.py etat` | soumissions utilisées et restantes |
| `python soumettre.py fin ...` | déclaration de fin (ci-dessous) |

**5 soumissions au maximum.** Une soumission au mauvais format (document manquant, clé manquante, nombre écrit en chaîne, date hors format) est refusée avec le détail des erreurs et ne compte pas. Toute soumission est journalisée.

## Fin

Terminer par la déclaration de fin :

```
python soumettre.py fin --soumission N --score-validation X --commande "<commande> {entree} {sortie}"
```

- `N` : la soumission retenue comme finale ;
- `X` : le score attendu sur le test caché, mesuré sur les documents fournis gardés pour la validation (entre 0 et 1) ;
- la commande du workflow, avec `{entree}` et `{sortie}`.
