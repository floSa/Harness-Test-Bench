"""Importe un goldset (PDF et réponses attendues) dans le format du banc, après vérification.

    python3 banc-essai/corpus/importer_goldset.py [--source goldset] [--destination banc-essai/corpus/goldset]
        [--repartition train=fourni,val=test-cache,test=relance] [--schema-neuf]

Source attendue (racine du dépôt, jamais versionnée) :

    goldset/
    ├── ground_truth.json              (facultatif : tous les documents, sert au recoupement)
    └── split/
        ├── train/*.pdf   val/*.pdf   test/*.pdf
        └── train_ground_truth.json   val_ground_truth.json   test_ground_truth.json

Un fichier de vérité associe à chaque PDF ses valeurs attendues. Formes reconnues :
`{"a.pdf": {...}}`, `{"a": {...}}`, `[{"file_name": "a.pdf", ...valeurs}]`, une liste sous une clé
unique (`{"documents": [...]}`), et des valeurs enveloppées (`{"a.pdf": {"fields": {...}}}`).
Toute autre forme arrête l'import avec un message : adapter alors `lire_verite()` (voir
banc-essai/documentation/goldset.md).

Étapes :
1. lecture et appariement PDF / vérité, dans chaque jeu ;
2. contrôles : PDF lisibles, PDF sans vérité, vérité sans PDF, doublons entre jeux (nom ou contenu),
   recoupement avec ground_truth.json, clés présentes dans chaque document ;
3. analyse de chaque champ (types rencontrés, formats de date, nombres écrits en texte) et schéma
   proposé (`schema.json`, « valide »: false) ; un schéma existant n'est jamais écrasé (sauf
   --schema-neuf) : c'est lui qui sert à convertir les valeurs ;
4. écriture des jeux du banc : `<destination>/<jeu>/doc-XXXX.pdf` et `reponses/doc-XXXX.json`
   (valeurs converties : nombres JSON, dates AAAA-MM-JJ, booléens ; champ absent : null),
   `correspondance.json` (identifiant -> jeu et fichier d'origine) ;
5. contrôle de la notation : les réponses attendues obtiennent 100 % et passent le contrôle de
   format ; une réponse altérée perd des points ;
6. rapport `<destination>/rapport-import.md`.

La destination doit être ignorée par git (contrôle `git check-ignore`), sinon l'import s'arrête.
Bibliothèque standard seulement.
"""
import argparse
import copy
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI.parent / "evaluation"))
import notation_goldset as ng  # noqa: E402

JEUX_SOURCE = ["train", "val", "test"]
REPARTITION = "train=fourni,val=test-cache,test=relance"
CLES_NOM = ["file_name", "filename", "file", "fichier", "nom_fichier", "document", "doc", "pdf", "name", "nom",
            "id", "path", "chemin", "source"]
ENVELOPPES = ["fields", "champs", "ground_truth", "groundtruth", "labels", "annotations", "values", "valeurs",
              "data", "donnees", "extraction", "attendu", "expected"]
FORMATS_DATE = [("AAAA-MM-JJ", r"(\d{4})-(\d{1,2})-(\d{1,2})", "amj"),
                ("AAAA/MM/JJ", r"(\d{4})/(\d{1,2})/(\d{1,2})", "amj"),
                ("JJ/MM/AAAA", r"(\d{1,2})/(\d{1,2})/(\d{4})", "jma"),
                ("JJ-MM-AAAA", r"(\d{1,2})-(\d{1,2})-(\d{4})", "jma"),
                ("JJ.MM.AAAA", r"(\d{1,2})\.(\d{1,2})\.(\d{4})", "jma"),
                ("AAAA-MM-JJTHH:MM", r"(\d{4})-(\d{2})-(\d{2})[T ][\d:.]+(?:Z|[+-]\d{2}:?\d{2})?", "amj")]
BOOLEENS = {"true": True, "false": False, "vrai": True, "faux": False, "oui": True, "non": False,
            "yes": True, "no": False}


class ImportArrete(Exception):
    pass


# 1. Lecture -----------------------------------------------------------------------------------------

def cle_nom(nom):
    """Clé d'appariement d'un nom de fichier : nom de base, sans .pdf, en minuscules."""
    base = str(nom).replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"\.pdf$", "", base, flags=re.I).casefold()


