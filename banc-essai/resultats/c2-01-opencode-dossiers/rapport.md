# Rapport d'essai : c2-01-opencode-dossiers

## Versions

| Élément | Valeur |
|---|---|
| Tâche | dossiers |
| corpus_empreintes_sha256 | `1401ebea2236bbb312d7ed460119a15f4530367a96b0d091cf5619b930a338c0` |
| evaluateur_commit | `5f4de58` |

## Résultat

| Mesure | Valeur |
|---|---|
| Score final (soumission déclarée) | 99,4 % |
| Meilleur score | 99,4 % |
| Score de validation annoncé | 99,0 % |
| Écart annoncé moins test | -0,4 % |
| Soumissions acceptées | 4 |
| Soumissions refusées (format) | 0 |
| Soumissions refusées (limite) | 0 |
| Soumission finale | 4 |
| Fin déclarée | oui |
| Dossiers entièrement justes | 9 sur 12 |
| Taux d'invention | 0,0 % |
| Relance : score | 99,4 % |
| Relance : dossiers entièrement justes | 6 sur 8 |
| Relance : JSON produits | 8 sur 8 |
| Relance : durée par document | 12.29 s |
| Relance : appels au modèle | 45 |
| Relance : coût par document | 0.005644 $ |
| Relance : fichiers refusés (lien, fichier spécial) | 0 |
| Relance : code de retour | 0 |

## Construction

| Mesure | Valeur |
|---|---|
| Harnais | opencode |
| Version du harnais | opencode 1.19.6 |
| Modèle (journal) | openrouter/deepseek/deepseek-v4.1-flash-1017 |
| Fournisseur (journal) | Pearl Research |
| Recette | dossiers |
| Début | 2026-11-24T06:18:12+01:00 |
| Fin | 2026-11-24T07:20:13+01:00 |
| Durée totale | 3721.3 s |
| Garde-fou atteint | non |
| Code de retour du harnais | 0 |
| Appels au modèle | 691 |
| Appels échoués | 0 |
| Appels refusés pour quota (429) | 0 |
| Temps d'attente après un 429 | 0.0 s |
| Appels avec image | 672 |
| Jetons d'entrée | 28835629 |
| Dont jetons lus dans le cache | 24943616 |
| Jetons de sortie | 1993926 |
| Temps dans le modèle | 3602.8 s |
| Coût calculé par le relais | 0.867609 $ |
| Coût facturé par OpenRouter | 0.867609 $ |
| Dépense de la clé (LiteLLM) | 0.8676092979999995 $ |
| Demandes réseau (mandataire PyPI) | 16 |
| Demandes réseau refusées | 8 |

## Soumissions

| Critère | Requête 1 | Requête 2 | Requête 3 | Requête 4 |
|---|---|---|---|---|
| Heure | 2026-11-24T06:28:35+01:00 | 2026-11-24T06:30:12+01:00 | 2026-11-24T06:46:28+01:00 | 2026-11-24T06:51:58+01:00 |
| Statut | acceptee | acceptee | acceptee | acceptee |
| Numéro | 1 | 2 | 3 | 4 |
| Score | 98,5 % | 98,5 % | 98,7 % | 99,4 % |

## Détail de la soumission finale

| Mesure | Valeur |
|---|---|
| Précision par champ | 99,4 % |
| Rappel par champ | 99,4 % |
| Interventions oubliées | 0 sur 37 |
| Dossiers dans le bon ordre | 12 sur 12 |
| Pièges inclus à tort : equipement_jumeau | 0 sur 5 |
| Pièges inclus à tort : rapport_annule | 0 sur 5 |
| Pièges inclus à tort : version_remplacee | 0 sur 8 |
| Rectificatifs : applique | 6 |

| Clé | Champs | Justes | Score |
|---|---|---|---|
| constructeur | 12 | 12 | 100,0 % |
| date_intervention | 37 | 37 | 100,0 % |
| date_validation | 37 | 37 | 100,0 % |
| debit_ml_min | 37 | 37 | 100,0 % |
| machine | 12 | 12 | 100,0 % |
| numero_serie | 12 | 12 | 100,0 % |
| pression_bar | 37 | 37 | 100,0 % |
| reference_piece | 37 | 37 | 100,0 % |
| reference_rapport | 37 | 37 | 100,0 % |
| site | 12 | 10 | 83,3 % |
| statut | 37 | 37 | 100,0 % |
| statut_actuel | 12 | 12 | 100,0 % |
| technicien | 37 | 37 | 100,0 % |
| tolerance_ml | 37 | 37 | 100,0 % |
| volume_dose_ml | 37 | 36 | 97,3 % |
| volume_nominal_ml | 37 | 37 | 100,0 % |
