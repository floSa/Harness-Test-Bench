"""Tâche « dossiers » : un dossier par équipement, plusieurs pièces à recouper.

Usage (depuis banc-essai/corpus/) :
    uv run python dossiers.py                 dossiers/fourni, dossiers/test-cache, dossiers/relance
    uv run python dossiers.py --sortie DIR    les mêmes, ailleurs (contrôle de reproductibilité)

Un dossier rassemble, dans le désordre et sous des noms opaques (piece-NN.pdf), les pièces
reçues pour un équipement : ses rapports d'intervention (générateur du corpus, mêmes pièges),
et des pièces qui obligent à recouper :
- rapport d'un équipement jumeau (même site, même modèle, autre n° de série) : à écarter ;
- ancienne version d'un rapport, remplacée par un rapport du dossier (« annule et remplace ») ;
- rapport annulé par un avis d'annulation ;
- rectificatif qui corrige une valeur d'un rapport.
La réponse attendue : l'équipement, ses interventions valides dans l'ordre des dates (valeurs
après rectificatif), et le statut actuel (celui de la dernière intervention valide).
"""
import argparse
import copy
import datetime as dt
import io
import json
import random
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

import dessins
import formats
import univers
import verite as vt
from donnees import CLIENTS, TYPES
from flux import remplacer_par_scan
from generer import STYLES
from plan import planifier

GRAINE = "20261123-dossiers"
ICI = Path(__file__).resolve().parent
EQUIPEMENT = ["machine", "constructeur", "numero_serie", "site"]
INTERVENTION = ["reference_rapport", "date_intervention", "date_validation", "volume_dose_ml",
                "volume_nominal_ml", "tolerance_ml", "debit_ml_min", "pression_bar",
                "reference_piece", "technicien", "statut"]
# Jeu : nombre de dossiers et graines du plan dont on prend les rapports (jeu du plan).
JEUX = {"fourni": (6, ["a", "b"], "fourni"), "test": (12, ["c", "d", "e", "f", "g", "h"], "test"),
        "relance": (8, ["i", "j", "k", "l", "m", "n"], "relance")}
DOSSIERS = {"fourni": "fourni", "test": "test-cache", "relance": "relance"}
CHAMPS_RECTIFIABLES = ["debit_ml_min", "pression_bar", "volume_dose_ml", "statut", "technicien"]
UNITE = {"debit_ml_min": "ml/min", "pression_bar": "bar", "volume_dose_ml": "ml"}
LIBELLE = {
    "fr": {"debit_ml_min": "débit mesuré après réglage", "pression_bar": "pression de service après réglage",
           "volume_dose_ml": "volume de dose moyen après réglage", "statut": "décision finale",
           "technicien": "technicien responsable de l'intervention"},
    "en": {"debit_ml_min": "measured flow rate after adjustment",
           "pression_bar": "operating pressure after adjustment",
           "volume_dose_ml": "mean dose volume after adjustment", "statut": "final decision",
           "technicien": "technician in charge of the intervention"},
}
STATUTS = {"fr": {"conforme": "conforme", "non_conforme": "non conforme", "a_revoir": "à revoir"},
           "en": {"conforme": "compliant", "non_conforme": "non-compliant", "a_revoir": "to be reviewed"}}


# Réserve de rapports ------------------------------------------------------------------------

def reserve(jeu):
    """Entrées de plan (emplacements et pièges déjà équilibrés) tirées de plusieurs graines."""
    _, graines, jeu_plan = JEUX[jeu]
    out = []
    for g in graines:
        plan, u = planifier(f"{GRAINE}/{g}")
        out += [(p, u, f"{GRAINE}/{g}") for p in plan if p["jeu"] == jeu_plan]
    return out


def prendre(pool, r, langue, presta=None):
    """Retire de la réserve une entrée de la langue voulue (et du prestataire voulu)."""
    choix = [k for k, (p, _, _) in enumerate(pool)
             if p["langue"] == langue and (presta is None or p["presta"]["nom"] == presta["nom"])]
    if not choix:
        choix = [k for k, (p, _, _) in enumerate(pool) if p["langue"] == langue]
    return pool.pop(r.choice(choix))


