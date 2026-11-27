# OpenCode : lancement

[Retour à la page d'entrée](../README.md)

Commandes depuis la racine du dépôt. Prérequis du banc (bubblewrap, relais démarré, ports libres) : [lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section 1. Le harnais doit être installé ([installation.md](installation.md)).

## 1. Lancer un essai

```bash
banc-essai/cage/lancer.sh opencode <recette> [--essai NOM] [--duree SECONDES] [--message "..."]
```

| Critère | `jouet` | `goldset` |
|---|---|---|
| Tâche | correction d'un petit paquet Python, notée par des cas cachés | extraction dans le goldset de PDF importé |
| Usage | vérifier une installation ou une configuration (essai court) | essai réel sur les documents de l'équipe |
| Dossier des résultats | `banc-essai/resultats/<essai>/` (créé par le lanceur) | `banc-essai/resultats-goldset/<essai>/` (hors git) |
| Préparation | aucune | import et validation du goldset : [goldset.md](../../../banc-essai/documentation/goldset.md) |
| Essai d'OpenCode | fait lors de la mise au point du banc | non fait |

| Option | Effet | Défaut |
|---|---|---|
| `--essai NOM` | nom de l'essai et du dossier de résultats | `opencode-<recette>-<AAAAMMJJ-HHMMSS>` |
| `--duree S` | garde-fou de durée de la cage | 7200 s |
| `--message "..."` | premier message donné à OpenCode | `Suis les consignes de consignes.md.` |

Un essai long se lance détaché du terminal ([lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section 2) :

```bash
setsid nohup banc-essai/cage/lancer.sh opencode goldset --essai essai-01 > ~/banc-espaces/essai-01.log 2>&1 < /dev/null &
```

## 2. Ce qui se passe

### 2.1 Côté banc

`banc-essai/cage/lancer.sh` prend le verrou (un essai à la fois), crée la clé virtuelle de l'essai, prépare un espace neuf `~/banc-espaces/<essai>/travail` et un dossier personnel neuf `~/banc-espaces/<essai>/maison`, démarre l'API de soumission, puis lance la cage avec l'entrée standard fermée (`< /dev/null`). À la sortie du harnais : dépense relevée, clé supprimée, relance du workflow déclaré, collecte et rapport. Détail : [lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section 3.

### 2.2 Dans la cage

| Étape | Programme | Détail |
|---|---|---|
| 1 | `banc-essai/cage/interieur.sh` | relais intérieurs (modèle `127.0.0.1:4100`, filtre `127.0.0.1:3128`, API `127.0.0.1:8765`), chargement de `/run/banc/cle.env` |
| 2 | `/opt/harnais/lancer.sh "<message>"` (copie en lecture seule de `harnais/opencode/`) | |
| 3 | `configurer.sh` | écrit `/home/banc/.config/opencode/opencode.json` ([configuration.md](configuration.md)) |
| 4 | `installe/opencode run --format json --print-logs --log-level INFO --auto "<message>"` | répertoire courant `/travail` ; événements JSON sur la sortie standard, journaux sur la sortie d'erreur ; code de retour gardé |
| 5 | `installe/opencode session list --format json` puis `installe/opencode export <id>` | chaque session exportée dans `/home/banc/opencode-sessions/<id>.json` ; une erreur d'export est ignorée |
| 6 | sortie | code de retour de l'étape 4 |

| Option de `opencode run` | Effet | Source |
|---|---|---|
| `--format json` | « raw JSON events » au lieu du texte mis en forme | [cli.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/cli.mdx), section run, consulté le 27/11/2026 |
| `--print-logs` | journaux sur la sortie d'erreur | `opencode run --help` (version 1.19.6) |
| `--log-level INFO` | niveau des journaux (`DEBUG`, `INFO`, `WARN`, `ERROR`) | idem |
| `--auto` | approuve toute permission non refusée explicitement | [permissions.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/permissions.mdx), section Auto mode |

Attention : `-p` de `opencode run` est un mot de passe de serveur (`--password`), pas le message.

## 3. Sorties et où les trouver

| Sortie | Emplacement | Dans git |
|---|---|---|
| Événements de la session (trace complète) | `banc-essai/resultats/<essai>/harnais/stdout.log` (`.gz` au-delà de 20 Mo) | oui (sauf goldset) |
| Journaux d'OpenCode et ligne `configuration écrite : …` | `banc-essai/resultats/<essai>/harnais/stderr.log` | oui (sauf goldset) |
| Appels au modèle vus par le relais | `banc-essai/resultats/<essai>/traces/appels.jsonl` | oui (sauf goldset) |
| Demandes réseau | `banc-essai/resultats/<essai>/traces/reseau.jsonl` | oui (sauf goldset) |
| Mesures et rapport | `banc-essai/resultats/<essai>/essai.json`, `rapport.md` | oui (sauf goldset) |
| Sessions exportées | `~/banc-espaces/<essai>/maison/opencode-sessions/<id>.json` | non : restent dans l'espace de l'essai, non recopiées dans `banc-essai/resultats/` |
| Configuration utilisée | `~/banc-espaces/<essai>/maison/.config/opencode/opencode.json` | non |
| Journal interne d'OpenCode | `~/banc-espaces/<essai>/maison/.local/share/opencode/log/opencode.log` | non |
| Base de sessions d'OpenCode | `~/banc-espaces/<essai>/maison/.local/share/opencode/opencode.db` | non |
| Fichiers produits par l'agent | `~/banc-espaces/<essai>/travail/` ; code recopié dans `banc-essai/resultats/<essai>/code/` | code seulement |

Pour la recette `goldset`, remplacer `banc-essai/resultats/` par `banc-essai/resultats-goldset/` (hors git : les traces recopient le texte des documents). Les sessions exportées et `opencode.db` contiennent aussi ce texte.

## 4. Format de la trace

### 4.1 `harnais/stdout.log`

Une ligne JSON par événement. Champs communs : `type`, `timestamp` (millisecondes depuis 1970), `sessionID`, puis `part` (ou `error`).

| `type` | Contenu de `part` | Exemple relevé |
|---|---|---|
| `step_start` | début d'un tour du modèle | une ligne par tour |
| `tool_use` | `tool` (nom de l'outil), `callID`, `state.status`, `state.input`, `state.output`, `state.time.start`, `state.time.end` | `"tool":"glob"`, `"input":{"pattern":"**/consignes.md"}` |
| `step_finish` | `reason` (`tool-calls`, ou fin), `tokens` (`input`, `output`, `reasoning`, `cache.read`, `cache.write`), `cost` (toujours 0 sur le banc : prix non déclarés) | |
| `text` | `text` : réponse finale de l'agent | résumé du travail fait (par exemple, pour la recette `jouet`, la correction apportée) |
| `error` | `error.name`, `error.data.message`, `error.data.isRetryable`, `error.data.metadata.url` | `APIError`, `Cannot connect to API: ECONNRESET` (relais injoignable) |

Compter les outils utilisés :

```bash
python3 -c '
import json, sys, collections
c = collections.Counter()
for l in open(sys.argv[1]):
    try: e = json.loads(l)
    except ValueError: continue
    if e.get("type") == "tool_use": c[e["part"]["tool"]] += 1
print(dict(c))' banc-essai/resultats/<essai>/harnais/stdout.log
```

Résultat : un dictionnaire qui associe à chaque outil son nombre d'appels.

### 4.2 `harnais/stderr.log`

Première ligne : `configuration écrite : /home/banc/.config/opencode/opencode.json`. Ensuite, une ligne par message, au format `timestamp=… level=INFO|WARN|ERROR run=<id> message=… <champs>`. Lignes utiles :

| Message | Sens |
|---|---|
| `loading path=/home/banc/.config/opencode/opencode.json` | fichier de configuration lu |
| `stream providerID=banc modelID=<modèle> … agent=build` | appel au modèle de l'agent principal (`agent=title` : titre de la session) |
| `evaluated permission=bash pattern="…" action.action=allow` | commande autorisée, avec son texte |
| `Failed to fetch models.dev` | catalogue refusé par la cage, sans effet |
| `background dependency install failed` | paquet npm refusé par la cage, sans effet |
| `downloading ripgrep url=…` | téléchargement de ripgrep depuis GitHub |
| `stream error … Cannot connect to API` | relais du modèle injoignable (voir [fonctionnement.md](fonctionnement.md), section 4) |
| `exiting loop` puis `disposing instance` | fin normale de la session |

### 4.3 Sessions exportées

`opencode export <id>` écrit un objet `{"info": …, "messages": […]}`. `info` donne l'agent (`build`), le modèle (`providerID: banc`), la version, les jetons cumulés et les permissions effectives ; chaque message a son `info` (rôle, jetons, raison de fin) et ses `parts` (texte, appels d'outils avec entrée et sortie complètes). Emplacement : `~/banc-espaces/<essai>/maison/opencode-sessions/<id>.json`. L'option `--sanitize` (« redact sensitive transcript and file data », `opencode export --help`) n'est pas utilisée par `lancer.sh`.

## 5. Suivre un essai en cours

```bash
python3 banc-essai/cage/suivi.py <essai>
```

Une ligne : durée, appels au modèle, coût, soumissions, déclaration de fin, taille de la trace et âge de sa dernière écriture. Une trace qui ne grossit plus pendant plusieurs minutes signale un blocage.

Pour voir ce que fait OpenCode (sans contenu des documents) :

```bash
tail -f banc-essai/resultats/<essai>/harnais/stderr.log | grep --line-buffered -E 'evaluated permission|level=ERROR'
```

## 6. Arrêter proprement

On arrête la cage, pas le lanceur, pour que le lanceur supprime la clé, collecte et produise un rapport partiel ([lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section 5) :

```bash
pgrep -af "timeout --kill-after=30"
kill <PID affiché pour l'essai>
```

Puis vérifier qu'aucune clé ne reste :

```bash
ls banc-essai/traces/secrets/ | grep '^cle-'
python3 banc-essai/traces/cles.py --supprimer <essai> <essai>-relance
```

## 7. Essai à la main, hors du lanceur

Ces deux formes n'ont pas été essayées sur le banc telles qu'écrites ici ; elles reprennent les commandes des scripts cités. Ne pas les lancer pendant un essai : elles ne prennent pas le verrou du lanceur.

### 7.1 Dans la cage, sans API ni relance (recommandé)

`banc-essai/cage/cage.sh` s'utilise seul (en-tête du script). OpenCode reste isolé ; aucun rapport n'est produit.

```bash
python3 banc-essai/traces/cles.py essai-main            # clé : banc-essai/traces/secrets/cle-essai-main.env
mkdir -p ~/banc-espaces/essai-main/travail ~/banc-espaces/essai-main/maison
banc-essai/cage/cage.sh --espace ~/banc-espaces/essai-main/travail --maison ~/banc-espaces/essai-main/maison \
  --harnais harnais/opencode --cle banc-essai/traces/secrets/cle-essai-main.env \
  -- /opt/harnais/lancer.sh "Crée le fichier bonjour.txt qui contient le mot bonjour." \
  < /dev/null > ~/banc-espaces/essai-main/stdout.log 2> ~/banc-espaces/essai-main/stderr.log
python3 banc-essai/traces/cles.py --depense essai-main
python3 banc-essai/traces/cles.py --supprimer essai-main
```

L'entrée standard doit rester fermée (`< /dev/null`) : sinon `opencode run` attend la fin de l'entrée et ne fait rien (constaté lors des essais de mise au point du banc : essai bloqué sans aucun appel au modèle jusqu'à son arrêt).

### 7.2 Hors de la cage (déconseillé)

Hors de la cage, OpenCode a tous les droits de l'utilisateur (`bash` et `edit` autorisés sans confirmation), contacte directement `models.opencode.ai`, `registry.npmjs.org` et GitHub, et lit les fichiers de configuration du projet et du dossier courant (ordre de priorité : [config.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/config.mdx), section Precedence order, consulté le 27/11/2026). À réserver à un dossier jetable :

```bash
R=$PWD
python3 banc-essai/traces/cles.py essai-main
D=$(mktemp -d); mkdir -p "$D/home" "$D/projet"
(
  set -a; . banc-essai/modele.env; . banc-essai/traces/secrets/cle-essai-main.env; set +a
  export HOME="$D/home" BANC_MODELE_URL=http://127.0.0.1:4100 NO_PROXY=127.0.0.1,localhost
  "$R/harnais/opencode/configurer.sh" "$HOME/.config/opencode"
  cd "$D/projet" && "$R/harnais/opencode/installe/opencode" run --format json "Crée le fichier bonjour.txt qui contient le mot bonjour." < /dev/null
)
python3 banc-essai/traces/cles.py --supprimer essai-main
```

Le sous-shell `( … )` garde la clé hors du shell courant. `HOME` est redirigé pour ne pas écraser `~/.config/opencode/` de l'utilisateur. Sans `--auto`, le comportement de `opencode run` face à une demande `ask` (accès hors du dossier, boucle répétée) n'a pas été vérifié sur le banc.
