# /// script
# requires-python = ">=3.12"
# dependencies = ["pypandoc-binary==1.15", "python-docx==1.2.0", "matplotlib==3.10.7"]
# ///
"""Construit la version SharePoint du kit : un guide Word et une archive des scripts.

    uv run livrables/word/construire.py

Source unique : livrables/word/introduction.md et livrables/kit-harnais-securise/guide/*.md.
Sorties dans livrables/sharepoint/ :
  « Sécuriser un harnais d'agent - guide.docx »
  « Sécuriser un harnais d'agent - scripts.zip »
"""
import re
import tempfile
import zipfile
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
KIT = ICI.parent / "kit-harnais-securise"
SORTIE = ICI.parent / "sharepoint"
NOM = "Sécuriser un harnais d'agent"
BLEU = RGBColor(0x1F, 0x3A, 0x5F)


def schema(chemin):
    fig, ax = plt.subplots(figsize=(11.5, 4.2), dpi=200)
    ax.set_xlim(0, 11.9)
    ax.set_ylim(0, 4.2)
    ax.axis("off")

    def boite(x, y, l, h, texte, fond="#e8eef6", bord="#1f3a5f", gras=None, style="-"):
        ax.add_patch(FancyBboxPatch((x - l / 2, y - h / 2), l, h, boxstyle="round,pad=0.05,rounding_size=0.12",
                                    facecolor=fond, edgecolor=bord, linewidth=1.4, linestyle=style))
        lignes = texte.split("\n")
        ax.text(x, y + (len(lignes) - 1) * 0.11, lignes[0], ha="center", va="center", fontsize=11,
                fontweight="bold", color="#1f3a5f")
        for i, ligne in enumerate(lignes[1:], 1):
            ax.text(x, y + (len(lignes) - 1) * 0.11 - i * 0.24, ligne, ha="center", va="center", fontsize=9)

    def fleche(x1, y1, x2, y2, texte, dy, dx=0.0):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                     color="#1f3a5f", linewidth=1.3))
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, texte, ha="center", va="center", fontsize=8.5, color="#333333")

    ax.add_patch(FancyBboxPatch((0.15, 0.2), 3.1, 3.8, boxstyle="round,pad=0.05,rounding_size=0.2",
                                facecolor="#f7f7f7", edgecolor="#888888", linewidth=1.2, linestyle="--"))
    ax.text(1.7, 3.72, "Pièce fermée : conteneur ou cage,\nsans accès à Internet", ha="center", va="center",
            fontsize=9, color="#555555")
    boite(1.7, 1.95, 2.7, 2.6, "Harnais\nvoit seulement espace/\nclé locale sans valeur")
    boite(6.4, 3.1, 2.7, 1.1, "Relais\nseul à détenir la clé du portail\nplafonne et journalise")
    boite(6.4, 0.95, 2.7, 0.9, "Filtre\nquelques sites autorisés")
    boite(10.3, 3.1, 2.3, 0.8, "Portail IAG\nAPI compatible OpenAI", fond="#ffffff")
    boite(10.3, 0.95, 2.3, 0.8, "PyPI, npm\nregistres de paquets", fond="#ffffff")
    fleche(3.05, 3.1, 5.0, 3.1, "appels au modèle", 0.2, 0.2)
    fleche(3.05, 0.95, 5.0, 0.95, "pip, npm", 0.2, 0.2)
    fleche(7.8, 3.1, 9.1, 3.1, "HTTPS + clé", 0.2)
    fleche(7.8, 0.95, 9.1, 0.95, "HTTPS", 0.2)
    fig.savefig(chemin, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def assembler():
    fichiers = sorted((KIT / "guide").glob("0*.md"))
    titres = {}
    for f in fichiers:
        m = re.match(r"# (\d+)\. (.+)", f.read_text().splitlines()[0])
        titres[m.group(1)] = m.group(2)

    def renvoi(m):
        return f"chapitre {m.group(1)} ({titres[m.group(1)]})"

    morceaux = [(ICI / "introduction.md").read_text()]
    for f in fichiers:
        texte = f.read_text()
        texte = re.sub(r"^\[Retour au sommaire\]\(\.\./README\.md\)\n\n", "", texte, flags=re.M)
        texte = re.sub(r"\[[^\]]*\]\((?:\.\./)?(?:guide/)?0(\d)-[a-z\-]+\.md\)", renvoi, texte)
        morceaux.append(texte)
    return "\n\n".join(morceaux)


def bordures(tableau):
    proprietes = tableau._tbl.tblPr
    cadre = OxmlElement("w:tblBorders")
    for cote in ("top", "left", "bottom", "right", "insideH", "insideV"):
        trait = OxmlElement(f"w:{cote}")
        trait.set(qn("w:val"), "single")
        trait.set(qn("w:sz"), "4")
        trait.set(qn("w:color"), "A6A6A6")
        cadre.append(trait)
    proprietes.append(cadre)


def fond(element, couleur):
    ombre = OxmlElement("w:shd")
    ombre.set(qn("w:val"), "clear")
    ombre.set(qn("w:fill"), couleur)
    element.append(ombre)


def mettre_en_forme(chemin):
    doc = Document(chemin)
    styles = doc.styles
    for nom in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if nom in [s.name for s in styles]:
            styles[nom].font.name = "Calibri"
            styles[nom].font.size = Pt(11)
    for nom, taille in (("Title", 24), ("Subtitle", 14), ("Heading 1", 18), ("Heading 2", 14), ("Heading 3", 12)):
        if nom in [s.name for s in styles]:
            styles[nom].font.name = "Calibri"
            styles[nom].font.size = Pt(taille)
            styles[nom].font.color.rgb = BLEU
    if "Heading 1" in [s.name for s in styles]:
        styles["Heading 1"].paragraph_format.page_break_before = True
    if "Source Code" in [s.name for s in styles]:
        code = styles["Source Code"]
        code.font.name = "Consolas"
        code.font.size = Pt(9)
        fond(code.element.get_or_add_pPr(), "F2F2F2")
    if "Verbatim Char" in [s.name for s in styles]:
        styles["Verbatim Char"].font.name = "Consolas"
        styles["Verbatim Char"].font.size = Pt(9.5)
    for tableau in doc.tables:
        bordures(tableau)
        for i, rangee in enumerate(tableau.rows):
            rangee._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))   # pas de ligne coupée entre deux pages
            for cellule in rangee.cells:
                if i == 0:
                    fond(cellule._tc.get_or_add_tcPr(), "DCE6F1")
                for paragraphe in cellule.paragraphs:
                    for morceau in paragraphe.runs:
                        morceau.font.size = Pt(9)
                        if i == 0:
                            morceau.font.bold = True
    # Le premier titre de niveau 1 suit la page de titre : saut de page déjà donné par le style.
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.core_properties.title = NOM
    doc.save(chemin)


