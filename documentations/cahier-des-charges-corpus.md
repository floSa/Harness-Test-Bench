# Cahier des charges du corpus

Version 2, 19 novembre 2026, validée par l'utilisateur sur les exemples (`banc-essai/corpus/exemples/`). Remplace la version 1 (historique git).

## 1. Principe

Rapports d'intervention fictifs sur des équipements de dosage (doseuses, pompes doseuses, remplisseuses, pipettes automatiques), en PDF de 3 à 6 pages, en français et en anglais. Tout est fictif : entreprises, marques, machines, logos, personnes. Les réponses sont tirées avant le rendu, puis recalculées à partir de ce qui est écrit (unité et arrondi affichés) : elles sont connues sans erreur.

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

| Critère | Grille | Classique | Compact | Récit | Réservé |
|---|---|---|---|---|---|
| Page d'entrée | cases de tailles variées, visas, révisions | bandeau, formulaire à deux colonnes | lignes clé-valeur sur quatre colonnes | formulaire écrit en lignes de texte | A4 paysage, deux colonnes, cartouche vertical |
| Tableau de mesures | entrées multiples (têtes × essais × avant ou après), cases fusionnées | essais regroupés dans une case (« a / b / c ») | liste « paramètre, valeur » | une ligne par essai, coupé entre deux pages selon la longueur | transposé (grandeurs en colonnes) |
| Statut | cases à cocher | case du formulaire | case du formulaire | case du formulaire | cases à cocher dans le cartouche |
| Texte libre | moyen | moyen | court | abondant | moyen |
| Pages | 5 | 3 | 3 | 4 à 5 | 3 à 4 |
| Jeux | fourni, test, relance | fourni, test | fourni, test, relance | fourni, test, relance | test, relance |

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

Chaque valeur reçoit au plus 2 difficultés tirées au sort (un emplacement hors défaut compte pour une) ; les pièges systématiques et l'étiquette `scan` n'entrent pas dans cette limite. Parts calculées par jeu, arrondies au plus proche, tirées en nombre exact.

| Famille | Piège | Règle | Part visée |
|---|---|---|---|
| Emplacement | voir section 11 | formulaire, tableau, phrase, paragraphe, schéma, logo, plaque, tampon, calcul | par champ, section 11 |
| Absence | `absent` | réponse `null`, avec un voisin tentant (n° du moteur, pression maximale, pièces commandées) et des marqueurs variés (vide, « — », « illisible », « n.c. », « n.m. ») | environ 9 % des valeurs, par champ |
| Doublons | `valeur_barree` | valeur imprimée barrée, valeur juste écrite à la main (image) | 5 % des documents |
| | `erratum` | le récit rectifie une valeur du tableau | 5 % des documents |
| | `conflit_regle` | synthèse provisoire en page d'entrée, une phrase désigne le tableau qui fait foi | 10 % des documents |
| | `version_remplacee` | « annule et remplace » une ancienne référence | 30 % des documents |
| Calcul | `moyenne_a_calculer` | moyenne des essais non écrite (emplacement `calcul` de la dose) | 15 % des documents |
| | `tolerance_en_pourcent` | tolérance en % du nominal | 30 % des documents |
| | `unite_a_convertir` | µl, cl, L ; L/h, ml/s, L/min ; mbar, kPa, psi | 25 % des valeurs numériques présentes |
| Forme | `synonyme_cle` | libellé synonyme (« EMT », « Set point », « OEM ») | 30 % des valeurs écrites avec un libellé |
| | `redacteur_autre` | le rédacteur du rapport n'est pas le technicien responsable | 30 % des documents |
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

- `banc-essai/corpus/` : générateur et modules (`README.md`), graine fixe 20261119 ;
- `fourni/` : 35 PDF, réponses, vérité, annotations, `verite.csv` (versionné) ;
- `test-cache/` (15) et `relance/` (10) : même contenu, hors git ;
- `plan-equilibre.md` : agrégats du plan ; `empreintes.sha256` : empreintes de tous les fichiers générés ;
- `controler.py` : contrôle des PDF contre la vérité et le plan ;
- `banc-essai/recettes/avec-aide/ontologie.md`.

