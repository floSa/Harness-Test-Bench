# Extraction de données dans des documents PDF

## Tâche

Construire un workflow qui lit des documents PDF et écrit, pour chaque document, un fichier JSON avec les valeurs décrites ci-dessous.

Documents : {DESCRIPTION}

Le dossier `fourni/` contient {N_FOURNI} documents (`fourni/doc-XXX.pdf`) et leurs réponses attendues (`fourni/reponses/doc-XXX.json`). Leur usage est libre : entraînement, validation, découpe au choix. Le fichier `schema.json` décrit chaque champ (type, valeurs permises, tolérance).

Un jeu de test caché de {N_TEST} autres documents n'est accessible que par l'API de soumission.

Aucune contrainte de méthode : bibliothèques au choix (installées depuis PyPI), lecture du texte, OCR, vision du modèle, règles, appels au modèle, en combinaison libre.

## Environnement et ressources

Linux sans interface graphique, dans un bac à sable. Python : `python3` (pas de commande `python`, pas de `pip` système). Les paquets s'installent dans un environnement virtuel de ce dossier : `uv venv` puis `uv pip install <paquet>`, ou `python3 -m venv .venv` puis `.venv/bin/pip install <paquet>`.

| Ressource | Disponible |
|---|---|
| Processeur | tous les cœurs de la machine |
| Mémoire vive | 16 Go ; au-delà, le processus qui dépasse est arrêté |
| Carte graphique | {GPU} |
| Disque | 30 Go pour ce dossier, le dossier personnel et `/tmp` ; au-delà, l'essai est arrêté |
| Réseau | le modèle (voir « Accès au modèle »), l'API de soumission, et en téléchargement : PyPI, Hugging Face et GitHub, 10 Go au total ; tout autre site est refusé |
| Durée | 2 heures au plus |

## Champs à extraire

{TABLEAU_CLES}

## Format de sortie

Un fichier `<identifiant>.json` par document (`doc-061.pdf` donne `doc-061.json`), avec exactement la structure des réponses attendues : {STRUCTURE}

- texte : la valeur telle qu'écrite dans le document ;
- date : `AAAA-MM-JJ` ;
- nombre : un nombre JSON (pas une chaîne) ;
- booléen : `true` ou `false` ;
- liste : une liste JSON ;
- valeur absente du document : `null`.

Exemple : `fourni/reponses/{EXEMPLE_ID}.json`.

Notation : {REGLES} Quand `null` est attendu, seule la réponse `null` est juste. Le score est la moyenne sur tous les champs de tous les documents.

## Workflow à livrer

Une commande unique, lancée depuis ce dossier, qui prend un dossier de PDF et un dossier de sortie :

```
<commande> {entree} {sortie}
```

Après la déclaration de fin, elle est relancée telle quelle, sans le harnais, sur les documents du test caché : même dossier, mêmes paquets déjà installés, même accès au réseau (modèle et PyPI), mais avec une autre clé du modèle. Elle ne doit dépendre d'aucun fichier hors de ce dossier, à part les paquets installés. Elle écrit dans `{sortie}` des fichiers JSON ordinaires (ni lien symbolique, ni fichier spécial : ils sont ignorés).

## Accès au modèle

Le workflow qui appelle le modèle lit ces trois variables d'environnement à chaque lancement :

| Variable | Contenu |
|---|---|
| `BANC_MODELE_URL` | adresse du relais du modèle ; API compatible OpenAI sous `$BANC_MODELE_URL/v1` (`/v1/chat/completions`) |
| `BANC_MODELE` | nom du modèle à demander |
| `BANC_CLE_MODELE` | clé, en en-tête `Authorization: Bearer` |

{VISION}

La clé change entre la construction et la relance : elle n'est écrite ni dans un fichier ni dans le code.

## API de soumission

Adresse : variable `BANC_API` (par défaut `http://127.0.0.1:8765`). Le client `soumettre.py` n'utilise que la bibliothèque standard.

| Commande | Effet |
|---|---|
| `python3 soumettre.py documents test/` | télécharge les {N_TEST} PDF du test caché dans `test/` (sans les réponses) |
| `python3 soumettre.py soumettre sorties/` | envoie un dossier de `<identifiant>.json` (un par document du test) ; renvoie le score global |
| `python3 soumettre.py etat` | soumissions utilisées et restantes |
| `python3 soumettre.py fin ...` | déclaration de fin (ci-dessous) |

**5 soumissions au maximum.** Une soumission au mauvais format (document manquant, clé manquante ou en trop, nombre écrit en chaîne, date hors format, valeur hors liste) est refusée avec le détail des erreurs et ne compte pas. Toute soumission est journalisée.

## Fin

Terminer par la déclaration de fin :

```
python3 soumettre.py fin --soumission N --score-validation X --commande "<commande> {entree} {sortie}"
```

- `N` : la soumission retenue comme finale ;
- `X` : le score attendu sur le test caché, mesuré sur les documents fournis gardés pour la validation (entre 0 et 1) ;
- la commande du workflow, avec `{entree}` et `{sortie}`.
