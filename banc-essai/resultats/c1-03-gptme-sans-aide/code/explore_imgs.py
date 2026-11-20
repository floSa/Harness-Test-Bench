import pymupdf, glob, os, hashlib, json
seen = {}
for f in sorted(glob.glob('fourni/*.pdf')):
    d = pymupdf.open(f)
    for pno, p in enumerate(d):
        for img in p.get_images(full=True):
            xref = img[0]
            pix = pymupdf.Pixmap(d, xref)
            h = hashlib.md5(pix.samples).hexdigest()[:10]
            seen.setdefault(h, []).append((os.path.basename(f), pno + 1, pix.width, pix.height))
print('unique', len(seen))
for h, v in sorted(seen.items(), key=lambda kv: -len(kv[1])):
    print(h, len(v), v[0], v[1:3])
