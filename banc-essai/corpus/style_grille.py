"""Style « grille » : page d'entrée découpée en cases de tailles variées (visas, révisions),
tableau de mesures à entrées multiples, zones ambiguës, tampon et signatures.

La disposition des cases dépend du prestataire (même prestataire, même gabarit).
"""
import io
import random
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

import dessins
import formats
from mise_en_page import Barree, Contexte, Curseur, cases_a_cocher, grille

STATUTS = {"fr": ["Conforme", "Non conforme", "À revoir"],
           "en": ["Compliant", "Non-compliant", "To be reviewed"]}
CODES_STATUT = ["conforme", "non_conforme", "a_revoir"]
T = {  # textes fixes
    "fr": {"type": "RAPPORT D'INTERVENTION", "sous": "Maintenance et contrôle métrologique",
           "ref": "Réf. document", "indice": "Indice", "page": "Page", "client": "Client",
           "siege": "Siège", "install": "Installation", "inventaire": "N° d'inventaire",
           "demande": "Date de la demande", "emission": "Date d'émission", "commande": "N° de commande",
           "affaire": "N° d'affaire", "objet": "Objet", "redige": "Rédigé par",
           "verifie": "Vérifié par", "approuve": "Approuvé par", "nom": "Nom", "date": "Date",
           "visa": "Visa", "visas": "Visas", "revisions": "Indice", "rev_objet": "Objet de la révision",
           "rev_a": "Première émission", "rev_b": "Correction après relecture",
           "annule": "Annule et remplace", "imprime": "Imprimé le",
           "objet_txt": "Contrôle métrologique et maintenance\npréventive de l'équipement de dosage",
           "synthese": "Synthèse des relevés", "provisoire": "(relevés provisoires)"},
    "en": {"type": "SERVICE REPORT", "sous": "Maintenance and metrological check",
           "ref": "Document ref.", "indice": "Revision", "page": "Page", "client": "Customer",
           "siege": "Head office", "install": "Installation", "inventaire": "Asset no.",
           "demande": "Request date", "emission": "Issue date", "commande": "PO number",
           "affaire": "Job no.", "objet": "Scope", "redige": "Prepared by",
           "verifie": "Checked by", "approuve": "Approved by", "nom": "Name", "date": "Date",
           "visa": "Signature", "visas": "Sign-off", "revisions": "Rev.", "rev_objet": "Description",
           "rev_a": "First issue", "rev_b": "Corrected after review",
           "annule": "Supersedes", "imprime": "Printed on",
           "objet_txt": "Metrological check and preventive\nmaintenance of dosing equipment",
           "synthese": "Readings summary", "provisoire": "(provisional readings)"},
}


