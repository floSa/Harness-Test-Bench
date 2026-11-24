import os,sys,json,base64,glob,concurrent.futures,time
import pymupdf,urllib.request
PROMPT=r"""On te donne un rapport d'intervention (texte + images). Donne UNIQUEMENT :
- date_intervention : date réelle de l'intervention (pas demande/émission/impression/prochaine visite)
- date_validation : date de l'APPROBATION FINALE (champ Validation date / Date de validation / Approuvé le / tampon APPROUVÉ-APPROVED). Ne prends PAS la date de rédaction, de vérification, ni "relu/reviewed", sauf si c'est explicitement la seule date d'approbation.
Format AAAA-MM-JJ. Si absente : null.
Réponds JSON : {"date_intervention":null,"date_validation":null,"preuve_validation":"page + extrait exact"}"""
def call(pdf):
    d=pymupdf.open(pdf); texts=[]; content=[]
    for i,pg in enumerate(d): texts.append(f"===== PAGE {i+1} =====\n{pg.get_text()}")
    content.append({"type":"text","text":PROMPT+"\n\nTEXTE:\n"+"\n".join(texts)})
    for i,pg in enumerate(d):
        pix=pg.get_pixmap(dpi=140)
        content.append({"type":"text","text":f"IMAGE PAGE {i+1}"})
        content.append({"type":"image_url","image_url":{"url":"data:image/png;base64,"+base64.b64encode(pix.tobytes("png")).decode()}})
    body={"model":os.environ['BANC_MODELE'],"messages":[{"role":"user","content":content}],"max_tokens":4000,"temperature":0}
    url=os.environ['BANC_MODELE_URL'].rstrip('/')+'/v1/chat/completions'
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+os.environ['BANC_CLE_MODELE']})
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    t=r['choices'][0]['message'].get('content') or ''; s=t.find('{'); e=t.rfind('}'); return json.loads(t[s:e+1])
args=sys.argv[1:]; items=[(args[i],args[i+1]) for i in range(0,len(args),2)]
def job(x):
    name,pdf=x
    for _ in range(3):
        try: return name,call(pdf)
        except Exception as e: time.sleep(2)
    return name,{'error':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for name,res in ex.map(job,items): print(name,json.dumps(res,ensure_ascii=False))
