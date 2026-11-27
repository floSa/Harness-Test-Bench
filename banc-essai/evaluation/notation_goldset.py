"""Notation de la tâche « goldset » : un jeu de PDF et de réponses attendues fourni par l'utilisateur.

Le jeu est importé par banc-essai/corpus/importer_goldset.py, qui écrit, pour chaque jeu (fourni,
test-cache, relance), les PDF `doc-XXXX.pdf` et leurs réponses `reponses/doc-XXXX.json`, et à côté
des jeux le fichier `schema.json` qui décrit chaque champ :

    {"version": 1, "valide": true, "description": "...",
     "champs": {"<chemin>": {"type": "texte|nombre|date|booleen|enum|liste",
                             "description": "...", "tolerance": 0.01, "valeurs": [...]}}}

Un chemin désigne une valeur dans le JSON d'un document ; un objet imbriqué donne des chemins
pointés (`adresse.ville`). La réponse d'un document reproduit la structure des réponses attendues.

Règles de comparaison (par type) :
- `null` attendu : juste seulement si la réponse est `null` ;
- texte : égal après normalisation (casse, accents, espaces) ;
- enum : une des valeurs permises, égale après normalisation ;
- nombre : écart au plus égal à la tolérance du champ (0,01 par défaut) ;
- date : chaîne `AAAA-MM-JJ` égale ;
- booléen : égal ;
- liste : éléments comparés sans ordre ; crédit partiel = F1 entre les éléments répondus et attendus
  (éléments normalisés comme ci-dessus ; un élément objet est comparé en entier).

Score : moyenne des crédits sur tous les champs de tous les documents (un champ juste vaut 1 ; une
liste vaut son F1). Sont aussi rendus : documents entièrement justes, score par champ, taux
d'invention (valeur donnée là où `null` est attendu) et taux d'omission (`null` donné là où une valeur
est attendue).
"""
import datetime
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

TYPES = {"texte", "nombre", "date", "booleen", "enum", "liste"}
TOLERANCE = 0.01
NOMBRE_MAX = 1e15
SEPARATEUR = "."


# Schéma ------------------------------------------------------------------------------------------

def charger_schema(chemin):
    s = json.loads(Path(chemin).read_text())
    err = erreurs_schema(s)
    if err:
        raise SystemExit(f"{chemin} : " + " ; ".join(err))
    return s


def erreurs_schema(s):
    if not isinstance(s, dict) or not isinstance(s.get("champs"), dict) or not s["champs"]:
        return ["objet avec « champs » non vide attendu"]
    err = []
    for chemin, d in s["champs"].items():
        if not isinstance(d, dict) or d.get("type") not in TYPES:
            err.append(f"{chemin} : type parmi {sorted(TYPES)} attendu")
            continue
        if d["type"] == "enum" and not (isinstance(d.get("valeurs"), list) and d["valeurs"]):
            err.append(f"{chemin} : enum sans liste « valeurs »")
        if "tolerance" in d and not (isinstance(d["tolerance"], (int, float)) and d["tolerance"] >= 0):
            err.append(f"{chemin} : tolérance positive attendue")
    return err


# Chemins -----------------------------------------------------------------------------------------

def aplatir(obj, prefixe=""):
    """{chemin: valeur} : les objets imbriqués sont dépliés, les listes restent des valeurs."""
    plat = {}
    for k, v in obj.items():
        chemin = f"{prefixe}{SEPARATEUR}{k}" if prefixe else str(k)
        if isinstance(v, dict) and v:
            plat.update(aplatir(v, chemin))
        else:
            plat[chemin] = v
    return plat


def deplier(plat):
    """Inverse d'aplatir : objet imbriqué à partir des chemins pointés."""
    obj = {}
    for chemin, v in plat.items():
        cur = obj
        *haut, bas = chemin.split(SEPARATEUR)
        for k in haut:
            cur = cur.setdefault(k, {})
        cur[bas] = v
    return obj


# Normalisation -----------------------------------------------------------------------------------

def normaliser_texte(t):
    t = unicodedata.normalize("NFKD", str(t))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.casefold().split())


def element(x):
    """Forme comparable d'un élément de liste."""
    if isinstance(x, bool) or x is None:
        return json.dumps(x)
    if isinstance(x, (int, float)):
        return f"{round(float(x), 2):g}"
    if isinstance(x, str):
        return normaliser_texte(x)
    if isinstance(x, list):
        return json.dumps(sorted(element(e) for e in x), ensure_ascii=False)
    if isinstance(x, dict):
        return json.dumps({k: element(v) for k, v in sorted(x.items())}, ensure_ascii=False, sort_keys=True)
    return str(x)


# Format ------------------------------------------------------------------------------------------

