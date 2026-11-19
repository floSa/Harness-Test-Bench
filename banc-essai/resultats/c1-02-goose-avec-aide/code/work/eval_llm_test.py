import sys, os, json, glob, re, unicodedata, time
sys.path.insert(0, '/travail/work')
from llm import chat
from prompt import build
from concurrent.futures import ThreadPoolExecutor

KEYS = ["machine","constructeur","numero_serie","site","reference_rapport","date_intervention","date_validation","volume_dose_ml","volume_nominal_ml","tolerance_ml","debit_ml_min","pression_bar","reference_piece","technicien","statut"]

def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def sget(pred, k):
    return pred.get(k) if isinstance(pred, dict) else None

def run(doc):
    text = open(f'/travail/work/textes/{doc}.txt').read()
    out = chat(build(text), max_tokens=16000)
    try:
        pred = json.loads(out)
    except Exception:
        m = re.search(r'\{.*\}', out or '', re.S)
        pred = json.loads(m.group(0)) if m else {}
    return doc, pred

outdir = sys.argv[1] if len(sys.argv)>1 else '/travail/work/preds'
os.makedirs(outdir, exist_ok=True)
docs = sorted(os.path.basename(p)[:-4] for p in glob.glob('/travail/test/*.pdf'))
todo = [d for d in docs if not os.path.exists(f'{outdir}/{d}.json')]
t0=time.time()
with ThreadPoolExecutor(max_workers=8) as ex:
    for doc, pred in ex.map(run, todo):
        json.dump(pred, open(f'{outdir}/{doc}.json','w'), ensure_ascii=False, indent=1)
        print('done', doc, f'{time.time()-t0:.0f}s', flush=True)
