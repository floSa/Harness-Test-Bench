import os,json,base64,sys,urllib.request,pymupdf,re,time

PROMPT = r"""Tu es un expert en extraction de données de dossiers d'intervention sur des équipements de dosage industriels (doseuse, pompe doseuse, remplisseuse, pipette automatique). On te fournit UN document (plusieurs pages) sous forme de texte extrait ET d'images de chaque page. Le texte peut être incomplet ou absent (page scannée) ; les images peuvent contenir des tableaux, des annotations de schéma, des tampons et des cases à cocher.

Analyse l'ENSEMBLE du document (texte + images) et renvoie UNIQUEMENT un objet JSON valide, sans texte autour, sans balises Markdown.

Détermine d'abord le type de document :
- "report" : rapport d'intervention / service report / compte rendu d'intervention.
- "rectification" : rectificatif / erratum / courrier corrigeant une valeur d'un rapport.
- "cancellation" : avis d'annulation d'un rapport.
- "other" : tout autre courrier.

Schéma de sortie :
{
  "type": "report" | "rectification" | "cancellation" | "other",
  "report_reference": "référence du rapport de CE document, ou null",
  "supersedes": ["références que ce rapport annule et remplace", ...],
  "cancels": ["références annulées par ce courrier", ...],
  "rectifies": "référence du rapport visé par le rectificatif, ou null",
  "corrections": [{"field": "clé parmi les 11 champs d'intervention", "value_normalized": valeur corrigée déjà convertie dans l'unité de la clé, "raw": "texte exact de la correction"}],
  "equipment": {"machine": null, "constructeur": null, "numero_serie": null, "site": null},
  "intervention": {
    "reference_rapport": null,
    "date_intervention": null,
    "date_validation": null,
    "volume_dose_ml": null,
    "volume_nominal_ml": null,
    "tolerance_ml": null,
    "debit_ml_min": null,
    "pression_bar": null,
    "reference_piece": null,
    "technicien": null,
    "statut": null
  }
}

Règles d'extraction (très importantes) :
1. Dates au format AAAA-MM-JJ. date_intervention = date réelle de l'intervention (pas la date de demande, d'émission, d'impression ni de prochaine visite). date_validation = date de l'approbation FINALE du rapport (champ "Validation date"/"Date de validation", "Approved ... on"/"Approuvé le", ou tampon "APPROVED ... <date>"). Ne pas confondre avec "report reviewed on" (relecture) sauf si c'est la seule date d'approbation. Une date absente, vide, "____", "n.c.", "n.m.", "—" ou "n/a" donne null. ATTENTION au tableau des visas : les dates "Rédigé par"/"Vérifié par" ne sont PAS des dates de validation ; ne prends la date que dans la colonne/ligne "Approuvé par"/"Approved by" si elle est remplie, ou dans une mention/tampon d'approbation explicite. Si seule la date de rédaction ou de vérification est remplie, date_validation = null.
2. Pour les nombres, renvoie un nombre JSON (pas une chaîne) dans l'unité demandée :
   - volume_dose_ml : volume de dose MOYEN mesuré APRÈS réglage (as left / après réglage / moyenne après / moyen des essais). Si plusieurs têtes et pas de moyenne générale, fais la moyenne de toutes les valeurs après réglage des têtes. Si la valeur n'est que dans une annotation du schéma (ex. "Fill volume as left: 19.3 mL"), utilise-la. Ignore les valeurs "avant réglage"/"as found". Convertis L, cl, µl, cm³ en mL.
   - volume_nominal_ml : volume de consigne / nominal / cible (target volume, "valeur visée", consigne). Convertis en mL.
   - tolerance_ml : tolérance admise sur le volume de dose. Si exprimée en %, calcule % × volume nominal. Si exprimée en µl/cl/L, convertis en mL. Si "n.c."/"n.m."/absent, null.
   - debit_ml_min : débit mesuré APRÈS réglage (as left / après réglage), dans le tableau, une note ("débit après réglage : ...") ou le texte de réglage. Si le tableau après réglage est vide/absent ("n.c.", "n.m.", "—") mais que le texte narratif donne un débit ("L'équipement débite alors X", "the equipment then delivers X", "débit après réglage"), utilise cette valeur narrative. Convertis L/h, L/min, ml/s, ml/min en mL/min. Si vraiment aucun débit après réglage ni narratif, null (ne prends pas la simple ligne "avant réglage/as found" du tableau).
   - pression_bar : pression de service mesurée APRÈS réglage, dans le tableau, une note ("pression de service après réglage : ...") ou le texte de réglage ("Pressure settled at X", "La pression s'est stabilisée à X", "operating pressure as left"). Convertis kPa, mbar, psi en bar. Si le tableau après réglage est vide/absent ("n.m.", "n.c.", "—") mais que le texte narratif donne une pression après réglage, utilise cette valeur. Si vraiment aucune, null (ne prends pas la simple ligne "avant réglage/as found").
3. report_reference : si l'en-tête n'a pas de référence explicite mais qu'une note/observation donne "réf. document", "report reference", "reference", "Réf. document : X" (et que X n'est pas une référence d'un autre rapport remplacé), utilise-la comme référence de CE rapport. De même pour reference_rapport.
4. reference_piece : référence de la pièce réellement REMPLACÉE pendant l'intervention ("remplacée", "replaced", "a été remplacé par", "part reference of the replaced part"). Ne prends pas une pièce contrôlée/conservée, commandée (non posée) ou proposée au devis. S'il n'y a aucune pièce remplacée, null. Si une note donne explicitement la référence de la pièce remplacée, elle prime sur la liste des pièces.
5. technicien : technicien responsable côté prestataire. Prends-le UNIQUEMENT si le document l'identifie explicitement comme responsable : "Lead technician", "Responsible technician", "Technicien responsable", "Intervenant principal", "Responsable technicien", "X (responsable)", "X (lead)", ou une phrase "X a conduit/lédé l'intervention"/"X led the visit". Ne prends JAMAIS : l'approbation client, un "assistant"/"accompagnant", une personne qui "a participé"/"took part"/"était présent", le demandeur/"requested by", ni le rédacteur du rapport ("Report prepared by", "Rapport rédigé par") sauf s'il est aussi désigné responsable. Si aucun responsable explicite, null.
6. statut : décision FINALE sur l'équipement : "conforme", "non_conforme" ou "a_revoir". Utilise le statut de conclusion, le tampon, la case cochée, ou une note "For the record, status/outcome". "À l'arrivée l'équipement était jugé non conforme" n'est PAS le statut final. En cas de contradiction entre une case cochée et le texte de conclusion, privilégie la conclusion/tampon le plus explicite. Mapping : Compliant/Conforme -> conforme ; Non-compliant/Non conforme -> non_conforme ; To be reviewed/À revoir -> a_revoir.
7. L'équipement du document : utilise les champs d'en-tête (Équipement/Machine/Unit/Equipment/Désignation, Constructeur/Manufacturer/Make/Fabricant/Brand, N° de série/Serial/Unit ID/Identifiant machine, Site/Location) et aussi les notes ("Additional information, equipment: ...", "serial number: ...", "équipement : ...", "implantation : ..."). Le "Siège" du client n'est PAS le site, et l'"Installation"/"Ligne"/"Line" n'est PAS le site. Pour le site, utilise aussi "visit to the customer, X" / "déplacement chez le client, X". Les valeurs "—", "n.c.", "n.m.", "n/a", "—" donnent null.
8. Ignore totalement les données du "convoyeur amont"/"upstream conveyor", du réseau d'air, des instruments de mesure, des moteurs, et des autres équipements, qui sont des distracteurs.
9. Pour un rectificatif : "rectifies" = référence du rapport visé ; "corrections" contient la ou les valeurs corrigées. Le champ doit être l'une des 11 clés d'intervention. Convertis la valeur dans l'unité de la clé et normalise le statut. N'invente pas d'autres corrections.
10. Pour un avis d'annulation : "cancels" = liste des références annulées.
11. Si le document est un rapport qui "annule et remplace"/"supersedes" un autre rapport, mets la référence de l'ancien rapport dans "supersedes".
12. N'invente JAMAIS de valeur. Une valeur absente est null.
"""

