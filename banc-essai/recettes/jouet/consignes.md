# Tâche de mise au point

Le dossier `dosage/` est un petit paquet Python de calcul sur des relevés de dosage. Ses tests sont dans `tests/` (`python -m pytest tests`).

## Bug signalé

> `vers_ml(250, "µl")` renvoie `250000.0` alors que 250 µl valent 0,25 ml. Les autres écritures du microlitre (`µL`, `ul`, `uL`) donnent le même résultat faux.

Corriger ce bug sans changer le comportement des autres fonctions. Des tests cachés, plus nombreux que ceux de `tests/`, notent la correction.

## Soumission

L'API de soumission est à l'adresse donnée par la variable `BANC_API` (par défaut `http://127.0.0.1:8765`). Le client `soumettre.py` n'utilise que la bibliothèque standard.

- `python soumettre.py soumettre dosage` : envoie le paquet `dosage/` (fichiers `.py` seulement) ; l'API renvoie le score, part des tests cachés réussis.
- **5 soumissions au maximum.** Une soumission au mauvais format est refusée et ne compte pas.
- `python soumettre.py etat` : soumissions utilisées et restantes.

## Fin

Terminer par la déclaration de fin, qui indique la soumission retenue :

```
python soumettre.py fin --soumission N --score-validation X
```

`X` est le score attendu sur les tests cachés, entre 0 et 1.
