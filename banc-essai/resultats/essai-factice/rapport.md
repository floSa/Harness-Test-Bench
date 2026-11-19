# Rapport d'essai : essai-factice

## Versions

| Élément | Valeur |
|---|---|
| Tâche | extraction |
| corpus_empreintes_sha256 | `1401ebea2236bbb312d7ed460119a15f4530367a96b0d091cf5619b930a338c0` |
| evaluateur_commit | `a1863e0` |

## Résultat

| Mesure | Valeur |
|---|---|
| Score final (soumission déclarée) | 12,4 % |
| Meilleur score | 12,4 % |
| Score de validation annoncé | 12,4 % |
| Écart annoncé moins test | -0,1 % |
| Soumissions acceptées | 5 |
| Soumissions refusées (format) | 1 |
| Soumissions refusées (limite) | 1 |
| Soumission déclarée finale | 2 |
| Taux d'invention | 0,0 % |
| Score sur le style jamais vu | 8,0 % |
| Relance : score | 11,3 % |
| Relance : JSON produits | 10 sur 10 |
| Relance : durée par document | 0.0 s |
| Relance : code de retour | 0 |

## Soumissions

| Critère | Requête 1 | Requête 2 | Requête 3 | Requête 4 | Requête 5 | Requête 6 | Requête 7 |
|---|---|---|---|---|---|---|---|
| Heure | 2026-11-19T14:06:28+01:00 | 2026-11-19T14:06:28+01:00 | 2026-11-19T14:06:28+01:00 | 2026-11-19T14:06:28+01:00 | 2026-11-19T14:06:28+01:00 | 2026-11-19T14:06:28+01:00 | 2026-11-19T14:06:28+01:00 |
| Statut | refusee_format | acceptee | acceptee | acceptee | acceptee | acceptee | refusee_limite |
| Numéro |  | 1 | 2 | 3 | 4 | 5 |  |
| Score |  | 12,4 % | 12,4 % | 12,4 % | 12,4 % | 12,4 % |  |

## Scores détaillés de la soumission finale

### Clé

| Clé | Champs | Justes | Score |
|---|---|---|---|
| constructeur | 15 | 0 | 0,0 % |
| date_intervention | 15 | 0 | 0,0 % |
| date_validation | 15 | 2 | 13,3 % |
| debit_ml_min | 15 | 2 | 13,3 % |
| machine | 15 | 0 | 0,0 % |
| numero_serie | 15 | 3 | 20,0 % |
| pression_bar | 15 | 2 | 13,3 % |
| reference_piece | 15 | 3 | 20,0 % |
| reference_rapport | 15 | 0 | 0,0 % |
| site | 15 | 3 | 20,0 % |
| statut | 15 | 9 | 60,0 % |
| technicien | 15 | 2 | 13,3 % |
| tolerance_ml | 15 | 2 | 13,3 % |
| volume_dose_ml | 15 | 0 | 0,0 % |
| volume_nominal_ml | 15 | 0 | 0,0 % |

### Famille de pièges

| Famille de pièges | Champs | Justes | Score |
|---|---|---|---|
| absence | 19 | 19 | 100,0 % |
| calcul | 24 | 0 | 0,0 % |
| doublons | 9 | 0 | 0,0 % |
| emplacement | 84 | 5 | 5,9 % |
| forme | 72 | 2 | 2,8 % |
| lecture_visuelle | 13 | 2 | 15,4 % |
| systematique | 93 | 8 | 8,6 % |

### Étiquette

| Étiquette | Champs | Justes | Score |
|---|---|---|---|
| absent | 19 | 19 | 100,0 % |
| cases_a_cocher | 5 | 2 | 40,0 % |
| conflit_regle | 2 | 0 | 0,0 % |
| dates_multiples | 30 | 2 | 6,7 % |
| erratum | 1 | 0 | 0,0 % |
| format_nombre | 28 | 0 | 0,0 % |
| moyenne_a_calculer | 2 | 0 | 0,0 % |
| personnes_multiples | 15 | 2 | 13,3 % |
| redacteur_autre | 5 | 0 | 0,0 % |
| scan | 8 | 0 | 0,0 % |
| synonyme_cle | 48 | 2 | 4,2 % |
| tableau_coupe | 4 | 1 | 25,0 % |
| tableau_multi_entrees | 15 | 0 | 0,0 % |
| tolerance_en_pourcent | 5 | 0 | 0,0 % |
| unite_a_convertir | 17 | 0 | 0,0 % |
| valeur_barree | 1 | 0 | 0,0 % |
| version_remplacee | 5 | 0 | 0,0 % |
| volumes_voisins | 15 | 0 | 0,0 % |
| zones_ambigues | 30 | 3 | 10,0 % |

### Emplacement

| Emplacement | Champs | Justes | Score |
|---|---|---|---|
| absent | 19 | 19 | 100,0 % |
| calcul | 2 | 0 | 0,0 % |
| formulaire | 76 | 4 | 5,3 % |
| logo | 3 | 0 | 0,0 % |
| paragraphe | 37 | 2 | 5,4 % |
| phrase | 28 | 3 | 10,7 % |
| plaque | 2 | 0 | 0,0 % |
| schema | 8 | 0 | 0,0 % |
| tableau | 46 | 0 | 0,0 % |
| tampon | 4 | 0 | 0,0 % |

### Style de mise en page

| Style de mise en page | Champs | Justes | Score |
|---|---|---|---|
| classique | 30 | 3 | 10,0 % |
| compact | 30 | 7 | 23,3 % |
| grille | 60 | 7 | 11,7 % |
| recit | 30 | 5 | 16,7 % |
| reserve | 75 | 6 | 8,0 % |

### Prestataire vu ou inédit

| Prestataire vu ou inédit | Champs | Justes | Score |
|---|---|---|---|
| inedit | 165 | 17 | 10,3 % |
| vu | 60 | 11 | 18,3 % |

### Marque vue ou inédite

| Marque vue ou inédite | Champs | Justes | Score |
|---|---|---|---|
| inedite | 150 | 19 | 12,7 % |
| vue | 75 | 9 | 12,0 % |

### Langue

| Langue | Champs | Justes | Score |
|---|---|---|---|
| en | 105 | 17 | 16,2 % |
| fr | 120 | 11 | 9,2 % |

### Prestataire

| Prestataire | Champs | Justes | Score |
|---|---|---|---|
| Fennet Technical Services | 45 | 5 | 11,1 % |
| Mabindor Mesure et Contrôle | 30 | 1 | 3,3 % |
| Nevevex Calibration Ltd | 30 | 7 | 23,3 % |
| Riliovane Services | 30 | 3 | 10,0 % |
| Sarolor Techniques | 30 | 4 | 13,3 % |
| Verelrix Ingénierie | 30 | 3 | 10,0 % |
| Vexitik Services Ltd | 30 | 5 | 16,7 % |
