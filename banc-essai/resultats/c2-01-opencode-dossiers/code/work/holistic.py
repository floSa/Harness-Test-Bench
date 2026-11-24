import os,sys,json,base64,glob,concurrent.futures,time
import pymupdf,urllib.request
PROMPT=r"""Tu reçois TOUTES les pièces d'un dossier d'équipement de dosage (texte + images de chaque page). Construis la réponse finale du dossier.

Règles :
- L'équipement du dossier est celui de la majorité des rapports.
- Chaque rapport d'intervention sur cet équipement = une intervention.
- À écarter : rapports sur un autre équipement (même site/modèle, numéro de série différent), rapports annulés/remplacés ("annule et remplace"/"supersedes"), rapports visés par un avis d'annulation.
- Un rectificatif remplace la valeur visée du rapport concerné ; les autres valeurs restent.
- Une intervention a exactement : reference_rapport, date_intervention, date_validation, volume_dose_ml, volume_nominal_ml, tolerance_ml, debit_ml_min, pression_bar, reference_piece, technicien, statut.
- Valeurs après réglage uniquement (tableau, note ou annotation de schéma). Dates AAAA-MM-JJ. Nombres JSON. Valeur absente = null. Statut = conforme/non_conforme/a_revoir.
- Site : champ Site/Location/Implantation, ou "visit to the customer, X"/"déplacement chez le client, X". Pas le Siège, pas l'Installation/Ligne.
- Technicien : seulement responsable explicite (Lead/Responsable/Intervenant principal/chargé d'intervention/conduit l'intervention).
- Pièce : seulement réellement remplacée.
- Trie les interventions par date_intervention croissante.
Réponds UNIQUEMENT :
{"machine":null,"constructeur":null,"numero_serie":null,"site":null,"interventions":[{...}],"statut_actuel":null}"""
def call(dossier):
    pdfs=sorted(glob.glob(dossier+'/*.pdf')); texts=[]; content=[]
    for p in pdfs:
        d=pymupdf.open(p); t=[]
        for i,pg in enumerate(d): t.append(f"--- {os.path.basename(p)} page {i+1} ---\n{pg.get_text()}")
        texts.append('\n'.join(t))
    content.append({"type":"text","text":PROMPT+"\n\nTEXTES:\n"+"\n".join(texts)})
    for p in pdfs:
        d=pymupdf.open(p)
        for i,pg in enumerate(d):
            pix=pg.get_pixmap(dpi=110)
            content.append({"type":"text","text":f"IMAGE {os.path.basename(p)} page {i+1}"})
            content.append({"type":"image_url","image_url":{"url":"data:image/png;base64,"+base64.b64encode(pix.tobytes("png")).decode()}})
    body={"model":os.environ['BANC_MODELE'],"messages":[{"role":"user","content":content}],"max_tokens":16000,"temperature":0}
    url=os.environ['BANC_MODELE_URL'].rstrip('/')+'/v1/chat/completions'
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+os.environ['BANC_CLE_MODELE']})
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    t=r['choices'][0]['message'].get('content') or ''; s=t.find('{'); e=t.rfind('}'); return json.loads(t[s:e+1])
def job(ds):
    for _ in range(3):
        try: return ds,call(f'test/{ds}')
        except Exception as e: time.sleep(2); err=repr(e)
    return ds,{'error':err}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    for ds,res in ex.map(job,sys.argv[1:]): print(ds,json.dumps(res,ensure_ascii=False))
