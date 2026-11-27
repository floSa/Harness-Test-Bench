# Cline : lancement

[Retour à la page d'entrée](../README.md)

Sur le banc, Cline ne se lance pas directement : c'est le lanceur d'essai du banc qui prépare l'espace de travail, la clé et la cage, puis appelle `harnais/cline/lancer.sh` dans la cage. Toutes les commandes se lancent depuis la racine du dépôt.

## 1. Lancer un essai

Prérequis : Cline installé ([installation](installation.md)), relais démarré (`banc-essai/traces/demarrer.sh`), aucun autre essai en cours (un seul à la fois, verrou `~/banc-espaces/.verrou`).

```bash
banc-essai/cage/lancer.sh cline <recette> [--essai NOM] [--duree SECONDES] [--message "..."]
```

| Critère | `jouet` | `goldset` |
|---|---|---|
| Tâche | vérification du branchement : corriger un petit paquet Python | extraction dans le goldset de PDF de l'équipe (jeu de PDF et de réponses attendues, importé et validé au préalable) |
| Jeu noté par l'API | cas cachés de `banc-essai/evaluation/taches/jouet` | `$BANC_GOLDSET/test-cache` (`banc-essai/corpus/goldset` par défaut) |
| Résultats écrits dans | `banc-essai/resultats/<essai>/` (dossier créé par le lanceur) | `banc-essai/resultats-goldset/<essai>/`, hors git |
| Commande | `banc-essai/cage/lancer.sh cline jouet` | `banc-essai/cage/lancer.sh cline goldset` |

Source : en-tête et corps de [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh). Le nom de l'essai vaut par défaut `cline-<recette>-<date>-<heure>` ; le message envoyé à Cline vaut par défaut « Suis les consignes de consignes.md. ». La recette `goldset` refuse de démarrer si `schema.json` n'est pas validé ou si les consignes manquent ([goldset.md](../../../banc-essai/documentation/goldset.md)).

L'essai jouet est court et ne sert qu'à vérifier le branchement. La durée et la consommation d'un essai goldset dépendent du nombre de documents et du modèle ; aucun essai d'extraction de Cline n'a été fait pendant la mise au point du banc ([fonctionnement](fonctionnement.md#2-comportements-constatés-lors-des-essais-de-mise-au-point)).

## 2. Ce qui se passe dans la cage

| Étape | Qui | Détail |
|---|---|---|
| 1 | `banc-essai/cage/lancer.sh` | espace neuf `~/banc-espaces/<essai>/{travail,maison,tmp}`, clé virtuelle de l'essai, API de soumission sur `127.0.0.1:8765`, puis `cage.sh … -- /opt/harnais/lancer.sh "<message>"` avec l'entrée standard fermée, la sortie standard dans `harnais/stdout.log`, l'erreur dans `harnais/stderr.log` |
| 2 | `banc-essai/cage/cage.sh` | bubblewrap : `harnais/cline/` monté en lecture seule sur `/opt/harnais`, `HOME=/home/banc`, dossier courant `/travail`, variables `BANC_*` du modèle, `HTTPS_PROXY` vers le filtre ; mémoire 16 Go, garde-fou de durée (7 200 s par défaut) |
| 3 | `banc-essai/cage/interieur.sh` | relais intérieurs (`127.0.0.1:4100` modèle, `:3128` filtre, `:8765` API), chargement de `BANC_CLE_MODELE` depuis `/run/banc/cle.env` |
| 4 | `harnais/cline/lancer.sh` | `configurer.sh` (`cline auth`, sortie renvoyée sur l'erreur standard), Node du harnais en tête du `PATH`, puis `exec cline --json -y "<message>"` ; les arguments sont réunis en un seul message (`"$*"`) |
| 5 | Cline | une session non interactive dans `/travail` : boucle appel au modèle, outils (`run_commands`, `editor`…), jusqu'à l'outil `submit_and_exit` ; la commande se termine avec la session |
| 6 | `banc-essai/cage/lancer.sh` | dépense relevée, clé supprimée, relance du workflow déclaré (recette `goldset` seulement), collecte, masque des clés, rapport |

## 3. Sorties et où les trouver

Dans `banc-essai/resultats/<essai>/` (ou `banc-essai/resultats-goldset/<essai>/`), d'après [la cage](../../../banc-essai/cage/README.md) et les essais de mise au point :

| Fichier | Contenu pour Cline |
|---|---|
| `harnais/stdout.log` | trace complète de Cline en NDJSON (section 4) ; compressée en `stdout.log.gz` au-delà de 20 Mo |
| `harnais/stderr.log` | ligne « Provider configured: openai-compatible (<modèle>) » de `configurer.sh`, avec des codes de couleur ; erreurs éventuelles de Cline (`{"type":"error",…}` d'après la [CLI reference](https://docs.cline.bot/cline-cli/cli-reference.md), consulté le 27/11/2026) |
| `essai.json`, `rapport.md`, `rapport.json` | mesures et rapport du banc (durée, appels, jetons, coût, score) |
| `traces/appels.jsonl` | appels au modèle vus par le relais |
| `traces/reseau.jsonl` | demandes au filtre : on y voit `registry.npmjs.org` et `data.cline.bot` refusés |
| `evaluation/` | soumissions et fin déclarée, journaux de l'API |
| `code/` | code écrit par le harnais, archivé pour relecture par `banc-essai/cage/archiver_code.py` |

Restent hors du dépôt, dans `~/banc-espaces/<essai>/` :

| Chemin | Contenu |
|---|---|
| `travail/` | espace de travail tel que Cline l'a laissé |
| `maison/.cline/data/sessions/<id>/<id>.json` | résumé de la session (modèle, consigne, jetons, coût, `enable_spawn`, `enable_teams`) |
| `maison/.cline/data/sessions/<id>/<id>.messages.json` | conversation complète ; n'est pas copiée dans les résultats |
| `maison/.cline/data/logs/cline.log` | journal d'exécution de Cline |
| `maison/.cline/data/settings/providers.json` | configuration, avec la clé de l'essai (supprimée du relais) |

## 4. Format de la trace

Une ligne JSON par événement, chacune avec `ts` (horodatage ISO 8601) et `type` ([CLI reference](https://docs.cline.bot/cline-cli/cli-reference.md), consulté le 27/11/2026 : types `agent_event`, `hook_event`, `team_event`, `run_result`, `run_aborted`). Types relevés dans les traces des essais de mise au point du banc :

| `type` | `event.type` | Contenu |
|---|---|---|
| `agent_event` | `iteration_start`, `iteration_end` | début et fin d'un tour ; `iteration_end` donne `hadToolCalls` et `toolCallCount` |
| `agent_event` | `usage` | jetons et coût de l'appel et cumulés (`inputTokens`, `outputTokens`, `cacheReadTokens`, `cost`, `totalCost`) |
| `agent_event` | `content_start` | morceau de raisonnement du modèle, ou appel d'outil (`toolName`, `input`) ; les morceaux de raisonnement sont de loin les plus nombreux |
| `agent_event` | `content_update` | sortie au fil de l'eau d'une commande |
| `agent_event` | `content_end` | fin d'un raisonnement ou résultat d'un outil (`output`) |
| `agent_event` | `done` | fin de l'agent, avec le texte final (une fois par session) |
| `run_result` | | bilan, une fois par session : `finishReason`, `iterations`, `usage`, `aggregateUsage`, `durationMs`, `text`, `model` |

Forme des lignes (abrégées ; identifiants et valeurs numériques remplacés) :

```text
{"ts":"<horodatage>","type":"agent_event","event":{"type":"content_start","contentType":"tool","toolName":"run_commands","toolCallId":"<id>","input":{"commands":["ls -la /travail","cat /travail/consignes.md"]}}}
{"ts":"<horodatage>","type":"run_result","finishReason":"completed","iterations":<n>,"usage":{"inputTokens":<n>,"outputTokens":<n>,"cacheReadTokens":<n>,"cacheWriteTokens":<n>,"totalCost":<n>},"durationMs":<n>,"text":"Submission recorded (verified): …","model":{"id":"modele-banc","provider":"openai-compatible"}}
```

Lire la trace sans outil supplémentaire (`jq` n'est pas forcément installé sur le poste) :

```bash
# Appels d'outils, dans l'ordre
python3 -c '
import json, sys
for ligne in open(sys.argv[1]):
    d = json.loads(ligne); e = d.get("event") or {}
    if e.get("type") == "content_start" and e.get("contentType") == "tool":
        print(d["ts"], e["toolName"], json.dumps(e.get("input"), ensure_ascii=False)[:100])
' banc-essai/resultats/<essai>/harnais/stdout.log
```

```bash
# Bilan de la session
python3 -c '
import json, sys
for ligne in open(sys.argv[1]):
    d = json.loads(ligne)
    if d["type"] == "run_result":
        print(d["finishReason"], d["iterations"], "itérations,", d["durationMs"] / 1000, "s,", d["usage"])
' banc-essai/resultats/<essai>/harnais/stdout.log
```

Pour un essai goldset, remplacer `banc-essai/resultats/` par `banc-essai/resultats-goldset/`. Forme de la sortie de la seconde commande :

```text
completed <n> itérations, <durée> s, {'inputTokens': <n>, 'outputTokens': <n>, 'cacheReadTokens': <n>, 'cacheWriteTokens': <n>, 'totalCost': <coût>}
```

Les chiffres qui font foi pour le banc sont ceux du relais (`essai.json`), pas ceux de Cline : lors des essais de mise au point du banc, Cline comptait nettement moins de jetons de sortie que le relais ; l'écart vient probablement des jetons de raisonnement (non vérifié). Les jetons d'entrée, le cache et le coût concordaient.

## 5. Suivre un essai en cours

```bash
python3 banc-essai/cage/suivi.py <essai>
```

Une ligne : minutes écoulées, appels au modèle et échecs, coût, soumissions, fin déclarée, taille et âge de la dernière écriture de la trace ([lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section « Suivre un essai en cours »). Une trace qui ne grossit plus pendant plusieurs minutes alors que les appels continuent n'est pas anormale (raisonnement long) ; une trace et des appels figés le sont.

Suivre la trace elle-même (outils appelés au fil de l'eau) :

```bash
tail -f banc-essai/resultats/<essai>/harnais/stdout.log | grep --line-buffered '"contentType":"tool","toolName"'
```

(essai goldset : `banc-essai/resultats-goldset/<essai>/harnais/stdout.log`).

## 6. Arrêter un essai proprement

Arrêter la cage, pas le lanceur, pour qu'il supprime la clé et écrive un rapport partiel ([lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section « Arrêter un essai proprement ») :

```bash
pgrep -af "timeout --kill-after=30"
kill <PID affiché pour l'essai>
ls banc-essai/traces/secrets/ | grep '^cle-'      # aucune clé ne doit rester
```

Arrêts propres à Cline, sans intervention : fin normale par `submit_and_exit` ; sortie après 3 erreurs consécutives (`--retries`, 3 par défaut, `cline --help`) ; Cline n'a pas de délai propre (`-t`, 0 par défaut) : le garde-fou de la cage s'applique.

## 7. Essai à la main

Hors de la cage, sans risque, seules les commandes qui n'appellent pas le modèle sont recommandées : `--version`, `--help`, `auth --help`, et `configurer.sh` avec un dossier personnel temporaire et des valeurs factices :

```bash
T=$(mktemp -d)
HOME=$T BANC_MODELE_URL=http://127.0.0.1:4100 BANC_MODELE=modele-banc BANC_CLE_MODELE=sk-factice \
  CLINE_NO_AUTO_UPDATE=1 harnais/cline/configurer.sh
cat "$T/.cline/data/settings/providers.json"
rm -rf "$T"
```

Une tâche réelle hors cage (`cline -y "…"`) donnerait au modèle les droits de l'utilisateur sur tout le poste, le dépôt, le test caché et `.env` compris : à ne pas faire sur le banc.

Une tâche à la main reste possible dans la cage, sans API de soumission, avec une clé créée puis supprimée à la main (non essayé pour Cline) :

```bash
python3 banc-essai/traces/cles.py manuel-cline                       # écrit banc-essai/traces/secrets/cle-manuel-cline.env
mkdir -p ~/banc-espaces/manuel-cline/{travail,maison}
banc-essai/cage/cage.sh --espace ~/banc-espaces/manuel-cline/travail --maison ~/banc-espaces/manuel-cline/maison \
  --harnais harnais/cline --cle banc-essai/traces/secrets/cle-manuel-cline.env \
  -- /opt/harnais/lancer.sh "Écris un fichier bonjour.txt qui contient Bonjour."
python3 banc-essai/traces/cles.py --supprimer manuel-cline
```

La trace NDJSON s'affiche dans le terminal ; le fichier produit est dans `~/banc-espaces/manuel-cline/travail/`. Le relais compte la dépense sur la clé `manuel-cline`. Le verrou d'essai n'est pas pris par `cage.sh` : ne pas lancer cette commande pendant un essai.

Commandes de Cline qui démarrent un service d'arrière-plan (« hub », constaté avec `cline history` hors cage) : l'arrêter avec `cline hub stop` et le même `HOME`. Dans la cage, les essais de mise au point du banc ont tourné sans hub (`"backendMode":"local"` dans `cline.log`).
