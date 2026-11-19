# Tâche de mise au point

Le dossier `dosage/` est un petit paquet Python de calcul sur des relevés de dosage. Ses tests sont dans `tests/` (`python3 -m pytest tests`, pytest à installer).

## Environnement et ressources

Linux sans interface graphique, dans un bac à sable. Python : `python3` (pas de commande `python`, pas de `pip` système). Les paquets s'installent dans un environnement virtuel de ce dossier : `uv venv` puis `uv pip install <paquet>`, ou `python3 -m venv .venv` puis `.venv/bin/pip install <paquet>`.

| Ressource | Disponible |
|---|---|
| Processeur | tous les cœurs de la machine |
| Mémoire vive | 16 Go ; au-delà, le processus qui dépasse est arrêté |
| Carte graphique | NVIDIA RTX 4060 Ti (CUDA) : 8 Go de mémoire au plus |
| Disque | 30 Go pour ce dossier, le dossier personnel et `/tmp` ; au-delà, l'essai est arrêté |
| Réseau | le modèle, l'API de soumission, et en téléchargement : PyPI, Hugging Face et GitHub, 10 Go au total ; tout autre site est refusé |
| Durée | 2 heures au plus |

## Bug signalé

> `vers_ml(250, "µl")` renvoie `250000.0` alors que 250 µl valent 0,25 ml. Les autres écritures du microlitre (`µL`, `ul`, `uL`) donnent le même résultat faux.

Corriger ce bug sans changer le comportement des autres fonctions. Des tests cachés, plus nombreux que ceux de `tests/`, notent la correction.

## Soumission

L'API de soumission est à l'adresse donnée par la variable `BANC_API` (par défaut `http://127.0.0.1:8765`). Le client `soumettre.py` n'utilise que la bibliothèque standard.

- `python3 soumettre.py soumettre dosage` : envoie le paquet `dosage/` (fichiers `.py` seulement) ; l'API renvoie le score, part des tests cachés réussis.
- **5 soumissions au maximum.** Une soumission au mauvais format est refusée et ne compte pas.
- `python3 soumettre.py etat` : soumissions utilisées et restantes.

## Fin

Terminer par la déclaration de fin, qui indique la soumission retenue :

```
python3 soumettre.py fin --soumission N --score-validation X
```

`X` est le score attendu sur les tests cachés, entre 0 et 1.
