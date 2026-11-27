# Pi : lancement

Retour : [page d'entrée de Pi](../README.md). Pages voisines : [installation](installation.md), [configuration](configuration.md), [fonctionnement](fonctionnement.md).

Commandes à lancer depuis la racine du dépôt. Le déroulé commun à tous les harnais (verrou, clé, API de soumission, relance, rapport) est décrit dans [`banc-essai/documentation/lancer-un-essai.md`](../../../banc-essai/documentation/lancer-un-essai.md) ; cette page en donne ce qui est propre à Pi.

## 1. Lancer un essai

Avant le premier essai : Pi installé ([installation](installation.md)), relais démarré (`curl -fs http://127.0.0.1:4100/health/liveliness` répond), aucun autre essai en cours.

```bash
banc-essai/cage/lancer.sh pi <recette> [--essai NOM] [--duree SECONDES] [--message "..."]
```

| Recette | Tâche | Ordre de grandeur pour Pi | Préalable |
|---|---|---|---|
| `jouet` | corriger un petit paquet Python, noté par des tests cachés ; sert à vérifier le harnais | `pi-jouet-1` : 23 s, 11 appels, 0,0013 $ | aucun |
| `sans-aide` | extraction dans les rapports d'intervention fictifs, une définition d'une ligne par clé | aucun essai de Pi | aucun |
| `avec-aide` | même tâche, avec l'ontologie des clés | `c1-04-pi-avec-aide` : 27 min, 365 appels, 0,27 $ | aucun |
| `dossiers` | recoupement de pièces par équipement (tâche 2) | aucun essai de Pi | aucun |
| `goldset` | extraction dans le goldset importé | aucun essai terminé de Pi au 27/11/2026 | goldset importé, schéma validé, consignes générées ([`banc-essai/documentation/goldset.md`](../../../banc-essai/documentation/goldset.md)) |

Chiffres tirés de [`banc-essai/resultats/pi-jouet-1/rapport.md`](../../../banc-essai/resultats/pi-jouet-1/rapport.md) et [`banc-essai/resultats/c1-04-pi-avec-aide/rapport.md`](../../../banc-essai/resultats/c1-04-pi-avec-aide/rapport.md) ; les autres recettes n'ont pas encore été essayées avec Pi.

| Option | Effet | Défaut |
|---|---|---|
| `--essai NOM` | nom du dossier de résultats | `pi-<recette>-<AAAAMMJJ-HHMMSS>` |
| `--duree SECONDES` | garde-fou de durée de la cage | 7200 |
| `--message "..."` | message donné à Pi | « Suis les consignes de consignes.md. » |

Exemples :

```bash
banc-essai/cage/lancer.sh pi jouet
banc-essai/cage/lancer.sh pi avec-aide --essai c3-pi-avec-aide
```

Un essai long se lance détaché du terminal, pour survivre à sa fermeture :

```bash
setsid nohup banc-essai/cage/lancer.sh pi goldset --essai essai-01 > ~/banc-espaces/essai-01.log 2>&1 < /dev/null &
```

Le lanceur rend le code de retour de Pi (0 en cas de fin normale ; 124 si le garde-fou de durée a arrêté la cage).

## 2. Ce que fait `harnais/pi/lancer.sh` dans la cage

La cage exécute `/opt/harnais/lancer.sh "<message>"`, c'est-à-dire [`harnais/pi/lancer.sh`](../lancer.sh) monté en lecture seule, avec l'entrée standard fermée.

| Étape | Action |
|---|---|
| 1 | `configurer.sh` écrit `/home/banc/.pi/agent/models.json` et `settings.json` ; son message part sur la sortie d'erreur (première ligne de `stderr.log`) |
| 2 | `PATH` commence par `/opt/harnais/installe/node/bin` ; `PI_SKIP_VERSION_CHECK=1`, `PI_OFFLINE=1`, `PI_TELEMETRY=0` exportées |
| 3 | `exec node .../dist/bundle/cli.js --mode json --provider banc --model "$BANC_MODELE" -- "<message>"` |

Commande exacte :

```bash
node /opt/harnais/installe/pi/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js \
  --mode json --provider banc --model "$BANC_MODELE" -- "$*"
```

| Élément | Effet (référence : [cli.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md), consulté le 27/11/2026) |
|---|---|
| `--mode json` | exécute le message, écrit les événements de la session en JSONL sur la sortie standard, puis s'arrête |
| `--provider banc` | limite la recherche du modèle au fournisseur `banc` de `models.json` |
| `--model "$BANC_MODELE"` | modèle exposé par le relais (`banc-essai/modele.env`) |
| `--` | fin des options : le message peut commencer par un tiret |
| `"$*"` | tous les arguments de `lancer.sh` réunis en un seul message |

Environnement vu par Pi dans la cage (relevé le 27/11/2026, clé exclue) :

```text
BANC_MODELE_URL=http://127.0.0.1:4100
BANC_MODELE=deepseek-v4.1-flash
BANC_CONTEXTE=1000000
BANC_SORTIE_MAX=32768
BANC_VISION=1
BANC_PRIX_ENTREE=0.05
BANC_PRIX_CACHE=0.003
BANC_PRIX_SORTIE=0.30
BANC_API=http://127.0.0.1:8765
HTTPS_PROXY=http://127.0.0.1:3128
HTTP_PROXY=http://127.0.0.1:3128
NO_PROXY=127.0.0.1,localhost
```

S'y ajoutent `BANC_CLE_MODELE` (clé de l'essai), `HOME=/home/banc`, et `BANC_API_ACTIVE=1` dans un essai. Pi travaille dans `/travail` (dossier courant), qui contient les consignes de la recette, le client de soumission et le jeu fourni.

