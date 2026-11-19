"""Style « récit » : texte abondant, formulaire écrit en lignes de texte, long tableau de
mesures (une ligne par essai) qui se coupe souvent entre deux pages. 4 à 6 pages."""
from xml.sax.saxutils import escape

from reportlab.platypus import SimpleDocTemplate, Spacer, Table

from base_flux import BaseFlux
from flux import image


class StyleRecit(BaseFlux):
    tolerance_caracteristiques = True
    densite = 4
    polices = [("Courier", "Courier-Bold"), ("Times-Roman", "Times-Bold")]

    def gabarit_doc(self, flux):
        doc = SimpleDocTemplate(flux, pagesize=self.taille, leftMargin=56, rightMargin=56, topMargin=62,
                                bottomMargin=50, invariant=1,
                                title=self.tr("Compte rendu d'intervention", "Intervention report"))
        build = doc.build
        doc.build = lambda h: build(h, onFirstPage=self.cadre, onLaterPages=self.cadre)
        return doc

    def cadre(self, c, doc):
        L, H = self.taille
        c.saveState()
        c.setFont(self.gras, 10.5)
        c.drawCentredString(L / 2, H - 32, self.presta["nom"].upper())
        c.setLineWidth(0.8)
        c.line(56, H - 40, L - 56, H - 40)
        c.line(56, H - 43, L - 56, H - 43)
        c.setFont(self.police, 7.5)
        self.pied_impression(c, 56, 30, 7.5)
        c.drawRightString(L - 56, 30, self.tr(f"feuillet {c.getPageNumber()}/{self.n_pages}",
                                              f"sheet {c.getPageNumber()}/{self.n_pages}"))
        self.entete_ref(c, L / 2 + 60, 30, self.police, 7.5, aligner_droite=True,
                        prefixe=self.tr("CR", "Report"))
        c.restoreState()

    def mesures(self, largeur):
        lr, fr = self.lr, self.fr
        ud = self.u["volume_dose_ml"]
        av, ap = self.essais()
        tetes = lr["tetes"]
        ld = self.lib("volume_dose_ml")
        rep = self.rp.random() < 0.5
        data = [[self.tr("Grandeur", "Quantity"), self.tr("Valeur", "Value"), self.tr("Unité", "Unit"),
                 "Observation"]]
        notes = []

        def ligne(lib, val, unite, obs="", note=None):
            data.append([self.cel(lib), val, unite if self.place_unite != "cellule" else "", self.cel(obs)])
            if note:
                for n in note:
                    notes.append((len(data) - 1, 1) + n)

        for h in range(tetes):
            suff = f" - {self.tr('tête', 'head')} {h + 1}" if tetes > 1 else ""
            for k in range(3):
                ligne(f"{ld} {self.tr('avant réglage', 'as found')}, {self.tr('essai', 'trial')} {k + 1}{suff}",
                      self.val_u(av[h][k], ud), ud)
        for h in range(tetes):
            suff = f" - {self.tr('tête', 'head')} {h + 1}" if tetes > 1 else ""
            for k in range(3):
                note = None
                if self.calcul():
                    note = [("calcul", "volume_dose_ml", ap[h][k],
                             "essai après réglage : la valeur attendue est la moyenne des essais", "texte")]
                ligne(f"{ld} {self.tr('après réglage', 'as left')}, {self.tr('essai', 'trial')} {k + 1}{suff}",
                      self.val_u(ap[h][k], ud), ud, note=note)
        if not self.calcul():
            contenu, nl = self.apres("volume_dose_ml")
            obs = self.tr("relevé sur schéma", "see diagram") if self.emp("volume_dose_ml") == "schema" else \
                self.tr("moyenne des essais", "mean of trials")
            ligne(f"{ld} {self.tr('moyenne après réglage', 'mean as left')}", contenu, ud, obs,
                  [(role, "volume_dose_ml", t, r, m) for role, t, r, m in nl])
        reste = []
        res, circ = self.n(lr["reservoir_l"]), self.n(lr["circuit_ml"])
        reste += [(self.tr("Capacité du réservoir", "Tank capacity"), res, "L", "",
                   [("leurre", "volume_dose_ml", res, "capacité du réservoir", "texte")]),
                  (self.tr("Volume du circuit", "Line volume"), circ, "ml", "",
                   [("leurre", "volume_dose_ml", circ, "volume du circuit", "texte")]),
                  (self.tr("Température du produit", "Product temperature"), self.n(lr["temperature"], 1), "°C", "",
                   None)]
        for cle, avant in [("debit_ml_min", self.cv("debit_ml_min", lr["debit_avant"])),
                           ("pression_bar", self.cv("pression_bar", lr["pression_avant"]))]:
            reste.append((f"{self.lib(cle)} {self.tr('avant réglage', 'as found')}", self.val_u(avant, self.u[cle]),
                          self.u[cle], "", [("leurre", cle, avant, "valeur avant réglage", "texte")]))
            contenu, nl = self.apres(cle)
            obs = self.tr("relevé sur schéma", "see diagram") if self.emp(cle) == "schema" else ""
            reste.append((f"{self.lib(cle)} {self.tr('après réglage', 'as left')}", contenu, self.u[cle], obs,
                          [(role, cle, t, r, m) for role, t, r, m in nl]))
        self.r.shuffle(reste)
        for lib, val, unite, obs, note in reste:
            ligne(lib, val, unite, obs, note)
        t = Table(data, colWidths=[0.47 * largeur, 0.2 * largeur, 0.1 * largeur, 0.23 * largeur],
                  repeatRows=1 if rep else 0)
        t.setStyle(self.style_table())
        return t, notes

    def histoire(self):
        L, _ = self.taille
        lg = L - 112
        S = [Spacer(1, 6)]
        S += self.P(self.tr("COMPTE RENDU D'INTERVENTION TECHNIQUE", "TECHNICAL INTERVENTION REPORT"), "titre", espace=10)
        S += [image(self.logo_presta, 140, 46), Spacer(1, 10)]
        for e in self.entrees_formulaire():
            if "img" in e:
                S += self.P(escape(f"{e['titre']} :"), "corps", espace=1)
                S += self.Im(e["img"], 110, 36, [n + ("image",) for n in e.get("notes", [])])
            else:
                S += self.P(escape(f"{e['titre']} : {e['valeur'].replace(chr(10), ', ')}"), "corps",
                            e.get("notes", []), espace=3)
        S += self.synthese_flux(lg)
        S += self.P(escape(" ".join(self.remplir(3))), espace=10)
        S += self.P(self.tr("I. CONTEXTE", "I. BACKGROUND"), "titre", espace=6)
        S += self.sections_flux(self.paragraphes()[:2])
        S += self.P(escape(" ".join(self.remplir(2))), espace=8)
        S += self.P(self.tr("II. CONSTAT ET MESURES", "II. FINDINGS AND READINGS"), "titre", espace=6)
        S += self.P(escape(" ".join(self.remplir(2))), espace=8)
        S += self.P(f"<b>{self.tr('Tableau 1 - Relevés de l intervention', 'Table 1 - Readings')}</b>".replace(
            "l intervention", "l'intervention"), "corps", espace=3)
        t, notes = self.mesures(lg)
        S += self.T(t, notes, espace=4, mesures=True)
        S += self.note_unites_flux() + self.regle_flux()
        S += self.P(self.tr("III. ACTIONS RÉALISÉES", "III. WORK PERFORMED"), "titre", espace=6)
        S += self.sections_flux(self.paragraphes()[2:4])
        S += self.zones_flux(lg, empile=False)
        if self.emp("date_intervention") == "tableau":
            S += self.table_flux(self.t_chronologie, lg)
        S += self.table_flux(self.t_caracteristiques, lg * 0.75)
        S += self.schema_flux(self.tr("IV. SCHÉMA DE L'INSTALLATION", "IV. INSTALLATION DIAGRAM"), lg)
        S += self.P(self.tr("V. OBSERVATIONS", "V. OBSERVATIONS"), "titre", espace=6)
        for html, n in self.phrases_fin():
            S += self.P(html, "corps", n)
        S += self.sections_flux(self.paragraphes()[4:])
        S += self.P(f"<b>{self.tr('Pièces', 'Parts')}</b>", "corps", espace=3)
        S += self.table_flux(self.t_pieces, lg)
        if self.absent("reference_piece"):
            S += self.P(escape(self.texte_sans_piece()))
        S += self.P(self.tr("VI. CONCLUSION", "VI. CONCLUSION"), "titre", espace=6)
        S += self.statut_flux(lg * 0.6)
        S += self.validation_flux(lg)
        return S
