# État du travail — extraction de rapports d'intervention

## Objectif
Livrer une commande unique `<commande> {entree} {sortie}` qui lit des PDF de rapports
d'intervention et écrit un JSON par document avec 15 clés. Score visé sur test caché.

## RÉSULTAT FINAL : TERMINÉ
- **Soumission 1 : score 1.0 sur le test caché (15 docs).**
- Fin déclarée : `python3 soumettre.py fin --soumission 1 --score-validation 1.0 --commande "./run.sh {entree} {sortie}"` → `{"enregistree": true}`.
- Commande finale : `./run.sh {entree} {sortie}` (depuis /travail).
- Vérifié : 15 JSON, 15 clés chacun, chemins absolus OK.

## Décisions / approche
- PDF textuels (pymupdf) MAIS certaines valeurs sont dans des IMAGES (volume nominal sur
  schéma, date de validation sur tampon, pression, logo constructeur, nom du technicien
  sur visa, pages scannées pleine page).
- Modèle `deepseek-v4.1-flash` multimodal : 1 appel par document = texte extrait (avec
  indices de cases cochées) + pages rendues à 150 dpi + images embarquées natives
  (upscalées x2 si < 600 px).
- max_tokens=12000, temperature=0 (variance réduite).
- Retry x5 avec backoff (2,4,6,8 s) si réponse vide/illisible.
- Workflow : 6 threads max (8 causait des réponses vides transitoires, cf. doc-019).
- Fichiers : `extract.py`, `eval.py`, `workflow.py`, `run.sh`, `ocr.py`, `ocr_doc.py`.
- Venv : `.venv` avec pymupdf.

## Résultats
- Baseline : 493/525 = 0.939.
- Prompt v3 (règles 1-9) + temp=0 : **525/525 = 1.0** sur les 35 docs fournis (55 s, 6 threads).
- Test caché : **1.0** (soumission 1).

## Règles du prompt (extract.py SYSTEM)
1. tolerance_ml : uniquement champ explicite Tolérance/EMT/MPE/écart toléré ; PAS
   l'incertitude élargie (doc-001, doc-015 → null).
2. debit_ml_min : si après réglage "—", prendre la prose ("L'équipement débite alors X").
3. pression_bar : si "—", prendre la prose ; unités bar/kPa/psi/mbar ; si pas de note
   d'unités, choisir l'unité plausible vs pression max admissible (doc-022 27.56 psi→1.9002 ;
   doc-034 63.82 psi→4.4002 ; doc-042 400 mbar→0.4 ; doc-012 200 kPa→2.0 ; doc-032 145.04 psi→10.0002).
4. site : désignation COMPLÈTE avec préfixe ("Établissement d'Issoire", "Site d'Issoire",
   "Plateforme d'Oyonnax", "Usine de Guingamp", "Dundee Facility") ; si champ "—"/"n.c."
   chercher la prose ("Le déplacement chez le client, X" / "The visit to the customer, X").
5. technicien : champ explicite (Technicien/Technician/Technicien responsable/Responsible
   technician/Lead technician/Chargé d'intervention/Intervenant principal), ou "(responsable)"
   dans INTERVENANTS, ou la personne qui "a conduit l'intervention"/"led the visit" ;
   JAMAIS un participant ("a participé"/"took part"), un accompagnant, le demandeur,
   "Approbation client"/"Checked by"/"Requested by"/"Prepared by".
6. reference_rapport : retirer suffixe "Rev. B"/"Indice B"/"Revision B".
7. tolerance en % : si colonne "—" mais prose "deviation allowed ... ± X %" →
   X % × volume_nominal_ml (doc-007 2.5%×1000=25 ; doc-021 8%×1=0.08 ; doc-037 2.5%×250=6.25).
8. Ne jamais utiliser l'"avant réglage"/"as found" pour volume_dose/debit/pression ;
   si après réglage manque et pas de prose → null (doc-030 pression → null).
9. "ANNULE ET REMPLACE X"/"Supersedes : X" = ancienne référence, ne pas l'utiliser ;
   prendre le champ "Référence du rapport/Report reference/Report no." ; si absent,
   chercher "Pour mémoire, N° de compte rendu : Y" (doc-055 → 5237, pas 4888).

## Contraintes
- 5 soumissions max (1 utilisée). Clé modèle en env (BANC_CLE_MODELE), jamais écrite.
- La commande finale tourne depuis /travail, sans fichiers hors dossier (sauf paquets).
