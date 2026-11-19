# Ontologie des rapports d'intervention

Définitions métier des 15 clés à extraire, unités et conversions, synonymes, règles de choix entre valeurs voisines. Une valeur absente du document vaut `null`.

## Nombres, dates et unités

Séparateurs : la virgule ou le point peut être décimal ; l'espace, le point, la virgule ou l'apostrophe peut séparer les milliers (`1 250,5`, `1.250,5`, `1,250.5`, `1'250.5`). Le format se déduit des autres nombres du même document. Dates écrites en `14/03/2026`, `14.03.26`, `2026-03-14`, `14 mars 2026`, `March 14, 2026` ; réponse au format ISO.

| Grandeur | Unité de la clé | Unités rencontrées | Conversion |
|---|---|---|---|
| Volume | ml | ml, mL, cm³, cc, µl, µL, ul, cl, L, l | 1 cm³ = 1 ml ; 1 µl = 0,001 ml ; 1 cl = 10 ml ; 1 L = 1 000 ml |
| Débit | ml/min | ml/min, mL/min, L/h, l/h, ml/s, L/min | 1 L/h = 1 000 / 60 ml/min ; 1 ml/s = 60 ml/min ; 1 L/min = 1 000 ml/min |
| Pression | bar | bar, mbar, kPa, psi | 1 mbar = 0,001 bar ; 1 kPa = 0,01 bar ; 1 psi = 0,06894757 bar |

## Clés

### `machine`

| Critère | Contenu |
|---|---|
| Type | texte |
| Définition | modèle de l'équipement contrôlé (pas le moteur, pas un équipement voisin) |
| Libellés (fr) | Équipement ; Machine, Modèle, Désignation |
| Libellés (en) | Equipment ; Machine, Model, Unit |
| Règles | Le modèle s'écrit « famille + numéro » (exemple : « Kaltis 85 »). Un nom de famille de machines peut être, dans un autre rapport, le nom d'un constructeur : seul le rôle dans le document compte. |

### `constructeur`

| Critère | Contenu |
|---|---|
| Type | texte |
| Définition | fabricant de l'équipement contrôlé (pas le prestataire, ni le fabricant du moteur ou des instruments) |
| Libellés (fr) | Constructeur ; Fabricant, Marque |
| Libellés (en) | Manufacturer ; Make, OEM, Brand |
| Règles | Le constructeur peut n'apparaître que dans son logo. Le prestataire (en-tête, pied de page, logo du rapport) n'est jamais le constructeur. |

### `numero_serie`

| Critère | Contenu |
|---|---|
| Type | texte |
| Définition | n° de série de l'équipement (pas celui du moteur, des instruments, ni le n° d'inventaire) |
| Libellés (fr) | N° de série ; N° de fabrication, Identifiant machine, S/N |
| Libellés (en) | Serial number ; S/N, Unit ID |
| Règles | Peut ne se lire que sur la plaque signalétique photographiée de l'équipement. « Illisible », « plaque absente » : valeur `null`. |

### `site`

| Critère | Contenu |
|---|---|
| Type | texte |
| Définition | site du client où l'équipement est installé (pas le siège, ni l'adresse du prestataire) |
| Libellés (fr) | Site ; Lieu d'intervention, Établissement, Implantation |
| Libellés (en) | Site ; Location, Plant |
| Règles | Le nom du site s'écrit en entier (« Usine de Cholet », « Telford Plant »). La ville du siège social du client n'est pas le site. |

### `reference_rapport`