def entree_pour(pdoc, marque, presta=None, sans_remplacement=False):
    """Copie d'une entrée de plan, recalée sur la marque du dossier (et un prestataire imposé)."""
    p = copy.deepcopy(pdoc)
    p["marque"] = marque
    if presta is not None:
        p["presta"], p["style"] = presta, presta["style_page"]
    # Le n° de série relie les pièces : jamais absent d'un rapport de dossier.
    if p["emplacements"].get("numero_serie") == "absent":
        p["emplacements"]["numero_serie"] = "formulaire"
    if sans_remplacement:
        p["pieges"]["reference_rapport"] = [x for x in p["pieges"]["reference_rapport"]
                                            if x != "version_remplacee"]
        p["pieges_doc"].pop("version_remplacee", None)
    return p


def rapport(pdoc, u, graine, ident, impose):
    """Rendu d'un rapport : (pdf, vérité, document)."""
    from donnees import tirer
    part = u[pdoc["jeu"]]
    doc = tirer(ident, pdoc["jeu"], pdoc["presta"], pdoc["marque"], part, graine, pdoc["pieges"],
                pdoc["pieges_doc"], pdoc["emplacements"], pdoc["style"], impose=impose)
    doc["presta_vu"], doc["marque_vue"] = False, False
    style = STYLES[doc["style"]](doc, graine)
    pdf, placements, page_scan = style.rendre()
    manquants = vt.affiner(pdf, placements, page_scan)
    v = vt.construire(doc, style, placements, page_scan, style.n_pages)
    v["introuvables"] = len(manquants)
    return pdf, v, doc


def remplace(v):
    """Vrai si le rapport cite une référence qu'il annule et remplace."""
    return "version_remplacee" in v["pieges_document"] or \
        "version_remplacee" in v["champs"]["reference_rapport"]["pieges"]


# Courriers ----------------------------------------------------------------------------------

def courrier(presta, langue, date_iso, objet, corps, signataire, graine, scan):
    """Courrier d'une page du prestataire ; tramé (image seule) si scan."""
    flux = io.BytesIO()
    c = canvas.Canvas(flux, pagesize=(595, 842), invariant=1)
    c.drawImage(ImageReader(dessins.logo(presta)), 50, 760, width=150, height=49)
    c.setFont("Helvetica", 9)
    c.drawString(50, 745, f"{presta['nom']} - {presta['ville']}")
    r = random.Random(graine)
    forme = r.choice(formats.FORMES_DATE[langue])
    c.setFont("Helvetica", 10)
    lieu = presta["ville"]
    c.drawRightString(545, 700, f"{lieu}, {'le ' if langue == 'fr' else ''}{formats.date(date_iso, forme)}")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 650, ("Objet : " if langue == "fr" else "Subject: ") + objet)
    c.setFont("Helvetica", 10.5)
    y = 615
    for para in corps:
        ligne = ""
        for mot in para.split():
            essai = (ligne + " " + mot).strip()
            if c.stringWidth(essai, "Helvetica", 10.5) > 490:
                c.drawString(50, y, ligne)
                y -= 15
                ligne = mot
            else:
                ligne = essai
        c.drawString(50, y, ligne)
        y -= 26
    c.drawString(330, y - 10, signataire)
    c.drawImage(ImageReader(dessins.signature(f"{graine}/sig")), 330, y - 70, width=110, height=50,
                mask="auto")
    c.showPage()
    c.save()
    pdf = flux.getvalue()
    if scan:
        pdf = remplacer_par_scan(pdf, 0, f"{graine}/scan")
    return pdf


def nouvelle_valeur(cle, valeur, r, langue, exclus):
    if cle == "statut":
        return r.choice([s for s in ("conforme", "non_conforme", "a_revoir") if s != valeur])
    if cle == "technicien":
        return univers.personne(r, langue, exclus)
    pas = 0.1 if cle == "pression_bar" else (1 if valeur >= 100 else (0.1 if valeur >= 1 else 0.01))
    for _ in range(50):
        x = round(round(valeur * (1 + r.choice([-1, 1]) * r.uniform(0.06, 0.22)) / pas) * pas, 4)
        if abs(x - valeur) >= 0.05 and x > 0:
            return x
    return round(valeur + 10 * pas, 4)


def ecrire_valeur(cle, x, langue):
    if cle == "statut":
        return STATUTS[langue][x]
    if cle == "technicien":
        return x
    style = "fr" if langue == "fr" else "en"
    return f"{formats.nombre(x, style)} {UNITE[cle]}"


