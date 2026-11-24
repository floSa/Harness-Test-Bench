import os,sys,json,base64,glob,concurrent.futures,time
import pymupdf,urllib.request
PROMPT=r"""Regarde attentivement TOUTES les pages et surtout les annotations sur les schémas, les notes et les tampons de ce rapport d'intervention. On cherche uniquement trois valeurs APRÈS réglage :
- volume de dose moyen après réglage (mL)
- débit après réglage (mL/min)
- pression de service après réglage (bar)
Pour chacune, indique si une valeur est explicitement écrite quelque part (texte, note, annotation de schéma, tableau après réglage), avec la valeur brute, l'unité et l'extrait exact. Si absente, mets null. Ne déduis rien, n'utilise pas les valeurs avant réglage. Réponds en JSON :
{"volume":{"value":null,"raw":""},"debit":{"value":null,"raw":""},"pression":{"value":null,"raw":""}}"""
def call(pdf):
    d=pymupdf.open(pdf); texts=[]; content=[]
    for i,pg in enumerate(d):
        texts.append(f"===== PAGE {i+1} =====\n{pg.get_text()}")
    content.append({"type":"text","text":PROMPT+"\n\nTEXTE:\n"+"\n".join(texts)})
    for i,pg in enumerate(d):
        pix=pg.get_pixmap(dpi=140)
        content.append({"type":"text","text":f"IMAGE PAGE {i+1}"})
        content.append({"type":"image_url","image_url":{"url":"data:image/png;base64,"+base64.b64encode(pix.tobytes("png")).decode()}})
    body={"model":os.environ['BANC_MODELE'],"messages":[{"role":"user","content":content}],"max_tokens":4000,"temperature":0}
    url=os.environ['BANC_MODELE_URL'].rstrip('/')+'/v1/chat/completions'
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+os.environ['BANC_CLE_MODELE']})
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    t=r['choices'][0]['message'].get('content') or ''
    s=t.find('{'); e=t.rfind('}'); return json.loads(t[s:e+1])
args=sys.argv[1:]
items=[(args[i],args[i+1]) for i in range(0,len(args),2)]
def job(x):
    name,pdf=x
    for _ in range(3):
        try: return name,call(pdf)
        except Exception as e: time.sleep(2)
    return name,{'error':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for name,res in ex.map(job,items): print(name,json.dumps(res,ensure_ascii=False))
