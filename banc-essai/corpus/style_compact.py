"""Style « compact » : lignes clé-valeur sur quatre colonnes, mesures en liste
« paramètre | valeur », texte court. 3 à 4 pages."""
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from base_flux import BaseFlux
from flux import image


class StyleCompact(BaseFlux):
    tolerance_caracteristiques = True
    densite = 1
    polices = [("Helvetica", "Helvetica-Bold"), ("Courier", "Courier-Bold")]

    def gabarit_doc(self, flux):
        doc = SimpleDocTemplate(flux, pagesize=self.taille, leftMargin=34, rightMargin=34, topMargin=50,
                                bottomMargin=44, invariant=1,
                                title=self.tr("Rapport d'intervention", "Service report"))
        build = doc.build
        doc.build = lambda h: build(h, onFirstPage=self.cadre, onLaterPages=self.cadre)
        return doc

    def cadre(self, c, doc):
        L, H = self.taille
        c.saveState()
        c.setFont(self.gras, 8.5)
        titre = f"{self.presta['nom'].upper()}  |  {self.tr('RAPPORT D INTERVENTION', 'SERVICE REPORT')}"
        c.drawString(34, H - 30, titre)
        self.entete_ref(c, L - 34, H - 30, self.police, 8)
        c.setLineWidth(0.6)
        c.line(34, H - 35, L - 34, H - 35)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        self.pied_impression(c, 34, 26, 7)
        c.setFont(self.police, 7)
        c.drawRightString(L - 34, 26, f"{c.getPageNumber()} / {self.n_pages}")
        c.restoreState()

    def style_kv(self):
        return TableStyle([("FONT", (0, 0), (-1, -1), self.police, 8),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.Color(0.7, 0.7, 0.7)),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)])

    def mesures(self, largeur):
        lr = self.lr
        ud = self.u["volume_dose_ml"]
        av, ap = self.essais()
        tetes = lr["tetes"]
        data, notes = [[self.cel(self.tr("Paramètre", "Parameter"), True), self.cel(self.tr("Valeur", "Value"), True)]], []
        sep = self.rp.choice([" ; ", " / ", "  "])
        ld = self.lib("volume_dose_ml")
        for h in range(tetes):
            suff = f" ({self.tr('tête', 'head')} {h + 1})" if tetes > 1 else ""
            data.append([self.cel(f"{ld}, {self.tr('avant réglage', 'as found')}, E1-E3{suff}"),
                         self.val_u(sep.join(av[h]), ud)])
            data.append([self.cel(f"{ld}, {self.tr('après réglage', 'as left')}, E1-E3{suff}"),
                         self.val_u(sep.join(ap[h]), ud)])
            if self.calcul():
                for x in ap[h]:
                    notes.append((len(data) - 1, 1, "calcul", "volume_dose_ml", x,
                                  "essai après réglage : la valeur attendue est la moyenne des essais", "texte"))
            elif tetes > 1:
                m = self.moy(lr["essais_apres"][h])
                data.append([self.cel(f"{ld}, {self.tr('moyenne', 'mean')}{suff}"), self.val_u(m, ud)])
                notes.append((len(data) - 1, 1, "leurre", "volume_dose_ml", m, "moyenne d'une seule tête", "texte"))
        if not self.calcul():
            contenu, nl = self.apres("volume_dose_ml")
            data.append([self.cel(self.lib_u(f"{ld}, {self.tr('moyenne après réglage', 'mean as left')}", ud)),
                         contenu])
            self.ajouter_notes(notes, len(data) - 1, 1, "volume_dose_ml", nl)
        for cle, avant in [("debit_ml_min", self.cv("debit_ml_min", lr["debit_avant"])),
                           ("pression_bar", self.cv("pression_bar", lr["pression_avant"]))]:
            lib = self.lib_u(self.lib(cle), self.u[cle])
            data.append([self.cel(f"{lib}, {self.tr('avant réglage', 'as found')}"), self.val_u(avant, self.u[cle])])
            notes.append((len(data) - 1, 1, "leurre", cle, avant, "valeur avant réglage", "texte"))
            contenu, nl = self.apres(cle)
            data.append([self.cel(f"{lib}, {self.tr('après réglage', 'as left')}"), contenu])
            self.ajouter_notes(notes, len(data) - 1, 1, cle, nl)
        data.append([self.cel(self.tr("Température du produit (°C)", "Product temperature (°C)")),
                     self.n(lr["temperature"], 1)])
        t = Table(data, colWidths=[0.55 * largeur, 0.45 * largeur])
        t.setStyle(self.style_kv())
        return t, notes

    def histoire(self):
        L, _ = self.taille
        lg = L - 68
        S = []
        tete = Table([[self.P(self.tr("<b>RAPPORT D'INTERVENTION</b><br/>Contrôle et maintenance",
                                      "<b>SERVICE REPORT</b><br/>Inspection and maintenance"), "titre")[0],
                       image(self.logo_presta, 120, 39.5)]], colWidths=[lg - 130, 130])
        S += [tete]
        entrees = self.entrees_formulaire()
        lignes, notes, ligne = [], [], []
        for e in entrees:
            if "img" in e:
                cellule, mode = image(e["img"], 95, 31), "image"
            else:
                cellule, mode = self.cel(e["valeur"].replace("\n", ", ")), "texte"
            ligne += [self.cel(e["titre"] + " :", True), cellule]
            for role, cle, texte, raison in e.get("notes", []):
                notes.append((len(lignes), len(ligne) - 1, role, cle, texte, raison, mode))
            if len(ligne) == 4:
                lignes.append(ligne)
                ligne = []
        if ligne:
            lignes.append(ligne + ["", ""])
        t = Table(lignes, colWidths=[0.2 * lg, 0.3 * lg, 0.2 * lg, 0.3 * lg])
        t.setStyle(self.style_kv())
        S += self.T(t, notes, espace=8)
        S += self.synthese_flux(lg)
        S += self.sections_flux(self.paragraphes()[:2])
        S += self.P(self.tr("Mesures", "Readings"), "titre", espace=4)
        t, notes = self.mesures(lg * 0.8)
        S += self.T(t, notes, espace=4, mesures=True)
        S += self.note_unites_flux() + self.regle_flux()
        S += self.table_flux(self.t_caracteristiques, lg * 0.6)
        if self.emp("date_intervention") == "tableau":
            S += self.table_flux(self.t_chronologie, lg)
        S += self.sections_flux(self.paragraphes()[2:4])
        S += self.schema_flux(self.tr("Schéma", "Diagram"), lg * 0.8)
        S += self.zones_flux(lg)
        S += self.table_flux(self.t_pieces, lg, titre=self.tr("Pièces", "Parts"))
        if self.absent("reference_piece"):
            S += self.P(escape(self.texte_sans_piece()))
        S += self.sections_flux(self.paragraphes()[4:])
        S += self.P(self.tr("Notes", "Notes"), "titre", espace=4)
        for html, n in self.phrases_fin():
            S += self.P(html, "corps", n, espace=3)
        S += self.statut_flux(lg * 0.5)
        S += self.validation_flux(lg)
        return S