def texte_rectificatif(langue, ref, date_int, serie, cle, ancienne, nouvelle):
    lib = LIBELLE[langue][cle]
    if langue == "fr":
        return (f"Rectificatif au rapport {ref}",
                [f"Le rapport {ref}, relatif à l'intervention du {date_int} sur l'équipement n° de série "
                 f"{serie}, comporte une erreur de saisie.",
                 f"Valeur à retenir pour le {lib} : {nouvelle} (au lieu de {ancienne}).",
                 "Les autres indications du rapport restent valables. Merci de mettre à jour vos dossiers."])
    return (f"Correction to report {ref}",
            [f"Report {ref}, covering the intervention of {date_int} on the equipment with serial number "
             f"{serie}, contains a data entry error.",
             f"Value to be used for the {lib}: {nouvelle} (instead of {ancienne}).",
             "All other information in the report remains valid. Please update your records."])


def texte_annulation(langue, ref, date_int, serie, r):
    if langue == "fr":
        motif = r.choice(["intervention saisie deux fois par erreur",
                          "intervention réalisée dans le cadre d'un essai, sans valeur contractuelle",
                          "rapport établi avant la fin de l'intervention, sans contrôle final"])
        return (f"Avis d'annulation du rapport {ref}",
                [f"Le rapport {ref} (intervention du {date_int}, équipement n° de série {serie}) est annulé : "
                 f"{motif}.", "Il ne doit pas être pris en compte dans l'historique de l'équipement."])
    motif = r.choice(["intervention entered twice by mistake",
                      "trial intervention with no contractual value",
                      "report issued before the end of the intervention, without final check"])
    return (f"Cancellation notice for report {ref}",
            [f"Report {ref} (intervention of {date_int}, equipment serial number {serie}) is cancelled: "
             f"{motif}.", "It must not be taken into account in the equipment history."])


# Un dossier ---------------------------------------------------------------------------------

def jumeau(serie, r):
    """N° de série voisin : mêmes premiers caractères, deux derniers chiffres changés."""
    chiffres = [k for k, ch in enumerate(serie) if ch.isdigit()]
    s = list(serie)
    for k in chiffres[-2:]:
        s[k] = r.choice([d for d in "0123456789" if d != serie[k]])
    return "".join(s)


