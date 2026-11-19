# Cahier des charges du corpus

Version 2, 19 novembre 2026, **proposition à valider avec les exemples** (`banc-essai/corpus/exemples/`). Remplace la version 1 (historique git). Le générateur de la version 1 est conservé dans `banc-essai/corpus/v1/` jusqu'au portage de ses mises en page.

## 1. Principe

Rapports d'intervention fictifs sur des équipements de dosage (doseuses, pompes doseuses, remplisseuses, pipettes automatiques), en PDF de 4 à 7 pages, en français et en anglais. Tout est fictif : entreprises, marques, machines, logos, personnes. Les réponses sont tirées avant le rendu, puis recalculées à partir de ce qui est écrit (unité et arrondi affichés) : elles sont connues sans erreur.

Le corpus teste trois capacités : trouver la bonne valeur parmi des valeurs voisines, ne rien inventer quand la valeur manque, et généraliser à des noms et des mises en page jamais vus.

## 2. Volumes

| Jeu | Documents | Accès du harnais |
|---|---|---|
| Fourni | 35, avec vérité terrain | libre |
| Test caché | 15 | API de soumission seulement |
| Relance | 10 | jamais ; sert à relancer le workflow livré (protocole, section 6) |

Total : 60 documents, au-dessus du minimum de 50.

## 3. Noms et généralisation

| Règle | Mise en œuvre |
|---|---|
| Noms inventés | mots générés à partir de syllabes (`univers.py`), graine fixe |
| Univers séparés | marques et prestataires du test et de la relance majoritairement absents du jeu fourni |
| Prestataires récurrents | un prestataire du jeu fourni signe plusieurs rapports, toujours avec la même mise en page |
| Rôles croisés | un même mot est marque dans un document, famille de machines ou nom de prestataire dans un autre (exemple : « Ostiovan » constructeur de l'exemple 1, machine « Ostiovan 600 » de l'exemple 2) |
| Étiquette | chaque nom porte `vu` ou `inedit` selon sa présence dans le jeu fourni |

## 4. Mises en page

| Style | Description | Jeu |
|---|---|---|
| Grille | page d'entrée en cases de tailles variées (référence, indice, dates, visas, révisions), tableau de mesures à entrées multiples | fourni, test |
| Classique | formulaire à deux colonnes, tableaux simples | fourni, test |
| Compact anglais | lignes clé-valeur, nombres anglais | fourni, test |
| Texte abondant | récit long, tableau coupé entre deux pages | fourni, test |
| Réservé | mise en page absente du jeu fourni (à concevoir) | test, relance |

Dans un style, la disposition dépend du prestataire (ordre et largeur des cases, police, format des nombres, des dates et place des unités).

## 5. Champs à extraire

Un JSON par document, avec exactement ces 15 clés ; `null` quand la valeur est absente.

| Clé | Type | Valeur qui fait foi | Leurres présents |
|---|---|---|---|
| `machine` | texte | modèle de l'équipement contrôlé | type du moteur, équipement voisin, ligne du client |
| `constructeur` | texte | fabricant de l'équipement | prestataire, marque du moteur, marque des instruments |
| `numero_serie` | texte | n° de série de l'équipement | n° du moteur, des instruments, d'inventaire |
| `site` | texte | site du client où l'équipement est installé | ville du siège du client, adresse du prestataire |
| `reference_rapport` | texte | référence du rapport en vigueur | version annulée, n° de commande, n° d'affaire |
| `date_intervention` | date ISO | jour de l'intervention | demande, incident, prochaine visite |
| `date_validation` | date ISO | approbation finale du rapport | rédaction, vérification, révision, impression, étalonnage des instruments |
| `volume_dose_ml` | nombre, ml | dose moyenne après réglage, toutes têtes et tous essais | essais un par un, moyenne d'une tête, avant réglage, réservoir, circuit |
| `volume_nominal_ml` | nombre, ml | volume de consigne | gamme du modèle |
| `tolerance_ml` | nombre, ml | tolérance admise ; en % elle se rapporte au nominal | incertitude de mesure |
| `debit_ml_min` | nombre, ml/min | débit mesuré après réglage | avant réglage, maximal, équipement voisin, synthèse provisoire |
| `pression_bar` | nombre, bar | pression de service mesurée après réglage | avant réglage, maximale, tarage de soupape, réseau d'air |
| `reference_piece` | texte | pièce effectivement remplacée | pièces contrôlées, commandées, proposées au devis |
| `technicien` | texte | intervenant responsable côté prestataire | accompagnant, rédacteur, vérificateur, demandeur et signataire client |
| `statut` | `conforme` / `non_conforme` / `a_revoir` | décision finale | statut d'arrivée, cases non cochées |

## 6. Pièges

Chaque valeur reçoit 0 à 2 pièges tirés au sort ; les pièges systématiques et l'étiquette `scan` n'entrent pas dans cette limite. Parts calculées par jeu, arrondies au plus proche, tirées en nombre exact.