def lire_verite(chemin):
    """{nom de fichier: valeurs attendues} et description de la forme reconnue."""
    brut = json.loads(Path(chemin).read_text(encoding="utf-8-sig"))
    forme = []
    if isinstance(brut, dict) and len(brut) == 1 and isinstance(next(iter(brut.values())), list):
        forme.append(f"liste sous la clé « {next(iter(brut))} »")
        brut = next(iter(brut.values()))
    if isinstance(brut, list):
        if not brut or not all(isinstance(x, dict) for x in brut):
            raise ImportArrete(f"{chemin} : liste d'objets attendue")
        communs = set.intersection(*(set(x) for x in brut))
        nom = next((c for c in CLES_NOM if c in communs), None)
        if nom is None:
            raise ImportArrete(f"{chemin} : liste d'objets sans clé de nom de fichier reconnue "
                               f"(cherchées : {', '.join(CLES_NOM)} ; présentes partout : {sorted(communs)[:15]}). "
                               "Adapter lire_verite().")
        forme.append(f"liste d'objets, nom de fichier dans « {nom} »")
        verite = {}
        for x in brut:
            valeurs = {k: v for k, v in x.items() if k != nom}
            if str(x[nom]) in verite:
                raise ImportArrete(f"{chemin} : « {x[nom]} » apparaît deux fois")
            verite[str(x[nom])] = valeurs
    elif isinstance(brut, dict) and brut and all(isinstance(v, dict) for v in brut.values()):
        forme.append("objet {nom de fichier: valeurs}")
        verite = {str(k): v for k, v in brut.items()}
    else:
        raise ImportArrete(f"{chemin} : forme non reconnue (ni objet {{fichier: valeurs}}, ni liste d'objets). "
                           "Adapter lire_verite().")
    # Valeurs enveloppées : chaque document a une même clé unique dont la valeur est un objet.
    for _ in range(2):
        cles = {tuple(v) for v in verite.values()}
        if len(cles) == 1 and len(next(iter(cles))) == 1:
            k = next(iter(cles))[0]
            if k.casefold() in ENVELOPPES and all(isinstance(v[k], dict) for v in verite.values()):
                forme.append(f"valeurs enveloppées sous « {k} »")
                verite = {n: v[k] for n, v in verite.items()}
                continue
        break
    # Enveloppe partielle (clé de métadonnées à côté) : signalée, pas devinée.
    return verite, " ; ".join(forme)


def lire_source(source):
    """Par jeu : PDF trouvés, vérité, forme ; plus la vérité globale éventuelle."""
    source = Path(source)
    split = source / "split"
    if not split.is_dir():
        raise ImportArrete(f"{split} introuvable : la source doit contenir split/ (voir la documentation)")
    jeux = {}
    for j in JEUX_SOURCE:
        d = split / j
        f = split / f"{j}_ground_truth.json"
        if not d.is_dir():
            raise ImportArrete(f"{d} introuvable")
        pdfs = sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
        autres = sorted(p.name for p in d.iterdir() if p.is_file() and p.suffix.lower() != ".pdf")
        if f.exists():
            verite, forme = lire_verite(f)
        else:
            verite, forme = None, None
        jeux[j] = {"dossier": d, "pdfs": pdfs, "autres": autres, "verite": verite, "forme": forme,
                   "fichier_verite": f}
    globale, forme_g = (lire_verite(source / "ground_truth.json") if (source / "ground_truth.json").exists()
                        else (None, None))
    for j, x in jeux.items():
        if x["verite"] is None:
            if globale is None:
                raise ImportArrete(f"ni {x['fichier_verite'].name} ni ground_truth.json : aucune vérité pour {j}")
            noms = {cle_nom(p.name) for p in x["pdfs"]}
            x["verite"] = {n: v for n, v in globale.items() if cle_nom(n) in noms}
            x["forme"] = f"extrait de ground_truth.json ({forme_g})"
    return jeux, globale, forme_g


# 2. Contrôles -----------------------------------------------------------------------------------------

