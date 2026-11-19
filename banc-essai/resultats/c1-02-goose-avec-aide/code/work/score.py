import json, glob, os, sys, re, unicodedata
KEYS = ["machine","constructeur","numero_serie","site","reference_rapport","date_intervention","date_validation","volume_dose_ml","volume_nominal_ml","tolerance_ml","debit_ml_min","pression_bar","reference_piece","technicien","statut"]
def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()
def eq(k, a, b):
    if a is None or b is None: return a is None and b is None
    if k in ('volume_dose_ml','volume_nominal_ml','tolerance_ml','debit_ml_min','pression_bar'):
        try: return abs(float(a)-float(b))<=0.01
        except: return False
    if k.startswith('date'):
        return str(a)==str(b)
    if k=='statut':
        return norm(a)==norm(b)
    return norm(a)==norm(b)
preds_dir = sys.argv[1] if len(sys.argv)>1 else '/travail/work/preds'
tot=0; good=0; per={k:[0,0] for k in KEYS}; errors={k:[] for k in KEYS}
for p in sorted(glob.glob('/travail/fourni/reponses/*.json')):
    doc=os.path.basename(p)[:-5]
    exp=json.load(open(p)); pred=json.load(open(f'{preds_dir}/{doc}.json'))
    for k in KEYS:
        tot+=1; per[k][1]+=1
        ok=eq(k, pred.get(k), exp.get(k))
        if ok: good+=1; per[k][0]+=1
        else: errors[k].append((doc, exp.get(k), pred.get(k)))
print(f'SCORE {good}/{tot} = {good/tot:.4f}')
for k in KEYS:
    print(f'{k:20s} {per[k][0]:2d}/{per[k][1]:2d}')
print()
for k in KEYS:
    if errors[k]:
        print('###',k)
        for e in errors[k]: print('  ',e)
