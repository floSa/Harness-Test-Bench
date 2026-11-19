# Protocole du banc des harnais

Version 1.6, 19 novembre 2026 (cadre de ressources de la cage : mémoire, carte graphique, disque, téléchargements ; un seul essai à la fois imposé par un verrou). Version 1.5 : corrections de la relecture indépendante. Version 1.4 : modèle DeepSeek V4.1 Flash, une clé par essai. Ce document fait foi : toute campagne s'y conforme, tout écart est noté au journal.

## 1. Question posée

À modèle identique, un harnais change-t-il la qualité de la solution produite, sa méthode, son coût et sa vitesse ? Et le classement des harnais tient-il quand on change de modèle ?

Un harnais est le programme qui entoure un modèle d'IA et lui donne des outils (lire et écrire des fichiers, lancer des commandes), puis le fait travailler en boucle jusqu'à la fin de la tâche.

## 2. Ce qu'on fait varier

Un seul facteur à la fois, les autres restant fixes.

| Facteur | Valeurs de la campagne 1 | Plus tard |
|---|---|---|
| Harnais | OpenCode, Pi, gptme, Goose, Cline | autres harnais open source |
| Modèle | DeepSeek V4.1 Flash, instantané du 17/10/2026 (`deepseek/deepseek-v4.1-flash-1017`, OpenRouter, fournisseur unique Pearl Research en fp8, sans repli) | 1 ou 2 autres modèles, dont Gemma 4 31B ; modèles locaux sur la RTX 4060 Ti 16 Go |
| Recette | « sans aide » et « avec aide » (section 4) | consignes de méthode, skills, outils (documentation locale par Grounded Docs) |
| Passes | 1, puis 2 si le budget le permet | 3 |

Campagne 1 : 5 harnais × 2 recettes × 1 à 2 passes = 10 à 20 essais.

## 3. La tâche

Construire un workflow qui extrait des valeurs précises de rapports d'intervention en PDF (cahier des charges : [cahier-des-charges-corpus.md](cahier-des-charges-corpus.md)).

| Jeu | Documents | Accès du harnais |
|---|---|---|
| Fourni | 35, avec les réponses attendues | libre : il le découpe lui-même en entraînement et validation |
| Test caché | 15, dont 5 d'un gabarit absent du jeu fourni | seulement par l'API de soumission, **5 soumissions au maximum** |

L'API sert les PDF du test caché, jamais leurs réponses ni leur vérité terrain ; le dossier `test-cache/` n'est jamais monté dans la cage. Le harnais y soumet un JSON par document et reçoit le score global seulement (exactitude par champ).

Le harnais livre :
- un workflow relançable : une commande unique qui prend un dossier de PDF et écrit un JSON par document ;
- ses soumissions à l'API ;
- une déclaration de fin : quelle soumission il retient comme finale, et le score de validation qu'il en attend.

Aucune contrainte de méthode : le harnais choisit ses bibliothèques (installées depuis PyPI), l'usage ou non de la vision du modèle, la découpe, le nombre d'itérations.

## 4. Les recettes

La recette est le message de départ et ce qui l'accompagne. Il est identique pour tous les harnais : « Suis les consignes de `consignes.md`. »

| Recette | Contenu de `consignes.md` |
|---|---|
| Sans aide | la tâche, la liste des clés à extraire avec une définition d'une ligne chacune, le format de sortie, l'API de soumission et sa limite de 5 |
| Avec aide | la même chose, plus l'ontologie : pour chaque clé, définition métier, unité attendue, synonymes, règles (« volume de dose mesuré après réglage, en ml, pas la capacité du réservoir ») |

## 5. Conditions d'exécution

