# Lancement de Goose

Retour : [page d'entrée du harnais](../README.md). Pages voisines : [installation](installation.md), [configuration](configuration.md), [fonctionnement](fonctionnement.md).

Toutes les commandes s'exécutent depuis la racine du dépôt.

## 1. Avant de lancer

| Condition | Vérification | Si elle manque |
|---|---|---|
| Goose installé | `harnais/goose/installe/goose --version` affiche `1.60.1` | [installation](installation.md) |
| Relais LiteLLM démarré | `curl -fs http://127.0.0.1:4100/health/liveliness` réussit | `banc-essai/traces/demarrer.sh` ; sinon le lanceur s'arrête avec `LiteLLM du banc arrêté` |
| Aucun autre essai en cours | `systemctl --user list-units --type=scope 'banc-cage-*'` ne liste rien | attendre : un seul essai à la fois (verrou `~/banc-espaces/.verrou`), sinon `un autre essai tourne déjà` |
| Port 8765 libre | `ss -ltn 'sport = :8765'` ne liste rien | sinon `port 8765 déjà pris` |
| Goldset seulement | `schema.json` validé et `recette/consignes.md` présents dans le goldset | voir la documentation du banc (`banc-essai/documentation/goldset.md`, cité par le lanceur) |

Sources : [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh), [`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md).

## 2. Lancer un essai

```bash
banc-essai/cage/lancer.sh goose <recette> [--essai NOM] [--duree SECONDES] [--message "TEXTE"]
```

| Recette | Tâche | Jeu noté pendant l'essai | Relance du workflow | Dossier des résultats |
|---|---|---|---|---|
| `jouet` | petite tâche de programmation avec tests cachés (mise au point) | tests cachés de `banc-essai/evaluation/taches/jouet` | non | `banc-essai/resultats/<essai>/` (dossier créé par le lanceur) |
| `goldset` | extraction dans le goldset de PDF de l'équipe, importé (`$BANC_GOLDSET`, défaut `banc-essai/corpus/goldset`) | `test-cache` du goldset | oui, sur `relance` du goldset | `banc-essai/resultats-goldset/<essai>/` (hors git) |

| Option | Défaut | Effet |
|---|---|---|
| `--essai NOM` | `goose-<recette>-<AAAAMMJJ-HHMMSS>` | nom de l'essai, du dossier de résultats et de la clé ; refus si le dossier existe déjà |
| `--duree S` | 7200 | garde-fou de durée de la cage, en secondes |
| `--message "..."` | `Suis les consignes de consignes.md.` | texte transmis à Goose |

Exemples :

```bash
banc-essai/cage/lancer.sh goose jouet
banc-essai/cage/lancer.sh goose goldset --essai goose-goldset-01
BANC_GOLDSET=/chemin/du/goldset banc-essai/cage/lancer.sh goose goldset
```

Le lanceur affiche une ligne `essai <nom> : harnais goose, recette <recette>, espace <dossier>`, puis rend la main à la fin de l'essai (moins d'une minute pour la tâche jouet ; une extraction dans des PDF peut dépasser une heure : voir [fonctionnement](fonctionnement.md)). Pour un essai long, le lancer dans une session qui survit à la fermeture du terminal (`tmux`, `screen`, ou `setsid nohup … &` comme dans [`banc-essai/documentation/lancer-un-essai.md`](../../../banc-essai/documentation/lancer-un-essai.md), section 2).

## 3. Ce que fait le lanceur du banc

Résumé de [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh) ; le détail est dans la documentation du banc.

| Étape | Action |
|---|---|
| 1 | espace neuf hors du dépôt : `~/banc-espaces/<essai>/travail` (espace de travail, `/travail` dans la cage), `maison` (`/home/banc`), `tmp` |
| 2 | clé virtuelle propre à l'essai (alias = nom de l'essai, plafond `BANC_BUDGET_ESSAI` de `modele.env`) |
| 3 | API de soumission sur `127.0.0.1:8765` |
| 4 | cage : `cage.sh … -- /opt/harnais/lancer.sh "<message>"`, entrée standard fermée, sortie standard vers `harnais/stdout.log`, sortie d'erreur vers `harnais/stderr.log` |
| 5 | à la sortie du harnais : dépense relevée, clé supprimée, relance du workflow déclaré avec une clé neuve (sauf jouet, et seulement si le harnais a déclaré la fin) |
| 6 | collecte : `essai.json`, appels au modèle, code produit, masquage des clés, rapport, compression des traces de plus de 20 Mo, index des résultats |

## 4. Ce que fait `harnais/goose/lancer.sh` dans la cage

Le dossier `harnais/goose/` est monté en lecture seule sur `/opt/harnais` ; la cage exécute `/opt/harnais/lancer.sh "<message>"`.

| Étape | Commande | Effet |
|---|---|---|
| 1 | `"$ICI/configurer.sh" >&2` | écrit `/home/banc/.config/goose/config.yaml` ([configuration](configuration.md)) ; message dans `stderr.log` |
| 2 | `export GOOSE_DISABLE_KEYRING=1 GOOSE_TELEMETRY_ENABLED=false GOOSE_DISABLE_SESSION_NAMING=true GOOSE_MODE=auto` | réglages forcés par l'environnement |
| 3 | `export OPENAI_API_KEY="${BANC_CLE_MODELE:?}"` | clé de l'essai ; arrêt si elle manque |
| 4 | `export GOOSE_CONTEXT_LIMIT="$BANC_CONTEXTE"`, seulement si `BANC_CONTEXTE` est inférieur à 128 000 | fenêtre de contexte déclarée à Goose ([configuration, section 7](configuration.md#7-fenêtre-de-contexte)) |
| 5 | `goose run --with-builtin developer -n essai --output-format stream-json -t "$*"` | exécution sans interaction |
| 6 | `goose session export -n essai --format json -o "$HOME/goose-session.json"` | export de la session, même après un échec de l'étape 5 ; une erreur d'export est ignorée |
| 7 | `exit "$code"` | code de retour de `goose run`, recopié dans `essai.json` (`code_retour`) |

Options de `goose run` utilisées (texte de `goose run --help`, version 1.60.1) :

| Option | Rôle |
|---|---|
| `--with-builtin developer` | ajoute l'extension intégrée `developer` : commandes `shell`, écriture et édition de fichiers, lecture d'images |
| `-n essai` | nom de la session, réutilisé par l'export |
| `--output-format stream-json` | événements JSON au fil de l'eau sur la sortie standard (`text` par défaut, `json` en fin de session) |
| `-t "<message>"` | consigne de départ, à la place d'un fichier d'instructions |

Options disponibles mais non utilisées : `--no-session` (aucune session enregistrée), `--max-turns` (tours sans intervention, défaut 1000), `--no-profile` (seules les extensions de la ligne de commande), `--recipe` et `--params` (recettes), `--stats`, `--debug`, `-q`.

## 5. Sorties produites et où les trouver

### Dans `banc-essai/resultats/<essai>/` (ou `banc-essai/resultats-goldset/<essai>/`)

| Fichier | Contenu propre à Goose |
|---|---|
| `harnais/stdout.log` | trace complète de la session en événements JSON (section 6) ; `stdout.log.gz` si elle dépasse 20 Mo |
| `harnais/stderr.log` | deux lignes en temps normal : `configuration écrite : /home/banc/.config/goose/config.yaml` et `Session exported to /home/banc/goose-session.json` |
| `essai.json` | mesures de l'essai, dont `version_harnais` (`goose 1.60.1`, lu dans `harnais/goose/version`) et `code_retour` |
| `rapport.md`, `rapport.json` | rapport d'essai (scores, construction, soumissions) |
| `traces/appels.jsonl` | appels au modèle vus par le relais |
| `traces/reseau.jsonl` | demandes au mandataire filtrant (dont `models.dev`, refusé) |
| `traces/memoire.json`, `disque.txt`, `gpu.txt` | relevés de ressources |
| `evaluation/` | soumissions et accès à l'API |
| `relance/` | relance du workflow déclaré (pas pour `jouet`) |
| `code/` | code écrit par Goose, archivé pour la relecture (ni PDF ni JSON) |

### Dans `~/banc-espaces/<essai>/` (hors dépôt, non collecté)

| Chemin | Contenu |
|---|---|
| `travail/` | espace de travail de l'essai, tel que Goose l'a laissé |
| `maison/goose-session.json` | session exportée (format JSON complet de Goose : `conversation`, `accumulated_usage`, `model_config`, extensions activées, mode) |
| `maison/.config/goose/config.yaml` | configuration écrite par `configurer.sh` |
| `maison/.local/share/goose/sessions/sessions.db` | base SQLite des sessions ([journalisation](https://goose-docs.ai/docs/guides/logs), consulté le 27/11/2026) |
| `maison/.local/state/goose/logs/cli/<date>/<horodatage>.log` | journal de Goose en JSON (avertissements, compactions) |
| `maison/.local/state/goose/logs/llm_request.<n>.jsonl` | fichiers de requêtes au modèle (dix dans un essai long) |

Emplacements constatés lors des essais de mise au point du banc. L'export `goose-session.json` et les journaux de Goose ne sont pas recopiés dans les résultats ; ils disparaissent avec l'espace de l'essai.

Pour un essai `goldset`, ces fichiers (trace, session, requêtes) contiennent le texte des PDF de l'équipe : ne jamais les copier dans le dépôt ni les transmettre.

## 6. Format de la trace (`stream-json`)

`harnais/stdout.log` commence par quatre lignes de bandeau qui ne sont pas du JSON (ligne vide, puis `__( O)>  ● new session · openai <modèle>`, l'identifiant et le dossier de la session, `goose is ready`). Ensuite, chaque ligne est un objet JSON.

| `type` | Contenu |
|---|---|
| `message` | un fragment de message : `message.role` (`assistant` ou `user`), `message.id`, `message.created`, `message.content` (liste), `message.metadata` (dont `inference.provider`, `inference.requestedModel`, et `operations.llm.advertised_tools`, liste des outils présentés au modèle) |
| `complete` | dernière ligne : `total_tokens`, `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_write_input_tokens`, `cost_usd` |

| Élément de `message.content` | Contenu |
|---|---|
| `text` | texte de la réponse, par fragments |
| `thinking` | raisonnement du modèle, par fragments |
| `toolRequest` | appel d'outil : `id`, `toolCall.value.name`, `toolCall.value.arguments` |
| `toolResponse` | résultat (rôle `user`) : `id`, `toolResult.value.content` (texte, image) |
| `systemNotification` | message de Goose, par exemple la compaction du contexte |

Constaté lors des essais de mise au point du banc : la trace compte toujours quatre lignes de bandeau et une seule ligne `complete` ; les fragments `thinking` en forment l'essentiel ; les notifications n'apparaissent qu'en cas de compaction ; l'outil `shell` domine largement les appels d'outils.

Les réponses arrivent en flux : un même message occupe de nombreuses lignes (un fragment par ligne). Pour compter les appels d'outils en ignorant le bandeau :

```bash
python3 - banc-essai/resultats/<essai>/harnais/stdout.log <<'EOF'
import collections, json, sys
outils = collections.Counter()
for ligne in open(sys.argv[1]):
    try:
        e = json.loads(ligne)
    except json.JSONDecodeError:
        continue
    if e.get("type") == "message":
        for c in e["message"]["content"]:
            if c.get("type") == "toolRequest":
                outils[c["toolCall"]["value"]["name"]] += 1
    elif e.get("type") == "complete":
        print("jetons :", e["input_tokens"], "entrée,", e["output_tokens"], "sortie")
print(dict(outils))
EOF
```

## 7. Suivre un essai en cours

```bash
python3 banc-essai/cage/suivi.py <essai>
```

Une ligne : durée, appels au modèle (dont échecs), coût, soumissions acceptées et scores, déclaration de fin, taille de la trace et âge de sa dernière écriture, essai terminé ou non ([`banc-essai/cage/suivi.py`](../../../banc-essai/cage/suivi.py) ; aucun contenu affiché). Pour la répéter toutes les minutes :

```bash
watch -n 60 python3 banc-essai/cage/suivi.py <essai>
```

Repères pour Goose : la trace grossit en continu tant que le modèle répond (fragments `thinking`) ; une trace immobile pendant plusieurs minutes avec des appels qui n'augmentent pas indique en général une commande longue lancée par Goose dans la cage (installation, traitement de PDF).

## 8. Arrêter un essai proprement

Le garde-fou arrête la cage seul au bout de `--duree` secondes (7200 par défaut : `timeout --kill-after=30`, [`banc-essai/cage/cage.sh`](../../../banc-essai/cage/cage.sh)). Pour arrêter plus tôt, la méthode du banc est décrite dans [`banc-essai/documentation/lancer-un-essai.md`, section 5](../../../banc-essai/documentation/lancer-un-essai.md#5-arrêter-un-essai-proprement) : arrêter la cage (le processus `timeout` qui en est le parent), pas le lanceur, pour que celui-ci supprime la clé, collecte les résultats et produise un rapport partiel. Rien n'est propre à Goose dans cette procédure.

### Arborescence des processus

D'après les scripts, et vérifié sur un essai en cours (`ps`, `systemctl --user list-units`) :

```text
banc-essai/cage/lancer.sh          (terminal de l'utilisateur)
└── banc-essai/cage/cage.sh        (tâche de fond de lancer.sh)
    └── unité systemd banc-cage-banc-cage-XXXXXX.scope
        └── timeout 7200 bwrap …   (groupe de processus propre)
            └── bwrap … (nouvelle session, espaces de noms propres)
                └── interieur.sh → /opt/harnais/lancer.sh → goose run → commandes lancées par Goose
```

Variante non éprouvée sur le banc, déduite de `cage.sh` (cage lancée par `systemd-run --user --scope`) : arrêter l'unité systemd de la cage, ce qui arrête tous ses processus (Goose et ce qu'il a lancé).

```bash
systemctl --user list-units --type=scope 'banc-cage-*' --no-pager   # la description contient ~/banc-espaces/<essai>/
systemctl --user stop banc-cage-banc-cage-XXXXXX.scope               # nom relevé à la ligne précédente
```

### À éviter

Ctrl+C dans le terminal du lanceur, ou l'arrêt du seul `lancer.sh`, ne suffit pas : `cage.sh` est une tâche de fond d'un script non interactif, qui ignore Ctrl+C ; `timeout` et `bwrap --new-session` sont dans leur propre groupe et leur propre session, que le terminal n'atteint pas. Le lanceur s'arrête alors et supprime la clé de l'essai (fonction `fin_de_script`), mais Goose continue dans la cage, ses appels au modèle échouent, et rien n'est collecté.

Constaté lors des essais de mise au point du banc : après l'arrêt du seul lanceur, la trace de Goose s'est arrêtée, mais les relevés écrits par les boucles du lanceur et de `cage.sh` (`traces/gpu.txt` et `traces/memoire.json`, qui ne tournent que tant que ces scripts vivent) ont continué d'être mis à jour pendant plusieurs minutes : les processus de la cage survivaient à l'arrêt.

### Vérifier qu'il ne reste rien

```bash
systemctl --user list-units --type=scope 'banc-cage-*' --no-pager
ps -eo pid,etime,cmd | grep -E '[g]oose run|[b]wrap --die-with-parent|[c]age/cage.sh'
```

S'il reste un processus, l'arrêter par son numéro (`kill <pid>`, puis `kill -9 <pid>` s'il ne s'arrête pas), jamais par `pkill -f` ni `killall`, qui pourraient toucher d'autres processus de la machine. Si le lanceur a été arrêté avant la fin, vérifier qu'aucune clé ne reste et supprimer celle de l'essai :

```bash
ls banc-essai/traces/secrets/ | grep '^cle-'
python3 banc-essai/traces/cles.py --supprimer <essai> <essai>-relance
```

## 9. Essai à la main

### Dans la cage (sans risque)

Le lanceur du banc accepte un nom et un message libres : c'est la façon sûre d'essayer Goose à la main, avec la cage, la clé plafonnée et la collecte.

```bash
banc-essai/cage/lancer.sh goose jouet --essai goose-main-1 --message "Liste les fichiers de /travail puis lis consignes.md."
```

### Hors de la cage : test de connexion sans outil (non vérifié sur le banc)

Hors de la cage, le mode `auto` et l'extension `developer` exécuteraient des commandes sur la machine réelle sans confirmation : ne pas lancer de tâche ainsi. Un simple test de connexion au relais, sans aucune extension, reste possible : dossier de Goose jetable, clé temporaire, extensions par défaut écartées par `--no-profile`.

```bash
python3 banc-essai/traces/cles.py goose-connexion                         # clé temporaire, jamais affichée
set -a; . banc-essai/traces/secrets/cle-goose-connexion.env; set +a
GOOSE_PATH_ROOT=$(mktemp -d) GOOSE_DISABLE_KEYRING=1 GOOSE_TELEMETRY_ENABLED=false \
GOOSE_DISABLE_SESSION_NAMING=true GOOSE_PROVIDER=openai OPENAI_HOST=http://127.0.0.1:4100 \
GOOSE_MODEL="$(grep '^BANC_MODELE=' banc-essai/modele.env | cut -d= -f2)" OPENAI_API_KEY="$BANC_CLE_MODELE" \
  harnais/goose/installe/goose run --no-profile --no-session --output-format stream-json -t "Réponds seulement OK."
python3 banc-essai/traces/cles.py --supprimer goose-connexion
unset BANC_CLE_MODELE
```

Avant de se fier à cette commande, vérifier dans la sortie que `advertised_tools` est vide (aucun outil présenté au modèle) : l'effet de `--no-profile` sur les extensions intégrées n'a pas été vérifié sur le banc.
