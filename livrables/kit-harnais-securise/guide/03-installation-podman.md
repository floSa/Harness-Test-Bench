# 3. Installation avec Podman

[Retour au sommaire](../README.md)

Podman lit les mêmes fichiers que Docker et fonctionne sans droits d'administration. Toutes les commandes se lancent depuis le dossier du kit.

## Étape 0. Installer Podman, s'il manque

Droits d'administration, une fois par poste (Ubuntu 24.04 fournit Podman 4.9 et podman-compose 1.0.6) :

```bash
sudo apt install podman podman-compose
```

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

Puis relancer `bash preparer.sh`. Les autres réglages sont décrits dans [06-reglages.md](06-reglages.md).

## Étape 2. Déclarer le complément Podman

Dans chaque nouveau terminal :

```bash
export COMPOSE_FILE=compose.yaml:compose.podman.yaml
```

Pourquoi : sans droits d'administration, Podman décale les numéros d'utilisateur des conteneurs. `compose.podman.yaml` les fait correspondre à ceux du poste. Sans lui, le harnais ne peut pas écrire dans `espace/`.

## Étape 3. Choisir le harnais

Dans `harnais/Dockerfile`, adapter la section « INSTALLATION DU HARNAIS » ; Goose y est installé en exemple. La ligne de chaque harnais est donnée dans [05-brancher-un-harnais.md](05-brancher-un-harnais.md).

## Étape 4. Construire et démarrer

```bash
podman compose build
```

```bash
podman compose up -d relais filtre
```

Des messages `the container name … is already in use` peuvent apparaître avec podman-compose 1.0.6 : ils sont sans effet.

## Étape 5. Vérifier les protections

```bash
podman compose run --rm harnais python3 /kit/verifier.py --appel
```

Attendu : `Bilan : 21 sur 21 protections conformes.`

Point propre à Podman : les limites de mémoire et de processus ne s'appliquent que si le système les délègue à l'utilisateur. Ubuntu 24.04 le fait par défaut. Si « mémoire plafonnée » est `NON CONFORME`, voir [07-depannage.md](07-depannage.md).

## Étape 6. Travailler

```bash
podman compose run --rm harnais
```

La commande ouvre un terminal dans le conteneur, dans `/travail`, qui correspond au dossier `espace/`. Y configurer le harnais ([05-brancher-un-harnais.md](05-brancher-un-harnais.md)), puis le lancer.

## Étape 7. Suivre la consommation

```bash
python3 outils/bilan.py
```

## Arrêter, recommencer à zéro

| Besoin | Commande |
|---|---|
| Arrêter (configuration, espace et journaux gardés) | `podman compose down` |
| Effacer aussi la configuration du harnais | `podman compose down -v` |
| Remettre le compteur de jetons à zéro | supprimer `journaux/compteur.json`, puis `podman compose up -d relais` |
| Changer la clé locale | `bash preparer.sh --nouvelle-cle`, puis `podman compose up -d relais` |

## Essai sans clé du portail

1. Dans `.env` : `IAG_URL=http://faux-portail:4198/v1`, `IAG_CLE=cle-factice`, `IAG_MODELE=modele-factice`, puis `bash preparer.sh`.
2. `podman compose up -d relais filtre faux-portail`
3. `podman compose run --rm harnais python3 /kit/verifier.py --appel`
4. `podman compose logs faux-portail` montre ce que le relais transmet au portail (jamais la valeur de la clé).
