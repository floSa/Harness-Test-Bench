"""Générateur du corpus de rapports d'intervention fictifs.

Usage (depuis banc-essai/corpus/) :
    uv run python generer.py --exemples      3 documents d'exemple dans exemples/
    uv run python generer.py                 les 50 documents (fourni/ et test-cache/)
    uv run python generer.py --sortie DIR    même corpus, écrit ailleurs (contrôle d'empreintes)
"""
import argparse
import hashlib
import json
import random
import re
from pathlib import Path

from entites import CLES, CLES_NUMERIQUES
from modele import allouer, reponse, tirer_document
from rendu import GABARITS

GRAINE = 20261119
ICI = Path(__file__).resolve().parent


def etiquettes(doc, placements, page_scan, coupe):
    sortie = {}
    for cle in CLES:
        tires = list(doc["pieges"][cle])
        systematiques = []
        if cle == "volume_dose_ml":
            systematiques.append("volumes_voisins")
        if cle in coupe:
            systematiques.append("tableau_coupe")
        pls = [p for p in placements if p["cle"] == cle]
        if cle in CLES_NUMERIQUES and any("," in p["texte"] or re.search(r"\d[  ]\d", p["texte"])
                                          for p in pls):
            systematiques.append("format_nombre")
        if "logo_seul" in tires:
            forme = "logo"
        elif "synonyme_cle" in tires:
            forme = "synonyme"
        else:
            forme = "exacte"
        if cle in CLES_NUMERIQUES:
            unite = "conversion" if "unite_a_convertir" in tires else "directe"
        else:
            unite = "sans_unite"
        scan = "oui" if pls and page_scan is not None and all(p["page"] == page_scan for p in pls) else "non"
        sortie[cle] = {"emplacement": doc["emplacements"][cle], "cle": forme, "unite": unite,
                       "piege": tires + systematiques, "scan": scan}
    return sortie


def rendre(doc, graine):
    g = GABARITS[doc["gabarit"]](doc, graine)
    pdf, placements, page_scan, angle = g.rendre()
    meta = {
        "id": doc["id"], "jeu": doc["jeu"], "gabarit": doc["gabarit"], "langue": doc["langue"],
        "pages": g.n_pages, "page_scannee": page_scan,
        "pieges_document": {k: v for k, v in doc["pieges_doc"].items()},
        "valeurs": etiquettes(doc, placements, page_scan, g.coupe),
    }
    return pdf, placements, meta


def ecrire_json(chemin, objet):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(objet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def exemples(sortie, graine):
    """Trois documents, un par gabarit fourni, avec les pièges de document imposés."""
    specs = [
        ("exemple-1", 1, 0, {"deux_logos": True, "scan": True, "logo_seul": False, "correction": False}),
        ("exemple-2", 2, 2, {"logo_seul": True, "correction": True, "deux_logos": False, "scan": False}),
        ("exemple-3", 3, 3, {"deux_logos": True, "scan": True, "logo_seul": False, "correction": False}),
    ]
    docs = [tirer_document(i, "exemple", g, c, f"{graine}-exemples") for i, g, c, _ in specs]
    allouer(docs, random.Random(f"{graine}-exemples/allocation"), {i: f for i, _, _, f in specs})
    for doc in docs:
        pdf, placements, meta = rendre(doc, f"{graine}-exemples")
        (sortie / f"{doc['id']}.pdf").write_bytes(pdf)
        ecrire_json(sortie / f"{doc['id']}.reponse.json", reponse(doc))
        ecrire_json(sortie / f"{doc['id']}.etiquettes.json", meta)
        ecrire_json(sortie / "controle" / f"{doc['id']}.json", placements)
        print(doc["id"], f"gabarit {doc['gabarit']}", f"{meta['pages']} pages",
              f"scan p{meta['page_scannee']}" if meta["page_scannee"] is not None else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exemples", action="store_true")
    ap.add_argument("--graine", type=int, default=GRAINE)
    ap.add_argument("--sortie", type=Path, default=ICI)
    a = ap.parse_args()
    if a.exemples:
        d = a.sortie / "exemples" if a.sortie == ICI else a.sortie
        d.mkdir(parents=True, exist_ok=True)
        exemples(d, a.graine)
        return
    raise SystemExit("Génération des 50 documents : après validation des exemples.")


if __name__ == "__main__":
    main()
