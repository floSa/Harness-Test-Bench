# Consigne d'amorçage : brancher le banc des harnais sur un poste d'entreprise

Ce fichier est le prompt à donner à un agent de code (par exemple : « Lis piag/AMORCAGE.md et exécute-le niveau par niveau. ») sur le poste d'entreprise, dans le clone de la branche `PIAG`. Il décrit sept niveaux. Chaque niveau a une condition de fin vérifiable : ne passer au suivant que lorsqu'elle est remplie, et noter le résultat dans `piag/journal-poste.md` (hors git).

## Rôle et but

Tu es l'agent chargé d'installer et de faire tourner ce banc d'essai sur ce poste. Le banc compare des harnais d'agents (OpenCode, Pi, gptme, Goose, Cline) sur l'extraction d'informations dans des PDF. Ici :

- le modèle est servi par un **portail compatible OpenAI** (une adresse et une clé) ;
- les documents sont un **goldset** de l'équipe : `goldset/` à la racine du dépôt, avec `split/train`, `split/val`, `split/test` (PDF) et `split/train_ground_truth.json`, `split/val_ground_truth.json`, `split/test_ground_truth.json` (pour chaque PDF, les valeurs à extraire), plus `goldset/ground_truth.json` (tous les documents) ;
- le but final : un tableau qui compare les harnais sur ce goldset.

Lis d'abord, dans cet ordre : `README.md`, `banc-essai/README.md`, `banc-essai/documentation/README.md`. Chaque niveau ci-dessous renvoie à la page détaillée à lire avant d'agir.

## Règles permanentes (non négociables)

1. **Rien ne quitte ce poste vers GitHub.** Ne jamais pousser. Ne jamais utiliser `git commit --no-verify`. Les données du goldset, les résultats des essais goldset et `.env` ne sont jamais versionnés. Les commits locaux sont permis (ils restent sur le poste).
2. **Ne jamais afficher une clé** (ni dans un message, ni dans un fichier de compte rendu, ni dans une commande visible). Les clés ne vivent que dans `.env` (`chmod 600`).
3. **Ne jamais modifier le goldset** (`goldset/`). Si sa forme n'est pas reconnue, adapter le code de l'importateur, pas les données.
4. **Ne jamais désactiver la vérification des certificats** (pas de `SSL_VERIFY=False`, pas de `--insecure`, pas de `verify=False`) : utiliser le certificat de l'entreprise (`BANC_CERTIFICAT`).
5. Interdits : `sudo` sans accord explicite de l'utilisateur, `pkill -f`, `killall`, ouvrir un port ailleurs que sur `127.0.0.1`, `docker ... prune`, toucher à d'autres conteneurs que `harness-litellm` et `harness-litellm-db`.
6. Rien de mémoire : chaque affirmation repose sur une commande lancée ou un fichier lu. Ce qui n'a pas pu être vérifié est écrit « non vérifié ».
7. Une seule décision est réservée à l'utilisateur à chaque fois qu'elle se présente : la lui poser, une question à la fois, avec ta recommandation. Les décisions réservées sont listées dans chaque niveau.
8. Python : `uv` et Python 3.12.

## Niveau 0. Diagnostic du poste

À lire : `banc-essai/documentation/lancer-un-essai.md` (section 1), `banc-essai/documentation/securite-et-donnees.md`.

1. Installer les garde-fous, en mode poste d'entreprise, avant toute autre chose :

   ```bash
   outils/installer-garde-fous.sh --poste-entreprise
   git config core.hooksPath
   ```

