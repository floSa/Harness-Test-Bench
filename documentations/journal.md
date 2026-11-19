# Journal

### 2026-11-18 — Cadrage

- Protocole (`protocole.md`) et cahier des charges du corpus (`cahier-des-charges-corpus.md`) écrits, version 1.
- Choix : 5 harnais open source (OpenCode, Pi, gptme, Goose, Cline) ; modèle `google/gemma-4-31b-it:free` via OpenRouter ; recettes « sans aide » et « avec aide » ; tâche d'extraction dans 50 rapports d'intervention fictifs (35 fournis, 15 en test caché, 5 soumissions) ; cage bubblewrap ; traces par un LiteLLM propre au banc.
- Kit local (hors git) : mission commune, 6 lots, fiches des harnais, prompts de lancement.
- Vérifié par recherche : modes sans interaction annoncés pour OpenCode (`opencode run`), Goose (`goose run`), Cline CLI (`cline -y`) ; à vérifier pour Pi et gptme. Gemma 4 31B accepte les images (API OpenRouter, 18/11/2026).
- Bubblewrap 0.9.0 installé par l'utilisateur ; essai : dans la cage, écriture refusée hors des dossiers autorisés et réseau coupé.
- Choix : un seul dépôt pour les 5 harnais (banc commun, comparaison au même endroit), un manuel de prise en main par harnais avec captures dans `documentations/manuels/<harnais>/`.
- Kit relu : tâche jouet et `consignes.md` des recettes confiés au lot 2.
- Reste à faire : lots 1 à 6.

### 2026-11-19 — Lot 1 (Corpus) : générateur et 3 documents d'exemple

- Environnement `banc-essai/corpus/` (uv, Python 3.12) : reportlab 5.1.0, PyMuPDF 2.1, Pillow 13.0.0, numpy 2.5.5, figés dans `uv.lock`.
- Entités fictives : constructeurs Vexilor (doseuses à piston), Pumanis (pompes doseuses), Corvalis (remplisseuses), Mikropal (pipettes automatiques) ; prestataires Techmaint Loire (gabarit 1), Calibro Services Ltd (2), Atelier Bréval Maintenance (3), Tessaly Field Services (4). Recherche web du jour : aucune entreprise trouvée sous ces noms.
- Générateur : `entites.py`, `modele.py` (tirage des réponses, répartition exacte des pièges), `dessins.py` (logos, schéma, signature, page scannée tramés en image), `rendu.py` (gabarits 1 à 3), `generer.py`, `controler.py`. Gabarit 4 : à écrire après validation.
- Règles de calcul des parts écrites au cahier des charges, section 11.
- 3 exemples (`banc-essai/corpus/exemples/`) : gabarit 1 (deux logos, page de mesures scannée), gabarit 2 (constructeur en logo seul, correction du débit, volume nominal en L), gabarit 3 (tableau coupé, deux logos, page scannée).
- Vérifié : contrôle automatique sans erreur sur les 3 exemples (valeurs écrites présentes dans la couche texte de leur page, valeurs en image absentes du texte, page scannée sans texte) ; deux générations successives donnent les mêmes empreintes SHA-256.
- Point pour le lot 3 : le générateur et sa graine sont dans le dépôt, donc le test caché se reconstruit à partir du dépôt ; la cage ne doit exposer que l'espace de travail.
- Reste à faire : validation des exemples par l'utilisateur, gabarit 4, génération des 50, contrôle des proportions, relecture de 5 réponses, ontologie, empreintes.
