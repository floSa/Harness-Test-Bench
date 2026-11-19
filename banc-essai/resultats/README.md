# Résultats des essais

Un dossier par essai. Dans chaque dossier : `rapport.md` (synthèse lisible), `essai.json` (mesures de construction : durée, appels, jetons, coût, ressources), `harnais/stdout.log` (trace de la session), `traces/` (appels au modèle, réseau), `evaluation/` (soumissions), `relance/` (workflow relancé). Explication du banc : [protocole expliqué](../../documentations/protocole-explique.md).

Page régénérée à la fin de chaque essai (`banc-essai/evaluation/index_resultats.py`).

| Essai | Nature | Début | Harnais | Recette | Score final | Score de relance | Durée | Appels au modèle | Coût |
|---|---|---|---|---|---|---|---|---|---|
| [jouet-factice](jouet-factice/rapport.md) | essai factice (fausses solutions) |  |  |  | 70,0 % |  |  |  |  |
| [essai-factice](essai-factice/rapport.md) | essai factice (fausses solutions) |  |  |  | 12,4 % | 11,3 % |  |  |  |
| [preuve-cage](preuve-cage/rapport.md) | preuve de la cage (sonde) | 2026-11-19 17:02 | sonde | jouet |  |  | 3 s | 2 |  |
| [preuve-cage-deepseek](preuve-cage-deepseek/rapport.md) | preuve de la cage (sonde) | 2026-11-19 21:33 | sonde | jouet |  |  | 5 s | 2 | 0,0000 $ |
| [preuve-cage-correctifs](preuve-cage-correctifs/rapport.md) | preuve de la cage (sonde) | 2026-11-19 21:58 | sonde | jouet |  |  | 5 s | 2 | 0,0001 $ |
| [verif-lanceur-extraction](verif-lanceur-extraction/rapport.md) | vérification du lanceur (faux harnais) | 2026-11-19 22:01 | factice | sans-aide | 12,4 % | 11,3 % | 5 s | 3 | 0,0000 $ |
| [opencode-jouet-1](opencode-jouet-1/rapport.md) | tâche jouet (mise au point) | 2026-11-19 22:11 | opencode | jouet | 100,0 % |  | 22 s | 11 | 0,0012 $ |
| [opencode-jouet-2](opencode-jouet-2/rapport.md) | tâche jouet (mise au point) | 2026-11-19 22:32 | opencode | jouet | 100,0 % |  | 20 s | 11 | 0,0013 $ |
| [preuve-cage-cadre](preuve-cage-cadre/rapport.md) | preuve de la cage (sonde) | 2026-11-19 22:41 | sonde | jouet |  |  | 6 s | 2 | 0,0000 $ |
| [verif-lanceur-cadre](verif-lanceur-cadre/rapport.md) | vérification du lanceur (faux harnais) | 2026-11-19 22:42 | factice | sans-aide | 12,4 % | 11,3 % | 3 s | 3 | 0,0000 $ |
| [opencode-jouet-3](opencode-jouet-3/rapport.md) | tâche jouet (mise au point) | 2026-11-19 22:42 | opencode | jouet | 100,0 % |  | 30 s | 12 | 0,0013 $ |

Score final : part des champs justes sur le test caché (tâche jouet : part des cas cachés réussis). Score de relance : même mesure, workflow relancé sans le harnais sur 10 documents neufs.
