"""Images du corpus : logos, signatures, schémas, pages scannées.

Chaque image est dessinée avec reportlab puis tramée par PyMuPDF : le texte qu'elle porte
n'existe donc pas dans la couche texte du PDF final.
"""
import io
import random

import numpy as np
import pymupdf
from PIL import Image, ImageFilter
from reportlab.pdfgen import canvas


def raster(dessin, largeur, hauteur, dpi=200):
    tampon = io.BytesIO()
    c = canvas.Canvas(tampon, pagesize=(largeur, hauteur), invariant=1)
    dessin(c)
    c.showPage()
    c.save()
    page = pymupdf.open(stream=tampon.getvalue(), filetype="pdf")[0]
    pix = page.get_pixmap(dpi=dpi)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


# Logos ---------------------------------------------------------------------------------------

LOGO_L, LOGO_H = 170, 56


def logo(entite):
    nom, coul, style = entite["nom"], entite["couleur"], entite["style"]

    def dessin(c):
        c.setFillColorRGB(*coul)
        c.setStrokeColorRGB(*coul)
        if style == "cercle":
            c.circle(28, 28, 24, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 26)
            c.drawCentredString(28, 19, nom[0])
            c.setFillColorRGB(*coul)
            c.setFont("Helvetica-Bold", 21)
            c.drawString(60, 19, nom.upper())
        elif style == "hexagone":
            p = c.beginPath()
            for i, (x, y) in enumerate([(14, 4), (38, 4), (50, 28), (38, 52), (14, 52), (2, 28)]):
                (p.moveTo if i == 0 else p.lineTo)(x, y)
            p.close()
            c.drawPath(p, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(26, 21, "P")
            c.setFillColorRGB(*coul)
            c.setFont("Helvetica-BoldOblique", 24)
            c.drawString(58, 18, nom.lower())
        elif style == "cartouche":
            c.roundRect(2, 8, 166, 40, 12, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 22)
            c.drawCentredString(85, 20, nom.upper())
        elif style == "goutte":
            c.circle(22, 20, 15, fill=1, stroke=0)
            p = c.beginPath()
            p.moveTo(8, 25)
            p.lineTo(22, 54)
            p.lineTo(36, 25)
            p.close()
            c.drawPath(p, fill=1, stroke=0)
            c.setFont("Times-Bold", 23)
            c.drawString(46, 20, nom.upper())
            c.setFont("Times-Italic", 9)
            c.drawString(47, 8, "precision liquid handling")
        elif style == "vagues":
            c.setLineWidth(3)
            for k in range(3):
                p = c.beginPath()
                p.moveTo(4, 14 + 12 * k)
                p.curveTo(14, 24 + 12 * k, 26, 4 + 12 * k, 40, 14 + 12 * k)
                c.drawPath(p, fill=0, stroke=1)
            c.setFont("Helvetica-Bold", 17)
            c.drawString(48, 30, "TECHMAINT")
            c.setFont("Helvetica", 15)
            c.drawString(48, 12, "LOIRE")
        elif style == "carre":
            c.rect(4, 6, 44, 44, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 30)
            c.drawCentredString(26, 17, "C")
            c.setFillColorRGB(*coul)
            c.setFont("Helvetica-Bold", 22)
            c.drawString(56, 26, "CALIBRO")
            c.setFont("Helvetica", 10)
            c.drawString(57, 12, "SERVICES LTD")
        elif style == "monogramme":
            c.setLineWidth(2)
            c.circle(26, 28, 22, fill=0, stroke=1)
            c.setFont("Times-BoldItalic", 20)
            c.drawCentredString(26, 21, "AB")
            c.setFont("Times-Italic", 17)
            c.drawString(56, 30, "Atelier Bréval")
            c.setFont("Times-Roman", 11)
            c.drawString(57, 14, "maintenance")
        elif style == "losange":
            p = c.beginPath()
            for i, (x, y) in enumerate([(24, 52), (46, 28), (24, 4), (2, 28)]):
                (p.moveTo if i == 0 else p.lineTo)(x, y)
            p.close()
            c.drawPath(p, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 19)
            c.drawString(54, 26, "T E S S A L Y")
            c.setFont("Helvetica", 9)
            c.drawString(55, 12, "FIELD SERVICES")

    return raster(dessin, LOGO_L, LOGO_H)


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
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(265, 182, textes["organe"])
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

def scanner(dessin, largeur, hauteur, graine):
    """Trame une page, la tourne légèrement, ajoute du bruit et la compresse en JPEG."""
    r = random.Random(graine)
    bruit = np.random.default_rng(r.randint(0, 2**32 - 1))
    img = raster(dessin, largeur, hauteur, dpi=150).convert("L")
    angle = r.choice([-1, 1]) * r.uniform(0.4, 1.4)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=255)
    tab = np.asarray(img, dtype=np.float32) * 0.9 + 14
    tab += bruit.normal(0, 13, tab.shape)
    img = Image.fromarray(np.clip(tab, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
    sortie = io.BytesIO()
    img.save(sortie, format="JPEG", quality=55)
    return sortie.getvalue(), angle
