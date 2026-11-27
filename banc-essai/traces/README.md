# Traces : relais LiteLLM du banc

Relais entre les harnais et le portail compatible OpenAI. Il garde la clé du portail, donne à chaque essai sa propre clé plafonnée et journalise chaque appel. Guide de branchement : [modele-et-fournisseur.md](../documentation/modele-et-fournisseur.md).

| Élément | Valeur |
|---|---|
| Conteneurs | `harness-litellm` (`ghcr.io/berriai/litellm:v1.106.4`), `harness-litellm-db` (`postgres:17.7-alpine`, exigé par les clés virtuelles) |
| Adresse | `http://127.0.0.1:4100` (API compatible OpenAI, `/v1/chat/completions`) |
| Modèle exposé | `BANC_MODELE` de `banc-essai/modele.env`, relayé en mode générique (`openai/<BANC_MODELE_FOURNISSEUR>`, `api_base` = `PORTAIL_URL`), avec les prix déclarés dans `modele.env` |
| Configuration | `config.yaml`, écrit par `generer_config.py` à chaque `demarrer.sh` (hors git) |
| Clés | `PORTAIL_URL` et `PORTAIL_CLE` lues dans `.env` (racine, hors git) et recopiées seules par `demarrer.sh` dans `secrets/fournisseur.env` (`BANC_FOURNISSEUR_URL`, `BANC_FOURNISSEUR_CLE`), avec le mandataire et le certificat éventuels ; le reste du `.env` n'entre pas dans le conteneur ; clé maître et mot de passe de la base dans `secrets/` (hors git), créés au premier démarrage ; une clé virtuelle par essai (alias = nom de l'essai, plafond `BANC_BUDGET_ESSAI`, modèle `BANC_MODELE` seulement, routes d'appel au modèle seulement), supprimée dès la sortie du harnais |
| Journal | `journaux/appels.jsonl` (hors git) : une ligne par appel, succès ou échec |
| Réglages | pas de pause du déploiement après une erreur (`disable_cooldowns`), pas de nouvelle tentative par le relais (`num_retries: 0`) : le harnais reçoit les vrais 429 ; dépense des clés écrite en base toutes les 1 à 6 s (`proxy_batch_write_at: 1`) |

## Commandes

Depuis la racine du dépôt :

| Action | Commande |
|---|---|
| Vérifier le portail, sans le relais | `python3 banc-essai/traces/verifier_portail.py` |
| Démarrer ou redémarrer | `banc-essai/traces/demarrer.sh` |
| Arrêter | `banc-essai/traces/arreter.sh` |
| Clé d'un essai | `python3 banc-essai/traces/cles.py <alias>` (écrit `secrets/cle-<alias>.env`, jamais affichée) ; `--supprimer <alias>` la retire ; `--depense <alias>` donne sa dépense |

`banc-essai/cage/lancer.sh` crée la clé de l'essai, extrait du journal les appels de l'essai, puis supprime la clé.

## Champs du journal

| Champ | Contenu |
|---|---|
| `debut`, `fin`, `duree_s` | horodatage de l'appel (UTC) et durée |
| `cle` | alias de la clé virtuelle (nom de l'essai, ou `<essai>-relance`) |
| `modele_demande`, `modele`, `fournisseur` | nom demandé, modèle réel renvoyé par le portail, fournisseur s'il est indiqué |
| `statut` | `succes` ou `echec` |
| `jetons_entree`, `jetons_cache`, `jetons_sortie` | jetons envoyés (dont lus dans le cache) et produits |
| `cout`, `cout_fournisseur` | coût calculé par le relais avec les prix de `modele.env` ; coût renvoyé par le portail s'il en renvoie un |
| `messages`, `images` | nombre de messages, nombre d'images envoyées (usage de la vision) |
| `flux`, `outils` | réponse en flux, nombre d'outils déclarés |
| `erreur` | type, code HTTP, message (toute chaîne qui ressemble à une clé est masquée) |

Sources : [clés virtuelles](https://docs.litellm.ai/docs/proxy/virtual_keys) (Postgres et clé maître exigés), [rappels personnalisés](https://docs.litellm.ai/docs/observability/custom_callback), [fournisseur compatible OpenAI](https://docs.litellm.ai/docs/providers/openai_compatible), [réglages du routeur](https://docs.litellm.ai/docs/proxy/configs).
