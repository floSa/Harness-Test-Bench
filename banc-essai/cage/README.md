# Cage

Exécution d'un harnais (ou de code qu'il a écrit) dans bubblewrap 0.9.0, sans `sudo`.

## Ce que voit un processus dans la cage

| Chemin | Accès |
|---|---|
| `/travail` | espace de travail de l'essai, lecture et écriture |
| `/home/banc` | dossier personnel du harnais (`HOME`), lecture et écriture |
| `/tmp` | sur le disque : `~/banc-espaces/<essai>/tmp` pour un essai, dossier temporaire supprimé à la sortie sinon |
| `/run/banc` | sockets des relais et clé de l'essai, lecture seule |
| `/sortie` | sortie de la relance du workflow ou des tests cachés de la tâche jouet, si montée |
| `/usr`, `/etc` | système, lecture seule |
| `/opt/harnais` | dossier du harnais (`harnais/<nom>/`), lecture seule |
| `/opt/outils/uv` | uv, lecture seule |
| `/entree` | PDF de la relance, lecture seule, si monté |
| reste de la racine | lecture seule ; `/home` ne contient que `banc` : le dépôt, le test caché et les secrets sont invisibles |

## Ressources

| Ressource | Cadre d'un essai (`lancer.sh`) | Option de `cage.sh` |
|---|---|---|
| Mémoire vive | 16 Go, processus fautif arrêté au-delà (unité systemd de l'utilisateur, `OOMPolicy=continue`) ; pic relevé toutes les 2 s | `--memoire 16G` (défaut), `--memoire-pic FICHIER` |
| Carte graphique | visible (WSL : `/dev/dxg`, `/usr/lib/wsl` en lecture seule ; Linux natif : `/dev/nvidia*`, non vérifié sur le banc) ; mémoire non plafonnable ; pic relevé par `lancer.sh` | `--gpu` |
| Disque | 30 Go (espace, dossier personnel, `/tmp`), relevé toutes les 30 s, essai arrêté au-delà | `--tmp DIR` |
| Téléchargements | 10 Go | `--telechargement OCTETS` |
| Essais simultanés | un seul (verrou `~/banc-espaces/.verrou`) | |

## Réseau

La cage a son propre espace de noms réseau, vide. Trois services y entrent par des sockets Unix (`relais.py`) :

| Dans la cage | Hors de la cage | Condition |
|---|---|---|
| `127.0.0.1:4100` | LiteLLM du banc | toujours (sauf `--sans-reseau`) |
| `127.0.0.1:8765` | API de soumission de l'essai | `--api` |
| `127.0.0.1:3128` (`HTTPS_PROXY`) | mandataire filtrant : `CONNECT` sur le port 443 vers PyPI (`pypi.org`, `files.pythonhosted.org`), Hugging Face (`huggingface.co`, `*.hf.co`) et GitHub (`github.com`, `*.githubusercontent.com`) seulement ; volume total plafonné (`--telechargement`, 10 Go par défaut) ; chaque demande et chaque tunnel fermé (octets) journalisés | toujours (sauf `--sans-reseau`) |

Aucune autre sortie : pas de DNS, pas de route, pas d'accès aux ports de l'hôte.

## Scripts

| Script | Rôle |
|---|---|
| `lancer.sh <harnais> <recette>` | essai complet : espace neuf hors du dépôt (`~/banc-espaces/<essai>/`), clé propre à l'essai (supprimée à la fin), API, cage, garde-fou de durée (7 200 s), collecte dans `banc-essai/resultats/<essai>/`, relance du workflow (extraction), rapport |
| `cage.sh` | exécution d'une commande dans la cage (utilisé par `lancer.sh`, `relancer.py` et la notation de la tâche jouet) |
| `interieur.sh` | démarrage dans la cage : relais intérieurs, clé du harnais, commande |
| `relais.py` | relais socket Unix vers TCP, mandataire filtrant |
| `sonde/` | « harnais » de preuve : tente lectures, écritures, connexions et routes du relais interdites, appelle le modèle |
| `factice/` | faux harnais d'extraction : vérifie le lanceur de bout en bout (soumission, fin, relance, clé gardée refusée à la relance, répartition des appels) |
| `collecter.py` | répartition du journal entre l'essai et sa relance, écriture de `essai.json` |

## Résultats d'un essai (`banc-essai/resultats/<essai>/`)

| Fichier | Contenu |
|---|---|
| `essai.json` | harnais, recette, heures, durée, code de retour, garde-fou, appels au modèle (dont échecs, 429, images), jetons (dont cache), coût (relais et OpenRouter), dépense relevée sur la clé et écart avec le journal, attente après les 429, temps dans le modèle (union des intervalles), modèles et fournisseurs du journal, version du harnais (`harnais/<nom>/version`), demandes réseau |
| `harnais/stdout.log`, `stderr.log` | sorties du harnais |
| `traces/appels.jsonl` | appels au modèle de la clé de l'essai |
| `traces/reseau.jsonl` | demandes au mandataire PyPI, acceptées ou refusées |
| `evaluation/` | journaux de l'API de soumission |
| `relance/` | relance du workflow déclaré, dans la cage, avec la clé `<essai>-relance` |
| `rapport.json`, `rapport.md` | rapport d'essai |

## Preuve

```
banc-essai/cage/lancer.sh sonde jouet --essai preuve-cage-<date> --message "$PWD/banc-essai/corpus/test-cache"
banc-essai/cage/lancer.sh factice sans-aide --essai verif-lanceur-<date>
```

La sonde reçoit le chemin réel du test caché et tente de le lire, d'écrire hors de l'espace de travail, de joindre des sites non autorisés, puis appelle le modèle (texte, puis image) ; chaque appel doit apparaître dans `traces/appels.jsonl`.
