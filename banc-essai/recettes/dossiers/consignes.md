# Dossiers d'équipement : recouper plusieurs pièces

## Tâche

Construire un workflow qui lit des dossiers d'équipement et écrit, pour chaque dossier, un fichier JSON qui décrit l'équipement et l'historique de ses interventions.

Un dossier rassemble toutes les pièces reçues pour **un** équipement de dosage (doseuse, pompe doseuse, remplisseuse ou pipette automatique), en français ou en anglais : des rapports d'intervention en PDF et des courriers de prestataires. Les pièces sont dans le désordre, sous des noms sans signification (`piece-01.pdf`, `piece-02.pdf`, ...). Certaines pages sont scannées (image seule).

Le dossier `fourni/` contient 6 dossiers (`fourni/dos-XXX/piece-NN.pdf`) et leurs réponses attendues (`fourni/reponses/dos-XXX.json`). Leur usage est libre.

Un jeu de test caché de 12 autres dossiers n'est accessible que par l'API de soumission. Ses noms de prestataires, de marques et de machines, et une partie de ses mises en page, sont absents du dossier `fourni/`.

Aucune contrainte de méthode : bibliothèques au choix (installées depuis PyPI), lecture du texte, OCR, vision du modèle, règles, appels au modèle, en combinaison libre.

## Règles des dossiers

| Pièce | Ce qu'elle implique |
|---|---|
| Rapport d'intervention sur l'équipement du dossier | une intervention de l'historique |
| Rapport sur un autre équipement (même site, même modèle, numéro de série différent) | à écarter |
| Rapport dont la référence est annulée et remplacée par un autre rapport du dossier | à écarter ; seul le rapport qui le remplace compte |
| Rapport visé par un avis d'annulation | à écarter |
| Rectificatif d'un prestataire | la valeur rectifiée remplace celle du rapport visé ; les autres valeurs du rapport restent valables |

L'équipement du dossier est celui de la majorité des rapports. Le statut actuel est le statut de la dernière intervention retenue (date d'intervention la plus récente), après rectificatif.

## Environnement et ressources

Linux sans interface graphique, dans un bac à sable. Python : `python3` (pas de commande `python`, pas de `pip` système). Les paquets s'installent dans un environnement virtuel de ce dossier : `uv venv` puis `uv pip install <paquet>`, ou `python3 -m venv .venv` puis `.venv/bin/pip install <paquet>`.

| Ressource | Disponible |
|---|---|
| Processeur | tous les cœurs de la machine |
| Mémoire vive | 16 Go ; au-delà, le processus qui dépasse est arrêté |
| Carte graphique | NVIDIA RTX 4060 Ti (CUDA) : 8 Go de mémoire au plus |
| Disque | 30 Go pour ce dossier, le dossier personnel et `/tmp` ; au-delà, l'essai est arrêté |
| Réseau | le modèle (voir « Accès au modèle »), l'API de soumission, et en téléchargement : PyPI, Hugging Face et GitHub, 10 Go au total ; tout autre site est refusé |
| Durée | 2 heures au plus |

## Valeurs à extraire

Pour l'équipement :

| Clé | Type | Définition |
|---|---|---|
| `machine` | texte | modèle de l'équipement contrôlé |
| `constructeur` | texte | fabricant de l'équipement contrôlé |
| `numero_serie` | texte | numéro de série de l'équipement contrôlé |
| `site` | texte | site du client où l'équipement est installé |

Pour chaque intervention retenue :

| Clé | Type | Définition |
|---|---|---|
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

Un fichier `<dossier>.json` par dossier (`dos-012/` donne `dos-012.json`), avec exactement ces clés :

```json
{
  "machine": "...", "constructeur": "...", "numero_serie": "...", "site": "...",
  "interventions": [ {"reference_rapport": "...", "date_intervention": "AAAA-MM-JJ", "...": "..."} ],
  "statut_actuel": "conforme"
}
```

- `interventions` : une entrée par intervention retenue, avec exactement les 11 clés ci-dessus, dans l'ordre des dates d'intervention (la plus ancienne d'abord) ;
- texte : la valeur telle qu'écrite dans le document ;
- date : `AAAA-MM-JJ` ;
- nombre : un nombre JSON (pas une chaîne), converti dans l'unité de la clé ;
- valeur absente : `null`.

Exemple : `fourni/reponses/dos-007.json`.

Notation : les interventions sont appariées par référence de rapport. Chaque valeur est comparée comme suit : texte égal après normalisation de la casse, des espaces et des accents ; nombre égal à 0,01 près ; date égale ; quand `null` est attendu, seule la réponse `null` est juste. Le score est un F1 par champ : une intervention en trop compte 11 valeurs fausses, une intervention oubliée 11 valeurs manquées. Le nombre de dossiers entièrement justes est aussi relevé.

## Workflow à livrer

Une commande unique, lancée depuis ce dossier, qui prend un dossier de dossiers (un sous-dossier `dos-XXX/` par dossier) et un dossier de sortie :

```
<commande> {entree} {sortie}
```

Après la déclaration de fin, elle est relancée telle quelle sur des dossiers neufs, sans le harnais : même dossier, mêmes paquets déjà installés, même accès au réseau (modèle et PyPI), mais avec une autre clé du modèle. Elle ne doit dépendre d'aucun fichier hors de ce dossier, à part les paquets installés. Elle écrit dans `{sortie}` des fichiers JSON ordinaires (ni lien symbolique, ni fichier spécial : ils sont ignorés).

## Accès au modèle

Le workflow qui appelle le modèle lit ces trois variables d'environnement à chaque lancement :

| Variable | Contenu |
|---|---|
| `BANC_MODELE_URL` | adresse du relais du modèle ; API compatible OpenAI sous `$BANC_MODELE_URL/v1` (`/v1/chat/completions`) |
| `BANC_MODELE` | nom du modèle à demander |
| `BANC_CLE_MODELE` | clé, en en-tête `Authorization: Bearer` |

La clé change entre la construction et la relance : elle n'est écrite ni dans un fichier ni dans le code.

## API de soumission

Adresse : variable `BANC_API` (par défaut `http://127.0.0.1:8765`). Le client `soumettre.py` n'utilise que la bibliothèque standard.

| Commande | Effet |
|---|---|
| `python3 soumettre.py documents test/` | télécharge les 12 dossiers du test caché dans `test/` (sans les réponses) |
| `python3 soumettre.py soumettre sorties/` | envoie un dossier de `<dossier>.json` (un par dossier du test) ; renvoie le score global |
| `python3 soumettre.py etat` | soumissions utilisées et restantes |
| `python3 soumettre.py fin ...` | déclaration de fin (ci-dessous) |

**5 soumissions au maximum.** Une soumission au mauvais format (dossier manquant, clé manquante, nombre écrit en chaîne, date hors format) est refusée avec le détail des erreurs et ne compte pas. Toute soumission est journalisée.

## Fin

Terminer par la déclaration de fin :

```
python3 soumettre.py fin --soumission N --score-validation X --commande "<commande> {entree} {sortie}"
```

- `N` : la soumission retenue comme finale ;
- `X` : le score attendu sur le test caché, mesuré sur les dossiers fournis gardés pour la validation (entre 0 et 1) ;
- la commande du workflow, avec `{entree}` et `{sortie}`.
