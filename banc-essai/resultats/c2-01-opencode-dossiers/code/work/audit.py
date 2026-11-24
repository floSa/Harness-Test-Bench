import os,sys,json,base64,glob,time,concurrent.futures,re
import pymupdf,urllib.request
PROMPT=r"""Tu es auditeur de données d'intervention sur équipements de dosage. On te donne toutes les pages (texte + images) d'UN rapport. Remplis le JSON ci-dessous en te fondant STRICTEMENT sur ce qui est explicitement lisible. Pour chaque champ, ajoute une preuve courte : la page et l'extrait exact (ou "absente").

{
 "report_reference": "",
 "equipment": {"machine":"", "constructeur":"", "numero_serie":"", "site":""},
 "raw": {
   "date_intervention": "",
   "date_validation": "",
   "dose_apres_reglage_valeurs_brutes": ["liste de toutes les valeurs de dose après réglage/as left, avec unité"],
   "volume_dose_moyen_brut": "",
   "volume_nominal_brut": "",
   "tolerance_brute": "",
   "debit_apres_reglage_brut": "",
   "pression_apres_reglage_brute": "",
   "piece_remplacee_brute": "",
   "technicien_responsable_brut": "",
   "statut_final_brut": ""
 },
 "normalise": {
   "volume_dose_ml": null, "volume_nominal_ml": null, "tolerance_ml": null,
   "debit_ml_min": null, "pression_bar": null,
   "reference_piece": null, "technicien": null, "statut": null,
   "date_intervention": null, "date_validation": null
 },
 "preuves": {"champ": "page + extrait"}
}

Règles : dates AAAA-MM-JJ ; nombres JSON ; doses/débits/pressions APRÈS réglage uniquement ; moyenne de tous les essais après réglage (toutes têtes) ; tolérance en % convertie avec le volume nominal ; unités converties (L, cl, µl, cm³ -> mL ; L/h, L/min, ml/s -> mL/min ; kPa, mbar, psi -> bar). Une valeur absente/—/n.c./n.m. = null. Pièce = seulement remplacée. Technicien = seulement responsable explicite. Statut final = conforme/non_conforme/a_revoir. Ne devine pas : préfère null et signale "absente".
Renvoie uniquement le JSON."""
def call(pdf):
    d=pymupdf.open(pdf); texts=[]; content=[]
    for i,pg in enumerate(d):
        texts.append(f"===== PAGE {i+1} =====\n{pg.get_text()}")
    content.append({"type":"text","text":PROMPT+"\n\nTEXTE:\n"+"\n".join(texts)})
    for i,pg in enumerate(d):
        pix=pg.get_pixmap(dpi=140)
        content.append({"type":"text","text":f"IMAGE PAGE {i+1}"})
        content.append({"type":"image_url","image_url":{"url":"data:image/png;base64,"+base64.b64encode(pix.tobytes("png")).decode()}})
    body={"model":os.environ['BANC_MODELE'],"messages":[{"role":"user","content":content}],"max_tokens":16000,"temperature":0}
    url=os.environ['BANC_MODELE_URL'].rstrip('/')+'/v1/chat/completions'
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+os.environ['BANC_CLE_MODELE']})
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    return r['choices'][0]['message'].get('content') or ''
if __name__=='__main__':
    # retained pieces from test_out
    import json
    retained=set()
    for f in glob.glob('work/test_out/*.json'):
        d=json.load(open(f))
        for it in d['interventions']: retained.add(it['reference_rapport'].lower())
    pdfs=[]
    for p in glob.glob('test/*/*.pdf'):
        txt=''.join(pg.get_text() for pg in pymupdf.open(p)).lower()
        if any(ref.replace(' ','') in txt.replace(' ','') for ref in retained): pdfs.append(p)
    pdfs=sorted(set(pdfs)); os.makedirs('work/audit',exist_ok=True)
    def job(p):
        ds=os.path.basename(os.path.dirname(p)); fn=os.path.basename(p)[:-4]; out=f'work/audit/{ds}__{fn}.json'
        if os.path.exists(out): return out
        for _ in range(3):
            try:
                t=call(p).strip()
                if t.startswith('```'):
                    t=t.split('\n',1)[1]
                    if t.rstrip().endswith('```'): t=t.rstrip()[:-3]
                obj=json.loads(t); json.dump(obj,open(out,'w'),ensure_ascii=False,indent=1); return out
            except Exception as e:
                print('RETRY',p,e,file=sys.stderr); time.sleep(2)
        return None
    print('pieces',len(pdfs),file=sys.stderr)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(job,pdfs): print(r,flush=True)
