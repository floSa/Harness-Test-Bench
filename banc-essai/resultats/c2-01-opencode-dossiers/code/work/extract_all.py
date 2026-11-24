import os,sys,glob,json,time,concurrent.futures,traceback
sys.path.insert(0,'work')
from proto import call
os.makedirs('work/pieces',exist_ok=True)
pdfs=sorted(glob.glob('fourni/dos-*/*.pdf'))
def job(p):
    ds=os.path.basename(os.path.dirname(p)); fn=os.path.basename(p)[:-4]
    out=f'work/pieces/{ds}__{fn}.json'
    if os.path.exists(out): return out
    for attempt in range(3):
        try:
            txt=call(p)
            # strip fences
            t=txt.strip()
            if t.startswith('```'):
                t=t.split('\n',1)[1]
                if t.rstrip().endswith('```'): t=t.rstrip()[:-3]
            obj=json.loads(t)
            json.dump(obj,open(out,'w'),ensure_ascii=False,indent=1)
            return out
        except Exception as e:
            print('RETRY',p,attempt,repr(e),file=sys.stderr)
            time.sleep(2)
    return None
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for r in ex.map(job,pdfs):
        print(r,flush=True)
