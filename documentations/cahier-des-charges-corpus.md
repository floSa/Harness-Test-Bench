# Cahier des charges du corpus

Version 1, 18 novembre 2026. À relire et valider avant toute génération.

## 1. Principe

50 rapports d'intervention fictifs sur des équipements de dosage (doseuses, pompes, remplisseuses, pipettes automatiques), en PDF de 3 à 5 pages, en français et en anglais. Tout est fictif : entreprises, machines, marques, logos, personnes. Les réponses attendues sont tirées au sort avant la génération : elles sont donc connues sans erreur.

## 2. Structure d'un document

| Page | Contenu | Ce que ça teste |
|---|---|---|
| Page de garde | logo du constructeur, parfois logo du prestataire ; nom de la machine, modèle, numéro de série, site, date, référence du rapport | lecture d'un formulaire ; constructeur ou prestataire |
| Mesures (1 à 2 pages) | tableaux : plusieurs grandeurs et unités (ml, L, µl, ml/min, bar, °C), avant et après réglage, tolérances | trouver la bonne valeur parmi plusieurs |
| Schéma | vue de la machine avec repères et cotes (capacité du réservoir, volume du circuit, volume de dose) | information dans une image : vision ou OCR |
| Récit | constat, actions, pièces remplacées, corrections éventuelles | valeur citée seulement dans une phrase |
| Conclusion | statut (conforme, non conforme, à revoir), technicien, signature | champ simple en fin de document |

## 3. Gabarits

4 prestataires fictifs, chacun avec sa mise en page, son vocabulaire et sa langue.

| Gabarit | Langue | Particularité |
|---|---|---|
| 1 | français | tableaux classiques, clés proches des noms attendus |
| 2 | anglais | format des nombres anglais (1,000.5), unités en abréviations |
| 3 | français | beaucoup de texte libre, tableaux coupés entre deux pages |
| 4 | anglais | mise en page différente ; **réservé au test** (jamais fourni) |

## 4. Champs à extraire

| Clé | Type | Exemple |
|---|---|---|
| `machine` | texte | « DosaLine 300 » |
| `constructeur` | texte | « Hydrex » |
| `numero_serie` | texte | « HX-2025-04417 » |
| `site` | texte | « Usine de Cholet » |
| `date_intervention` | date ISO | `2026-03-14` |
| `volume_dose_ml` | nombre, ml | `49.6` |
| `volume_nominal_ml` | nombre, ml | `50` |
| `debit_ml_min` | nombre, ml/min | `150` |
| `pression_bar` | nombre, bar | `2.4` |
| `reference_piece` | texte | « JT-118 » |
| `technicien` | texte | « Claire Morvan » |
| `statut` | `conforme` / `non_conforme` / `a_revoir` | `conforme` |

Un champ absent du document vaut `null`.

## 5. Pièges

Chaque valeur attendue reçoit 0, 1 ou 2 pièges, tirés au sort selon les proportions visées.

| Piège | Règle de génération | Part visée |
|---|---|---|
| Volumes voisins | le volume de dose côtoie capacité du réservoir (L), volume du circuit, tolérance, ancienne valeur | tous les documents |
| Unité à convertir | valeur donnée en µl ou en L | 20 % des valeurs de volume |
| Format de nombre | virgule décimale, séparateur de milliers français ou anglais | selon le gabarit |
| Synonyme de clé | « Contenance », « Capacité utile », « Fill volume », « Dose » | 30 % des clés |
| Valeur seulement dans le récit | absente des tableaux | 15 % des valeurs |
| Correction | « lire 25 ml au lieu de 20 ml » | 5 % des documents |
| Tableau coupé | la ligne cherchée passe sur la page suivante | gabarit 3 |
| Constructeur en logo seul | nom absent du texte, présent seulement dans le logo | 20 % des documents |
| Constructeur ou prestataire | deux logos sur la page de garde | 30 % des documents |
| Valeur dans le schéma seulement | cote lisible uniquement sur l'image | 10 % des valeurs |
| Champ absent | réponse attendue `null` | 5 % des valeurs |
| Page scannée | une page rendue en image dégradée (bruit, légère rotation) | 20 % des documents |

## 6. Étiquettes de difficulté

Chaque valeur attendue porte des étiquettes, utilisées pour le score par difficulté :

| Étiquette | Valeurs |
|---|---|
| `emplacement` | `garde`, `tableau`, `recit`, `schema`, `conclusion` |
| `cle` | `exacte`, `synonyme`, `logo` |
| `unite` | `directe`, `conversion`, `sans_unite` |
| `piege` | liste des pièges appliqués, vide sinon |
| `scan` | `oui`, `non` |

## 7. L'ontologie (recette « avec aide »)

Un fichier `ontologie.md` donne, pour chaque clé : sa définition métier, son unité attendue et les conversions, ses synonymes, et les règles de choix entre valeurs voisines. Exemple :

> `volume_dose_ml` : volume délivré à chaque cycle, mesuré après réglage, en millilitres. Synonymes : dose, volume délivré, fill volume. Convertir µl et L en ml. Ne pas confondre avec la capacité du réservoir (en litres), le volume du circuit, la tolérance (± …) ou la valeur avant réglage.

## 8. Répartition

| Jeu | Documents | Gabarits |
|---|---|---|
| Fourni | 35 : PDF et réponses attendues (`reponses/<id>.json`) | 1, 2, 3 |
| Test caché | 15 : 10 des gabarits 1 à 3, 5 du gabarit 4 | réponses jamais dans l'espace du harnais |

## 9. Format de réponse et notation

Réponse : un JSON par document, avec exactement les 12 clés de la section 4.

Notation, par valeur :
- texte : égal après normalisation (casse, espaces, accents) ;
- nombre : égal à 0,01 près, après conversion dans l'unité attendue ;
- date : égale au format ISO ;
- `null` attendu : juste seulement si la réponse est `null`.

Score d'un essai : pourcentage de valeurs justes sur le test caché, détaillé par clé, par étiquette et par gabarit.

## 10. Livrables de la génération

- `banc-essai/corpus/generer.py` : générateur, avec graine fixe pour reproduire le corpus à l'identique ;
- `banc-essai/corpus/fourni/` : 35 PDF et leurs réponses ;
- `banc-essai/corpus/test-cache/` : 15 PDF et leurs réponses (hors git) ;
- `banc-essai/corpus/etiquettes.json` : étiquettes de chaque valeur ;
- `banc-essai/recettes/avec-aide/ontologie.md`.