def archive_scripts(chemin):
    lisezmoi = (f"Scripts du kit « {NOM} ».\n\n"
                f"Le mode d'emploi est le document Word « {NOM} - guide », au même emplacement.\n"
                "Décompresser ce dossier sur le poste (Linux ou WSL2), puis suivre le chapitre du mode choisi.\n")
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo("kit-harnais-securise/LISEZMOI.txt", date_time=(2026, 11, 23, 0, 0, 0))
        info.external_attr = 0o644 << 16
        z.writestr(info, lisezmoi)
        for f in sorted(KIT.rglob("*")):
            rel = f.relative_to(KIT)
            if f.is_dir() or rel.parts[0] in ("guide",) or rel.name in ("README.md", ".env", ".verrou"):
                continue
            if "__pycache__" in rel.parts:
                continue
            if rel.parts[0] in ("espace", "journaux", "certificats") and f.name != ".gitkeep":
                continue
            if rel.parts[:2] in (("sans-conteneur", "harnais"), ("sans-conteneur", "maison")):
                continue
            info = zipfile.ZipInfo(f"kit-harnais-securise/{rel.as_posix()}", date_time=(2026, 11, 23, 0, 0, 0))
            info.external_attr = (0o755 if f.stat().st_mode & 0o111 else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())


def main():
    SORTIE.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        schema(tmp / "schema.png")
        (tmp / "guide.md").write_text(assembler())
        docx = SORTIE / f"{NOM} - guide.docx"
        pypandoc.convert_file(str(tmp / "guide.md"), "docx", format="markdown", outputfile=str(docx),
                              extra_args=[f"--resource-path={tmp}",
                                          "--metadata", f"title={NOM}",
                                          "--metadata", "subtitle=Guide d'installation et d'utilisation du kit, avec le portail IAG"])
        mettre_en_forme(docx)
        (tmp / "schema.png").replace(SORTIE.parent / "word" / "schema.png")
    archive_scripts(SORTIE / f"{NOM} - scripts.zip")
    for f in sorted(SORTIE.iterdir()):
        print(f"{f.name} : {f.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    main()
