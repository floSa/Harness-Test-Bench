# 2. Installation avec Docker

[Retour au sommaire](../README.md)

Prérequis : Docker Engine et Docker Compose v2 (`docker compose version` répond). Sous Windows, Docker Desktop ou Docker Engine installé dans WSL2 ; la licence de Docker Desktop est à vérifier avec le service informatique.

Toutes les commandes se lancent depuis le dossier du kit.

## Étape 1. Créer les réglages

```bash
bash preparer.sh
```

La première fois, le script crée `.env` et s'arrête. Ouvrir `.env` et renseigner :

```bash
IAG_URL=https://<adresse du portail>/v1
IAG_CLE=<clé personnelle du portail>
IAG_MODELE=<nom exact du modèle>
```

Puis relancer `bash preparer.sh`. Le script crée la clé locale du relais, celle que le harnais connaîtra à la place de la vraie clé. Les autres réglages sont décrits dans [06-reglages.md](06-reglages.md).

## Étape 2. Choisir le harnais

Dans `harnais/Dockerfile`, adapter la section « INSTALLATION DU HARNAIS » ; Goose y est installé en exemple. La ligne de chaque harnais est donnée dans [05-brancher-un-harnais.md](05-brancher-un-harnais.md).

Installer le harnais dans l'image fige sa version pour tous les testeurs. Pendant le test, l'image est en lecture seule : le harnais ne peut pas se modifier.

## Étape 3. Construire et démarrer

```bash
docker compose build
```

```bash
docker compose up -d relais filtre
```

## Étape 4. Vérifier les protections

```bash
docker compose run --rm harnais python3 /kit/verifier.py --appel
```

Attendu : `Bilan : 21 sur 21 protections conformes.` L'option `--appel` fait un vrai appel de quelques jetons au modèle. En cas de ligne `NON CONFORME`, voir [07-depannage.md](07-depannage.md).

## Étape 5. Travailler

```bash
docker compose run --rm harnais
```

La commande ouvre un terminal dans le conteneur, dans `/travail`, qui correspond au dossier `espace/`. Y configurer le harnais ([05-brancher-un-harnais.md](05-brancher-un-harnais.md)), puis le lancer.

## Étape 6. Suivre la consommation

```bash
python3 outils/bilan.py
```

Le bilan donne les appels, les jetons, les refus du relais et les téléchargements, sans jamais afficher le contenu des échanges.

## Arrêter, recommencer à zéro

| Besoin | Commande |
|---|---|
| Arrêter (configuration, espace et journaux gardés) | `docker compose down` |
| Effacer aussi la configuration du harnais | `docker compose down -v` |
| Remettre le compteur de jetons à zéro | supprimer `journaux/compteur.json`, puis `docker compose up -d relais` |
| Changer la clé locale | `bash preparer.sh --nouvelle-cle`, puis `docker compose up -d relais` |

## Essai sans clé du portail

Pour tout essayer avant d'avoir la clé, ou montrer le kit à une équipe sécurité :

1. Dans `.env` : `IAG_URL=http://faux-portail:4198/v1`, `IAG_CLE=cle-factice`, `IAG_MODELE=modele-factice`, puis `bash preparer.sh`.
2. `docker compose --profile essai up -d relais filtre faux-portail`
3. `docker compose run --rm harnais python3 /kit/verifier.py --appel`
4. `docker compose logs faux-portail` montre ce que le relais transmet au portail (jamais la valeur de la clé).
