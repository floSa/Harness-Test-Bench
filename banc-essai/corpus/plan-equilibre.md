# Équilibre du plan du corpus

Généré par `plan.py` (graine fixe). Agrégats seulement : aucune valeur, aucun identifiant de document du test caché ni de la relance.

## Composition

| Critère | fourni | test | relance |
|---|---|---|---|
| Documents | 35 | 15 | 10 |
| Style grille | 9 | 4 | 3 |
| Style classique | 9 | 2 | 0 |
| Style compact | 9 | 2 | 2 |
| Style recit | 8 | 2 | 2 |
| Style reserve | 0 | 5 | 3 |
| Langue fr | 19 | 8 | 5 |
| Langue en | 16 | 7 | 5 |
| Prestataires distincts | 8 | 7 | 4 |
| Documents d'un prestataire vu | 35 | 4 | 0 |
| Documents d'une marque vue | 35 | 5 | 0 |
| Type doseuse | 10 | 5 | 5 |
| Type pompe | 11 | 4 | 3 |
| Type remplisseuse | 7 | 3 | 1 |
| Type pipette | 7 | 3 | 1 |

## Emplacements par champ (tous jeux)

Effectifs sur 60 documents. Case vide : emplacement non prévu pour ce champ.

| Champ | formulaire | tableau | phrase | paragraphe | schema | logo | plaque | tampon | calcul | absent |
|---|---|---|---|---|---|---|---|---|---|---|
| `machine` | 36 |  | 9 | 15 |  |  |  |  |  |  |
| `constructeur` | 33 |  | 7 | 8 |  | 12 |  |  |  |  |
| `numero_serie` | 28 |  | 5 | 8 |  |  | 7 |  |  | 12 |
| `site` | 31 |  | 5 | 12 |  |  |  |  |  | 12 |
| `reference_rapport` | 55 |  | 5 |  |  |  |  |  |  |  |
| `date_intervention` | 28 | 5 | 12 | 15 |  |  |  |  |  |  |
| `date_validation` | 24 |  | 7 | 5 |  |  |  | 16 |  | 8 |
| `volume_dose_ml` |  | 28 | 8 | 8 | 7 |  |  |  | 9 |  |
| `volume_nominal_ml` | 9 | 31 | 5 | 8 | 7 |  |  |  |  |  |
| `tolerance_ml` | 4 | 33 | 7 | 8 |  |  |  |  |  | 8 |
| `debit_ml_min` |  | 28 | 7 | 8 | 9 |  |  |  |  | 8 |
| `pression_bar` |  | 28 | 7 | 8 | 9 |  |  |  |  | 8 |
| `reference_piece` |  | 31 | 5 | 12 |  |  |  |  |  | 12 |
| `technicien` | 28 |  | 9 | 15 |  |  |  |  |  | 8 |
| `statut` | 29 |  | 16 | 15 |  |  |  |  |  |  |

## Emplacements par jeu (toutes valeurs)

| Emplacement | fourni | test | relance |
|---|---|---|---|
| formulaire | 176 (34 %) | 76 (34 %) | 53 (35 %) |
| tableau | 106 (20 %) | 46 (20 %) | 32 (21 %) |
| phrase | 66 (13 %) | 28 (12 %) | 20 (13 %) |
| paragraphe | 88 (17 %) | 37 (16 %) | 20 (13 %) |
| schema | 18 (3 %) | 8 (4 %) | 6 (4 %) |
| logo | 7 (1 %) | 3 (1 %) | 2 (1 %) |
| plaque | 4 (1 %) | 2 (1 %) | 1 (1 %) |
| tampon | 9 (2 %) | 4 (2 %) | 3 (2 %) |
| calcul | 5 (1 %) | 2 (1 %) | 2 (1 %) |
| absent | 46 (9 %) | 19 (8 %) | 11 (7 %) |

## Pièges par jeu

| Piège | Part visée | fourni | test | relance |
|---|---|---|---|---|
| scan | 20 % des documents | 8 (23 %) | 4 (27 %) | 3 (30 %) |
| version_remplacee | 30 % des documents | 11 (31 %) | 5 (33 %) | 4 (40 %) |
| tolerance_en_pourcent | 30 % des documents | 11 (31 %) | 5 (33 %) | 4 (40 %) |
| redacteur_autre | 30 % des documents | 11 (31 %) | 5 (33 %) | 4 (40 %) |
| conflit_regle | 10 % des documents | 4 (11 %) | 2 (13 %) | 2 (20 %) |
| valeur_barree | 5 % des documents | 2 (6 %) | 1 (7 %) | 1 (10 %) |
| erratum | 5 % des documents | 2 (6 %) | 1 (7 %) | 1 (10 %) |
| synonyme_cle | 30 % des valeurs éligibles | 110 | 48 | 34 |
| unite_a_convertir | 25 % des valeurs éligibles | 38 | 17 | 11 |

## Répartition par style (jeu fourni et test)

| Critère | grille | classique | compact | recit | reserve |
|---|---|---|---|---|---|
| Documents | 13 | 11 | 11 | 10 | 5 |
| Valeurs en phrase (moyenne par document) | 2,0 | 1,5 | 2,1 | 1,8 | 2,2 |
| Valeurs en paragraphe (moyenne par document) | 2,5 | 2,9 | 2,4 | 2,3 | 2,4 |
| Valeurs en schema (moyenne par document) | 0,5 | 0,5 | 0,5 | 0,7 | 0,6 |
| Valeurs en absent (moyenne par document) | 1,3 | 1,1 | 1,6 | 1,4 | 0,8 |
| Valeurs en calcul (moyenne par document) | 0,2 | 0,2 | 0,1 | 0,1 | 0,2 |
| Valeurs en tampon (moyenne par document) | 0,2 | 0,3 | 0,3 | 0,3 | 0,2 |
| Valeurs en logo (moyenne par document) | 0,2 | 0,2 | 0,2 | 0,3 | 0,2 |
| scan | 3 | 2 | 3 | 3 | 1 |
| version_remplacee | 4 | 3 | 3 | 4 | 2 |
| conflit_regle | 2 | 1 | 1 | 1 | 1 |
| valeur_barree | 0 | 1 | 1 | 0 | 1 |
| erratum | 0 | 1 | 1 | 0 | 1 |

## Charge des documents

Charge : somme des difficultés d'un document (emplacement hors défaut : 1 à 1,5 ; piège : 1).

| Critère | fourni | test | relance |
|---|---|---|---|
| Minimum | 11,5 | 12,5 | 13,0 |
| Moyenne | 14,4 | 14,6 | 14,6 |
| Maximum | 18,5 | 18,5 | 16,0 |
| Pièges par valeur, maximum | 2 | 2 | 2 |
