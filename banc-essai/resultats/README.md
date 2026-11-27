# Résultats des essais

Un dossier par essai. Dans chaque dossier : `rapport.md` (synthèse lisible), `essai.json` (mesures de construction : durée, appels, jetons, coût, ressources), `harnais/stdout.log` (trace de la session), `traces/` (appels au modèle, réseau), `evaluation/` (soumissions), `relance/` (workflow relancé). Explication du banc : [protocole expliqué](../../documentations/protocole-explique.md).

Page régénérée à la fin de chaque essai (`banc-essai/evaluation/index_resultats.py`).

| Essai | Nature | Début | Harnais | Recette | Score final | Score de relance | Durée | Appels au modèle | Coût |
|---|---|---|---|---|---|---|---|---|---|
| [jouet-factice](jouet-factice/rapport.md) | essai factice (fausses solutions) |  |  |  | 70,0 % |  |  |  |  |
| [essai-factice](essai-factice/rapport.md) | essai factice (fausses solutions) |  |  |  | 12,4 % | 11,3 % |  |  |  |
| [captures](captures/rapport.md) | essai de campagne |  |  |  |  |  |  |  |  |
| [manuel-opencode-jouet](manuel-opencode-jouet/rapport.md) | essai de campagne |  |  |  |  |  |  |  |  |
| [preuve-cage](preuve-cage/rapport.md) | preuve de la cage (sonde) | 2026-11-19 17:02 | sonde | jouet |  |  | 3 s | 2 |  |
| [preuve-cage-deepseek](preuve-cage-deepseek/rapport.md) | preuve de la cage (sonde) | 2026-11-19 21:33 | sonde | jouet |  |  | 5 s | 2 | 0,0000 $ |
| [preuve-cage-correctifs](preuve-cage-correctifs/rapport.md) | preuve de la cage (sonde) | 2026-11-19 21:58 | sonde | jouet |  |  | 5 s | 2 | 0,0001 $ |
| [verif-lanceur-extraction](verif-lanceur-extraction/rapport.md) | vérification du lanceur (faux harnais) | 2026-11-19 22:01 | factice | sans-aide | 12,4 % | 11,3 % | 5 s | 3 | 0,0000 $ |
| [opencode-jouet-1](opencode-jouet-1/rapport.md) | tâche jouet (mise au point) | 2026-11-19 22:11 | opencode | jouet | 100,0 % |  | 22 s | 11 | 0,0012 $ |
| [opencode-jouet-2](opencode-jouet-2/rapport.md) | tâche jouet (mise au point) | 2026-11-19 22:32 | opencode | jouet | 100,0 % |  | 20 s | 11 | 0,0013 $ |
| [preuve-cage-cadre](preuve-cage-cadre/rapport.md) | preuve de la cage (sonde) | 2026-11-19 22:41 | sonde | jouet |  |  | 6 s | 2 | 0,0000 $ |
| [verif-lanceur-cadre](verif-lanceur-cadre/rapport.md) | vérification du lanceur (faux harnais) | 2026-11-19 22:42 | factice | sans-aide | 12,4 % | 11,3 % | 3 s | 3 | 0,0000 $ |
| [opencode-jouet-3](opencode-jouet-3/rapport.md) | tâche jouet (mise au point) | 2026-11-19 22:42 | opencode | jouet | 100,0 % |  | 30 s | 12 | 0,0013 $ |
| [goose-jouet-1](goose-jouet-1/rapport.md) | tâche jouet (mise au point) | 2026-11-19 23:00 | goose | jouet | 100,0 % |  | 22 s | 8 | 0,0014 $ |
| [gptme-jouet-1](gptme-jouet-1/rapport.md) | tâche jouet (mise au point) | 2026-11-19 23:03 | gptme | jouet | 100,0 % |  | 48 s | 15 | 0,0022 $ |
| [pi-jouet-1](pi-jouet-1/rapport.md) | tâche jouet (mise au point) | 2026-11-19 23:07 | pi | jouet | 100,0 % |  | 23 s | 11 | 0,0013 $ |
| [cline-jouet-1](cline-jouet-1/rapport.md) | tâche jouet (mise au point) | 2026-11-19 23:09 | cline | jouet | 100,0 % |  | 29 s | 8 | 0,0016 $ |
| [c1-01-opencode-sans-aide](c1-01-opencode-sans-aide/rapport.md) | essai de campagne | 2026-11-19 23:33 | opencode | sans-aide | 100,0 % | 99,3 % | 1446 s | 286 | 0,3102 $ |
| [c1-02-goose-avec-aide](c1-02-goose-avec-aide/rapport.md) | essai de campagne | 2026-11-19 23:59 | goose | avec-aide | 99,6 % | 98,7 % | 1772 s | 299 | 0,3065 $ |
| [c1-03-gptme-sans-aide](c1-03-gptme-sans-aide/rapport.md) | essai de campagne | 2026-11-20 00:33 | gptme | sans-aide | 100,0 % | 99,3 % | 2111 s | 588 | 0,2987 $ |
| [c1-04-pi-avec-aide](c1-04-pi-avec-aide/rapport.md) | essai de campagne | 2026-11-20 01:10 | pi | avec-aide | 100,0 % | 99,3 % | 1615 s | 365 | 0,2738 $ |
| [c2-01-opencode-dossiers](c2-01-opencode-dossiers/rapport.md) | essai de campagne | 2026-11-24 06:18 | opencode | dossiers | 99,4 % | 99,4 % | 3721 s | 691 | 0,8676 $ |
| [piag-sonde-portail](piag-sonde-portail/rapport.md) | tâche jouet (mise au point) | 2026-11-27 09:40 | sonde | jouet |  |  | 6 s | 2 | 0,0000 $ |

Score final : part des champs justes sur le test caché (tâche jouet : part des cas cachés réussis). Score de relance : même mesure, workflow relancé sans le harnais sur le jeu de relance (documents neufs).
