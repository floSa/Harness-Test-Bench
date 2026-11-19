"""Rendu PDF des rapports : un gabarit par prestataire.

Chaque valeur écrite est enregistrée (page, mode texte ou image, chaîne) pour le contrôle
automatique des pièges.
"""
import datetime as dt
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
from entites import CONSTRUCTEURS, MOIS, PRESTATAIRES, STATUTS

UNITES = {
    "fr": {"ml": "ml", "µl": "µl", "L": "L", "ml/min": "ml/min", "bar": "bar", "°C": "°C"},
    "en": {"ml": "mL", "µl": "µL", "L": "L", "ml/min": "mL/min", "bar": "bar", "°C": "°C"},
}
NBSP = " "


def nombre(x, style, min_dec=0, max_dec=6):
    dec = min_dec
    while dec < max_dec and abs(round(x, dec) - x) > 1e-9:
        dec += 1
    s = f"{x:,.{dec}f}"
    if style == "fr":
        s = s.replace(",", " ").replace(".", ",")
    return s


def convertir(x_ml, unite):
    if unite == "µl":
        return round(x_ml * 1000, 6)
    if unite == "L":
        return round(x_ml / 1000, 9)
    return x_ml


class Contexte:
    def __init__(self):
        self.placements = []
        self.page = 0
        self.scan = False

    def place(self, cle, texte, mode="texte"):
        self.placements.append({"cle": cle, "page": self.page, "texte": texte,
                                "mode": "image" if self.scan else mode})


class Curseur:
    def __init__(self, c, ctx, x, largeur, y, y_bas=60):
        self.c, self.ctx, self.x, self.l, self.y, self.y_bas = c, ctx, x, largeur, y, y_bas

    def _poser(self, objet, espace):
        _, h = objet.wrapOn(self.c, self.l, 2000)
        if self.y - h < self.y_bas:
            raise RuntimeError(f"débordement de page ({self.y - h:.0f} < {self.y_bas})")
        objet.drawOn(self.c, self.x, self.y - h)
        self.y -= h + espace
        return h

    def hauteur(self, objet):
        return objet.wrapOn(self.c, self.l, 2000)[1]

    def para(self, html, style, places=(), espace=5):
        self._poser(Paragraph(html, style), espace)
        for cle, texte in places:
            self.ctx.place(cle, texte)

    def table(self, table, places=(), espace=10):
        self._poser(table, espace)
        for cle, texte in places:
            self.ctx.place(cle, texte)

    def image(self, img, largeur, hauteur, x=None, espace=8):
        if self.y - hauteur < self.y_bas:
            raise RuntimeError("débordement de page (image)")
        self.c.drawImage(ImageReader(img), self.x if x is None else x, self.y - hauteur,
                         largeur, hauteur)
        self.y -= hauteur + espace

    def saut(self, h):
        self.y -= h


