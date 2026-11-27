# OpenCode : configuration

[Retour à la page d'entrée](../README.md)

Sur le banc, la configuration d'OpenCode n'est jamais écrite à la main : `harnais/opencode/configurer.sh` la produit au début de chaque essai, dans le dossier personnel neuf de l'essai, à partir des variables que la cage transmet. Changer de modèle ou de portail ne demande donc aucune modification du harnais.

## 1. Chaîne de configuration

| Étape | Fichier ou programme | Ce qui passe |
|---|---|---|
| 1. Description du modèle | `banc-essai/modele.env` (versionné, sans clé) | nom exposé `BANC_MODELE`, contexte, sortie maximale, vision, prix |
| 2. Secrets | `.env` à la racine (jamais commité) | adresse et clé du portail compatible OpenAI (`PORTAIL_URL`, `PORTAIL_CLE`) : lues par le relais seulement |
| 3. Clé de l'essai | `banc-essai/traces/cles.py` | clé virtuelle du relais, écrite dans `banc-essai/traces/secrets/cle-<essai>.env` (`BANC_CLE_MODELE=…`) |
| 4. Cage | `banc-essai/cage/cage.sh` | transmet `BANC_MODELE_URL=http://127.0.0.1:4100`, les variables `BANC_*` de `modele.env` (liste fermée, voir section 3), et copie la clé dans `/run/banc/cle.env` (lecture seule) |
| 5. Démarrage dans la cage | `banc-essai/cage/interieur.sh` | charge `/run/banc/cle.env` dans l'environnement (`BANC_CLE_MODELE`) |
| 6. Harnais | `harnais/opencode/lancer.sh` appelle `configurer.sh` | écrit `/home/banc/.config/opencode/opencode.json` |

Guide du banc pour les étapes 1 à 3 : [modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md).

## 2. Le fichier écrit

```bash
harnais/opencode/configurer.sh [DOSSIER]     # défaut : $HOME/.config/opencode
```

Le script écrit `DOSSIER/opencode.json` et affiche `configuration écrite : DOSSIER/opencode.json` sur la sortie d'erreur quand `lancer.sh` l'appelle. Dans la cage, `HOME=/home/banc`, qui correspond sur le poste à `~/banc-espaces/<essai>/maison/` : le fichier y reste après l'essai.

Attention : appelé sans argument hors de la cage, le script écrase `~/.config/opencode/opencode.json` de l'utilisateur. Hors de la cage, toujours lui donner un dossier.

### 2.1 Exemple

Produit avec les valeurs par défaut de `banc-essai/modele.env` (`BANC_MODELE=modele-banc`, `BANC_CONTEXTE=128000`, `BANC_SORTIE_MAX=16384`, `BANC_VISION=0`) :

```bash
T=$(mktemp -d)
BANC_MODELE_URL=http://127.0.0.1:4100 BANC_MODELE=modele-banc BANC_CONTEXTE=128000 BANC_SORTIE_MAX=16384 BANC_VISION=0 \
  harnais/opencode/configurer.sh "$T"
cat "$T/opencode.json"; rm -rf "$T"
```

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "banc/modele-banc",
  "small_model": "banc/modele-banc",
  "autoupdate": false,
  "share": "disabled",
  "provider": {
    "banc": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "LiteLLM du banc",
      "options": {
        "baseURL": "http://127.0.0.1:4100/v1",
        "apiKey": "{env:BANC_CLE_MODELE}"
      },
      "models": {
        "modele-banc": {
          "name": "modele-banc",
          "attachment": false,
          "tool_call": true,
          "modalities": {
            "input": ["text"],
            "output": ["text"]
          },
          "limit": {
            "context": 128000,
            "output": 16384
          }
        }
      }
    }
  },
  "permission": {
    "edit": "allow",
    "bash": "allow",
    "webfetch": "deny"
  }
}
```

Avec `BANC_VISION=1`, le modèle est déclaré avec `"attachment": true` et `"input": ["text", "image"]`.

(Tableaux `input` et `output` remis sur une ligne pour la lecture ; le script les écrit sur plusieurs lignes.)

### 2.2 Clé par clé

| Clé | Valeur | Effet | Source |
|---|---|---|---|
| `model` | `banc/<BANC_MODELE>` | modèle de l'agent, sous la forme `<fournisseur>/<modèle>` | [config.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/config.mdx), section Models |
| `small_model` | même modèle | modèle des tâches légères (titre de la session) ; sans cette clé, OpenCode chercherait un modèle moins cher chez le fournisseur | idem |
| `autoupdate` | `false` | pas de vérification ni d'avis de mise à jour | idem, section Autoupdate |
| `share` | `"disabled"` | partage des sessions coupé entièrement | idem, section Sharing |
| `provider.banc.npm` | `@ai-sdk/openai-compatible` | client des API compatibles OpenAI (`/v1/chat/completions`) | [providers.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/providers.mdx), section Custom provider |
| `provider.banc.options.baseURL` | `<BANC_MODELE_URL>/v1` | adresse du relais du banc, jamais celle du portail | idem |
| `provider.banc.options.apiKey` | `{env:BANC_CLE_MODELE}` | clé lue dans l'environnement au lancement ; variable absente : chaîne vide | [config.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/config.mdx), section Env vars |
| `models.<nom>.limit.context`, `.output` | `BANC_CONTEXTE`, `BANC_SORTIE_MAX` | place restante dans le contexte, connue d'OpenCode (sert à décider la compaction) ; un fournisseur personnalisé n'est pas décrit par le catalogue `models.dev` | [providers.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/providers.mdx), section Custom provider |
| `models.<nom>.attachment`, `modalities` | selon `BANC_VISION` (`1` : texte et image ; `0` : texte seul, `attachment: false`) | autorise l'envoi d'images au modèle | clés lues par la version 1.19.6 (`debug config`) ; non décrites dans la documentation de cette version |
| `models.<nom>.tool_call` | `true` | le modèle reçoit les outils de l'agent | idem |
| `permission.edit`, `.bash` | `"allow"` | modifications de fichiers et commandes sans confirmation | [permissions.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/permissions.mdx) |
| `permission.webfetch` | `"deny"` | outil de lecture de pages web retiré | idem |

Les sources ci-dessus ont été consultées le 27/11/2026 ; ce sont les pages de documentation du dépôt au tag `v1.19.6`, qui correspondent à la version installée.

### 2.3 Syntaxe : version 1 et non version 2

La version 1.19.6 lit les clés `provider`, `npm`, `options` (au singulier) et ignore la syntaxe `providers`, `package`, `settings` que décrit aujourd'hui le site [opencode.ai/docs/config](https://opencode.ai/docs/config/) (consulté le 27/11/2026), qui documente la version 2 (constaté lors des essais de mise au point du banc avec `opencode debug config` ; rappelé dans l'en-tête de `harnais/opencode/configurer.sh`). La documentation du tag v1.19.6 décrit bien la syntaxe `provider` utilisée ici.

## 3. Variables lues

| Variable | Lue par | Obligatoire | Défaut hors cage | Origine dans un essai |
|---|---|---|---|---|
| `BANC_MODELE_URL` | `configurer.sh` | oui (arrêt sinon) | | `cage.sh` : `http://127.0.0.1:4100` |
| `BANC_MODELE` | `configurer.sh` | oui (arrêt sinon : `BANC_MODELE: parameter null or not set`) | | `modele.env` (`modele-banc` par défaut) |
| `BANC_CONTEXTE` | `configurer.sh` | non | 1000000 | `modele.env` (128000 par défaut) |
| `BANC_SORTIE_MAX` | `configurer.sh` | non | 32768 | `modele.env` (16384 par défaut) |
| `BANC_VISION` | `configurer.sh` | non | 1 | `modele.env` (0 par défaut) |
| `BANC_CLE_MODELE` | OpenCode, au lancement (`{env:…}`) | oui pour appeler le modèle | | `/run/banc/cle.env`, chargé par `interieur.sh` |
| `HOME` | `configurer.sh`, OpenCode | | | `cage.sh` : `/home/banc` |
| `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` (et minuscules) | OpenCode | | | `cage.sh` : filtre `127.0.0.1:3128`, exclusion `127.0.0.1,localhost` |
| `BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE` | personne côté OpenCode | | | transmises par `cage.sh`, non utilisées par `configurer.sh` |

