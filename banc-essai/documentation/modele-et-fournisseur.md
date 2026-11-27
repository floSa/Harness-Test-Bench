# Modèle et portail : brancher le banc sur un portail compatible OpenAI

Cette page explique comment le banc joint le modèle d'IA par un portail compatible OpenAI (une adresse et une clé), y compris derrière un mandataire HTTP et un certificat d'entreprise.

## 1. Principe : un seul point de contact avec le portail

```mermaid
flowchart LR
    H["Harnais dans la cage"] -->|"clé de l'essai (virtuelle, plafonnée)"| R["Relais LiteLLM du banc<br/>127.0.0.1:4100"]
    W["Workflow relancé dans la cage"] -->|"clé de la relance"| R
    R -->|"vraie clé du portail"| F["Portail compatible OpenAI"]
```

| Élément | Où il vit | Qui le voit |
|---|---|---|
| Clé du portail | `.env` (racine, hors git), puis `banc-essai/traces/secrets/fournisseur.env` | le relais seulement (conteneur `harness-litellm`) |
| Clé d'un essai | créée par `banc-essai/traces/cles.py`, supprimée à la fin de l'essai | le harnais, dans la cage |
| Description du modèle | `banc-essai/modele.env` (versionné, sans clé) | le relais, `cles.py`, la cage et les harnais |
| Configuration du relais | `banc-essai/traces/config.yaml` (généré, hors git) | le relais |

Aucun harnais ne reçoit la clé du portail. Changer de modèle ne touche à aucun harnais : seuls `modele.env` et `.env` changent.

## 2. Les deux fichiers à remplir

### 2.1 `banc-essai/modele.env` : quel modèle, avec quelles capacités

| Variable | Rôle | Valeur livrée | À faire |
|---|---|---|---|
| `BANC_MODELE_FOURNISSEUR` | nom du modèle chez le portail | vide | nom rendu par `GET <PORTAIL_URL>/models` (affiché par `verifier_portail.py`) |
| `BANC_MODELE` | nom vu par les harnais (lettres, chiffres, points, tirets) | `modele-banc` | garder |
| `BANC_CONTEXTE` | fenêtre de contexte en jetons | `128000` | valeur annoncée par le portail |
| `BANC_SORTIE_MAX` | sortie maximale en jetons | `16384` | valeur annoncée par le portail |
| `BANC_VISION` | lecture d'images (1 ou 0) | `0` | résultat de `verifier_portail.py` |
| `BANC_PRIX_ENTREE`, `BANC_PRIX_CACHE`, `BANC_PRIX_SORTIE` | prix en dollars par million de jetons | `1` (prix conventionnels) | prix du portail s'il en a, sinon garder (section 5) |
| `BANC_BUDGET_ESSAI` | plafond d'une clé d'essai, dans l'unité des prix | `40` | à ajuster (section 5) |

Tant que `BANC_MODELE_FOURNISSEUR` est vide, `demarrer.sh` refuse de démarrer le relais et le dit.

Qui lit quoi :

| Lecteur | Variables lues |
|---|---|
| `banc-essai/traces/generer_config.py` (appelé par `demarrer.sh`) | nom du modèle chez le portail, nom exposé, prix |
| `banc-essai/traces/cles.py` | `BANC_MODELE` (seul modèle permis à la clé), `BANC_BUDGET_ESSAI` |
| `banc-essai/cage/cage.sh` | transmet aux harnais `BANC_MODELE`, `BANC_CONTEXTE`, `BANC_SORTIE_MAX`, `BANC_VISION`, `BANC_PRIX_*` |
| harnais | voir la page `configuration.md` de chaque harnais |

### 2.2 `.env` : les secrets (racine du dépôt, jamais commité)

Modèle commenté : [`.env.exemple`](../../.env.exemple).

```bash
cp .env.exemple .env
chmod 600 .env
```

| Variable | Obligatoire | Contenu |
|---|---|---|
| `PORTAIL_URL` | oui | adresse de base du portail, avec le `/v1` final, sans `/chat/completions` |
| `PORTAIL_CLE` | oui | clé d'API du portail ; l'utilisateur l'écrit lui-même, elle n'est jamais affichée |
| `BANC_MANDATAIRE` | non | mandataire HTTP sortant : `http://hote:port` ou `http://identifiant:mot-de-passe@hote:port` |
| `BANC_CERTIFICAT` | non | chemin d'un fichier PEM des autorités de confiance, autorité interne comprise |

`demarrer.sh` ne charge jamais tout le `.env` : il en extrait seulement ces variables.

## 3. Brancher le portail, étape par étape

1. Obtenir : l'adresse de base du portail, une clé, le nom du modèle, et savoir s'il faut un mandataire et un certificat (section 4).
2. Remplir `.env` (section 2.2).
3. Vérifier le portail directement, sans le banc. Si le nom du modèle est encore inconnu, le passer par `--modele` : la première vérification affiche les modèles disponibles.

   ```bash
   python3 banc-essai/traces/verifier_portail.py --modele <nom supposé>
   ```

   Sept vérifications, rapport dans `banc-essai/traces/journaux/verification-portail.json` :

   | Vérification | Indispensable | Pourquoi |
   |---|---|---|
   | liste des modèles et présence du modèle demandé | oui | nom exact à reporter dans `BANC_MODELE_FOURNISSEUR` |
   | appel simple | oui | adresse, clé et mandataire corrects |
   | appel avec outil | oui | les harnais ne travaillent que par appels d'outils |
   | réponse en flux | oui | la plupart des harnais demandent des réponses en flux |
   | flux avec appel d'outil | oui | forme exacte des requêtes des harnais |
   | lecture d'une image | non | à reporter dans `BANC_VISION` |
   | jetons comptés | oui | sans jetons, ni coût ni plafond |

   Le script ne montre jamais la clé. Code de sortie 0 : portail utilisable par les harnais.