def erreurs_valeur(chemin, v, d):
    """Erreurs de format d'une valeur selon la définition `d` du champ (vide si acceptable)."""
    if v is None:
        return []
    t = d["type"]
    montre = json.dumps(v, ensure_ascii=False)[:80]
    if t == "nombre":
        if isinstance(v, bool) or not isinstance(v, (int, float)) or (isinstance(v, float) and not math.isfinite(v)):
            return [f"{chemin} : nombre JSON ou null attendu, reçu {montre}"]
        if abs(v) > NOMBRE_MAX:
            return [f"{chemin} : nombre hors limites"]
        return []
    if t == "booleen":
        return [] if isinstance(v, bool) else [f"{chemin} : true, false ou null attendu, reçu {montre}"]
    if t == "liste":
        return [] if isinstance(v, list) else [f"{chemin} : liste JSON ou null attendue, reçu {montre}"]
    if not isinstance(v, str):
        return [f"{chemin} : texte ou null attendu, reçu {montre}"]
    if not v.strip():
        return [f"{chemin} : texte vide (utiliser null pour une valeur absente)"]
    if t == "date":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return [f"{chemin} : date au format AAAA-MM-JJ attendue, reçu « {v[:40]} »"]
        try:
            datetime.date.fromisoformat(v)
        except ValueError:
            return [f"{chemin} : date impossible « {v} »"]
    if t == "enum" and normaliser_texte(v) not in {normaliser_texte(x) for x in d["valeurs"]}:
        return [f"{chemin} : une de {d['valeurs'][:20]} ou null attendue, reçu « {v[:40]} »"]
    return []


def erreurs_document(r, schema):
    if not isinstance(r, dict):
        return ["objet JSON attendu"]
    plat = aplatir(r)
    champs = schema["champs"]
    err = []
    manq, trop = sorted(set(champs) - set(plat)), sorted(set(plat) - set(champs))
    if manq or trop:
        err.append(f"clés manquantes {manq[:30]}, clés en trop {trop[:30]}")
    for chemin, d in champs.items():
        if chemin in plat:
            err += erreurs_valeur(chemin, plat[chemin], d)
    return err


def valider(reponses, ids, schema):
    """Erreurs de format d'une soumission : un objet par document attendu, exactement les champs du schéma."""
    if not isinstance(reponses, dict):
        return ["les réponses doivent être un objet {identifiant: {clé: valeur}}"]
    err = []
    manquants, inconnus = sorted(set(ids) - set(reponses)), sorted(set(reponses) - set(ids))
    if manquants:
        err.append(f"documents manquants : {', '.join(manquants[:50])}")
    if inconnus:
        err.append(f"documents inconnus : {', '.join(inconnus[:50])}")
    for i in sorted(set(ids) & set(reponses)):
        err += [f"{i} : {e}" for e in erreurs_document(reponses[i], schema)]
    return err


# Comparaison -------------------------------------------------------------------------------------

def credit(d, reponse, attendu):
    """Crédit d'un champ entre 0 et 1. Une valeur au mauvais format vaut 0."""
    vide = lambda x: x is None or x == [] or (isinstance(x, str) and not x.strip())
    if vide(attendu):
        return float(vide(reponse))
    if vide(reponse) or erreurs_valeur("", reponse, d):
        return 0.0
    t = d["type"]
    if t == "nombre":
        return float(abs(float(reponse) - float(attendu)) <= d.get("tolerance", TOLERANCE) + 1e-9)
    if t in ("date", "booleen"):
        return float(reponse == attendu)
    if t == "liste":
        r, a = Counter(map(element, reponse)), Counter(map(element, attendu))
        communs = sum((r & a).values())
        return 2 * communs / (sum(r.values()) + sum(a.values()))
    return float(normaliser_texte(reponse) == normaliser_texte(attendu))


# Jeu -----------------------------------------------------------------------------------------------

def charger_jeu(dossier):
    """Identifiants (triés), réponses attendues et schéma d'un jeu importé (schéma : dossier parent)."""
    d = Path(dossier)
    ids = sorted(p.stem for p in d.glob("doc-*.pdf"))
    attendus = {i: json.loads((d / "reponses" / f"{i}.json").read_text()) for i in ids}
    schema = charger_schema(d.parent / "schema.json")
    return ids, attendus, schema


# Notation ------------------------------------------------------------------------------------------

def noter(reponses, attendus, schema):
    """Note des réponses (document sans réponse ou mal formé : tous ses champs à 0)."""
    champs = schema["champs"]
    par_cle = defaultdict(lambda: [0, 0.0])
    total = n = 0.0
    parfaits = null_att = inventes = valeur_att = omises = 0
    detail = {}
    for i, att in attendus.items():
        r = reponses.get(i) if isinstance(reponses, dict) else None
        ok_doc = isinstance(r, dict) and not erreurs_document(r, schema)
        pr, pa = (aplatir(r) if ok_doc else {}), aplatir(att)
        detail[i] = {}
        somme = 0.0
        for chemin, d in champs.items():
            a, rep = pa.get(chemin), pr.get(chemin)
            c = credit(d, rep, a) if ok_doc else 0.0
            detail[i][chemin] = round(c, 4)
            par_cle[chemin][0] += 1
            par_cle[chemin][1] += c
            somme += c
            n += 1
            if a is None or a == []:
                null_att += 1
                inventes += ok_doc and rep not in (None, [])
            else:
                valeur_att += 1
                omises += (not ok_doc) or rep in (None, [])
        total += somme
        parfaits += ok_doc and somme == len(champs)
    return {
        "documents": len(attendus),
        "champs": int(n),
        "justes": round(total, 2),
        "score": round(total / n, 4) if n else 0.0,
        "documents_parfaits": parfaits,
        "invention": {"null_attendus": null_att, "inventes": inventes,
                      "taux": round(inventes / null_att, 4) if null_att else None},
        "omission": {"valeurs_attendues": valeur_att, "omises": omises,
                     "taux": round(omises / valeur_att, 4) if valeur_att else None},
        "par": {"cle": {k: {"n": v[0], "justes": round(v[1], 2), "score": round(v[1] / v[0], 4)}
                        for k, v in sorted(par_cle.items())}},
        "detail": detail,
    }