Les valeurs par défaut hors cage sont celles du script ; dans un essai, la cage transmet toujours celles de `modele.env`.

Conséquence de la dernière ligne : OpenCode ne connaît pas le prix du modèle et inscrit un coût nul dans ses sessions (`"cost": 0` dans les sessions exportées, constaté lors des essais de mise au point du banc). Le coût de référence est celui du relais, dans `essai.json` (avec les prix conventionnels de 1 de `modele.env`, ce coût se lit en millions de jetons).

## 4. Changer de modèle ou de portail

| Changement | Où | Action sur le harnais |
|---|---|---|
| Autre modèle sur le même portail | `banc-essai/modele.env` (`BANC_MODELE_FOURNISSEUR`, capacités, prix), puis `banc-essai/traces/demarrer.sh` | aucune |
| Autre portail compatible OpenAI | `.env` (`PORTAIL_URL`, `PORTAIL_CLE`) et `modele.env` (`BANC_MODELE_FOURNISSEUR`), contrôle par `python3 banc-essai/traces/verifier_portail.py`, puis `demarrer.sh` | aucune |
| Modèle sans lecture d'images | `BANC_VISION=0` dans `modele.env` | aucune : `configurer.sh` déclare alors l'entrée texte seule |
| Fenêtre de contexte plus petite | `BANC_CONTEXTE` dans `modele.env` | aucune |

OpenCode parle toujours au relais (`127.0.0.1:4100/v1`) sous le nom `BANC_MODELE` ; seul le relais connaît le portail et le nom réel du modèle (`BANC_MODELE_FOURNISSEUR`). Procédure complète et vérificateur du portail : [modele-et-fournisseur.md](../../../banc-essai/documentation/modele-et-fournisseur.md), section 3.

