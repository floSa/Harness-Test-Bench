"""Générateur du corpus : exécute le plan (plan.py) document par document.

Usage (depuis banc-essai/corpus/) :
    uv run python generer.py --exemples      un document par style (plan à graine séparée) dans exemples/
    uv run python generer.py                 les 60 documents : fourni/, test-cache/, relance/
    uv run python generer.py --sortie DIR    les mêmes, ailleurs (contrôle de reproductibilité)
"""
import argparse
import json
from pathlib import Path

import verite as vt
from donnees import tirer
from plan import GRAINE, planifier
from style_classique import StyleClassique
from style_compact import StyleCompact
from style_grille import StyleGrille
from style_recit import StyleRecit
from style_reserve import StyleReserve

STYLES = {"grille": StyleGrille, "classique": StyleClassique, "compact": StyleCompact,
          "recit": StyleRecit, "reserve": StyleReserve}
ICI = Path(__file__).resolve().parent


def ecrire_json(chemin, objet):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(objet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def document(pdoc, univers, graine, ident=None):
    """Document complet (valeurs et présentation) à partir d'une entrée du plan."""
    part = univers[pdoc["jeu"]]
    doc = tirer(ident or pdoc["id"], pdoc["jeu"], pdoc["presta"], pdoc["marque"], part, graine,
                pdoc["pieges"], pdoc["pieges_doc"], pdoc["emplacements"], pdoc["style"])
    doc["presta_vu"], doc["marque_vue"] = pdoc["presta_vu"], pdoc["marque_vue"]
    return doc


def produire(doc, graine, sortie):
    style = STYLES[doc["style"]](doc, graine)
    pdf, placements, page_scan = style.rendre()
    manquants = vt.affiner(pdf, placements, page_scan)
    v = vt.construire(doc, style, placements, page_scan, style.n_pages)
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / f"{doc['id']}.pdf").write_bytes(pdf)
    ecrire_json(sortie / "verite" / f"{doc['id']}.json", v)
    ecrire_json(sortie / "reponses" / f"{doc['id']}.json", vt.reponse(v))
    (sortie / "annotations").mkdir(exist_ok=True)
    (sortie / "annotations" / f"{doc['id']}.pdf").write_bytes(vt.annoter(pdf, v))
    return v, manquants


def exemples(graine, styles):
    g = f"{graine}-exemples"
    plan, u = planifier(g)
    sortie = ICI / "exemples"
    for style in styles:
        pdoc = next(d for d in plan if d["style"] == style)
        doc = document(pdoc, u, g, ident=f"exemple-{style}")
        v, manquants = produire(doc, g, sortie)
        print(doc["id"], doc["prestataire"]["nom"], "/", doc["marque"]["nom"], f"{v['pages']} pages",
              f"scan p{v['page_scannee'] + 1}" if v["page_scannee"] is not None else "",
              f"- {len(manquants)} écriture(s) introuvable(s)")
        for m in manquants:
            print("   introuvable :", m["cle"], repr(m["texte"]), "page", m["page"] + 1)


DOSSIERS = {"fourni": "fourni", "test": "test-cache", "relance": "relance"}


def corpus(graine, racine):
    """Les 60 documents du plan, chacun dans le dossier de son jeu ; verite.csv par jeu."""
    plan, u = planifier(graine)
    bilan = {}
    for pdoc in plan:
        doc = document(pdoc, u, graine)
        sortie = racine / DOSSIERS[pdoc["jeu"]]
        v, manquants = produire(doc, graine, sortie)
        bilan[pdoc["id"]] = (pdoc["jeu"], pdoc["style"], v["pages"], len(manquants))
    for jeu, dossier in DOSSIERS.items():
        ecrire_csv(racine / dossier)
    return bilan


def ecrire_csv(dossier):
    import csv
    lignes = []
    for f in sorted((dossier / "verite").glob("*.json")):
        v = json.loads(f.read_text())
        for cle, ch in v["champs"].items():
            lignes.append({"id": v["id"], "jeu": v["jeu"], "style": v["style"], "langue": v["langue"],
                           "prestataire": v["prestataire"], "prestataire_vu": v["prestataire_vu"],
                           "marque_vue": v["marque_vue"], "champ": cle,
                           "valeur": "" if ch["valeur"] is None else ch["valeur"],
                           "nulle": ch["valeur"] is None, "emplacement": ch["emplacement"],
                           "pieges": " ".join(ch["pieges"]), "scan": ch["scan"],
                           "leurres": len(ch["leurres"])})
    with open(dossier / "verite.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exemples", action="store_true")
    ap.add_argument("--styles", nargs="*", default=list(STYLES))
    ap.add_argument("--graine", type=int, default=GRAINE)
    ap.add_argument("--sortie", help="racine de sortie (contrôle des empreintes)")
    a = ap.parse_args()
    if a.exemples:
        exemples(a.graine, a.styles)
        return
    racine = Path(a.sortie) if a.sortie else ICI
    bilan = corpus(a.graine, racine)
    from collections import Counter
    print(len(bilan), "documents ;", dict(Counter(j for j, *_ in bilan.values())),
          "; écritures introuvables :", sum(m for *_, m in bilan.values()))


if __name__ == "__main__":
    main()
