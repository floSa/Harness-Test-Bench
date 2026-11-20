# Traces : LiteLLM du banc

Relais entre les harnais et OpenRouter, propre au banc : LLM-Service et les conteneurs `rag-*` et `llm-*` ne sont ni utilisés ni modifiés.

| Élément | Valeur |
|---|---|
| Conteneurs | `harness-litellm` (`ghcr.io/berriai/litellm:v1.106.4`), `harness-litellm-db` (`postgres:17.7-alpine`, exigé par les clés virtuelles) |
| Adresse | `http://127.0.0.1:4100` (API compatible OpenAI, `/v1/chat/completions`) |
| Modèle exposé | `deepseek-v4.1-flash` -> `openrouter/deepseek/deepseek-v4.1-flash-1017`, fournisseur Pearl Research seul (fp8, sans repli) ; prix déclarés au relais : 0,05 $ par million de jetons envoyés, 0,003 $ lus dans le cache, 0,30 $ produits (relevés le 19/11/2026) |
| Clés | `OPENROUTER_API_KEY` dans `.env` (racine, hors git), recopiée seule par `demarrer.sh` dans `secrets/fournisseur.env` sous le nom `BANC_OPENROUTER_KEY` (le reste du `.env` n'entre pas dans le conteneur ; les routes de transfert direct de LiteLLM ne trouvent aucune clé de fournisseur) ; clé maître et mot de passe de la base dans `secrets/` (hors git), créés au premier démarrage ; une clé virtuelle par essai (alias = nom de l'essai, plafond de 2 $, modèle `deepseek-v4.1-flash` seulement, routes d'appel au modèle seulement), supprimée dès la sortie du harnais ; limite de 10 $ posée sur la clé OpenRouter |
| Journal | `journaux/appels.jsonl` (hors git) : une ligne par appel, succès ou échec |
| Réglages | pas de pause du déploiement après une erreur (`disable_cooldowns`), pas de nouvelle tentative par le relais (`num_retries: 0`) : le harnais reçoit les vrais 429 ; dépense des clés écrite en base toutes les 1 à 6 s (`proxy_batch_write_at: 1`) |

Autre fournisseur compatible OpenAI (portail d'entreprise) : [guide d'adaptation](../../documentations/adapter-point-d-acces.md) ; `faux_portail.py` imite un point d'accès pour vérifier ce que le relais transmet, sans dépense.

## Commandes

Depuis la racine du dépôt :

| Action | Commande |
|---|---|
| Démarrer | `banc-essai/traces/demarrer.sh` |
| Arrêter | `banc-essai/traces/arreter.sh` |
| Clé d'un essai | `python3 banc-essai/traces/cles.py <alias>` (écrit `secrets/cle-<alias>.env`, jamais affichée) ; `--supprimer <alias>` la retire ; `--depense <alias>` donne sa dépense |

`banc-essai/cage/lancer.sh` crée la clé de l'essai, extrait du journal les appels de l'essai, puis supprime la clé.

## Champs du journal

| Champ | Contenu |
|---|---|
| `debut`, `fin`, `duree_s` | horodatage de l'appel (UTC) et durée |
| `cle` | alias de la clé virtuelle (nom de l'essai, ou `<essai>-relance`) |
| `modele_demande`, `modele`, `fournisseur` | nom demandé, modèle réel chez OpenRouter, fournisseur qui a servi l'appel (absent en réponse en flux) |
| `statut` | `succes` ou `echec` |
| `jetons_entree`, `jetons_cache`, `jetons_sortie` | jetons envoyés (dont lus dans le cache) et produits |
| `cout`, `cout_openrouter` | coût calculé par le relais, coût facturé par OpenRouter (dollars) |
| `messages`, `images` | nombre de messages, nombre d'images envoyées (usage de la vision) |
| `flux`, `outils` | réponse en flux, nombre d'outils déclarés |
| `erreur` | type, code HTTP, message (toute chaîne qui ressemble à une clé est masquée) |

Sources : [clés virtuelles](https://docs.litellm.ai/docs/proxy/virtual_keys) (Postgres et clé maître exigés), [rappels personnalisés](https://docs.litellm.ai/docs/observability/custom_callback), [OpenRouter](https://docs.litellm.ai/docs/providers/openrouter), [réglages du routeur](https://docs.litellm.ai/docs/proxy/configs), [versions de l'image](https://docs.litellm.ai/blog/cleaner-release-versions) (consultés le 19/11/2026).
