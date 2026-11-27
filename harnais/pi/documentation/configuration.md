# Pi : configuration

Retour : [page d'entrée de Pi](../README.md). Pages voisines : [installation](installation.md), [lancement](lancement.md), [fonctionnement](fonctionnement.md).

Aucune configuration n'est à écrire à la main. À chaque essai, `harnais/pi/lancer.sh` appelle `harnais/pi/configurer.sh`, qui écrit la configuration de Pi dans le dossier personnel de la cage à partir des variables transmises par la cage. Pour changer de modèle ou de portail, on modifie `banc-essai/modele.env` et `.env`, jamais le harnais.

## 1. Chaîne de configuration

| Étape | Fichier | Ce qui passe |
|---|---|---|
| 1 | [`banc-essai/modele.env`](../../../banc-essai/modele.env) (versionné, sans clé) | nom du modèle exposé, contexte, sortie maximale, vision, prix |
| 2 | [`banc-essai/cage/cage.sh`](../../../banc-essai/cage/cage.sh) | lit les lignes `BANC_MODELE`, `BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION`, `BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE` de `modele.env` et les place dans l'environnement de la cage, avec `BANC_MODELE_URL=http://127.0.0.1:4100` |
| 3 | [`banc-essai/cage/interieur.sh`](../../../banc-essai/cage/interieur.sh) | charge `/run/banc/cle.env` (clé de l'essai, `BANC_CLE_MODELE`) dans l'environnement, puis lance `/opt/harnais/lancer.sh` |
| 4 | [`harnais/pi/lancer.sh`](../lancer.sh) | appelle `configurer.sh` (messages sur la sortie d'erreur), puis Pi |
| 5 | [`harnais/pi/configurer.sh`](../configurer.sh) | écrit `$HOME/.pi/agent/models.json` et `$HOME/.pi/agent/settings.json` ; dans la cage, `HOME=/home/banc`, soit `~/banc-espaces/<essai>/maison/` sur le poste |

La configuration est donc réécrite à chaque essai, dans un dossier personnel neuf : rien ne passe d'un essai à l'autre.

## 2. Variables lues par `configurer.sh`

| Variable | Obligatoire | Défaut du script | Usage dans `models.json` |
|---|---|---|---|
| `BANC_MODELE_URL` | oui (arrêt sinon) | | `baseUrl` = valeur + `/v1` |
| `BANC_MODELE` | oui (arrêt sinon) | | `id` et `name` du modèle ; `defaultModel` de `settings.json` |
| `BANC_VISION` | non | `1` | `1` : `input` = `["text", "image"]` ; autre valeur : `["text"]` |
| `BANC_CONTEXTE` | non | `1000000` | `contextWindow` (jetons) |
| `BANC_SORTIE_MAX` | non | `32768` | `maxTokens` (jetons) |
| `BANC_PRIX_ENTREE` | non | `0.05` | `cost.input` (dollars par million de jetons) |
| `BANC_PRIX_SORTIE` | non | `0.30` | `cost.output` |
| `BANC_PRIX_CACHE` | non | `0.003` | `cost.cacheRead` |
| `BANC_CLE_MODELE` | pas à l'écriture | | non lue par le script : `models.json` contient le texte `$BANC_CLE_MODELE`, que Pi remplace par la valeur de la variable au lancement |

Les défauts du script reprennent les valeurs actuelles de `modele.env` ; dans la cage, ce sont toujours les valeurs de `modele.env` qui s'appliquent.

Le script accepte un dossier de destination en argument (défaut : `$HOME/.pi/agent`) :

```bash
harnais/pi/configurer.sh [DOSSIER]
```

## 3. Fichiers écrits, exemple réel

Exemple produit le 27/11/2026 par `configurer.sh` vers un dossier temporaire, avec les valeurs de `banc-essai/modele.env` et `BANC_MODELE_URL=http://127.0.0.1:4100` :

```bash
T=$(mktemp -d)
set -a; . banc-essai/modele.env; set +a
BANC_MODELE_URL=http://127.0.0.1:4100 harnais/pi/configurer.sh "$T"
cat "$T/models.json" "$T/settings.json"
```

`models.json` :

```json
{
  "providers": {
    "banc": {
      "baseUrl": "http://127.0.0.1:4100/v1",
      "api": "openai-completions",
      "apiKey": "$BANC_CLE_MODELE",
      "models": [
        {
          "id": "deepseek-v4.1-flash",
          "name": "deepseek-v4.1-flash",
          "input": [
            "text",
            "image"
          ],
          "contextWindow": 1000000,
          "maxTokens": 32768,
          "cost": {
            "input": 0.05,
            "output": 0.3,
            "cacheRead": 0.003,
            "cacheWrite": 0
          }
        }
      ]
    }
  }
}
```

| Champ | Sens (référence : [models-configuration.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/models-configuration.md), consulté le 27/11/2026) |
|---|---|
| `providers.banc` | fournisseur ajouté, nommé `banc` (tout nom qui n'est pas un fournisseur intégré ajoute un fournisseur) |
| `baseUrl` | adresse de base de l'API : le relais LiteLLM du banc, vu de la cage |
| `api` | `openai-completions` : API Chat Completions compatible OpenAI (`/v1/chat/completions`) |
| `apiKey` | « $NOM » : la clé est lue dans la variable d'environnement `NOM` au moment de l'appel |
| `id`, `name` | nom du modèle envoyé à l'API, et nom utilisé par `--model` |
| `input` | types d'entrée acceptés par le modèle : texte, et images si la vision est déclarée |
| `contextWindow`, `maxTokens` | fenêtre de contexte et sortie maximale ; défauts de Pi sans ces champs : 128 000 et 16 384 |
| `cost` | prix en dollars par million de jetons ; Pi en tire le coût affiché par message (champ `usage.cost` de la session) ; `cacheWrite` est fixé à 0 par le script |
| `reasoning` | absent : Pi considère que le modèle ne raisonne pas et fixe le niveau de réflexion à `off` (entrée `thinking_level_change` des sessions des essais, colonne `thinking: no` de `--list-models`) |

`settings.json` :

```json
{
  "defaultProvider": "banc",
  "defaultModel": "deepseek-v4.1-flash",
  "enableInstallTelemetry": false,
  "enableAnalytics": false
}
```

| Réglage | Sens (référence : [settings.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md), consulté le 27/11/2026) |
|---|---|
| `defaultProvider`, `defaultModel` | fournisseur et modèle au démarrage (redondants avec `--provider` et `--model` de `lancer.sh`) |
| `enableInstallTelemetry` | `false` : pas de signalement anonyme d'installation ou de mise à jour, pas d'en-têtes d'attribution vers le fournisseur (défaut de Pi : `true`) |
| `enableAnalytics` | `false` : pas de partage de données d'usage (défaut de Pi : `false`, utilisé seulement par l'assistant de premier lancement) |

Fichiers créés par Pi lui-même au démarrage dans le même dossier : `auth.json` et `models-store.json`, vides (`{}`) sur le banc (constaté dans `~/banc-espaces/pi-jouet-1/maison/.pi/agent/` et lors de la vérification du 27/11/2026).

Tous les autres réglages restent aux défauts de Pi 1.5.2. Ceux qui comptent pour un essai :

| Réglage | Défaut | Conséquence sur le banc |
|---|---|---|
| `defaultTools` | `read`, `bash`, `edit`, `write` | quatre outils déclarés au modèle (champ `outils` = 4 dans `traces/appels.jsonl` des essais) |
| `compaction.enabled`, `compaction.reserveTokens`, `compaction.keepRecentTokens` | `true`, 16 384, 20 000 | résumé automatique de l'historique quand le contexte dépasse `contextWindow` − 16 384 jetons |
| `retry.enabled`, `retry.maxRetries` | `true`, 3 | nouvelles tentatives de Pi après une erreur passagère du fournisseur |
| `defaultProjectTrust` | `"ask"` | en mode JSON, sans invite possible : les ressources de projet (`.pi/` de l'espace de travail) ne sont pas chargées |
| `httpProxy` | aucun | Pi suit `HTTP_PROXY` et `HTTPS_PROXY` de la cage (section 5) |

## 4. Changer de modèle ou de portail

Le harnais ne contient ni nom de fournisseur ni clé. Pour passer d'OpenRouter à un portail compatible OpenAI, ou changer de modèle :

| Étape | Action | Référence |
|---|---|---|
| 1 | `.env` : `PORTAIL_URL` et `PORTAIL_CLE` (ou `OPENROUTER_API_KEY`) | [`banc-essai/documentation/modele-et-fournisseur.md`](../../../banc-essai/documentation/modele-et-fournisseur.md), section 2.2 |
| 2 | `banc-essai/modele.env` : `BANC_FOURNISSEUR`, `BANC_MODELE_FOURNISSEUR`, `BANC_MODELE`, puis `BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION`, prix | idem, section 2.1 |
| 3 | `banc-essai/traces/demarrer.sh` : le relais relit sa configuration | idem, section 3 |
| 4 | Vérification sans harnais : `banc-essai/traces/verifier_portail.py` | idem |
| 5 | `banc-essai/cage/lancer.sh pi jouet` | [lancement](lancement.md) |

Points propres à Pi :

| Variable de `modele.env` | Effet sur Pi | Risque si elle est fausse |
|---|---|---|
| `BANC_MODELE` | nom demandé au relais | refus du relais (modèle non permis à la clé) |
| `BANC_CONTEXTE` | seuil de compaction automatique | trop grand : Pi ne résume pas à temps et le portail refuse les requêtes trop longues ; Pi tente alors un résumé puis une nouvelle requête ([compaction.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/compaction.md)) ; non observé sur le banc |
| `BANC_SORTIE_MAX` | sortie maximale déclarée | supérieure à la limite du portail : refus possible des requêtes ; non vérifié sur le banc |
| `BANC_VISION` | déclare au modèle l'entrée `image` ; l'outil `read` lit les images (82 appels de Pi avec image dans `c1-04-pi-avec-aide`) | `1` avec un modèle sans vision : appels avec image en échec ; comportement de Pi avec `0` non vérifié sur le banc |
| `BANC_PRIX_*` | coût affiché par Pi dans sa session | sans effet sur le plafond, calculé par le relais avec les mêmes prix |

Aucune variable de `modele.env` ne permet de déclarer un modèle qui raisonne (`reasoning`) : avec un tel modèle, Pi reste au niveau de réflexion `off` (voir [fonctionnement](fonctionnement.md), limites).

## 5. Autonomie, permissions, télémétrie et réseau

Autonomie et permissions :

| Point | État sur le banc | Source |
|---|---|---|
| Demande d'approbation avant un outil | aucune : Pi n'a pas de système d'approbation, il exécute les appels d'outils directement | [security.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/security.md), consulté le 27/11/2026 ; commentaire de [`lancer.sh`](../lancer.sh) |
| Bac à sable intégré | aucun : la documentation renvoie à un conteneur, une machine virtuelle ou un bac à sable externes | idem |
| Ce qui borne les outils | la cage : écriture seulement dans `/travail`, `/home/banc` et `/tmp` ; dépôt, test caché et secrets invisibles ; réseau limité au relais, à l'API et au filtre de téléchargement | [`banc-essai/cage/README.md`](../../../banc-essai/cage/README.md) |
| Interaction | aucune : entrée standard fermée par le lanceur, mode `--mode json` qui exécute le message et s'arrête | [`banc-essai/cage/lancer.sh`](../../../banc-essai/cage/lancer.sh), [cli.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/cli.md) |

Télémétrie et accès réseau coupés par `lancer.sh` :

| Réglage | Effet documenté | Source |
|---|---|---|
| `PI_OFFLINE=1` | coupe toute activité réseau automatique, dont le rafraîchissement du catalogue de modèles | [environment-variables.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/environment-variables.md), consulté le 27/11/2026 |
| `PI_SKIP_VERSION_CHECK=1` | coupe la demande de dernière version à `pi.dev` | idem |
| `PI_TELEMETRY=0` | coupe la télémétrie d'installation et de mise à jour et les en-têtes d'attribution | idem |
| `enableInstallTelemetry: false`, `enableAnalytics: false` | mêmes coupures, dans `settings.json` | [settings.md v1.5.2](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) |

Constat : dans les essais `pi-jouet-1` et `c1-04-pi-avec-aide`, le filtre de la cage n'a reçu que des demandes vers `pypi.org` et `files.pythonhosted.org` (installation de paquets Python par le harnais), aucune refusée, aucune vers `pi.dev` ([`traces/reseau.jsonl`](../../../banc-essai/resultats/pi-jouet-1/traces/reseau.jsonl) de chaque essai). Les appels au modèle vers `127.0.0.1:4100` ne passent pas par le filtre : la cage pose `NO_PROXY=127.0.0.1,localhost` et aucun de ces appels n'apparaît dans `reseau.jsonl`.

## 6. Où est la clé, et où elle n'est pas

| Emplacement | Clé présente | Détail |
|---|---|---|
| `.env` (racine du dépôt) | clé du fournisseur (`OPENROUTER_API_KEY` ou `PORTAIL_CLE`) | jamais visible dans la cage, jamais lue par le harnais |
| `banc-essai/traces/secrets/cle-<essai>.env` | clé virtuelle de l'essai (`BANC_CLE_MODELE=...`) | créée par `banc-essai/traces/cles.py`, supprimée du relais dès la sortie du harnais |
| `/run/banc/cle.env` dans la cage | copie de la clé de l'essai | lecture seule, chargée dans l'environnement par `interieur.sh` |
| environnement du processus Pi | `BANC_CLE_MODELE` | hérité par les commandes que Pi exécute : une commande `env` du modèle peut l'afficher dans la trace |
| `models.json` | non | contient le texte `$BANC_CLE_MODELE`, pas la valeur |
| `settings.json`, `auth.json` | non | `auth.json` reste vide (`{}`) |
| `banc-essai/resultats/<essai>/` | non | en fin d'essai, `banc-essai/cage/masquer.py` remplace toute chaîne de la forme `sk-` suivie de 20 caractères ou plus par `sk-***` dans les fichiers texte des résultats |

La clé de l'essai n'ouvre que le modèle `BANC_MODELE`, avec un plafond de dépense (`BANC_BUDGET_ESSAI`, 2 $), et cesse de fonctionner à la fin de l'essai ([`banc-essai/traces/README.md`](../../../banc-essai/traces/README.md)).
