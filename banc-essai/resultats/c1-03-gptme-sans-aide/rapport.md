# Rapport d'essai : c1-03-gptme-sans-aide

## Versions

| Élément | Valeur |
|---|---|
| Tâche | extraction |
| corpus_empreintes_sha256 | `1401ebea2236bbb312d7ed460119a15f4530367a96b0d091cf5619b930a338c0` |
| evaluateur_commit | `f155af3` |

## Résultat

| Mesure | Valeur |
|---|---|
| Score final (soumission déclarée) | 100,0 % |
| Meilleur score | 100,0 % |
| Score de validation annoncé | 100,0 % |
| Écart annoncé moins test | 0,0 % |
| Soumissions acceptées | 1 |
| Soumissions refusées (format) | 0 |
| Soumissions refusées (limite) | 0 |
| Soumission finale | 1 |
| Fin déclarée | oui |
| Taux d'invention | 0,0 % |
| Score sur le style jamais vu | 100,0 % |
| Relance : score | 99,3 % |
| Relance : JSON produits | 10 sur 10 |
| Relance : durée par document | 1.96 s |
| Relance : appels au modèle | 10 |
| Relance : coût par document | 0.000597 $ |
| Relance : fichiers refusés (lien, fichier spécial) | 0 |
| Relance : code de retour | 0 |

## Construction

| Mesure | Valeur |
|---|---|
| Harnais | gptme |
| Version du harnais | gptme 0.37.0 |
| Modèle (journal) | openrouter/deepseek/deepseek-v4.1-flash-1017 |
| Fournisseur (journal) | Pearl Research |
| Recette | sans-aide |
| Début | 2026-11-20T00:33:43+01:00 |
| Fin | 2026-11-20T01:08:54+01:00 |
| Durée totale | 2110.7 s |
| Garde-fou atteint | non |
| Code de retour du harnais | 0 |
| Appels au modèle | 588 |
| Appels échoués | 11 |
| Appels refusés pour quota (429) | 0 |
| Temps d'attente après un 429 | 0.0 s |
| Appels avec image | 355 |
| Jetons d'entrée | 20389931 |
| Dont jetons lus dans le cache | 18517504 |
| Jetons de sortie | 498463 |
| Temps dans le modèle | 1922.4 s |
| Coût calculé par le relais | 0.298713 $ |
| Coût facturé par OpenRouter | 0.298713 $ |
| Dépense de la clé (LiteLLM) | 0.2987127619999999 $ |
| Demandes réseau (mandataire PyPI) | 2 |
| Demandes réseau refusées | 0 |

## Soumissions

| Critère | Requête 1 |
|---|---|
| Heure | 2026-11-20T01:07:50+01:00 |
| Statut | acceptee |
| Numéro | 1 |
| Score | 100,0 % |

## Scores détaillés de la soumission finale

### Clé

| Clé | Champs | Justes | Score |
|---|---|---|---|
| constructeur | 15 | 15 | 100,0 % |
| date_intervention | 15 | 15 | 100,0 % |
| date_validation | 15 | 15 | 100,0 % |
| debit_ml_min | 15 | 15 | 100,0 % |
| machine | 15 | 15 | 100,0 % |
| numero_serie | 15 | 15 | 100,0 % |
| pression_bar | 15 | 15 | 100,0 % |
| reference_piece | 15 | 15 | 100,0 % |
| reference_rapport | 15 | 15 | 100,0 % |
| site | 15 | 15 | 100,0 % |
| statut | 15 | 15 | 100,0 % |
| technicien | 15 | 15 | 100,0 % |
| tolerance_ml | 15 | 15 | 100,0 % |
| volume_dose_ml | 15 | 15 | 100,0 % |
| volume_nominal_ml | 15 | 15 | 100,0 % |

### Famille de pièges

| Famille de pièges | Champs | Justes | Score |
|---|---|---|---|
| absence | 19 | 19 | 100,0 % |
| calcul | 24 | 24 | 100,0 % |
| doublons | 9 | 9 | 100,0 % |
| emplacement | 84 | 84 | 100,0 % |
| forme | 72 | 72 | 100,0 % |
| lecture_visuelle | 13 | 13 | 100,0 % |
| systematique | 93 | 93 | 100,0 % |

### Étiquette

| Étiquette | Champs | Justes | Score |
|---|---|---|---|
| absent | 19 | 19 | 100,0 % |
| cases_a_cocher | 5 | 5 | 100,0 % |
| conflit_regle | 2 | 2 | 100,0 % |
| dates_multiples | 30 | 30 | 100,0 % |
| erratum | 1 | 1 | 100,0 % |
| format_nombre | 28 | 28 | 100,0 % |
| moyenne_a_calculer | 2 | 2 | 100,0 % |
| personnes_multiples | 15 | 15 | 100,0 % |
| redacteur_autre | 5 | 5 | 100,0 % |
| scan | 8 | 8 | 100,0 % |
| synonyme_cle | 48 | 48 | 100,0 % |
| tableau_coupe | 4 | 4 | 100,0 % |
| tableau_multi_entrees | 15 | 15 | 100,0 % |
| tolerance_en_pourcent | 5 | 5 | 100,0 % |
| unite_a_convertir | 17 | 17 | 100,0 % |
| valeur_barree | 1 | 1 | 100,0 % |
| version_remplacee | 5 | 5 | 100,0 % |
| volumes_voisins | 15 | 15 | 100,0 % |
| zones_ambigues | 30 | 30 | 100,0 % |

### Emplacement

| Emplacement | Champs | Justes | Score |
|---|---|---|---|
| absent | 19 | 19 | 100,0 % |
| calcul | 2 | 2 | 100,0 % |
| formulaire | 76 | 76 | 100,0 % |
| logo | 3 | 3 | 100,0 % |
| paragraphe | 37 | 37 | 100,0 % |
| phrase | 28 | 28 | 100,0 % |
| plaque | 2 | 2 | 100,0 % |
| schema | 8 | 8 | 100,0 % |
| tableau | 46 | 46 | 100,0 % |
| tampon | 4 | 4 | 100,0 % |

### Style de mise en page

| Style de mise en page | Champs | Justes | Score |
|---|---|---|---|
| classique | 30 | 30 | 100,0 % |
| compact | 30 | 30 | 100,0 % |
| grille | 60 | 60 | 100,0 % |
| recit | 30 | 30 | 100,0 % |
| reserve | 75 | 75 | 100,0 % |

### Prestataire vu ou inédit

| Prestataire vu ou inédit | Champs | Justes | Score |
|---|---|---|---|
| inedit | 165 | 165 | 100,0 % |
| vu | 60 | 60 | 100,0 % |

### Marque vue ou inédite

| Marque vue ou inédite | Champs | Justes | Score |
|---|---|---|---|
| inedite | 150 | 150 | 100,0 % |
| vue | 75 | 75 | 100,0 % |

### Langue

| Langue | Champs | Justes | Score |
|---|---|---|---|
| en | 105 | 105 | 100,0 % |
| fr | 120 | 120 | 100,0 % |

### Prestataire

| Prestataire | Champs | Justes | Score |
|---|---|---|---|
| Fennet Technical Services | 45 | 45 | 100,0 % |
| Mabindor Mesure et Contrôle | 30 | 30 | 100,0 % |
| Nevevex Calibration Ltd | 30 | 30 | 100,0 % |
| Riliovane Services | 30 | 30 | 100,0 % |
| Sarolor Techniques | 30 | 30 | 100,0 % |
| Verelrix Ingénierie | 30 | 30 | 100,0 % |
| Vexitik Services Ltd | 30 | 30 | 100,0 % |
