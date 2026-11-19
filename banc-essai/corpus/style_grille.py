"""Style « grille » : page d'entrée en cases de tailles variées, visas et révisions,
tableau de mesures à entrées multiples. 5 pages."""
from reportlab.lib import colors
from reportlab.platypus import Table

import dessins
import textes
from base import Base
from mise_en_page import cases_a_cocher, grille


class StyleGrille(Base):
    pages_scannables = (1, 2, 4)
    densite = 2

    def pages(self):
        return [self.page_entree, self.page_intervention, self.page_mesures, self.page_schema,
                self.page_conclusion]

    def cadre(self, c, ctx):
        L, H = self.taille
        c.setFillColorRGB(*self.presta["couleur"])
        c.rect(36, H - 34, L - 72, 3, fill=1, stroke=0)
        c.setFont(self.gras, 9)
        c.drawString(36, H - 28, self.presta["nom"])
        c.setFillColorRGB(0, 0, 0)
        if self.emp("reference_rapport") == "formulaire":
            c.setFont(self.police, 8)
            ref = self.v["reference_rapport"]
            suffixe = f"  {self.tr('Indice', 'Revision')} B"
            c.drawRightString(L - 36, H - 28, f"{self.tr('Réf. document', 'Document ref.')} {ref}{suffixe}")
            x1 = L - 36 - c.stringWidth(suffixe, self.police, 8)
            ctx.noter("verite", "reference_rapport", ref,
                      (x1 - c.stringWidth(ref, self.police, 8), H - 31, x1, H - 21))
        c.setFont(self.police, 7.5)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        imp = self.d(self.lr["impression"])
        c.drawString(36, 26, f"{self.tr('Imprimé le', 'Printed on')} {imp}")
        ctx.noter("leurre", "date_validation", imp,
                  (36, 22, 40 + c.stringWidth(f"{self.tr('Imprimé le', 'Printed on')} {imp}", self.police, 7.5), 34),
                  raison="date d'impression")
        c.drawRightString(L - 36, 26, f"Page {ctx.page + 1}/{self.n_pages}")
        c.setFillColorRGB(0, 0, 0)

    # Page 1 ------------------------------------------------------------------------------------

    def _cellule(self, e, poids):
        cl = {"p": poids, "titre": e["titre"], "notes": e.get("notes", [])}
        if "img" in e:
            cl["img"] = e["img"]
        else:
            cl["valeur"] = e["valeur"]
        return cl

    def page_entree(self, c, ctx):
        L, H = self.taille
        rp = self.rp
        c.setFillColorRGB(*self.presta["couleur"])
        c.rect(36, H - 34, L - 72, 3, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        groupes = {}
        for e in self.entrees_formulaire():
            groupes.setdefault(e["groupe"], []).append(e)
        refs = groupes.pop("ref", [])
        bloc_ref = {"p": 1.45, "sous": [self._cellule(e, 1) for e in refs[:2]] +
                    [{"p": 1, "titre": "Page", "valeur": f"1/{self.n_pages}"}]}
        logo = {"p": 1.2, "img": self.logo_presta}
        typ = {"p": 2.2, "valeur": self.tr("RAPPORT D'INTERVENTION\nMaintenance et contrôle métrologique",
                                           "SERVICE REPORT\nMaintenance and metrological check"),
               "taille": 13, "gras": True}
        lignes = [(84, [bloc_ref, typ, logo] if rp.random() < 0.5 else [logo, typ, bloc_ref])]
        ordre = ["lieu", "equipement", "dates"]
        rp.shuffle(ordre)
        for g in ordre:
            es = groupes.get(g, []) + (refs[2:] if g == "dates" else [])
            self.r.shuffle(es)
            lignes.append((46, [self._cellule(e, rp.uniform(0.8, 1.4)) for e in es]))
        bas = [{"p": 2.6, "titre": self.tr("Objet", "Scope"), "taille": 9,
                "valeur": self.tr("Contrôle métrologique et maintenance\npréventive de l'équipement de dosage",
                                  "Metrological check and preventive\nmaintenance of dosing equipment")}]
        if self.emp("statut") == "formulaire":
            k = textes.CODES_STATUT.index(self.v["statut"])
            bas.append({"p": 1.4, "titre": self.lib("statut"),
                        "dessin": cases_a_cocher(textes.STATUTS[self.langue], k, self.police),
                        "notes": [("verite", "statut", textes.STATUTS[self.langue][k], None)]})
        lignes.append((62, bas))
        syn = self.synthese_provisoire()
        if syn:
            cle, lib, txt = syn
            lignes.append((36, [{"p": 1.3, "valeur": self.tr("Synthèse des relevés\n(provisoire)",
                                                             "Readings summary\n(provisional)"),
                                 "taille": 8.5, "gras": True},
                                {"p": 1, "titre": lib, "valeur": f"{txt} {self.u[cle]}",
                                 "notes": [("leurre", cle, txt, "relevé provisoire ; le tableau fait foi")]}]))
        y = grille(c, ctx, 36, H - 44, L - 72, lignes, self.police, self.gras)
        for p in ctx.placements:
            if p["cle"] == "statut" and p["page"] == ctx.page and p["role"] == "verite":
                p["mode"] = "image" if ctx.scan else "trace"
        y = self._visas(c, ctx, y - 14)
        self._revisions(c, ctx, y - 14)

    def _visas(self, c, ctx, y_haut):
        L, _ = self.taille
        v, lr = self.v, self.lr
        tech_ici = self.emp("technicien") == "formulaire" and not self.pd.get("redacteur_autre")
        noms = [v["technicien"] if tech_ici else lr["accompagnant"], lr["verificateur"], lr["approbateur"]]
        dates = [self.d(lr["emission"]), self.d(lr["verification"]), self.d(v["date_validation"])]
        f = (0.92, 0.92, 0.92)
        tete = [{"p": 0.55, "valeur": self.tr("Visas", "Sign-off"), "gras": True, "taille": 8.5, "fond": f}] + \
               [{"p": 1, "valeur": x, "gras": True, "taille": 8.5, "fond": f}
                for x in (self.tr("Rédigé par", "Prepared by"), self.tr("Vérifié par", "Checked by"),
                          self.tr("Approuvé par", "Approved by"))]
        l_nom = [{"p": 0.55, "valeur": self.tr("Nom", "Name"), "taille": 8}]
        for i, nom in enumerate(noms):
            if i == 0 and tech_ici:
                notes = [("verite", "technicien", nom, None)]
            else:
                notes = [("leurre", "technicien", nom,
                          ["rédacteur du rapport", "vérificateur", "approbateur client"][i])]
            l_nom.append({"p": 1, "valeur": nom, "taille": 8.5, "notes": notes})
        l_date = [{"p": 0.55, "valeur": "Date", "taille": 8}]
        for i, dte in enumerate(dates):
            if i < 2:
                l_date.append({"p": 1, "valeur": dte, "taille": 8.5,
                               "notes": [("leurre", "date_validation", dte,
                                          ["date de rédaction", "date de vérification"][i])]})
            elif self.emp("date_validation") == "formulaire":
                l_date.append({"p": 1, "valeur": dte, "taille": 8.5,
                               "notes": [("verite", "date_validation", dte, None)]})
            else:
                l_date.append({"p": 1, "valeur": "", "taille": 8.5})
        l_visa = [{"p": 0.55, "valeur": self.tr("Visa", "Signature"), "taille": 8}]
        for i in range(3):
            if i == 2 and self.emp("date_validation") == "tampon":
                dv = self.d(v["date_validation"], "jj/mm/aaaa" if self.fr else "abr_en")
                img = dessins.tampon([self.tr("APPROUVÉ", "APPROVED"), lr["client"][:24], dv],
                                     (0.15, 0.2, 0.6), f"{self.graine}/{self.doc['id']}/tampon")
                l_visa.append({"p": 1, "img": img, "masque": True,
                               "notes": [("verite", "date_validation", dv, None)]})
            elif i == 2 and self.emp("date_validation") != "formulaire":
                l_visa.append({"p": 1, "valeur": ""})
            else:
                l_visa.append({"p": 1, "img": dessins.signature(f"{self.graine}/{self.doc['id']}/v{i}")})
        return grille(c, ctx, 36, y_haut, L - 72, [(16, tete), (18, l_nom), (18, l_date), (64, l_visa)],
                      self.police, self.gras)

    def _revisions(self, c, ctx, y_haut):
        L, _ = self.taille
        lr = self.lr
        f = (0.92, 0.92, 0.92)
        tete = [{"p": 0.5, "valeur": self.tr("Indice", "Rev."), "gras": True, "taille": 8, "fond": f},
                {"p": 0.9, "valeur": "Date", "gras": True, "taille": 8, "fond": f},
                {"p": 3, "valeur": self.tr("Objet de la révision", "Description"), "gras": True,
                 "taille": 8, "fond": f}]
        ra = [{"p": 0.5, "valeur": "A", "taille": 8}, {"p": 0.9, "valeur": self.d(lr["emission"]), "taille": 8},
              {"p": 3, "valeur": self.tr("Première émission", "First issue"), "taille": 8}]
        rb = [{"p": 0.5, "valeur": "B", "taille": 8},
              {"p": 0.9, "valeur": self.d(lr["verification"]), "taille": 8,
               "notes": [("leurre", "date_validation", self.d(lr["verification"]), "date de la révision B")]},
              {"p": 3, "valeur": self.tr("Correction après relecture", "Corrected after review"), "taille": 8}]
        return grille(c, ctx, 36, y_haut, (L - 72) * 0.62, [(14, tete), (14, ra), (14, rb)],
                      self.police, self.gras)

    # Page 2 ------------------------------------------------------------------------------------

    def page_intervention(self, c, ctx):
        L, _ = self.taille
        self.cadre(c, ctx)
        v, lr = self.v, self.lr
        cur = self.curseur(c, ctx)
        cur.para(self.tr("1. Intervention", "1. Visit"), self.s["titre"], espace=8)
        if self.emp("technicien") == "formulaire":
            interv = (f"{v['technicien']} ({self.tr('responsable', 'lead')})\n"
                      f"{lr['accompagnant']} ({self.tr('accompagnant', 'assistant')})")
            notes = [("verite", "technicien", v["technicien"], None),
                     ("leurre", "technicien", lr["accompagnant"], "accompagnant")]
        else:
            interv = f"{lr['accompagnant']} ({self.tr('accompagnant', 'assistant')})"
            notes = [("leurre", "technicien", lr["accompagnant"], "accompagnant")]
        duree = self.n(lr["duree_h"])
        lignes = [(46, [{"p": 1.6, "titre": self.tr("Intervenants", "Field team"), "valeur": interv,
                         "notes": notes},
                        {"p": 1.2, "titre": self.tr("Demandeur", "Requested by"), "valeur": lr["demandeur"],
                         "notes": [("leurre", "technicien", lr["demandeur"], "demandeur côté client")]},
                        {"p": 1.1, "titre": self.tr("Horaires", "Times"),
                         "valeur": self.tr(f"Arrivée : {lr['arrivee']}\nDurée : {duree} h",
                                           f"Arrival: {lr['arrivee']}\nDuration: {duree} h")}])]
        cur.y = grille(c, ctx, 36, cur.y, L - 72, lignes, self.police, self.gras) - 10
        self.zones_ambigues(cur, ctx)
        if self.emp("date_intervention") == "tableau":
            self.table_chronologie(cur)
        self.sections(cur, self.paragraphes()[:3])

    # Page 3 ------------------------------------------------------------------------------------

    def page_mesures(self, c, ctx):
        L, _ = self.taille
        self.cadre(c, ctx)
        lr = self.lr
        cur = self.curseur(c, ctx)
        cur.para(self.tr("2. Mesures", "2. Measurements"), self.s["titre"], espace=8)
        ud = self.u["volume_dose_ml"]
        calcul = self.calcul()
        avec_u = self.place_unite == "colonne"
        tetes = lr["tetes"]
        cols = ["G"] + (["T"] if tetes > 1 else []) + (["U"] if avec_u else []) + \
               ["A1", "A2", "A3", "P1", "P2", "P3"] + ([] if calcul else ["M"]) + ["TOL"]
        ci = {k: i for i, k in enumerate(cols)}
        h0, h1 = [""] * len(cols), [""] * len(cols)
        h0[ci["G"]] = self.tr("Grandeur", "Parameter")
        if "T" in ci:
            h0[ci["T"]] = self.tr("Tête", "Head")
        if avec_u:
            h0[ci["U"]] = self.tr("Unité", "Unit")
        h0[ci["A1"]], h0[ci["P1"]] = self.tr("Avant réglage", "As found"), self.tr("Après réglage", "As left")
        if not calcul:
            h0[ci["M"]] = self.tr("Moyenne\naprès", "Mean\nas left")
        h0[ci["TOL"]] = self.lib("tolerance_ml")
        for k, e in zip(["A1", "A2", "A3", "P1", "P2", "P3"], ["E1", "E2", "E3"] * 2):
            h1[ci[k]] = e
        data = [h0, h1]
        spans = [("SPAN", (ci["A1"], 0), (ci["A3"], 0)), ("SPAN", (ci["P1"], 0), (ci["P3"], 0))]
        spans += [("SPAN", (ci[k], 0), (ci[k], 1)) for k in ["G", "T", "U", "M", "TOL"] if k in ci]
        notes = []
        av, ap = self.essais()
        r0 = len(data)
        for h in range(tetes):
            row = [""] * len(cols)
            row[ci["G"]] = self.cel(self.lib_u(self.lib("volume_dose_ml"), ud)) if h == 0 else ""
            if "T" in ci:
                row[ci["T"]] = str(h + 1)
            if avec_u:
                row[ci["U"]] = ud
            for j, k in enumerate(["A1", "A2", "A3"]):
                row[ci[k]] = self.val_u(av[h][j], ud)
            for j, k in enumerate(["P1", "P2", "P3"]):
                row[ci[k]] = self.val_u(ap[h][j], ud)
                if calcul:
                    notes.append((len(data), ci[k], "calcul", "volume_dose_ml", ap[h][j],
                                  "essai après réglage : la valeur attendue est la moyenne des essais"))
            if not calcul:
                if tetes == 1:
                    contenu, nl = self.apres("volume_dose_ml")
                    row[ci["M"]] = contenu
                    self.ajouter_notes(notes, len(data), ci["M"], "volume_dose_ml", nl)
                else:
                    m = self.moy(lr["essais_apres"][h])
                    row[ci["M"]] = self.val_u(m, ud)
                    notes.append((len(data), ci["M"], "leurre", "volume_dose_ml", m, "moyenne d'une seule tête"))
            data.append(row)
        if self.emp("tolerance_ml") == "tableau":
            data[r0][ci["TOL"]] = self.vu("tolerance_ml")
            notes.append(((r0, r0 + tetes - 1), ci["TOL"], "verite", "tolerance_ml", self.ecrit_tol, None))
        elif self.absent("tolerance_ml"):
            data[r0][ci["TOL"]] = "n.c."
        spans += [("SPAN", (ci["G"], r0), (ci["G"], r0 + tetes - 1)),
                  ("SPAN", (ci["TOL"], r0), (ci["TOL"], r0 + tetes - 1))]
        if avec_u and tetes > 1:
            spans.append(("SPAN", (ci["U"], r0), (ci["U"], r0 + tetes - 1)))
        if tetes > 1 and not calcul:
            row = [""] * len(cols)
            row[ci["G"]] = self.tr("Moyenne générale", "Overall mean")
            contenu, nl = self.apres("volume_dose_ml")
            row[ci["M"]] = contenu
            self.ajouter_notes(notes, len(data), ci["M"], "volume_dose_ml", nl)
            spans.append(("SPAN", (ci["G"], len(data)), (ci["P3"], len(data))))
            data.append(row)
        for cle, avant in [("debit_ml_min", self.cv("debit_ml_min", lr["debit_avant"])),
                           ("pression_bar", self.cv("pression_bar", lr["pression_avant"])), (None, None)]:
            row = [""] * len(cols)
            unite = self.u[cle] if cle else "°C"
            libelle = self.lib(cle) if cle else self.tr("Température", "Temperature")
            row[ci["G"]] = self.cel(self.lib_u(libelle, unite))
            if avec_u:
                row[ci["U"]] = unite
            if cle:
                row[ci["A1"]] = self.val_u(avant, unite)
                notes.append((len(data), (ci["A1"], ci["A3"]), "leurre", cle, avant, "valeur avant réglage"))
                contenu, nl = self.apres(cle)
                row[ci["P1"]] = contenu
                self.ajouter_notes(notes, len(data), (ci["P1"], ci["P3"]), cle, nl)
            else:
                row[ci["A1"]] = self.val_u(self.n(lr["temperature"] - 1.5, 1), unite)
                row[ci["P1"]] = self.val_u(self.n(lr["temperature"], 1), unite)
            if not calcul:
                row[ci["M"]] = "—"
            row[ci["TOL"]] = "—"
            spans += [("SPAN", (ci["A1"], len(data)), (ci["A3"], len(data))),
                      ("SPAN", (ci["P1"], len(data)), (ci["P3"], len(data)))]
            data.append(row)
        larg = {"G": 96, "T": 28, "U": 38, "M": 64, "TOL": 58}
        reste = (L - 72 - sum(larg[k] for k in cols if k in larg)) / 6
        t = Table(data, colWidths=[larg.get(k, reste) for k in cols])
        t.setStyle(self.style_table(spans + [("BACKGROUND", (0, 1), (-1, 1), colors.Color(0.92, 0.92, 0.92)),
                                             ("ALIGN", (1, 0), (-1, -1), "CENTER")]))
        cur.para(f"<b>{self.tr('Tableau 1 - Relevés', 'Table 1 - Readings')}</b>", self.s["corps"], espace=4)
        cur.table(t, notes, espace=4)
        self.note_unites(cur)
        self.regle_priorite(cur)
        cur.saut(8)
        cur.para(f"<b>{self.tr('Tableau 2 - Caractéristiques', 'Table 2 - Ratings')}</b>", self.s["corps"],
                 espace=4)
        self.caracteristiques(cur)
        self.sections(cur, self.paragraphes()[3:5])

    # Pages 4 et 5 ------------------------------------------------------------------------------

    def page_schema(self, c, ctx):
        self.cadre(c, ctx)
        cur = self.curseur(c, ctx)
        self.schema(cur, ctx, self.tr("3. Schéma de principe", "3. Layout diagram"))
        cur.saut(6)
        self.sections(cur, self.paragraphes()[5:6])

    def page_conclusion(self, c, ctx):
        L, _ = self.taille
        self.cadre(c, ctx)
        cur = self.curseur(c, ctx)
        cur.para(self.tr("4. Pièces", "4. Parts"), self.s["titre"], espace=6)
        self.table_pieces(cur)
        cur.para("5. Observations", self.s["titre"], espace=6)
        for html, n in self.phrases_fin():
            cur.para(html, self.s["corps"], n)
        self.sections(cur, self.paragraphes()[6:])
        cur.para("6. Signatures", self.s["titre"], espace=6)
        self.bloc_validation(c, ctx, 36, cur.y, L - 72, avec_validation=False)
