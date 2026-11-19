"""Mise en page en flux (platypus) avec enregistrement des valeurs écrites.

Chaque flowable enveloppé dans `Enregistre` note, au moment où il est dessiné, le cadre absolu
de ses valeurs (paragraphe entier, case de tableau, image) et la page. Un tableau enregistré
peut se couper entre deux pages : ses notes suivent leurs lignes.
"""
import io

import pymupdf
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Image, Table

import dessins


class Enregistre(Flowable):
    def __init__(self, interne, ctx, notes=(), notes_cases=(), decalage=0, ref=None):
        """notes : [(role, cle, texte, raison, mode)] pour tout le flowable ;
        notes_cases : [(ligne, colonne, role, cle, texte, raison, mode)] pour un tableau.
        ref : dictionnaire partagé entre morceaux d'un tableau coupé (pages occupées)."""
        super().__init__()
        self.interne, self.ctx = interne, ctx
        self.notes, self.notes_cases = list(notes), list(notes_cases)
        self.decalage = decalage
        self.ref = ref if ref is not None else {"pages": set()}

    def wrap(self, aw, ah):
        self.w, self.h = self.interne.wrap(aw, ah)
        return self.w, self.h

    def split(self, aw, ah):
        if not isinstance(self.interne, Table):
            return []
        morceaux = self.interne.split(aw, ah)
        if len(morceaux) < 2:
            return []
        t1, t2 = morceaux[0], morceaux[1]
        k = len(t1._cellvalues)
        rep = self.interne.repeatRows if isinstance(self.interne.repeatRows, int) else 0
        n1 = [n for n in self.notes_cases if self._ligne(n) < k]
        n2 = [(self._ligne(n) - k + rep,) + tuple(n[1:]) for n in self.notes_cases if self._ligne(n) >= k]
        return [Enregistre(t1, self.ctx, self.notes, n1, ref=self.ref),
                Enregistre(t2, self.ctx, [], n2, ref=self.ref)]

    @staticmethod
    def _ligne(n):
        return n[0] if isinstance(n[0], int) else n[0][0]

    def draw(self):
        self.interne.drawOn(self.canv, 0, 0)
        x, y = self.canv.absolutePosition(0, 0)
        page = self.canv.getPageNumber() - 1
        self.ref["pages"].add(page)
        self.ctx.page = page
        for role, cle, texte, raison, *mode in self.notes:
            self.ctx.noter(role, cle, texte, (x, y, x + self.w, y + self.h), raison=raison,
                           mode=mode[0] if mode else "texte")
        if self.notes_cases:
            t = self.interne
            cols, rows = t._colpositions, t._rowpositions
            for ligne, col, role, cle, texte, raison, *mode in self.notes_cases:
                c0, c1 = (col, col) if isinstance(col, int) else col
                l0, l1 = (ligne, ligne) if isinstance(ligne, int) else ligne
                bbox = (x + cols[c0], y + rows[l1 + 1], x + cols[c1 + 1], y + rows[l0])
                self.ctx.noter(role, cle, texte, bbox, raison=raison, mode=mode[0] if mode else "texte")


class Dessin(Flowable):
    """Bloc dessiné à la main : fonction(c, ctx_decale, largeur, hauteur), coordonnées locales."""

    def __init__(self, largeur, hauteur, fonction, ctx):
        super().__init__()
        self.l, self.h, self.f, self.ctx = largeur, hauteur, fonction, ctx

    def wrap(self, aw, ah):
        return self.l, self.h

    def draw(self):
        x, y = self.canv.absolutePosition(0, 0)
        self.ctx.page = self.canv.getPageNumber() - 1
        self.f(self.canv, ContexteDecale(self.ctx, x, y), self.l, self.h)


class ContexteDecale:
    def __init__(self, ctx, dx, dy):
        self.ctx, self.dx, self.dy = ctx, dx, dy

    def noter(self, role, cle, texte, bbox, mode="texte", raison=None):
        x0, y0, x1, y1 = bbox
        self.ctx.noter(role, cle, texte, (x0 + self.dx, y0 + self.dy, x1 + self.dx, y1 + self.dy),
                       mode=mode, raison=raison)


def image(pil, largeur, hauteur):
    flux = io.BytesIO()
    pil.save(flux, format="PNG")
    flux.seek(0)
    return Image(flux, largeur, hauteur)


def remplacer_par_scan(pdf, page, graine):
    """Remplace une page par sa version tramée, bruitée et tournée (image seule)."""
    src = pymupdf.open(stream=pdf, filetype="pdf")
    rect = src[page].rect
    pix = src[page].get_pixmap(dpi=150)
    from PIL import Image as PILImage
    img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
    jpeg, _ = dessins.degrader(img, graine)
    out = pymupdf.open()
    for i in range(len(src)):
        if i == page:
            p = out.new_page(width=rect.width, height=rect.height)
            p.insert_image(rect, stream=jpeg)
        else:
            out.insert_pdf(src, from_page=i, to_page=i)
    out.set_metadata(src.metadata)
    return out.tobytes(garbage=3, deflate=True, no_new_id=True)
