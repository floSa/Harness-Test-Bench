"""Contrôle automatique du corpus généré (relit les PDF et la vérité, pas le générateur).

Usage (depuis banc-essai/corpus/) :
    uv run python controler.py            contrôle fourni/, test-cache/, relance/
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf

from donnees import CLES
from plan import DOCUMENT, EMPLACEMENTS, GRAINE, planifier, quotas

ICI = Path(__file__).resolve().parent
DOSSIERS = {"fourni": "fourni", "test": "test-cache", "relance": "relance"}
IMAGES = {"schema", "logo", "plaque", "tampon"}


def norm(t):
    return re.sub(r"\s+", " ", t.replace(" ", " ")).strip()


def controler_document(pdf, v, rep, pdoc):
    err, alertes = [], []
    doc = pymupdf.open(pdf)
    textes = [norm(p.get_text()) for p in doc]
    tout = " ".join(textes)
    if not 3 <= len(doc) <= 6:
        err.append(f"{len(doc)} pages")
    if v["pages"] != len(doc):
        err.append("nombre de pages différent de la vérité")
    if sorted(rep) != sorted(CLES):
        err.append("réponse : clés incorrectes")
    ps = v["page_scannee"]
    if ps is not None and textes[ps]:
        err.append(f"page scannée {ps + 1} : couche texte non vide")
    for cle, ch in v["champs"].items():
        if rep[cle] != ch["valeur"]:
            err.append(f"{cle} : réponse différente de la vérité")
        if ch["emplacement"] != pdoc["emplacements"][cle]:
            err.append(f"{cle} : emplacement {ch['emplacement']} au lieu de {pdoc['emplacements'][cle]} (plan)")
        ecr = [e for e in ch["ecritures"] if e["role"] == "verite"]
        if ch["valeur"] is None:
            if ecr:
                err.append(f"{cle} : valeur absente mais écrite")
            continue
        if not ch["ecritures"]:
            err.append(f"{cle} : valeur jamais écrite")
        for e in ch["ecritures"]:
            if e["mode"] == "texte" and e["page"] != ps:
                clip = pymupdf.Rect(e["cadre"]) + (-3, -3, 3, 3)
                if not doc[e["page"]].search_for(norm(e["texte"]), clip=clip):
                    err.append(f"{cle} : « {e['texte']} » introuvable p. {e['page'] + 1}")
        if ch["emplacement"] in IMAGES:
            if any(e["mode"] == "texte" for e in ecr):
                err.append(f"{cle} : prévu en image mais écrit en texte")
            for e in ecr:
                s = norm(e["texte"])
                if len(s) > 3 and s in tout:
                    alertes.append(f"{cle} : « {s} » prévu en image se lit aussi dans le texte")
    return err, alertes


def main():
    plan, _ = planifier(GRAINE)
    par_id = {p["id"]: p for p in plan}
    total_err, comptes = 0, {j: Counter() for j in DOSSIERS}
    for jeu, dossier in DOSSIERS.items():
        d = ICI / dossier
        pdfs = sorted(d.glob("doc-*.pdf"))
        attendus = [p for p in plan if p["jeu"] == jeu]
        if len(pdfs) != len(attendus):
            print(f"{jeu} : {len(pdfs)} PDF pour {len(attendus)} prévus")
            total_err += 1
        for pdf in pdfs:
            v = json.loads((d / "verite" / f"{pdf.stem}.json").read_text())
            rep = json.loads((d / "reponses" / f"{pdf.stem}.json").read_text())
            err, alertes = controler_document(pdf, v, rep, par_id[pdf.stem])
            total_err += len(err)
            for m in err:
                print(f"  ERREUR {pdf.stem} {m}")
            for m in alertes:
                print(f"  alerte {pdf.stem} {m}")
            for cle, ch in v["champs"].items():
                comptes[jeu][(cle, ch["emplacement"])] += 1
            for nom in DOCUMENT:
                if nom in v["pieges_document"]:
                    comptes[jeu][nom] += 1
        # Parts visées du plan retrouvées dans les fichiers générés.
        n = len(attendus)
        for cle, parts in EMPLACEMENTS.items():
            for e, k in quotas(parts, n).items():
                if comptes[jeu][(cle, e)] != k:
                    print(f"  ERREUR {jeu} {cle}/{e} : {comptes[jeu][(cle, e)]} au lieu de {k}")
                    total_err += 1
        for nom, part in DOCUMENT.items():
            k = quotas({nom: part}, n)[nom]
            if comptes[jeu][nom] != k:
                print(f"  ERREUR {jeu} {nom} : {comptes[jeu][nom]} au lieu de {k}")
                total_err += 1
        print(f"{jeu} : {len(pdfs)} documents contrôlés")
    print(f"Total : {total_err} erreur(s)")
    return total_err


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
