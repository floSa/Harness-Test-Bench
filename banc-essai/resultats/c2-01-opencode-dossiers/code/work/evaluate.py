import json,glob,os,sys,re,unicodedata
sys.path.insert(0,'work')
from consolidate import consolidate,FIELDS

def normtxt(x):
    if x is None: return None
    s=str(x)
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))
    s=re.sub(r'\s+',' ',s).strip().lower()
    return s

def val_ok(field,got,exp):
    if exp is None: return got is None
    if got is None: return False
    if field.startswith('date'): return str(got)==str(exp)
    if field in ('volume_dose_ml','volume_nominal_ml','tolerance_ml','debit_ml_min','pression_bar'):
        try: return abs(float(got)-float(exp))<=0.0100001
        except: return False
    return normtxt(got)==normtxt(exp)

def score_file(dossier):
    got=consolidate(f'fourni/{dossier}')
    exp=json.load(open(f'fourni/reponses/{dossier}.json'))
    # equipment keys
    res={}
    for f in ['machine','constructeur','numero_serie','site']:
        res[f]=val_ok(f,got.get(f),exp.get(f))
    # interventions matched by ref
    gi={normtxt(i['reference_rapport']):i for i in got['interventions'] if i.get('reference_rapport')}
    ei={normtxt(i['reference_rapport']):i for i in exp['interventions'] if i.get('reference_rapport')}
    tp=fp=fn=0
    detail=[]
    for ref,e in ei.items():
        if ref in gi:
            g=gi[ref]
            for f in FIELDS:
                ok=val_ok(f,g.get(f),e.get(f))
                if ok: tp+=1
                else: fp+=1; detail.append((ref,f,g.get(f),e.get(f)))
        else:
            fn+=len(FIELDS); detail.append((ref,'MISSING_INTERVENTION',None,None))
    for ref,g in gi.items():
        if ref not in ei:
            fp+=len(FIELDS); detail.append((ref,'EXTRA_INTERVENTION',None,None))
    res['_tp'],res['_fp'],res['_fn']=tp,fp,fn
    res['_detail']=detail
    res['statut_actuel']=val_ok('statut',got.get('statut_actuel'),exp.get('statut_actuel'))
    return got,exp,res

if __name__=='__main__':
    tot_tp=tot_fp=tot_fn=0; perfect=0; n=0
    for d in sorted(os.listdir('fourni')):
        if not d.startswith('dos-'): continue
        got,exp,r=score_file(d); n+=1
        tot_tp+=r['_tp']; tot_fp+=r['_fp']; tot_fn+=r['_fn']
        eq=sum(1 for f in ['machine','constructeur','numero_serie','site'] if r[f])
        allok=(r['_fp']==0 and r['_fn']==0 and eq==4 and r['statut_actuel'])
        perfect+=allok
        print(d, f"fields={eq}/4 tp={r['_tp']} fp={r['_fp']} fn={r['_fn']} perfect={allok}")
        for det in r['_detail']:
            print('   ',det)
    prec=tot_tp/(tot_tp+tot_fp) if tot_tp+tot_fp else 0
    rec=tot_tp/(tot_tp+tot_fn) if tot_tp+tot_fn else 0
    print('TOTAL tp',tot_tp,'fp',tot_fp,'fn',tot_fn,'P',round(prec,4),'R',round(rec,4),'F1',round(2*prec*rec/(prec+rec),4),'perfect',perfect,'/',n)