def call(pdfpath):
    d=pymupdf.open(pdfpath)
    texts=[]; imgs=[]
    for i,pg in enumerate(d):
        t=pg.get_text()
        texts.append(f"===== PAGE {i+1} =====\n{t}")
        pix=pg.get_pixmap(dpi=140)
        imgs.append(base64.b64encode(pix.tobytes("png")).decode())
    content=[{"type":"text","text":PROMPT+"\n\nTEXTE EXTRAIT:\n"+"\n".join(texts)}]
    for j,img in enumerate(imgs):
        content.append({"type":"text","text":f"IMAGE PAGE {j+1}:"})
        content.append({"type":"image_url","image_url":{"url":"data:image/png;base64,"+img}})
    body={"model":os.environ['BANC_MODELE'],"messages":[{"role":"user","content":content}],"max_tokens":16000,"temperature":0}
    url=os.environ['BANC_MODELE_URL'].rstrip('/')+'/v1/chat/completions'
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+os.environ['BANC_CLE_MODELE']})
    t0=time.time()
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    dt=time.time()-t0
    msg=r['choices'][0]['message']
    txt=msg.get('content') or ''
    print("TIME",round(dt,1),"finish",r['choices'][0].get('finish_reason'),"usage",r.get('usage',{}).get('total_tokens'),file=sys.stderr)
    return txt

if __name__=='__main__':
    txt=call(sys.argv[1])
    print(txt)