## 11. Plan du corpus

Le plan est tiré avant tout rendu (`plan.py`, graine fixe) ; le générateur l'exécute sans rien tirer d'autre que les valeurs. Le rapport `banc-essai/corpus/plan-equilibre.md` en donne les agrégats (aucune valeur, aucun identifiant du test ni de la relance).

| Étape | Règle |
|---|---|
| Composition | jeu, style, prestataire, marque, type d'équipement (à parts égales par univers), langue, nom vu ou inédit |
| Emplacements | pour chaque champ, parts visées ci-dessous, tirées en nombre exact par jeu (plus grand reste) |
| Équilibrage | les emplacements difficiles vont aux documents les moins chargés, et aux styles qui en ont le moins pour ce champ |
| Pièges | pièges de document, puis de valeur, sur les documents les moins chargés, dans la limite de 2 difficultés par valeur |
| Contrôle | `plan.py` vérifie les effectifs par jeu, la limite par valeur et l'absence de piège sur un champ absent |

| Emplacement | Sens |
|---|---|
| `formulaire` | libellé et valeur côte à côte : page d'entrée, cartouche, bloc de conclusion |
| `tableau` | case d'un tableau, libellé en tête de ligne ou de colonne |
| `phrase` | phrase courte qui contient le libellé et la valeur |
| `paragraphe` | valeur noyée dans un long paragraphe, sans libellé ; le titre de la section évoque la clé |
| `schema` | cote du schéma (image) |
| `logo` | constructeur seulement dans son logo (image) |
| `plaque` | n° de série seulement sur la plaque photographiée de la machine (image) |
| `tampon` | date de validation seulement dans le tampon (image) |
| `calcul` | dose à calculer : moyenne des essais |
| `absent` | réponse `null` |

| Champ | formulaire | tableau | phrase | paragraphe | schema | logo | plaque | tampon | calcul | absent |
|---|---|---|---|---|---|---|---|---|---|---|
| `machine` | 60 |  | 15 | 25 |  |  |  |  |  |  |
| `constructeur` | 55 |  | 10 | 15 |  | 20 |  |  |  |  |
| `numero_serie` | 45 |  | 10 | 15 |  |  | 10 |  |  | 20 |
| `site` | 50 |  | 10 | 20 |  |  |  |  |  | 20 |
| `reference_rapport` | 90 |  | 10 |  |  |  |  |  |  |  |
| `date_intervention` | 45 | 10 | 20 | 25 |  |  |  |  |  |  |
| `date_validation` | 40 |  | 10 | 10 |  |  |  | 25 |  | 15 |
| `volume_dose_ml` |  | 45 | 15 | 15 | 10 |  |  |  | 15 |  |
| `volume_nominal_ml` | 15 | 50 | 10 | 15 | 10 |  |  |  |  |  |
| `tolerance_ml` | 5 | 55 | 10 | 15 |  |  |  |  |  | 15 |
| `debit_ml_min` |  | 45 | 10 | 15 | 15 |  |  |  |  | 15 |
| `pression_bar` |  | 45 | 10 | 15 | 15 |  |  |  |  | 15 |
| `reference_piece` |  | 50 | 10 | 20 |  |  |  |  |  | 20 |
| `technicien` | 45 |  | 15 | 25 |  |  |  |  |  | 15 |
| `statut` | 50 |  | 25 | 25 |  |  |  |  |  |  |

Parts en % des documents de chaque jeu.

| Jeu | Composition |
|---|---|
| Fourni | 35 documents, 8 prestataires (2 par style, un francophone et un anglophone), 4 à 5 documents chacun |
| Test | 15 documents : 4 de 2 prestataires déjà vus, 6 de 3 nouveaux prestataires dans les styles connus, 5 du style réservé ; environ un tiers de marques déjà vues |
| Relance | 10 documents, prestataires et marques inédits, dont 3 du style réservé |
