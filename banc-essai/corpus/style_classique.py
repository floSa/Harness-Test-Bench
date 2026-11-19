"""Style « classique » : bandeau de couleur, formulaire à deux colonnes, tableaux simples ;
les essais après réglage sont regroupés dans une case (« a / b / c »)."""
from xml.sax.saxutils import escape

from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer, Table

from base_flux import BaseFlux
from flux import image


class StyleClassique(BaseFlux):
    densite = 2

    def gabarit_doc(self, flux):
        L, H = self.taille
        doc = SimpleDocTemplate(flux, pagesize=self.taille, leftMargin=40, rightMargin=40, topMargin=60,
                                bottomMargin=52, invariant=1,
                                title=self.tr("Rapport d'intervention", "Service report"))
        doc.build = self._avec_cadre(doc.build)
        return doc

    def _avec_cadre(self, build):
        def b(histoire):
            return build(histoire, onFirstPage=self.cadre, onLaterPages=self.cadre)
        return b

    def cadre(self, c, doc):
        L, H = self.taille
        c.saveState()
        c.setFillColorRGB(*self.presta["couleur"])
        c.rect(0, H - 38, L, 38, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(self.gras, 13)
        c.drawString(40, H - 25, self.presta["nom"])
        self.entete_ref(c, L - 40, H - 25, self.police, 9, prefixe=self.tr("Rapport n°", "Report no."))
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.line(40, 42, L - 40, 42)
        self.pied_impression(c, 40, 30)
        c.drawRightString(L - 40, 30, f"Page {c.getPageNumber()}/{self.n_pages}")
        c.restoreState()

    def table_mesures(self, largeur):
        lr = self.lr
        ud = self.u["volume_dose_ml"]
        calcul = self.calcul()
        avec_u = self.place_unite == "colonne"
        tete = [self.tr("Grandeur", "Parameter"), self.tr("Avant réglage", "As found"),
                self.tr("Essais après réglage", "As-left trials")]
        if not calcul:
            tete.append(self.tr("Moyenne après", "Mean as left"))
        tete.append(self.lib("tolerance_ml"))
        if avec_u:
            tete.append(self.tr("Unité", "Unit"))
        ic = {k: i for i, k in enumerate(["G", "A", "E"] + ([] if calcul else ["M"]) + ["TOL"] +
                                          (["U"] if avec_u else []))}
        data, notes = [[self.cel(x, True) for x in tete]], []
        av, ap = self.essais()
        tetes = lr["tetes"]
        for h in range(tetes):
            row = [""] * len(tete)
            libelle = self.lib_u(self.lib("volume_dose_ml"), ud)
            row[ic["G"]] = self.cel(libelle + (f" - {self.tr('tête', 'head')} {h + 1}" if tetes > 1 else ""))
            moy_av = self.moy(lr["essais_avant"][h])
            row[ic["A"]] = self.val_u(moy_av, ud)
            notes.append((len(data), ic["A"], "leurre", "volume_dose_ml", moy_av, "dose avant réglage", "texte"))
            essais = " / ".join(ap[h])
            row[ic["E"]] = self.val_u(essais, ud)
            if calcul:
                for x in ap[h]:
                    notes.append((len(data), ic["E"], "calcul", "volume_dose_ml", x,
                                  "essai après réglage : la valeur attendue est la moyenne des essais", "texte"))
            else:
                if tetes == 1:
                    contenu, nl = self.apres("volume_dose_ml")
                    row[ic["M"]] = contenu
                    self.ajouter_notes(notes, len(data), ic["M"], "volume_dose_ml", nl)
                else:
                    m = self.moy(lr["essais_apres"][h])
                    row[ic["M"]] = self.val_u(m, ud)
                    notes.append((len(data), ic["M"], "leurre", "volume_dose_ml", m, "moyenne d'une seule tête",
                                  "texte"))
            if h == 0:
                if self.emp("tolerance_ml") == "tableau":
                    row[ic["TOL"]] = self.vu("tolerance_ml")
                    notes.append((len(data), ic["TOL"], "verite", "tolerance_ml", self.ecrit_tol, None, "texte"))
                elif self.absent("tolerance_ml"):
                    row[ic["TOL"]] = "n.c."
            if avec_u:
                row[ic["U"]] = ud
            data.append(row)
        if tetes > 1 and not calcul:
            row = [""] * len(tete)
            row[ic["G"]] = self.cel(self.tr("Moyenne générale", "Overall mean"), True)
            contenu, nl = self.apres("volume_dose_ml")
            row[ic["M"]] = contenu
            self.ajouter_notes(notes, len(data), ic["M"], "volume_dose_ml", nl)
            if avec_u:
                row[ic["U"]] = ud
            data.append(row)
        for cle, avant in [("debit_ml_min", self.cv("debit_ml_min", lr["debit_avant"])),
                           ("pression_bar", self.cv("pression_bar", lr["pression_avant"]))]:
            if self.absent(cle) and self.r.random() < 0.5:
                continue
            row = [""] * len(tete)
            row[ic["G"]] = self.cel(self.lib_u(self.lib(cle), self.u[cle]))
            row[ic["A"]] = self.val_u(avant, self.u[cle])
            notes.append((len(data), ic["A"], "leurre", cle, avant, "valeur avant réglage", "texte"))
            contenu, nl = self.apres(cle)
            row[ic["E"]] = contenu
            self.ajouter_notes(notes, len(data), ic["E"], cle, nl)
            if avec_u:
                row[ic["U"]] = self.u[cle]
            data.append(row)
        larg = {"G": 0.25, "A": 0.15, "E": 0.25, "M": 0.13, "TOL": 0.12, "U": 0.08}
        total = sum(larg[k] for k in ic)
        t = Table(data, colWidths=[largeur * larg[k] / total for k in sorted(ic, key=ic.get)])
        t.setStyle(self.style_table())
        return t, notes

    def histoire(self):
        L, _ = self.taille
        lg = L - 80
        S = []
        logos = [[image(self.logo_presta, 150, 49.4), self.P("", "corps")[0]]]
        S.append(Table(logos, colWidths=[lg / 2, lg / 2]))
        S += self.P(self.tr("RAPPORT D'INTERVENTION", "SERVICE REPORT"), "titre", espace=2)
        S += self.P(self.tr("Maintenance et contrôle métrologique d'un équipement de dosage",
                            "Maintenance and metrological check of dosing equipment"), "corps", espace=10)
        lignes, notes = [], []
        entrees = self.entrees_formulaire()
        self.rp.shuffle(entrees) if self.rp.random() < 0.3 else None
        for e in entrees:
            if "img" in e:
                lignes.append([self.cel(e["titre"], True), image(e["img"], 120, 39.5)])
                mode = "image"
            else:
                lignes.append([self.cel(e["titre"], True), self.cel(e["valeur"].replace("\n", " ; "))])
                mode = "texte"
            for role, cle, texte, raison in e.get("notes", []):
                notes.append((len(lignes) - 1, 1, role, cle, texte, raison, mode))
        t = Table(lignes, colWidths=[0.34 * lg, 0.66 * lg])
        t.setStyle(self.style_table(entete=False))
        S += self.T(t, notes, espace=10)
        S += self.synthese_flux(lg)
        S += self.sections_flux(self.paragraphes()[:1])
        S += self.P(self.tr("1. Mesures relevées", "1. Measurements"), "titre", espace=6)
        t, notes = self.table_mesures(lg)
        S += self.T(t, notes, espace=4, mesures=True)
        S += self.note_unites_flux() + self.regle_flux()
        S += self.P(f"<b>{self.tr('Caractéristiques', 'Ratings')}</b>", "corps", espace=3)
        S += self.table_flux(self.t_caracteristiques, min(lg, 380))
        if self.emp("date_intervention") == "tableau":
            S += self.table_flux(self.t_chronologie, lg)
        S += self.sections_flux(self.paragraphes()[1:3])
        S += self.schema_flux(self.tr("2. Schéma de principe", "2. Layout diagram"), lg)
        S += self.zones_flux(lg)
        S += self.P(self.tr("3. Compte rendu", "3. Report"), "titre", espace=6)
        S += self.sections_flux(self.paragraphes()[3:])
        S += self.table_flux(self.t_pieces, lg, titre=self.tr("4. Pièces", "4. Parts"))
        if self.absent("reference_piece"):
            S += self.P(escape(self.texte_sans_piece()))
        S += self.P("5. Observations", "titre", espace=6)
        for html, n in self.phrases_fin():
            S += self.P(html, "corps", n)
        S += self.P(self.tr("6. Conclusion", "6. Conclusion"), "titre", espace=6)
        S += self.statut_flux(lg * 0.6)
        S += self.validation_flux(lg)
        return S
