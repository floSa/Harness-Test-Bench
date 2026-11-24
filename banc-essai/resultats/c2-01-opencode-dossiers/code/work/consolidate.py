import os,json,glob,re,sys
from collections import Counter

FIELDS=["reference_rapport","date_intervention","date_validation","volume_dose_ml","volume_nominal_ml","tolerance_ml","debit_ml_min","pression_bar","reference_piece","technicien","statut"]

def canon_serial(s):
    if not s: return None
    s=str(s).upper()
    s=re.sub(r'[^A-Z0-9]','',s)
    s=s.replace('O','0').replace('I','1').replace('L','1').replace('S','5').replace('B','8')
    return s

def lev(a,b):
    if a is None or b is None: return 99
    if a==b: return 0
    if abs(len(a)-len(b))>2: return 99
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):
            cur.append(min(prev[j]+1,cur[j-1]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def clean_machine(m):
    if not m: return None
    s=m.strip()
    s=re.sub(r'^(doseuse volumétrique à piston|doseuse volumétrique|doseuse|remplisseuse rotative|remplisseuse|piston filler|rotary filling machine|filling machine|diaphragm metering pump|pompe doseuse|machine)\s+','',s,flags=re.I)
    s=re.sub(r'\s*;\s*.*$','',s)
    s=re.sub(r'^(the\s+)','',s,flags=re.I)
    return s.strip() or None

def norm(s):
    return re.sub(r'\s+',' ',str(s)).strip().lower()

def norm_date(d):
    if not d: return None
    s=str(d).strip()
    m=re.match(r'^(\d{4})-(\d{2})-(\d{2})$',s)
    if m: return s
    m=re.match(r'^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$',s)
    if m:
        a,b,c=m.groups(); yr=int(c); yr=yr+2000 if yr<100 else yr
        # ambiguous: assume day/month if first>12, else day/month (European)
        dd,mm=int(a),int(b)
        return f"{yr:04d}-{mm:02d}-{dd:02d}"
    return None

def num(v):
    if v is None: return None
    if isinstance(v,(int,float)): return float(v)
    try:
        s=str(v).replace(',','.').replace(' ','')
        return float(s)
    except: return None

def status_norm(s):
    if not s: return None
    t=norm(s).replace('_',' ').replace('-',' ')
    if 'non' in t and ('conform' in t or 'compliant' in t): return 'non_conforme'
    if 'revoir' in t or 'review' in t: return 'a_revoir'
    if 'conform' in t or 'compliant' in t: return 'conforme'
    return None

def consolidate(dossier_dir, pieces_dir='work/pieces'):
    pieces=[]
    for p in sorted(glob.glob(os.path.join(dossier_dir,'*.pdf'))):
        base=os.path.basename(p)[:-4]
        key=os.path.basename(dossier_dir)+'__'+base
        fp=os.path.join(pieces_dir,f'{key}.json')
        if not os.path.exists(fp): continue
        obj=json.load(open(fp))
        obj['_piece']=base; obj['_file']=p
        pieces.append(obj)
    reports=[p for p in pieces if p.get('type')=='report']
    # ensure ref
    for p in reports:
        it=p.get('intervention') or {}
        if not it.get('reference_rapport'): it['reference_rapport']=p.get('report_reference')
    # majority serial
    serial_counts=Counter()
    for p in reports:
        s=canon_serial(((p.get('equipment') or {}).get('numero_serie')) or (p.get('intervention') or {}).get('numero_serie'))
        if s: serial_counts[s]+=1
    target_serial=serial_counts.most_common(1)[0][0] if serial_counts else None
    # matching reports
    def same_serial(s):
        cs=canon_serial(s)
        if cs is None or target_serial is None: return True
        return cs==target_serial
    matching=[p for p in reports if same_serial(((p.get('equipment') or {}).get('numero_serie')))]
    if not matching: matching=reports
    # machine majority
    mc=Counter()
    for p in matching:
        m=clean_machine((p.get('equipment') or {}).get('machine'))
        if m: mc[m]+=1
    machine=mc.most_common(1)[0][0] if mc else None
    cc=Counter()
    for p in matching:
        c=(p.get('equipment') or {}).get('constructeur')
        if c: cc[c.strip()]+=1
    constructeur=cc.most_common(1)[0][0] if cc else None
    # raw serial majority among matching
    sc=Counter()
    for p in matching:
        s=(p.get('equipment') or {}).get('numero_serie')
        if s: sc[str(s).strip()]+=1
    if sc:
        # prefer canonical majority; choose most common raw among same canonical
        cand=[k for k in sc if canon_serial(k)==target_serial] or list(sc)
        raw_serial=max(cand,key=lambda k:(sc[k],k))
    else: raw_serial=None
    # exclusions
    cancelled=set()
    superseded=set()
    for p in pieces:
        for r in (p.get('cancels') or []):
            if r: cancelled.add(norm(r))
        for r in (p.get('supersedes') or []):
            if r: superseded.add(norm(r))
    active=[]
    for p in reports:
        ref=norm((p.get('intervention') or {}).get('reference_rapport') or p.get('report_reference') or '')
        if ref and ref in cancelled: continue
        if ref and ref in superseded: continue
        s=(p.get('equipment') or {}).get('numero_serie')
        if not same_serial(s): continue
        active.append(p)
    # dedupe by ref
    byref={}
    for p in active:
        ref=((p.get('intervention') or {}).get('reference_rapport') or p.get('report_reference') or '')
        key=norm(ref)
        if key in byref:
            # choose richer
            a=byref[key]['intervention']; b=p['intervention']
            if sum(v is not None for v in b.values())>sum(v is not None for v in a.values()): byref[key]=p
        else: byref[key]=p
    active=list(byref.values())
    # apply corrections
    corrections={}
    for p in pieces:
        if p.get('type')=='rectification' and p.get('rectifies'):
            corrections.setdefault(norm(p['rectifies']),[]).extend(p.get('corrections') or [])
    for p in active:
        ref=norm((p.get('intervention') or {}).get('reference_rapport') or '')
        for corr in corrections.get(ref,[]):
            f=corr.get('field'); v=corr.get('value_normalized')
            if f in FIELDS:
                if f=='statut': v=status_norm(v if isinstance(v,str) else corr.get('raw'))
                elif f.startswith('date'): v=norm_date(v)
                elif f in ('volume_dose_ml','volume_nominal_ml','tolerance_ml','debit_ml_min','pression_bar'): v=num(v)
                p['intervention'][f]=v
    # normalize fields
    for p in active:
        it=p['intervention']
        for f in ('volume_dose_ml','volume_nominal_ml','tolerance_ml','debit_ml_min','pression_bar'):
            it[f]=num(it.get(f))
        for f in ('date_intervention','date_validation'):
            it[f]=norm_date(it.get(f))
        it['statut']=status_norm(it.get('statut')) if it.get('statut') else None
        for f in ('reference_rapport','reference_piece','technicien'):
            if it.get(f) is not None: it[f]=str(it[f]).strip()
    # sort by date
    active.sort(key=lambda p:(p['intervention'].get('date_intervention') or '9999'))
    # site majority among active
    sitec=Counter()
    for p in active:
        s=(p.get('equipment') or {}).get('site')
        if s and norm(s) not in ('n.c.','n.m.','n/a','—','-'): sitec[str(s).strip()]+=1
    site=sitec.most_common(1)[0][0] if sitec else None
    interventions=[]
    for p in active:
        it=p['intervention']
        row={}
        for f in FIELDS: row[f]=it.get(f)
        interventions.append(row)
    statut_actuel=interventions[-1]['statut'] if interventions else None
    out={"machine":machine,"constructeur":constructeur,"numero_serie":raw_serial,"site":site,
         "interventions":interventions,"statut_actuel":statut_actuel}
    return out

if __name__=='__main__':
    out=consolidate(sys.argv[1])
    print(json.dumps(out,ensure_ascii=False,indent=2))
