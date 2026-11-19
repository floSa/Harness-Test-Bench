"""Base des styles en flux (classique, compact, récit, réservé) : pagination automatique,
deux passes (la seconde connaît le nombre de pages), page scannée remplacée après coup."""
import io
import random
from xml.sax.saxutils import escape

from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

import dessins
import textes
from base import Base
from flux import Dessin, Enregistre, image, remplacer_par_scan
from mise_en_page import Contexte, cases_a_cocher


class BaseFlux(Base):
    def __init__(self, doc, graine):
        super().__init__(doc, graine)
        self._etat_r = self.r.getstate()
        self._etat_rp = self.rp.getstate()
        self._remplissage0 = list(self.remplissage)
        self.coupe = set()

    def _reinitialiser(self):
        self.r.setstate(self._etat_r)
        self.rp.setstate(self._etat_rp)
        self.remplissage = list(self._remplissage0)
        for k in ("_paragraphes", "_phrases_fin"):
            self.__dict__.pop(k, None)

    # À fournir par chaque style ----------------------------------------------------------------

    def gabarit_doc(self, flux):
        raise NotImplementedError

    def histoire(self):
        raise NotImplementedError

    def cadre(self, c, doc):
        pass

    # Rendu -------------------------------------------------------------------------------------

    def rendre(self):
        L, H = self.taille
        n_pages = 0
        for _ in range(2):
            self._reinitialiser()
            self.ctx = Contexte(H)
            self.n_pages = n_pages
            self.ref_schema = {"pages": set()}
            self.ref_mesures = {"pages": set()}
            flux = io.BytesIO()
            doc = self.gabarit_doc(flux)
            doc.build(self.histoire())
            n_pages = doc.page
        self.n_pages = n_pages
        pdf = flux.getvalue()
        placements = self.ctx.placements
        # Tableau de mesures coupé entre deux pages.
        if len(self.ref_mesures["pages"]) > 1:
            premiere = min(self.ref_mesures["pages"])
            for p in placements:
                if p.get("table_mesures") and p["page"] > premiere and not p["cle"].startswith("_"):
                    self.coupe.add(p["cle"])
        page_scan = None
        if self.pd.get("scan"):
            exclues = {0} | self.ref_schema["pages"]
            choix = [i for i in range(n_pages) if i not in exclues] or [n_pages - 1]
            page_scan = random.Random(f"{self.graine}/{self.doc['id']}/page_scan").choice(choix)
            pdf = remplacer_par_scan(pdf, page_scan, f"{self.graine}/{self.doc['id']}/scan")
            for p in placements:
                if p["page"] == page_scan:
                    p["mode"] = "image"
        return pdf, placements, page_scan

    # Briques -----------------------------------------------------------------------------------

    def P(self, html, style="corps", notes=(), espace=5):
        return [Enregistre(Paragraph(html, self.s[style] if isinstance(style, str) else style), self.ctx,
                           notes=notes), Spacer(1, espace)]

    def T(self, t, notes_cases=(), espace=8, mesures=False):
        e = Enregistre(t, self.ctx, notes_cases=notes_cases, ref=self.ref_mesures if mesures else None)
        if mesures:
            e.ctx = _Marqueur(self.ctx)
        return [e, Spacer(1, espace)]

    def Im(self, pil, largeur, hauteur, notes=(), espace=6, ref=None):
        return [Enregistre(image(pil, largeur, hauteur), self.ctx, notes=notes, ref=ref), Spacer(1, espace)]

    def sections_flux(self, sections, style_titre="inter"):
        out = []
        for titre, html, notes in sections:
            out.append(KeepTogether(self.P(escape(titre), style_titre, espace=2) + self.P(html, "corps", notes,
                                                                                          espace=8)))
        return out

    def schema_flux(self, titre, largeur):
        out = self.P(escape(titre), "titre", espace=8) if titre else []
        organes = {"doseuse": ("Groupe piston", "Piston unit"), "pompe": ("Tête de pompe", "Pump head"),
                   "remplisseuse": ("Têtes de remplissage", "Filling heads"),
                   "pipette": ("Module de pipetage", "Pipetting module")}
        ts = {"reservoir_nom": self.tr("Réservoir", "Tank"),
              "reservoir": f"{self.tr('Capacité', 'Capacity')} : {self.n(self.lr['reservoir_l'])} L",
              "circuit": f"Circuit : {self.n(self.lr['circuit_ml'])} ml",
              "organe": organes[self.marque["type"]][0 if self.fr else 1]}
        notes = []
        for cle, nom in [("volume_dose_ml", "dose"), ("volume_nominal_ml", "nominal"),
                         ("debit_ml_min", "debit"), ("pression_bar", "pression")]:
            if self.emp(cle) == "schema":
                ts[nom] = f"{self.lib(cle)} : {self.vu(cle)}"
                notes.append(("verite", cle, self.vu(cle), None, "image"))
        larg = min(dessins.SCHEMA_L, largeur)
        out += self.Im(dessins.schema(ts), larg, dessins.SCHEMA_H * larg / dessins.SCHEMA_L, notes,
                       ref=self.ref_schema)
        out += self.P(escape(self.tr("Repères : 1 réservoir ; 2 circuit d'alimentation ; 3 organe de "
                                     "dosage ; 4 manomètre ; 5 sens d'écoulement ; 6 buse de sortie.",
                                     "Key: 1 tank; 2 supply line; 3 dosing unit; 4 pressure gauge; "
                                     "5 flow direction; 6 outlet nozzle.")), "petit")
        return out

    def zones_flux(self, largeur, empile=False):
        """Plaque du moteur (et de la machine) et instruments de mesure."""
        img, notes = self.img_moteur()
        gauche = self.Im(img, 175, 68, notes, espace=2) + \
            self.P(self.tr("Plaque du moteur d'entraînement.", "Drive motor rating plate."), "petit")
        if self.emp("numero_serie") == "plaque":
            img, notes = self.img_plaque_machine()
            gauche += self.Im(img, 175, 68, notes, espace=2) + \
                self.P(self.tr("Plaque signalétique de l'équipement.", "Equipment rating plate."), "petit")
        lt = largeur if empile else largeur - 190
        t, n = self.t_instruments(lt)
        droite = self.T(t, [x + ("texte",) for x in n])
        if empile:
            return gauche + droite
        cadre = Table([[gauche, droite]], colWidths=[190, lt])
        cadre.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        return [cadre, Spacer(1, 8)]

    def table_flux(self, constructeur, largeur):
        t, notes = constructeur(largeur)
        return self.T(t, [x + ("texte",) for x in notes])

    def validation_flux(self, largeur, hauteur=92):
        return [Dessin(largeur, hauteur, lambda c, ctx, w, h: self.bloc_validation(c, ctx, 0, h, w), self.ctx),
                Spacer(1, 6)]

    def statut_flux(self, largeur, cases=False):
        """Statut à l'emplacement « formulaire » : en clair ou par cases à cocher."""
        if self.emp("statut") != "formulaire":
            return []
        k = textes.CODES_STATUT.index(self.v["statut"])
        if cases:
            def dessiner(c, ctx, w, h):
                c.setFont(self.gras, 8)
                c.drawString(0, h - 8, self.lib("statut").upper())
                cases_a_cocher(textes.STATUTS[self.langue], k, self.police)(c, -6, 0, w, h - 4)
                ctx.noter("verite", "statut", textes.STATUTS[self.langue][k], (0, 0, w, h), mode="trace")
            return [Dessin(largeur, 56, dessiner, self.ctx), Spacer(1, 6)]
        lib, txt = self.statut_formulaire()
        t = Table([[self.cel(lib, True), txt]], colWidths=[0.4 * largeur, 0.6 * largeur])
        t.setStyle(self.style_table(entete=False))
        return self.T(t, [(0, 1, "verite", "statut", txt, None, "texte")])

    def synthese_flux(self, largeur):
        syn = self.synthese_provisoire()
        if not syn:
            return []
        cle, lib, txt = syn
        t = Table([[self.cel(self.tr("Synthèse des relevés (provisoire)", "Readings summary (provisional)"), True),
                    self.cel(lib), f"{txt} {self.u[cle]}"]],
                  colWidths=[0.4 * largeur, 0.35 * largeur, 0.25 * largeur])
        t.setStyle(self.style_table(entete=False))
        return self.T(t, [(0, 2, "leurre", cle, txt, "relevé provisoire ; le tableau fait foi", "texte")])

    def regle_flux(self):
        if not self.pd.get("conflit_regle"):
            return []
        return self.P(escape(self.tr("Les valeurs du tableau des mesures font foi ; la synthèse reprend des "
                                     "relevés provisoires.",
                                     "Measurement table values prevail; the summary shows provisional "
                                     "readings.")), "petit")

    def note_unites_flux(self):
        if self.place_unite != "note":
            return []
        return self.P(escape(self.tr(
            f"Unités : volumes en {self.u['volume_dose_ml']}, débits en {self.u['debit_ml_min']}, pressions "
            f"en {self.u['pression_bar']}, températures en °C.",
            f"Units: volumes in {self.u['volume_dose_ml']}, flow in {self.u['debit_ml_min']}, pressure in "
            f"{self.u['pression_bar']}, temperature in °C.")), "petit")

    def entete_ref(self, c, x, y, police, taille, aligner_droite=True, prefixe=None):
        """Référence du rapport en en-tête de page (si elle est à l'emplacement « formulaire »)."""
        if self.emp("reference_rapport") != "formulaire":
            return
        ref = self.v["reference_rapport"]
        txt = f"{prefixe or self.tr('Réf.', 'Ref.')} {ref}"
        c.setFont(police, taille)
        w = c.stringWidth(txt, police, taille)
        x0 = x - w if aligner_droite else x
        c.drawString(x0, y, txt)
        x1 = x0 + w
        self.ctx.page = c.getPageNumber() - 1
        self.ctx.noter("verite", "reference_rapport", ref,
                       (x1 - c.stringWidth(ref, police, taille), y - 3, x1, y + taille))

    def pied_impression(self, c, x, y, taille=7.5):
        imp = self.d(self.lr["impression"])
        c.setFont(self.police, taille)
        txt = f"{self.tr('Imprimé le', 'Printed on')} {imp}"
        c.drawString(x, y, txt)
        self.ctx.page = c.getPageNumber() - 1
        self.ctx.noter("leurre", "date_validation", imp,
                       (x, y - 3, x + c.stringWidth(txt, self.police, taille) + 2, y + taille),
                       raison="date d'impression")


class _Marqueur:
    """Contexte qui marque les écritures du tableau de mesures (détection du tableau coupé)."""

    def __init__(self, ctx):
        self.ctx = ctx

    def __getattr__(self, k):
        return getattr(self.ctx, k)

    def __setattr__(self, k, v):
        if k == "ctx":
            object.__setattr__(self, k, v)
        else:
            setattr(self.ctx, k, v)

    def noter(self, *a, **k):
        self.ctx.noter(*a, **k)
        self.ctx.placements[-1]["table_mesures"] = True
