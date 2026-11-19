"""Vérité terrain d'un document et PDF annoté.

Vérité : pour chaque champ, la valeur normalisée, ses écritures (page, cadre, texte ou image),
la règle qui fait foi, les pièges et les leurres (valeur, page, cadre, raison).
PDF annoté : copie du document avec cadres verts (valeur juste), orange (valeur imprimée
puis corrigée) et rouges numérotés (leurres), suivie d'une page de synthèse.
"""
import re

import pymupdf

from donnees import CLES, CLES_NUMERIQUES

REGLES = {
    "machine": "modèle de l'équipement contrôlé (pas le moteur, pas un équipement voisin)",
    "constructeur": "fabricant de l'équipement contrôlé (pas le prestataire, ni le fabricant du "
                    "moteur ou des instruments)",
    "numero_serie": "n° de série de l'équipement (pas celui du moteur, des instruments, ni le n° "
                    "d'inventaire)",
    "site": "site du client où l'équipement est installé (pas le siège, ni l'adresse du prestataire)",
    "reference_rapport": "référence du rapport en vigueur (pas la version annulée, ni la commande "
                         "ou l'affaire)",
    "date_intervention": "jour de l'intervention sur site, format ISO",
    "date_validation": "date de l'approbation finale du rapport (pas la rédaction, la "
                       "vérification, l'impression ni l'étalonnage des instruments), format ISO",
    "volume_dose_ml": "dose moyenne après réglage, toutes têtes et tous essais confondus, en ml",
    "volume_nominal_ml": "volume de consigne de l'équipement, en ml (pas la gamme du modèle)",
    "tolerance_ml": "tolérance admise sur la dose, en ml ; une tolérance en % se rapporte au "
                    "volume nominal (pas l'incertitude de mesure)",
    "debit_ml_min": "débit mesuré après réglage, en ml/min (pas le débit maximal, ni celui d'un "
                    "équipement voisin)",
    "pression_bar": "pression de service mesurée après réglage, en bar (pas la pression maximale, "
                    "le tarage de soupape ou le réseau d'air)",
    "reference_piece": "référence de la pièce effectivement remplacée (pas contrôlée, commandée ou "
                       "proposée au devis)",
    "technicien": "intervenant responsable côté prestataire (pas l'accompagnant, le rédacteur, le "
                  "vérificateur ou le client)",
    "statut": "décision finale : conforme, non_conforme ou a_revoir",
}
SYSTEMATIQUES = {"volume_dose_ml": ["volumes_voisins", "tableau_multi_entrees"],
                 "date_validation": ["dates_multiples"], "date_intervention": ["dates_multiples"],
                 "technicien": ["personnes_multiples"], "numero_serie": ["zones_ambigues"],
                 "constructeur": ["zones_ambigues"], "statut": ["cases_a_cocher"]}


def _norm(t):
    return re.sub(r"\s+", " ", t.replace(" ", " ")).strip()


def affiner(pdf, placements, page_scan):
    """Resserre le cadre des écritures en texte sur la chaîne trouvée dans la page.

    Renvoie la liste des écritures en texte introuvables (erreurs de contrôle).
    """
    doc = pymupdf.open(stream=pdf, filetype="pdf")
    manquants = []
    for p in placements:
        if p["mode"] != "texte" or p["page"] == page_scan:
            continue
        page = doc[p["page"]]
        clip = pymupdf.Rect(p["cadre"]) + (-2, -2, 2, 2)
        trouves = page.search_for(_norm(p["texte"]), clip=clip)
        if not trouves:
            manquants.append(p)
            continue
        r = trouves[0]
        p["cadre"] = [round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)]
    return manquants