4. Remplir `banc-essai/modele.env` : nom du modèle, vision, contexte et sortie maximale.
5. Démarrer le relais (il génère `config.yaml`) :

   ```bash
   banc-essai/traces/demarrer.sh
   ```

6. Vérifier la chaîne complète depuis la cage (42 vérifications, 41 sans vision, dont l'absence de toute clé du portail dans la cage) :

   ```bash
   banc-essai/cage/lancer.sh sonde jouet --essai sonde-portail
   grep bilan banc-essai/resultats/sonde-portail/harnais/stdout.log
   ```

## 4. Mandataire et certificat d'entreprise

| Situation | Réglage | Effet |
|---|---|---|
| Sortie Internet par un mandataire | `BANC_MANDATAIRE=http://hote:port` dans `.env` | utilisé par le relais (`HTTPS_PROXY`, `AIOHTTP_TRUST_ENV`), par le filtre de la cage (PyPI, Hugging Face, GitHub) et par `verifier_portail.py` |
| Mandataire avec identifiant | `http://identifiant:mot-de-passe@hote:port` | en-tête `Proxy-Authorization` envoyé par le filtre de la cage |
| Inspection TLS par une autorité interne | `BANC_CERTIFICAT=/chemin/ac.pem` dans `.env` | fichier copié dans `banc-essai/traces/certificats/ca.pem`, monté dans le relais (`SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`) ; utilisé aussi par `verifier_portail.py` |
| Installations des harnais derrière le mandataire | `. outils/env-mandataire.sh` avant `installer.sh` | exporte mandataire et certificat pour curl, npm, Node, pip et uv |
| Images Docker à télécharger derrière le mandataire | réglage du service Docker du poste (hors banc) | voir la documentation Docker sur le mandataire du démon |

La vérification des certificats n'est jamais désactivée : un `SSL_VERIFY=False` exposerait la clé du portail à une interception.

Le fichier PEM de `BANC_CERTIFICAT` remplace la liste d'autorités du relais : il doit contenir l'autorité interne et les autorités publiques (le paquet `ca-certificates` du poste les réunit souvent déjà, par exemple dans `/etc/ssl/certs/ca-certificates.crt`).

Dans la cage, les harnais et les workflows téléchargent leurs paquets par le filtre de la cage, qui ouvre un tunnel TLS de bout en bout : ils utilisent les autorités du système (`/etc` du poste, en lecture seule). Si l'autorité interne n'y est pas, `uv` et `pip` refusent la connexion : l'ajouter au magasin du système du poste.

## 5. Coût et plafonds

Le relais calcule le coût de chaque appel avec les prix de `modele.env`, et refuse une clé d'essai au-delà de `BANC_BUDGET_ESSAI`. Avec les prix conventionnels livrés (1 par million de jetons, entrée comme sortie), le plafond de 40 vaut 40 millions de jetons par essai, et le « coût » des rapports devient une mesure de volume. Avec les prix réels du portail, le plafond et les coûts sont en dollars.

## 6. Problèmes fréquents

| Symptôme | Cause probable | Correction |
|---|---|---|
| `verifier_portail.py` : HTTP 404 à chaque appel | `PORTAIL_URL` sans `/v1`, ou avec `/chat/completions` | adresse de base seule, avec `/v1` |
| HTTP 401 ou 403 | clé fausse ou expirée | nouvelle clé dans `.env` |
| `CERTIFICATE_VERIFY_FAILED` | autorité interne inconnue | `BANC_CERTIFICAT` (section 4) |
| délai dépassé ou connexion refusée | mandataire absent ou faux | `BANC_MANDATAIRE` |
| « modèle ABSENT » à la première vérification | nom différent chez le portail | reprendre un nom de la liste affichée |
| appel avec outil en échec | le portail ignore `tools` | portail inutilisable par les harnais : à signaler aux responsables du portail |
| image en échec | modèle sans vision | `BANC_VISION=0` (le banc fonctionne en texte seul) |
| `demarrer.sh` : « BANC_MODELE_FOURNISSEUR à remplir » | `modele.env` non rempli | section 2.1 |
| `demarrer.sh` : « LiteLLM ne répond pas » | erreur de configuration | `docker logs harness-litellm` |

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| [`banc-essai/modele.env`](../modele.env) | description du modèle |
| [`.env.exemple`](../../.env.exemple) | modèle du fichier des secrets |
| [`banc-essai/traces/demarrer.sh`](../traces/demarrer.sh) | démarre le relais, écrit `config.yaml` et `secrets/fournisseur.env` |
| [`banc-essai/traces/generer_config.py`](../traces/generer_config.py) | configuration du relais |
| [`banc-essai/traces/verifier_portail.py`](../traces/verifier_portail.py) | vérification directe du portail |
| [`banc-essai/traces/cles.py`](../traces/cles.py) | clés d'essai |
| [`banc-essai/traces/README.md`](../traces/README.md) | journal des appels, champs relevés |
| [`banc-essai/cage/relais.py`](../cage/relais.py) | filtre réseau de la cage, mandataire de l'entreprise |
| [`outils/env-mandataire.sh`](../../outils/env-mandataire.sh) | mandataire et certificat pour les installations |
