# /// script
# requires-python = ">=3.12"
# dependencies = ["pypandoc-binary==1.15", "python-docx==1.2.0", "matplotlib==3.10.7"]
# ///
"""Construit le document Word « Sécuriser un harnais d'agent ».

    uv run livrables/word/construire.py

Source : livrables/word/guide.md. Les blocs {{code:<fichier>:<langage>}} y sont remplacés par le contenu
des fichiers de livrables/word/code/, ceux qui ont été essayés. Sortie : livrables/sharepoint/.
"""
import re
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import pypandoc
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ICI = Path(__file__).resolve().parent
SORTIE = ICI.parent / "sharepoint"
NOM = "Sécuriser un harnais d'agent"
BLEU = RGBColor(0x1F, 0x3A, 0x5F)


def schema(chemin):
    fig, ax = plt.subplots(figsize=(11, 3.0), dpi=200)
    ax.set_xlim(0, 11.6)
    ax.set_ylim(0, 3.0)
    ax.axis("off")

    def boite(x, y, l, h, lignes, fond="#e8eef6"):
        ax.add_patch(FancyBboxPatch((x - l / 2, y - h / 2), l, h, boxstyle="round,pad=0.05,rounding_size=0.12",
                                    facecolor=fond, edgecolor="#1f3a5f", linewidth=1.4))
        haut = y + (len(lignes) - 1) * 0.13
        ax.text(x, haut, lignes[0], ha="center", va="center", fontsize=11, fontweight="bold", color="#1f3a5f")
        for i, ligne in enumerate(lignes[1:], 1):
            ax.text(x, haut - i * 0.26, ligne, ha="center", va="center", fontsize=9)

    def fleche(x1, x2, y, texte):
        ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=14,
                                     color="#1f3a5f", linewidth=1.3))
        ax.text((x1 + x2) / 2, y + 0.22, texte, ha="center", va="center", fontsize=8.5, color="#333333")

    ax.add_patch(FancyBboxPatch((0.15, 0.2), 3.3, 2.6, boxstyle="round,pad=0.05,rounding_size=0.2",
                                facecolor="#f7f7f7", edgecolor="#888888", linewidth=1.2, linestyle="--"))
    ax.text(1.8, 2.5, "Environnement fermé : conteneur ou cage", ha="center", va="center", fontsize=9,
            color="#555555")
    ax.text(1.8, 0.45, "ni Internet, ni reste du poste", ha="center", va="center", fontsize=8.5, color="#555555")
    boite(1.8, 1.45, 2.8, 1.2, ["Harnais", "voit seulement espace/", "clé locale sans valeur ailleurs"])
    boite(6.0, 1.45, 2.8, 1.2, ["Relais", "seul à connaître la vraie clé", "relaie l'appel au modèle"])
    boite(10.0, 1.45, 2.4, 0.9, ["Portail IAG", "API compatible OpenAI"], fond="#ffffff")
    fleche(3.2, 4.55, 1.45, "clé locale")
    fleche(7.45, 8.75, 1.45, "vraie clé")
    fig.savefig(chemin, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def assembler():
    texte = (ICI / "guide.md").read_text()

    def code(m):
        contenu = (ICI / "code" / m.group(1)).read_text().rstrip("\n")
        return f"```{m.group(2)}\n{contenu}\n```"

    return re.sub(r"\{\{code:([^:}]+):([^}]+)\}\}", code, texte)


def bordures(tableau):
    cadre = OxmlElement("w:tblBorders")
    for cote in ("top", "left", "bottom", "right", "insideH", "insideV"):
        trait = OxmlElement(f"w:{cote}")
        trait.set(qn("w:val"), "single")
        trait.set(qn("w:sz"), "4")
        trait.set(qn("w:color"), "A6A6A6")
        cadre.append(trait)
    tableau._tbl.tblPr.append(cadre)


def fond(element, couleur):
    ombre = OxmlElement("w:shd")
    ombre.set(qn("w:val"), "clear")
    ombre.set(qn("w:fill"), couleur)
    element.append(ombre)


def mettre_en_forme(chemin):
    doc = Document(chemin)
    noms = [s.name for s in doc.styles]
    for nom in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if nom in noms:
            doc.styles[nom].font.name = "Calibri"
            doc.styles[nom].font.size = Pt(11)
    for nom, taille in (("Title", 24), ("Subtitle", 13), ("Heading 1", 16), ("Heading 2", 13)):
        if nom in noms:
            doc.styles[nom].font.name = "Calibri"
            doc.styles[nom].font.size = Pt(taille)
            doc.styles[nom].font.color.rgb = BLEU
    if "Heading 1" in noms:
        doc.styles["Heading 1"].paragraph_format.space_before = Pt(18)
    if "Source Code" in noms:
        doc.styles["Source Code"].font.name = "Consolas"
        doc.styles["Source Code"].font.size = Pt(8.5)
        fond(doc.styles["Source Code"].element.get_or_add_pPr(), "F2F2F2")
    if "Verbatim Char" in noms:
        doc.styles["Verbatim Char"].font.name = "Consolas"
        doc.styles["Verbatim Char"].font.size = Pt(9.5)
    for tableau in doc.tables:
        bordures(tableau)
        for i, rangee in enumerate(tableau.rows):
            rangee._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))   # pas de ligne coupée entre deux pages
            for cellule in rangee.cells:
                if i == 0:
                    fond(cellule._tc.get_or_add_tcPr(), "DCE6F1")
                for paragraphe in cellule.paragraphs:
                    for morceau in paragraphe.runs:
                        morceau.font.size = Pt(9.5)
                        morceau.font.bold = morceau.font.bold or i == 0
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.core_properties.title = NOM
    doc.save(chemin)


def main():
    SORTIE.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        schema(tmp / "schema.png")
        (tmp / "guide.md").write_text(assembler())
        docx = SORTIE / f"{NOM}.docx"
        pypandoc.convert_file(str(tmp / "guide.md"), "docx", format="markdown", outputfile=str(docx),
                              extra_args=[f"--resource-path={tmp}", "--metadata", f"title={NOM}",
                                          "--metadata", "subtitle=Mode d'emploi, avec le portail IAG"])
        mettre_en_forme(docx)
        (tmp / "schema.png").replace(ICI / "schema.png")
    print(f"{docx.name} : {docx.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    main()
