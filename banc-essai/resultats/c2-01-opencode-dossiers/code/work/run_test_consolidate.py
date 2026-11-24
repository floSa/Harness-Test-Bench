import sys,os,json
sys.path.insert(0,'work')
from consolidate import consolidate
os.makedirs('work/test_out',exist_ok=True)
for d in sorted(os.listdir('test')):
    if not d.startswith('dos-'): continue
    out=consolidate(f'test/{d}','work/test_pieces')
    json.dump(out,open(f'work/test_out/{d}.json','w'),ensure_ascii=False,indent=2)
    print('===',d)
    print(json.dumps({k:out[k] for k in ['machine','constructeur','numero_serie','site','statut_actuel']},ensure_ascii=False))
    for it in out['interventions']:
        print('  ',it['reference_rapport'],it['date_intervention'],it['statut'],'vol',it['volume_dose_ml'],'nom',it['volume_nominal_ml'],'tol',it['tolerance_ml'],'deb',it['debit_ml_min'],'pres',it['pression_bar'],'piece',it['reference_piece'],'tech',it['technicien'],'dv',it['date_validation'])