## 5. Autonomie et permissions

| Réglage | Valeur sur le banc | Effet | Source |
|---|---|---|---|
| `permission.edit`, `permission.bash` | `allow` | aucune confirmation pour écrire ou exécuter | `configurer.sh` |
| `permission.webfetch` | `deny` | refus maintenu même avec `--auto` (« Explicit "deny" rules are still enforced ») | [permissions.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/permissions.mdx), section Auto mode |
| Option `--auto` de `opencode run` | présente dans `lancer.sh` | approuve toute demande qui n'est pas explicitement refusée ; couvre `external_directory` et `doom_loop`, qui valent `ask` par défaut | idem, sections Auto mode et Defaults |
| `external_directory` | `ask` par défaut, approuvé par `--auto` | accès hors de `/travail` (par exemple `/tmp`) autorisé ; la cage borne ce qui est visible | idem, section External Directories ; constaté lors des essais de mise au point : images rendues dans `/tmp` puis lues |
| `doom_loop` | `ask` par défaut, approuvé par `--auto` | même appel d'outil répété trois fois de suite : pas d'arrêt | idem, section Available Permissions |
| `question`, `plan_enter`, `plan_exit` | `deny` dans l'agent `build` | l'agent ne peut ni poser de question ni passer en mode plan | relevé : `opencode agent list` (dossier jetable, réseau coupé) et champ `permission` d'une session exportée |

L'autonomie complète est voulue : la cage (espace de travail seul inscriptible, réseau filtré, mémoire, disque et durée plafonnés) borne ce que le harnais peut toucher ([cage/README.md](../../../banc-essai/cage/README.md)). Hors de la cage, la même configuration donne à l'agent tous les droits de l'utilisateur.

## 6. Télémétrie et réseau

| Point | Réglage | Constat |
|---|---|---|
| Mise à jour automatique | `autoupdate: false` | aucune demande de mise à jour relevée dans `reseau.jsonl` des essais |
| Partage des sessions | `share: "disabled"` | aucune demande vers un service de partage relevée |
| Lecture de pages web par l'agent | `webfetch: deny` | |
| Recherche web par l'agent | aucun réglage nécessaire | l'outil `websearch` n'existe qu'avec le fournisseur OpenCode ou les variables `OPENCODE_ENABLE_EXA`, `OPENCODE_ENABLE_PARALLEL` ([tools.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/tools.mdx), consulté le 27/11/2026) ; absent de la liste des outils de l'agent `build` (`opencode debug agent build`) |
| Catalogue des modèles (`models.opencode.ai`) | non coupé par la configuration | demandé à chaque démarrage, refusé par la cage, sans effet. La variable `OPENCODE_DISABLE_MODELS_FETCH` existe ([cli.mdx](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/web/src/content/docs/cli.mdx), section Environment variables) mais `lancer.sh` ne la pose pas |
| Paquet `@opencode-ai/plugin` (`registry.npmjs.org`) | non coupé | demandé, refusé, sans effet ; `OPENCODE_DISABLE_DEFAULT_PLUGINS` existe (même source), effet sur cette demande non vérifié sur le banc |
| Télémétrie | aucune option documentée | la documentation de la version 1.19.6 ne mentionne pas de télémétrie (recherche des mots « telemetry » et « analytics » dans les pages du tag) ; dans la cage, toute sortie autre que PyPI, Hugging Face et GitHub est refusée et journalisée |

## 7. Où est la clé, et où elle n'est pas

| Emplacement | Clé présente | Détail |
|---|---|---|
| `.env` (racine) | clé du portail (`PORTAIL_CLE`) | lue par le relais seulement ; invisible dans la cage (`/home` ne contient que `banc`) |
| `banc-essai/traces/secrets/cle-<essai>.env` | clé virtuelle de l'essai | hors git, supprimée du relais dès la sortie du harnais (`banc-essai/cage/lancer.sh`) |
| `/run/banc/cle.env` dans la cage | clé virtuelle de l'essai | copie en lecture seule, dossier supprimé à la sortie de la cage (`cage.sh`, fonction `nettoyer`) |
| Environnement d'OpenCode et de ses commandes | `BANC_CLE_MODELE` | voulu : le workflow écrit par l'agent appelle aussi le modèle. Un agent peut l'afficher : constaté lors des essais de mise au point du banc (l'agent a listé ses variables d'environnement) ; `banc-essai/cage/masquer.py` masque toute chaîne qui ressemble à une clé dans les résultats |
| `opencode.json` | non | seulement la référence `{env:BANC_CLE_MODELE}` |
| `opencode debug config` | non | la clé y est remplacée par `***` |
| `~/.local/share/opencode/auth.json` du dossier personnel de l'essai | non | fichier absent : aucune connexion par `/connect` (relevé dans `~/banc-espaces/<essai>/maison/.local/share/opencode/` lors des essais de mise au point) |
| Sessions exportées, `stdout.log` | non en principe | sauf si l'agent l'affiche lui-même (voir plus haut) |
