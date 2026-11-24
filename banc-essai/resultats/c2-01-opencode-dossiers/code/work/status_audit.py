import os,sys,json,base64,glob,concurrent.futures,time
import pymupdf,urllib.request
PROMPT=r"""On te donne un rapport d'intervention complet (texte + images). Détermine UNIQUEMENT le statut final de l'équipement : "conforme", "non_conforme", "a_revoir", ou null si aucun statut final n'est indiqué. Cherche : conclusion, case cochée (☒), tampon, mention "For the record, status/outcome", "Statut", "Verdict", "Result", "Avis". Attention : "À l'arrivée, l'équipement était jugé non conforme" n'est PAS le statut final. Si l'avis du technicien dit que l'équipement peut être remis en production sans réserve -> conforme ; sous réserve d'une visite rapprochée / subject to follow-up -> a_revoir ; ne peut pas être remis en production en l'état -> non_conforme. Réponds en JSON : {"statut":"conforme|non_conforme|a_revoir|null","preuve":"page + extrait exact"}"""
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
