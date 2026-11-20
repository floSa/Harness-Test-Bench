import pymupdf, sys, os
sys.path.insert(0, '.')
from ocr import ocr_png

pdf = sys.argv[1]
d = pymupdf.open(pdf)
for pno, p in enumerate(d):
    for img in p.get_images(full=True):
        xref = img[0]
        pix = pymupdf.Pixmap(d, xref)
        if pix.width < 200:
            continue
        path = f'/tmp/img_{os.path.basename(pdf)[:-4]}_{pno+1}_{xref}.png'
        pix.save(path)
        print('==== page', pno + 1, 'xref', xref, pix.width, pix.height)
        print(ocr_png(path))
