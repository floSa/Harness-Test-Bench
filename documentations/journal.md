# Journal

### 2026-11-18 — Cadrage

- Protocole (`protocole.md`) et cahier des charges du corpus (`cahier-des-charges-corpus.md`) écrits, version 1.
- Choix : 5 harnais open source (OpenCode, Pi, gptme, Goose, Cline) ; modèle `google/gemma-4-31b-it:free` via OpenRouter ; recettes « sans aide » et « avec aide » ; tâche d'extraction dans 50 rapports d'intervention fictifs (35 fournis, 15 en test caché, 5 soumissions) ; cage bubblewrap ; traces par un LiteLLM propre au banc.
- Kit local (hors git) : mission commune, 6 lots, fiches des harnais, prompts de lancement.
- Vérifié par recherche : modes sans interaction annoncés pour OpenCode (`opencode run`), Goose (`goose run`), Cline CLI (`cline -y`) ; à vérifier pour Pi et gptme. Gemma 4 31B accepte les images (API OpenRouter, 18/11/2026).
- Bubblewrap 0.9.0 installé par l'utilisateur ; essai : dans la cage, écriture refusée hors des dossiers autorisés et réseau coupé.
- Choix : un seul dépôt pour les 5 harnais (banc commun, comparaison au même endroit), un manuel de prise en main par harnais avec captures dans `documentations/manuels/<harnais>/`.
- Reste à faire : lots 1 à 6.