## 3. Sorties et où les trouver

| Emplacement | Contenu | Dans git |
|---|---|---|
| `banc-essai/resultats/<essai>/harnais/stdout.log` | trace JSONL de Pi (section 4) ; compressée en `stdout.log.gz` au-delà de 20 Mo | oui (goldset : non) |
| `banc-essai/resultats/<essai>/harnais/stderr.log` | message de `configurer.sh`, puis diagnostics de Pi s'il y en a ; une seule ligne dans les deux essais réels | idem |
| `banc-essai/resultats/<essai>/traces/appels.jsonl` | appels au modèle de la clé de l'essai, vus par le relais (jetons, durée, coût, images, outils, erreurs) | idem |
| `banc-essai/resultats/<essai>/code/` | code écrit par Pi dans l'espace de travail (ni PDF ni JSON) | idem |
| `banc-essai/resultats/<essai>/rapport.md`, `essai.json` | rapport et mesures de l'essai | idem |
| `~/banc-espaces/<essai>/maison/.pi/agent/sessions/--travail--/<horodatage>_<id>.jsonl` | session enregistrée par Pi (même contenu que la trace, sans les morceaux de réponse en flux) | non, hors dépôt |
| `~/banc-espaces/<essai>/maison/.pi/agent/` | `models.json`, `settings.json`, `auth.json`, `models-store.json` de l'essai | non |
| `~/banc-espaces/<essai>/travail/` | espace de travail final (workflow, sorties) | non |

Pour la recette `goldset`, le dossier de résultats est `banc-essai/resultats-goldset/<essai>/`, hors git : la trace recopie le texte des documents lus.

## 4. Format de la trace

`stdout.log` est un flux JSONL : un objet JSON par ligne, défini par [json.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/json.md) (consulté le 27/11/2026).

