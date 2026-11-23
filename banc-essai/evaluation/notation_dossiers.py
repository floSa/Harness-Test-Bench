"""Notation de la tâche « dossiers » (corpus : banc-essai/corpus/dossiers.py).

Réponse attendue par dossier :
    {"machine", "constructeur", "numero_serie", "site",
     "interventions": [{11 clés d'intervention}, ...] dans l'ordre des dates,
     "statut_actuel"}

Les interventions sont appariées par référence de rapport (texte normalisé). Score : F1 par champ.
Un champ juste compte pour un vrai positif ; chaque intervention répondue compte 11 champs
répondus, chaque intervention attendue 11 champs attendus, plus 5 champs d'équipement et de
statut actuel de part et d'autre. Une intervention qui ne devait pas être retenue (équipement
jumeau, rapport annulé, version remplacée) ajoute 11 champs répondus faux ; une intervention
oubliée, 11 champs attendus manqués. Règles de comparaison des valeurs : notation.py.
"""
import json
from collections import defaultdict
from pathlib import Path

import notation

EQUIPEMENT = ["machine", "constructeur", "numero_serie", "site"]
INTERVENTION = ["reference_rapport", "date_intervention", "date_validation", "volume_dose_ml",
                "volume_nominal_ml", "tolerance_ml", "debit_ml_min", "pression_bar",
                "reference_piece", "technicien", "statut"]
CLES_DOSSIER = EQUIPEMENT + ["interventions", "statut_actuel"]
MAX_INTERVENTIONS = 30
N_DOSSIER = len(EQUIPEMENT) + 1
N_INTER = len(INTERVENTION)


# Format ------------------------------------------------------------------------------------------

def valider(reponses, ids):
    """Erreurs de format d'une soumission : un objet par dossier attendu."""
    if not isinstance(reponses, dict):
        return ["les réponses doivent être un objet {dossier: {...}}"]
    err = []
    manquants, inconnus = sorted(set(ids) - set(reponses)), sorted(set(reponses) - set(ids))
    if manquants:
        err.append(f"dossiers manquants : {', '.join(manquants)}")
    if inconnus:
        err.append(f"dossiers inconnus : {', '.join(inconnus)}")
    for i in sorted(set(ids) & set(reponses)):
        err += [f"{i} : {e}" for e in erreurs_dossier(reponses[i])]
    return err


def erreurs_dossier(r):
    if not isinstance(r, dict):
        return ["objet JSON attendu"]
    err = []
    if set(r) != set(CLES_DOSSIER):
        err.append(f"clés manquantes {sorted(set(CLES_DOSSIER) - set(r))}, "
                   f"clés en trop {sorted(set(r) - set(CLES_DOSSIER))}")
    for cle in EQUIPEMENT:
        err += notation.erreurs_valeur(cle, r.get(cle))
    err += [e.replace("statut", "statut_actuel", 1) for e in notation.erreurs_valeur("statut", r.get("statut_actuel"))]
    inter = r.get("interventions")
    if not isinstance(inter, list):
        return err + ["interventions : liste attendue"]
    if len(inter) > MAX_INTERVENTIONS:
        return err + [f"interventions : au plus {MAX_INTERVENTIONS}"]
    for k, it in enumerate(inter, start=1):
        if not isinstance(it, dict):
            err.append(f"intervention {k} : objet attendu")
            continue
        if set(it) != set(INTERVENTION):
            err.append(f"intervention {k} : clés manquantes {sorted(set(INTERVENTION) - set(it))}, "
                       f"clés en trop {sorted(set(it) - set(INTERVENTION))}")
        for cle in INTERVENTION:
            err += [f"intervention {k} : {e}" for e in notation.erreurs_valeur(cle, it.get(cle))]
    return err


# Vérité --------------------------------------------------------------------------------------------

def charger_jeu(dossier):
    """Identifiants (triés), réponses attendues, vérités et pièces de chaque dossier."""
    d = Path(dossier)
    ids = sorted(p.name for p in d.glob("dos-*") if p.is_dir())
    attendus = {i: json.loads((d / "reponses" / f"{i}.json").read_text()) for i in ids}
    verites = {i: json.loads((d / "verite" / f"{i}.json").read_text()) for i in ids}
    return ids, attendus, verites


def _ref(x):
    return notation.normaliser_texte(x) if isinstance(x, str) else None


# Notation ------------------------------------------------------------------------------------------