1. **Copie neuve** de l'espace de travail à chaque essai (`banc-essai/recettes/<recette>/` copié dans un dossier vierge).
2. **Cage** : le harnais tourne dans bubblewrap (`banc-essai/cage/`). Écriture seulement dans l'espace de travail, son dossier personnel et `/tmp` (sur le disque) ; le reste de la machine en lecture seule ou invisible ; réseau limité au relais du modèle, à l'API de soumission et à un mandataire de téléchargement (PyPI, Hugging Face, GitHub). Le test caché n'est jamais monté dans la cage.
3. **Modèle** : tous les appels passent par un LiteLLM propre au banc (`banc-essai/traces/`), qui relaie vers OpenRouter. Une clé virtuelle par essai (et une pour la relance du workflow), supprimée à la fin de l'essai. Le prix du fournisseur est déclaré au relais, qui calcule le coût de chaque appel ; le coût facturé par OpenRouter est journalisé à côté. LLM-Service n'est pas utilisé ni modifié.
4. **Mode** : sans interaction (le harnais reçoit le message et travaille seul). Toute intervention humaine est comptée et notée.
5. **Limites** : 5 soumissions ; plafond de 2 $ par clé, donc par essai ; plafond global de 10 $ sur la clé OpenRouter du banc ; garde-fou de 2 heures par essai (le temps est mesuré, pas imposé) ; un seul essai à la fois sur la machine (verrou du lanceur).
6. **Ressources** (annoncées dans les consignes, sans aucune indication d'outil ni de méthode) :

| Ressource | Cadre | Tenue | Mesure |
|---|---|---|---|
| Processeur | tous les cœurs | un seul essai à la fois | |
| Mémoire vive | 16 Go | plafond du noyau (unité systemd de l'utilisateur) : le processus qui dépasse est arrêté, le harnais continue | pic de mémoire, nombre d'arrêts |
| Carte graphique | RTX 4060 Ti, 8 Go annoncés | aucun blocage possible sous WSL | pic de mémoire de la carte pendant l'essai (relevé toutes les 5 s, usage antérieur retranché) |
| Disque | 30 Go (espace de travail, dossier personnel, `/tmp`) | essai arrêté au-delà (relevé toutes les 30 s) | pic d'occupation |
| Téléchargements | 10 Go depuis PyPI, Hugging Face, GitHub | le mandataire coupe au-delà | volume par site, sites refusés |
| Recherche sur Internet | non (campagne 2 : recette « outils ») | tout autre site refusé et journalisé | demandes refusées |

7. **Versions figées** : version du harnais, du modèle et du corpus notées dans le résultat de chaque essai.

## 6. Ce qu'on mesure

Les capacités (ce que le harnais sait faire) et les résultats (ce qu'il a fait) sont présentés dans des tableaux séparés.

**Résultat**

| Mesure | Source |
|---|---|
| Score final : exactitude par champ, sur le test caché, de la soumission déclarée finale | API de soumission |
| Meilleur score obtenu | API de soumission |
| Écart entre le score de validation annoncé et le score de test | déclaration de fin, API |
| Score par champ et par étiquette de difficulté | API de soumission, étiquettes du corpus |
| Score par famille de pièges, par style de mise en page, par nom vu ou inédit | API de soumission, vérité terrain du corpus |
| Taux d'invention : part des réponses non nulles là où `null` est attendu | API de soumission |
| Score sur le style de mise en page jamais vu | API de soumission |

**Construction**

| Mesure | Source |
|---|---|
| Temps total, temps dans le modèle, temps d'attente dû aux quotas (erreurs 429) | journaux LiteLLM |
| Requêtes, jetons d'entrée et de sortie, coût | journaux LiteLLM, OpenRouter |
| Soumissions utilisées | API de soumission |
| Interventions humaines | journal de l'essai |
| Boucles et erreurs d'outils | journaux LiteLLM et du harnais |

**Méthode**

| Mesure | Source |
|---|---|
| Usage de la vision (appels avec image) | journaux LiteLLM |
| Approches essayées (OCR, extraction de texte, règles, appel au modèle par document…) | journaux, code produit |
| Workflow structuré et relançable | relance du workflow sur 10 nouveaux documents |

**Workflow livré**

| Mesure | Source |
|---|---|
| Fonctionne sur de nouveaux documents | relance après l'essai, sans le harnais, dans la cage, sur un lot neuf |
| Temps d'exécution par document | relance |
| Coût d'exécution par document (si le workflow appelle un modèle) | journaux LiteLLM |

**Qualité du code** : grille notée à l'aveugle (le relecteur ne sait pas quel harnais a écrit le code) : lisibilité, structure, tests, gestion des erreurs, relançabilité ; complétée par des outils automatiques (lint, complexité).

## 7. Anti-triche

- Le test caché n'existe pas dans la cage ; seule l'API y donne accès.
- L'API refuse au-delà de 5 soumissions et journalise chacune (heure, statut, score et scores agrégés dans `soumissions.jsonl` ; contenu soumis et détail par document hors git). Une soumission au mauvais format (dont un nombre au-delà de 10⁹ en valeur absolue) est refusée avec le détail des erreurs et ne compte pas ; elle est journalisée. Une erreur interne de l'API est journalisée (`erreurs.jsonl`), répond 500 et ne compte pas. Chaque requête est journalisée (`acces.jsonl`).
- L'API ne renvoie que le score global : ni score par clé, ni détail par document.
- Les PDF du test étant lisibles par le harnais, une réponse saisie à la main par le modèle (lecture directe des 15 documents) reste possible. Le journal des appels ne garde pas le contenu des messages et ne la repère donc pas ; elle se révèle par l'écart entre le score de test et celui de la relance du workflow, et par les transcriptions du harnais quand il en produit (lot 4).
- La cage empêche de lire l'évaluateur, le test caché et les secrets, d'écrire hors de l'espace de travail et de sortir sur le réseau hors des trois accès prévus (preuve : sonde du lot 3, `banc-essai/resultats/preuve-cage-*`). Les demandes réseau refusées sont journalisées ; les accès aux fichiers ne le sont pas.
- Clé de l'essai : limitée aux routes d'appel au modèle (ni transfert direct vers un fournisseur, ni gestion des clés) ; le relais ne connaît la clé OpenRouter que sous un nom propre au banc, inutilisable par ses routes de transfert direct. La clé est supprimée dès la sortie du harnais, avant la relance, qui reçoit une clé neuve.
- Relance : seuls les fichiers ordinaires de la sortie sont lus (un lien symbolique posé par le workflow vers un fichier de l'hôte est ignoré et compté dans `fichiers_refuses`) ; une réponse mal formée compte faux. Sans bubblewrap, la relance et la notation de la tâche jouet refusent de tourner.
- Tâche jouet : les cas cachés (appels et valeurs attendues) ne sont jamais montés dans la cage ; la cage reçoit les appels seuls et renvoie les valeurs obtenues, comparées hors de la cage ; une ligne de résultat en trop annule la soumission. Limite : le code soumis tourne dans le même processus que l'exécutant et peut écrire ses propres valeurs, mais sans connaître les valeurs attendues.
- Sans déclaration de fin (harnais arrêté, garde-fou atteint) : la dernière soumission acceptée tient lieu de soumission finale, le rapport l'indique, et le workflow n'est pas relancé (pas de score de relance).

## 8. Plan des campagnes

1. **Mise au point** : une tâche jouet (corriger un bug, tests cachés) pour valider cage, traces et lancement de chaque harnais.
2. **Campagne 1** : 5 harnais × 2 recettes, DeepSeek V4.1 Flash, 1 passe ; puis 2e passe si le budget le permet.
3. **Campagne 2** : autres recettes (consignes de méthode, skills, outils) sur les 2 meilleurs harnais.
4. **Campagne 3** : autres modèles, dont des modèles locaux, pour vérifier que le classement tient.

## 9. Limites connues

- Modèles gratuits écartés pour la campagne 1 : le 19/11/2026, Gemma 4 31B gratuit sur OpenRouter a renvoyé 429 (« rate-limited upstream ») à 74 appels sur 74 entre 17 h 02 et 21 h 18 ; l'offre gratuite de l'API Google plafonne Gemma 4 31B à 16 000 jetons envoyés par minute, en dessous de la taille d'un appel de harnais.
- Le fournisseur peut garder les requêtes, d'où un corpus entièrement fictif.
- En réponse en flux, le nom du fournisseur n'est pas journalisé (fournisseur unique, sans repli).
- `/tmp` de la cage est sur le disque, dans le dossier de l'essai (`~/banc-espaces/<essai>/tmp`), compté dans les 30 Go.
- La mémoire de la carte graphique n'est pas plafonnable sous WSL : les 8 Go sont une consigne, le pic est mesuré et un dépassement est noté. La mesure est globale à la carte : l'usage antérieur à l'essai est retranché.
- Pic de mémoire vive relevé toutes les 2 s : une exécution plus courte (relance de quelques secondes) peut ne pas être relevée.
- Le plafond de téléchargement vaut pour un passage dans la cage : la relance du workflow a son propre plafond de 10 Go.
- `/proc/self/mountinfo` montre dans la cage les chemins de l'hôte des dossiers montés (espace de travail, dossier du harnais, uv) ; ces chemins ne donnent accès à rien.
- Un LiteLLM arrêté pendant un essai ne laisse aucune ligne au journal : les appels perdus ne sont pas comptés. La dépense relevée sur la clé (`depense_cle_usd`) est comparée au total du journal (`ecart_depense_journal_usd`).
- Le harnais ne peut pas lancer ses propres bacs à sable par espace de noms utilisateur (`--disable-userns`) : un harnais qui en dépend le signalera au lot 4.
- Prix et disponibilité d'un modèle peuvent changer : la date, l'identifiant exact, le fournisseur et le prix sont notés.
- Cline : sa CLI (version 2.0) a un mode sans interaction ; s'il ne peut pas viser le LiteLLM du banc, il appelle OpenRouter directement et ses traces viennent du journal OpenRouter, écart signalé dans les résultats.