class StyleGrille:
    taille = A4

    def __init__(self, doc, graine):
        self.doc, self.graine = doc, graine
        self.v, self.lr, self.p = doc["valeurs"], doc["leurres"], doc["pieges"]
        self.langue = doc["langue"]
        self.fr = self.langue == "fr"
        self.t = T[self.langue]
        self.presta, self.marque = doc["prestataire"], doc["marque"]
        self.r = random.Random(f"{graine}/{doc['id']}/rendu")
        # Choix propres au prestataire : identiques dans tous ses documents.
        rp = random.Random(self.presta["graine_page"])
        self.rp = rp
        self.police, self.gras = rp.choice([("Helvetica", "Helvetica-Bold"),
                                            ("Times-Roman", "Times-Bold")])
        self.style_nb = doc["pieges_doc"].get("style_nombres") or rp.choice(
            ["fr", "fr_colle", "de"] if self.fr else ["en", "en_colle", "ch"])
        self.forme_date = doc["pieges_doc"].get("forme_date") or rp.choice(
            formats.FORMES_DATE[self.langue])
        self.place_unite = doc["pieges_doc"].get("place_unite") or rp.choice(
            ["colonne", "entete", "cellule", "note"])
        self.ordre_lignes = rp.sample([0, 1, 2], 3)
        self.logo_droite = rp.random() < 0.5
        self.poids = {k: rp.uniform(0.75, 1.3) for k in range(40)}
        base = ParagraphStyle("b", fontName=self.police, fontSize=9.5, leading=12.5)
        self.s = {"corps": base,
                  "titre": ParagraphStyle("t", parent=base, fontName=self.gras, fontSize=12.5,
                                          leading=16),
                  "petit": ParagraphStyle("p", parent=base, fontSize=8, leading=10),
                  "case": ParagraphStyle("c", parent=base, fontSize=8, leading=9.6)}
        self.logo_presta = dessins.logo(self.presta)
        self.logo_marque = dessins.logo(self.marque)
        self.verite = {}
        self._preparer()

    # Valeurs écrites et vérité ----------------------------------------------------------------

    def n(self, x, min_dec=0):
        return formats.nombre(x, self.style_nb, min_dec)

    def d(self, iso, forme=None):
        return formats.date(iso, forme or self.forme_date)

    def absent(self, cle):
        return "champ_absent" in self.p[cle]

    def ou(self, cle):
        return None if self.absent(cle) else self.doc["emplacements"][cle]

    def lib(self, cle):
        return self.doc["libelles"][cle]

    def _preparer(self):
        """Fixe l'écriture de chaque valeur numérique et en déduit la vérité."""
        u = self.doc["unites"]
        self.u = {}
        self.ecrit = {}
        for cle, grandeur in [("volume_dose_ml", "volume"), ("volume_nominal_ml", "volume"),
                              ("tolerance_ml", "volume"), ("debit_ml_min", "debit"),
                              ("pression_bar", "pression")]:
            aff, ver = formats.convertir(self.v[cle], grandeur, u[cle])
            self.u[cle] = u[cle]
            self.ecrit[cle] = self.n(aff, 1 if cle == "pression_bar" else 0)
            self.verite[cle] = ver
        # Facteur de la dose pour écrire essais et leurres dans la même unité.
        self.f_dose = formats.UNITES["volume"][u["volume_dose_ml"]]
        if "tolerance_en_pourcent" in self.p["tolerance_ml"]:
            self.ecrit_tol = f"± {self.n(self.lr['pct'])} %"
            self.verite["tolerance_ml"] = round(self.verite["volume_nominal_ml"] * self.lr["pct"] / 100, 6)
        else:
            self.ecrit_tol = f"± {self.ecrit['tolerance_ml']}"
        for cle in ["machine", "constructeur", "numero_serie", "site", "reference_rapport",
                    "date_intervention", "date_validation", "reference_piece", "technicien",
                    "statut"]:
            self.verite[cle] = self.v[cle]
        for cle in self.verite:
            if self.absent(cle):
                self.verite[cle] = None
        # Valeur barrée : faute de frappe imprimée, valeur juste écrite à la main.
        self.faute = {}
        for cle in ["volume_dose_ml", "debit_ml_min", "pression_bar"]:
            if "valeur_barree" in self.p[cle] or "erratum" in self.p[cle]:
                x = self.v[cle]
                f = formats.UNITES["volume" if cle == "volume_dose_ml" else
                                   ("debit" if cle == "debit_ml_min" else "pression")][self.u[cle]]
                faux = x * (1 + self.r.choice([-1, 1]) * self.r.uniform(0.07, 0.15))
                pas = self.lr["pas"] if cle == "volume_dose_ml" else (0.1 if cle == "pression_bar" else 1)
                faux = round(round(faux / pas) * pas, 6)
                self.faute[cle] = self.n(round(faux / f, 6) if f in formats.FACTEURS_DECIMAUX
                                         else round(faux / f, 2))

    def cv(self, cle, x):
        """Leurre de débit ou de pression écrit dans l'unité d'affichage de la clé."""
        g = "debit" if cle == "debit_ml_min" else "pression"
        aff, _ = formats.convertir(x, g, self.u[cle])
        return self.n(aff, 1 if (cle == "pression_bar" and self.u[cle] == "bar") else 0)

    def vol(self, x_ml):
        """Volume leurre écrit dans l'unité de la dose."""
        return self.n(round(x_ml / self.f_dose, 6))

    # Rendu -------------------------------------------------------------------------------------

    def pages(self):
        return [self.page_entree, self.page_intervention, self.page_mesures, self.page_schema,
                self.page_conclusion]

    def rendre(self):
        fonctions = self.pages()
        self.n_pages = len(fonctions)
        L, H = self.taille
        ctx = Contexte(H)
        page_scan = None
        if self.doc["pieges_doc"].get("scan"):
            page_scan = self.doc["pieges_doc"].get("page_scan", self.r.choice([1, 2, 4]))
        flux = io.BytesIO()
        c = canvas.Canvas(flux, pagesize=self.taille, invariant=1)
        c.setTitle(self.t["type"].title())
        for i, f in enumerate(fonctions):
            ctx.page = i
            if i == page_scan:
                ctx.scan = True
                jpeg, _ = dessins.scanner(lambda cc: f(cc, ctx), L, H,
                                          f"{self.graine}/{self.doc['id']}/scan")
                ctx.scan = False
                c.drawImage(ImageReader(io.BytesIO(jpeg)), 0, 0, L, H)
            else:
                f(c, ctx)
            c.showPage()
        c.save()
        return flux.getvalue(), ctx.placements, page_scan

    def cadre(self, c, ctx):
        L, H = self.taille
        c.setFillColorRGB(*self.presta["couleur"])
        c.rect(36, H - 34, L - 72, 3, fill=1, stroke=0)
        c.setFont(self.gras, 9)
        c.drawString(36, H - 28, self.presta["nom"])
        c.setFillColorRGB(0, 0, 0)
        c.setFont(self.police, 8)
        ref = self.v["reference_rapport"]
        txt = f"{self.t['ref']} {ref}  {self.t['indice']} B"
        c.drawRightString(L - 36, H - 28, txt)
        x1 = L - 36 - c.stringWidth(f"  {self.t['indice']} B", self.police, 8)
        ctx.noter("verite", "reference_rapport", ref,
                  (x1 - c.stringWidth(ref, self.police, 8), H - 31, x1, H - 21))
        c.setFont(self.police, 7.5)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        imp = self.d(self.lr["impression"])
        c.drawString(36, 26, f"{self.t['imprime']} {imp}")
        ctx.noter("leurre", "date_validation", imp, (36, 22, 140, 34),
                  raison="date d'impression")
        c.drawRightString(L - 36, 26, f"{self.t['page']} {ctx.page + 1}/{self.n_pages}")
        c.setFillColorRGB(0, 0, 0)

    def w(self, k):
        return self.poids[k]

    # Page 1 : page d'entrée en grille ---------------------------------------------------------

    def page_entree(self, c, ctx):
        L, H = self.taille
        t, v, lr = self.t, self.v, self.lr
        c.setFillColorRGB(*self.presta["couleur"])
        c.rect(36, H - 34, L - 72, 3, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        logo = {"p": 1.25, "img": self.logo_presta}
        typ = {"p": 2.3, "valeur": f"{t['type']}\n{t['sous']}", "taille": 13, "gras": True}
        ref = v["reference_rapport"]
        sous_ref = [{"p": 1, "titre": t["ref"], "valeur": ref,
                     "notes": [("verite", "reference_rapport", ref, None)]},
                    {"p": 1, "titre": t["indice"], "valeur": "B"},
                    {"p": 1, "titre": t["page"], "valeur": f"1/{self.n_pages}"}]
        if "version_remplacee" in self.p["reference_rapport"]:
            sous_ref[1] = {"p": 1, "titre": f"{t['indice']} / {t['annule']}",
                           "valeur": f"B  /  {lr['ref_ancienne']}",
                           "notes": [("leurre", "reference_rapport", lr["ref_ancienne"],
                                      "référence de la version annulée")]}
        bloc_ref = {"p": 1.45, "sous": sous_ref}
        ligne_a = [bloc_ref, typ, logo] if self.logo_droite else [logo, typ, bloc_ref]

        def champ(cle, titre_defaut=None, valeur=None, k=0, p=1.0):
            titre = self.lib(cle)
            if self.absent(cle) or self.ou(cle) not in ("grille", "visas"):
                return {"p": p * self.w(k), "titre": titre,
                        "valeur": {"numero_serie": "illisible" if self.fr else "unreadable"}.get(
                            cle, "—") if self.absent(cle) else "—"}
            val = valeur if valeur is not None else v[cle]
            return {"p": p * self.w(k), "titre": titre, "valeur": val,
                    "notes": [("verite", cle, val, None)]}

        client = {"p": 1.4 * self.w(1), "titre": t["client"],
                  "valeur": f"{lr['client']}\n{t['siege']} : {lr['ville_siege']}",
                  "notes": [("leurre", "site", lr["ville_siege"], "ville du siège du client")]}
        site = champ("site", k=2, p=1.4)
        install = {"p": 1.0 * self.w(3), "titre": t["install"],
                   "valeur": f"{lr['ligne']}\n{lr['type_machine']}"}
        machine = champ("machine", k=4, p=1.3)
        if self.doc["pieges_doc"].get("logo_seul"):
            cons = {"p": 1.25 * self.w(5), "titre": self.lib("constructeur"),
                    "img": self.logo_marque,
                    "notes": [("verite", "constructeur", v["constructeur"], None)]}
        else:
            cons = champ("constructeur", k=5, p=1.1)
        serie = champ("numero_serie", k=6, p=1.2)
        inv = {"p": 0.9 * self.w(7), "titre": t["inventaire"], "valeur": lr["inventaire"],
               "notes": [("leurre", "numero_serie", lr["inventaire"], "n° d'inventaire du client")]}
        di = self.d(v["date_intervention"])
        dates = [{"p": self.w(8), "titre": t["demande"], "valeur": self.d(lr["demande"]),
                  "notes": [("leurre", "date_intervention", self.d(lr["demande"]), "date de la demande")]},
                 champ("date_intervention", valeur=di, k=9),
                 {"p": self.w(10), "titre": t["emission"], "valeur": self.d(lr["emission"]),
                  "notes": [("leurre", "date_validation", self.d(lr["emission"]), "date d'émission")]},
                 {"p": self.w(11), "titre": t["commande"], "valeur": lr["commande"],
                  "notes": [("leurre", "reference_rapport", lr["commande"], "n° de commande")]},
                 {"p": self.w(12), "titre": t["affaire"], "valeur": lr["affaire"],
                  "notes": [("leurre", "reference_rapport", lr["affaire"], "n° d'affaire")]}]
        if self.ou("date_intervention") != "grille":
            dates[1] = {"p": self.w(9), "titre": self.lib("date_intervention"), "valeur": "—"}
        lignes_mid = [[client, site, install], [machine, cons, serie, inv], dates]
        for ligne in lignes_mid:
            self.rp.shuffle(ligne)
        hauteurs = [44, 46, 40]
        corps = [(hauteurs[i], lignes_mid[i]) for i in self.ordre_lignes]
        coche = CODES_STATUT.index(v["statut"])
        statut = {"p": 1.4, "titre": self.lib("statut"),
                  "dessin": cases_a_cocher(STATUTS[self.langue], coche, self.police),
                  "notes": [("verite", "statut", STATUTS[self.langue][coche], None)]}
        objet = {"p": 2.6, "titre": t["objet"], "valeur": t["objet_txt"], "taille": 9}
        lignes = [(82, ligne_a)] + corps + [(62, [objet, statut])]
        if "conflit_regle" in self.p["debit_ml_min"]:
            lignes.append((36, self._synthese(provisoire=True)))
        y = grille(c, ctx, 36, H - 44, L - 72, lignes, self.police, self.gras)
        y = self._visas(c, ctx, y - 14)
        self._revisions(c, ctx, y - 14)
        self._registrer_cases(ctx)

    def _registrer_cases(self, ctx):
        for p in ctx.placements:
            if p["cle"] == "statut" and p["page"] == ctx.page and p["role"] == "verite":
                p["mode"] = "image" if ctx.scan else "trace"

    def _synthese(self, provisoire):
        lr, t = self.lr, self.t
        faux = self.cv("debit_ml_min", self.lr["debit_avant"])
        cells = [{"p": 1.2, "titre": "", "valeur": f"{t['synthese']}\n{t['provisoire']}",
                  "taille": 8.5, "gras": True},
                 {"p": 1, "titre": self.lib("volume_dose_ml"),
                  "valeur": f"{self.vol(lr['essais_apres'][0][0])} {self.u['volume_dose_ml']}",
                  "notes": [("leurre", "volume_dose_ml", self.vol(lr["essais_apres"][0][0]),
                             "relevé provisoire de la synthèse (premier essai)")]},
                 {"p": 1, "titre": self.lib("debit_ml_min"),
                  "valeur": f"{faux} {self.u['debit_ml_min']}",
                  "notes": [("leurre", "debit_ml_min", faux,
                             "relevé provisoire de la synthèse ; le tableau de mesures fait foi")]}]
        return cells

    def _visas(self, c, ctx, y_haut):
        L, _ = self.taille
        t, v, lr = self.t, self.v, self.lr
        redac = (lr["accompagnant"] if self.doc["pieges_doc"].get("redacteur_autre")
                 or self.absent("technicien") else v["technicien"])
        noms = [redac, lr["verificateur"], lr["approbateur"]]
        dates = [self.d(lr["emission"]), self.d(lr["verification"]), self.d(v["date_validation"])]
        tete = [{"p": 0.55, "valeur": t["visas"], "gras": True, "taille": 8.5, "fond": (0.92, 0.92, 0.92)}] + \
               [{"p": 1, "valeur": x, "gras": True, "taille": 8.5, "fond": (0.92, 0.92, 0.92)}
                for x in (t["redige"], t["verifie"], t["approuve"])]
        l_nom = [{"p": 0.55, "valeur": t["nom"], "taille": 8}]
        for i, nom in enumerate(noms):
            if i == 0 and nom == v["technicien"] and not self.absent("technicien"):
                notes = [("verite", "technicien", nom, None)]
            elif i == 0:
                notes = [("leurre", "technicien", nom, "rédacteur du rapport, pas l'intervenant responsable")]
            else:
                notes = [("leurre", "technicien", nom, "vérificateur" if i == 1 else "approbateur client")]
            l_nom.append({"p": 1, "valeur": nom, "taille": 8.5, "notes": notes})
        l_date = [{"p": 0.55, "valeur": t["date"], "taille": 8}]
        raisons = ["date de rédaction", "date de vérification"]
        for i, dte in enumerate(dates):
            if i == 2:
                if self.absent("date_validation") or self.ou("date_validation") == "tampon":
                    l_date.append({"p": 1, "valeur": "", "taille": 8.5})
                else:
                    l_date.append({"p": 1, "valeur": dte, "taille": 8.5,
                                   "notes": [("verite", "date_validation", dte, None)]})
            else:
                l_date.append({"p": 1, "valeur": dte, "taille": 8.5,
                               "notes": [("leurre", "date_validation", dte, raisons[i])]})
        l_visa = [{"p": 0.55, "valeur": t["visa"], "taille": 8}]
        for i in range(3):
            if i == 2 and self.ou("date_validation") == "tampon":
                img = dessins.tampon([("APPROUVÉ" if self.fr else "APPROVED"),
                                      lr["client"][:26], self.d(v["date_validation"], "jj/mm/aaaa"
                                                                if self.fr else "abr_en")],
                                     (0.15, 0.2, 0.6), f"{self.graine}/{self.doc['id']}/tampon")
                l_visa.append({"p": 1, "img": img, "masque": True,
                               "notes": [("verite", "date_validation",
                                          self.d(v["date_validation"], "jj/mm/aaaa" if self.fr else "abr_en"),
                                          None)]})
            elif i == 2 and self.absent("date_validation"):
                l_visa.append({"p": 1, "valeur": ""})
            else:
                l_visa.append({"p": 1, "img": dessins.signature(f"{self.graine}/{self.doc['id']}/v{i}")})
        return grille(c, ctx, 36, y_haut, L - 72, [(16, tete), (18, l_nom), (18, l_date),
                                                    (64, l_visa)], self.police, self.gras)

    def _revisions(self, c, ctx, y_haut):
        L, _ = self.taille
        t, lr = self.t, self.lr
        tete = [{"p": 0.5, "valeur": t["revisions"], "gras": True, "taille": 8, "fond": (0.92,) * 3},
                {"p": 0.9, "valeur": t["date"], "gras": True, "taille": 8, "fond": (0.92,) * 3},
                {"p": 3, "valeur": t["rev_objet"], "gras": True, "taille": 8, "fond": (0.92,) * 3}]
        ra = [{"p": 0.5, "valeur": "A", "taille": 8},
              {"p": 0.9, "valeur": self.d(lr["emission"]), "taille": 8},
              {"p": 3, "valeur": t["rev_a"], "taille": 8}]
        rb = [{"p": 0.5, "valeur": "B", "taille": 8},
              {"p": 0.9, "valeur": self.d(lr["verification"]), "taille": 8,
               "notes": [("leurre", "date_validation", self.d(lr["verification"]),
                          "date de la révision B")]},
              {"p": 3, "valeur": t["rev_b"], "taille": 8}]
        return grille(c, ctx, 36, y_haut, (L - 72) * 0.62, [(14, tete), (14, ra), (14, rb)],
                      self.police, self.gras)

    # Page 2 : intervention --------------------------------------------------------------------

    def page_intervention(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        v, lr, fr = self.v, self.lr, self.fr
        cur = Curseur(c, ctx, 36, L - 72, H - 50)
        cur.para("1. Intervention" if fr else "1. Visit", self.s["titre"], espace=8)
        if self.absent("technicien"):
            interv = f"{lr['accompagnant']} ({'accompagnant' if fr else 'assistant'})"
            notes = [("leurre", "technicien", lr["accompagnant"], "accompagnant")]
        else:
            interv = (f"{v['technicien']} ({'responsable' if fr else 'lead'})\n"
                      f"{lr['accompagnant']} ({'accompagnant' if fr else 'assistant'})")
            notes = [("verite", "technicien", v["technicien"], None),
                     ("leurre", "technicien", lr["accompagnant"], "accompagnant")]
        duree = self.n(lr["duree_h"])
        lignes = [(46, [{"p": 1.6, "titre": "Intervenants" if fr else "Field team", "valeur": interv,
                         "notes": notes},
                        {"p": 1.2, "titre": "Demandeur" if fr else "Requested by",
                         "valeur": lr["demandeur"],
                         "notes": [("leurre", "technicien", lr["demandeur"], "demandeur côté client")]},
                        {"p": 1.1, "titre": "Horaires" if fr else "Times",
                         "valeur": (f"Arrivée : {lr['arrivee']}\nDurée : {duree} h" if fr else
                                    f"Arrival: {lr['arrivee']}\nDuration: {duree} h")}]),
                  (40, [{"p": 2, "titre": "Motif" if fr else "Reason",
                         "valeur": (f"Dérive signalée le {self.d(lr['incident'])}" if fr else
                                    f"Drift reported on {self.d(lr['incident'])}"),
                         "notes": [("leurre", "date_intervention", self.d(lr["incident"]),
                                    "date de l'incident signalé")]},
                        {"p": 1.4, "titre": "Contrat" if fr else "Contract",
                         "valeur": lr["commande"]}])]
        y = grille(c, ctx, 36, cur.y, L - 72, lignes, self.police, self.gras)
        cur.y = y - 12
        # Plaque du moteur et instruments : zones ambiguës.
        m = lr["moteur"]
        plaque = dessins.plaque([f"{m['marque'].upper()}  MOTOR", f"TYPE {m['type']}",
                                 f"N° {m['serie']}", f"{self.n(m['kw'])} kW  {m['trmin']} min-1",
                                 f"{m['tension']}  50 Hz  IP55"])
        y0 = cur.y
        bb = cur.image(plaque, 200, 78, espace=4)
        for cle, txt, raison in [("constructeur", m["marque"], "marque du moteur"),
                                 ("numero_serie", m["serie"], "n° de série du moteur"),
                                 ("machine", m["type"], "type du moteur")]:
            ctx.noter("leurre", cle, txt, bb, mode="image", raison=raison)
        cur.para("Plaque du moteur d'entraînement (relevée sur site)." if fr else
                 "Drive motor rating plate (recorded on site).", self.s["petit"])
        # Instruments à droite de la plaque.
        lignes_i = [["Instrument", "Marque" if fr else "Make", "N° série" if fr else "Serial",
                     "Étalonné le" if fr else "Calibrated"]]
        notes_i = []
        for k, ins in enumerate(lr["instruments"], start=1):
            dte = self.d(ins["etalonnage"])
            lignes_i.append([Paragraph(escape(ins["nom"]), self.s["case"]), ins["marque"],
                             ins["serie"], dte])
            notes_i += [(k, 1, "leurre", "constructeur", ins["marque"], "marque d'un instrument de mesure"),
                        (k, 2, "leurre", "numero_serie", ins["serie"], "n° de série d'un instrument"),
                        (k, 3, "leurre", "date_validation", dte, "date d'étalonnage d'un instrument")]
        ti = Table(lignes_i, colWidths=[78, 56, 56, 86])
        ti.setStyle(self._style_table())
        sauve = cur.y
        cur.y = y0
        cur.l = 276
        cur.table(ti, notes_i, x=L - 36 - 276)
        cur.l = L - 72
        cur.y = min(sauve, cur.y) - 6
        cur.para("Déroulement" if fr else "Work performed", self.s["titre"], espace=6)
        for html, notes in self.recit()[0]:
            cur.para(html, self.s["corps"], notes)

    # Récit -------------------------------------------------------------------------------------

    def recit(self):
        v, lr, fr = self.v, self.lr, self.fr
        out = []
        av = self.vol(lr["avant"])
        ud = self.u["volume_dose_ml"]
        out.append(((f"Intervention à la demande de {escape(lr['demandeur'])} ({escape(lr['client'])}) "
                     f"sur l'équipement de la {lr['ligne'].lower()}." if fr else
                     f"Call-out requested by {escape(lr['demandeur'])} ({escape(lr['client'])}) "
                     f"on the {lr['ligne'].lower()} equipment."), []))
        out.append(((f"À l'arrivée, la dose moyenne relevée était de {av} {ud}, hors tolérance ; "
                     f"l'équipement a été consigné, démonté et nettoyé." if fr else
                     f"On arrival the average dose read {av} {ud}, out of tolerance; the equipment "
                     f"was locked out, dismantled and cleaned."),
                    [("leurre", "volume_dose_ml", av, "dose avant réglage")]))
        for cle in ["date_intervention", "site", "numero_serie"]:
            if self.ou(cle) == "recit":
                val = self.d(v[cle], "long_fr" if fr else "long_en") if cle.startswith("date") else v[cle]
                phr = {("date_intervention", True): f"Le technicien est intervenu le {val}.",
                       ("date_intervention", False): f"The technician attended on {val}.",
                       ("site", True): f"L'équipement est installé sur le site client : {val}.",
                       ("site", False): f"The equipment is installed at the customer site: {val}.",
                       ("numero_serie", True): f"Le numéro de série relevé sur la plaque de la machine "
                                               f"est {val}.",
                       ("numero_serie", False): f"The serial number read on the machine plate is {val}."}
                out.append((escape(phr[(cle, fr)]), [("verite", cle, val, None)]))
        vo = lr["voisin"]
        dv, pv = self.cv("debit_ml_min", vo["debit"]), self.n(vo["pression"], 1)
        out.append(((f"Le convoyeur amont {vo['modele']} (débit {dv} {self.u['debit_ml_min']}, "
                     f"pression {pv} bar) n'est pas concerné par cette intervention." if fr else
                     f"The upstream conveyor {vo['modele']} (flow {dv} {self.u['debit_ml_min']}, "
                     f"pressure {pv} bar) is outside the scope of this visit."),
                    [("leurre", "machine", vo["modele"], "équipement voisin"),
                     ("leurre", "debit_ml_min", dv, "débit de l'équipement voisin"),
                     ("leurre", "pression_bar", pv, "pression de l'équipement voisin")]))
        out.append(((f"Le réseau d'air comprimé de l'atelier est à {self.n(lr['air'], 1)} bar." if fr else
                     f"The workshop compressed-air network runs at {self.n(lr['air'], 1)} bar."),
                    [("leurre", "pression_bar", self.n(lr["air"], 1), "réseau d'air de l'atelier")]))
        suite = []
        for cle in ["volume_nominal_ml", "debit_ml_min", "pression_bar", "volume_dose_ml"]:
            if self.ou(cle) == "recit":
                s = f"{self.ecrit[cle]} {self.u[cle]}"
                suite.append(((f"Après réglage, {self.lib(cle).lower()} : {s}." if fr else
                             f"As left, {self.lib(cle).lower()}: {s}."),
                            [("verite", cle, s, None)]))
        for cle in ["volume_dose_ml", "debit_ml_min", "pression_bar"]:
            if "erratum" in self.p[cle]:
                juste = f"{self.ecrit[cle]} {self.u[cle]}"
                faux = f"{self.faute[cle]} {self.u[cle]}"
                suite.append(((f"Erratum : dans le tableau des mesures, lire {juste} au lieu de {faux} "
                             f"pour {self.lib(cle).lower()}." if fr else
                             f"Erratum: in the measurement table, read {juste} instead of {faux} "
                             f"for {self.lib(cle).lower()}."), [("verite", cle, juste, None)]))
        phrases = {
            ("conforme", True): "Après réglage, les mesures sont dans la tolérance.",
            ("non_conforme", True): "Malgré le réglage, la dose reste hors tolérance ; une pièce est "
                                    "en commande.",
            ("a_revoir", True): "Une légère fuite reste à surveiller ; une nouvelle visite est à "
                                "programmer.",
            ("conforme", False): "As left, readings are within tolerance.",
            ("non_conforme", False): "Despite adjustment the dose remains out of tolerance; a part "
                                     "is on order.",
            ("a_revoir", False): "A slight leak is to be monitored; a follow-up visit is to be "
                                 "scheduled.",
        }
        suite.append((phrases[(v["statut"], fr)], []))
        pv = self.d(lr["prochaine"])
        suite.append(((f"Prochaine visite préventive : {pv}." if fr else f"Next preventive visit: {pv}."),
                       [("leurre", "date_intervention", pv, "date de la prochaine visite")]))
        return out, suite

    # Page 3 : mesures -------------------------------------------------------------------------

    def _style_table(self, extra=()):
        return TableStyle([("FONT", (0, 0), (-1, -1), self.police, 8),
                           ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
                           ("FONT", (0, 0), (-1, 0), self.gras, 8)] + list(extra))

    def _val(self, texte, unite):
        return f"{texte} {unite}" if self.place_unite == "cellule" and texte not in ("—", "") else texte

    def _lib_u(self, libelle, unite):
        return f"{libelle} ({unite})" if self.place_unite == "entete" else libelle

    def page_mesures(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        v, lr, fr, p = self.v, self.lr, self.fr, self.p
        cur = Curseur(c, ctx, 36, L - 72, H - 50)
        cur.para("2. Mesures" if fr else "2. Measurements", self.s["titre"], espace=8)
        ud = self.u["volume_dose_ml"]
        calcul = "moyenne_a_calculer" in p["volume_dose_ml"]
        avec_unite = self.place_unite == "colonne"
        tetes = lr["tetes"]
        tete_col = tetes > 1
        E = ["E1", "E2", "E3"]
        cols = ["G"] + (["T"] if tete_col else []) + (["U"] if avec_unite else []) + \
               ["A1", "A2", "A3", "P1", "P2", "P3"] + ([] if calcul else ["M"]) + ["TOL"]
        ci = {k: i for i, k in enumerate(cols)}
        h0 = ["" for _ in cols]
        h1 = ["" for _ in cols]
        h0[ci["G"]] = "Grandeur" if fr else "Parameter"
        if tete_col:
            h0[ci["T"]] = "Tête" if fr else "Head"
        if avec_unite:
            h0[ci["U"]] = "Unité" if fr else "Unit"
        h0[ci["A1"]] = "Avant réglage" if fr else "As found"
        h0[ci["P1"]] = "Après réglage" if fr else "As left"
        if not calcul:
            h0[ci["M"]] = "Moyenne\naprès" if fr else "Mean\nas left"
        h0[ci["TOL"]] = self.lib("tolerance_ml")
        for k, e in zip(["A1", "A2", "A3"], E):
            h1[ci[k]] = e
        for k, e in zip(["P1", "P2", "P3"], E):
            h1[ci[k]] = e
        data = [h0, h1]
        spans = [("SPAN", (ci["A1"], 0), (ci["A3"], 0)), ("SPAN", (ci["P1"], 0), (ci["P3"], 0))]
        for k in ["G", "T", "U", "M", "TOL"]:
            if k in ci:
                spans.append(("SPAN", (ci[k], 0), (ci[k], 1)))
        notes = []
        lib_dose = self._lib_u(self.lib("volume_dose_ml"), ud)
        r0 = len(data)
        for h in range(tetes):
            row = ["" for _ in cols]
            row[ci["G"]] = Paragraph(escape(lib_dose), self.s["case"]) if h == 0 else ""
            if tete_col:
                row[ci["T"]] = str(h + 1)
            if avec_unite:
                row[ci["U"]] = ud
            for j, k in enumerate(["A1", "A2", "A3"]):
                row[ci[k]] = self._val(self.vol(lr["essais_avant"][h][j]), ud)
            for j, k in enumerate(["P1", "P2", "P3"]):
                txt = self.vol(lr["essais_apres"][h][j])
                row[ci[k]] = self._val(txt, ud)
                if calcul:
                    notes.append((len(data), ci[k], "calcul", "volume_dose_ml", txt,
                                  "essai après réglage : la valeur attendue est la moyenne des essais"))
            if not calcul:
                m = self.vol(sum(lr["essais_apres"][h]) / 3)
                if tetes == 1:
                    if "valeur_barree" in p["volume_dose_ml"]:
                        img = dessins.manuscrit(self._val(self.ecrit["volume_dose_ml"], ud),
                                                f"{self.graine}/{self.doc['id']}/main")
                        row[ci["M"]] = Barree(self._val(self.faute["volume_dose_ml"], ud), self.police,
                                              8, img)
                        notes.append((len(data), ci["M"], "erronee", "volume_dose_ml",
                                      self.faute["volume_dose_ml"], "valeur imprimée barrée"))
                        notes.append((len(data), ci["M"], "verite", "volume_dose_ml",
                                      self.ecrit["volume_dose_ml"], None, "image"))
                    elif self.ou("volume_dose_ml") == "tableau":
                        row[ci["M"]] = self._val(m, ud)
                        notes.append((len(data), ci["M"], "verite", "volume_dose_ml", m, None))
                    else:
                        row[ci["M"]] = "—"
                else:
                    row[ci["M"]] = self._val(m, ud)
                    notes.append((len(data), ci["M"], "leurre", "volume_dose_ml", m,
                                  "moyenne d'une seule tête"))
            data.append(row)
        if self.ou("tolerance_ml") == "tableau":
            data[r0][ci["TOL"]] = self._val(self.ecrit_tol, "" if "%" in self.ecrit_tol else
                                            self.u["tolerance_ml"])
            notes.append(((r0, r0 + tetes - 1), ci["TOL"], "verite", "tolerance_ml", self.ecrit_tol,
                          None))
        elif self.absent("tolerance_ml"):
            data[r0][ci["TOL"]] = "n.c."
        spans += [("SPAN", (ci["G"], r0), (ci["G"], r0 + tetes - 1)),
                  ("SPAN", (ci["TOL"], r0), (ci["TOL"], r0 + tetes - 1))]
        if avec_unite and tetes > 1:
            spans.append(("SPAN", (ci["U"], r0), (ci["U"], r0 + tetes - 1)))
        if tetes > 1 and not calcul:
            row = ["" for _ in cols]
            row[ci["G"]] = "Moyenne générale" if fr else "Overall mean"
            if self.ou("volume_dose_ml") == "tableau":
                row[ci["M"]] = self._val(self.ecrit["volume_dose_ml"], ud)
                notes.append((len(data), ci["M"], "verite", "volume_dose_ml",
                              self.ecrit["volume_dose_ml"], None))
            else:
                row[ci["M"]] = "—"
            spans.append(("SPAN", (ci["G"], len(data)), (ci["P3"], len(data))))
            data.append(row)
        # Débit, pression, température : une valeur avant, une après (cases fusionnées).
        for cle, av, unite in [("debit_ml_min", self.cv("debit_ml_min", lr["debit_avant"]),
                                self.u["debit_ml_min"]),
                               ("pression_bar", self.cv("pression_bar", lr["pression_avant"]),
                                self.u["pression_bar"]),
                               (None, self.n(lr["temperature"] - 1.5, 1), "°C")]:
            if cle and self.absent(cle) and cle == "debit_ml_min":
                continue
            row = ["" for _ in cols]
            libelle = self.lib(cle) if cle else ("Température" if fr else "Temperature")
            row[ci["G"]] = Paragraph(escape(self._lib_u(libelle, unite)), self.s["case"])
            if avec_unite:
                row[ci["U"]] = unite
            row[ci["A1"]] = self._val(av, unite)
            if cle:
                notes.append((len(data), (ci["A1"], ci["A3"]), "leurre", cle, av, "valeur avant réglage"))
            if cle is None:
                apres = self.n(lr["temperature"], 1)
            elif self.absent(cle):
                apres = "n.m."
            elif "valeur_barree" in p[cle] or "erratum" in p[cle]:
                apres = self.faute[cle]
                notes.append((len(data), (ci["P1"], ci["P3"]), "erronee", cle, apres,
                              "valeur corrigée ailleurs"))
            elif self.ou(cle) == "tableau":
                apres = self.ecrit[cle]
                notes.append((len(data), (ci["P1"], ci["P3"]), "verite", cle, apres, None))
            else:
                apres = "—"
            row[ci["P1"]] = self._val(apres, unite)
            if not calcul:
                row[ci["M"]] = "—"
            row[ci["TOL"]] = "—"
            spans += [("SPAN", (ci["A1"], len(data)), (ci["A3"], len(data))),
                      ("SPAN", (ci["P1"], len(data)), (ci["P3"], len(data)))]
            data.append(row)
        largeurs = {"G": 100, "T": 30, "U": 40, "M": 52, "TOL": 58}
        reste = (L - 72 - sum(largeurs[k] for k in cols if k in largeurs)) / 6
        t = Table(data, colWidths=[largeurs.get(k, reste) for k in cols])
        t.setStyle(self._style_table(spans + [("BACKGROUND", (0, 1), (-1, 1),
                                                colors.Color(0.92, 0.92, 0.92)),
                                               ("ALIGN", (1, 0), (-1, -1), "CENTER")]))
        cur.para("<b>Tableau 1 - Relevés</b>" if fr else "<b>Table 1 - Readings</b>", self.s["corps"],
                 espace=4)
        cur.table(t, notes, espace=4)
        if self.place_unite == "note":
            cur.para((f"Unités : volumes en {ud}, débits en {self.u['debit_ml_min']}, pressions en "
                      f"{self.u['pression_bar']}, températures en °C." if fr else
                      f"Units: volumes in {ud}, flow in {self.u['debit_ml_min']}, pressure in "
                      f"{self.u['pression_bar']}, temperature in °C."), self.s["petit"])
        inc = self.vol(lr["incertitude"])
        cur.para((f"Incertitude élargie sur la dose : ± {inc} {ud} (k = 2)." if fr else
                  f"Expanded uncertainty on dose: ± {inc} {ud} (k = 2)."), self.s["petit"],
                 [("leurre", "tolerance_ml", inc, "incertitude de mesure")])
        if "conflit_regle" in self.p["debit_ml_min"]:
            cur.para(("Les valeurs du tableau 1 font foi ; la synthèse de la page d'entrée reprend "
                      "des relevés provisoires." if fr else
                      "Table 1 values prevail; the summary on the cover page shows provisional "
                      "readings."), self.s["petit"])
        cur.saut(10)
        # Caractéristiques.
        un = self.u["volume_nominal_ml"]
        lignes = [["Caractéristique" if fr else "Rating", "Valeur" if fr else "Value"]]
        notes = []
        if self.ou("volume_nominal_ml") == "tableau":
            lignes.append([self.lib("volume_nominal_ml"), f"{self.ecrit['volume_nominal_ml']} {un}"])
            notes.append((len(lignes) - 1, 1, "verite", "volume_nominal_ml",
                          self.ecrit["volume_nominal_ml"], None))
        g0, g1 = lr["gamme"]
        gam = f"{self.n(g0)} – {self.n(g1)} ml"
        res = f"{self.n(lr['reservoir_l'])} L"
        circ = f"{self.n(lr['circuit_ml'])} ml"
        for lib, val, cle, raison in [
                ("Gamme du modèle (constructeur)" if fr else "Model range (OEM)", gam,
                 "volume_nominal_ml", "gamme du constructeur"),
                ("Capacité du réservoir" if fr else "Tank capacity", res, "volume_dose_ml",
                 "capacité du réservoir"),
                ("Volume du circuit" if fr else "Line volume", circ, "volume_dose_ml", "volume du circuit"),
                ("Débit maximal" if fr else "Max. flow",
                 f"{self.cv('debit_ml_min', lr['debit_max'])} {self.u['debit_ml_min']}",
                 "debit_ml_min", "débit maximal du constructeur"),
                ("Pression maximale admissible" if fr else "Max. allowable pressure",
                 f"{self.n(lr['pression_max'], 1)} bar", "pression_bar", "pression maximale"),
                ("Tarage de la soupape" if fr else "Relief valve setting", f"{self.n(lr['tarage'], 1)} bar",
                 "pression_bar", "tarage de la soupape")]:
            lignes.append([lib, val])
            notes.append((len(lignes) - 1, 1, "leurre", cle, val.rsplit(" ", 1)[0], raison))
        t = Table(lignes, colWidths=[220, 140])
        t.setStyle(self._style_table())
        cur.para("<b>Tableau 2 - Caractéristiques</b>" if fr else "<b>Table 2 - Ratings</b>",
                 self.s["corps"], espace=4)
        cur.table(t, notes)

    # Page 4 : schéma -------------------------------------------------------------------------

    def page_schema(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        fr = self.fr
        cur = Curseur(c, ctx, 36, L - 72, H - 50)
        cur.para("3. Schéma de principe" if fr else "3. Layout diagram", self.s["titre"], espace=14)
        organes = {"doseuse": ("Groupe piston", "Piston unit"), "pompe": ("Tête de pompe", "Pump head"),
                   "remplisseuse": ("Têtes de remplissage", "Filling heads"),
                   "pipette": ("Module de pipetage", "Pipetting module")}
        textes = {"reservoir_nom": "Réservoir" if fr else "Tank",
                  "reservoir": f"{'Capacité' if fr else 'Capacity'} : {self.n(self.lr['reservoir_l'])} L",
                  "circuit": f"Circuit : {self.n(self.lr['circuit_ml'])} ml",
                  "organe": organes[self.marque["type"]][0 if fr else 1]}
        notes = []
        for cle, nom in [("volume_dose_ml", "dose"), ("volume_nominal_ml", "nominal"),
                         ("debit_ml_min", "debit"), ("pression_bar", "pression")]:
            if self.ou(cle) == "schema":
                s = f"{self.ecrit[cle]} {self.u[cle]}"
                textes[nom] = f"{self.lib(cle)} : {s}"
                notes.append((cle, s))
        img = dessins.schema(textes)
        bb = cur.image(img, dessins.SCHEMA_L, dessins.SCHEMA_H, x=(L - dessins.SCHEMA_L) / 2, espace=12)
        for cle, s in notes:
            ctx.noter("verite", cle, s, bb, mode="image")
        cur.para((f"Repères : 1 réservoir ; 2 circuit d'alimentation ; 3 organe de dosage ; "
                  f"4 manomètre ; 5 sens d'écoulement ; 6 buse de sortie." if fr else
                  "Key: 1 tank; 2 supply line; 3 dosing unit; 4 pressure gauge; 5 flow direction; "
                  "6 outlet nozzle."), self.s["corps"])

    # Page 5 : pièces et conclusion -----------------------------------------------------------

    def page_conclusion(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        v, lr, fr = self.v, self.lr, self.fr
        cur = Curseur(c, ctx, 36, L - 72, H - 50)
        cur.para("4. Pièces" if fr else "4. Parts", self.s["titre"], espace=6)
        lignes = [["Référence" if fr else "Part no.", "Désignation" if fr else "Description",
                   "Action", "Prix unitaire HT" if fr else "Unit price"]]
        notes = []
        actions = (["remplacée", "contrôlée, conservée", "commandée (non posée)", "proposée au devis"]
                   if fr else ["replaced", "inspected, kept", "ordered (not fitted)", "quoted"])
        raisons = [None, "pièce contrôlée, non remplacée", "pièce commandée, non posée",
                   "pièce proposée au devis"]
        for k, ((ref, nom), prix) in enumerate(zip(lr["pieces"], lr["prix"])):
            if k == 0 and (self.absent("reference_piece") or self.ou("reference_piece") != "tableau"):
                continue
            lignes.append([ref, Paragraph(escape(nom), self.s["case"]), actions[k],
                           f"{self.n(prix, 2)} €"])
            notes.append((len(lignes) - 1, 0, "verite" if k == 0 else "leurre", "reference_piece",
                          ref, raisons[k]))
        t = Table(lignes, colWidths=[100, 190, 130, 103])
        t.setStyle(self._style_table())
        cur.table(t, notes)
        if self.absent("reference_piece"):
            cur.para("Aucune pièce n'a été remplacée lors de cette visite." if fr else
                     "No part was replaced during this visit.", self.s["corps"])
        cur.para("5. Observations", self.s["titre"], espace=6)
        for html, n in self.recit()[1]:
            cur.para(html, self.s["corps"], n)
        cur.saut(6)
        cur.para("6. Signatures", self.s["titre"], espace=6)
        y = cur.y
        c.setFont(self.police, 8.5)
        if not self.absent("technicien"):
            c.drawString(36, y - 10, ("Le technicien responsable : " if fr else "Lead technician: ") +
                         v["technicien"])
            ctx.noter("verite", "technicien", v["technicien"], (36, y - 14, 300, y - 2))
        c.drawImage(ImageReader(dessins.signature(f"{self.graine}/{self.doc['id']}/s1")), 40, y - 58, 120, 37)
        c.drawString(L / 2 + 10, y - 10, ("Pour le client, bon pour accord : " if fr else
                                          "For the customer: ") + lr["approbateur"])
        ctx.noter("leurre", "technicien", lr["approbateur"], (L / 2 + 10, y - 14, L - 36, y - 2),
                  raison="signataire côté client")
        c.drawImage(ImageReader(dessins.signature(f"{self.graine}/{self.doc['id']}/s2")),
                    L / 2 + 14, y - 58, 120, 37)