| Événement | Contenu | Nombre dans `pi-jouet-1` | Nombre dans `c1-04-pi-avec-aide` |
|---|---|---|---|
| `session` | en-tête : version du format (3), identifiant, heure, dossier de travail | 1 | 1 |
| `agent_start`, `agent_end` | début et fin d'une exécution ; `agent_end` contient tous les messages produits | 1 | 1 |
| `turn_start`, `turn_end` | un tour = une réponse du modèle et les outils qu'elle appelle ; `turn_end` porte le message complet (fournisseur, modèle, jetons, coût, raison d'arrêt) | 11 | 99 |
| `message_start`, `message_end` | début et fin d'un message (système, utilisateur, modèle, résultat d'outil) ; `message_end` fait foi (nombre de chacun) | 28 | 199 |
| `message_update` | morceau de réponse en flux (texte ou appel d'outil), écrit au fil de l'eau | 595 | 8 684 |
| `tool_execution_start`, `_update`, `_end` | appel d'outil : nom, arguments, résultat (nombre de `tool_execution_start`) | 15 | 98 |
| `agent_settled` | Pi n'a plus rien à faire ; `aborted` vaut `true` si l'exécution a été interrompue | 1 | 1 |

Comptes relevés le 27/11/2026 dans les traces des deux essais. Le premier `message_start` contient l'invite système de Pi, découpée en sections (`preamble`, `tools`, `rules`, `docs`, `cwd`).

Outils appelés et dernier message du modèle (Python seul, sans dépendance ; pour une trace compressée, remplacer `open(...)` par `gzip.open(..., "rt")`) :

```bash
python3 - banc-essai/resultats/pi-jouet-1/harnais/stdout.log <<'PY'
import json, sys, collections
outils = collections.Counter()
for ligne in open(sys.argv[1]):
    e = json.loads(ligne)
    if e["type"] == "tool_execution_start":
        outils[e["toolName"]] += 1
    if e["type"] == "agent_end":
        fin = [m for m in e["messages"] if m["role"] == "assistant"][-1]
        print("".join(b.get("text", "") for b in fin["content"] if b["type"] == "text"))
print(dict(outils))
PY
```

Résultat pour `pi-jouet-1` : `{'bash': 9, 'read': 5, 'edit': 1}`. Pour `c1-04-pi-avec-aide` : `{'bash': 77, 'read': 21}`.

Lecture dans un navigateur : Pi exporte une session en page HTML, sans réseau ni modèle (essayé le 27/11/2026 sur la session de `pi-jouet-1`). `PI_CODING_AGENT_DIR` pointe vers un dossier jetable pour que Pi n'écrive rien dans `~/.pi` du compte :

```bash
PI_OFFLINE=1 PI_CODING_AGENT_DIR=$(mktemp -d) harnais/pi/installe/node/bin/node \
  harnais/pi/installe/pi/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js \
  --export ~/banc-espaces/pi-jouet-1/maison/.pi/agent/sessions/--travail--/<fichier>.jsonl /tmp/session.html
```

La page exportée contient tout le contenu de la session : ne pas la diffuser pour un essai `goldset`.

## 5. Suivre un essai en cours

```bash
python3 banc-essai/cage/suivi.py <essai>
```

Une ligne : durée, appels au modèle et échecs, coût, soumissions, déclaration de fin, taille de la trace et âge de sa dernière écriture. Pi écrit sa trace à chaque morceau de réponse : une trace qui ne grossit plus depuis plusieurs minutes alors qu'aucune commande longue ne tourne signale un blocage. Nombre de tours déjà faits :

```bash
grep -c '"type":"turn_end"' banc-essai/resultats/<essai>/harnais/stdout.log
```

## 6. Arrêter un essai proprement

On arrête la cage, pas le lanceur, pour que le lanceur supprime la clé et écrive un rapport partiel :

```bash
pgrep -af "timeout --kill-after=30"
kill <PID de la ligne qui cite l'essai>
```

Procédure complète et contrôle des clés restantes : [`banc-essai/documentation/lancer-un-essai.md`](../../../banc-essai/documentation/lancer-un-essai.md), section 5. Pi n'a pas de procédure d'arrêt propre : il est arrêté avec la cage ; sa session reste lisible jusqu'au dernier message enregistré.

## 7. Essai à la main hors banc

Lancer Pi directement sur le poste, hors de la cage, n'est pas sans risque : Pi exécute sans confirmation les commandes proposées par le modèle, avec tous les droits du compte (dépôt, `.env`, test caché, réseau) ; sa documentation recommande de le faire tourner dans un conteneur, une machine virtuelle ou un bac à sable ([security.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md), consulté le 27/11/2026). Le banc ne prévoit donc pas d'essai hors cage.

Sans appel au modèle, les commandes de la page [installation](installation.md), section 5 (version, liste des modèles dans la cage) et l'export HTML ci-dessus suffisent à vérifier Pi.

Pour un échange avec le modèle sans le cadre d'un essai (sans API de soumission, sans relance ni rapport), la cage peut être appelée directement avec une clé temporaire. Commande composée à partir des interfaces de `cles.py` et `cage.sh`, non exécutée lors de la rédaction (elle appelle le modèle) ; à ne pas lancer pendant un essai :

```bash
ESSAI=manuel-pi-$(date +%Y%m%d-%H%M%S)
D=~/banc-espaces/$ESSAI && mkdir -p "$D/travail" "$D/maison"
python3 banc-essai/traces/cles.py "$ESSAI"
banc-essai/cage/cage.sh --espace "$D/travail" --maison "$D/maison" --harnais harnais/pi \
  --cle "banc-essai/traces/secrets/cle-$ESSAI.env" --duree 600 \
  -- /opt/harnais/lancer.sh "Crée un fichier bonjour.txt qui contient Bonjour." \
  < /dev/null > "$D/stdout.log" 2> "$D/stderr.log"
python3 banc-essai/traces/cles.py --supprimer "$ESSAI"
```

Les appels apparaissent dans le journal du relais (`banc-essai/traces/journaux/appels.jsonl`) sous l'alias de la clé. Une session interactive (interface en terminal) dans la cage n'est pas prévue : `cage.sh` lance bubblewrap avec `--new-session`, qui détache le processus du terminal ; non essayé sur le banc.
