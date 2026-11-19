import pymupdf, glob, os, re

STATUS_LABELS = [
    ('non_conforme', ['non-conforme','non conforme','noncompliant','non compliant']),
    ('a_revoir', ['a revoir','à revoir','to be reviewed','reviewed']),
    ('conforme', ['conforme','compliant']),
]

def norm(s):
    s = s.lower()
    for a,b in [('à','a'),('é','e'),('è','e'),('ê','e'),('ç','c'),('û','u'),('ô','o')]:
        s = s.replace(a,b)
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def page_status(page):
    words = page.get_text('words')
    drawings = page.get_drawings()
    boxes = []
    for dr in drawings:
        r = dr['rect']
        if dr['type'] in ('s','f') and 5 <= r.width <= 14 and 5 <= r.height <= 14:
            # box candidate if it's a rect item or fill
            items = dr.get('items', [])
            if any(it[0]=='re' for it in items) or dr['type']=='f':
                boxes.append((r, dr))
    # merge boxes with same bbox
    outs = []
    for r, dr in boxes:
        # marks inside
        marked = False
        nlines = 0
        for d2 in drawings:
            r2 = d2['rect']
            if abs(r2.x0-r.x0)<1.5 and abs(r2.y0-r.y0)<1.5 and abs(r2.x1-r.x1)<1.5 and abs(r2.y1-r.y1)<1.5:
                lines = [it for it in d2.get('items',[]) if it[0] in ('l','c')]
                nlines += len(lines)
                if d2.get('fill') and d2 is not dr:
                    marked = True
        if nlines >= 2:
            marked = True
        # label at same y to the right
        cand = []
        for w in words:
            x0,y0,x1,y1,t = w[:5]
            if abs((y0+y1)/2 - (r.y0+r.y1)/2) < 7 and x0 > r.x1-1 and x0 < r.x1+160:
                cand.append((x0,t))
        cand.sort()
        label = ' '.join(t for _,t in cand)
        if label:
            outs.append((round((r.y0+r.y1)/2,1), label, marked))
    # dedupe by (y,label)
    seen=set(); res=[]
    for y,label,m in outs:
        key=(y,norm(label))
        if key in seen: continue
        seen.add(key); res.append((y,label,m))
    return res

if __name__ == '__main__':
    for p in sorted(glob.glob('/travail/fourni/*.pdf')+glob.glob('/travail/test/*.pdf')):
        d = pymupdf.open(p)
        rows=[]
        for pno,page in enumerate(d,1):
            for y,label,m in page_status(page):
                if m: rows.append((pno,label))
        if rows:
            print(os.path.basename(p), rows)