class Gabarit:
    taille = A4
    police, gras, italique = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
    corps = 10
    style_nombres = "fr"
    pages_scannables = (0, 1)

    def __init__(self, doc, graine):
        self.doc = doc
        self.langue = doc["langue"]
        self.v = doc["valeurs"]
        self.lr = doc["leurres"]
        self.r = random.Random(f"{graine}/{doc['id']}/rendu")
        self.graine = graine
        self.cons = CONSTRUCTEURS[doc["constructeur_idx"]]
        self.prest = PRESTATAIRES[doc["gabarit"]]
        self.u = UNITES["fr" if self.style_nombres == "fr" else "en"]
        self.coupe = set()
        st = lambda **k: ParagraphStyle("s", fontName=self.police, fontSize=self.corps,
                                        leading=self.corps * 1.35, **k)
        self.s_corps = st()
        self.s_petit = ParagraphStyle("p", parent=self.s_corps, fontSize=self.corps - 1.5,
                                      leading=(self.corps - 1.5) * 1.3)
        self.s_titre = ParagraphStyle("t", parent=self.s_corps, fontName=self.gras,
                                      fontSize=self.corps + 3, leading=(self.corps + 3) * 1.3,
                                      spaceBefore=4)
        self.s_cellule = ParagraphStyle("c", parent=self.s_corps, fontSize=self.corps - 1,
                                        leading=(self.corps - 1) * 1.25)
        self.s_cellule_g = ParagraphStyle("cg", parent=self.s_cellule, fontName=self.gras)
        # Valeur erronée pour le piège « correction ».
        self.erronee = None
        cle = doc["pieges_doc"]["correction"]
        if cle:
            x = self.v[cle]
            facteur = 1 + self.r.choice([-1, 1]) * self.r.uniform(0.06, 0.2)
            pas = 0.1 if cle == "pression_bar" else (1 if cle == "debit_ml_min" else
                                                     (0.001 if x < 1 else 0.01 if x < 10 else 0.1))
            self.erronee = round(round(x * facteur / pas) * pas, 6)
        self.logo_cons = dessins.logo(self.cons)
        self.logo_prest = dessins.logo(self.prest)

    # Mise en forme ---------------------------------------------------------------------------

    def lib(self, cle):
        return self.doc["libelles"][cle]

    def unite_vol(self, cle):
        return self.doc["unites"][cle]

    def vol(self, x_ml, unite, min_dec=0):
        return nombre(convertir(x_ml, unite), self.style_nombres, min_dec)

    def num(self, cle, x=None):
        """Chaîne du nombre (sans unité) dans l'unité d'affichage de la clé."""
        x = self.v[cle] if x is None else x
        if cle in ("volume_dose_ml", "volume_nominal_ml"):
            return self.vol(x, self.unite_vol(cle))
        if cle == "pression_bar":
            return nombre(x, self.style_nombres, 1)
        return nombre(x, self.style_nombres)

    def unite(self, cle):
        if cle in ("volume_dose_ml", "volume_nominal_ml"):
            return self.u[self.unite_vol(cle)]
        return self.u["ml/min" if cle == "debit_ml_min" else "bar"]

    def avec_unite(self, cle, x=None):
        return f"{self.num(cle, x)}{NBSP}{self.unite(cle)}"

    def date(self, iso, forme):
        d = dt.date.fromisoformat(iso)
        if forme == "court_fr":
            return d.strftime("%d/%m/%Y")
        if forme == "long_fr":
            jour = "1er" if d.day == 1 else str(d.day)
            return f"{jour} {MOIS['fr'][d.month - 1]} {d.year}"
        if forme == "abr_en":
            return f"{d.day} {MOIS['en'][d.month - 1][:3]} {d.year}"
        if forme == "long_en":
            return f"{d.day} {MOIS['en'][d.month - 1]} {d.year}"
        if forme == "us_en":
            return f"{MOIS['en'][d.month - 1]} {d.day}, {d.year}"
        return iso

    def absent(self, cle):
        return "champ_absent" in self.doc["pieges"][cle]

    def ici(self, cle, emplacement):
        """Vrai si la valeur attendue doit être écrite à cet emplacement."""
        return not self.absent(cle) and self.doc["emplacements"][cle] == emplacement

    def statut_texte(self):
        cle = "en4" if self.doc["gabarit"] == 4 else self.langue
        return STATUTS[cle][self.v["statut"]]

    # Récit commun ----------------------------------------------------------------------------

    def recit(self):
        """Paragraphes du compte rendu : liste de (html, [(cle, chaîne)])."""
        fr = self.langue == "fr"
        lr, out = self.lr, []
        d_av = self.vol(lr["dose_avant"], self.unite_vol("volume_dose_ml"))
        u_dose = self.unite("volume_dose_ml")
        lib_dose = self.lib("volume_dose_ml").lower()
        if fr:
            out.append((f"Intervention sur l'équipement installé en « {escape(lr['ligne_client'])} », "
                        f"à la demande de {escape(lr['contact'])}. L'opérateur signale une dérive "
                        f"de la quantité délivrée lors des contrôles en ligne.", []))
            out.append((f"Relevé avant réglage, {lib_dose} : {d_av}{NBSP}{u_dose} (moyenne de dix "
                        f"cycles consécutifs).", [("_voisins", d_av)]))
            out.append(("Démontage et nettoyage du circuit, contrôle de l'étanchéité, puis réglage "
                        "de la course jusqu'à stabilisation des mesures.", []))
        else:
            out.append((f"Call-out on the equipment of {escape(lr['ligne_client'])}, requested by "
                        f"{escape(lr['contact'])}. The operator reported a drift of the delivered "
                        f"quantity during in-line checks.", []))
            out.append((f"As-found reading, {lib_dose}: {d_av}{NBSP}{u_dose} (average of ten "
                        f"consecutive cycles).", [("_voisins", d_av)]))
            out.append(("Circuit dismantled and cleaned, tightness checked, stroke adjusted until "
                        "readings were stable.", []))

        # Valeurs présentes seulement dans le récit.
        for cle in ["date_intervention", "site", "numero_serie", "volume_dose_ml",
                    "volume_nominal_ml", "debit_ml_min", "pression_bar"]:
            if not self.ici(cle, "recit") or cle == self.doc["pieges_doc"]["correction"]:
                continue
            lib = self.lib(cle)
            if cle == "date_intervention":
                s = self.date(self.v[cle], "long_fr" if fr else "long_en")
                txt = (f"{lib} : {s}, de 8 h à 12 h." if fr else f"{lib}: {s}, from 8 am to noon.")
            elif cle == "site":
                s = self.v[cle]
                txt = (f"Le déplacement a eu lieu sur le site client ({lib.lower()} : {s})." if fr
                       else f"The visit took place at the customer's premises ({lib.lower()}: {s}).")
            elif cle == "numero_serie":
                s = self.v[cle]
                txt = (f"La plaque signalétique a été relevée ; {lib} : {s}." if fr
                       else f"The rating plate was recorded; {lib}: {s}.")
            else:
                s = self.avec_unite(cle)
                txt = (f"Relevé après réglage, {lib.lower()} : {s}." if fr
                       else f"As-left reading, {lib.lower()}: {s}.")
            out.append((escape(txt), [(cle, s)]))

        # Pièces.
        if self.absent("reference_piece"):
            out.append(("Aucune pièce n'a été remplacée lors de cette visite." if fr
                        else "No parts were replaced during this visit.", []))
        elif self.ici("reference_piece", "recit"):
            ref = self.v["reference_piece"]
            out.append(((f"Pièce remplacée : {escape(lr['piece_nom'])} neuf, "
                         f"{self.lib('reference_piece').lower()} {ref}." if fr else
                         f"Part replaced: new {escape(lr['piece_nom'])}, "
                         f"{self.lib('reference_piece').lower()} {ref}."), [("reference_piece", ref)]))
        out.append(((f"La pièce {lr['autre_ref']} ({escape(lr['autre_nom'])}) a été contrôlée et "
                     f"conservée." if fr else
                     f"Part {lr['autre_ref']} ({escape(lr['autre_nom'])}) was inspected and kept."),
                    [("_leurre", lr["autre_ref"])]))
        res = f"{nombre(lr['reservoir_l'], self.style_nombres)}{NBSP}{self.u['L']}"
        out.append(((f"Le réservoir de {res} a été vidangé puis rincé." if fr else
                     f"The {res} tank was drained and rinsed."), [("_voisins", res)]))

        # Correction.
        cle = self.doc["pieges_doc"]["correction"]
        if cle:
            juste, faux = self.avec_unite(cle), self.avec_unite(cle, self.erronee)
            lib = self.lib(cle).lower()
            out.append(((f"Erratum : dans le tableau des mesures, lire {juste} au lieu de {faux} "
                         f"pour {lib}." if fr else
                         f"Erratum: in the measurement table, read {juste} instead of {faux} "
                         f"for the {lib}."), [(cle, juste)]))

        st = self.v["statut"]
        phrases = {
            ("fr", "conforme"): "Les mesures après réglage sont dans la tolérance.",
            ("fr", "non_conforme"): "La dose reste hors tolérance malgré le réglage ; "
                                    "une pièce est en commande.",
            ("fr", "a_revoir"): "Une légère fuite reste à surveiller ; une nouvelle visite "
                                "est à programmer.",
            ("en", "conforme"): "As-left readings are within tolerance.",
            ("en", "non_conforme"): "The dose remains out of tolerance after adjustment; "
                                    "a part has been ordered.",
            ("en", "a_revoir"): "A slight leak remains to be monitored; a follow-up visit "
                                "is to be scheduled.",
        }
        out.append((phrases[(self.langue, st)], []))
        pv = self.date(lr["prochaine_visite"], "long_fr" if fr else "long_en")
        out.append(((f"Prochaine visite préventive conseillée le {pv}." if fr else
                     f"Next preventive visit recommended on {pv}."), []))
        return out

    # Schéma commun ---------------------------------------------------------------------------

    def schema_image(self, ctx):
        fr = self.langue == "fr"
        organes = {"doseuse": ("Groupe piston", "Piston unit"), "pompe": ("Tête de pompe", "Pump head"),
                   "remplisseuse": ("Tête de remplissage", "Filling head"),
                   "pipette": ("Module de pipetage", "Pipetting module")}
        res = f"{nombre(self.lr['reservoir_l'], self.style_nombres)} {self.u['L']}"
        circ = f"{nombre(self.lr['circuit_ml'], self.style_nombres)} {self.u['ml']}"
        textes = {
            "reservoir_nom": "Réservoir" if fr else "Tank",
            "reservoir": (f"Capacité : {res}" if fr else f"Capacity: {res}"),
            "circuit": (f"Circuit : {circ}" if fr else f"Line: {circ}"),
            "organe": organes[self.cons["type"]][0 if fr else 1],
        }
        noms = {"volume_dose_ml": "dose", "volume_nominal_ml": "nominal",
                "debit_ml_min": "debit", "pression_bar": "pression"}
        for cle, nom in noms.items():
            if self.ici(cle, "schema"):
                s = self.avec_unite(cle).replace(NBSP, " ")
                textes[nom] = f"{self.lib(cle)} : {s}" if fr else f"{self.lib(cle)}: {s}"
                ctx.place(cle, s.replace(" ", NBSP), "image")
        return dessins.schema(textes)

    def legende_schema(self):
        organe = {"doseuse": "groupe piston", "pompe": "tête de pompe",
                  "remplisseuse": "tête de remplissage", "pipette": "module de pipetage"}
        organe_en = {"doseuse": "piston unit", "pompe": "pump head",
                     "remplisseuse": "filling head", "pipette": "pipetting module"}
        t = self.cons["type"]
        if self.langue == "fr":
            return (f"Repères : 1 réservoir ; 2 circuit d'alimentation ; 3 {organe[t]} ; "
                    f"4 manomètre ; 5 sens d'écoulement ; 6 buse de sortie et récipient.")
        return (f"Key: 1 tank; 2 supply line; 3 {organe_en[t]}; 4 pressure gauge; "
                f"5 flow direction; 6 outlet nozzle and container.")

    # Rendu -----------------------------------------------------------------------------------

    def pages(self):
        raise NotImplementedError

    def rendre(self):
        """Renvoie (octets PDF, placements, page scannée ou None, angle)."""
        ctx = Contexte()
        fonctions = self.pages()
        self.n_pages = len(fonctions)
        page_scan, angle = None, None
        if self.doc["pieges_doc"]["scan"]:
            page_scan = self.r.choice(self.pages_scannables)
        tampon = io.BytesIO()
        largeur, hauteur = self.taille
        c = canvas.Canvas(tampon, pagesize=self.taille, invariant=1)
        c.setTitle("Rapport d'intervention" if self.langue == "fr" else "Service report")
        for i, f in enumerate(fonctions):
            ctx.page = i
            if i == page_scan:
                ctx.scan = True
                jpeg, angle = dessins.scanner(lambda cc: f(cc, ctx), largeur, hauteur,
                                              f"{self.graine}/{self.doc['id']}/scan")
                ctx.scan = False
                c.drawImage(ImageReader(io.BytesIO(jpeg)), 0, 0, largeur, hauteur)
            else:
                f(c, ctx)
            c.showPage()
        c.save()
        return tampon.getvalue(), ctx.placements, page_scan, angle

    def logos(self, c, ctx, positions):
        """positions : deux couples (x, y) ; le second sert au logo du prestataire."""
        ordre = [("cons", self.logo_cons), ("prest", self.logo_prest)]
        if self.doc["pieges_doc"]["deux_logos"]:
            if self.r.random() < 0.5:
                ordre.reverse()
        else:
            ordre = ordre[:1]
        for (qui, img), (x, y) in zip(ordre, positions):
            c.drawImage(ImageReader(img), x, y, dessins.LOGO_L, dessins.LOGO_H)
            if qui == "cons":
                ctx.place("constructeur", self.cons["nom"], "image")

    def style_table(self, entete=True, fond=colors.Color(0.92, 0.92, 0.92)):
        cmds = [("FONT", (0, 0), (-1, -1), self.police, self.corps - 1),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
        if entete:
            cmds += [("BACKGROUND", (0, 0), (-1, 0), fond),
                     ("FONT", (0, 0), (-1, 0), self.gras, self.corps - 1)]
        return TableStyle(cmds)

    def cellule(self, texte, gras=False):
        return Paragraph(escape(texte), self.s_cellule_g if gras else self.s_cellule)

    def valeur_tableau(self, cle, vide="—"):
        """Chaîne à écrire dans la case « après réglage » d'une clé numérique."""
        if self.doc["pieges_doc"]["correction"] == cle:
            return self.num(cle, self.erronee), ("_erronee", self.num(cle, self.erronee))
        if self.ici(cle, "tableau"):
            return self.num(cle), (cle, self.num(cle))
        return vide, None


# Gabarit 1 : français, tableaux classiques ---------------------------------------------------

class Gabarit1(Gabarit):
    police, gras, italique = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
    style_nombres = "fr"
    pages_scannables = (0, 1, 3)

    def pages(self):
        self.forme_date = self.r.choice(["court_fr", "long_fr"])
        return [self.garde, self.mesures, self.schema, self.compte_rendu]

    def cadre(self, c, ctx):
        L, H = self.taille
        c.setFillColorRGB(*self.prest["couleur"])
        c.rect(0, H - 38, L, 38, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(self.gras, 13)
        c.drawString(40, H - 25, self.prest["nom"])
        c.setFont(self.police, 9)
        c.drawRightString(L - 40, H - 25, f"Rapport n° {self.lr['reference_rapport']}")
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont(self.police, 7.5)
        c.line(40, 42, L - 40, 42)
        c.drawString(40, 30, f"{self.prest['nom']}, {self.prest['adresse']}")
        c.drawRightString(L - 40, 30, f"Page {ctx.page + 1}/{self.n_pages}")
        c.setFillColorRGB(0, 0, 0)

    def garde(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        self.logos(c, ctx, [(40, H - 112), (L - 40 - dessins.LOGO_L, H - 112)])
        cur = Curseur(c, ctx, 40, L - 80, H - 140)
        cur.para("RAPPORT D'INTERVENTION", ParagraphStyle("g", parent=self.s_titre, fontSize=20,
                                                          leading=24))
        cur.para("Maintenance et contrôle métrologique d'un équipement de dosage", self.s_corps,
                 espace=14)
        lignes, places = [], []

        def ligne(libelle, valeur, cle=None):
            lignes.append([self.cellule(libelle, True), self.cellule(valeur)])
            if cle:
                places.append((cle, valeur))

        ligne("Référence du rapport", self.lr["reference_rapport"])
        ligne(self.lib("machine"), self.v["machine"], "machine")
        ligne("Type d'équipement", self.lr["type_machine"])
        if not self.doc["pieges_doc"]["logo_seul"]:
            ligne(self.lib("constructeur"), self.v["constructeur"], "constructeur")
        if self.ici("numero_serie", "garde"):
            ligne(self.lib("numero_serie"), self.v["numero_serie"], "numero_serie")
        elif self.absent("numero_serie"):
            ligne(self.lib("numero_serie"), "illisible (plaque détériorée)")
        ligne("N° d'inventaire client", self.lr["inventaire"])
        if self.ici("site", "garde"):
            ligne(self.lib("site"), self.v["site"], "site")
        ligne("Ligne", self.lr["ligne_client"])
        if self.ici("date_intervention", "garde"):
            ligne(self.lib("date_intervention"),
                  self.date(self.v["date_intervention"], self.forme_date), "date_intervention")
        ligne("Date d'émission du rapport", self.date(self.lr["date_rapport"], self.forme_date))
        ligne("Contact client", self.lr["contact"])
        t = Table(lignes, colWidths=[170, L - 80 - 170])
        t.setStyle(self.style_table(entete=False))
        cur.table(t, places, espace=18)
        cur.para("<b>Objet de la visite</b>", self.s_corps)
        cur.para("Visite de maintenance préventive avec contrôle des volumes délivrés, du débit et "
                 "de la pression, réglage si nécessaire et remplacement des pièces d'usure.",
                 self.s_corps)

    def mesures(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 40, L - 80, H - 70)
        cur.para("1. Mesures relevées", self.s_titre, espace=8)
        cur.para("Les relevés sont des moyennes de dix cycles, à cadence nominale, avec de l'eau "
                 "déminéralisée à température ambiante.", self.s_corps, espace=10)
        ud = self.unite_vol("volume_dose_ml")
        entete = ["Grandeur", "Avant réglage", "Après réglage", "Tolérance", "Unité"]
        lignes, places = [entete], []
        apres, pl = self.valeur_tableau("volume_dose_ml")
        av = self.vol(self.lr["dose_avant"], ud)
        tol = "± " + self.vol(self.lr["tolerance_ml"], ud)
        lignes.append([self.cellule(self.lib("volume_dose_ml")), av, apres, tol,
                       self.unite("volume_dose_ml")])
        places += [("_voisins", av), ("_voisins", tol)] + ([pl] if pl else [])
        if not self.absent("debit_ml_min"):
            apres, pl = self.valeur_tableau("debit_ml_min")
            lignes.append([self.cellule(self.lib("debit_ml_min")),
                           nombre(self.lr["debit_avant"], "fr"), apres, "—", self.u["ml/min"]])
            places += [pl] if pl else []
        if self.absent("pression_bar"):
            lignes.append([self.cellule(self.lib("pression_bar")), "non mesurée", "non mesurée",
                           "—", self.u["bar"]])
        else:
            apres, pl = self.valeur_tableau("pression_bar")
            lignes.append([self.cellule(self.lib("pression_bar")),
                           nombre(self.lr["pression_avant"], "fr", 1), apres, "—", self.u["bar"]])
            places += [pl] if pl else []
        lignes.append([self.cellule("Température du produit"),
                       nombre(self.lr["temperature_avant"], "fr", 1),
                       nombre(self.lr["temperature"], "fr", 1), "—", self.u["°C"]])
        t = Table(lignes, colWidths=[150, 85, 85, 85, 110])
        t.setStyle(self.style_table())
        cur.para("<b>Tableau 1 : relevés avant et après réglage</b>", self.s_corps)
        cur.table(t, places, espace=16)

        lignes, places = [["Caractéristique", "Valeur", "Unité"]], []
        val, pl = self.valeur_tableau("volume_nominal_ml", vide=None)
        if val is not None:
            lignes.append([self.cellule(self.lib("volume_nominal_ml")), val,
                           self.unite("volume_nominal_ml")])
            places.append(pl)
        res = nombre(self.lr["reservoir_l"], "fr")
        circ = nombre(self.lr["circuit_ml"], "fr")
        lignes += [[self.cellule("Capacité du réservoir"), res, "L"],
                   [self.cellule("Volume du circuit"), circ, "ml"],
                   [self.cellule("Débit maximal constructeur"), nombre(self.lr["debit_max"], "fr"),
                    "ml/min"],
                   [self.cellule("Pression maximale admissible"),
                    nombre(self.lr["pression_max"], "fr", 1), "bar"]]
        places += [("_voisins", res), ("_voisins", circ)]
        t = Table(lignes, colWidths=[200, 120, 110])
        t.setStyle(self.style_table())
        cur.para("<b>Tableau 2 : caractéristiques de l'équipement</b>", self.s_corps)
        cur.table(t, places, espace=12)
        cur.para("La tolérance s'applique au volume nominal. Les instruments de mesure utilisés "
                 "sont étalonnés et raccordés.", self.s_petit)

    def schema(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 40, L - 80, H - 70)
        cur.para("2. Schéma de principe", self.s_titre, espace=14)
        img = self.schema_image(ctx)
        cur.image(img, dessins.SCHEMA_L, dessins.SCHEMA_H, x=(L - dessins.SCHEMA_L) / 2, espace=14)
        cur.para(self.legende_schema(), self.s_corps)
        cur.para("Cotes relevées sur site lors de l'intervention.", self.s_petit)

    def compte_rendu(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 40, L - 80, H - 70)
        cur.para("3. Compte rendu de l'intervention", self.s_titre, espace=8)
        for html, places in self.recit():
            cur.para(html, self.s_corps, places)
        cur.saut(6)
        cur.para("4. Pièces", self.s_titre, espace=6)
        lignes, places = [["Référence", "Désignation", "Action"]], []
        if self.ici("reference_piece", "tableau"):
            lignes.append([self.v["reference_piece"], self.cellule(self.lr["piece_nom"]), "remplacée"])
            places.append(("reference_piece", self.v["reference_piece"]))
        lignes.append([self.lr["autre_ref"], self.cellule(self.lr["autre_nom"]), "contrôlée, conservée"])
        t = Table(lignes, colWidths=[110, 220, 185])
        t.setStyle(self.style_table())
        cur.table(t, places, espace=12)
        cur.para("5. Conclusion", self.s_titre, espace=6)
        tech = self.v["technicien"] if not self.absent("technicien") else "non renseigné"
        lignes = [[self.cellule(self.lib("statut"), True), self.cellule(self.statut_texte())],
                  [self.cellule(self.lib("technicien"), True), self.cellule(tech)],
                  [self.cellule("Validé par (client)", True), self.cellule(self.lr["valideur"])]]
        places = [("statut", self.statut_texte())]
        if not self.absent("technicien"):
            places.append(("technicien", tech))
        t = Table(lignes, colWidths=[170, 345])
        t.setStyle(self.style_table(entete=False))
        cur.table(t, places, espace=6)
        cur.para("Signature du technicien :", self.s_petit, espace=2)
        cur.image(dessins.signature(f"{self.graine}/{self.doc['id']}/sig"), 120, 37)


# Gabarit 2 : anglais, nombres anglais, unités abrégées --------------------------------------

class Gabarit2(Gabarit):
    police, gras, italique = "Times-Roman", "Times-Bold", "Times-Italic"
    corps = 10.5
    style_nombres = "en"
    pages_scannables = (0, 1, 3)

    def pages(self):
        self.forme_date = self.r.choice(["abr_en", "long_en", "court_fr"])
        return [self.garde, self.mesures, self.schema, self.compte_rendu]

    def cadre(self, c, ctx):
        L, H = self.taille
        c.setStrokeColorRGB(*self.prest["couleur"])
        c.setLineWidth(2)
        c.line(45, H - 40, L - 45, H - 40)
        c.setFillColorRGB(*self.prest["couleur"])
        c.setFont(self.gras, 10)
        c.drawString(45, H - 34, self.prest["nom"].upper() + "  |  SERVICE REPORT")
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.setFont(self.police, 8)
        c.setLineWidth(0.5)
        c.line(45, 44, L - 45, 44)
        c.drawString(45, 32, f"Report {self.lr['reference_rapport']}")
        c.drawRightString(L - 45, 32, f"Page {ctx.page + 1} of {self.n_pages}")
        c.setFillColorRGB(0, 0, 0)
        c.setStrokeColorRGB(0, 0, 0)

    def garde(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        self.logos(c, ctx, [(L - 45 - dessins.LOGO_L, H - 120), (L - 45 - dessins.LOGO_L, H - 185)])
        c.setFont(self.gras, 26)
        c.drawString(45, H - 95, "SERVICE REPORT")
        c.setFont(self.italique, 12)
        c.drawString(45, H - 115, "Field service and calibration of dosing equipment")
        y = H - 230

        def ligne(libelle, valeur, cle=None):
            nonlocal y
            c.setFont(self.gras, 11)
            c.drawString(60, y, f"{libelle}:")
            c.setFont(self.police, 11)
            c.drawString(230, y, valeur)
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(60, y - 6, L - 60, y - 6)
            y -= 24
            if cle:
                ctx.place(cle, valeur)

        def section(titre):
            nonlocal y
            y -= 8
            c.setFillColorRGB(*self.prest["couleur"])
            c.setFont(self.gras, 12)
            c.drawString(45, y, titre)
            c.setFillColorRGB(0, 0, 0)
            y -= 22

        section("Visit")
        ligne("Report no.", self.lr["reference_rapport"])
        if self.ici("date_intervention", "garde"):
            ligne(self.lib("date_intervention"),
                  self.date(self.v["date_intervention"], self.forme_date), "date_intervention")
        ligne("Report issued", self.date(self.lr["date_rapport"], self.forme_date))
        if self.ici("site", "garde"):
            ligne(self.lib("site"), self.v["site"], "site")
        ligne("Customer contact", self.lr["contact"])
        section("Equipment")
        ligne(self.lib("machine"), self.v["machine"], "machine")
        ligne("Type", self.lr["type_machine"])
        if not self.doc["pieges_doc"]["logo_seul"]:
            ligne(self.lib("constructeur"), self.v["constructeur"], "constructeur")
        if self.ici("numero_serie", "garde"):
            ligne(self.lib("numero_serie"), self.v["numero_serie"], "numero_serie")
        elif self.absent("numero_serie"):
            ligne(self.lib("numero_serie"), "not readable (plate missing)")
        ligne("Asset tag", self.lr["inventaire"])
        ligne("Customer line", self.lr["ligne_client"])

    def mesures(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 45, L - 90, H - 70)
        cur.para("1  Measurements", self.s_titre, espace=8)
        ud = self.unite_vol("volume_dose_ml")
        lignes, places = [["Parameter", "As found", "As left", "Tol.", "Unit"]], []
        apres, pl = self.valeur_tableau("volume_dose_ml")
        av = self.vol(self.lr["dose_avant"], ud)
        tol = "± " + self.vol(self.lr["tolerance_ml"], ud)
        lignes.append([self.cellule(self.lib("volume_dose_ml")), av, apres, tol,
                       self.unite("volume_dose_ml")])
        places += [("_voisins", av), ("_voisins", tol)] + ([pl] if pl else [])
        if not self.absent("debit_ml_min"):
            apres, pl = self.valeur_tableau("debit_ml_min")
            lignes.append([self.cellule(self.lib("debit_ml_min")), nombre(self.lr["debit_avant"], "en"),
                           apres, "—", self.u["ml/min"]])
            places += [pl] if pl else []
        if self.absent("pression_bar"):
            lignes.append([self.cellule(self.lib("pression_bar")), "n/m", "n/m", "—", "bar"])
        else:
            apres, pl = self.valeur_tableau("pression_bar")
            lignes.append([self.cellule(self.lib("pression_bar")),
                           nombre(self.lr["pression_avant"], "en", 1), apres, "—", "bar"])
            places += [pl] if pl else []
        lignes.append([self.cellule("Product temp."), nombre(self.lr["temperature_avant"], "en", 1),
                       nombre(self.lr["temperature"], "en", 1), "—", "°C"])
        t = Table(lignes, colWidths=[160, 80, 80, 80, 105])
        t.setStyle(self.style_table(fond=colors.Color(0.85, 0.93, 0.94)))
        cur.table(t, places, espace=6)
        cur.para("n/m: not measured. Readings are averages of ten cycles.", self.s_petit, espace=14)

        cur.para("2  Equipment ratings", self.s_titre, espace=8)
        lignes, places = [["Rating", "Value", "Unit"]], []
        val, pl = self.valeur_tableau("volume_nominal_ml", vide=None)
        if val is not None:
            lignes.append([self.cellule(self.lib("volume_nominal_ml")), val,
                           self.unite("volume_nominal_ml")])
            places.append(pl)
        res = nombre(self.lr["reservoir_l"], "en")
        circ = nombre(self.lr["circuit_ml"], "en")
        lignes += [[self.cellule("Tank capacity"), res, "L"],
                   [self.cellule("Line volume"), circ, "mL"],
                   [self.cellule("Max. flow (OEM)"), nombre(self.lr["debit_max"], "en"), "mL/min"],
                   [self.cellule("Relief valve setting"), nombre(self.lr["pression_max"], "en", 1),
                    "bar"]]
        places += [("_voisins", res), ("_voisins", circ)]
        t = Table(lignes, colWidths=[200, 150, 155])
        t.setStyle(self.style_table(fond=colors.Color(0.85, 0.93, 0.94)))
        cur.table(t, places, espace=14)

        cur.para("3  Parts", self.s_titre, espace=8)
        lignes, places = [["Part no.", "Description", "Action"]], []
        if self.ici("reference_piece", "tableau"):
            lignes.append([self.v["reference_piece"], self.cellule(self.lr["piece_nom"]), "Replaced"])
            places.append(("reference_piece", self.v["reference_piece"]))
        lignes.append([self.lr["autre_ref"], self.cellule(self.lr["autre_nom"]), "Inspected, OK"])
        t = Table(lignes, colWidths=[130, 230, 145])
        t.setStyle(self.style_table(fond=colors.Color(0.85, 0.93, 0.94)))
        cur.table(t, places)

    def schema(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 45, L - 90, H - 70)
        cur.para("4  Diagram", self.s_titre, espace=14)
        cur.image(self.schema_image(ctx), dessins.SCHEMA_L, dessins.SCHEMA_H,
                  x=(L - dessins.SCHEMA_L) / 2, espace=14)
        cur.para(self.legende_schema(), self.s_corps)
        cur.para("Dimensions recorded on site.", self.s_petit)

    def compte_rendu(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 45, L - 90, H - 70)
        cur.para("5  Work performed", self.s_titre, espace=8)
        for html, places in self.recit():
            cur.para(html, self.s_corps, places)
        cur.saut(10)
        cur.para("6  Sign-off", self.s_titre, espace=8)
        tech = self.v["technicien"] if not self.absent("technicien") else "—"
        cur.para(f"<b>{escape(self.lib('statut'))}:</b> {self.statut_texte()}", self.s_corps,
                 [("statut", self.statut_texte())])
        cur.para(f"<b>{escape(self.lib('technicien'))}:</b> {escape(tech)}", self.s_corps,
                 [] if self.absent("technicien") else [("technicien", tech)])
        cur.para(f"<b>Customer acceptance:</b> {escape(self.lr['valideur'])}", self.s_corps, espace=8)
        cur.image(dessins.signature(f"{self.graine}/{self.doc['id']}/sig"), 120, 37)


# Gabarit 3 : français, texte abondant, tableau coupé -----------------------------------------

REMPLISSAGE_FR = [
    "L'équipement est exploité en deux postes, cinq jours par semaine, pour le conditionnement "
    "de produits liquides.",
    "La dernière intervention préventive avait donné lieu à un simple nettoyage du circuit, sans "
    "remplacement de pièce.",
    "L'accès à la machine a été rendu possible après consignation électrique et pneumatique par "
    "le responsable de ligne.",
    "Les produits dosés sur cette ligne sont aqueux et peu visqueux ; aucun produit dangereux "
    "n'était présent dans le circuit au moment de la visite.",
    "Le plan de prévention a été relu avec le service sécurité du site avant le début des travaux.",
    "Un balisage de la zone a été mis en place pendant toute la durée de l'intervention.",
    "Les contrôles ont été réalisés avec des instruments étalonnés, dont les certificats sont "
    "tenus à disposition du client.",
    "L'historique de maintenance de l'équipement a été consulté sur le registre tenu par le client.",
    "Les essais de répétabilité ont porté sur une série de cycles consécutifs à cadence nominale.",
    "Le technicien a vérifié l'absence de bulles d'air dans le circuit avant chaque série de "
    "mesures.",
    "Les fixations du bâti et l'état des flexibles ont été contrôlés visuellement ; aucune trace "
    "de corrosion n'a été relevée.",
    "Le produit utilisé pour les essais est de l'eau déminéralisée à température ambiante.",
    "Le responsable de production a été informé du déroulement de l'intervention à chaque étape.",
    "Les capots de protection ont été remontés et leurs sécurités vérifiées avant la remise en "
    "service.",
    "Les consignes de nettoyage en place ont été rappelées à l'équipe de production.",
    "Le poste de travail a été laissé propre et dégagé à la fin de la visite.",
    "Le carnet de bord de la machine a été complété et visé par le technicien.",
    "Aucun bruit anormal ni échauffement n'a été constaté pendant les essais à vide.",
    "La documentation du constructeur était disponible sur place et à jour.",
    "Les raccords rapides ont été démontés, nettoyés et remontés avec un lubrifiant compatible.",
]


class Gabarit3(Gabarit):
    police, gras, italique = "Courier", "Courier-Bold", "Courier-Oblique"
    corps = 9.5
    style_nombres = "fr"
    pages_scannables = (0, 1, 2, 4)

    def pages(self):
        self.forme_date = self.r.choice(["court_fr", "long_fr"])
        self.remplissage = self.r.sample(REMPLISSAGE_FR, len(REMPLISSAGE_FR))
        self._preparer_tableau()
        paras = self.recit()
        self.recit_p3, self.recit_p5 = paras[:3], paras[3:]
        return [self.garde, self.contexte, self.suite, self.schema, self.observations]

    def cadre(self, c, ctx):
        L, H = self.taille
        c.setFont(self.gras, 11)
        c.drawCentredString(L / 2, H - 32, self.prest["nom"].upper())
        c.setLineWidth(0.8)
        c.line(50, H - 40, L - 50, H - 40)
        c.line(50, H - 43, L - 50, H - 43)
        c.setFont(self.police, 8)
        c.drawCentredString(L / 2, 30, f"CR {self.lr['reference_rapport']} - feuillet "
                                       f"{ctx.page + 1}/{self.n_pages}")

    def garde(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 60, L - 120, H - 80)
        cur.para("COMPTE RENDU D'INTERVENTION TECHNIQUE",
                 ParagraphStyle("g", parent=self.s_titre, fontSize=15, leading=19, alignment=1),
                 espace=16)
        n = 2 if self.doc["pieges_doc"]["deux_logos"] else 1
        x0 = (L - n * dessins.LOGO_L - (n - 1) * 30) / 2
        self.logos(c, ctx, [(x0, cur.y - dessins.LOGO_H), (x0 + dessins.LOGO_L + 30,
                                                          cur.y - dessins.LOGO_H)])
        cur.saut(dessins.LOGO_H + 30)
        lignes = [f"Compte rendu n° {self.lr['reference_rapport']}, émis le "
                  f"{self.date(self.lr['date_rapport'], self.forme_date)}.", ]
        places = []

        def ligne(libelle, valeur, cle=None):
            lignes.append(f"{libelle} : {valeur}")
            if cle:
                places.append((cle, valeur))

        ligne(self.lib("machine"), self.v["machine"], "machine")
        ligne("Nature de l'équipement", self.lr["type_machine"])
        if not self.doc["pieges_doc"]["logo_seul"]:
            ligne(self.lib("constructeur"), self.v["constructeur"], "constructeur")
        if self.ici("numero_serie", "garde"):
            ligne(self.lib("numero_serie"), self.v["numero_serie"], "numero_serie")
        elif self.absent("numero_serie"):
            ligne(self.lib("numero_serie"), "non relevé")
        ligne("N° d'immobilisation", self.lr["inventaire"])
        if self.ici("site", "garde"):
            ligne(self.lib("site"), self.v["site"], "site")
        ligne("Atelier", self.lr["ligne_client"])
        if self.ici("date_intervention", "garde"):
            ligne(self.lib("date_intervention"),
                  self.date(self.v["date_intervention"], self.forme_date), "date_intervention")
        ligne("Demandeur", self.lr["contact"])
        for l in lignes:
            cur.para(escape(l), self.s_corps, espace=7)
        for cle, val in places:
            ctx.place(cle, val)
        cur.saut(14)
        cur.para("Le présent compte rendu décrit le déroulement de l'intervention, les mesures "
                 "relevées, les actions réalisées et l'avis du technicien sur l'aptitude de "
                 "l'équipement à poursuivre sa production.", self.s_corps)

    def _preparer_tableau(self):
        """Lignes du tableau 1, coupé entre les feuillets 2 et 3."""
        ud = self.unite_vol("volume_dose_ml")
        lib_d = self.lib("volume_dose_ml")
        av = self.vol(self.lr["dose_avant"], ud)
        tol = "± " + self.vol(self.lr["tolerance_ml"], ud)
        res = nombre(self.lr["reservoir_l"], "fr")
        circ = nombre(self.lr["circuit_ml"], "fr")
        leurres = [
            (f"{lib_d} avant réglage", av, self.unite("volume_dose_ml"), "", ("_voisins", av)),
            ("Capacité du réservoir", res, "L", "", ("_voisins", res)),
            ("Volume du circuit", circ, "ml", "", ("_voisins", circ)),
            ("Température du produit", nombre(self.lr["temperature"], "fr", 1), "°C", "", None),
            ("Débit maximal constructeur", nombre(self.lr["debit_max"], "fr"), "ml/min", "", None),
            ("Pression maximale admissible", nombre(self.lr["pression_max"], "fr", 1), "bar", "",
             None),
        ]
        self.r.shuffle(leurres)
        k = self.r.randint(3, 4)
        partie1, reste = leurres[:k], leurres[k:]

        def renvoi(cle):
            e = self.doc["emplacements"][cle]
            return "voir schéma" if e == "schema" else ("voir § III" if e == "recit" else "")

        attendues = []
        val, pl = self.valeur_tableau("volume_dose_ml")
        attendues.append((f"{lib_d} après réglage", val, self.unite("volume_dose_ml"),
                          renvoi("volume_dose_ml") or "moyenne de 10 cycles", pl))
        attendues.append(("Tolérance admise", tol, self.unite("volume_dose_ml"), "",
                          ("_voisins", tol)))
        val, pl = self.valeur_tableau("volume_nominal_ml")
        attendues.append((self.lib("volume_nominal_ml"), val, self.unite("volume_nominal_ml"),
                          renvoi("volume_nominal_ml") or "donnée constructeur", pl))
        if not self.absent("debit_ml_min"):
            val, pl = self.valeur_tableau("debit_ml_min")
            attendues.append((f"{self.lib('debit_ml_min')} après réglage", val, "ml/min",
                              renvoi("debit_ml_min"), pl))
        if self.absent("pression_bar"):
            attendues.append((self.lib("pression_bar"), "non mesurée", "bar", "", None))
        else:
            val, pl = self.valeur_tableau("pression_bar")
            attendues.append((self.lib("pression_bar"), val, "bar", renvoi("pression_bar"), pl))
        partie2 = attendues + reste
        self.r.shuffle(partie2)
        self.tableau = (partie1, partie2)
        for *_, pl in partie2:
            if pl and not pl[0].startswith("_"):
                self.coupe.add(pl[0])
        if self.doc["pieges_doc"]["correction"]:
            self.coupe.add(self.doc["pieges_doc"]["correction"])
        self.entete_repetee = self.r.random() < 0.5

    def _table(self, lignes, entete):
        data = ([["Grandeur", "Valeur", "Unité", "Observation"]] if entete else [])
        places = []
        for lib, val, unite, obs, pl in lignes:
            data.append([self.cellule(lib), val, unite, self.cellule(obs)])
            if pl:
                places.append(pl)
        t = Table(data, colWidths=[190, 90, 60, 135])
        t.setStyle(self.style_table(entete=entete))
        return t, places

    def contexte(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 60, L - 120, H - 70)
        partie1, _ = self.tableau
        table, places = self._table(partie1, True)
        titre = Paragraph("<b>Tableau 1 - Relevés de l'intervention</b>", self.s_corps)
        besoin = cur.hauteur(table) + cur.hauteur(titre) + 12
        cur.para("I. CONTEXTE", self.s_titre, espace=8)
        cur.para(" ".join(self.remplissage[0:2]), self.s_corps, espace=6)
        cur.para(" ".join(self.remplissage[2:4]), self.s_corps, espace=6)
        cur.para("II. CONSTAT", self.s_titre, espace=8)
        html, pl = self.recit()[1]
        cur.para(html, self.s_corps, pl, espace=6)
        i = 4
        while i < len(self.remplissage) - 2:
            texte = " ".join(self.remplissage[i:i + 2])
            if cur.y - cur.hauteur(Paragraph(texte, self.s_corps)) - 6 - besoin < cur.y_bas:
                break
            cur.para(texte, self.s_corps, espace=6)
            i += 2
        self.remplissage = self.remplissage[i:]
        cur.y = cur.y_bas + besoin
        cur.para(titre.text, self.s_corps, espace=4)
        cur.table(table, places)

    def suite(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 60, L - 120, H - 70)
        _, partie2 = self.tableau
        if self.entete_repetee:
            cur.para("<b>Tableau 1 (suite)</b>", self.s_corps, espace=4)
        table, places = self._table(partie2, self.entete_repetee)
        cur.table(table, places, espace=16)
        cur.para("III. ACTIONS RÉALISÉES", self.s_titre, espace=8)
        for html, pl in [self.recit_p3[0], self.recit_p3[2]]:
            cur.para(html, self.s_corps, pl, espace=6)
        for p in self.remplissage[:2]:
            cur.para(p, self.s_corps, espace=6)

    def schema(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 60, L - 120, H - 70)
        cur.para("IV. SCHÉMA DE L'INSTALLATION", self.s_titre, espace=14)
        cur.image(self.schema_image(ctx), dessins.SCHEMA_L, dessins.SCHEMA_H,
                  x=(L - dessins.SCHEMA_L) / 2, espace=14)
        cur.para(self.legende_schema(), self.s_corps)

    def observations(self, c, ctx):
        L, H = self.taille
        self.cadre(c, ctx)
        cur = Curseur(c, ctx, 60, L - 120, H - 70)
        cur.para("V. OBSERVATIONS", self.s_titre, espace=8)
        for html, pl in self.recit_p5:
            cur.para(html, self.s_corps, pl, espace=6)
        if self.ici("reference_piece", "tableau"):
            lignes = [["Référence", "Désignation", "Quantité"],
                      [self.v["reference_piece"], self.cellule(self.lr["piece_nom"]), "1"]]
            t = Table(lignes, colWidths=[130, 245, 100])
            t.setStyle(self.style_table())
            cur.para("<b>Pièces remplacées</b>", self.s_corps, espace=4)
            cur.table(t, [("reference_piece", self.v["reference_piece"])])
        cur.para("VI. CONCLUSION", self.s_titre, espace=8)
        tech = self.v["technicien"] if not self.absent("technicien") else "—"
        cur.para(f"{escape(self.lib('statut'))} : {self.statut_texte()}", self.s_corps,
                 [("statut", self.statut_texte())], espace=4)
        cur.para(f"{escape(self.lib('technicien'))} : {escape(tech)}", self.s_corps,
                 [] if self.absent("technicien") else [("technicien", tech)], espace=4)
        cur.para(f"Visa du responsable de site : {escape(self.lr['valideur'])}", self.s_corps,
                 espace=6)
        cur.image(dessins.signature(f"{self.graine}/{self.doc['id']}/sig"), 120, 37)


GABARITS = {1: Gabarit1, 2: Gabarit2, 3: Gabarit3}
