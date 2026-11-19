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

### 2026-11-19 — Lot 1 (Corpus) : cahier des charges v2 et 2 exemples du style « grille »

- Retour de l'utilisateur sur les exemples v1 : 15 champs, prestataires et marques nombreux et inventés, rôles croisés entre noms (généralisation), page d'entrée en grille de cases, absence de valeur avec voisins tentants, plusieurs dates et signatures, valeurs répétées dont une fait foi, formats de nombres, unités et dates variés, vérité terrain annotée ; 3 à 4 façons de présenter ; au moins 50 documents.
- Cahier des charges réécrit en version 2 (proposition à valider) : 60 documents (35 fournis, 15 test, 10 relance), 15 champs, familles de pièges et parts visées, vérité terrain et PDF annoté, taux d'invention.
- Générateur v2 : `univers.py` (noms générés, rôles croisés), `donnees.py` (15 champs, leurres), `formats.py` (nombres, unités, dates ; psi = 0,06894757 bar d'après NIST SP 811 via NISTunits), `mise_en_page.py`, `style_grille.py`, `verite.py`, `generer.py`. Version 1 rangée dans `banc-essai/corpus/v1/`.
- 2 exemples dans `banc-essai/corpus/exemples/` (PDF, `verite/`, `reponses/`, `annotations/`) : exemple 1 en français (remplisseuse à 3 têtes, moyenne à calculer, dose en L, débit en ml/s, tolérance en %, pression seulement dans le schéma, n° de série absent, constructeur en logo seul, date de validation seulement dans le tampon, version remplacée, date d'intervention seulement dans le récit) ; exemple 2 en anglais (dose barrée et corrigée à la main en µL, synthèse provisoire contredite par le tableau, pression en psi, site et pièce absents, rédacteur différent du technicien, page scannée, dates américaines, machine nommée d'après le constructeur de l'exemple 1).
- Vérifié : toutes les écritures en texte sont retrouvées dans les PDF à leur cadre ; deux générations donnent les mêmes empreintes (PDF et vérité) ; relecture visuelle des pages.
- Reste à faire : validation de la v2, styles classique, compact anglais, texte abondant (portage v1) et style réservé, tirage des pièges en proportions, étiquette nom vu ou inédit, `verite.csv`, contrôle automatique v2, génération des 60, relecture de 5 vérités, ontologie, empreintes.

### 2026-11-19 — Lot 1 (Corpus) : plan du corpus et rapport d'équilibre

- Retour de l'utilisateur : style grille validé ; 4 à 5 mises en page, modifiables ; 3 à 6 pages ; ajouter du texte de remplissage où la valeur est noyée sans libellé (le titre évoque la clé) ; disséminer les valeurs entre page d'entrée, tableaux, schémas et paragraphes ; tirer un plan de répartition avant la génération pour équilibrer pièges et emplacements.
- `plan.py` : composition (60 documents, 5 styles dont un réservé au test et à la relance, types d'équipement à parts égales), emplacements par champ (formulaire, tableau, phrase, paragraphe, schéma, logo, plaque, tampon, calcul, absent) en nombres exacts par jeu, pièges de document et de valeur, équilibrage de la charge des documents et des styles. Rapport `banc-essai/corpus/plan-equilibre.md` (agrégats seulement).
- Vérifié : contrôle du plan sans écart (effectifs par jeu, au plus 2 difficultés par valeur, aucun piège sur un champ absent) ; charge par document de 11,5 à 18,5 (moyenne 14,4 à 14,6 selon le jeu) ; plan et rapport identiques sur deux exécutions ; PDF annotés désormais reproductibles (identifiant de fichier figé).
- Cahier des charges v2 complété (section 11, 3 à 6 pages).
- Reste à faire : brancher le générateur sur le plan ; emplacements paragraphe et plaque, texte de remplissage ; styles classique, compact, récit, réservé ; contrôle automatique v2 ; génération des 60 ; relecture de 5 vérités ; ontologie ; empreintes.

### 2026-11-19 — Lot 1 (Corpus) : générateur branché sur le plan, 5 styles

- Générateur v2 branché sur le plan : `donnees.py` prend l'emplacement de chaque valeur dans le plan ; `base.py` écrit chaque champ à chacun de ses emplacements (formulaire, tableau, phrase, paragraphe sans libellé, schéma, logo, plaque, tampon, calcul, absent) ; `textes.py` : 37 phrases de remplissage par langue, titres de sections qui évoquent les clés, statut exprimé par une phrase (« peut être remis en production sans réserve »).
- Styles : grille (`style_grille.py`, placement à la main), classique, compact, récit, réservé (`style_*.py`, mise en page en flux sur `base_flux.py` et `flux.py` : pagination automatique, position de chaque valeur notée au dessin, tableau coupé entre deux pages détecté et étiqueté, page scannée remplacée après coup).
- Exemples : un document par style (`banc-essai/corpus/exemples/exemple-<style>`), tirés d'un plan à graine séparée : aucun document du corpus n'y figure.
- Vérifié : essai de rendu sur 180 documents planifiés (4 graines) sans erreur, toutes les écritures en texte retrouvées dans les PDF, chaque valeur non nulle écrite au moins une fois, aucune valeur absente écrite ; pages : grille 5, classique 3, compact 3, récit 4 à 5, réservé 3 à 4 ; exemples identiques à l'octet sur deux générations.
- Défauts trouvés à la relecture et corrigés : moyennes d'essais non arrondies, tolérance répétée dans deux tableaux, tolérance écrite sans unité sur la ligne de la dose (lue dans l'unité de la dose), style réservé à 2 pages, cadre d'annotation trop étroit pour les dates longues.
- Reste à faire : validation des styles ; contrôle automatique v2 et `verite.csv` ; génération des 60 ; relecture de 5 vérités ; ontologie ; empreintes ; recherche web sur un échantillon de noms générés.

### 2026-11-19 — Lot 1 (Corpus) : génération des 60 documents, relecture, ontologie

- Génération : 60 documents (35 fournis versionnés ; 15 test caché et 10 relance hors git), réponses, vérité, annotations, `verite.csv` par jeu ; `empreintes.sha256` (243 fichiers).
- Contrôle automatique (`controler.py`, relit les PDF) : 3 à 6 pages, réponses égales à la vérité, emplacements conformes au plan, chaque écriture en texte retrouvée à son cadre, valeurs prévues en image jamais écrites en texte, valeurs absentes jamais écrites, page scannée sans texte, parts visées du plan retrouvées par jeu. Résultat : 0 erreur ; 1 alerte acceptée (valeur prévue en image qui coïncide avec un leurre écrit).
- Reproductibilité : deux générations complètes, empreintes identiques.
- Relecture indépendante de 5 documents fournis tirés au sort (graine « relecture-20261119 » : doc-047, doc-007, doc-015, doc-009, doc-058) par deux sous-agents qui extraient les 15 champs avant de lire la vérité : 73 champs sur 75 identiques ; 1 vérité non décidable (pièce citée sans dire qu'elle est remplacée), 1 écart de forme (« Site de Oyonnax »). Défauts corrigés : phrase de la pièce (« de la pièce remplacée »), mesures en phrase qualifiées « après réglage », essais après réglage retirés du tableau quand la dose est écrite ailleurs, essais tous distincts, dose d'arrivée égale à la moyenne des essais avant réglage, élision des noms de site, numéro de version annulée inférieur au numéro en vigueur, note d'unités limitée au tableau, rédacteur affiché dans tous les styles, ponctuation anglaise, en-têtes et dates qui passent à la ligne, titres solidaires de leur tableau. Contrôles ciblés de ces défauts : 0 sur 3 graines.
- Ontologie : `banc-essai/recettes/avec-aide/ontologie.md`, générée depuis les libellés et règles du générateur.
- Noms : recherche web groupée sur les 18 marques et prestataires du jeu fourni, aucune correspondance exacte (seulement des noms voisins).
- Reste à faire : lot 2 (API d'évaluation, recettes, tâche jouet) ; ajouter le taux d'invention et le score par famille de pièges au protocole ; noter que la recette « sans aide » doit donner une définition d'une ligne par clé.
- Contre-relecture après corrections (doc-001 compact, doc-020 grille, graine « contre-relecture-20261119») : 29 champs sur 30 identiques ; 1 vérité non décidable (pression écrite seulement dans le schéma, égale à la valeur avant réglage, case après réglage vide). Corrigé : valeurs avant réglage toujours distinctes des valeurs après (débit, pression), cotes du schéma qualifiées « après réglage », débit minimal des pipettes porté à 5 ml/min, noms de famille distincts entre les 5 personnes d'un document. Contrôles ciblés : 0 défaut sur 4 graines ; contrôle automatique : 0 erreur ; empreintes identiques sur deux générations.

### 2026-11-19 — Lot 2 (Évaluation) : API de soumission, notation, recettes, tâche jouet

- `banc-essai/evaluation/` (uv, Python 3.12 ; serveur et client en bibliothèque standard, pytest 9.2.0 pour les tests) : `notation.py` (format, comparaison, scores par clé, étiquette, famille de pièges, emplacement, style, prestataire, langue, nom vu ou inédit, taux d'invention), `api.py` (127.0.0.1, port 8765 par défaut), `client/soumettre.py`, `preparer.py`, `relancer.py`, `rapport.py`, `jouet.py`, `essai_factice.py`, `README.md`.
- Choix de fonctionnement, notés au protocole (version 1.2) : l'API sert les PDF du test caché sans réponses ni vérité et renvoie le score global seulement ; une soumission mal formée est refusée avec le détail et ne compte pas ; l'état de l'API est relu depuis ses journaux à chaque démarrage ; un document sans réponse compte faux pour ses 15 champs ; le détail par document (`detail-cache.jsonl`) reste hors git.
- Recettes : `sans-aide/consignes.md` (tâche, 15 clés avec une définition d'une ligne, format, workflow `{entree} {sortie}`, API et limite de 5, déclaration de fin) ; `avec-aide/consignes.md` (même texte et renvoi à `ontologie.md`). L'espace préparé contient `fourni/` (35 PDF et réponses), sans vérité ni annotations.
- Tâche jouet (`banc-essai/recettes/jouet/`) : paquet `dosage`, bug signalé (microlitres convertis à l'envers), 5 tests visibles ; 10 tests cachés dans `banc-essai/evaluation/taches/jouet/` ; seuls les `.py` du paquet sont acceptés (pas de conftest ni de configuration pytest).
- Vérifié : 21 tests automatiques réussis (documents servis sans réponses, 10 refus de format non décomptés, score exact sur réponses connues avec erreurs placées, tolérance de 0,01, casse et espaces, taux d'invention, limite de 5 et refus au-delà, persistance après redémarrage, déclaration de fin, tâche jouet : solution juste 100 %, correction trop ciblée 70 %, code d'origine 60 %, fichiers de configuration refusés).
- Essai complet avec fausse solution (`essai_factice.py`, résultats dans `banc-essai/resultats/essai-factice/` et `jouet-factice/`) : API lancée en processus, 15 PDF du test caché téléchargés par le client, une soumission mal formée refusée, 5 acceptées, la sixième refusée, fin déclarée, relance sur les 10 documents du jeu « relance », rapports JSON et Markdown. Scores recalculés à part depuis les réponses : 12,44 % sur le test, 11,33 % sur la relance, identiques à ceux de l'API.
- Point pour le lot 3 : la relance du workflow et les tests cachés de la tâche jouet exécutent du code écrit par le harnais hors cage (sous-processus avec délai) ; à faire passer dans la cage.
- Reste à faire : lot 3 (cage et traces), puis lot 4 (harnais) qui s'appuie sur la tâche jouet.
