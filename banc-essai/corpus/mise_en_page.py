"""Outils de mise en page communs aux styles : enregistrement des valeurs écrites avec leur
cadre, curseur vertical, grille de cases, tableaux, valeur barrée et corrigée à la main.

Coordonnées enregistrées : origine en haut à gauche (convention PyMuPDF), en points.
"""
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Paragraph, Table


class Contexte:
    def __init__(self, hauteur_page):
        self.placements = []
        self.page = 0
        self.scan = False
        self.h = hauteur_page

    def _cadre(self, b):
        x0, y0, x1, y1 = b
        return [round(x0, 1), round(self.h - y1, 1), round(x1, 1), round(self.h - y0, 1)]

    def noter(self, role, cle, texte, bbox, mode="texte", raison=None):
        """role : verite, leurre ou erronee (valeur fausse remplacée par une correction)."""
        self.placements.append({"role": role, "cle": cle, "texte": texte, "page": self.page,
                                "mode": "image" if self.scan else mode, "cadre": self._cadre(bbox),
                                "raison": raison})


class Curseur:
    def __init__(self, c, ctx, x, largeur, y, y_bas=50):
        self.c, self.ctx, self.x, self.l, self.y, self.y_bas = c, ctx, x, largeur, y, y_bas

    def poser(self, objet, espace=6, x=None):
        _, h = objet.wrapOn(self.c, self.l, 3000)
        if self.y - h < self.y_bas:
            raise RuntimeError(f"débordement de page ({self.y - h:.0f} < {self.y_bas})")
        x = self.x if x is None else x
        objet.drawOn(self.c, x, self.y - h)
        bbox = (x, self.y - h, x + self.l, self.y)
        self.y -= h + espace
        return bbox

    def para(self, html, style, notes=(), espace=6):
        """notes : [(role, cle, texte, raison)] écrits dans ce paragraphe."""
        bbox = self.poser(Paragraph(html, style), espace)
        for role, cle, texte, raison in notes:
            self.ctx.noter(role, cle, texte, bbox, raison=raison)
        return bbox

    def table(self, t, notes=(), espace=10, x=None):
        """notes : [(ligne, colonne, role, cle, texte, raison)] ; colonne peut être (c0, c1)."""
        x = self.x if x is None else x
        bbox = self.poser(t, espace, x)
        for ligne, col, role, cle, texte, raison, *mode in notes:
            self.ctx.noter(role, cle, texte, case(t, x, bbox[1], ligne, col), raison=raison,
                           mode=mode[0] if mode else "texte")
        return bbox

    def image(self, img, largeur, hauteur, x=None, espace=8, masque=False):
        if self.y - hauteur < self.y_bas:
            raise RuntimeError("débordement de page (image)")
        x = self.x if x is None else x
        self.c.drawImage(ImageReader(img), x, self.y - hauteur, largeur, hauteur,
                         mask="auto" if masque else None)
        bbox = (x, self.y - hauteur, x + largeur, self.y)
        self.y -= hauteur + espace
        return bbox

    def saut(self, h):
        self.y -= h


def case(t, x, y_bas_table, ligne, col):
    """Cadre d'une case d'un tableau déjà posé (reportlab : y vers le haut)."""
    c0, c1 = (col, col) if isinstance(col, int) else col
    l0, l1 = (ligne, ligne) if isinstance(ligne, int) else ligne
    cols, rows = t._colpositions, t._rowpositions
    return (x + cols[c0], y_bas_table + rows[l1 + 1], x + cols[c1 + 1], y_bas_table + rows[l0])


class Barree(Flowable):
    """Valeur imprimée, barrée, et valeur corrigée à la main à côté (image)."""

    def __init__(self, texte, police, taille, img_manuscrit):
        super().__init__()
        self.texte, self.police, self.taille, self.img = texte, police, taille, img_manuscrit

    def wrap(self, aw, ah):
        return min(aw, 80), self.taille + 22

    def draw(self):
        c = self.canv
        y = 20
        c.setFont(self.police, self.taille)
        c.drawString(0, y, self.texte)
        w = stringWidth(self.texte, self.police, self.taille)
        c.setStrokeColorRGB(0.1, 0.15, 0.55)
        c.setLineWidth(1)
        c.line(-1, y + self.taille * 0.35, w + 1, y + self.taille * 0.35)
        c.drawImage(ImageReader(self.img), 0, 0, 62, 18, mask="auto")