| Critère | Contenu |
|---|---|
| Type | texte |
| Définition | référence du rapport en vigueur (pas la version annulée, ni la commande ou l'affaire) |
| Libellés (fr) | Référence du rapport ; N° de document, Réf. document, N° de compte rendu |
| Libellés (en) | Report reference ; Document no., Report ID |
| Règles | Le rapport peut annuler et remplacer une version antérieure : seule la référence en vigueur compte. |

### `date_intervention`

| Critère | Contenu |
|---|---|
| Type | date ISO (AAAA-MM-JJ) |
| Définition | jour de l'intervention sur site, format ISO |
| Libellés (fr) | Date d'intervention ; Date de visite, Intervenu le, Date de passage |
| Libellés (en) | Date of intervention ; Visit date, Service date |
| Règles | Dates voisines : incident signalé, demande d'intervention, émission du rapport, prochaine visite. |

### `date_validation`

| Critère | Contenu |
|---|---|
| Type | date ISO (AAAA-MM-JJ) |
| Définition | date de l'approbation finale du rapport (pas la rédaction, la vérification, l'impression ni l'étalonnage des instruments), format ISO |
| Libellés (fr) | Date de validation ; Approuvé le, Date d'approbation |
| Libellés (en) | Validation date ; Approved on, Approval date |
| Règles | Date d'approbation (« Approuvé par … le », tampon « APPROUVÉ », phrase « approuvé … le »). Ni la date de rédaction, ni celle de vérification, ni la date d'impression en pied de page. Case vide : `null`. |

### `volume_dose_ml`

| Critère | Contenu |
|---|---|
| Type | nombre, ml |
| Définition | dose moyenne après réglage, toutes têtes et tous essais confondus, en ml |
| Libellés (fr) | Volume de dose ; Dose, Volume délivré, Capacité utile, Contenance |
| Libellés (en) | Dose volume ; Fill volume, Dose, Delivered volume |
| Règles | Si plusieurs têtes : moyenne générale. Si seuls les essais sont écrits : moyenne des essais après réglage. Une valeur barrée et corrigée à la main : la valeur manuscrite. Un erratum : la valeur rectifiée. Ne pas confondre avec la dose avant réglage, la moyenne d'une seule tête, la capacité du réservoir (L), le volume du circuit ni l'incertitude. |

### `volume_nominal_ml`

| Critère | Contenu |
|---|---|
| Type | nombre, ml |
| Définition | volume de consigne de l'équipement, en ml (pas la gamme du modèle) |
| Libellés (fr) | Volume nominal ; Consigne, Volume de consigne |
| Libellés (en) | Nominal volume ; Set point, Target volume |
| Règles | La gamme du modèle (« 5 – 500 ml ») n'est pas le volume nominal. |

### `tolerance_ml`

| Critère | Contenu |
|---|---|
| Type | nombre, ml |
| Définition | tolérance admise sur la dose, en ml ; une tolérance en % se rapporte au volume nominal (pas l'incertitude de mesure) |
| Libellés (fr) | Tolérance ; Écart maximal toléré, EMT, Tolérance admise |
| Libellés (en) | Tolerance ; Max. permissible error, MPE, Acceptance limit |
| Règles | Une tolérance en % se convertit : nominal × % / 100. L'incertitude élargie (k = 2) n'est pas la tolérance. « n.c. » : `null`. |

### `debit_ml_min`

| Critère | Contenu |
|---|---|
| Type | nombre, ml/min |
| Définition | débit mesuré après réglage, en ml/min (pas le débit maximal, ni celui d'un équipement voisin) |
| Libellés (fr) | Débit ; Cadence volumique, Débit volumique |
| Libellés (en) | Flow rate ; Throughput, Delivery rate |
| Règles | Valeur après réglage. Une synthèse marquée provisoire cède devant le tableau des mesures quand une phrase le précise. « n.m. » (non mesuré) : `null`. |

### `pression_bar`

| Critère | Contenu |
|---|---|
| Type | nombre, bar |
| Définition | pression de service mesurée après réglage, en bar (pas la pression maximale, le tarage de soupape ou le réseau d'air) |
| Libellés (fr) | Pression de service ; Pression de travail, Pression ligne |
| Libellés (en) | Operating pressure ; Line pressure, Working pressure |
| Règles | Valeur après réglage. Ne pas confondre avec la pression maximale admissible, le tarage de la soupape ou le réseau d'air de l'atelier. « n.m. » : `null`. |

### `reference_piece`

| Critère | Contenu |
|---|---|
| Type | texte |
| Définition | référence de la pièce effectivement remplacée (pas contrôlée, commandée ou proposée au devis) |
| Libellés (fr) | Référence pièce ; Réf. article, Code pièce |
| Libellés (en) | Part reference ; Part number, P/N, Item code |
| Règles | « Aucune pièce remplacée » : `null`, même si des pièces sont commandées ou proposées au devis. |

### `technicien`

| Critère | Contenu |
|---|---|
| Type | texte (prénom nom) |
| Définition | intervenant responsable côté prestataire (pas l'accompagnant, le rédacteur, le vérificateur ou le client) |
| Libellés (fr) | Technicien responsable ; Intervenant principal, Chargé d'intervention |
| Libellés (en) | Lead technician ; Lead engineer, Responsible technician |
| Règles | Intervenant marqué responsable (« responsable », « lead », signataire technicien responsable). Le rédacteur du rapport peut être une autre personne. |

### `statut`

| Critère | Contenu |
|---|---|
| Type | conforme / non_conforme / a_revoir |
| Définition | décision finale : conforme, non_conforme ou a_revoir |
| Libellés (fr) | Statut ; Avis, Verdict, Décision |
| Libellés (en) | Status ; Outcome, Result |
| Règles | Peut être indiqué par une case cochée, un libellé (« Conforme », « Compliant », « To be reviewed ») ou une phrase : « remis en production sans réserve » = conforme ; « ne peut pas être remis en production » = non_conforme ; « sous réserve d'une nouvelle visite » = a_revoir. Le statut à l'arrivée n'est pas le statut final. |
