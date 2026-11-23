# Corpus du banc

Rapports d'intervention fictifs (PDF) et leur vérité terrain. Cahier des charges : [documentations/cahier-des-charges-corpus.md](../../documentations/cahier-des-charges-corpus.md).

## Commandes

Depuis `banc-essai/corpus/` :

| Commande | Effet |
|---|---|
| `uv run python plan.py` | tire le plan des 60 documents et écrit `plan-equilibre.md` |
| `uv run python generer.py` | génère les 60 documents dans `fourni/`, `test-cache/`, `relance/` |
| `uv run python generer.py --exemples` | un document par style dans `exemples/` (plan à graine séparée) |
| `uv run python generer.py --sortie DIR` | régénère ailleurs, pour comparer les empreintes |
| `uv run python dossiers.py` | tâche 2 : 26 dossiers d'équipement dans `dossiers/fourni/`, `dossiers/test-cache/`, `dossiers/relance/` |
| `uv run python controler.py` | contrôle les PDF générés contre la vérité et le plan |
| `sha256sum -c empreintes.sha256` | vérifie que les fichiers générés n'ont pas changé |

## Contenu d'un dossier de jeu

| Fichier | Contenu |
|---|---|
| `doc-NNN.pdf` | le rapport |
| `reponses/doc-NNN.json` | les 15 valeurs attendues |
| `verite/doc-NNN.json` | valeurs, emplacements, pièges, écritures et leurres avec leur cadre |
| `annotations/doc-NNN.pdf` | le rapport annoté (vert : valeur juste ; rouge numéroté : leurre ; orange : valeur barrée) |
| `verite.csv` | une ligne par document et par champ |

`test-cache/`, `relance/` et leurs équivalents sous `dossiers/` ne sont jamais versionnés ni copiés dans un espace de travail de harnais.

## Modules

| Module | Rôle |
|---|---|
| `univers.py` | noms inventés (marques, familles, prestataires, personnes, sites) |
| `plan.py` | composition, emplacements et pièges de chaque document, équilibrage |
| `donnees.py` | tirage des valeurs et des leurres d'un document |
| `formats.py` | nombres, unités, dates |
| `textes.py` | phrases de remplissage, titres, statut en phrase |
| `base.py`, `base_flux.py`, `flux.py`, `mise_en_page.py`, `dessins.py` | briques de rendu communes |
| `style_*.py` | les 5 mises en page |
| `verite.py` | vérité terrain et PDF annoté |

## Tâche 2 : dossiers d'équipement

| Fichier | Contenu |
|---|---|
| `dossiers/<jeu>/dos-NNN/piece-NN.pdf` | pièces du dossier, dans le désordre |
| `dossiers/<jeu>/reponses/dos-NNN.json` | réponse attendue : équipement, interventions retenues, statut actuel |
| `dossiers/<jeu>/verite/dos-NNN.json` | nature de chaque pièce (rapport retenu, version remplacée, équipement jumeau, rapport annulé, avis d'annulation, rectificatif) |
| `dossiers/<jeu>/verite/dos-NNN/piece-NN.json` | vérité détaillée de chaque rapport (format de la tâche 1) |
