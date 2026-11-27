# Modèle et fournisseur : brancher OpenRouter ou un portail compatible OpenAI

Cette page explique comment le banc joint le modèle d'IA, et comment le faire passer d'OpenRouter à un portail d'entreprise compatible OpenAI (une adresse et une clé), y compris derrière un mandataire HTTP et un certificat d'entreprise.

## 1. Principe : un seul point de contact avec le fournisseur

```mermaid
flowchart LR
    H["Harnais dans la cage"] -->|"clé de l'essai (virtuelle, plafonnée)"| R["Relais LiteLLM du banc<br/>127.0.0.1:4100"]
    W["Workflow relancé dans la cage"] -->|"clé de la relance"| R
    R -->|"vraie clé du fournisseur"| F["Fournisseur : OpenRouter<br/>ou portail compatible OpenAI"]
```

| Élément | Où il vit | Qui le voit |
|---|---|---|
| Vraie clé du fournisseur | `.env` (racine, hors git), puis `banc-essai/traces/secrets/fournisseur.env` | le relais seulement (conteneur `harness-litellm`) |
| Clé d'un essai | créée par `banc-essai/traces/cles.py`, supprimée à la fin de l'essai | le harnais, dans la cage |
| Description du modèle | `banc-essai/modele.env` (versionné, sans clé) | le relais, `cles.py`, la cage et les harnais |
| Configuration du relais | `banc-essai/traces/config.yaml` (généré, hors git) | le relais |

Aucun harnais ne reçoit la vraie clé. Changer de fournisseur ne touche à aucun harnais : seuls `modele.env` et `.env` changent.

## 2. Les deux fichiers à remplir

### 2.1 `banc-essai/modele.env` : quel modèle, avec quelles capacités

| Variable | Rôle | OpenRouter (réglage du dépôt) | Portail compatible OpenAI |
|---|---|---|---|
| `BANC_FOURNISSEUR` | fournisseur | `openrouter` | `portail` |
| `BANC_MODELE_FOURNISSEUR` | nom du modèle chez le fournisseur | `deepseek/deepseek-v4.1-flash-1017` | nom rendu par `GET <PORTAIL_URL>/models` |
| `BANC_OPENROUTER_ORDRE` | fournisseur imposé par OpenRouter, sans repli | `pearl-research` | ignoré |
| `BANC_MODELE` | nom vu par les harnais (lettres, chiffres, points, tirets) | `deepseek-v4.1-flash` | au choix, par exemple `modele-banc` |
| `BANC_CONTEXTE` | fenêtre de contexte en jetons | `1000000` | valeur annoncée par le portail |
| `BANC_SORTIE_MAX` | sortie maximale en jetons | `32768` | valeur annoncée par le portail |
| `BANC_VISION` | lecture d'images (1 ou 0) | `1` | résultat de `verifier_portail.py` |
| `BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE` | prix en dollars par million de jetons | prix du fournisseur | prix conventionnels si le portail n'en donne pas (section 5) |
| `BANC_BUDGET_ESSAI` | plafond de dépense d'une clé d'essai, en dollars | `2` | à fixer avec les prix conventionnels |

Qui lit quoi :

| Lecteur | Variables lues |
|---|---|
| `banc-essai/traces/generer_config.py` (appelé par `demarrer.sh`) | fournisseur, noms du modèle, ordre OpenRouter, prix |
| `banc-essai/traces/cles.py` | `BANC_MODELE` (seul modèle permis à la clé), `BANC_BUDGET_ESSAI` |
| `banc-essai/cage/cage.sh` | transmet aux harnais `BANC_MODELE`, `BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION`, `BANC_PRIX_*` |
| `harnais/opencode/configurer.sh`, `harnais/pi/configurer.sh` | contexte, sortie maximale, vision (et prix pour Pi) |
| `harnais/goose`, `harnais/gptme`, `harnais/cline` | `BANC_MODELE` seulement (voir la page `configuration.md` de chaque harnais) |

### 2.2 `.env` : les secrets (racine du dépôt, jamais commité)

