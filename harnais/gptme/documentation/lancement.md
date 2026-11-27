# gptme : lancement

Retour à la [page d'entrée](../README.md). Toutes les commandes se lancent depuis la racine du dépôt. Le déroulé commun à tous les harnais (prérequis, étapes du lanceur, lecture des résultats) est décrit dans [lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md) ; cette page en donne ce qui est propre à gptme.

## 1. Lancer un essai

Prérequis : gptme installé ([installation.md](installation.md)), relais du modèle démarré (`banc-essai/traces/demarrer.sh`), aucun autre essai en cours.

```bash
banc-essai/cage/lancer.sh gptme <recette> [--essai NOM] [--duree S] [--message "..."]
```

| Critère | `jouet` | `goldset` |
|---|---|---|
| Tâche | correction d'un petit paquet Python, tests cachés | extraction de données d'un jeu de PDF de l'équipe, réponses de référence fournies par l'utilisateur |
| Résultats dans | `banc-essai/resultats/<essai>/` (dossier créé par le lanceur) | `banc-essai/resultats-goldset/<essai>/` (hors git) |
| Remarque | quelques appels au modèle, à lancer d'abord | schéma validé et consignes générées exigés ([goldset.md](../../../banc-essai/documentation/goldset.md)) ; non essayée avec gptme lors de la mise au point du banc |

| Option | Défaut | Effet |
|---|---|---|
| `--essai NOM` | `gptme-<recette>-<date>-<heure>` | nom de l'essai, du dossier de résultats et de la clé virtuelle |
| `--duree S` | 7 200 s | garde-fou de durée de la cage |
| `--message "..."` | `Suis les consignes de consignes.md.` | message donné à gptme |

Exemples :

```bash
banc-essai/cage/lancer.sh gptme jouet --essai test-gptme
BANC_GOLDSET=/chemin/du/goldset banc-essai/cage/lancer.sh gptme goldset
```

Source : en-tête et code de [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh).

## 2. Ce que fait `lancer.sh` du harnais dans la cage

Le lanceur du banc appelle `/opt/harnais/lancer.sh "<message>"` dans la cage, entrée standard fermée, sortie standard vers `harnais/stdout.log`, erreurs vers `harnais/stderr.log`. Le script [`harnais/gptme/lancer.sh`](../lancer.sh) :

1. appelle `configurer.sh` (message `configuration écrite : /home/banc/.config/gptme/config.toml` sur la sortie d'erreur) ;
2. pose `GPTME_TIKTOKEN_TIMEOUT=0` et `GPTME_NO_LOCAL_DISCOVERY=1` ([configuration.md](configuration.md), section 3) ;
3. remplace son processus par `installe/bin/python`, qui charge `gptme.cli.main` (le script `installe/bin/gptme` ne fonctionne pas dans la cage, voir [installation.md](installation.md)), avec ces options :

| Option | Effet | Source |
|---|---|---|
| `--non-interactive` | traite le message puis s'arrête ; aucune confirmation | `gptme --help` |
| `--output-format json` | un objet JSON par message sur la sortie standard | `gptme --help` |
| `--tool-format tool` | appels d'outils natifs de l'API (champ `tools` des requêtes), pas d'outils écrits en Markdown | `gptme --help` ; 15 outils déclarés par appel dans le journal du relais (`traces/appels.jsonl`), constaté lors des essais de mise au point du banc |
| `-m "banc/$BANC_MODELE"` | modèle du fournisseur `banc` | [configuration.md](configuration.md) |
| `--name essai` | nom de la conversation, donc de son dossier de journaux | `gptme --help` |
| `"$*"` | message, tous les arguments réunis en un seul texte | |

La session se termine quand le modèle appelle l'outil `complete` (`Complete tool call detected, stopping session immediately` dans `stderr.log`), ou au garde-fou de durée. Code de retour 0 lors des essais de mise au point du banc.

## 3. Sorties produites

`<résultats>` désigne `banc-essai/resultats/<essai>/` pour la recette `jouet` et `banc-essai/resultats-goldset/<essai>/` pour la recette `goldset`.

| Fichier | Contenu | Dans git |
|---|---|---|
| `<résultats>/harnais/stdout.log` | trace de la session : objets JSON des messages, mêlés aux sorties brutes des commandes | `jouet` : oui ; `goldset` : non ; compressé en `.gz` au-delà de 20 Mo |
| `<résultats>/harnais/stderr.log` | messages d'état de gptme : configuration, avertissements, compactions, nouvelles tentatives, fin | `jouet` : oui ; `goldset` : non |
| `<résultats>/traces/appels.jsonl` | appels au modèle vus par le relais (jetons, coût, statut) | `jouet` : oui ; `goldset` : non |
| `<résultats>/essai.json`, `rapport.md` | chiffres de l'essai, rapport | `jouet` : oui ; `goldset` : non |
| `<résultats>/code/` | code écrit par l'agent, archivé pour la relecture | `jouet` : oui ; `goldset` : non |
| `~/banc-espaces/<essai>/maison/.local/share/gptme/logs/essai/` | journaux complets de la conversation (section 4) | non : hors du dépôt, non recopiés par le lanceur |
| `~/banc-espaces/<essai>/travail/` | espace de travail de l'agent | non |

Le dossier `~/banc-espaces` devient `$BANC_ESPACES` si cette variable est définie. Liste complète des fichiers d'un essai : [`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md).

## 4. Journaux de conversation de gptme

Constatés lors des essais de mise au point du banc, dans `~/banc-espaces/<essai>/maison/.local/share/gptme/logs/essai/` :

| Fichier | Contenu |
|---|---|
| `conversation.jsonl` | journal complet des messages ; la documentation le décrit comme journal maître sans perte, d'où l'outil `recall` relit les résultats retirés par la compaction (<https://gptme.org/docs/context-compression.html>, consulté le 27/11/2026) |
| `events.jsonl` | événements de la conversation |
| `config.toml` | configuration de la conversation (modèle, outils, mode sans interaction) ; sans clé |
| `compaction.jsonl` | une ligne par compaction : déclencheur, méthode, jetons avant et après |
| `RESUME.md` | point de reprise écrit à la compaction |
| `views/compacted-NNN.jsonl` | vue compactée que voit le modèle après chaque compaction |
| `model_selection_trace.json` | modèle demandé et retenu |
| `lesson-emissions.jsonl`, `files/`, `branches/` | leçons injectées, fichiers joints, branches de conversation |
| `workspace` | lien vers `/travail` |

Ces fichiers restent sur le poste et ne sont pas suivis par git. Après un essai goldset, ils contiennent des extraits des documents.

## 5. Format de la trace (`stdout.log`)

Chaque message est une ligne JSON qui commence par `{"type": "message"`. Entre ces lignes, gptme écrit aussi la sortie brute des commandes lancées par l'agent : le fichier n'est pas un JSON par ligne.

| Champ | Contenu |
|---|---|
| `type` | `message` |
| `role` | `user` (message initial), `assistant` (réponse du modèle, appel d'outil inclus), `system` (résultat d'un outil) |
| `content` | texte ; un appel d'outil s'écrit `@shell(<id>): {"command": "..."}` ; le raisonnement du modèle apparaît entre `<think>` et `</think>` |
| `timestamp` | heure locale, sans fuseau |
| `call_id` | identifiant de l'appel d'outil auquel répond un message `system` |
| `metadata.model`, `metadata.served_model` | modèle demandé (`banc/...`) et modèle servi |
| `metadata.usage` | `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`, `reasoning_tokens` |
| `metadata.cost` | coût calculé par gptme avec des prix empruntés : faux ([configuration.md](configuration.md), section 4) |
| `metadata.timings` | `ttft_ms` (premier jeton), `gen_ms`, `tool_ms`, `tool_ms_by_name` |
| `metadata.tool`, `metadata.tool_call` | outil exécuté, numéro d'appel |
| `metadata.compaction_*` | marques de compaction |

Extraire les messages et les lire en une ligne chacun :

```bash
R=banc-essai/resultats/<essai>        # recette goldset : banc-essai/resultats-goldset/<essai>
grep '^{"type": "message"' "$R/harnais/stdout.log" | python3 -c '
import json, sys
for ligne in sys.stdin:
    m = json.loads(ligne); meta = m.get("metadata") or {}
    print(m["timestamp"][11:19], m["role"], meta.get("tool", ""), (meta.get("usage") or {}).get("input_tokens", ""))'
```

Compter les outils utilisés : même filtre, puis `metadata.tool`. Constaté lors des essais de mise au point du banc : `shell` domine largement, suivi de `save` et `patch`, `ipython` reste rare, `complete` termine la session.

Pour une trace compressée : `zcat .../stdout.log.gz | grep '^{"type": "message"'`.

## 6. Suivre un essai en cours

```bash
python3 banc-essai/cage/suivi.py <essai>
tail -f banc-essai/resultats/<essai>/harnais/stderr.log      # recette goldset : banc-essai/resultats-goldset/<essai>/
```

`suivi.py` donne en une ligne la durée, les appels au modèle et leurs échecs, le coût mesuré par le relais, les soumissions, la déclaration de fin, la taille de la trace et l'âge de sa dernière écriture. `stderr.log` montre les événements propres à gptme : `Auto-summarize triggered` (compaction), `Discarding failed LLM attempt N/11` (nouvelle tentative après une erreur du fournisseur), `Complete tool call detected` (fin). Le montant `Session cost reached $…` de ce fichier est faux ; le coût réel est celui de `suivi.py`.

## 7. Arrêter un essai proprement

Arrêter la cage, pas le lanceur, pour que le lanceur supprime la clé et produise le rapport ([lancer-un-essai.md](../../../banc-essai/documentation/lancer-un-essai.md), section 5) :

```bash
pgrep -af "timeout --kill-after=30"
kill <PID affiché pour l'essai>
ls banc-essai/traces/secrets/ | grep '^cle-'
```

gptme reçoit alors le signal d'arrêt par `timeout` ; la conversation déjà écrite reste dans `~/banc-espaces/<essai>/maison/.local/share/gptme/logs/essai/`. Comportement de gptme à l'arrêt : non vérifié sur le banc.

## 8. Essai à la main, hors lanceur

Lancer gptme directement sur l'hôte, hors cage, n'est pas conseillé : en mode sans interaction, l'agent exécute toute commande avec les droits de l'utilisateur, sur tout le dossier personnel (dépôt, `.env`, test caché compris).

Pour vérifier la configuration ou le lien avec le modèle sans le lanceur, rester dans la cage avec `cage.sh` et une clé temporaire. Procédure tirée des scripts du banc, non exécutée lors de la rédaction (non vérifiée sur le banc) ; un ou deux appels au modèle :

```bash
python3 banc-essai/traces/cles.py manuel-gptme
E=$(mktemp -d); mkdir -p "$E/travail" "$E/maison"
banc-essai/cage/cage.sh --espace "$E/travail" --maison "$E/maison" --harnais harnais/gptme \
  --cle banc-essai/traces/secrets/cle-manuel-gptme.env --duree 300 \
  -- /opt/harnais/lancer.sh "Réponds seulement OK, sans utiliser d'outil."
python3 banc-essai/traces/cles.py --supprimer manuel-gptme
ls "$E/maison/.local/share/gptme/logs/essai/"
rm -rf "$E"
```

La sortie standard affiche la trace JSON ; l'appel figure dans `banc-essai/traces/journaux/appels.jsonl` sous l'alias `manuel-gptme`. Une session interactive dans la cage (sans `--non-interactive`) n'a pas été essayée : la cage ouvre une nouvelle session de terminal (`--new-session`), ce qui peut gêner la saisie.