def noter_dossier(rep, att, ver):
    """Détail d'un dossier : vrais positifs, champs répondus, champs attendus, et constats."""
    d = {"vp": 0, "repondus": N_DOSSIER, "attendus": N_DOSSIER + N_INTER * len(att["interventions"]),
         "champs": {}, "pieges_inclus": [], "oubliees": [], "ordre": None, "rectificatif": None,
         "null_attendus": 0, "inventes": 0}
    ok_rep = isinstance(rep, dict) and not erreurs_dossier(rep)
    for cle in EQUIPEMENT:
        ok = ok_rep and notation.juste(cle, rep.get(cle), att[cle])
        d["champs"][cle] = ok
        d["vp"] += ok
    ok = ok_rep and notation.juste("statut", rep.get("statut_actuel"), att["statut_actuel"])
    d["champs"]["statut_actuel"] = ok
    d["vp"] += ok
    predites = rep["interventions"] if ok_rep else []
    d["repondus"] += N_INTER * len(predites)
    nature = {_ref(p["reference"]): p["nature"] for p in ver["pieces"]
              if p["nature"] in ("equipement_jumeau", "rapport_annule", "version_remplacee")}
    attendues = {_ref(it["reference_rapport"]): it for it in att["interventions"]}
    vues, ordre_pred = set(), []
    for it in predites:
        cle_ref = _ref(it.get("reference_rapport"))
        if cle_ref in attendues and cle_ref not in vues:
            vues.add(cle_ref)
            ordre_pred.append(cle_ref)
            a = attendues[cle_ref]
            for cle in INTERVENTION:
                ok = notation.juste(cle, it.get(cle), a[cle])
                d["champs"].setdefault(cle, [0, 0])
                d["champs"][cle][0] += 1
                d["champs"][cle][1] += ok
                d["vp"] += ok
                if a[cle] is None:
                    d["null_attendus"] += 1
                    d["inventes"] += it.get(cle) is not None
        else:
            d["pieges_inclus"].append(nature.get(cle_ref, "doublon" if cle_ref in vues else "inconnue"))
    d["oubliees"] = sorted(set(attendues) - vues)
    ordre_att = [r for r in (_ref(it["reference_rapport"]) for it in att["interventions"]) if r in vues]
    d["ordre"] = ordre_pred == ordre_att
    rect = ver.get("rectificatif")
    if rect:
        it = next((x for x in predites if _ref(x.get("reference_rapport")) == _ref(rect["reference"])), None)
        piece = next(p for p in ver["pieces"] if p["nature"] == "rectificatif")
        if it is None:
            d["rectificatif"] = "intervention_absente"
        elif notation.juste(rect["champ"], it.get(rect["champ"]), piece["nouvelle"]):
            d["rectificatif"] = "applique"
        elif notation.juste(rect["champ"], it.get(rect["champ"]), piece["ancienne"]):
            d["rectificatif"] = "ignore"
        else:
            d["rectificatif"] = "autre_valeur"
    d["parfait"] = d["vp"] == d["attendus"] == d["repondus"] and d["ordre"]
    return d


def noter(reponses, attendus, verites):
    """Score F1 par champ sur l'ensemble des dossiers, et scores détaillés."""
    vp = rep_n = att_n = 0
    parfaits = 0
    par_cle = defaultdict(lambda: [0, 0])
    pieges = defaultdict(lambda: [0, 0])   # nature : [présentes, incluses à tort]
    rectif = defaultdict(int)
    oubliees = ordre_ok = null_att = inventes = 0
    n_inter = 0
    detail = {}
    for i, att in attendus.items():
        rep = reponses.get(i) if isinstance(reponses, dict) else None
        d = noter_dossier(rep, att, verites[i])
        detail[i] = d
        vp, rep_n, att_n = vp + d["vp"], rep_n + d["repondus"], att_n + d["attendus"]
        parfaits += d["parfait"]
        for cle, v in d["champs"].items():
            if isinstance(v, list):
                par_cle[cle][0] += v[0]
                par_cle[cle][1] += v[1]
            else:
                par_cle[cle][0] += 1
                par_cle[cle][1] += v
        for p in verites[i]["pieces"]:
            if p["nature"] in ("equipement_jumeau", "rapport_annule", "version_remplacee"):
                pieges[p["nature"]][0] += 1
        for n in d["pieges_inclus"]:
            pieges[n][1] += 1
        if d["rectificatif"]:
            rectif[d["rectificatif"]] += 1
        oubliees += len(d["oubliees"])
        n_inter += len(att["interventions"])
        ordre_ok += bool(d["ordre"])
        null_att += d["null_attendus"]
        inventes += d["inventes"]
    f1 = 2 * vp / (rep_n + att_n) if rep_n + att_n else 0.0
    return {
        "dossiers": len(attendus),
        "score": round(f1, 4),
        "precision": round(vp / rep_n, 4) if rep_n else None,
        "rappel": round(vp / att_n, 4) if att_n else None,
        "dossiers_parfaits": parfaits,
        "interventions": {"attendues": n_inter, "oubliees": oubliees},
        "pieges": {k: {"presents": v[0], "inclus_a_tort": v[1]} for k, v in sorted(pieges.items())},
        "rectificatifs": dict(rectif),
        "ordre_juste": ordre_ok,
        "invention": {"null_attendus": null_att, "inventes": inventes,
                      "taux": round(inventes / null_att, 4) if null_att else None},
        "par": {"cle": {k: {"n": v[0], "justes": v[1], "score": round(v[1] / v[0], 4) if v[0] else None}
                        for k, v in sorted(par_cle.items())}},
        "detail": detail,
    }
