# Lancer un essai, le suivre, l'arrêter, lire ses résultats

Un essai = un harnais, une recette (une tâche et ses consignes), dans la cage, avec une clé du modèle propre à l'essai. Une seule commande le lance ; tout le reste (espace neuf, clé, API de soumission, collecte, relance, rapport) est fait par le lanceur.

## 1. Prérequis, à vérifier une fois

| Élément | Vérification | Page de référence |
|---|---|---|
| bubblewrap | `bwrap --version` | [`banc-essai/cage/README.md`](../cage/README.md) |
| systemd de l'utilisateur (plafond de mémoire) | `systemd-run --user --scope true` | idem |
| uv et Python 3.12 | `uv --version` | |
| Docker (relais LiteLLM) | `docker compose version` | [modele-et-fournisseur.md](modele-et-fournisseur.md) |
| relais démarré | `curl -fs http://127.0.0.1:4100/health/liveliness` | idem |
| harnais installé | `harnais/<harnais>/installer.sh` | `harnais/<harnais>/README.md` |
| ports libres | rien n'écoute sur 8765 (API) ni 4100 (relais, déjà pris par lui) | |

## 2. La commande

```bash
banc-essai/cage/lancer.sh <harnais> <recette> [--essai NOM] [--duree SECONDES] [--message "..."]
```

| Paramètre | Valeurs | Défaut |
|---|---|---|
| `<harnais>` | `opencode`, `pi`, `gptme`, `goose`, `cline` (dossiers de `harnais/`), ou `sonde` (preuves de la cage) | |
| `<recette>` | `jouet`, `goldset` | |
| `--essai` | nom du dossier de résultats | `<harnais>-<recette>-<date>` |
| `--duree` | garde-fou de durée, en secondes | 7200 |
| `--message` | premier message donné au harnais | « Suis les consignes de consignes.md. » |

| Recette | Tâche | Jeu noté par l'API | Jeu de relance |
|---|---|---|---|
| `jouet` | petit paquet Python de calcul sur des relevés de dosage, noté par des tests cachés (mise au point d'un harnais, quelques minutes) | tests cachés | aucun |
| `goldset` | extraction dans le goldset importé ([goldset.md](goldset.md)) | `<goldset>/test-cache/` | `<goldset>/relance/` |

Un essai long se lance détaché du terminal, pour survivre à sa fermeture :

```bash
setsid nohup banc-essai/cage/lancer.sh pi goldset --essai essai-01 > ~/banc-espaces/essai-01.log 2>&1 < /dev/null &
```

## 3. Ce que fait le lanceur, dans l'ordre

| Étape | Détail |
|---|---|
| 1. Verrou | un seul essai à la fois sur la machine (`~/banc-espaces/.verrou`) |
| 2. Clé de l'essai | `banc-essai/traces/cles.py` : clé virtuelle, modèle `BANC_MODELE` seul, plafond `BANC_BUDGET_ESSAI`, routes d'appel au modèle seules |
| 3. Espace neuf | `~/banc-espaces/<essai>/travail` : consignes, client `soumettre.py`, jeu fourni ; rien du test caché ni de la relance |
| 4. API de soumission | `127.0.0.1:8765`, 5 soumissions, journal de chaque requête |
| 5. Cage | le harnais est lancé par `/opt/harnais/lancer.sh "<message>"` ; réseau limité au relais du modèle, à l'API et à PyPI, Hugging Face et GitHub ; 16 Go de mémoire, 30 Go de disque, 10 Go de téléchargement, durée plafonnée |
| 6. Fin du harnais | dépense relevée, clé supprimée : un workflow qui l'aurait gardée ne peut plus s'en servir |
| 7. Relance | si le harnais a déclaré sa fin : son workflow est relancé dans la cage, sans lui, sur le jeu de relance, avec une clé neuve |
| 8. Collecte | journal des appels de l'essai et de la relance, réseau, mémoire, disque, code écrit par le harnais, masquage de toute chaîne qui ressemble à une clé, compression des traces de plus de 20 Mo |
| 9. Rapport | `rapport.md` et `rapport.json`, puis index des résultats |

## 4. Suivre un essai en cours

```bash
python3 banc-essai/cage/suivi.py <essai>
```

Une ligne : durée, appels au modèle, coût, soumissions, déclaration de fin, taille de la trace et âge de sa dernière écriture. Aucun contenu n'est affiché. Une trace qui n'est plus écrite depuis longtemps signale un harnais bloqué.

## 5. Arrêter un essai proprement

Le lanceur doit pouvoir finir son travail (clé supprimée, collecte, rapport). On arrête donc la cage, pas le lanceur :

```bash
pgrep -af "timeout --kill-after=30"
kill <PID affiché pour l'essai>
```

Le lanceur reprend la main, supprime la clé et produit un rapport partiel. Arrêter seulement le lanceur laisse vivre les processus de la cage, qui tournent dans leur propre session (constaté pendant la mise au point du banc) ; c'est pourquoi on arrête `timeout`, parent de la cage. Après un arrêt, vérifier qu'aucune clé ne reste :

```bash
ls banc-essai/traces/secrets/ | grep '^cle-'
python3 banc-essai/traces/cles.py --supprimer <essai> <essai>-relance
```

## 6. Lire les résultats

Dossier : `banc-essai/resultats-goldset/<essai>/` pour la recette `goldset` (hors git), `banc-essai/resultats/<essai>/` pour la tâche jouet et la sonde.

| Fichier | Contenu |
|---|---|
| `rapport.md` | synthèse lisible : score final, meilleur score, validation annoncée, relance, construction (appels, jetons, coût, durée), soumissions, détail par champ |
| `essai.json` | mesures de construction |
| `harnais/stdout.log`, `harnais/stderr.log` | trace complète de la session du harnais (format propre à chaque harnais) |
| `traces/appels.jsonl` | un appel au modèle par ligne (sans contenu : jetons, durée, coût, images, outils) |
| `traces/reseau.jsonl` | demandes au filtre réseau de la cage |
| `evaluation/soumissions.jsonl` | soumissions : heure, statut, score |
| `evaluation/fin.json` | déclaration de fin : soumission retenue, score annoncé, commande du workflow |
| `relance/resultat.json` | relance du workflow : JSON produits, score, durée et coût par document |
| `code/` | code écrit par le harnais (ni PDF ni JSON) |

| Mesure | Ce qu'elle dit |
|---|---|
| Score final | qualité sur le test caché de la soumission retenue par le harnais |
| Score de relance | qualité du workflow livré sur des documents jamais vus : la mesure qui compte le plus |
| Documents entièrement justes | part des documents sans aucune erreur : plus sévère que le score par champ |
| Écart annoncé moins test | lucidité du harnais sur la qualité de son travail |
| Taux d'invention, d'omission | valeurs inventées là où rien n'était attendu, valeurs manquées |
| Appels, jetons, coût, durée | coût de construction ; coût par document de la relance : coût d'exploitation |

Index des essais : `banc-essai/resultats-goldset/README.md` (et `banc-essai/resultats/README.md` pour la tâche jouet), régénéré à la fin de chaque essai.