2. Relever, sans rien installer, et écrire dans `piag/diagnostic.md` (tableau : élément, commande, résultat, OK ou KO, correction proposée) :

   | Élément | Commande |
   |---|---|
   | système | `cat /etc/os-release`, `uname -r` (Linux natif ou WSL) |
   | bubblewrap | `bwrap --version` ; essai : `bwrap --ro-bind /usr /usr --symlink usr/bin /bin --unshare-all true && echo ok` |
   | espaces de noms utilisateur | `cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null` ; sous Ubuntu 24.04, profil AppArmor de bwrap |
   | systemd de l'utilisateur | `systemd-run --user --scope true && echo ok` |
   | Docker et Compose | `docker version`, `docker compose version`, `docker run --rm hello-world` |
   | uv, Python 3.12 | `uv --version`, `uv python find 3.12` |
   | outils | `curl --version`, `git --version`, `ss -V`, `flock --version` |
   | carte graphique | `nvidia-smi` (facultatif) |
   | mandataire | `env \| grep -i _proxy` (noms seulement), configuration du poste |
   | certificat d'entreprise | présence d'une autorité interne dans `/etc/ssl/certs/` ou fichier fourni par l'utilisateur |
   | accès réseau | `curl -sI https://pypi.org`, `https://github.com`, `https://registry.npmjs.org`, `https://nodejs.org`, `https://ghcr.io` (par le mandataire s'il existe) |
   | place disque | `df -h ~` (prévoir 40 Go) |

3. Pour chaque KO : proposer la correction ; si elle demande des droits d'administration (paquet système, profil AppArmor, groupe docker), la décrire à l'utilisateur et attendre.

**Décision réservée :** toute installation système.
**Fin du niveau 0 :** `piag/diagnostic.md` complet, tous les éléments indispensables (bubblewrap, systemd utilisateur, Docker, uv, accès à PyPI et GitHub) à OK.

## Niveau 1. Portail du modèle

À lire : `banc-essai/documentation/modele-et-fournisseur.md` en entier.

1. Demander à l'utilisateur, s'il ne les a pas donnés : l'adresse du portail, le nom du modèle à utiliser, le mandataire et le certificat éventuels. La clé, il l'écrit lui-même dans `.env` : ne jamais la demander en clair dans la conversation.
2. `cp .env.exemple .env && chmod 600 .env`, puis l'utilisateur remplit `PORTAIL_URL`, `PORTAIL_CLE`, et si besoin `BANC_MANDATAIRE`, `BANC_CERTIFICAT`.
3. `python3 banc-essai/traces/verifier_portail.py --modele <nom du modèle>` : lire chaque ligne (la première vérification affiche les modèles du portail si le nom est faux). Les vérifications indispensables doivent toutes réussir (outils et flux compris : sans eux, aucun harnais ne peut travailler).
4. Remplir `banc-essai/modele.env` : `BANC_MODELE_FOURNISSEUR` (nom exact du modèle), `BANC_VISION` (résultat de la vérification d'image), `BANC_CONTEXTE` et `BANC_SORTIE_MAX` (annoncés par le portail ou sa documentation, sinon demander à l'utilisateur), et des prix : ceux du portail s'il en a, sinon des prix conventionnels (section 5 de la page) avec un `BANC_BUDGET_ESSAI` qui laisse un essai aller au bout (repère : un essai de construction consomme couramment de 10 à 30 millions de jetons d'entrée, en grande partie relus dans le cache ; plafond livré : 40 millions).
5. `banc-essai/traces/demarrer.sh`, puis la sonde :

   ```bash
   banc-essai/cage/lancer.sh sonde jouet --essai sonde-portail
   grep bilan banc-essai/resultats/sonde-portail/harnais/stdout.log
   ```

