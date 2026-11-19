# Rapport d'essai : c1-02-goose-avec-aide

## Versions

| Élément | Valeur |
|---|---|
| Tâche | extraction |
| corpus_empreintes_sha256 | `1401ebea2236bbb312d7ed460119a15f4530367a96b0d091cf5619b930a338c0` |
| evaluateur_commit | `389e943` |

## Résultat

| Mesure | Valeur |
|---|---|
| Score final (soumission déclarée) | 99,6 % |
| Meilleur score | 99,6 % |
| Score de validation annoncé | 99,5 % |
| Écart annoncé moins test | -0,1 % |
| Soumissions acceptées | 1 |
| Soumissions refusées (format) | 0 |
| Soumissions refusées (limite) | 0 |
| Soumission finale | 1 |
| Fin déclarée | oui |
| Taux d'invention | 0,0 % |
| Score sur le style jamais vu | 98,7 % |
| Relance : score | 98,7 % |
| Relance : JSON produits | 10 sur 10 |
| Relance : durée par document | 19.37 s |
| Relance : appels au modèle | 11 |
| Relance : coût par document | 0.001966 $ |
| Relance : fichiers refusés (lien, fichier spécial) | 0 |
| Relance : code de retour | 0 |

## Construction

| Mesure | Valeur |
|---|---|
| Harnais | goose |
| Version du harnais | goose 1.60.1 |
| Modèle (journal) | openrouter/deepseek/deepseek-v4.1-flash-1017 |
| Fournisseur (journal) | Pearl Research |
| Recette | avec-aide |
| Début | 2026-11-19T23:59:34+01:00 |
| Fin | 2026-11-20T00:29:06+01:00 |
| Durée totale | 1771.9 s |
| Garde-fou atteint | non |
| Code de retour du harnais | 0 |
| Appels au modèle | 299 |
| Appels échoués | 0 |
| Appels refusés pour quota (429) | 0 |
| Temps d'attente après un 429 | 0.0 s |
| Appels avec image | 0 |
| Jetons d'entrée | 5065416 |
| Dont jetons lus dans le cache | 4294272 |
| Jetons de sortie | 854763 |
| Temps dans le modèle | 1584.0 s |
| Coût calculé par le relais | 0.30654 $ |
| Coût facturé par OpenRouter | 0.30654 $ |
| Dépense de la clé (LiteLLM) | 0.3065404160000002 $ |
| Demandes réseau (mandataire PyPI) | 38 |
| Demandes réseau refusées | 30 |

## Soumissions

| Critère | Requête 1 |
|---|---|
| Heure | 2026-11-20T00:24:53+01:00 |
| Statut | acceptee |
| Numéro | 1 |
| Score | 99,6 % |

## Scores détaillés de la soumission finale

### Clé

| Clé | Champs | Justes | Score |
|---|---|---|---|
| constructeur | 15 | 15 | 100,0 % |
| date_intervention | 15 | 15 | 100,0 % |
| date_validation | 15 | 15 | 100,0 % |
| debit_ml_min | 15 | 14 | 93,3 % |
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
| calcul | 24 | 23 | 95,8 % |
| doublons | 9 | 8 | 88,9 % |
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
| unite_a_convertir | 17 | 16 | 94,1 % |
| valeur_barree | 1 | 0 | 0,0 % |
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
| tableau | 46 | 45 | 97,8 % |
| tampon | 4 | 4 | 100,0 % |

### Style de mise en page

| Style de mise en page | Champs | Justes | Score |
|---|---|---|---|
| classique | 30 | 30 | 100,0 % |
| compact | 30 | 30 | 100,0 % |
| grille | 60 | 60 | 100,0 % |
| recit | 30 | 30 | 100,0 % |
| reserve | 75 | 74 | 98,7 % |

### Prestataire vu ou inédit

| Prestataire vu ou inédit | Champs | Justes | Score |
|---|---|---|---|
| inedit | 165 | 164 | 99,4 % |
| vu | 60 | 60 | 100,0 % |

### Marque vue ou inédite

| Marque vue ou inédite | Champs | Justes | Score |
|---|---|---|---|
| inedite | 150 | 149 | 99,3 % |
| vue | 75 | 75 | 100,0 % |

### Langue

| Langue | Champs | Justes | Score |
|---|---|---|---|
| en | 105 | 104 | 99,1 % |
| fr | 120 | 120 | 100,0 % |

### Prestataire

| Prestataire | Champs | Justes | Score |
|---|---|---|---|
| Fennet Technical Services | 45 | 44 | 97,8 % |
| Mabindor Mesure et Contrôle | 30 | 30 | 100,0 % |
| Nevevex Calibration Ltd | 30 | 30 | 100,0 % |
| Riliovane Services | 30 | 30 | 100,0 % |
| Sarolor Techniques | 30 | 30 | 100,0 % |
| Verelrix Ingénierie | 30 | 30 | 100,0 % |
| Vexitik Services Ltd | 30 | 30 | 100,0 % |
