# Pi

Pi est un harnais d'agent de code en ligne de commande, minimaliste et extensible, écrit en TypeScript pour Node.js : il donne au modèle quatre outils (lire, exécuter une commande, modifier, écrire un fichier) et enchaîne les appels jusqu'à la fin de la tâche.

| Élément | Valeur |
|---|---|
| Version figée | 1.5.2 (`installer.sh`, variable `VERSION` ; fichier `version`) ; dernière version publiée le 27/11/2026 : 1.6.1 (registre npm) |
| Paquet | `@earendil-works/pi-coding-agent` (npm), projet repris de `@mariozechner/pi-coding-agent` |
| Licence | MIT (`package.json` du paquet installé) |
| Forme | ligne de commande (interface en terminal, mode sans interaction, mode JSON, mode RPC) |
| Moteur | Node.js 26.13.1 propre au harnais (Pi exige Node.js 22.19 ou plus récent) |
| Dépôt officiel | [github.com/earendil-works/pi](https://github.com/earendil-works/pi) (dossier `packages/coding-agent`) |
| Documentation officielle de la version | [docs de la v1.5.2](https://github.com/earendil-works/pi/tree/v1.5.2/packages/coding-agent/docs), aussi présente après installation dans `harnais/pi/installe/pi/node_modules/@earendil-works/pi-coding-agent/docs/` |

| Fichier du dossier | Rôle |
|---|---|
| [`installer.sh`](installer.sh) | installe Node.js et Pi dans `harnais/pi/installe/` (hors git) |
| [`configurer.sh`](configurer.sh) | écrit `models.json` et `settings.json` de Pi à partir des variables `BANC_*` |
| [`lancer.sh`](lancer.sh) | point d'entrée dans la cage : configure, puis lance `pi --mode json` |
| [`version`](version) | version relevée dans les rapports d'essai (`pi 1.5.2`) |
| `installe/` | Node.js et Pi installés, hors git, créé par `installer.sh` |
| [`documentation/`](documentation/) | les quatre pages ci-dessous |

## En trois commandes

Depuis la racine du dépôt, relais du modèle démarré (`banc-essai/traces/demarrer.sh`) :

```bash
harnais/pi/installer.sh
```

```bash
harnais/pi/installe/node/bin/node harnais/pi/installe/pi/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js --version
```

Réponse attendue : `1.5.2`.

```bash
banc-essai/cage/lancer.sh pi jouet
```

Les résultats arrivent dans `banc-essai/resultats/<essai>/` (dossier créé par le lanceur ; nom par défaut : `pi-jouet-<AAAAMMJJ-HHMMSS>`) ; ceux de la recette `goldset`, dans `banc-essai/resultats-goldset/<essai>/`. L'essai jouet est court et ne fait que quelques appels au modèle : il sert à vérifier le harnais avant un essai `goldset`.

## Documentation

| Page | Contenu |
|---|---|
| [Installation](documentation/installation.md) | prérequis, ce que fait `installer.sh`, hôtes contactés, mandataire et certificat d'entreprise, vérification, mise à jour, désinstallation |
| [Configuration](documentation/configuration.md) | fichiers écrits par `configurer.sh` (exemple réel), variables lues, lien avec `banc-essai/modele.env`, autonomie, télémétrie et réseau coupés, emplacement de la clé |
| [Lancement](documentation/lancement.md) | lancer un essai par recette, ce qui se passe dans la cage, sorties et format de la trace, suivi, arrêt, essai à la main |
| [Fonctionnement](documentation/fonctionnement.md) | capacités du harnais avec sources, comportements constatés lors des essais de mise au point du banc, problèmes connus et dépannage, limites |

Voir aussi : [vue d'ensemble des harnais](../README.md) et [documentation du banc](../../banc-essai/documentation/).
