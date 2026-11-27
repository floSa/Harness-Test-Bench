# Consigne d'amorçage : mettre en place le banc des harnais sur un poste d'entreprise

Ce fichier est le prompt à donner à un agent de code sur le poste, dans le clone de la branche `PIAG` (par exemple : « Lis piag/AMORCAGE.md et exécute-le niveau par niveau, en t'arrêtant à chaque décision réservée. »).

## Mission

Mettre en place le banc et **prouver que toute la base est solide et fonctionne**. La mission ne comprend **aucun essai** de harnais sur le goldset et aucune comparaison : elle s'arrête quand tout est prêt à lancer un essai, et vérifié.

Concrètement :

1. le poste a tout ce qu'il faut (WSL, Docker, bubblewrap, systemd, accès réseau) ;
2. le modèle **Gemini 3.7 Flash** du portail compatible OpenAI (portail IAG) répond, avec les fonctions dont les harnais ont besoin ;
3. le goldset `goldset/` (à la racine du dépôt) est lu dans `goldset/split/` et ses données sont rangées aux bons endroits : `train` et `val` donnés aux harnais avec leurs réponses, `test` servi par l'API de test sans ses réponses ;
4. l'API de test répond et note correctement ;
5. chaque harnais est installé et se branche bien sur le portail (un message, une réponse : pas de tâche) ;
6. la documentation est mise à jour avec tout ce qui a été appris sur ce poste, pour que chaque personne puisse reprendre un harnais, le lancer, le tester et le faire évoluer seule ;
7. un bilan `piag/etat-du-poste.md` dit, point par point, ce qui est OK ou KO, avec sa preuve.

Lire d'abord, dans cet ordre : `README.md`, `banc-essai/README.md`, `banc-essai/documentation/README.md`. Chaque niveau ci-dessous renvoie à la page détaillée à lire avant d'agir. Chaque niveau a une condition de fin vérifiable : ne passer au suivant que lorsqu'elle est remplie.

## Règles permanentes (non négociables)

1. **Rien ne quitte ce poste vers GitHub.** Ne jamais pousser. Ne jamais utiliser `git commit --no-verify`. Le goldset, son import, les résultats et `.env` ne sont jamais versionnés.
2. **Commits locaux** : un par étape, en français, préfixé par le périmètre, avec l'identité de `piag/identite.local` (niveau 0) et la ligne `Co-authored-by: <COAUTEUR>` à la fin de chaque message de commit.
3. **Ne jamais afficher une clé** (ni dans un message, ni dans un fichier de compte rendu, ni dans une commande visible). La clé du portail ne vit que dans `.env` (`chmod 600`) : l'utilisateur l'y écrit lui-même ; ne jamais la lui demander en clair.
4. **Ne jamais modifier le goldset** (`goldset/`). Si sa forme n'est pas reconnue, adapter le code de l'importateur, pas les données.
5. **Ne jamais désactiver la vérification des certificats** (pas de `SSL_VERIFY=False`, `--insecure`, `verify=False`) : utiliser le certificat de l'entreprise (`BANC_CERTIFICAT`).
6. **Pas d'essai** : ne lancer `banc-essai/cage/lancer.sh <harnais> goldset` à aucun moment. Seuls sont permis : la sonde de la cage, et le test de connexion des harnais (`harnais/verifier-connexion.sh`).
7. Interdits : `sudo` sans accord explicite de l'utilisateur, `pkill -f`, `killall`, ouvrir un port ailleurs que sur `127.0.0.1`, `docker ... prune`, toucher à d'autres conteneurs que `harness-litellm` et `harness-litellm-db`.
8. Rien de mémoire : chaque affirmation repose sur une commande lancée ou un fichier lu ; ce qui n'a pas pu être vérifié est écrit « non vérifié ».
9. Les décisions réservées à l'utilisateur lui sont posées une à la fois, avec une recommandation.
10. Python : `uv` et Python 3.12.
11. **Documentation tenue à jour au fil de l'eau** : tout réglage, contournement, valeur du portail, adaptation de code ou comportement d'un harnais découvert sur ce poste est reporté dans la page qui en parle (niveau 6), sans jamais y écrire de clé ni recopier le contenu d'un document du goldset.

## Niveau 0. Identité, garde-fous, diagnostic du poste

À lire : `banc-essai/documentation/securite-et-donnees.md`, `banc-essai/documentation/lancer-un-essai.md` (section 1).

1. Garde-fous, avant toute autre chose :

   ```bash
   outils/installer-garde-fous.sh --poste-entreprise
   git config core.hooksPath        # doit afficher outils/git
   ```

2. Identité git : l'utilisateur copie `piag/identite.exemple` en `piag/identite.local` et le remplit. Puis :

   ```bash
   git check-ignore piag/identite.local && . piag/identite.local
   git config user.name "$GIT_UTILISATEUR" && git config user.email "$GIT_EMAIL"
   ```

   Vérifier `git config user.name` et `git config user.email`, et garder `COAUTEUR` pour la ligne `Co-authored-by` des commits.
3. Diagnostic, sans rien installer, écrit dans `piag/etat-du-poste.md` (tableau : élément, commande, résultat, OK ou KO, correction proposée) :

   | Élément | Commande | Attendu |
   |---|---|---|
   | système | `cat /etc/os-release`, `uname -r` | Ubuntu sous WSL2 (noyau `microsoft-standard-WSL2`) |
   | systemd dans WSL | `systemctl --user is-system-running`, `systemd-run --user --scope true` | réussite ; sinon `[boot] systemd=true` dans `/etc/wsl.conf`, puis `wsl --shutdown` depuis Windows |
   | mémoire de WSL | `free -g` | au moins 20 Go ; sinon `memory=` dans `%UserProfile%\.wslconfig` côté Windows |
   | disque | `df -h ~` | au moins 40 Go libres |
   | bubblewrap et cage | `bwrap --version` ; `E=$(mktemp -d) M=$(mktemp -d); banc-essai/cage/cage.sh --espace $E --maison $M --memoire 2G --duree 30 --sans-reseau -- bash -c 'echo ok; ls /home'` | `ok` puis `banc` (la cage démarre, plafond de mémoire compris, et ne voit pas les dossiers personnels) ; sinon profil AppArmor de bwrap (Ubuntu 24.04) ou systemd |
   | Docker et Compose | `docker version`, `docker compose version` | client et serveur répondent |
   | images du relais | `docker pull ghcr.io/berriai/litellm:v1.106.4`, `docker pull postgres:17.7-alpine` | téléchargées (sinon : mandataire du démon Docker) |
   | uv, Python 3.12 | `uv --version`, `uv python find 3.12` | trouvés (sinon `uv python install 3.12`) |
   | outils | `curl --version`, `git --version`, `ss -V`, `flock --version`, `python3 --version` | présents |
   | mandataire et certificat | `env \| grep -i _proxy` (noms seulement) ; autorité interne dans `/etc/ssl/certs/` | relevés, à reporter au niveau 1 |
   | sites d'installation | `curl -sI` sur `https://pypi.org`, `https://github.com`, `https://registry.npmjs.org`, `https://nodejs.org`, `https://ghcr.io` (après `. outils/env-mandataire.sh` s'il y a un mandataire) | réponse HTTP de chacun ; liste des sites bloqués à faire ouvrir |