def grille(c, ctx, x, y_haut, largeur, lignes, police, gras, couleur_titre=(0.35, 0.35, 0.35)):
    """Page d'entrée en grille : lignes = [(hauteur, [cellule, ...])].

    cellule : {"p": poids de largeur, "titre": str, "valeur": str | None, "taille": float,
               "img": image, "masque": bool, "dessin": fonction(c, x0, y0, x1, y1),
               "notes": [(role, cle, texte, raison)], "sous": [cellules empilées]}
    Renvoie l'ordonnée du bas de la grille.
    """
    y = y_haut
    for hauteur, cellules in lignes:
        total = sum(cl["p"] for cl in cellules)
        x0 = x
        for cl in cellules:
            w = largeur * cl["p"] / total
            _cellule(c, ctx, x0, y - hauteur, x0 + w, y, cl, police, gras, couleur_titre)
            x0 += w
        y -= hauteur
    return y


def _cellule(c, ctx, x0, y0, x1, y1, cl, police, gras, couleur_titre):
    if "sous" in cl:
        h = (y1 - y0) / len(cl["sous"])
        for i, s in enumerate(cl["sous"]):
            _cellule(c, ctx, x0, y1 - (i + 1) * h, x1, y1 - i * h, s, police, gras, couleur_titre)
        return
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.7)
    if cl.get("fond"):
        c.setFillColorRGB(*cl["fond"])
        c.rect(x0, y0, x1 - x0, y1 - y0, fill=1, stroke=1)
    else:
        c.rect(x0, y0, x1 - x0, y1 - y0, fill=0, stroke=1)
    if cl.get("titre"):
        c.setFillColorRGB(*couleur_titre)
        c.setFont(police, 6.3)
        c.drawString(x0 + 3, y1 - 8.5, cl["titre"].upper())
    c.setFillColorRGB(0, 0, 0)
    if cl.get("img") is not None:
        iw, ih = cl["img"].size
        hmax, wmax = (y1 - y0) - (14 if cl.get("titre") else 6), (x1 - x0) - 8
        k = min(hmax / ih, wmax / iw)
        w, h = iw * k, ih * k
        xi, yi = x0 + (x1 - x0 - w) / 2, y0 + 3
        c.drawImage(ImageReader(cl["img"]), xi, yi, w, h, mask="auto" if cl.get("masque") else None)
        for role, cle, texte, raison in cl.get("notes", []):
            ctx.noter(role, cle, texte, (xi, yi, xi + w, yi + h), mode="image", raison=raison)
        return
    if cl.get("dessin"):
        cl["dessin"](c, x0, y0, x1, y1)
    elif cl.get("valeur") is not None:
        taille = cl.get("taille", 9.5)
        texte = cl["valeur"]
        lignes = texte.split("\n")
        police_v = gras if cl.get("gras") else police
        while taille > 6 and max(stringWidth(l, police_v, taille) for l in lignes) > (x1 - x0) - 8:
            taille -= 0.5
        c.setFont(police_v, taille)
        yy = y1 - (12 if cl.get("titre") else 4) - taille
        for l in lignes:
            c.drawString(x0 + 4, yy, l)
            yy -= taille * 1.25
    for role, cle, texte, raison in cl.get("notes", []):
        ctx.noter(role, cle, texte, (x0, y0, x1, y1), raison=raison)


def cases_a_cocher(options, coche, police, taille=8.5):
    """Dessin de cases à cocher ; la croix n'est qu'un tracé (pas de texte)."""

    def dessin(c, x0, y0, x1, y1):
        y = y1 - 20
        for i, o in enumerate(options):
            c.rect(x0 + 6, y, 8, 8, fill=0, stroke=1)
            if i == coche:
                c.setLineWidth(1.4)
                c.line(x0 + 6, y, x0 + 14, y + 8)
                c.line(x0 + 6, y + 8, x0 + 14, y)
                c.setLineWidth(0.7)
            c.setFont(police, taille)
            c.drawString(x0 + 18, y + 1, o)
            y -= 13

    return dessin


def cellule(texte, style):
    return Paragraph(escape(texte), style)
