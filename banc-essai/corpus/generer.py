"""Générateur du corpus : exécute le plan (plan.py) document par document.

Usage (depuis banc-essai/corpus/) :
    uv run python generer.py --exemples      un document par style (plan à graine séparée) dans exemples/
    uv run python generer.py                 les 60 documents : fourni/, test-cache/, relance/
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exemples", action="store_true")
    ap.add_argument("--styles", nargs="*", default=list(STYLES))
    ap.add_argument("--graine", type=int, default=GRAINE)
    a = ap.parse_args()
    if a.exemples:
        exemples(a.graine, a.styles)
        return
    raise SystemExit("Génération des 60 documents : après validation des exemples de chaque style.")


if __name__ == "__main__":
    main()
