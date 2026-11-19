# Cage

Exécution d'un harnais (ou de code qu'il a écrit) dans bubblewrap 0.9.0, sans `sudo`.

## Ce que voit un processus dans la cage

| Chemin | Accès |
|---|---|
| `/travail` | espace de travail de l'essai, lecture et écriture |
| `/home/banc` | dossier personnel du harnais (`HOME`), lecture et écriture |
| `/tmp` | en mémoire, perdu à la sortie |
| `/sortie` | sortie de la relance du workflow ou des tests cachés de la tâche jouet, si montée |
| `/usr`, `/etc` | système, lecture seule |
| `/opt/harnais` | dossier du harnais (`harnais/<nom>/`), lecture seule |
| `/opt/outils/uv` | uv, lecture seule |
| `/entree` | PDF de la relance, lecture seule, si monté |
| reste de la racine | lecture seule ; `/home` ne contient que `banc` : le dépôt, le test caché et les secrets sont invisibles |

## Réseau

La cage a son propre espace de noms réseau, vide. Trois services y entrent par des sockets Unix (`relais.py`) :

| Dans la cage | Hors de la cage | Condition |
|---|---|---|
| `127.0.0.1:4100` | LiteLLM du banc | toujours (sauf `--sans-reseau`) |
| `127.0.0.1:8765` | API de soumission de l'essai | `--api` |
| `127.0.0.1:3128` (`HTTPS_PROXY`) | mandataire filtrant : `CONNECT` vers `pypi.org` et `files.pythonhosted.org` sur le port 443 seulement, chaque demande journalisée | toujours (sauf `--sans-reseau`) |

Aucune autre sortie : pas de DNS, pas de route, pas d'accès aux ports de l'hôte.

## Scripts

| Script | Rôle |
|---|---|
| `lancer.sh <harnais> <recette>` | essai complet : espace neuf hors du dépôt (`~/banc-espaces/<essai>/`), clé propre à l'essai (supprimée à la fin), API, cage, garde-fou de durée (7 200 s), collecte dans `banc-essai/resultats/<essai>/`, relance du workflow (extraction), rapport |
| `cage.sh` | exécution d'une commande dans la cage (utilisé par `lancer.sh`, `relancer.py` et la notation de la tâche jouet) |
| `interieur.sh` | démarrage dans la cage : relais intérieurs, clé du harnais, commande |
| `relais.py` | relais socket Unix vers TCP, mandataire filtrant |
| `outils.sh` | installe pytest (tests cachés de la tâche jouet) dans `outils/`, hors git |
| `sonde/` | « harnais » de preuve : tente lectures, écritures et connexions interdites, appelle le modèle |

## Résultats d'un essai (`banc-essai/resultats/<essai>/`)

| Fichier | Contenu |
|---|---|
| `essai.json` | harnais, recette, heures, durée, code de retour, garde-fou, appels au modèle (dont échecs, 429, images), jetons (dont cache), coût (relais et OpenRouter), temps dans le modèle, demandes réseau |
| `harnais/stdout.log`, `stderr.log` | sorties du harnais |
| `traces/appels.jsonl` | appels au modèle de la clé de l'essai |
| `traces/reseau.jsonl` | demandes au mandataire PyPI, acceptées ou refusées |
| `evaluation/` | journaux de l'API de soumission |
| `relance/` | relance du workflow déclaré, dans la cage, avec la clé `<essai>-relance` |
| `rapport.json`, `rapport.md` | rapport d'essai |

## Preuve

```
banc-essai/cage/lancer.sh sonde jouet --essai preuve-cage --message "$PWD/banc-essai/corpus/test-cache"
```

La sonde reçoit le chemin réel du test caché et tente de le lire, d'écrire hors de l'espace de travail, de joindre des sites non autorisés, puis appelle le modèle (texte, puis image) ; chaque appel doit apparaître dans `traces/appels.jsonl`.