| Famille | Piège | Règle | Part visée |
|---|---|---|---|
| Emplacement | `recit_seul` | valeur seulement dans une phrase | 12 % des valeurs |
| | `schema_seul` | valeur seulement dans le schéma (image) | 8 % des valeurs numériques |
| | `tampon_seul` | date de validation seulement dans un tampon (image) | 20 % des documents |
| | `logo_seul` | constructeur seulement dans son logo | 20 % des documents |
| Absence | `champ_absent` | réponse `null`, avec un voisin tentant (n° du moteur, pression maximale, pièces commandées) et des marqueurs variés (vide, « — », « illisible », « n.c. », « n.m. ») | 10 % des valeurs |
| Doublons | `valeur_barree` | valeur imprimée barrée, valeur juste écrite à la main (image) | 5 % des documents |
| | `erratum` | le récit rectifie une valeur du tableau | 5 % des documents |
| | `conflit_regle` | synthèse provisoire en page d'entrée, une phrase désigne le tableau qui fait foi | 10 % des documents |
| | `version_remplacee` | « annule et remplace » une ancienne référence | 30 % des documents |
| Calcul | `moyenne_a_calculer` | moyenne des essais non écrite | 15 % des documents |
| | `tolerance_en_pourcent` | tolérance en % du nominal | 30 % des documents |
| | `unite_a_convertir` | µl, cl, L ; L/h, ml/s, L/min ; mbar, kPa, psi | 25 % des valeurs numériques |
| Forme | `synonyme_cle` | libellé synonyme (« EMT », « Set point », « OEM ») | 30 % des valeurs |
| | `format_nombre` | séparateurs selon le prestataire : `1 250,5`, `1250,5`, `1.250,5`, `1,250.5`, `1250.5`, `1'250.5` | selon le prestataire |
| | dates | `14/03/2026`, `2026-03-14`, `14.03.26`, `14 mars 2026`, `March 14, 2026` (format américain réservé aux prestataires anglophones) | selon le prestataire |
| | place de l'unité | dans la case, dans l'en-tête, dans une colonne, dans une note sous le tableau | selon le prestataire |
| Systématique | zones ambiguës | plaque du moteur (image), instruments de mesure, équipement voisin, réseau d'air, pièces et devis | tous les documents |
| | personnes et dates multiples | 5 personnes, 8 dates par document | tous les documents |
| Lecture visuelle | `scan` | une page tramée, bruitée, légèrement tournée | 20 % des documents |
| | cases à cocher | statut indiqué par une croix tracée, sans texte | style grille |

Une écriture ambiguë comme « 1,250 » n'apparaît que si la langue et l'ordre de grandeur la tranchent.

## 7. Vérité terrain et annotation

| Fichier | Contenu |
|---|---|
| `verite/<id>.json` | par champ : valeur normalisée, emplacement, règle qui fait foi, pièges, écritures (texte, page, cadre, texte ou image), leurres (texte, page, cadre, raison) ; par document : prestataire, formats, unités écrites, page scannée |
| `reponses/<id>.json` | les 15 valeurs attendues |
| `annotations/<id>.pdf` | copie du document : cadres verts (valeur juste ; pointillés pour les essais à moyenner), orange (valeur barrée), rouges numérotés (leurres) ; page de synthèse |
| `verite.csv` | toutes les valeurs du corpus, une ligne par document et par champ |

Le cadre de chaque écriture en texte est vérifié dans le PDF (recherche de la chaîne dans la page) ; une écriture introuvable est une erreur de génération.

## 8. Notation

| Type | Règle |
|---|---|
| Texte | égal après normalisation (casse, espaces, accents) |
| Nombre | égal à 0,01 près dans l'unité de la clé ; les valeurs voisines d'un même champ diffèrent d'au moins 0,02 |
| Date | égale au format ISO |
| `null` attendu | juste seulement si la réponse est `null` |
| Taux d'invention | part des réponses non nulles là où `null` est attendu (à ajouter au protocole) |

Scores détaillés par clé, par famille de pièges, par style, par prestataire et par nom vu ou inédit.

## 9. Ontologie (recette « avec aide »)

`banc-essai/recettes/avec-aide/ontologie.md` : pour chaque clé, définition métier, unité et conversions, synonymes, règle de choix entre valeurs voisines (colonne « valeur qui fait foi » de la section 5, détaillée).

La recette « sans aide » donne au moins une définition d'une ligne par clé : sans elle, `technicien` ou `date_validation` ne sont pas décidables.

## 10. Livrables de la génération

- `banc-essai/corpus/generer.py` et ses modules, graine fixe ;
- `banc-essai/corpus/fourni/` : 35 PDF, réponses, vérité, annotations ;
- `banc-essai/corpus/test-cache/` et `relance/` : hors git ;
- `banc-essai/corpus/empreintes.sha256` : empreintes de tous les fichiers générés ;
- `banc-essai/recettes/avec-aide/ontologie.md`.