Modèle commenté : [`.env.exemple`](../../.env.exemple). Créer le fichier et le protéger :

```bash
cp .env.exemple .env
chmod 600 .env
```

| Variable | Obligatoire | Contenu |
|---|---|---|
| `OPENROUTER_API_KEY` | avec `openrouter` | clé OpenRouter |
| `PORTAIL_URL` | avec `portail` | adresse de base du portail, avec le `/v1` final, sans `/chat/completions` |
| `PORTAIL_CLE` | avec `portail` | clé d'API du portail |
| `BANC_MANDATAIRE` | non | mandataire HTTP sortant : `http://hote:port` ou `http://identifiant:mot-de-passe@hote:port` |
| `BANC_CERTIFICAT` | non | chemin d'un fichier PEM des autorités de confiance, autorité interne comprise |

`demarrer.sh` ne charge jamais tout le `.env` : il en extrait seulement ces variables.

## 3. Passer au portail, étape par étape

1. Obtenir du portail : l'adresse de base, une clé, le nom exact du modèle, et savoir s'il faut un mandataire et un certificat.
2. Remplir `.env` (section 2.2).
3. Dans `banc-essai/modele.env` : `BANC_FOURNISSEUR=portail`, `BANC_MODELE_FOURNISSEUR=<nom du modèle>`, `BANC_MODELE=modele-banc`.
4. Vérifier le portail directement, sans le banc :

   ```bash
   python3 banc-essai/traces/verifier_portail.py
   ```

   Sept vérifications, rapport dans `banc-essai/traces/journaux/verification-portail.json` :

   | Vérification | Indispensable | Pourquoi |
   |---|---|---|
   | liste des modèles et présence du modèle demandé | oui | nom exact à reporter dans `BANC_MODELE_FOURNISSEUR` |
   | appel simple | oui | adresse, clé et mandataire corrects |
   | appel avec outil | oui | les harnais ne travaillent que par appels d'outils |
   | réponse en flux | oui | OpenCode, Goose, Cline et Pi demandent des réponses en flux |
   | flux avec appel d'outil | oui | forme exacte des requêtes des harnais |
   | lecture d'une image | non | à reporter dans `BANC_VISION` |
   | jetons comptés | oui | sans jetons, ni coût ni plafond |

   Le script ne montre jamais la clé. Code de sortie 0 : portail utilisable par les harnais.
5. Reporter dans `modele.env` la vision et, si le portail les annonce, le contexte et la sortie maximale.
6. Redémarrer le relais (il régénère `config.yaml`) :

   ```bash
   banc-essai/traces/demarrer.sh
   ```

7. Vérifier la chaîne complète depuis la cage (44 vérifications, dont l'absence de toute clé du fournisseur dans la cage) :

   ```bash
   banc-essai/cage/lancer.sh sonde jouet --essai sonde-portail
   grep bilan banc-essai/resultats/sonde-portail/harnais/stdout.log
   ```

Vérifié sur le banc le 27/11/2026 avec OpenRouter appelé comme un portail générique (`PORTAIL_URL=https://openrouter.ai/api/v1`) : vérificateur 7 sur 7, sonde 44 sur 44 ([`banc-essai/resultats/piag-sonde-portail/`](../resultats/piag-sonde-portail/rapport.md)).

## 4. Mandataire et certificat d'entreprise

| Situation | Réglage | Effet |
|---|---|---|
| Sortie Internet par un mandataire | `BANC_MANDATAIRE=http://hote:port` dans `.env` | le relais l'utilise (`HTTPS_PROXY`, `AIOHTTP_TRUST_ENV`) ; le filtre de la cage aussi, pour PyPI, Hugging Face et GitHub ; `verifier_portail.py` aussi |
| Mandataire avec identifiant | `http://identifiant:mot-de-passe@hote:port` | en-tête `Proxy-Authorization` envoyé par le filtre de la cage (vérifié avec un faux mandataire : accès accepté, refus avec un mauvais mot de passe) |
| Inspection TLS par une autorité interne | `BANC_CERTIFICAT=/chemin/ac.pem` dans `.env` | fichier copié dans `banc-essai/traces/certificats/ca.pem`, monté dans le relais (`SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`) ; `verifier_portail.py` l'utilise aussi |
| Images Docker à télécharger derrière le mandataire | réglage du service Docker du poste (hors banc) | voir la documentation Docker sur le mandataire du démon |

La vérification des certificats n'est jamais désactivée : un `SSL_VERIFY=False` exposerait la clé du portail à une interception.

Le fichier PEM de `BANC_CERTIFICAT` remplace la liste d'autorités du relais : il doit contenir l'autorité interne et, si le relais doit joindre d'autres sites, les autorités publiques (le paquet `ca-certificates` du poste les fournit souvent déjà avec l'autorité interne, par exemple `/etc/ssl/certs/ca-certificates.crt`).

