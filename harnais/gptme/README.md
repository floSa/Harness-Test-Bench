# gptme

gptme est un agent en ligne de commande écrit en Python : il donne à un modèle d'IA des outils (commandes shell, Python, lecture et écriture de fichiers) et enchaîne ses appels jusqu'à la fin de la tâche ; le banc le lance sans interaction, dans la cage, avec le modèle servi par le relais du banc.

| Élément | Valeur |
|---|---|
| Version figée | 0.37.0 (fichier [`version`](version), variable `VERSION` de [`installer.sh`](installer.sh)) ; publiée sur PyPI le 15/11/2026 |
| Licence | MIT (métadonnées du paquet PyPI) |
| Forme | paquet PyPI `gptme`, sans extension facultative, dans un environnement virtuel sur le Python du système (`/usr/bin/python3`, 3.11.5 au moins) |
| Dépôt officiel | <https://github.com/gptme/gptme> ; documentation <https://gptme.org/docs/> |
| Lancement sur le banc | `gptme --non-interactive --output-format json --tool-format tool` (dans [`lancer.sh`](lancer.sh)) |
| Essais réels | tâche jouet 100 % (48 s, 0,0022 $) ; extraction sans aide 100 % au test caché, 99,3 % à la relance (35 min, 0,30 $) |

| Fichier du dossier | Rôle |
|---|---|
| [`installer.sh`](installer.sh) | installe gptme 0.37.0 dans `installe/` (hors git) |
| [`configurer.sh`](configurer.sh) | écrit `$HOME/.config/gptme/config.toml` (fournisseur « banc » = relais du banc) |
| [`lancer.sh`](lancer.sh) | lance gptme sans interaction dans la cage ; sa sortie standard est la trace de la session |
| [`version`](version) | version relevée dans chaque essai (`essai.json`, champ `version_harnais`) |
| `installe/` | environnement virtuel créé par `installer.sh`, ignoré par git |
| `documentation/` | documentation détaillée (ci-dessous) |

## En trois commandes

Depuis la racine du dépôt, relais du modèle démarré (`banc-essai/traces/demarrer.sh`) :

```bash
harnais/gptme/installer.sh
harnais/gptme/installe/bin/python -c 'import importlib.metadata as m; print(m.version("gptme"))'
banc-essai/cage/lancer.sh gptme jouet --essai jouet-gptme
```

La deuxième commande doit afficher `0.37.0`. Le rapport de l'essai est ensuite dans `banc-essai/resultats/jouet-gptme/rapport.md`.

## Documentation détaillée

| Page | Contenu |
|---|---|
| [documentation/installation.md](documentation/installation.md) | prérequis, étapes de `installer.sh`, hôtes réseau à autoriser, mandataire et certificat d'entreprise, vérification, mise à jour, désinstallation |
| [documentation/configuration.md](documentation/configuration.md) | fichier écrit par `configurer.sh`, variables lues, changement de modèle ou de portail, autonomie, télémétrie, emplacement de la clé, pistes pour déclarer contexte et prix |
| [documentation/lancement.md](documentation/lancement.md) | lancer un essai, rôle de `lancer.sh` dans la cage, sorties et format de la trace, suivi, arrêt, essai à la main |
| [documentation/fonctionnement.md](documentation/fonctionnement.md) | capacités du harnais, constats chiffrés des essais, problèmes connus et dépannage, limites |

Vue d'ensemble des cinq harnais et contrat commun avec le banc : [../README.md](../README.md). Documentation du banc (modèle et fournisseur, goldset, lancement, sécurité) : [../../banc-essai/documentation/](../../banc-essai/documentation/README.md).