**Décisions réservées :** modèle choisi, prix conventionnels et plafond par essai.
**Fin du niveau 1 :** vérificateur sans KO indispensable ; sonde « 42/42 vérifications conformes » (ou 41/41 si le modèle n'a pas de vision) ; le rapport de la sonde ne contient aucune clé.

## Niveau 2. Banc sans harnais

1. Tests automatiques : `uv run --project banc-essai/evaluation pytest` : tous réussis.
2. Démonstration du goldset (données publiques) :

   ```bash
   python3 banc-essai/corpus/goldset_demo.py
   python3 banc-essai/corpus/consignes_goldset.py --goldset banc-essai/corpus/demo/import
   ```

**Fin du niveau 2 :** tests réussis ; import de démonstration conforme (`banc-essai/corpus/demo/import/rapport-import.md`, contrôle de la notation « oui » sur les trois jeux).

## Niveau 3. Harnais, un par un

À lire : `harnais/README.md`, puis pour chaque harnais `harnais/<harnais>/README.md` et son dossier `documentation/` (installation, configuration, lancement, fonctionnement).

Ordre conseillé : `pi`, `opencode`, `goose`, `gptme`, `cline`. Pour chacun :

1. installation, dans un terminal où le mandataire et le certificat de `.env` sont chargés (les scripts d'installation ne lisent pas `.env` eux-mêmes) :

   ```bash
   . outils/env-mandataire.sh
   harnais/<harnais>/installer.sh
   ```

   Hôtes réseau à autoriser : `documentation/installation.md` du harnais ;
2. vérifier la version installée (commande donnée dans le README du harnais) ;
3. tâche jouet dans la cage : `banc-essai/cage/lancer.sh <harnais> jouet --essai jouet-<harnais>` ;
4. lire `banc-essai/resultats/jouet-<harnais>/rapport.md`.

Un harnais qui échoue après deux corrections raisonnables est mis de côté, avec la cause dans le journal : il ne bloque pas les autres.

**Fin du niveau 3 :** pour chaque harnais retenu, tâche jouet réussie dans la cage, avec trace complète et appels visibles dans `traces/appels.jsonl`.

## Niveau 4. Goldset de l'équipe

À lire : `banc-essai/documentation/goldset.md` en entier.

1. Vérifier que `goldset/` est à la racine et ignoré : `git check-ignore goldset/split && echo ignoré`.
2. Importer : `python3 banc-essai/corpus/importer_goldset.py`, puis lire `banc-essai/corpus/goldset/rapport-import.md` en entier.
3. Si l'import s'arrête sur une forme non reconnue : adapter `importer_goldset.py` (section 7 de la page), ajouter un cas de test qui reproduit cette forme dans `banc-essai/evaluation/tests/test_goldset.py`, relancer les tests, puis l'import.
4. Présenter à l'utilisateur, champ par champ, le schéma proposé (`banc-essai/corpus/goldset/schema.json`) : type, tolérance, ordre jour/mois, valeurs des listes fermées, et une description par champ ; plus la description générale des documents. Signaler en particulier les identifiants faits de chiffres (à garder en texte), les champs toujours `null`, les types mélangés et les écarts avec `ground_truth.json`.
5. Après accord : `"valide": true`, relancer l'import (code de sortie 0 attendu), puis `python3 banc-essai/corpus/consignes_goldset.py`, et faire relire `banc-essai/corpus/goldset/recette/consignes.md` par l'utilisateur.

**Décisions réservées :** chaque règle de notation du schéma, la répartition des jeux si l'utilisateur en veut une autre (par défaut train fourni, val test caché, test relance).
**Fin du niveau 4 :** rapport d'import sans constat bloquant ni échec de conversion ; contrôle de la notation « oui » sur les trois jeux ; schéma validé ; consignes générées et relues.

## Niveau 5. Premier essai complet

1. Un seul harnais (celui qui a le mieux réussi la tâche jouet), détaché du terminal :

   ```bash
   setsid nohup banc-essai/cage/lancer.sh <harnais> goldset --essai g01-<harnais> > ~/banc-espaces/g01.log 2>&1 < /dev/null &
   python3 banc-essai/cage/suivi.py g01-<harnais>
   ```

2. Suivre toutes les 10 minutes ; arrêt propre si besoin (section 5 de `lancer-un-essai.md`).
3. Lire `banc-essai/resultats-goldset/g01-<harnais>/rapport.md` : score final, documents entièrement justes, relance, coût.
4. Contrôler que rien n'est versionnable : `git status --short` ne doit montrer aucun fichier du goldset ni des résultats goldset.

**Fin du niveau 5 :** rapport complet avec relance ; aucune clé restante (`ls banc-essai/traces/secrets/ | grep '^cle-'` vide) ; `git status` propre de toute donnée.

## Niveau 6. Campagne et comparaison

1. Chaque harnais retenu, une fois, sur le goldset, un essai à la fois (`g01-<harnais>`, `g02-<harnais>`...). Si le budget le permet, une deuxième passe pour mesurer la variabilité.
2. Tableau comparatif dans `piag/comparaison.md` (hors git, il cite des résultats internes) : harnais en colonnes, critères en lignes : score de relance, documents entièrement justes à la relance, score final au test caché, écart entre score annoncé et score réel, taux d'invention et d'omission, coût et durée de construction, coût et durée par document à la relance, incidents.
3. Lecture : la relance (workflow seul, sur des documents jamais vus) est la mesure principale ; un écart de quelques points entre deux harnais sur une seule passe n'est pas une différence établie.

**Fin du niveau 6 :** tableau comparatif complet, chaque chiffre renvoyant au rapport d'essai d'où il vient.

## Compte rendu

À la fin de chaque niveau, ajouter à `piag/journal-poste.md` : date, ce qui a été fait, résultats vérifiés (chiffres), problèmes et corrections, décisions prises par l'utilisateur, reste à faire. Une modification du code du banc fait l'objet d'un commit local (jamais poussé), en français, préfixé par le périmètre.
