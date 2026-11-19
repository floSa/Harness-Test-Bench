# Traces : LiteLLM du banc

Relais entre les harnais et OpenRouter, propre au banc : LLM-Service et les conteneurs `rag-*` et `llm-*` ne sont ni utilisés ni modifiés.

| Élément | Valeur |
|---|---|
| Conteneurs | `harness-litellm` (`ghcr.io/berriai/litellm:v1.106.4`), `harness-litellm-db` (`postgres:17.7-alpine`, exigé par les clés virtuelles) |
| Adresse | `http://127.0.0.1:4100` (API compatible OpenAI, `/v1/chat/completions`) |
| Modèle exposé | `gemma-4-31b` -> `openrouter/google/gemma-4-31b-it:free` |
| Clés | `OPENROUTER_API_KEY` dans `.env` (racine, hors git) ; clé maître et mot de passe de la base dans `secrets/` (hors git), créés au premier démarrage ; une clé virtuelle par harnais (alias = nom du harnais, plafond de 2 $, modèle `gemma-4-31b` seulement) |
| Journal | `journaux/appels.jsonl` (hors git) : une ligne par appel, succès ou échec |
| Réglages | pas de pause du déploiement après une erreur (`disable_cooldowns`), pas de nouvelle tentative par le relais (`num_retries: 0`) : le harnais reçoit les vrais 429 |

## Commandes

Depuis la racine du dépôt :

| Action | Commande |
|---|---|
| Démarrer | `banc-essai/traces/demarrer.sh` |
| Arrêter | `banc-essai/traces/arreter.sh` |
| Clé d'un harnais | `python3 banc-essai/traces/cles.py <harnais>` (écrit `secrets/cle-<harnais>.env`, jamais affichée) |

`banc-essai/cage/lancer.sh` crée la clé du harnais et extrait du journal les appels de l'essai.

## Champs du journal

| Champ | Contenu |
|---|---|
| `debut`, `fin`, `duree_s` | horodatage de l'appel (UTC) et durée |
| `cle` | alias de la clé virtuelle (nom du harnais, ou `<harnais>-relance`) |
| `modele_demande`, `modele` | nom demandé, modèle réel chez OpenRouter |
| `statut` | `succes` ou `echec` |
| `jetons_entree`, `jetons_sortie`, `cout` | consommation |
| `messages`, `images` | nombre de messages, nombre d'images envoyées (usage de la vision) |
| `flux`, `outils` | réponse en flux, nombre d'outils déclarés |
| `erreur` | type, code HTTP, message (toute chaîne qui ressemble à une clé est masquée) |

Sources : [clés virtuelles](https://docs.litellm.ai/docs/proxy/virtual_keys) (Postgres et clé maître exigés), [rappels personnalisés](https://docs.litellm.ai/docs/observability/custom_callback), [OpenRouter](https://docs.litellm.ai/docs/providers/openrouter), [réglages du routeur](https://docs.litellm.ai/docs/proxy/configs), [versions de l'image](https://docs.litellm.ai/blog/cleaner-release-versions) (consultés le 19/11/2026).
