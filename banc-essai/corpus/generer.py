"""Générateur du corpus (version 2).

Usage (depuis banc-essai/corpus/) :
    uv run python generer.py --exemples      documents d'exemple dans exemples/
"""
import argparse
import json
from pathlib import Path

import univers
import verite as vt
from donnees import tirer
from style_grille import StyleGrille

GRAINE = 20261119
ICI = Path(__file__).resolve().parent


def ecrire_json(chemin, objet):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(objet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def produire(doc, graine, sortie):
    style = StyleGrille(doc, graine)
    pdf, placements, page_scan = style.rendre()
    manquants = vt.affiner(pdf, placements, page_scan)
    v = vt.construire(doc, style, placements, page_scan, style.n_pages)
    (sortie / f"{doc['id']}.pdf").write_bytes(pdf)
    ecrire_json(sortie / "verite" / f"{doc['id']}.json", v)
    ecrire_json(sortie / "reponses" / f"{doc['id']}.json", vt.reponse(v))
    (sortie / "annotations").mkdir(exist_ok=True)
    (sortie / "annotations" / f"{doc['id']}.pdf").write_bytes(vt.annoter(pdf, v))
    return v, manquants


def _avec_type(marque, typ, familles=None):
    m = dict(marque)
    m["type"] = typ
    if familles:
        m["familles"] = familles
    return m


def exemples(sortie, graine):
    u = univers.construire(graine)
    f = u["fourni"]
    pfr = next(p for p in f["prestataires"] if p["langue"] == "fr")
    pen = next(p for p in f["prestataires"] if p["langue"] == "en")
    m1 = _avec_type(f["marques"][4], "remplisseuse")
    # Ambiguïté : la famille de machines du 2e document porte le nom du constructeur du 1er.
    m2 = _avec_type(f["marques"][5], "pompe", familles=[m1["nom"]])
    specs = [
        ("exemple-1", pfr, m1,
         {"volume_dose_ml": ["moyenne_a_calculer", "unite_a_convertir"],
          "tolerance_ml": ["tolerance_en_pourcent"], "volume_nominal_ml": ["synonyme_cle"],
          "debit_ml_min": ["unite_a_convertir"], "pression_bar": ["schema_seul"],
          "numero_serie": ["champ_absent"], "constructeur": ["logo_seul"],
          "date_validation": ["tampon_seul"], "reference_rapport": ["version_remplacee"],
          "site": ["synonyme_cle"], "date_intervention": ["recit_seul"]},
         {"logo_seul": True, "style_nombres": "fr", "place_unite": "entete", "forme_date": "jj/mm/aaaa"}),
        ("exemple-2", pen, m2,
         {"volume_dose_ml": ["valeur_barree", "unite_a_convertir"],
          "volume_nominal_ml": ["recit_seul"], "debit_ml_min": ["conflit_regle"],
          "pression_bar": ["unite_a_convertir"], "site": ["champ_absent"],
          "reference_piece": ["champ_absent"], "machine": ["synonyme_cle"],
          "constructeur": ["synonyme_cle"]},
         {"scan": True, "page_scan": 1, "style_nombres": "en", "place_unite": "cellule",
          "forme_date": "us", "redacteur_autre": True}),
    ]
    for ident, presta, marque, pieges, pieges_doc in specs:
        doc = tirer(ident, "exemple", presta, marque, f, f"{graine}-exemples", pieges, pieges_doc)
        if ident == "exemple-2":
            doc["unites"]["pression_bar"] = "psi"
        v, manquants = produire(doc, f"{graine}-exemples", sortie)
        print(ident, presta["nom"], "/", marque["nom"], f"{v['pages']} pages",
              f"scan p{v['page_scannee'] + 1}" if v["page_scannee"] is not None else "",
              f"- {len(manquants)} écriture(s) introuvable(s)")
        for m in manquants:
            print("   introuvable :", m["cle"], repr(m["texte"]), "page", m["page"] + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exemples", action="store_true")
    ap.add_argument("--graine", type=int, default=GRAINE)
    a = ap.parse_args()
    if a.exemples:
        d = ICI / "exemples"
        d.mkdir(parents=True, exist_ok=True)
        exemples(d, a.graine)
        return
    raise SystemExit("Génération du corpus : après validation des exemples.")


if __name__ == "__main__":
    main()
