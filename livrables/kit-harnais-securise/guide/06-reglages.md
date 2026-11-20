# 6. Réglages

[Retour au sommaire](../README.md)

## Les réglages de `.env`

`.env` est créé par `bash preparer.sh` à partir de `.env.exemple`. Il contient la clé du portail : ne jamais le partager ni le versionner. Après une modification, relancer le relais (`docker compose up -d relais`, ou une nouvelle session sans conteneur).

| Réglage | Rôle | Valeur par défaut |
|---|---|---|
| `IAG_URL` | adresse de l'API du portail, avec `/v1`, sans `/chat/completions` | à renseigner |
| `IAG_CLE` | clé personnelle du portail ; lue par le relais seul | à renseigner |
| `IAG_MODELE` | modèle utilisé par le harnais | à renseigner |
| `IAG_MODELES` | autres modèles autorisés, séparés par des virgules | `IAG_MODELE` seul |
| `PLAFOND_JETONS` | jetons envoyés et produits sur toute la durée du test ; au-delà, le relais refuse | 30 000 000 |
| `APPELS_PAR_MINUTE` | débit maximal | 60 |
| `APPELS_SIMULTANES` | appels transmis en même temps au portail | 4 |
| `MEMOIRE_MAX`, `CPU_MAX` | ressources du harnais | 8g, 4 |
| `DOMAINES_AUTORISES` | seuls sites joignables par le harnais (`.exemple.org` inclut les sous-domaines) | PyPI et registre npm |
| `QUOTA_TELECHARGEMENT_MO` | volume total téléchargeable | 5 000 Mo |
| `HTTPS_PROXY`, `NO_PROXY` | proxy de l'entreprise, utilisé par le relais et le filtre | aucun |
| `SSL_CERT_FILE` | certificat de l'autorité interne de l'entreprise : `/certificats/<fichier>` avec conteneur (fichier déposé dans `certificats/`), chemin du fichier sur le poste sans conteneur | aucun |
| `IAG_ENTETE_CLE` | en-tête qui porte la clé, si le portail n'utilise pas `Authorization: Bearer` (ex. `api-key`) | `Authorization` |
| `IAG_ENTETES` | en-têtes fixes exigés par le portail, en JSON | aucun |
| `ROUTES_SUPPLEMENTAIRES` | autres routes que `/v1/chat/completions` (ex. `/v1/responses`) | aucune |
| `COMPTER_FLUX` | `0` si le portail refuse le champ `stream_options` | `1` |

Ordre de grandeur pour le plafond : une tâche d'une demi-heure consomme de 6 à 21 millions de jetons, car le harnais renvoie toute la conversation à chaque appel.

## Questions à poser aux administrateurs du portail

| Question | Pourquoi |
|---|---|
| Adresse exacte de l'API compatible OpenAI (avec `/v1`) | réglage `IAG_URL` |
| Nom exact du modèle, et la liste des modèles accessibles | réglage `IAG_MODELE` |
| Le modèle accepte-t-il l'appel d'outils (« function calling ») ? | indispensable : sans outils, un harnais parle mais n'agit pas |
| Les réponses en flux (`stream: true`) sont-elles acceptées ? | la plupart des harnais les utilisent |
| Taille de contexte du modèle | les harnais envoient de longues conversations |
| Limites de débit et quota par clé | régler `APPELS_PAR_MINUTE` et `PLAFOND_JETONS` en dessous |
| La clé passe-t-elle par `Authorization: Bearer` ou par un autre en-tête ? | réglage `IAG_ENTETE_CLE` |
| Quel niveau de données le portail peut-il recevoir ? Les requêtes sont-elles conservées ? | tout ce que le harnais lit peut partir au portail |

## Ce que le relais transmet au portail

| Ce que le harnais envoie au relais | Ce que le portail reçoit |
|---|---|
| `POST $OPENAI_BASE_URL/chat/completions` | `POST <IAG_URL>/chat/completions` |
| `Authorization: Bearer <clé locale>` | `Authorization: Bearer <clé du portail>`, ou l'en-tête de `IAG_ENTETE_CLE` |
| aucun en-tête particulier | les en-têtes de `IAG_ENTETES` |
| `model`, `messages`, `tools`, `stream`… | les mêmes champs, plus `stream_options` pour compter les jetons d'une réponse en flux |
| autres en-têtes du harnais | non transmis |