def empreinte(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def apparier(jeux, globale):
    """Documents appariés par jeu, et constats."""
    constats = defaultdict(list)
    docs = {}
    vus_nom, vus_contenu = {}, {}
    for j, x in jeux.items():
        par_cle = {}
        for n, v in x["verite"].items():
            k = cle_nom(n)
            if k in par_cle:
                constats["bloquant"].append(f"{j} : deux entrées de vérité pour « {n} »")
            par_cle[k] = (n, v)
        pdf_par_cle = {cle_nom(p.name): p for p in x["pdfs"]}
        for k in sorted(set(pdf_par_cle) - set(par_cle)):
            constats["ecartes"].append(f"{j} : PDF sans vérité, écarté : {pdf_par_cle[k].name}")
        for k in sorted(set(par_cle) - set(pdf_par_cle)):
            constats["ecartes"].append(f"{j} : vérité sans PDF, écartée : {par_cle[k][0]}")
        if x["autres"]:
            constats["info"].append(f"{j} : fichiers non PDF ignorés : {', '.join(x['autres'][:10])}")
        docs[j] = []
        for k in sorted(set(pdf_par_cle) & set(par_cle)):
            p = pdf_par_cle[k]
            n, v = par_cle[k]
            debut = p.read_bytes()[:1024]
            if b"%PDF" not in debut:
                constats["ecartes"].append(f"{j} : {p.name} ne commence pas comme un PDF, écarté")
                continue
            if not isinstance(v, dict):
                constats["ecartes"].append(f"{j} : vérité de {n} qui n'est pas un objet, écartée")
                continue
            h = empreinte(p)
            if k in vus_nom:
                constats["bloquant"].append(f"« {p.name} » présent dans {vus_nom[k]} et {j}")
            if h in vus_contenu:
                constats["bloquant"].append(f"même contenu : {vus_contenu[h][1]} ({vus_contenu[h][0]}) et {p.name} ({j})")
            vus_nom[k], vus_contenu[h] = j, (j, p.name)
            docs[j].append({"jeu": j, "pdf": p, "nom_verite": n, "valeurs": v, "empreinte": h,
                            "octets": p.stat().st_size})
    if globale is not None:
        g = {cle_nom(n): v for n, v in globale.items()}
        ecarts = [d["pdf"].name for j in docs for d in docs[j]
                  if cle_nom(d["pdf"].name) in g and g[cle_nom(d["pdf"].name)] != d["valeurs"]]
        absents = [d["pdf"].name for j in docs for d in docs[j] if cle_nom(d["pdf"].name) not in g]
        total = sum(len(v) for v in docs.values())
        constats["info"].append(f"recoupement avec ground_truth.json : {len(g)} entrées, "
                                f"{total - len(ecarts) - len(absents)} identiques sur {total} documents appariés")
        for n in ecarts[:20]:
            constats["attention"].append(f"valeurs différentes entre le fichier du jeu et ground_truth.json : {n}")
        for n in absents[:20]:
            constats["attention"].append(f"absent de ground_truth.json : {n}")
    return docs, constats


# 3. Analyse des champs et schéma proposé ---------------------------------------------------------------

def nombre_texte(s):
    """Nombre écrit en texte (« 1 234,5 », « 12.5 », « -3 ») ou None."""
    t = s.strip().replace(" ", " ").replace("\xa0", " ")
    if re.fullmatch(r"[-+]?\d{1,3}( \d{3})+(,\d+)?", t) or re.fullmatch(r"[-+]?\d+(,\d+)?", t):
        t = t.replace(" ", "").replace(",", ".")
    elif re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+(\.\d+)?", t):
        t = t.replace(",", "")
    elif not re.fullmatch(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?", t):
        return None
    try:
        return float(t) if any(c in t for c in ".eE") else int(t)
    except ValueError:
        return None


def date_texte(s, ordre_jm="jm"):
    """(date ISO, nom du format) ou (None, None). ordre_jm : « jm » (jour d'abord) ou « mj »."""
    for nom, motif, sens in FORMATS_DATE:
        m = re.fullmatch(motif, s.strip())
        if not m:
            continue
        a, b, c = (int(x) for x in m.groups())
        if sens == "amj":
            an, mois, jour = a, b, c
        else:
            jour, mois, an = (a, b, c) if ordre_jm == "jm" else (b, a, c)
        try:
            return datetime.date(an, mois, jour).isoformat(), nom
        except ValueError:
            return None, None
    return None, None


def analyser(docs):
    """Par chemin : présence, types rencontrés, formats, exemples."""
    stats = defaultdict(lambda: {"presents": 0, "types": Counter(), "formats_date": Counter(), "nombres_texte": 0,
                                 "exemples": [], "valeurs": Counter(), "jm_sur": False, "mj_sur": False})
    n = 0
    for j in docs:
        for d in docs[j]:
            n += 1
            for chemin, v in ng.aplatir(d["valeurs"]).items():
                s = stats[chemin]
                s["presents"] += 1
                t = ("null" if v is None else "booleen" if isinstance(v, bool) else "nombre"
                     if isinstance(v, (int, float)) else "texte" if isinstance(v, str) else "liste"
                     if isinstance(v, list) else "objet_vide" if v == {} else type(v).__name__)
                s["types"][t] += 1
                if isinstance(v, str):
                    iso, fmt = date_texte(v)
                    if fmt:
                        s["formats_date"][fmt] += 1
                        m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-]\d{4}", v.strip())
                        if m:
                            s["jm_sur"] |= int(m.group(1)) > 12
                            s["mj_sur"] |= int(m.group(2)) > 12
                    if nombre_texte(v) is not None:
                        s["nombres_texte"] += 1
                    s["valeurs"][v] += 1
                if v is not None and len(s["exemples"]) < 3 and json.dumps(v, ensure_ascii=False) not in s["exemples"]:
                    s["exemples"].append(json.dumps(v, ensure_ascii=False)[:60])
    return stats, n


def proposer(stats, n):
    """Schéma proposé et justification par champ."""
    champs, notes = {}, {}
    for chemin, s in sorted(stats.items()):
        t = s["types"]
        non_null = sum(c for k, c in t.items() if k != "null")
        d = {"type": "texte", "description": ""}
        if non_null == 0:
            raison = "toujours null : type texte par défaut, à confirmer"
        elif set(t) - {"null"} == {"booleen"}:
            d["type"], raison = "booleen", "booléens JSON"
        elif set(t) - {"null"} == {"liste"}:
            d["type"], raison = "liste", "listes JSON (comparées sans ordre, crédit partiel)"
        elif set(t) - {"null"} == {"nombre"}:
            d["type"], d["tolerance"], raison = "nombre", 0.01, "nombres JSON ; tolérance 0,01 à ajuster à l'unité"
        elif set(t) - {"null"} <= {"texte", "nombre"} and t["texte"] and sum(s["formats_date"].values()) == t["texte"] \
                and not t["nombre"]:
            d["type"] = "date"
            fmts = ", ".join(f"{k} ({c})" for k, c in s["formats_date"].most_common())
            ordre = ("jour avant mois (un jour > 12 vu)" if s["jm_sur"] and not s["mj_sur"] else
                     "mois avant jour (un mois > 12 vu en 2e position)" if s["mj_sur"] and not s["jm_sur"] else
                     "ordre jour/mois NON déterminable : jour d'abord supposé, à confirmer" if s["formats_date"].keys()
                     - {"AAAA-MM-JJ", "AAAA/MM/JJ", "AAAA-MM-JJTHH:MM"} else "format année d'abord")
            d["ordre_jour_mois"] = "mj" if s["mj_sur"] and not s["jm_sur"] else "jm"
            raison = f"dates écrites en texte : {fmts} ; {ordre} ; converties en AAAA-MM-JJ"
        elif set(t) - {"null"} <= {"texte", "nombre"} and s["nombres_texte"] == t["texte"]:
            d["type"], d["tolerance"] = "nombre", 0.01
            raison = (f"nombres écrits en texte ({t['texte']}) convertis en nombres JSON" if t["texte"]
                      else "nombres JSON") + " ; tolérance 0,01 à ajuster"
        elif set(t) - {"null"} == {"texte"}:
            distinctes = len(s["valeurs"])
            if distinctes <= 12 and t["texte"] >= 15 and distinctes <= t["texte"] / 4:
                d["type"] = "enum"
                d["valeurs"] = sorted(s["valeurs"])
                raison = f"texte à {distinctes} valeurs distinctes sur {t['texte']} : liste fermée proposée"
            else:
                raison = "texte libre (normalisé : casse, accents, espaces)"
        else:
            raison = f"types mélangés {dict(t)} : texte par défaut, À EXAMINER (valeurs converties en texte)"
        if s["presents"] < n:
            raison += f" ; absent de {n - s['presents']} documents (null attendu)"
        champs[chemin] = d
        notes[chemin] = raison
    return {"version": 1, "valide": False,
            "description": "À compléter : nature des documents et de l'information recherchée (repris dans les consignes).",
            "champs": champs}, notes


# 4. Conversion et écriture -------------------------------------------------------------------------------

def convertir(v, d):
    """(valeur convertie, converti_ok)."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None, True
    t = d["type"]
    if t == "nombre":
        if isinstance(v, bool):
            return v, False
        if isinstance(v, (int, float)):
            return v, True
        x = nombre_texte(v) if isinstance(v, str) else None
        return (x, True) if x is not None else (v, False)
    if t == "date":
        if isinstance(v, str):
            iso, _ = date_texte(v, d.get("ordre_jour_mois", "jm"))
            if iso:
                return iso, True
        return v, False
    if t == "booleen":
        if isinstance(v, bool):
            return v, True
        if isinstance(v, str) and v.strip().casefold() in BOOLEENS:
            return BOOLEENS[v.strip().casefold()], True
        if v in (0, 1):
            return bool(v), True
        return v, False
    if t == "liste":
        return (v, True) if isinstance(v, list) else (v, False)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f"{v:g}" if isinstance(v, float) else str(v), True
    if isinstance(v, str):
        if t == "enum" and ng.normaliser_texte(v) not in {ng.normaliser_texte(x) for x in d["valeurs"]}:
            return v, False
        return v, True
    return json.dumps(v, ensure_ascii=False), False


def identifiants(docs):
    """doc-XXXX attribués dans un ordre tiré de l'empreinte : ni le jeu ni l'ordre d'origine ne transparaissent."""
    tous = sorted((d for j in docs for d in docs[j]), key=lambda d: hashlib.sha256(
        (d["jeu"] + "/" + d["pdf"].name + "/" + d["empreinte"]).encode()).hexdigest())
    largeur = max(3, len(str(len(tous))))
    for k, d in enumerate(tous, start=1):
        d["id"] = f"doc-{k:0{largeur}d}"


def ecrire(docs, schema, destination, repartition):
    conversions = defaultdict(lambda: [0, 0, []])   # chemin : [convertis, échecs, exemples d'échec]
    for jeu_banc in set(repartition.values()):
        d = destination / jeu_banc
        if d.exists():
            shutil.rmtree(d)
        (d / "reponses").mkdir(parents=True)
    correspondance = {}
    for j, liste in docs.items():
        dest = destination / repartition[j]
        for doc in liste:
            plat = ng.aplatir(doc["valeurs"])
            sortie = {}
            for chemin, dfn in schema["champs"].items():
                v, ok = convertir(plat.get(chemin), dfn)
                sortie[chemin] = v
                if plat.get(chemin) is not None and v is not plat.get(chemin):
                    conversions[chemin][0] += 1
                if not ok:
                    conversions[chemin][1] += 1
                    if len(conversions[chemin][2]) < 3:
                        conversions[chemin][2].append(json.dumps(plat.get(chemin), ensure_ascii=False)[:40])
            shutil.copy2(doc["pdf"], dest / f"{doc['id']}.pdf")
            (dest / "reponses" / f"{doc['id']}.json").write_text(
                json.dumps(ng.deplier(sortie), ensure_ascii=False, indent=2) + "\n")
            correspondance[doc["id"]] = {"jeu_source": j, "jeu_banc": repartition[j], "fichier": doc["pdf"].name,
                                         "entree_verite": doc["nom_verite"], "sha256": doc["empreinte"]}
    (destination / "correspondance.json").write_text(json.dumps(dict(sorted(correspondance.items())),
                                                                ensure_ascii=False, indent=2) + "\n")
    return conversions


# 5. Contrôle de la notation --------------------------------------------------------------------------------

def alterer(r, schema):
    """Copie de la réponse avec une valeur non nulle changée (ou une valeur inventée)."""
    plat = ng.aplatir(copy.deepcopy(r))
    for chemin, d in schema["champs"].items():
        v = plat.get(chemin)
        if v is None:
            continue
        t = d["type"]
        plat[chemin] = (v + 1000 if t == "nombre" else (not v) if t == "booleen" else "1900-01-01"
                        if t == "date" else (v + ["ajout"]) if t == "liste" else "valeur altérée")
        if t == "enum":
            autres = [x for x in d["valeurs"] if ng.normaliser_texte(x) != ng.normaliser_texte(v)]
            if not autres:
                continue
            plat[chemin] = autres[0]
        return ng.deplier(plat)
    chemin = next(iter(schema["champs"]))
    plat[chemin] = "valeur inventée" if schema["champs"][chemin]["type"] in ("texte", "enum") else plat[chemin]
    return ng.deplier(plat)


def controler(destination, repartition, schema):
    lignes = []
    tout_ok = True
    for jeu_banc in sorted(set(repartition.values())):
        ids = sorted(p.stem for p in (destination / jeu_banc).glob("doc-*.pdf"))
        att = {i: json.loads((destination / jeu_banc / "reponses" / f"{i}.json").read_text()) for i in ids}
        err = ng.valider(att, ids, schema)
        note = ng.noter(att, att, schema)
        alt = {i: alterer(r, schema) for i, r in att.items()}
        note_alt = ng.noter(alt, att, schema)
        ok = not err and note["score"] == 1.0 and note_alt["score"] < 1.0
        tout_ok &= ok
        lignes.append((jeu_banc, len(ids), len(err), note["score"], note_alt["score"], ok, err[:5]))
    return lignes, tout_ok


# 6. Rapport ------------------------------------------------------------------------------------------------

def rapport(destination, source, jeux, docs, constats, stats, n, schema, notes, schema_origine, conversions,
            controle, repartition):
    L = ["# Rapport d'import du goldset", "",
         f"Source : `{source}` ; destination : `{destination}` ; "
         f"date : {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}.", "",
         "## Jeux", "", "| Jeu source | Jeu du banc | PDF trouvés | Entrées de vérité | Documents importés | Forme du fichier de vérité |",
         "|---|---|---|---|---|---|"]
    for j, x in jeux.items():
        L.append(f"| {j} | {repartition[j]} | {len(x['pdfs'])} | {len(x['verite'])} | {len(docs[j])} | {x['forme']} |")
    L += ["", "## Constats", ""]
    noms = {"bloquant": "Bloquant (import arrêté)", "attention": "À examiner", "ecartes": "Documents écartés",
            "info": "Information"}
    if not any(constats.values()):
        L.append("Aucun constat.")
    for k in ("bloquant", "attention", "ecartes", "info"):
        if constats.get(k):
            L += [f"### {noms[k]}", ""] + [f"- {c}" for c in constats[k][:60]]
            if len(constats[k]) > 60:
                L.append(f"- ... et {len(constats[k]) - 60} autres")
            L.append("")
    L += ["## Champs", "",
          f"Schéma utilisé : `{destination / 'schema.json'}` ({schema_origine}). "
          "Un champ imbriqué est désigné par son chemin pointé (`adresse.ville`).", "",
          "| Champ | Présent dans | Types rencontrés | Type retenu | Exemples | Justification | Conversions | Échecs de conversion |",
          "|---|---|---|---|---|---|---|---|"]
    for chemin in sorted(set(stats) | set(schema["champs"])):
        s = stats.get(chemin)
        d = schema["champs"].get(chemin, {})
        types = ", ".join(f"{k} {c}" for k, c in s["types"].most_common()) if s else "absent du goldset"
        ex = " ; ".join(f"`{e}`" for e in s["exemples"]) if s else ""
        conv = conversions.get(chemin, [0, 0, []])
        echecs = f"{conv[1]} ({' ; '.join(conv[2])})" if conv[1] else "0"
        retenu = d.get("type", "NON RETENU (absent du schéma)")
        L.append(f"| `{chemin}` | {s['presents'] if s else 0}/{n} | {types} | {retenu} | {ex} | "
                 f"{notes.get(chemin, '')} | {conv[0]} | {echecs} |")
    L += ["", "## Contrôle de la notation", "",
          "| Jeu du banc | Documents | Erreurs de format des réponses attendues | Score des réponses attendues | Score d'une réponse altérée par document | Conforme |",
          "|---|---|---|---|---|---|"]
    lignes, ok = controle
    for jeu_banc, nb, nerr, s1, s2, conf, err in lignes:
        L.append(f"| {jeu_banc} | {nb} | {nerr} | {s1:.4f} | {s2:.4f} | {'oui' if conf else 'NON'} |")
    for jeu_banc, nb, nerr, s1, s2, conf, err in lignes:
        L += [f"- {jeu_banc} : {e}" for e in err]
    L += ["", "## Suite", ""]
    if not schema.get("valide"):
        L += ["1. Relire `schema.json` : type de chaque champ, tolérance des nombres, ordre jour/mois des dates, "
              "liste des valeurs des enum, et une `description` par champ (reprise dans les consignes).",
              "2. Mettre `\"valide\": true`, puis relancer l'import : les valeurs sont converties selon le schéma validé.",
              "3. Générer les consignes : `python3 banc-essai/corpus/consignes_goldset.py`."]
    else:
        L += ["Schéma validé. Étape suivante : `python3 banc-essai/corpus/consignes_goldset.py`."]
    (destination / "rapport-import.md").write_text("\n".join(L) + "\n")


# Principal -----------------------------------------------------------------------------------------------

def ignore_par_git(chemin):
    r = subprocess.run(["git", "-C", str(RACINE), "check-ignore", "-q", str(chemin)], capture_output=True)
    return r.returncode == 0


def importer(source, destination, repartition=REPARTITION, schema_neuf=False, verifier_git=True):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    rep = dict(x.split("=", 1) for x in repartition.split(","))
    if sorted(rep) != sorted(JEUX_SOURCE) or len(set(rep.values())) != 3 \
            or not set(rep.values()) <= {"fourni", "test-cache", "relance"}:
        raise ImportArrete("répartition : train, val et test vers fourni, test-cache et relance, chacun une fois")
    if verifier_git and not ignore_par_git(destination / "x"):
        raise ImportArrete(f"{destination} n'est pas ignoré par git : données de l'entreprise jamais versionnées")
    jeux, globale, _ = lire_source(source)
    docs, constats = apparier(jeux, globale)
    if constats.get("bloquant"):
        raise ImportArrete("constats bloquants :\n- " + "\n- ".join(constats["bloquant"][:30]))
    if not all(docs.values()):
        raise ImportArrete(f"jeu vide après appariement : {[j for j in docs if not docs[j]]}")
    stats, n = analyser(docs)
    destination.mkdir(parents=True, exist_ok=True)
    f_schema = destination / "schema.json"
    propose, notes = proposer(stats, n)
    if f_schema.exists() and not schema_neuf:
        schema = ng.charger_schema(f_schema)
        origine = "existant, " + ("validé" if schema.get("valide") else "NON validé")
        manquants = sorted(set(stats) - set(schema["champs"]))
        if manquants:
            constats["attention"].append(f"champs du goldset absents du schéma (ignorés) : {manquants[:20]}")
    else:
        schema = propose
        f_schema.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n")
        origine = "proposé par l'import, NON validé"
    identifiants(docs)
    conversions = ecrire(docs, schema, destination, rep)
    controle = controler(destination, rep, schema)
    rapport(destination, source, jeux, docs, constats, stats, n, schema, notes, origine, conversions, controle, rep)
    return {"documents": {rep[j]: len(docs[j]) for j in docs}, "schema": origine, "controle_ok": controle[1],
            "constats": {k: len(v) for k, v in constats.items()},
            "echecs_conversion": sum(c[1] for c in conversions.values())}


def main():
    a = argparse.ArgumentParser(description="Importe un goldset dans le format du banc")
    a.add_argument("--source", default=str(RACINE / "goldset"))
    a.add_argument("--destination", default=str(ICI / "goldset"))
    a.add_argument("--repartition", default=REPARTITION)
    a.add_argument("--schema-neuf", action="store_true", help="réécrit la proposition de schéma (écrase schema.json)")
    o = a.parse_args()
    try:
        r = importer(o.source, o.destination, o.repartition, o.schema_neuf)
    except ImportArrete as e:
        print(f"import arrêté : {e}", file=sys.stderr)
        return 1
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"rapport : {Path(o.destination) / 'rapport-import.md'}")
    return 0 if r["controle_ok"] and not r["echecs_conversion"] else 2


if __name__ == "__main__":
    sys.exit(main())
