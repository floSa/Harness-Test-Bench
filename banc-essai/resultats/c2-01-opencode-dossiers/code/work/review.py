import os,sys,json,base64,glob,concurrent.futures,time
import pymupdf,urllib.request
PROMPT=r"""Tu es relecteur qualité. On te donne TOUTES les pièces PDF d'un dossier d'équipement de dosage (texte + images de chaque page), puis une PROPOSITION de réponse JSON. Vérifie la proposition champ par champ à partir des pièces.

Règles du dossier :
- L'équipement du dossier est celui de la majorité des rapports.
- À écarter : rapports sur un autre équipement (même site/modèle, numéro de série différent), rapports annulés/remplacés (header "annule et remplace"/"supersedes"), rapports visés par un avis d'annulation.
- Un rectificatif remplace la valeur visée du rapport concerné ; les autres valeurs restent.
- Chaque intervention retenue doit avoir exactement : reference_rapport, date_intervention, date_validation, volume_dose_ml, volume_nominal_ml, tolerance_ml, debit_ml_min, pression_bar, reference_piece, technicien, statut.
- Les valeurs après réglage peuvent être dans le tableau, une note, ou une annotation de schéma. Les dates de validation peuvent être dans un tampon "APPROUVÉ/APPROVED".
- Les valeurs absentes sont null. Les intervalles de dates sont AAAA-MM-JJ.

Ta mission : signale UNIQUEMENT les erreurs certaines de la proposition (valeur fausse, intervention en trop/manquante, équipement/site/série faux). Ne signale pas une valeur null comme erreur si le document ne la donne pas explicitement. Ne propose pas de changement si tu n'as pas de preuve explicite dans les pièces.

Réponds en JSON :
{"erreurs":[{"champ":"...","reference":"...","propose":..., "actuel":..., "preuve":"page + extrait exact"}]}
Si aucune erreur certaine : {"erreurs":[]}"""
def call(dossier, outjson):
    pdfs=sorted(glob.glob(dossier+'/*.pdf')); content=[]; texts=[]
    for k,p in enumerate(pdfs):
        d=pymupdf.open(p); doc=[]
        for i,pg in enumerate(d): doc.append(f"--- {os.path.basename(p)} page {i+1} ---\n{pg.get_text()}")
        texts.append('\n'.join(doc))
    content.append({"type":"text","text":PROMPT+"\n\nPROPOSITION:\n"+json.dumps(outjson,ensure_ascii=False)+"\n\nTEXTES:\n"+"\n".join(texts)})
    for k,p in enumerate(pdfs):
        d=pymupdf.open(p)
        for i,pg in enumerate(d):
            pix=pg.get_pixmap(dpi=110)
            content.append({"type":"text","text":f"IMAGE {os.path.basename(p)} page {i+1}"})
            content.append({"type":"image_url","image_url":{"url":"data:image/png;base64,"+base64.b64encode(pix.tobytes("png")).decode()}})
    body={"model":os.environ['BANC_MODELE'],"messages":[{"role":"user","content":content}],"max_tokens":12000,"temperature":0}
    url=os.environ['BANC_MODELE_URL'].rstrip('/')+'/v1/chat/completions'
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+os.environ['BANC_CLE_MODELE']})
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    t=r['choices'][0]['message'].get('content') or ''; s=t.find('{'); e=t.rfind('}'); return json.loads(t[s:e+1])
args=sys.argv[1:]; dslist=[d for d in args]
def job(ds):
    for _ in range(2):
        try:
            out=json.load(open(f'work/prod_test2/{ds}.json'))
            return ds,call(f'test/{ds}',out)
        except Exception as e:
            time.sleep(2); err=repr(e)
    return ds,{'error':err}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    for ds,res in ex.map(job,dslist): print(ds,json.dumps(res,ensure_ascii=False))