4. Pour chaque KO : décrire la correction à l'utilisateur ; celles qui demandent des droits d'administration ou un réglage Windows sont à sa main.

**Décision réservée :** toute installation système ou tout réglage Windows.
**Fin du niveau 0 :** garde-fous et identité en place ; diagnostic complet ; tous les éléments indispensables (systemd, bubblewrap, Docker et images, uv, PyPI et GitHub joignables) à OK.

## Niveau 1. Portail IAG et modèle Gemini 3.7 Flash

À lire : `banc-essai/documentation/modele-et-fournisseur.md` en entier.

1. `cp .env.exemple .env && chmod 600 .env` ; l'utilisateur y écrit `PORTAIL_URL` (adresse de base, avec le `/v1` final) et `PORTAIL_CLE`, et si besoin `BANC_MANDATAIRE` et `BANC_CERTIFICAT` (relevés au niveau 0).
2. Vérification directe du portail, avec le modèle Gemini 3.7 Flash. Son nom exact chez le portail n'est pas connu d'avance : la première vérification affiche la liste des modèles du portail ; y repérer celui de Gemini 3.7 Flash et relancer avec ce nom.

   ```bash
   python3 banc-essai/traces/verifier_portail.py --modele gemini-3.7-flash
   ```

   Les vérifications indispensables (liste des modèles, appel simple, appel avec outil, flux, flux avec outil, jetons comptés) doivent toutes réussir : sans outils ni flux, aucun harnais ne peut travailler. Si l'une échoue, le rapporter tel quel à l'utilisateur, sans contournement.
