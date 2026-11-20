import json, glob, os, sys, unicodedata, re
from concurrent.futures import ThreadPoolExecutor
import extract

CLES = extract.CLES


def norm(s):
    if s is None:
        return None
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower()
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def parse_json(txt):
    if not txt:
        return None
    m = re.search(r'\{.*\}', txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def score_one(pred, gold):
    ok = 0
    details = {}
    for k in CLES:
        p = pred.get(k) if isinstance(pred, dict) else None
        g = gold.get(k)
        good = False
        if g is None:
            good = p is None
        elif isinstance(g, (int, float)) and not isinstance(g, bool):
            try:
                good = p is not None and abs(float(p) - float(g)) <= 0.01
            except Exception:
                good = False
        else:
            good = norm(p) == norm(g)
        details[k] = good
        ok += good
    return ok, details


def run(pdf):
    try:
        obj = extract.extract(pdf)
        if isinstance(obj, dict):
            return pdf, obj, ''
        return pdf, parse_json(obj), obj
    except Exception as e:
        return pdf, None, repr(e)


if __name__ == '__main__':
    pdfs = sorted(glob.glob('fourni/*.pdf'))
    if len(sys.argv) > 1:
        pdfs = [p for p in pdfs if any(a in p for a in sys.argv[1:])]
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(run, pdfs))
    total_ok = 0
    total = 0
    per_key = {k: 0 for k in CLES}
    for pdf, pred, raw in results:
        gold = json.load(open('fourni/reponses/' + os.path.basename(pdf)[:-4] + '.json'))
        ok, det = score_one(pred, gold)
        total_ok += ok
        total += len(CLES)
        for k in CLES:
            per_key[k] += det[k]
        bad = [k for k in CLES if not det[k]]
        print(f'{os.path.basename(pdf)} {ok}/15  manqués: {bad}')
        if pred is None:
            print('   RAW:', raw[:300])
        else:
            for k in bad:
                print(f'     {k}: pred={pred.get(k)!r} gold={gold.get(k)!r}')
    print('=== TOTAL', total_ok, '/', total, '=', round(total_ok / total, 4))
    print('par clé:', {k: per_key[k] for k in CLES})
