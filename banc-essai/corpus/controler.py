"""Contrôle automatique des documents générés.

Par document : chaque valeur écrite en texte se retrouve dans la couche texte de sa page ;
chaque valeur posée en image (logo, schéma, page scannée) en est absente ; constructeur
absent du texte quand il n'est que dans le logo ; page scannée sans texte ; 3 à 5 pages.

Usage (depuis banc-essai/corpus/) :
    uv run python controler.py exemples
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf


def normaliser(t):
    t = unicodedata.normalize("NFC", t).replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


def jetons(t):
    return set(re.split(r"[\s();:|]+", t))


def controler_document(pdf, placements, meta):
    erreurs, alertes = [], []
    doc = pymupdf.open(pdf)
    pages = [normaliser(p.get_text()) for p in doc]
    tout = " ".join(pages)
    if not 3 <= len(pages) <= 5:
        erreurs.append(f"{len(pages)} pages")
    if len(pages) != meta["pages"]:
        erreurs.append("nombre de pages différent des étiquettes")
    ps = meta["page_scannee"]
    if ps is not None:
        if pages[ps]:
            erreurs.append(f"page scannée {ps + 1} : couche texte non vide")
        if len(doc[ps].get_images()) != 1:
            erreurs.append(f"page scannée {ps + 1} : {len(doc[ps].get_images())} images")
    en_texte = {p["cle"] for p in placements if p["mode"] == "texte"}
    autres = {normaliser(p["texte"]).split(" ")[0] for p in placements if p["mode"] == "texte"}
    for p in placements:
        texte = normaliser(p["texte"])
        if p["mode"] == "texte":
            if texte not in pages[p["page"]]:
                erreurs.append(f"{p['cle']} : « {texte} » absent du texte de la page {p['page'] + 1}")
        elif not p["cle"].startswith("_") and p["cle"] not in en_texte:
            # Valeur seulement en image : elle ne doit pas se lire dans la couche texte,
            # sauf coïncidence avec une autre grandeur écrite (alerte).
            nombre = texte.split(" ")[0] if re.match(r"^[\d.,]", texte) else texte
            if nombre in jetons(tout):
                grave = len(nombre) > 2 and nombre not in autres
                (erreurs if grave else alertes).append(
                    f"{p['cle']} : « {nombre} » posé en image, se lit aussi dans le texte "
                    f"({'inattendu' if grave else 'coïncidence avec une autre grandeur ou nombre court'})")
    if meta["pieges_document"]["logo_seul"]:
        if meta_nom := next((p["texte"] for p in placements if p["cle"] == "constructeur"), None):
            if meta_nom.lower() in tout.lower():
                erreurs.append("logo seul : nom du constructeur présent dans le texte")
    images_garde = len(doc[0].get_images())
    attendu = 1 if ps == 0 else (2 if meta["pieges_document"]["deux_logos"] else 1)
    if images_garde != attendu:
        erreurs.append(f"page de garde : {images_garde} images, {attendu} attendue(s)")
    # Chaque valeur non nulle doit être écrite quelque part.
    for cle, e in meta["valeurs"].items():
        if "champ_absent" in e["piege"]:
            if any(p["cle"] == cle for p in placements):
                erreurs.append(f"{cle} : champ absent mais écrit")
        elif not any(p["cle"] == cle for p in placements):
            erreurs.append(f"{cle} : valeur attendue jamais écrite")
    return erreurs, alertes


def controler_dossier(dossier):
    dossier = Path(dossier)
    total = 0
    for pdf in sorted(dossier.glob("*.pdf")):
        ident = pdf.stem
        meta_f = dossier / f"{ident}.etiquettes.json"
        meta = json.loads(meta_f.read_text()) if meta_f.exists() else None
        placements = json.loads((dossier / "controle" / f"{ident}.json").read_text())
        erreurs, alertes = controler_document(pdf, placements, meta)
        total += len(erreurs)
        print(f"{ident} : {len(erreurs)} erreur(s), {len(alertes)} alerte(s)")
        for m in erreurs:
            print("  ERREUR", m)
        for m in alertes:
            print("  alerte", m)
    return total


if __name__ == "__main__":
    sys.exit(1 if controler_dossier(sys.argv[1]) else 0)
