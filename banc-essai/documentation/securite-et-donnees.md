# Sécurité et données : ce que le banc protège, et comment

Un harnais d'agent exécute des commandes, écrit des fichiers et appelle un modèle sans demander de confirmation. Le banc lui laisse cette autonomie, mais dans des limites qu'il ne peut pas franchir. Sur un poste d'entreprise, il faut en plus que rien des documents ne sorte du poste.

## 1. Ce qui est protégé

| Risque | Protection | Où | Vérification |
|---|---|---|---|
| Le harnais lit la clé du portail | la clé n'existe que dans `.env` et dans le conteneur du relais ; le harnais reçoit une clé virtuelle propre à l'essai | `banc-essai/traces/` | sonde : absence de `PORTAIL_CLE` et `BANC_FOURNISSEUR_CLE` dans la cage |
| Le harnais dépense sans limite | plafond par clé d'essai (`BANC_BUDGET_ESSAI`), clé supprimée dès la fin du harnais | `banc-essai/traces/cles.py` | dépense de la clé relevée dans `essai.json` |
| Le harnais se sert d'une autre route du relais | la clé d'essai n'est permise que sur les routes d'appel au modèle | `cles.py` (`ROUTES`) | sonde : routes de gestion et de transfert direct refusées |
| Le harnais lit le test caché ou le reste de la machine | cage bubblewrap : seul l'espace de l'essai est visible et inscriptible ; `/usr` et `/etc` en lecture seule | `banc-essai/cage/cage.sh` | sonde : lecture du dépôt et du test caché impossible |
| Le harnais envoie des données sur Internet | aucun réseau dans la cage, sauf le relais du modèle, l'API de soumission et un filtre qui ne laisse passer que PyPI, Hugging Face et GitHub (en téléchargement, 10 Go au plus) | `banc-essai/cage/relais.py` | `traces/reseau.jsonl` de chaque essai ; sonde : autres sites refusés |
| Le harnais épuise la machine | mémoire (16 Go), disque (30 Go), durée (2 h) plafonnés | `cage.sh`, `lancer.sh` | `traces/memoire.json`, `traces/disque.txt` |
| Une clé apparaît dans une trace | toute chaîne qui ressemble à une clé est masquée dans les résultats | `banc-essai/cage/masquer.py` | |
| Les documents de l'entreprise partent sur GitHub | goldset, import et résultats goldset hors git ; garde-fou de commit ; push refusé sur un poste d'entreprise | `.gitignore`, `outils/git/` | section 2 |

Le détail des preuves de la cage (42 vérifications) est dans [`banc-essai/cage/README.md`](../cage/README.md).

## 2. Les données de l'entreprise ne quittent pas le poste

Le dépôt est public. Sur le poste d'entreprise, tout ce qui touche au goldset reste local :

| Contenu | Emplacement | Versionné |
|---|---|---|
| Goldset source | `goldset/` | non (`.gitignore`) |
| Goldset importé (PDF, réponses, schéma, consignes) | `banc-essai/corpus/goldset/` | non |
| Démonstration | `banc-essai/corpus/demo/` | non |
| Résultats des essais goldset (les traces recopient le texte des documents) | `banc-essai/resultats-goldset/` | non |
| Secrets | `.env`, `banc-essai/traces/secrets/`, `banc-essai/traces/certificats/` | non |
| Espace de travail et dossier personnel de chaque essai (copies des documents, code et sessions du harnais) | `~/banc-espaces/<essai>/`, hors du dépôt | non ; à effacer à la fin de la campagne si les documents ne doivent pas rester sur le poste |

Garde-fous git, installés une fois par clone :

```bash
outils/installer-garde-fous.sh --poste-entreprise
```

| Garde-fou | Refuse | Fichier |
|---|---|---|
| avant un commit | goldset, import, démonstration, résultats goldset, `.env`, secrets et certificats du relais, PDF hors du corpus public, fichier de plus de 20 Mo | [`outils/git/pre-commit`](../../outils/git/pre-commit) |
| avant un push | tout push, dès que `.poste-entreprise` existe à la racine (créé par l'option `--poste-entreprise`) | [`outils/git/pre-push`](../../outils/git/pre-push) |

Vérifié dans un dépôt jetable : commit propre accepté ; `.env`, fichier du goldset, résultat goldset et PDF hors corpus refusés ; PDF du corpus de démonstration accepté ; push accepté sans `.poste-entreprise`, refusé avec.

Contrôle à tout moment :

```bash
git config core.hooksPath        # doit afficher outils/git
git status --ignored --short | grep -E 'goldset|resultats-goldset|\.env'   # doivent être ignorés (!!)
```

## 3. Ce que le banc ne protège pas

| Limite | Conséquence | Parade |
|---|---|---|
| Le contenu des documents part au portail du modèle | c'est le principe même de l'extraction par un modèle | n'utiliser qu'un portail autorisé pour ces documents |
| Les paquets téléchargés depuis PyPI, Hugging Face ou GitHub ne sont pas inspectés | un paquet piégé s'exécute dans la cage | la cage borne ce qu'il peut atteindre ; garder les essais sur un poste sans autre donnée sensible accessible |
| `/etc` du poste est visible en lecture dans la cage | la configuration système est lisible (pas les dossiers personnels) | ne pas laisser de secret dans `/etc` |
| `git commit --no-verify` contourne le garde-fou de commit | un fichier interdit peut être commité volontairement | la consigne d'amorçage interdit `--no-verify` ; le garde-fou de push reste actif |
