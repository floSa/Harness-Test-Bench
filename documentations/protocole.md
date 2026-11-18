# Protocole du banc des harnais

Version 1, 18 novembre 2026. Ce document fait foi : toute campagne s'y conforme, tout écart est noté au journal.

## 1. Question posée

À modèle identique, un harnais change-t-il la qualité de la solution produite, sa méthode, son coût et sa vitesse ? Et le classement des harnais tient-il quand on change de modèle ?

Un harnais est le programme qui entoure un modèle d'IA et lui donne des outils (lire et écrire des fichiers, lancer des commandes), puis le fait travailler en boucle jusqu'à la fin de la tâche.

## 2. Ce qu'on fait varier

Un seul facteur à la fois, les autres restant fixes.

| Facteur | Valeurs de la campagne 1 | Plus tard |
|---|---|---|
| Harnais | OpenCode, Pi, gptme, Goose, Cline | autres harnais open source |
| Modèle | Gemma 4 31B (`google/gemma-4-31b-it:free`, OpenRouter) | 1 ou 2 autres modèles ; modèles locaux sur la RTX 4060 Ti 16 Go |
| Recette | « sans aide » et « avec aide » (section 4) | consignes de méthode, skills, outils (documentation locale par Grounded Docs) |
| Passes | 1, puis 2 si le budget le permet | 3 |

Campagne 1 : 5 harnais × 2 recettes × 1 à 2 passes = 10 à 20 essais.

## 3. La tâche

Construire un workflow qui extrait des valeurs précises de rapports d'intervention en PDF (cahier des charges : [cahier-des-charges-corpus.md](cahier-des-charges-corpus.md)).

| Jeu | Documents | Accès du harnais |
|---|---|---|
| Fourni | 35, avec les réponses attendues | libre : il le découpe lui-même en entraînement et validation |
| Test caché | 15, dont 5 d'un gabarit absent du jeu fourni | seulement par l'API de soumission, **5 soumissions au maximum** |

Le harnais livre :
- un workflow relançable : une commande unique qui prend un dossier de PDF et écrit un JSON par document ;
- ses soumissions à l'API ;
- une déclaration de fin : quelle soumission il retient comme finale, et le score de validation qu'il en attend.

Aucune contrainte de méthode : le harnais choisit ses bibliothèques (installées depuis PyPI), l'usage ou non de la vision du modèle, la découpe, le nombre d'itérations.

## 4. Les recettes

La recette est le message de départ et ce qui l'accompagne. Il est identique pour tous les harnais : « Suis les consignes de `consignes.md`. »

| Recette | Contenu de `consignes.md` |
|---|---|
| Sans aide | la tâche, la liste des clés à extraire, le format de sortie, l'API de soumission et sa limite de 5 |
| Avec aide | la même chose, plus l'ontologie : pour chaque clé, définition métier, unité attendue, synonymes, règles (« volume de dose mesuré après réglage, en ml, pas la capacité du réservoir ») |

## 5. Conditions d'exécution

1. **Copie neuve** de l'espace de travail à chaque essai (`banc-essai/recettes/<recette>/` copié dans un dossier vierge).
2. **Cage** : le harnais tourne dans bubblewrap (`banc-essai/cage/`). Écriture seulement dans l'espace de travail ; le reste de la machine en lecture seule ou invisible ; réseau limité au proxy de modèles, à l'API de soumission et à PyPI. Le test caché n'est jamais monté dans la cage.
3. **Modèle** : tous les appels passent par un LiteLLM propre au banc (`banc-essai/traces/`), qui relaie vers OpenRouter. Une clé par harnais. LLM-Service n'est pas utilisé ni modifié.
4. **Mode** : sans interaction (le harnais reçoit le message et travaille seul). Toute intervention humaine est comptée et notée.
5. **Limites** : 5 soumissions ; plafond de 2 $ par clé ; garde-fou de 2 heures par essai (le temps est mesuré, pas imposé).
6. **Versions figées** : version du harnais, du modèle et du corpus notées dans le résultat de chaque essai.

## 6. Ce qu'on mesure

Les capacités (ce que le harnais sait faire) et les résultats (ce qu'il a fait) sont présentés dans des tableaux séparés.

**Résultat**

| Mesure | Source |
|---|---|
| Score final : exactitude par champ, sur le test caché, de la soumission déclarée finale | API de soumission |
| Meilleur score obtenu | API de soumission |
| Écart entre le score de validation annoncé et le score de test | déclaration de fin, API |
| Score par champ et par étiquette de difficulté | API de soumission, étiquettes du corpus |
| Score sur le gabarit jamais vu | API de soumission |

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
| Fonctionne sur de nouveaux documents | relance hors cage, sur un lot neuf |
| Temps d'exécution par document | relance |
| Coût d'exécution par document (si le workflow appelle un modèle) | journaux LiteLLM |

**Qualité du code** : grille notée à l'aveugle (le relecteur ne sait pas quel harnais a écrit le code) : lisibilité, structure, tests, gestion des erreurs, relançabilité ; complétée par des outils automatiques (lint, complexité).

## 7. Anti-triche

- Le test caché n'existe pas dans la cage ; seule l'API y donne accès.
- L'API refuse au-delà de 5 soumissions et journalise chacune (heure, contenu, score).
- Toute tentative de lire l'évaluateur, de sortir de la cage ou de contourner la limite est relevée dans les journaux et notée.

## 8. Plan des campagnes

1. **Mise au point** : une tâche jouet (corriger un bug, tests cachés) pour valider cage, traces et lancement de chaque harnais.
2. **Campagne 1** : 5 harnais × 2 recettes, Gemma 4 31B, 1 passe ; puis 2e passe si le budget le permet.
3. **Campagne 2** : autres recettes (consignes de méthode, skills, outils) sur les 2 meilleurs harnais.
4. **Campagne 3** : autres modèles, dont des modèles locaux, pour vérifier que le classement tient.

## 9. Limites connues

- Modèles gratuits : 20 requêtes par minute, 1 000 par jour ; le fournisseur peut garder les requêtes, d'où un corpus entièrement fictif.
- La gratuité d'un modèle peut disparaître : la date et l'identifiant exact sont notés.
- Cline : sa CLI (version 2.0) a un mode sans interaction ; s'il ne peut pas viser le LiteLLM du banc, il appelle OpenRouter directement et ses traces viennent du journal OpenRouter, écart signalé dans les résultats.