def construire(doc, style, placements, page_scan, n_pages):
    champs = {}
    for cle in CLES:
        occ = [p for p in placements if p["cle"] == cle and p["role"] in ("verite", "calcul")]
        fausses = [p for p in placements if p["cle"] == cle and p["role"] in ("leurre", "erronee")]
        pieges = list(doc["pieges"][cle]) + SYSTEMATIQUES.get(cle, [])
        if cle in CLES_NUMERIQUES and any(re.search(r"\d[ .,']\d{3}(?!\d)", o["texte"]) or
                                          ("," in o["texte"]) for o in occ):
            pieges.append("format_nombre")
        absent = "champ_absent" in doc["pieges"][cle]
        if absent:
            emplacement = "absent"
        elif "logo_seul" in doc["pieges"][cle]:
            emplacement = "logo"
        elif any(o["role"] == "calcul" for o in occ):
            emplacement = "calcul"
        else:
            emplacement = doc["emplacements"][cle]
        champs[cle] = {
            "valeur": style.verite[cle],
            "emplacement": emplacement,
            "regle": REGLES[cle],
            "pieges": pieges,
            "scan": bool(occ) and page_scan is not None and all(o["page"] == page_scan for o in occ),
            "ecritures": [{k: o[k] for k in ("texte", "page", "mode", "cadre")} | {"role": o["role"]}
                          for o in occ],
            "leurres": [{k: o[k] for k in ("texte", "page", "mode", "cadre", "raison")} |
                        {"role": o["role"]} for o in fausses],
        }
    return {"id": doc["id"], "jeu": doc["jeu"], "style": "grille", "langue": doc["langue"],
            "prestataire": doc["prestataire"]["nom"], "pages": n_pages, "page_scannee": page_scan,
            "unites_ecrites": style.u, "format_nombres": style.style_nb, "format_dates": style.forme_date,
            "champs": champs}


def reponse(verite):
    return {cle: verite["champs"][cle]["valeur"] for cle in CLES}


COULEURS = {"verite": (0, 0.6, 0.1), "calcul": (0, 0.6, 0.1), "leurre": (0.85, 0.1, 0.1),
            "erronee": (0.95, 0.55, 0)}


def annoter(pdf, verite):
    doc = pymupdf.open(stream=pdf, filetype="pdf")
    leurres = []
    for cle, ch in verite["champs"].items():
        for e in ch["ecritures"]:
            page = doc[e["page"]]
            r = pymupdf.Rect(e["cadre"])
            page.draw_rect(r, color=COULEURS[e["role"]], width=1.4,
                           dashes="[3 2] 0" if e["role"] == "calcul" else None)
            page.insert_text((r.x0, r.y0 - 1.5), cle, fontsize=5.5, color=COULEURS[e["role"]])
        for l in ch["leurres"]:
            leurres.append((cle, l))
    for i, (cle, l) in enumerate(leurres, start=1):
        page = doc[l["page"]]
        r = pymupdf.Rect(l["cadre"])
        page.draw_rect(r, color=COULEURS[l["role"]], width=0.8)
        page.insert_text((r.x1 + 1, r.y0 + 5), str(i), fontsize=6, color=COULEURS[l["role"]])
    # Synthèse.
    L, H = doc[0].rect.width, doc[0].rect.height
    lignes = [f"Vérité terrain : {verite['id']} ({verite['prestataire']}, {verite['langue']})",
              f"Pages : {verite['pages']} ; page scannée : "
              f"{verite['page_scannee'] + 1 if verite['page_scannee'] is not None else 'aucune'} ; "
              f"nombres : {verite['format_nombres']} ; dates : {verite['format_dates']}", ""]
    for cle, ch in verite["champs"].items():
        pages = sorted({e["page"] + 1 for e in ch["ecritures"]})
        lignes.append(f"{cle} = {ch['valeur']!r}  [{ch['emplacement']}, p. {pages or '-'}]")
        if ch["pieges"]:
            lignes.append(f"    pièges : {', '.join(ch['pieges'])}")
    lignes.append("")
    lignes.append("Leurres (numéros reportés sur les pages) :")
    for i, (cle, l) in enumerate(leurres, start=1):
        lignes.append(f"  {i:>2}. {cle} : « {l['texte']} » p. {l['page'] + 1} — {l['raison']}")
    par_page = 72
    for k in range(0, len(lignes), par_page):
        page = doc.new_page(width=L, height=H)
        page.insert_text((36, 40), "\n".join(lignes[k:k + par_page]), fontsize=7.2, lineheight=1.35)
    return doc.tobytes(garbage=3, deflate=True, no_new_id=True)
