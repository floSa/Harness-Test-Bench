"""Style « réservé » (test caché et relance seulement) : A4 paysage, deux colonnes, cartouche
vertical à droite (prestataire, référence, statut, page), tableau de mesures transposé."""
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Table

import textes
from base_flux import BaseFlux
from flux import image
from mise_en_page import cases_a_cocher

COL = 292


class StyleReserve(BaseFlux):
    taille = landscape(A4)
    densite = 3

    def gabarit_doc(self, flux):
        L, H = self.taille
        cadres = [Frame(36, 40, COL, H - 76, id="g", leftPadding=0, rightPadding=0),
                  Frame(36 + COL + 20, 40, COL, H - 76, id="d", leftPadding=0, rightPadding=0)]
        doc = BaseDocTemplate(flux, pagesize=self.taille, invariant=1,
                              title=self.tr("Rapport d'intervention", "Service report"))
        doc.addPageTemplates([PageTemplate(id="p", frames=cadres, onPage=self.cadre)])
        return doc

    def cadre(self, c, doc):
        L, H = self.taille
        x0, x1 = L - 36 - 150, L - 36
        c.saveState()
        c.setLineWidth(0.8)
        c.rect(x0, 36, 150, H - 72, fill=0, stroke=1)
        y = H - 36
        c.drawImage(ImageReader(self.logo_presta), x0 + 6, y - 52, 138, 45)
        y -= 58
        c.line(x0, y, x1, y)
        c.setFont(self.gras, 10)
        for l in self.tr("RAPPORT\nD'INTERVENTION", "SERVICE\nREPORT").split("\n"):
            y -= 13
            c.drawString(x0 + 6, y, l)
        y -= 8
        c.line(x0, y, x1, y)
        c.setFont(self.police, 6.5)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.drawString(x0 + 6, y - 9, self.tr("PRESTATAIRE", "CONTRACTOR"))
        c.setFillColorRGB(0, 0, 0)
        c.setFont(self.police, 8)
        c.drawString(x0 + 6, y - 20, self.presta["nom"][:30])
        y -= 26
        c.line(x0, y, x1, y)
        if self.emp("reference_rapport") == "formulaire":
            c.setFont(self.police, 6.5)
            c.setFillColorRGB(0.35, 0.35, 0.35)
            c.drawString(x0 + 6, y - 9, self.lib("reference_rapport").upper())
            c.setFillColorRGB(0, 0, 0)
            self.entete_ref(c, x0 + 6, y - 20, self.police, 8, aligner_droite=False, prefixe="")
            y -= 26
            c.line(x0, y, x1, y)
        page = c.getPageNumber()
        if page == 1 and self.emp("statut") == "formulaire":
            k = textes.CODES_STATUT.index(self.v["statut"])
            c.setFont(self.police, 6.5)
            c.drawString(x0 + 6, y - 9, self.lib("statut").upper())
            cases_a_cocher(textes.STATUTS[self.langue], k, self.police, 8)(c, x0, y - 52, x1, y - 6)
            self.ctx.page = page - 1
            self.ctx.noter("verite", "statut", textes.STATUTS[self.langue][k], (x0, y - 52, x1, y - 6),
                           mode="trace")
            y -= 56
            c.line(x0, y, x1, y)
        c.setFont(self.police, 8)
        c.drawString(x0 + 6, 58, f"{self.tr('Folio', 'Sheet')} {page}/{self.n_pages}")
        self.pied_impression(c, x0 + 6, 46, 7)
        c.restoreState()

    def fiche(self):
        lignes, notes = [], []
        for e in self.entrees_formulaire():
            titre = f"<font size=6.3 color='#555555'>{escape(e['titre'].upper())}</font>"
            if "img" in e:
                lignes.append([[Paragraph(titre, self.s["case"]), image(e["img"], 100, 33)]])
                mode = "image"
            else:
                val = escape(e["valeur"].replace("\n", ", "))
                lignes.append([Paragraph(f"{titre}<br/>{val}", self.s["case"])])
                mode = "texte"
            for role, cle, texte, raison in e.get("notes", []):
                notes.append((len(lignes) - 1, 0, role, cle, texte, raison, mode))
        # Deux colonnes de cases pour une fiche plus compacte.
        paires = [lignes[i:i + 2] for i in range(0, len(lignes), 2)]
        data = [[p[0][0], p[1][0] if len(p) > 1 else ""] for p in paires]
        notes2 = [(n[0] // 2, n[0] % 2) + n[2:] for n in notes]
        t = Table(data, colWidths=[COL / 2, COL / 2])
        t.setStyle(self.style_table(entete=False))
        return t, notes2

    def mesures(self):
        lr = self.lr
        ud = self.u["volume_dose_ml"]
        av, ap = self.essais()
        tetes = lr["tetes"]
        colonnes = ["", self.lib_u(self.lib("volume_dose_ml"), ud), self.lib_u(self.lib("debit_ml_min"),
                    self.u["debit_ml_min"]), self.lib_u(self.lib("pression_bar"), self.u["pression_bar"])]
        data = [[self.cel(x, True) for x in colonnes]]
        notes = []
        d_av = self.cv("debit_ml_min", lr["debit_avant"])
        p_av = self.cv("pression_bar", lr["pression_avant"])
        data.append([self.tr("Avant réglage", "As found"), self.val_u(self.moy([x for t in lr["essais_avant"]
                                                                                for x in t]), ud),
                     self.val_u(d_av, self.u["debit_ml_min"]), self.val_u(p_av, self.u["pression_bar"])])
        notes += [(1, 2, "leurre", "debit_ml_min", d_av, "valeur avant réglage", "texte"),
                  (1, 3, "leurre", "pression_bar", p_av, "valeur avant réglage", "texte")]
        for h in range(tetes):
            for k in range(3):
                lib = f"E{k + 1}" + (f" T{h + 1}" if tetes > 1 else "")
                data.append([lib, self.val_u(ap[h][k], ud), "·", "·"])
                if self.calcul():
                    notes.append((len(data) - 1, 1, "calcul", "volume_dose_ml", ap[h][k],
                                  "essai après réglage : la valeur attendue est la moyenne des essais", "texte"))
        row = [self.tr("Après réglage", "As left")]
        for j, cle in enumerate(["volume_dose_ml", "debit_ml_min", "pression_bar"], start=1):
            if cle == "volume_dose_ml" and self.calcul():
                row.append("")
                continue
            contenu, nl = self.apres(cle)
            row.append(contenu)
            self.ajouter_notes(notes, len(data), j, cle, nl)
        data.append(row)
        tol = ["Tol."]
        if self.emp("tolerance_ml") == "tableau":
            tol.append(self.vu("tolerance_ml"))
            notes.append((len(data), 1, "verite", "tolerance_ml", self.ecrit_tol, None, "texte"))
        else:
            tol.append("n.c." if self.absent("tolerance_ml") else "")
        data.append(tol + ["", ""])
        t = Table(data, colWidths=[52, 80, 80, 80])
        t.setStyle(self.style_table([("ALIGN", (1, 1), (-1, -1), "CENTER")]))
        return t, notes

    def histoire(self):
        S = []
        S += self.P(self.tr("Fiche de l'intervention", "Visit record"), "titre", espace=6)
        t, n = self.fiche()
        S += self.T(t, n)
        S += self.synthese_flux(COL)
        S += self.sections_flux(self.paragraphes()[:2])
        S.append(PageBreak())
        S += self.P(self.tr("Relevés", "Readings"), "titre", espace=6)
        t, n = self.mesures()
        S += self.T(t, n, espace=4, mesures=True)
        S += self.note_unites_flux() + self.regle_flux()
        S += self.table_flux(self.t_caracteristiques, COL)
        if self.emp("date_intervention") == "tableau":
            S += self.table_flux(self.t_chronologie, COL)
        S += self.sections_flux(self.paragraphes()[2:4])
        S.append(PageBreak())
        S += self.schema_flux(self.tr("Schéma", "Diagram"), COL)
        S += self.zones_flux(COL, empile=True)
        S += self.table_flux(self.t_pieces, COL, titre=self.tr("Pièces", "Parts"))
        if self.absent("reference_piece"):
            S += self.P(escape(self.texte_sans_piece()))
        S += self.sections_flux(self.paragraphes()[4:])
        S += self.P("Observations", "titre", espace=6)
        for html, n in self.phrases_fin():
            S += self.P(html, "corps", n, espace=3)
        S += self.validation_flux(COL, 100)
        return S