def dossier(ident, pool, r, graine_jeu, options):
    """options : ensemble parmi {"jumeau", "annule", "rectificatif"} (quotas du jeu)."""
    p0, u0, g0 = prendre(pool, r, r.choice(["fr", "en"]))
    langue, marque = p0["langue"], p0["marque"]
    typ = TYPES[marque["type"]]
    # Identité de l'équipement, commune à tous les rapports du dossier.
    machine = f"{r.choice(marque['familles'])} {r.choice([40, 85, 120, 160, 250, 300, 600])}"
    pref = marque["prefixe_serie"]
    serie = r.choice([f"{pref}-{r.randint(2016, 2024)}-{r.randint(10000, 99999)}",
                      f"{pref}{r.randint(100000, 999999)}", f"{pref}/{r.randint(16, 24)}/{r.randint(1000, 9999)}"])
    site, _ = univers.site(r, langue)
    client = r.choice(CLIENTS[langue]).format(m=r.choice(univers.DEBUTS) + r.choice(univers.FINS))
    nominal = float(r.choice(typ["nominal"]))
    base = {"machine": machine, "serie": serie, "site": site, "client": client, "nominal": nominal,
            "pct": r.choice([0.5, 1, 1.5, 2, 2.5, 3])}
    debit0 = r.uniform(*typ["debit"][:2])
    pression0 = r.uniform(*typ["pression"])

    def mesures(r):
        """Débit et pression d'une visite : proches de ceux de l'équipement, jamais identiques."""
        return {"debit": debit0 * r.uniform(0.85, 1.15), "pression": pression0 * r.uniform(0.85, 1.15)}

    n_valides = r.choice([2, 3, 3, 4])
    debut = dt.date(2024, 3, 1) + dt.timedelta(days=r.randint(0, 300))
    dates = [debut]
    for _ in range(n_valides - 1):
        dates.append(dates[-1] + dt.timedelta(days=r.randint(45, 200)))
    pieces = []      # (pdf, description)
    valides = []     # (vérité du rapport, document)
    for k, d in enumerate(dates):
        pd, u, g = (p0, u0, g0) if k == 0 else prendre(pool, r, langue)
        pdoc = entree_pour(pd, marque)
        pdf, v, doc = rapport(pdoc, u, g, f"{ident}-r{k + 1}", base | mesures(r) | {"intervention": d})
        pieces.append((pdf, {"nature": "rapport", "retenu": True, "reference": v["champs"]["reference_rapport"]["valeur"],
                             "verite_rapport": v}))
        valides.append((v, doc))

    # Ancienne version d'un rapport qui en annule et remplace un autre.
    for v, doc in valides:
        if remplace(v) and r.random() < 0.7:
            pd, u, g = prendre(pool, r, langue, doc["prestataire"])
            pdoc = entree_pour(pd, marque, presta=doc["prestataire"], sans_remplacement=True)
            imp = base | mesures(r) | {"intervention": dt.date.fromisoformat(v["champs"]["date_intervention"]["valeur"]
                                                                or doc["valeurs"]["date_intervention"]),
                          "ref": doc["leurres"]["ref_ancienne"]}
            pdf, va, _ = rapport(pdoc, u, g, f"{ident}-ancien", imp)
            pieces.append((pdf, {"nature": "version_remplacee", "retenu": False,
                                 "reference": doc["leurres"]["ref_ancienne"],
                                 "remplacee_par": v["champs"]["reference_rapport"]["valeur"],
                                 "verite_rapport": va}))
            break

    # Rapport d'un équipement jumeau (même site, même modèle, autre n° de série).
    if "jumeau" in options:
        pd, u, g = prendre(pool, r, langue)
        d = r.choice(dates) if r.random() < 0.5 else dates[0] + dt.timedelta(days=r.randint(10, 400))
        pdf, vj, _ = rapport(entree_pour(pd, marque), u, g, f"{ident}-jumeau",
                             base | mesures(r) | {"intervention": d, "serie": jumeau(serie, r)})
        pieces.append((pdf, {"nature": "equipement_jumeau", "retenu": False,
                             "reference": vj["champs"]["reference_rapport"]["valeur"],
                             "numero_serie": vj["champs"]["numero_serie"]["valeur"], "verite_rapport": vj}))

    # Rapport annulé par un avis d'annulation.
    if "annule" in options:
        pd, u, g = prendre(pool, r, langue)
        d = dates[0] + dt.timedelta(days=r.randint(5, max(6, (dates[-1] - dates[0]).days + 60)))
        pdf, van, docan = rapport(entree_pour(pd, marque), u, g, f"{ident}-annule", base | mesures(r) | {"intervention": d})
        ref = van["champs"]["reference_rapport"]["valeur"]
        pieces.append((pdf, {"nature": "rapport_annule", "retenu": False, "reference": ref, "verite_rapport": van}))
        quand = d + dt.timedelta(days=r.randint(8, 40))
        objet, corps = texte_annulation(langue, ref, formats.date(d, "jj/mm/aaaa"), serie, r)
        pdf = courrier(docan["prestataire"], langue, quand.isoformat(), objet, corps,
                       univers.personne(r, langue), f"{graine_jeu}/{ident}/annulation", r.random() < 0.4)
        pieces.append((pdf, {"nature": "avis_annulation", "retenu": False, "annule": ref}))

    # Réponse attendue (avant rectificatif).
    interventions = []
    for v, doc in valides:
        interventions.append({c: v["champs"][c]["valeur"] for c in INTERVENTION})

    # Rectificatif d'une valeur d'un rapport valide.
    rectificatif = None
    if "rectificatif" in options:
        k = r.randrange(len(valides))
        v, doc = valides[k]
        cles = [c for c in CHAMPS_RECTIFIABLES if interventions[k][c] is not None]
        cle = r.choice(cles)
        ancienne = interventions[k][cle]
        exclus = [doc["valeurs"]["technicien"], doc["leurres"]["accompagnant"], doc["leurres"]["verificateur"],
                  doc["leurres"]["approbateur"], doc["leurres"]["demandeur"]]
        nouvelle = nouvelle_valeur(cle, ancienne, r, langue, exclus)
        ref = interventions[k]["reference_rapport"]
        d = dt.date.fromisoformat(interventions[k]["date_intervention"] or doc["valeurs"]["date_intervention"])
        objet, corps = texte_rectificatif(langue, ref, formats.date(d, "jj/mm/aaaa"), serie, cle,
                                          ecrire_valeur(cle, ancienne, langue), ecrire_valeur(cle, nouvelle, langue))
        quand = dt.date.fromisoformat(doc["valeurs"]["date_validation"]) + dt.timedelta(days=r.randint(5, 30))
        pdf = courrier(doc["prestataire"], langue, quand.isoformat(), objet, corps,
                       univers.personne(r, langue, exclus), f"{graine_jeu}/{ident}/rectificatif", r.random() < 0.4)
        pieces.append((pdf, {"nature": "rectificatif", "retenu": False, "rapport": ref, "champ": cle,
                             "ancienne": ancienne, "nouvelle": nouvelle}))
        interventions[k][cle] = nouvelle
        rectificatif = {"reference": ref, "champ": cle}

    # Ordre des dates (les dates d'intervention valides sont distinctes et toujours lisibles :
    # l'ordre suit les dates imposées).
    ordre = sorted(range(len(interventions)), key=lambda k: dates[k])
    interventions = [interventions[k] for k in ordre]
    sites = [v["champs"]["site"]["valeur"] for v, _ in valides]
    reponse = {
        "machine": machine, "constructeur": marque["nom"], "numero_serie": serie,
        "site": site if any(s is not None for s in sites) else None,
        "interventions": interventions,
        "statut_actuel": interventions[-1]["statut"],
    }
    # Pièces dans le désordre, sous des noms opaques.
    r.shuffle(pieces)
    composition = []
    for n, (pdf, desc) in enumerate(pieces, start=1):
        desc = dict(desc)
        vr = desc.pop("verite_rapport", None)
        if vr is not None:
            desc["style"], desc["prestataire"], desc["pages"] = vr["style"], vr["prestataire"], vr["pages"]
            desc["introuvables"] = vr["introuvables"]
        composition.append({"piece": f"piece-{n:02d}.pdf", **desc})
    verite = {"id": ident, "langue": langue, "type": marque["type"], "rectificatif": rectificatif,
              "pieces": composition, "reponse": reponse}
    rapports = {f"piece-{n:02d}": desc.get("verite_rapport") for n, (_, desc) in enumerate(pieces, start=1)
                if desc.get("verite_rapport") is not None}
    return [pdf for pdf, _ in pieces], verite, reponse, rapports