Dans la cage, les harnais et les workflows téléchargent leurs paquets par le filtre de la cage, qui ouvre un tunnel TLS de bout en bout : ils utilisent les autorités du système (`/etc` du poste, en lecture seule). Si l'autorité interne n'y est pas, `uv` et `pip` refusent la connexion : l'ajouter au magasin du système du poste (action de l'administrateur du poste).

## 5. Coût et plafonds sans prix du fournisseur

Le relais calcule le coût de chaque appel avec les prix de `modele.env`, et refuse une clé d'essai au-delà de `BANC_BUDGET_ESSAI`. Avec un portail qui ne facture pas à l'appel, des prix conventionnels transforment ce plafond en plafond de jetons. Exemple : avec `BANC_PRIX_ENTREE=1`, `BANC_PRIX_CACHE=1` et `BANC_PRIX_SORTIE=1`, un plafond de 20 correspond à 20 millions de jetons par essai. Le coût affiché dans les rapports devient alors une mesure de volume, pas une dépense.

## 6. Problèmes fréquents

| Symptôme | Cause probable | Correction |
|---|---|---|
| `verifier_portail.py` : HTTP 404 à chaque appel | `PORTAIL_URL` sans `/v1`, ou avec `/chat/completions` | adresse de base seule, avec `/v1` |
| HTTP 401 ou 403 | clé fausse ou expirée | nouvelle clé dans `.env` |
| `CERTIFICATE_VERIFY_FAILED` | autorité interne inconnue | `BANC_CERTIFICAT` (section 4) |
| délai dépassé ou connexion refusée | mandataire absent ou faux | `BANC_MANDATAIRE` |
| « modèle ABSENT » à la première vérification | nom du modèle différent chez le portail | reprendre un nom de la liste affichée |
| appel avec outil en échec | le portail ignore `tools` | portail inutilisable par les harnais : signaler au fournisseur du portail |
| image en échec | modèle sans vision | `BANC_VISION=0` (le banc fonctionne en texte seul) |
| `demarrer.sh` : « LiteLLM ne répond pas » | erreur de configuration | `docker logs harness-litellm` |
| harnais : appel refusé, modèle non permis à la clé (non reproduit sur le banc) | `BANC_MODELE` changé sans redémarrer le relais | `banc-essai/traces/demarrer.sh` |

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| [`banc-essai/modele.env`](../modele.env) | description du modèle |
| [`.env.exemple`](../../.env.exemple) | modèle du fichier des secrets |
| [`banc-essai/traces/demarrer.sh`](../traces/demarrer.sh) | démarre le relais, écrit `config.yaml` et `secrets/fournisseur.env` |
| [`banc-essai/traces/generer_config.py`](../traces/generer_config.py) | configuration du relais |
| [`banc-essai/traces/verifier_portail.py`](../traces/verifier_portail.py) | vérification directe du fournisseur |
| [`banc-essai/traces/cles.py`](../traces/cles.py) | clés d'essai |
| [`banc-essai/traces/README.md`](../traces/README.md) | journal des appels, champs relevés |
| [`banc-essai/cage/relais.py`](../cage/relais.py) | filtre réseau de la cage, mandataire de l'entreprise |
