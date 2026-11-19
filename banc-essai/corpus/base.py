"""Base commune des styles : lecture du plan, écriture des valeurs, vérité, textes et blocs.

Chaque style (style_*.py) ne fait que disposer les blocs sur ses pages. L'emplacement de
chaque valeur vient du plan : formulaire, tableau, phrase, paragraphe, schema, logo, plaque,
tampon, calcul ou absent.
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
import textes
from mise_en_page import Barree, Contexte, Curseur

NBSP = " "


class Base:
    taille = A4
    pages_scannables = (1, 2)
    densite = 2          # phrases de remplissage par section de texte libre
    tolerance_caracteristiques = False   # vrai si le tableau de mesures n'a pas de case tolérance
    polices = [("Helvetica", "Helvetica-Bold"), ("Times-Roman", "Times-Bold")]

    def __init__(self, doc, graine):
        self.doc, self.graine = doc, graine
        self.v, self.lr, self.p = doc["valeurs"], doc["leurres"], doc["pieges"]
        self.pd = doc["pieges_doc"]
        self.langue = doc["langue"]
        self.fr = self.langue == "fr"
        self.presta, self.marque = doc["prestataire"], doc["marque"]
        self.r = random.Random(f"{graine}/{doc['id']}/rendu")
        rp = random.Random(self.presta["graine_page"])      # choix propres au prestataire
        self.rp = rp
        self.police, self.gras = rp.choice(self.polices)
        self.style_nb = self.pd.get("style_nombres") or rp.choice(
            ["fr", "fr_colle", "de"] if self.fr else ["en", "en_colle", "ch"])
        self.forme_date = self.pd.get("forme_date") or rp.choice(
            formats.FORMES_DATE[self.langue] + (["us"] if not self.fr else []))
        self.place_unite = self.pd.get("place_unite") or rp.choice(
            ["colonne", "entete", "cellule", "note"])
        self.marqueur_vide = rp.choice(["—", "", "n.c." if self.fr else "n/a"])
        corps = rp.choice([9, 9.5, 10])
        base = ParagraphStyle("b", fontName=self.police, fontSize=corps, leading=corps * 1.32)
        self.s = {"corps": base,
                  "titre": ParagraphStyle("t", parent=base, fontName=self.gras, fontSize=corps + 3,
                                          leading=(corps + 3) * 1.3),
                  "inter": ParagraphStyle("i", parent=base, fontName=self.gras, fontSize=corps + 0.5,
                                          leading=(corps + 0.5) * 1.3),
                  "petit": ParagraphStyle("p", parent=base, fontSize=corps - 1.5,
                                          leading=(corps - 1.5) * 1.3),
                  "case": ParagraphStyle("c", parent=base, fontSize=8, leading=9.6),
                  "case_g": ParagraphStyle("cg", parent=base, fontName=self.gras, fontSize=8,
                                           leading=9.6)}
        self.logo_presta = dessins.logo(self.presta)
        self.logo_marque = dessins.logo(self.marque)
        self.remplissage = self.r.sample(textes.REMPLISSAGE[self.langue],
                                         len(textes.REMPLISSAGE[self.langue]))
        self.verite = {}
        self._preparer()

    # Accès --------------------------------------------------------------------------------------

    def n(self, x, min_dec=0):
        return formats.nombre(x, self.style_nb, min_dec)

    def d(self, iso, forme=None):
        return formats.date(iso, forme or self.forme_date)

    def dl(self, iso):
        return formats.date(iso, "long_fr" if self.fr else "long_en")

    def emp(self, cle):
        return self.doc["emplacements"][cle]

    def absent(self, cle):
        return self.emp(cle) == "absent"

    def lib(self, cle):
        return self.doc["libelles"][cle]

    def tr(self, fr, en):
        return fr if self.fr else en

    def remplir(self, k=1):
        out = []
        for _ in range(k):
            if not self.remplissage:
                self.remplissage = self.r.sample(textes.REMPLISSAGE[self.langue],
                                                 len(textes.REMPLISSAGE[self.langue]))
            out.append(self.remplissage.pop())
        return out

    # Valeurs écrites et vérité -----------------------------------------------------------------

    def _preparer(self):
        u = self.doc["unites"]
        self.u, self.ecrit = {}, {}
        for cle, g in [("volume_dose_ml", "volume"), ("volume_nominal_ml", "volume"),
                       ("tolerance_ml", "volume"), ("debit_ml_min", "debit"),
                       ("pression_bar", "pression")]:
            aff, ver = formats.convertir(self.v[cle], g, u[cle])
            self.u[cle] = u[cle]
            self.ecrit[cle] = self.n(aff, 1 if (cle == "pression_bar" and u[cle] == "bar") else 0)
            self.verite[cle] = ver
        self.f_dose = formats.UNITES["volume"][u["volume_dose_ml"]]
        self.pct = "tolerance_en_pourcent" in self.p["tolerance_ml"]
        if self.pct:
            self.ecrit_tol = f"± {self.n(self.lr['pct'])} %"
            self.verite["tolerance_ml"] = round(self.verite["volume_nominal_ml"] * self.lr["pct"] / 100, 6)
        else:
            self.ecrit_tol = f"± {self.ecrit['tolerance_ml']}"
        for cle in ["machine", "constructeur", "numero_serie", "site", "reference_rapport",
                    "date_intervention", "date_validation", "reference_piece", "technicien", "statut"]:
            self.verite[cle] = self.v[cle]
        for cle in list(self.verite):
            if self.absent(cle):
                self.verite[cle] = None
        if self.emp("volume_dose_ml") == "calcul":
            self.p["volume_dose_ml"] = self.p["volume_dose_ml"] + ["moyenne_a_calculer"]
        # Valeur fausse imprimée (valeur barrée ou erratum).
        self.faute = {}
        for cle in ["volume_dose_ml", "volume_nominal_ml", "debit_ml_min", "pression_bar"]:
            if {"valeur_barree", "erratum"} & set(self.p[cle]):
                g = "volume" if cle.startswith("volume") else ("debit" if cle == "debit_ml_min" else "pression")
                f = formats.UNITES[g][self.u[cle]]
                faux = self.v[cle] * (1 + self.r.choice([-1, 1]) * self.r.uniform(0.07, 0.15))
                pas = self.lr["pas"] if g == "volume" else (0.1 if g == "pression" else 1)
                faux = round(round(faux / pas) * pas, 6)
                self.faute[cle] = self.n(round(faux / f, 6) if f in formats.FACTEURS_DECIMAUX
                                         else round(faux / f, 2))

    def vu(self, cle):
        """Valeur numérique écrite avec son unité (tolérance : ± ... ou ± ... %)."""
        if cle == "tolerance_ml":
            return self.ecrit_tol if self.pct else f"{self.ecrit_tol} {self.u[cle]}"
        return f"{self.ecrit[cle]} {self.u[cle]}"

    def cv(self, cle, x):
        """Leurre de débit ou de pression, écrit dans l'unité d'affichage de la clé."""
        g = "debit" if cle == "debit_ml_min" else "pression"
        aff, _ = formats.convertir(x, g, self.u[cle])
        return self.n(aff, 1 if (cle == "pression_bar" and self.u[cle] == "bar") else 0)

    def moy(self, essais_ml):
        """Moyenne d'essais, arrondie au pas de mesure, écrite dans l'unité de la dose."""
        pas = self.lr["pas"]
        return self.vol(round(round(sum(essais_ml) / len(essais_ml) / pas) * pas, 6))

    def vol(self, x_ml):
        """Volume leurre écrit dans l'unité de la dose."""
        return self.n(round(x_ml / self.f_dose, 6))

    def texte_valeur(self, cle):
        """Chaîne de la valeur juste pour les champs non numériques."""
        if cle.startswith("date"):
            return self.d(self.v[cle])
        if cle == "statut":
            return textes.STATUTS[self.langue][textes.CODES_STATUT.index(self.v["statut"])]
        return self.v[cle]

    # Formulaire (page d'entrée, cartouche) ------------------------------------------------------

    def entrees_formulaire(self):
        """Entrées du formulaire de tête, valeurs et leurres mêlés.

        Une entrée : {"cle", "titre", "valeur", "notes", "img"?, "groupe"}. Une valeur prévue
        ailleurs est omise ou remplacée par un marqueur vide, au choix du document.
        """
        t, v, lr = self.tr, self.v, self.lr
        E = []

        def champ(cle, groupe, valeur=None):
            e = self.emp(cle)
            if e == "formulaire":
                val = valeur if valeur is not None else self.texte_valeur(cle)
                E.append({"cle": cle, "titre": self.lib(cle), "valeur": val, "groupe": groupe,
                          "notes": [("verite", cle, val, None)]})
            elif e == "logo" and cle == "constructeur":
                E.append({"cle": cle, "titre": self.lib(cle), "img": self.logo_marque, "groupe": groupe,
                          "notes": [("verite", cle, v[cle], None)]})
            elif e == "absent" and cle == "numero_serie":
                E.append({"cle": cle, "titre": self.lib(cle), "groupe": groupe,
                          "valeur": self.r.choice([t("illisible", "unreadable"),
                                                   t("plaque absente", "plate missing"), "—"])})
            elif self.r.random() < 0.5:
                E.append({"cle": cle, "titre": self.lib(cle), "groupe": groupe,
                          "valeur": self.marqueur_vide or "—"})

        if self.emp("reference_rapport") == "formulaire":
            champ("reference_rapport", "ref")
        if "version_remplacee" in self.p["reference_rapport"] or self.pd.get("version_remplacee"):
            E.append({"cle": None, "titre": t("Annule et remplace", "Supersedes"),
                      "valeur": lr["ref_ancienne"], "groupe": "ref",
                      "notes": [("leurre", "reference_rapport", lr["ref_ancienne"],
                                 "référence de la version annulée")]})
        E.append({"cle": None, "titre": t("N° de commande", "PO number"), "valeur": lr["commande"],
                  "groupe": "ref", "notes": [("leurre", "reference_rapport", lr["commande"], "n° de commande")]})
        E.append({"cle": None, "titre": t("N° d'affaire", "Job no."), "valeur": lr["affaire"],
                  "groupe": "ref", "notes": [("leurre", "reference_rapport", lr["affaire"], "n° d'affaire")]})
        E.append({"cle": None, "titre": t("Client", "Customer"),
                  "valeur": f"{lr['client']}\n{t('Siège', 'Head office')} : {lr['ville_siege']}",
                  "groupe": "lieu", "notes": [("leurre", "site", lr["ville_siege"], "ville du siège du client")]})
        champ("site", "lieu")
        E.append({"cle": None, "titre": t("Installation", "Installation"),
                  "valeur": f"{lr['ligne']}\n{lr['type_machine']}", "groupe": "lieu"})
        champ("machine", "equipement")
        champ("constructeur", "equipement")
        champ("numero_serie", "equipement")
        E.append({"cle": None, "titre": t("N° d'inventaire", "Asset no."), "valeur": lr["inventaire"],
                  "groupe": "equipement",
                  "notes": [("leurre", "numero_serie", lr["inventaire"], "n° d'inventaire du client")]})
        if self.emp("volume_nominal_ml") == "formulaire":
            champ("volume_nominal_ml", "equipement", self.vu("volume_nominal_ml"))
        if self.emp("tolerance_ml") == "formulaire":
            champ("tolerance_ml", "equipement", self.vu("tolerance_ml"))
        for cle_l, titre, raison, cle_v in [
                ("demande", t("Date de la demande", "Request date"), "date de la demande",
                 "date_intervention"),
                ("emission", t("Date d'émission", "Issue date"), "date d'émission", "date_validation")]:
            E.append({"cle": None, "titre": titre, "valeur": self.d(lr[cle_l]), "groupe": "dates",
                      "notes": [("leurre", cle_v, self.d(lr[cle_l]), raison)]})
        champ("date_intervention", "dates")
        return E

    # Textes ------------------------------------------------------------------------------------

    def phrase(self, cle):
        """Phrase courte avec libellé (emplacement « phrase »)."""
        val = self.vu(cle) if cle in self.u else self.texte_valeur(cle)
        if cle == "date_intervention" or cle == "date_validation":
            val = self.dl(self.v[cle])
        modeles = (["Pour mémoire, {l} : {v}.", "À noter, {l} : {v}.", "Information complémentaire, {l} : {v}."]
                   if self.fr else ["For the record, {l}: {v}.", "Note, {l}: {v}.",
                                    "Additional information, {l}: {v}."])
        l = self.lib(cle)
        l = l if l.isupper() or l[:2].isupper() else l[0].lower() + l[1:]
        html = escape(self.r.choice(modeles).format(l=l, v=val))
        return html, [("verite", cle, val, None)]

    def paragraphes(self):
        if not hasattr(self, "_paragraphes"):
            self._paragraphes = self._paragraphes_()
        return self._paragraphes

    def _paragraphes_(self):
        """Sections de texte libre : [(titre, html, notes)]. Les valeurs à l'emplacement
        « paragraphe » y sont écrites sans libellé, au milieu de phrases de remplissage."""
        T = textes.TITRES[self.langue]
        v, lr, fr = self.v, self.lr, self.fr
        P = lambda c: self.emp(c) == "paragraphe"
        sections = []

        def section(cle_titre, phrases, notes):
            corps = self.remplir(self.r.randint(1, self.densite)) + phrases + \
                    self.remplir(self.r.randint(0, self.densite))
            sections.append((T[cle_titre], escape(" ".join(corps)), notes))

        # Équipement.
        ph, no = [], []
        m = lr["moteur"]
        base = self.tr(f"L'intervention porte sur l'équipement de dosage de la {lr['ligne'].lower()}",
                       f"The visit concerns the dosing equipment of {lr['ligne'].lower()}")
        if P("machine"):
            base = self.tr(f"L'intervention porte sur la {lr['type_machine']} {v['machine']}",
                           f"The visit concerns the {lr['type_machine']} {v['machine']}")
            no.append(("verite", "machine", v["machine"], None))
        if P("constructeur"):
            base += self.tr(f", sortie des ateliers {v['constructeur']}", f", built by {v['constructeur']}")
            no.append(("verite", "constructeur", v["constructeur"], None))
        if P("numero_serie"):
            base += self.tr(f", dont la plaque porte le numéro {v['numero_serie']}",
                            f", whose plate reads {v['numero_serie']}")
            no.append(("verite", "numero_serie", v["numero_serie"], None))
        ph.append(base + ".")
        ph.append(self.tr(f"Elle est entraînée par un moteur {m['marque']} de type {m['type']}.",
                          f"It is driven by a {m['marque']} motor, type {m['type']}."))
        no += [("leurre", "constructeur", m["marque"], "marque du moteur"),
               ("leurre", "machine", m["type"], "type du moteur")]
        section("equipement", ph, no)

        # Lieu et date.
        ph, no = [], []
        dem = self.dl(lr["demande"])
        if P("site") and P("date_intervention"):
            ph.append(self.tr(f"Le déplacement chez le client, {v['site']}, a eu lieu le "
                              f"{self.dl(v['date_intervention'])}, à la suite d'une demande du {dem}.",
                              f"The visit to the customer, {v['site']}, took place on "
                              f"{self.dl(v['date_intervention'])}, following a request of {dem}."))
        elif P("site"):
            ph.append(self.tr(f"Le déplacement chez le client, {v['site']}, fait suite à une demande "
                              f"du {dem}.", f"The visit to the customer, {v['site']}, follows a "
                                            f"request of {dem}."))
        elif P("date_intervention"):
            ph.append(self.tr(f"Le déplacement a eu lieu le {self.dl(v['date_intervention'])}, à la "
                              f"suite d'une demande du {dem}.",
                              f"The visit took place on {self.dl(v['date_intervention'])}, following "
                              f"a request of {dem}."))
        else:
            ph.append(self.tr(f"La demande d'intervention a été reçue le {dem}.",
                              f"The service request was received on {dem}."))
        if P("site"):
            no.append(("verite", "site", v["site"], None))
        if P("date_intervention"):
            no.append(("verite", "date_intervention", self.dl(v["date_intervention"]), None))
        no.append(("leurre", "date_intervention", dem, "date de la demande"))
        ph.append(self.tr(f"Le siège du client se trouve à {lr['ville_siege']}.",
                          f"The customer's head office is in {lr['ville_siege']}."))
        no.append(("leurre", "site", lr["ville_siege"], "ville du siège du client"))
        section("lieu", ph, no)

        # Réglages.
        ph, no = [], []
        ud = self.u["volume_dose_ml"]
        av = f"{self.vol(lr['avant'])} {ud}"
        if P("volume_dose_ml"):
            ph.append(self.tr(f"Après plusieurs ajustements de la course, la quantité délivrée s'est "
                              f"stabilisée autour de {self.vu('volume_dose_ml')} en moyenne, contre {av} "
                              f"à l'arrivée.",
                              f"After several stroke adjustments, the delivered quantity settled at "
                              f"{self.vu('volume_dose_ml')} on average, against {av} on arrival."))
            no.append(("verite", "volume_dose_ml", self.vu("volume_dose_ml"), None))
        else:
            ph.append(self.tr(f"À l'arrivée, la quantité délivrée était de {av} en moyenne.",
                              f"On arrival the delivered quantity averaged {av}."))
        no.append(("leurre", "volume_dose_ml", self.vol(lr["avant"]), "dose avant réglage"))
        if P("volume_nominal_ml"):
            ph.append(self.tr(f"La valeur visée par le client est de {self.vu('volume_nominal_ml')}.",
                              f"The customer's target value is {self.vu('volume_nominal_ml')}."))
            no.append(("verite", "volume_nominal_ml", self.vu("volume_nominal_ml"), None))
        if P("tolerance_ml"):
            ph.append(self.tr(f"L'écart admis par le cahier des charges du client est de "
                              f"{self.vu('tolerance_ml')}.",
                              f"The deviation allowed by the customer's specification is "
                              f"{self.vu('tolerance_ml')}."))
            no.append(("verite", "tolerance_ml", self.vu("tolerance_ml"), None))
        if P("debit_ml_min"):
            dm = f"{self.cv('debit_ml_min', lr['debit_max'])} {self.u['debit_ml_min']}"
            ph.append(self.tr(f"L'équipement débite alors {self.vu('debit_ml_min')}, loin de son "
                              f"maximum de {dm}.",
                              f"The equipment then delivers {self.vu('debit_ml_min')}, well below its "
                              f"maximum of {dm}."))
            no += [("verite", "debit_ml_min", self.vu("debit_ml_min"), None),
                   ("leurre", "debit_ml_min", dm.rsplit(" ", 1)[0], "débit maximal")]
        if P("pression_bar"):
            tar = f"{self.n(lr['tarage'], 1)} bar"
            ph.append(self.tr(f"La pression s'est stabilisée à {self.vu('pression_bar')}, la soupape "
                              f"restant tarée à {tar}.",
                              f"Pressure settled at {self.vu('pression_bar')}, the relief valve "
                              f"remaining set at {tar}."))
            no += [("verite", "pression_bar", self.vu("pression_bar"), None),
                   ("leurre", "pression_bar", self.n(lr["tarage"], 1), "tarage de la soupape")]
        section("reglages", ph, no)

        # Pièces.
        ph, no = [], []
        (ref0, nom0), (ref1, nom1), (ref2, nom2) = lr["pieces"][:3]
        if P("reference_piece"):
            ph.append(self.tr(f"Le {nom0} usé a été remplacé par un élément neuf portant la "
                              f"référence {ref0}.",
                              f"The worn {nom0} was replaced with a new item, reference {ref0}."))
            no.append(("verite", "reference_piece", ref0, None))
        elif self.absent("reference_piece"):
            ph.append(self.tr(f"Aucun remplacement n'a été nécessaire ; la pièce {ref2} ({nom2}) a "
                              f"toutefois été commandée par précaution.",
                              f"No replacement was needed; part {ref2} ({nom2}) was nevertheless "
                              f"ordered as a precaution."))
            no.append(("leurre", "reference_piece", ref2, "pièce commandée, non posée"))
        ph.append(self.tr(f"La pièce {ref1} ({nom1}) a été contrôlée et jugée en bon état.",
                          f"Part {ref1} ({nom1}) was inspected and found in good condition."))
        no.append(("leurre", "reference_piece", ref1, "pièce contrôlée, non remplacée"))
        section("pieces", ph, no)

        # Équipe.
        ph, no = [], []
        if P("technicien"):
            ph.append(self.tr(f"{v['technicien']} a conduit l'intervention avec l'appui de "
                              f"{lr['accompagnant']}, à la demande de {lr['demandeur']}.",
                              f"{v['technicien']} led the visit with the support of "
                              f"{lr['accompagnant']}, at the request of {lr['demandeur']}."))
            no.append(("verite", "technicien", v["technicien"], None))
        else:
            ph.append(self.tr(f"{lr['accompagnant']} a participé à l'intervention, à la demande de "
                              f"{lr['demandeur']}.",
                              f"{lr['accompagnant']} took part in the visit, at the request of "
                              f"{lr['demandeur']}."))
        no += [("leurre", "technicien", lr["accompagnant"], "accompagnant"),
               ("leurre", "technicien", lr["demandeur"], "demandeur côté client")]
        section("equipe", ph, no)

        # Avis.
        ph, no = [], []
        if P("statut"):
            avis = textes.AVIS[(self.langue, v["statut"])]
            ph.append(self.tr(f"Au terme des essais, {avis}.", f"At the end of the tests, {avis}."))
            no.append(("verite", "statut", avis, None))
        else:
            ph.append(self.tr("Les essais ont été conduits jusqu'à stabilisation des mesures.",
                              "Tests were run until readings were stable."))
        section("avis", ph, no)

        # Validation.
        ph, no = [], []
        ver = self.dl(lr["verification"])
        if P("date_validation"):
            ph.append(self.tr(f"Relu le {ver}, le rapport a été approuvé par {lr['approbateur']} le "
                              f"{self.dl(v['date_validation'])}.",
                              f"Reviewed on {ver}, the report was approved by {lr['approbateur']} on "
                              f"{self.dl(v['date_validation'])}."))
            no.append(("verite", "date_validation", self.dl(v["date_validation"]), None))
        else:
            ph.append(self.tr(f"Le rapport a été relu le {ver}.", f"The report was reviewed on {ver}."))
        no.append(("leurre", "date_validation", ver, "date de vérification"))
        section("validation", ph, no)
        return sections

    def phrases_fin(self):
        if not hasattr(self, "_phrases_fin"):
            self._phrases_fin = self._phrases_fin_()
        return self._phrases_fin

    def _phrases_fin_(self):
        """Phrases de la partie « observations » : valeurs à l'emplacement « phrase »,
        erratum, règle de priorité, statut d'arrivée, prochaine visite, leurres voisins."""
        v, lr = self.v, self.lr
        out = []
        cles = [c for c in self.doc["emplacements"] if self.emp(c) == "phrase"]
        self.r.shuffle(cles)
        for c in cles:
            out.append(self.phrase(c))
        for cle in self.faute:
            if "erratum" in self.p[cle]:
                juste, faux = self.vu(cle), f"{self.faute[cle]} {self.u[cle]}"
                l = self.lib(cle).lower()
                out.append((escape(self.tr(f"Erratum : dans le tableau des mesures, lire {juste} au "
                                           f"lieu de {faux} pour {l}.",
                                           f"Erratum: in the measurement table, read {juste} instead "
                                           f"of {faux} for {l}.")),
                            [("verite", cle, juste, None)]))
        vo = lr["voisin"]
        dv, pv = self.cv("debit_ml_min", vo["debit"]), self.n(vo["pression"], 1)
        out.append((escape(self.tr(
            f"Le convoyeur amont {vo['modele']} (débit {dv} {self.u['debit_ml_min']}, pression {pv} bar) "
            f"n'est pas concerné par cette intervention ; le réseau d'air de l'atelier est à "
            f"{self.n(lr['air'], 1)} bar.",
            f"The upstream conveyor {vo['modele']} (flow {dv} {self.u['debit_ml_min']}, pressure {pv} bar) "
            f"is outside the scope of this visit; the workshop air network runs at "
            f"{self.n(lr['air'], 1)} bar.")),
            [("leurre", "machine", vo["modele"], "équipement voisin"),
             ("leurre", "debit_ml_min", dv, "débit de l'équipement voisin"),
             ("leurre", "pression_bar", pv, "pression de l'équipement voisin"),
             ("leurre", "pression_bar", self.n(lr["air"], 1), "réseau d'air de l'atelier")]))
        arrivee = textes.STATUTS[self.langue][1]
        out.append((escape(self.tr(f"À l'arrivée, l'équipement était jugé {arrivee.lower()}.",
                                   f"On arrival the equipment was rated {arrivee.lower()}.")),
                    [("leurre", "statut", arrivee.lower(), "statut à l'arrivée")]))
        pv_ = self.d(lr["prochaine"])
        out.append((escape(self.tr(f"Prochaine visite préventive : {pv_}.", f"Next preventive visit: {pv_}.")),
                    [("leurre", "date_intervention", pv_, "date de la prochaine visite")]))
        return out

    # Blocs -------------------------------------------------------------------------------------

    def style_table(self, extra=(), entete=True):
        cmds = [("FONT", (0, 0), (-1, -1), self.police, 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
        if entete:
            cmds += [("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
                     ("FONT", (0, 0), (-1, 0), self.gras, 8)]
        return TableStyle(cmds + list(extra))

    def cel(self, texte, gras=False):
        return Paragraph(escape(texte), self.s["case_g" if gras else "case"])

    def val_u(self, texte, unite):
        """Valeur dans une case : avec unité seulement si le prestataire l'écrit dans la case."""
        return f"{texte} {unite}" if self.place_unite == "cellule" and texte not in ("—", "", "n.m.") else texte

    def lib_u(self, libelle, unite):
        return f"{libelle} ({unite})" if self.place_unite == "entete" else libelle

    def note_unites(self, cur):
        if self.place_unite == "note":
            cur.para(escape(self.tr(
                f"Unités : volumes en {self.u['volume_dose_ml']}, débits en {self.u['debit_ml_min']}, "
                f"pressions en {self.u['pression_bar']}, températures en °C.",
                f"Units: volumes in {self.u['volume_dose_ml']}, flow in {self.u['debit_ml_min']}, "
                f"pressure in {self.u['pression_bar']}, temperature in °C.")), self.s["petit"])

    def apres(self, cle, mode_essais=False):
        """Case « après réglage » d'une valeur numérique : (contenu, notes [(role, texte, raison, mode)])."""
        if self.absent(cle):
            return "n.m.", []
        if "valeur_barree" in self.p[cle]:
            img = dessins.manuscrit(self.val_u(self.ecrit[cle], self.u[cle]),
                                    f"{self.graine}/{self.doc['id']}/main/{cle}")
            return (Barree(self.val_u(self.faute[cle], self.u[cle]), self.police, 8, img),
                    [("erronee", self.faute[cle], "valeur imprimée barrée", "texte"),
                     ("verite", self.ecrit[cle], None, "image")])
        if "erratum" in self.p[cle]:
            return self.val_u(self.faute[cle], self.u[cle]), [("erronee", self.faute[cle],
                                                               "valeur rectifiée par l'erratum", "texte")]
        if self.emp(cle) == "tableau":
            return self.val_u(self.ecrit[cle], self.u[cle]), [("verite", self.ecrit[cle], None, "texte")]
        return self.marqueur_vide or "—", []

    def ajouter_notes(self, notes, ligne, col, cle, liste):
        for role, texte, raison, mode in liste:
            notes.append((ligne, col, role, cle, texte, raison, mode))

    def essais(self):
        """Essais avant et après réglage, écrits dans l'unité de la dose."""
        lr = self.lr
        return ([[self.vol(x) for x in t] for t in lr["essais_avant"]],
                [[self.vol(x) for x in t] for t in lr["essais_apres"]])

    def calcul(self):
        return self.emp("volume_dose_ml") == "calcul"

    def table_pieces(self, cur, titre=True):
        t, notes = self.t_pieces(cur.l)
        cur.table(t, notes)
        if self.absent("reference_piece"):
            cur.para(self.texte_sans_piece(), self.s["corps"])

    def texte_sans_piece(self):
        return self.tr("Aucune pièce n'a été remplacée lors de cette visite.",
                       "No part was replaced during this visit.")

    def t_pieces(self, largeur):
        lr = self.lr
        lignes = [[self.tr("Référence", "Part no."), self.tr("Désignation", "Description"), "Action",
                   self.tr("Prix unitaire HT", "Unit price")]]
        notes = []
        actions = (["remplacée", "contrôlée, conservée", "commandée (non posée)", "proposée au devis"]
                   if self.fr else ["replaced", "inspected, kept", "ordered (not fitted)", "quoted"])
        raisons = [None, "pièce contrôlée, non remplacée", "pièce commandée, non posée",
                   "pièce proposée au devis"]
        for k, ((ref, nom), prix) in enumerate(zip(lr["pieces"], lr["prix"])):
            if k == 0 and self.emp("reference_piece") != "tableau":
                continue
            lignes.append([ref, self.cel(nom), actions[k], f"{self.n(prix, 2)} €"])
            notes.append((len(lignes) - 1, 0, "verite" if k == 0 else "leurre", "reference_piece", ref,
                          raisons[k]))
        t = Table(lignes, colWidths=[0.2 * largeur, 0.36 * largeur, 0.25 * largeur, 0.19 * largeur])
        t.setStyle(self.style_table())
        return t, notes

    def table_chronologie(self, cur):
        t, notes = self.t_chronologie(cur.l)
        cur.table(t, notes)

    def t_chronologie(self, largeur):
        """Dates de l'affaire : la date d'intervention y figure si le plan la met en tableau."""
        lr, v = self.lr, self.v
        lignes = [[self.tr("Étape", "Step"), "Date"]]
        notes = []
        for lib, iso, cle, role, raison in [
                (self.tr("Incident signalé", "Incident reported"), lr["incident"], "date_intervention",
                 "leurre", "date de l'incident"),
                (self.tr("Demande d'intervention", "Service request"), lr["demande"], "date_intervention",
                 "leurre", "date de la demande"),
                (self.lib("date_intervention"), v["date_intervention"], "date_intervention", "verite", None),
                (self.tr("Émission du rapport", "Report issued"), lr["emission"], "date_validation",
                 "leurre", "date d'émission")]:
            if role == "verite" and self.emp("date_intervention") != "tableau":
                continue
            lignes.append([lib, self.d(iso)])
            notes.append((len(lignes) - 1, 1, role, cle, self.d(iso), raison))
        t = Table(lignes, colWidths=[0.45 * largeur, 0.25 * largeur])
        t.setStyle(self.style_table())
        return t, notes

    def t_instruments(self, lt):
        lr = self.lr
        lignes = [["Instrument", self.tr("Marque", "Make"), self.tr("N° série", "Serial"),
                   self.tr("Étalonné le", "Calibrated")]]
        notes = []
        for k, ins in enumerate(lr["instruments"], start=1):
            dte = self.d(ins["etalonnage"])
            lignes.append([self.cel(ins["nom"]), ins["marque"], ins["serie"], dte])
            notes += [(k, 1, "leurre", "constructeur", ins["marque"], "marque d'un instrument de mesure"),
                      (k, 2, "leurre", "numero_serie", ins["serie"], "n° de série d'un instrument"),
                      (k, 3, "leurre", "date_validation", dte, "date d'étalonnage d'un instrument")]
        t = Table(lignes, colWidths=[0.28 * lt, 0.22 * lt, 0.22 * lt, 0.28 * lt])
        t.setStyle(self.style_table())
        return t, notes

    def img_moteur(self):
        m = self.lr["moteur"]
        img = dessins.plaque([f"{m['marque'].upper()}  MOTOR", f"TYPE {m['type']}", f"N° {m['serie']}",
                              f"{self.n(m['kw'])} kW  {m['trmin']} min-1", f"{m['tension']}  50 Hz  IP55"])
        notes = [("leurre", "constructeur", m["marque"], "marque du moteur", "image"),
                 ("leurre", "numero_serie", m["serie"], "n° de série du moteur", "image"),
                 ("leurre", "machine", m["type"], "type du moteur", "image")]
        return img, notes

    def img_plaque_machine(self):
        img = dessins.plaque([self.v["machine"].upper(), f"S/N {self.v['numero_serie']}",
                              self.lr["type_machine"][:30], "230 V  50 Hz"])
        return img, [("verite", "numero_serie", self.v["numero_serie"], None, "image")]

    def zones_ambigues(self, cur, ctx, largeur_table=None):
        """Plaque du moteur (image) à gauche, instruments de mesure à droite ; plaque de la
        machine si le n° de série n'est lisible que là."""
        lr, fr = self.lr, self.fr
        m = lr["moteur"]
        plaque = dessins.plaque([f"{m['marque'].upper()}  MOTOR", f"TYPE {m['type']}", f"N° {m['serie']}",
                                 f"{self.n(m['kw'])} kW  {m['trmin']} min-1", f"{m['tension']}  50 Hz  IP55"])
        y0 = cur.y
        bb = cur.image(plaque, 190, 74, espace=3)
        for cle, txt, raison in [("constructeur", m["marque"], "marque du moteur"),
                                 ("numero_serie", m["serie"], "n° de série du moteur"),
                                 ("machine", m["type"], "type du moteur")]:
            ctx.noter("leurre", cle, txt, bb, mode="image", raison=raison)
        cur.para(self.tr("Plaque du moteur d'entraînement.", "Drive motor rating plate."), self.s["petit"])
        if self.emp("numero_serie") == "plaque":
            pm = dessins.plaque([self.v["machine"].upper(), f"S/N {self.v['numero_serie']}",
                                 self.lr["type_machine"][:30], "230 V  50 Hz"])
            bb = cur.image(pm, 190, 74, espace=3)
            ctx.noter("verite", "numero_serie", self.v["numero_serie"], bb, mode="image")
            cur.para(self.tr("Plaque signalétique de l'équipement.", "Equipment rating plate."),
                     self.s["petit"])
        bas_gauche = cur.y
        lt = largeur_table or (cur.l - 205)
        t, notes = self.t_instruments(lt)
        sauve_l, cur.y, cur.l = cur.l, y0, lt
        cur.table(t, notes, x=cur.x + sauve_l - lt)
        cur.l = sauve_l
        cur.y = min(bas_gauche, cur.y) - 4

    def schema(self, cur, ctx, titre):
        fr = self.fr
        cur.para(titre, self.s["titre"], espace=12)
        organes = {"doseuse": ("Groupe piston", "Piston unit"), "pompe": ("Tête de pompe", "Pump head"),
                   "remplisseuse": ("Têtes de remplissage", "Filling heads"),
                   "pipette": ("Module de pipetage", "Pipetting module")}
        textes_s = {"reservoir_nom": self.tr("Réservoir", "Tank"),
                    "reservoir": f"{self.tr('Capacité', 'Capacity')} : {self.n(self.lr['reservoir_l'])} L",
                    "circuit": f"Circuit : {self.n(self.lr['circuit_ml'])} ml",
                    "organe": organes[self.marque["type"]][0 if fr else 1]}
        notes = []
        for cle, nom in [("volume_dose_ml", "dose"), ("volume_nominal_ml", "nominal"),
                         ("debit_ml_min", "debit"), ("pression_bar", "pression")]:
            if self.emp(cle) == "schema":
                textes_s[nom] = f"{self.lib(cle)} : {self.vu(cle)}"
                notes.append((cle, self.vu(cle)))
        larg = min(dessins.SCHEMA_L, cur.l)
        haut = dessins.SCHEMA_H * larg / dessins.SCHEMA_L
        bb = cur.image(dessins.schema(textes_s), larg, haut, x=cur.x + (cur.l - larg) / 2, espace=10)
        for cle, s in notes:
            ctx.noter("verite", cle, s, bb, mode="image")
        cur.para(escape(self.tr("Repères : 1 réservoir ; 2 circuit d'alimentation ; 3 organe de dosage ; "
                                "4 manomètre ; 5 sens d'écoulement ; 6 buse de sortie.",
                                "Key: 1 tank; 2 supply line; 3 dosing unit; 4 pressure gauge; "
                                "5 flow direction; 6 outlet nozzle.")), self.s["petit"])

    def caracteristiques(self, cur):
        t, notes = self.t_caracteristiques(min(cur.l, 380))
        cur.table(t, notes)

    def t_caracteristiques(self, largeur):
        """Tableau des caractéristiques : volume nominal et tolérance (si en tableau), leurres."""
        lr = self.lr
        lignes = [[self.tr("Caractéristique", "Rating"), self.tr("Valeur", "Value")]]
        notes = []
        cles = ["volume_nominal_ml"] + (["tolerance_ml"] if self.tolerance_caracteristiques else [])
        for cle in cles:
            if self.emp(cle) == "tableau":
                lignes.append([self.cel(self.lib(cle)), self.vu(cle)])
                txt = self.ecrit_tol if cle == "tolerance_ml" else self.ecrit[cle]
                notes.append((len(lignes) - 1, 1, "verite", cle, txt, None))
        g0, g1 = lr["gamme"]
        unite_l = "ml" if self.fr else "mL"
        for lib, val, cle, raison in [
                (self.tr("Gamme du modèle (constructeur)", "Model range (OEM)"),
                 f"{self.n(g0)} – {self.n(g1)} {unite_l}", "volume_nominal_ml", "gamme du constructeur"),
                (self.tr("Capacité du réservoir", "Tank capacity"), f"{self.n(lr['reservoir_l'])} L",
                 "volume_dose_ml", "capacité du réservoir"),
                (self.tr("Volume du circuit", "Line volume"), f"{self.n(lr['circuit_ml'])} {unite_l}",
                 "volume_dose_ml", "volume du circuit"),
                (self.tr("Incertitude élargie (k = 2)", "Expanded uncertainty (k = 2)"),
                 f"± {self.vol(lr['incertitude'])} {self.u['volume_dose_ml']}", "tolerance_ml",
                 "incertitude de mesure"),
                (self.tr("Débit maximal", "Max. flow"),
                 f"{self.cv('debit_ml_min', lr['debit_max'])} {self.u['debit_ml_min']}", "debit_ml_min",
                 "débit maximal du constructeur"),
                (self.tr("Pression maximale admissible", "Max. allowable pressure"),
                 f"{self.n(lr['pression_max'], 1)} bar", "pression_bar", "pression maximale"),
                (self.tr("Tarage de la soupape", "Relief valve setting"), f"{self.n(lr['tarage'], 1)} bar",
                 "pression_bar", "tarage de la soupape")]:
            lignes.append([self.cel(lib), val])
            notes.append((len(lignes) - 1, 1, "leurre", cle, val.rsplit(" ", 1)[0].lstrip("± "), raison))
        t = Table(lignes, colWidths=[0.6 * largeur, 0.4 * largeur])
        t.setStyle(self.style_table())
        return t, notes

    def synthese_provisoire(self):
        """Valeur provisoire du champ visé par « conflit_regle » : (cle, libellé, texte) ou None."""
        cle = self.pd.get("conflit_regle")
        if not cle:
            return None
        if cle == "volume_dose_ml":
            txt = self.vol(self.lr["essais_apres"][0][0])
        elif cle == "debit_ml_min":
            txt = self.cv(cle, self.lr["debit_avant"])
        else:
            txt = self.cv(cle, self.lr["pression_avant"])
        return cle, self.lib(cle), txt

    def regle_priorite(self, cur):
        if self.pd.get("conflit_regle"):
            cur.para(escape(self.tr("Les valeurs du tableau des mesures font foi ; la synthèse reprend des "
                                    "relevés provisoires.",
                                    "Measurement table values prevail; the summary shows provisional "
                                    "readings.")), self.s["petit"])

    def bloc_validation(self, c, ctx, x, y, largeur, avec_validation=True):
        """Signatures du technicien et du client, tampon d'approbation. Renvoie le bas du bloc.
        avec_validation=False : la date de validation est portée ailleurs (visas du style grille)."""
        v, lr = self.v, self.lr
        c.setFont(self.police, 8.5)
        moitie = largeur / 2
        if self.emp("technicien") == "formulaire":
            txt = f"{self.lib('technicien')} : {v['technicien']}"
            c.drawString(x, y - 10, txt)
            w = c.stringWidth(v["technicien"], self.police, 8.5)
            x1 = x + c.stringWidth(txt, self.police, 8.5)
            ctx.noter("verite", "technicien", v["technicien"], (x1 - w, y - 13, x1, y - 2))
        else:
            c.drawString(x, y - 10, self.tr("Le technicien :", "Technician:"))
        c.drawImage(ImageReader(dessins.signature(f"{self.graine}/{self.doc['id']}/s1")), x, y - 52,
                    min(110, moitie - 10), 34)
        texte_client = self.tr("Approbation client : ", "Customer approval: ") + lr["approbateur"]
        c.drawString(x + moitie, y - 10, texte_client)
        ctx.noter("leurre", "technicien", lr["approbateur"], (x + moitie, y - 13, x + largeur, y - 2),
                  raison="approbateur côté client")
        e = self.emp("date_validation") if avec_validation else None
        if e == "formulaire":
            dv = self.d(v["date_validation"])
            c.drawString(x + moitie, y - 22, f"{self.lib('date_validation')} : {dv}")
            w = c.stringWidth(dv, self.police, 8.5)
            x1 = x + moitie + c.stringWidth(f"{self.lib('date_validation')} : {dv}", self.police, 8.5)
            ctx.noter("verite", "date_validation", dv, (x1 - w, y - 25, x1, y - 14))
        elif e == "absent":
            c.drawString(x + moitie, y - 22, f"{self.lib('date_validation')} : ____________")
        if e == "tampon":
            dv = self.d(v["date_validation"], "jj/mm/aaaa" if self.fr else "abr_en")
            img = dessins.tampon([self.tr("APPROUVÉ", "APPROVED"), lr["client"][:24], dv], (0.15, 0.2, 0.6),
                                 f"{self.graine}/{self.doc['id']}/tampon")
            lt = min(140, moitie - 12)
            c.drawImage(ImageReader(img), x + moitie + 6, y - 12 - lt / 2, lt, lt / 2, mask="auto")
            ctx.noter("verite", "date_validation", dv, (x + moitie + 6, y - 12 - lt / 2, x + moitie + 6 + lt, y - 12),
                      mode="image")
            return y - 16 - lt / 2
        c.drawImage(ImageReader(dessins.signature(f"{self.graine}/{self.doc['id']}/s2")), x + moitie,
                    y - 64, min(110, moitie - 10), 34)
        return y - 68

    def statut_formulaire(self):
        """Statut écrit en clair (styles sans cases à cocher) : (libellé, texte)."""
        return self.lib("statut"), self.texte_valeur("statut")

    # Rendu -------------------------------------------------------------------------------------

    def pages(self):
        raise NotImplementedError

    def rendre(self):
        fonctions = self.pages()
        self.n_pages = len(fonctions)
        L, H = self.taille
        ctx = Contexte(H)
        page_scan = None
        if self.pd.get("scan"):
            page_scan = self.pd.get("page_scan", self.r.choice(self.pages_scannables))
        flux = io.BytesIO()
        c = canvas.Canvas(flux, pagesize=self.taille, invariant=1)
        c.setTitle(self.tr("Rapport d'intervention", "Service report"))
        for i, f in enumerate(fonctions):
            ctx.page = i
            if i == page_scan:
                ctx.scan = True
                jpeg, _ = dessins.scanner(lambda cc: f(cc, ctx), L, H, f"{self.graine}/{self.doc['id']}/scan")
                ctx.scan = False
                c.drawImage(ImageReader(io.BytesIO(jpeg)), 0, 0, L, H)
            else:
                f(c, ctx)
            c.showPage()
        c.save()
        return flux.getvalue(), ctx.placements, page_scan

    def curseur(self, c, ctx, haut=50, marge=36):
        L, H = self.taille
        return Curseur(c, ctx, marge, L - 2 * marge, H - haut)

    def sections(self, cur, sections, style_titre="inter"):
        for titre, html, notes in sections:
            cur.para(escape(titre), self.s[style_titre], espace=3)
            cur.para(html, self.s["corps"], notes, espace=8)
