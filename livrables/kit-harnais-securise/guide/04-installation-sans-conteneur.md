# 4. Installation sans conteneur (bubblewrap)

[Retour au sommaire](../README.md)

Le relais et le filtre tournent comme de simples programmes Python sur le poste. Le harnais tourne dans une cage bubblewrap : il utilise les mêmes mécanismes du noyau qu'un conteneur, sans image ni service. bubblewrap est l'outil d'isolement des applications Flatpak.

Dans la cage, le harnais :

- voit `espace/` (sous `/travail`), son dossier de configuration et le système du poste en lecture seule ;
- ne voit ni le dossier personnel, ni `.env`, ni les disques Windows ;
- n'a aucun réseau, seulement deux passages vers le relais et le filtre ;
- est limité en mémoire, en processeur et en nombre de processus.

Prérequis : Linux ou WSL2 avec systemd, python3. Toutes les commandes se lancent depuis le dossier du kit.

## Étape 0. Installer bubblewrap

Droits d'administration, une fois par poste :

```bash
sudo apt install bubblewrap apparmor-profiles
```

Vérifier que bubblewrap peut créer une cage :

```bash
bwrap --ro-bind / / --unshare-user --unshare-net true && echo "bubblewrap utilisable"
```

Sur Ubuntu 24.04, cette vérification peut échouer avec `setting up uid map: Permission denied`. C'est une protection d'Ubuntu (AppArmor) qui réserve cette fonction aux programmes autorisés. Ubuntu fournit l'autorisation de bubblewrap sans l'activer. Pour l'activer (droits d'administration) :

```bash
sudo cp /usr/share/apparmor/extra-profiles/bwrap-userns-restrict /etc/apparmor.d/
```

```bash
sudo apparmor_parser -r /etc/apparmor.d/bwrap-userns-restrict
```

Puis relancer la vérification. Ce profil n'autorise que bubblewrap ; il est préférable à la désactivation de la protection pour tout le poste.

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

## Étape 2. Installer le harnais

Le harnais s'installe dans `sans-conteneur/harnais/`, visible dans la cage en lecture seule. Exemple avec Goose (les autres harnais : [05-brancher-un-harnais.md](05-brancher-un-harnais.md)) :

```bash
mkdir -p sans-conteneur/harnais/bin
curl -fsSL -o goose.tar.gz https://github.com/aaif-goose/goose/releases/download/v1.60.1/goose-x86_64-unknown-linux-gnu.tar.gz
echo "0327b1857f8030343f59b77503e0455629bbf472c2901cb94b88389d6278635a  goose.tar.gz" | sha256sum -c
tar -xzf goose.tar.gz -C sans-conteneur/harnais/bin ./goose && rm goose.tar.gz
```

## Étape 3. Vérifier les protections

```bash
python3 sans-conteneur/lancer.py python3 /kit/verifier.py --appel
```

Attendu : `Bilan : 21 sur 21 protections conformes.` En cas de ligne `NON CONFORME`, voir [07-depannage.md](07-depannage.md).

## Étape 4. Travailler

```bash
python3 sans-conteneur/lancer.py
```

La commande démarre le relais et le filtre, puis ouvre un terminal dans la cage, dans `/travail`. Y configurer le harnais ([05-brancher-un-harnais.md](05-brancher-un-harnais.md)), puis le lancer. À la sortie du terminal (`exit`), le relais et le filtre s'arrêtent. Une seule session à la fois.

## Étape 5. Suivre la consommation

```bash
python3 outils/bilan.py
```

## Recommencer à zéro

| Besoin | Commande |
|---|---|
| Effacer la configuration du harnais | supprimer `sans-conteneur/maison/` |
| Remettre le compteur de jetons à zéro | supprimer `journaux/compteur.json` |
| Changer la clé locale | `bash preparer.sh --nouvelle-cle` |

## Essai sans clé du portail

1. Dans `.env` : `IAG_URL=http://127.0.0.1:4198/v1`, `IAG_CLE=cle-factice`, `IAG_MODELE=modele-factice`, puis `bash preparer.sh`.
2. Dans un second terminal : `ECOUTE=127.0.0.1:4198 python3 outils/faux_portail.py`. Ce terminal affiche ce que le relais transmet au portail (jamais la valeur de la clé).
3. `python3 sans-conteneur/lancer.py python3 /kit/verifier.py --appel`