3. Remplir `banc-essai/modele.env` : `BANC_MODELE_FOURNISSEUR` (nom exact), `BANC_VISION` (résultat de la vérification d'image), `BANC_CONTEXTE` et `BANC_SORTIE_MAX` (valeurs annoncées par le portail ou sa documentation ; sinon demander à l'utilisateur), prix (ceux du portail s'il en a, sinon garder les prix conventionnels de 1) et `BANC_BUDGET_ESSAI` (40 millions de jetons par défaut).
4. Quota du portail : demander à l'utilisateur les limites connues (appels par minute, jetons par jour) et les noter dans le bilan ; relancer `verifier_portail.py` deux fois de suite et relever toute réponse 429.
5. Relais et sonde de la cage :

   ```bash
   banc-essai/traces/demarrer.sh
   banc-essai/cage/lancer.sh sonde jouet --essai sonde-portail
   grep bilan banc-essai/resultats/sonde-portail/harnais/stdout.log
   ```

**Décisions réservées :** confirmation du modèle retenu ; prix et plafond par essai.
**Fin du niveau 1 :** vérificateur sans KO indispensable ; sonde « 42/42 vérifications conformes » (41/41 si le modèle n'a pas de vision) ; aucune clé dans les résultats de la sonde.

## Niveau 2. Tests automatiques du banc

```bash
uv run --project banc-essai/evaluation pytest
```

**Fin du niveau 2 :** tous les tests réussis.

## Niveau 3. Données du goldset

À lire : `banc-essai/documentation/goldset.md` en entier.

1. Vérifier que `goldset/` est à la racine, avec `split/train`, `split/val`, `split/test` et les trois `split/*_ground_truth.json`, et qu'il est ignoré par git :

   ```bash
   ls goldset goldset/split
   git check-ignore goldset/split && echo ignoré
   ```

2. Importer (répartition par défaut : `train` et `val` vers le jeu fourni aux harnais, `test` vers le test caché de l'API et vers la relance) :

   ```bash
   python3 banc-essai/corpus/importer_goldset.py
   ```

   Puis lire `banc-essai/corpus/goldset/rapport-import.md` en entier : documents écartés, doublons, écarts avec `ground_truth.json`, types de chaque champ, échecs de conversion.
3. Si l'import s'arrête sur une forme non reconnue : adapter `banc-essai/corpus/importer_goldset.py` (section 7 de la page), ajouter un cas de test qui reproduit cette forme dans `banc-essai/evaluation/tests/test_goldset.py`, relancer les tests, puis l'import.
4. Présenter à l'utilisateur, champ par champ, le schéma proposé (`banc-essai/corpus/goldset/schema.json`) : type, tolérance des nombres, ordre jour et mois des dates, valeurs des listes fermées, une description par champ, et la description générale des documents. Signaler les identifiants faits de chiffres (à garder en texte), les champs toujours `null`, les types mélangés.
5. Après accord : `"valide": true`, relancer l'import (code de sortie 0 attendu), générer les consignes, les faire relire :

   ```bash
   python3 banc-essai/corpus/importer_goldset.py
   python3 banc-essai/corpus/consignes_goldset.py
   ```

**Décisions réservées :** chaque règle de notation du schéma ; les consignes données aux harnais.
**Fin du niveau 3 :** rapport d'import sans constat bloquant ni échec de conversion ; contrôle de la notation « oui » sur les trois jeux ; schéma validé ; consignes générées et relues ; `git status --short` ne montre aucun fichier du goldset.

## Niveau 4. API de test

```bash
uv run --project banc-essai/evaluation python banc-essai/evaluation/verifier_api.py
```

Dix vérifications : schéma validé ; état de l'API ; liste des documents de test ; PDF servis identiques ; réponses du test jamais servies ; espace d'un harnais sans aucun PDF du test ; soumission mal formée refusée sans être décomptée ; réponses attendues notées 100 % ; réponses altérées sous 100 % ; jeu de relance.

**Fin du niveau 4 :** « 10/10 vérifications conformes ».

## Niveau 5. Harnais : installation et branchement au portail

À lire : `harnais/README.md`, puis pour chaque harnais `harnais/<harnais>/README.md` et `harnais/<harnais>/documentation/installation.md`.

Pour chaque harnais (`pi`, `opencode`, `goose`, `gptme`, `cline`) :

1. installation, dans un terminal où le mandataire et le certificat de `.env` sont chargés :

   ```bash
   . outils/env-mandataire.sh
   harnais/<harnais>/installer.sh
   ```

2. version installée (commande donnée dans le README du harnais) ;
3. branchement au portail, dans la cage : un seul message (« Réponds seulement : OK »), aucune tâche :

   ```bash
   harnais/verifier-connexion.sh <harnais>
   ```

   Conforme : au moins un appel au modèle, aucun en échec, code de retour 0. La ligne affiche aussi les sites refusés au démarrage (sans effet sur le banc, à noter).

Un harnais qui échoue après deux corrections raisonnables est noté KO avec sa cause : il ne bloque pas les autres.

**Fin du niveau 5 :** chaque harnais installé, avec sa version, et « OK » au test de connexion (ou KO expliqué).

## Niveau 6. Documentation à jour

But : une personne qui reprend un harnais n'a besoin que de sa documentation pour l'installer sur ce poste, le lancer sur le goldset, lire ses résultats, modifier sa configuration et revérifier qu'il fonctionne.

| Page | À reporter |
|---|---|
| `banc-essai/documentation/modele-et-fournisseur.md` | section « Portail de ce poste » : nom exact du modèle, contexte, sortie maximale, vision, quota relevé, mandataire et certificat nécessaires (sans clé), résultats du vérificateur et de la sonde, problèmes rencontrés et corrections |
| `banc-essai/documentation/goldset.md` | section « Goldset de ce poste » : forme réelle des fichiers de vérité, adaptations faites à l'importateur (et test ajouté), nombre de documents par jeu, décisions de l'utilisateur sur le schéma (types, tolérances, dates, listes fermées) |
| `harnais/<harnais>/documentation/installation.md` | réglages nécessaires sur ce poste (mandataire, certificat, sites à ouvrir), version installée, problèmes et corrections |
| `harnais/<harnais>/documentation/fonctionnement.md` | résultat du test de connexion, sites refusés au démarrage, comportements observés, problèmes connus avec ce portail |
| `harnais/<harnais>/README.md` | section « Prise en main sur ce poste » : vérifier le branchement (`harnais/verifier-connexion.sh <harnais>`), lancer un essai jouet puis un essai goldset (commandes complètes), où lire les résultats (`banc-essai/resultats-goldset/<essai>/rapport.md`), où modifier la configuration (`configurer.sh`, `lancer.sh`) et comment revérifier après une modification |
| `piag/README.md` | état du poste en une phrase et renvoi au bilan |

Contrôles après mise à jour : liens relatifs de toutes les pages valides ; aucune clé ni adresse de mandataire avec mot de passe ; aucun extrait de document du goldset ; un commit local par page ou groupe de pages, avec la ligne `Co-authored-by`.

**Fin du niveau 6 :** chaque page du tableau mise à jour, pour chaque harnais.

## Niveau 7. Bilan

Compléter `piag/etat-du-poste.md` (hors git) :

| Section | Contenu |
|---|---|
| Poste | diagnostic du niveau 0, corrections faites |
| Portail | modèle retenu (nom exact), vérifications réussies, vision, contexte, quota relevé |
| Relais et cage | bilan de la sonde |
| Données | nombre de documents par jeu (fourni, test caché, relance), constats de l'import, schéma validé |
| API de test | bilan de `verifier_api.py` |
| Harnais | tableau : harnais en colonnes ; version, installation, connexion au portail, sites refusés en lignes |
| Reste à faire | points KO, décisions en attente |
| Prêt pour un essai | commande d'un essai, à ne pas lancer : `banc-essai/cage/lancer.sh <harnais> goldset --essai <nom>` |

**Fin de la mission :** bilan complet, chaque ligne avec sa preuve (commande et résultat) ; aucune clé restante (`ls banc-essai/traces/secrets/ | grep '^cle-'` vide) ; `git status --short` propre de toute donnée ; commits locaux faits, rien de poussé.
