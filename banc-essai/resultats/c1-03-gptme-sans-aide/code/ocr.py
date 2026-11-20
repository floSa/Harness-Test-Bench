import pymupdf, os, base64, json, urllib.request, hashlib

URL = os.environ['BANC_MODELE_URL'].rstrip('/') + '/v1/chat/completions'
KEY = os.environ['BANC_CLE_MODELE']
MODEL = os.environ['BANC_MODELE']


def ocr_png(path, prompt='Transcris tout le texte visible dans cette image, ligne par ligne, en conservant les libellés et les valeurs.'):
    b = base64.b64encode(open(path, 'rb').read()).decode()
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': prompt},
        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + b}}]}],
        'max_tokens': 4000}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Bearer ' + KEY})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    return r['choices'][0]['message'].get('content') or ''


if __name__ == '__main__':
    d = pymupdf.open('fourni/doc-020.pdf')
    for pno, p in enumerate(d):
        for img in p.get_images(full=True):
            xref = img[0]
            pix = pymupdf.Pixmap(d, xref)
            if pix.width > 1200:
                pix.save('/tmp/big.png')
                print('page', pno + 1, pix.width, pix.height)
                print(ocr_png('/tmp/big.png'))
