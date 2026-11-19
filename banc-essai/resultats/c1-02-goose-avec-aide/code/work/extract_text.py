import pymupdf, glob, os, sys, json, time
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
OUT = '/travail/work/textes'
os.makedirs(OUT, exist_ok=True)

def ocr_image(doc, xref):
    pix = pymupdf.Pixmap(doc, xref)
    if pix.n - pix.alpha >= 4:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    # upscale small images for OCR
    if pix.width < 700:
        z = min(3.0, 1000/pix.width)
        pix = pymupdf.Pixmap(pix, 0) if False else pix
    png = pix.tobytes('png')
    res, _ = ocr(png)
    if not res: return []
    return [t for _, t, s in res if s > 0.35]

def process(pdf):
    doc = pymupdf.open(pdf)
    out = []
    for pno, page in enumerate(doc, 1):
        out.append(f"\n\n===== PAGE {pno} =====")
        out.append(page.get_text())
        infos = page.get_image_info(xrefs=True)
        for i, info in enumerate(infos):
            b = info['bbox']
            lines = ocr_image(doc, info['xref'])
            if lines:
                out.append(f"\n[IMAGE p{pno} #{i+1} bbox=({b[0]:.0f},{b[1]:.0f},{b[2]:.0f},{b[3]:.0f}) texte OCR:]")
                out.append(' | '.join(lines))
    return '\n'.join(out)

if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob('/travail/fourni/*.pdf'))
    for p in files:
        name = os.path.basename(p)[:-4]
        dest = os.path.join(OUT, name + '.txt')
        if os.path.exists(dest): continue
        t0=time.time()
        txt = process(p)
        open(dest,'w').write(txt)
        print(name, len(txt), f'{time.time()-t0:.1f}s', flush=True)
