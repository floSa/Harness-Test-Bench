"""Images du corpus : logos, signatures, schémas, pages scannées.

Chaque image est dessinée avec reportlab puis tramée par PyMuPDF : le texte qu'elle porte
n'existe donc pas dans la couche texte du PDF final.
"""
import io
import random

import numpy as np
import pymupdf
from PIL import Image, ImageFilter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


def raster(dessin, largeur, hauteur, dpi=200, alpha=False):
    flux = io.BytesIO()
    c = canvas.Canvas(flux, pagesize=(largeur, hauteur), invariant=1)
    dessin(c)
    c.showPage()
    c.save()
    page = pymupdf.open(stream=flux.getvalue(), filetype="pdf")[0]
    pix = page.get_pixmap(dpi=dpi, alpha=alpha)
    return Image.frombytes("RGBA" if alpha else "RGB", (pix.width, pix.height), pix.samples)


# Logos ---------------------------------------------------------------------------------------

LOGO_L, LOGO_H = 170, 56


def _icone(c, style, coul, initiales):
    c.setFillColorRGB(*coul)
    c.setStrokeColorRGB(*coul)
    if style == "cercle":
        c.circle(26, 28, 23, fill=1, stroke=0)
    elif style == "hexagone":
        p = c.beginPath()
        for i, (x, y) in enumerate([(14, 4), (38, 4), (50, 28), (38, 52), (14, 52), (2, 28)]):
            (p.moveTo if i == 0 else p.lineTo)(x, y)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    elif style == "carre" or style == "cartouche":
        c.roundRect(4, 6, 44, 44, 4 if style == "carre" else 12, fill=1, stroke=0)
    elif style == "losange":
        p = c.beginPath()
        for i, (x, y) in enumerate([(26, 54), (50, 28), (26, 2), (2, 28)]):
            (p.moveTo if i == 0 else p.lineTo)(x, y)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    elif style == "goutte":
        c.circle(26, 20, 16, fill=1, stroke=0)
        p = c.beginPath()
        p.moveTo(11, 26)
        p.lineTo(26, 55)
        p.lineTo(41, 26)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    if style in ("vagues", "monogramme"):
        c.setLineWidth(2.5)
        if style == "vagues":
            for k in range(3):
                p = c.beginPath()
                p.moveTo(4, 14 + 12 * k)
                p.curveTo(14, 24 + 12 * k, 28, 4 + 12 * k, 44, 14 + 12 * k)
                c.drawPath(p, fill=0, stroke=1)
            return
        c.circle(26, 28, 22, fill=0, stroke=1)
        c.setFont("Times-BoldItalic", 18)
        c.drawCentredString(26, 22, initiales)
        return
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20 if len(initiales) == 1 else 15)
    c.drawCentredString(26, 21, initiales)


def logo(entite):
    """Logo générique : une icône et le nom, sur une ou deux lignes."""
    nom, coul, style = entite["nom"], entite["couleur"], entite["style"]
    mots = nom.split()
    initiales = (mots[0][0] + (mots[1][0] if len(mots) > 1 else "")).upper()
    police = {"cercle": "Helvetica-Bold", "hexagone": "Helvetica-BoldOblique",
              "cartouche": "Helvetica-Bold", "goutte": "Times-Bold", "vagues": "Helvetica-Bold",
              "carre": "Helvetica-Bold", "monogramme": "Times-Italic", "losange": "Helvetica"}[style]

    def dessin(c):
        _icone(c, style, coul, initiales)
        c.setFillColorRGB(*coul)
        lignes = [mots[0].upper() if style != "monogramme" else mots[0]]
        if len(mots) > 1:
            lignes.append(" ".join(mots[1:]))
        for i, l in enumerate(lignes):
            taille = 19 if i == 0 else 10
            while stringWidth(l, police, taille) > 112 and taille > 6:
                taille -= 0.5
            c.setFont(police if i == 0 else "Helvetica", taille)
            c.drawString(56, 30 if (i == 0 and len(lignes) > 1) else (12 if i else 21), l)

    return raster(dessin, LOGO_L, LOGO_H)


def tampon(lignes, couleur, graine):
    """Tampon encré, légèrement tourné, fond transparent (RGBA)."""
    r = random.Random(graine)
    angle = r.uniform(-12, 12)

    def dessin(c):
        c.translate(90, 45)
        c.rotate(angle)
        c.setStrokeColorRGB(*couleur)
        c.setFillColorRGB(*couleur)
        c.setLineWidth(2)
        c.roundRect(-82, -34, 164, 68, 8, fill=0, stroke=1)
        c.setLineWidth(0.8)
        c.roundRect(-78, -30, 156, 60, 6, fill=0, stroke=1)
        y = 13
        for i, l in enumerate(lignes):
            c.setFont("Helvetica-Bold", 15 if i == 0 else 12)
            c.drawCentredString(0, y, l)
            y -= 15

    img = raster(dessin, 180, 90, dpi=150, alpha=True)
    return img


def manuscrit(texte, graine, couleur=(0.1, 0.15, 0.55)):
    """Valeur écrite « à la main » (image, fond transparent)."""
    r = random.Random(graine)

    def dessin(c):
        c.translate(4, 8)
        c.rotate(r.uniform(-4, 4))
        c.setFillColorRGB(*couleur)
        c.setFont("Times-Italic", 13)
        c.drawString(0, 0, texte)

    return raster(dessin, 90, 26, dpi=200, alpha=True)