# Corpus -------------------------------------------------------------------------------------

def ecrire_json(chemin, objet):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(objet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def corpus(racine):
    r = random.Random(f"{GRAINE}/dossiers")
    total = sum(n for n, _, _ in JEUX.values())
    numeros = list(range(1, total + 1))
    r.shuffle(numeros)
    bilan = []
    for jeu, (n, _, _) in JEUX.items():
        pool = reserve(jeu)
        sortie = racine / DOSSIERS[jeu]
        # Quotas exacts par jeu : rectificatif 50 %, jumeau 45 %, rapport annulé 40 %.
        tirages = {nom: set(r.sample(range(n), round(part * n)))
                   for nom, part in (("rectificatif", 0.5), ("jumeau", 0.45), ("annule", 0.4))}
        for k in range(n):
            ident = f"dos-{numeros.pop():03d}"
            options = {nom for nom, ks in tirages.items() if k in ks}
            pdfs, verite, reponse, rapports = dossier(ident, pool, r, f"{GRAINE}/{jeu}", options)
            for k, pdf in enumerate(pdfs, start=1):
                (sortie / ident).mkdir(parents=True, exist_ok=True)
                (sortie / ident / f"piece-{k:02d}.pdf").write_bytes(pdf)
            ecrire_json(sortie / "reponses" / f"{ident}.json", reponse)
            ecrire_json(sortie / "verite" / f"{ident}.json", verite)
            for piece, vr in rapports.items():
                ecrire_json(sortie / "verite" / ident / f"{piece}.json", vr)
            bilan.append((jeu, ident, verite))
    return bilan


def resume(bilan):
    from collections import Counter
    lignes = []
    for jeu in JEUX:
        vs = [v for j, _, v in bilan if j == jeu]
        nat = Counter(p["nature"] for v in vs for p in v["pieces"])
        pages = sum(p.get("pages", 1) for v in vs for p in v["pieces"])
        intro = sum(p.get("introuvables", 0) for v in vs for p in v["pieces"])
        lignes.append(f"{jeu} : {len(vs)} dossiers, {sum(nat.values())} pièces, {pages} pages, "
                      f"{sum(len(v['reponse']['interventions']) for v in vs)} interventions valides ; "
                      f"{dict(nat)} ; écritures introuvables : {intro}")
    return "\n".join(lignes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sortie", help="racine de sortie (contrôle des empreintes)")
    a = ap.parse_args()
    racine = Path(a.sortie) if a.sortie else ICI / "dossiers"
    print(resume(corpus(racine)))


if __name__ == "__main__":
    main()