def plaque(lignes):
    """Plaque signalétique métallique (image)."""

    def dessin(c):
        c.setFillColorRGB(0.78, 0.79, 0.80)
        c.roundRect(1, 1, 228, 88, 6, fill=1, stroke=0)
        c.setFillColorRGB(0.45, 0.46, 0.48)
        for x, y in [(9, 9), (221, 9), (9, 81), (221, 81)]:
            c.circle(x, y, 3, fill=1, stroke=0)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        y = 72
        for i, l in enumerate(lignes):
            c.setFont("Helvetica-Bold" if i == 0 else "Courier", 9 if i == 0 else 8)
            c.drawString(18, y, l)
            y -= 12

    return raster(dessin, 230, 90, dpi=150)


# Signature -----------------------------------------------------------------------------------

def signature(graine):
    r = random.Random(graine)

    def dessin(c):
        c.setStrokeColorRGB(0.1, 0.15, 0.5)
        c.setLineWidth(1.3)
        x, y = 8, 18
        p = c.beginPath()
        p.moveTo(x, y)
        for _ in range(r.randint(4, 7)):
            nx = x + r.uniform(12, 26)
            p.curveTo(x + r.uniform(0, 15), y + r.uniform(-14, 22), nx - r.uniform(0, 15),
                      y + r.uniform(-14, 22), nx, 14 + r.uniform(-4, 10))
            x = nx
        c.drawPath(p, fill=0, stroke=1)
        c.line(10, 8, x - r.uniform(0, 30), 10)

    return raster(dessin, 150, 46, dpi=150)


# Schéma --------------------------------------------------------------------------------------

SCHEMA_L, SCHEMA_H = 480, 290


def schema(textes):
    """textes : dict avec reservoir, circuit, organe, et facultativement dose, nominal,
    debit, pression (chaînes complètes « libellé : valeur unité »)."""

    def fleche(c, x1, y1, x2, y2):
        c.line(x1, y1, x2, y2)
        p = c.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(x2 - 7, y2 + 3.5)
        p.lineTo(x2 - 7, y2 - 3.5)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    def repere(c, x, y, n):
        c.setFillColorRGB(1, 1, 1)
        c.circle(x, y, 7, fill=1, stroke=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x, y - 3, str(n))

    def dessin(c):
        c.setStrokeColorRGB(0.15, 0.15, 0.15)
        c.setFillColorRGB(0, 0, 0)
        c.setLineWidth(1.2)
        # Réservoir
        c.setFillColorRGB(0.80, 0.88, 0.96)
        c.rect(30, 140, 110, 66, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.rect(30, 140, 110, 110, fill=0, stroke=1)
        c.setFont("Helvetica", 9)
        c.drawCentredString(85, 236, textes["reservoir_nom"])
        c.drawCentredString(85, 124, textes["reservoir"])
        # Circuit
        c.setLineWidth(3)
        c.line(140, 160, 220, 160)
        c.setLineWidth(1.2)
        c.drawCentredString(180, 168, textes["circuit"])
        # Organe de dosage
        c.rect(220, 120, 90, 80, fill=0, stroke=1)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(265, 184, textes["organe"])
        if "nominal" in textes:
            c.setFont("Helvetica", 8.5)
            c.drawCentredString(265, 140, textes["nominal"])
        # Manomètre
        c.line(265, 200, 265, 232)
        c.circle(265, 250, 18, fill=0, stroke=1)
        c.line(265, 250, 276, 260)
        c.setFont("Helvetica", 9)
        if "pression" in textes:
            c.drawString(290, 246, textes["pression"])
        # Sortie
        c.setLineWidth(3)
        c.line(310, 160, 410, 160)
        c.line(410, 160, 410, 112)
        c.setLineWidth(1.2)
        fleche(c, 330, 172, 385, 172)
        if "debit" in textes:
            c.drawString(318, 180, textes["debit"])
        p = c.beginPath()
        p.moveTo(400, 112)
        p.lineTo(420, 112)
        p.lineTo(410, 96)
        p.close()
        c.drawPath(p, fill=0, stroke=1)
        c.rect(388, 18, 44, 66, fill=0, stroke=1)
        c.setFillColorRGB(0.80, 0.88, 0.96)
        c.rect(389, 19, 42, 34, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        if "dose" in textes:
            c.line(440, 19, 440, 53)
            c.line(436, 19, 444, 19)
            c.line(436, 53, 444, 53)
            c.drawRightString(382, 33, textes["dose"])
        for x, y, n in [(30, 258, 1), (180, 148, 2), (226, 206, 3), (288, 266, 4),
                        (395, 172, 5), (428, 104, 6)]:
            repere(c, x, y, n)

    return raster(dessin, SCHEMA_L, SCHEMA_H, dpi=150)


# Page scannée --------------------------------------------------------------------------------

def degrader(img, graine):
    """Tourne légèrement une page tramée, ajoute du bruit et la compresse en JPEG."""
    r = random.Random(graine)
    bruit = np.random.default_rng(r.randint(0, 2**32 - 1))
    img = img.convert("L")
    angle = r.choice([-1, 1]) * r.uniform(0.4, 1.4)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=255)
    tab = np.asarray(img, dtype=np.float32) * 0.9 + 14
    tab += bruit.normal(0, 13, tab.shape)
    img = Image.fromarray(np.clip(tab, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
    sortie = io.BytesIO()
    img.save(sortie, format="JPEG", quality=55)
    return sortie.getvalue(), angle


def scanner(dessin, largeur, hauteur, graine):
    """Trame une page dessinée, puis la dégrade (voir degrader)."""
    return degrader(raster(dessin, largeur, hauteur, dpi=150), graine)
