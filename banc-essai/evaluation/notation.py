"""Notation des réponses d'extraction contre la vérité terrain du corpus.

Règles (cahier des charges du corpus, section 8) :
- texte : égal après normalisation (casse, espaces, accents) ;
- nombre : égal à 0,01 près dans l'unité de la clé ;
- date : égale au format ISO ;
- `null` attendu : juste seulement si la réponse est `null`.
"""
import datetime
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

CLES = ["machine", "constructeur", "numero_serie", "site", "reference_rapport", "date_intervention",
        "date_validation", "volume_dose_ml", "volume_nominal_ml", "tolerance_ml", "debit_ml_min",
        "pression_bar", "reference_piece", "technicien", "statut"]
NOMBRES = {"volume_dose_ml", "volume_nominal_ml", "tolerance_ml", "debit_ml_min", "pression_bar"}
DATES = {"date_intervention", "date_validation"}
STATUTS = {"conforme", "non_conforme", "a_revoir"}
TOLERANCE = 0.01 + 1e-9

# Familles de pièges (cahier des charges, section 6).
FAMILLES = {
    "absent": "absence",
    "valeur_barree": "doublons", "erratum": "doublons", "conflit_regle": "doublons",
    "version_remplacee": "doublons",
    "moyenne_a_calculer": "calcul", "tolerance_en_pourcent": "calcul", "unite_a_convertir": "calcul",
    "synonyme_cle": "forme", "redacteur_autre": "forme", "format_nombre": "forme",
    "zones_ambigues": "systematique", "dates_multiples": "systematique", "personnes_multiples": "systematique",
    "volumes_voisins": "systematique", "tableau_multi_entrees": "systematique", "tableau_coupe": "systematique",
    "scan": "lecture_visuelle", "cases_a_cocher": "lecture_visuelle",
}
# Pièges de document qui portent sur un seul champ.
PIEGES_DOC_CHAMP = {"redacteur_autre": "technicien", "version_remplacee": "reference_rapport"}
# Emplacements qui comptent comme difficulté (hors formulaire et tableau).
EMPLACEMENTS_DIFFICILES = {"phrase", "paragraphe", "schema", "logo", "plaque", "tampon", "calcul"}


# Valeur absolue maximale d'un nombre (au-delà : refus de format, ni infini ni entier géant).
NOMBRE_MAX = 1e9


# Format ------------------------------------------------------------------------------------------

def erreurs_valeur(cle, v):
    """Liste des erreurs de format d'une valeur (vide si la valeur est acceptable)."""
    if v is None:
        return []
    if cle in NOMBRES:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
            return [f"{cle} : nombre ou null attendu, reçu {json.dumps(v, ensure_ascii=False)[:80]}"]
        if not -NOMBRE_MAX <= v <= NOMBRE_MAX:
            return [f"{cle} : nombre hors limites (au plus {NOMBRE_MAX:g} en valeur absolue)"]
        return []
    if not isinstance(v, str):
        return [f"{cle} : texte ou null attendu, reçu {json.dumps(v, ensure_ascii=False)}"]
    if not v.strip():
        return [f"{cle} : texte vide (utiliser null pour une valeur absente)"]
    if cle in DATES:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return [f"{cle} : date au format AAAA-MM-JJ attendue, reçu « {v} »"]
        try:
            datetime.date.fromisoformat(v)
        except ValueError:
            return [f"{cle} : date impossible « {v} »"]
    if cle == "statut" and v not in STATUTS:
        return [f"statut : une de {sorted(STATUTS)} ou null attendue, reçu « {v} »"]
    return []


def valider(reponses, ids):
    """Erreurs de format d'une soumission : un objet par document attendu, exactement les 15 clés."""
    if not isinstance(reponses, dict):
        return ["les réponses doivent être un objet {identifiant: {clé: valeur}}"]
    err = []
    manquants = sorted(set(ids) - set(reponses))
    inconnus = sorted(set(reponses) - set(ids))
    if manquants:
        err.append(f"documents manquants : {', '.join(manquants)}")
    if inconnus:
        err.append(f"documents inconnus : {', '.join(inconnus)}")
    for i in sorted(set(ids) & set(reponses)):
        r = reponses[i]
        if not isinstance(r, dict):
            err.append(f"{i} : objet JSON attendu")
            continue
        if set(r) != set(CLES):
            manq, trop = sorted(set(CLES) - set(r)), sorted(set(r) - set(CLES))
            err.append(f"{i} : clés manquantes {manq}, clés en trop {trop}")
        for cle in CLES:
            err += [f"{i} : {e}" for e in erreurs_valeur(cle, r.get(cle))]
    return err


# Comparaison -------------------------------------------------------------------------------------

def normaliser_texte(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.casefold().split())


def juste(cle, reponse, attendu):
    """Vrai si la réponse est juste. Une valeur au mauvais format est fausse."""
    if attendu is None:
        return reponse is None
    if reponse is None or erreurs_valeur(cle, reponse):
        return False
    if cle in NOMBRES:
        return abs(float(reponse) - float(attendu)) <= TOLERANCE
    if cle in DATES or cle == "statut":
        return reponse.strip() == attendu
    return normaliser_texte(reponse) == normaliser_texte(attendu)


# Vérité --------------------------------------------------------------------------------------------

def charger_jeu(dossier):
    """Identifiants (triés), réponses attendues et vérités d'un jeu du corpus."""
    d = Path(dossier)
    ids = sorted(p.stem for p in d.glob("doc-*.pdf"))
    attendus = {i: json.loads((d / "reponses" / f"{i}.json").read_text()) for i in ids}
    verites = {i: json.loads((d / "verite" / f"{i}.json").read_text()) for i in ids}
    return ids, attendus, verites


def etiquettes(verite, cle):
    """Étiquettes de difficulté d'un champ : pièges, absence, page scannée, pièges de document."""
    ch = verite["champs"][cle]
    e = set(ch["pieges"])
    if ch["valeur"] is None:
        e.add("absent")
    if ch.get("scan"):
        e.add("scan")
    for piege, champ in PIEGES_DOC_CHAMP.items():
        if champ == cle and piege in verite["pieges_document"]:
            e.add(piege)
    return e


def familles(verite, cle):
    f = {FAMILLES.get(e, "autre") for e in etiquettes(verite, cle)}
    if verite["champs"][cle]["emplacement"] in EMPLACEMENTS_DIFFICILES:
        f.add("emplacement")
    return f


# Notation ------------------------------------------------------------------------------------------

def _score(c):
    return {"n": c[0], "justes": c[1], "score": round(c[1] / c[0], 4) if c[0] else None}


def noter(reponses, attendus, verites):
    """Note des réponses (document sans réponse : tous ses champs faux ; valeur mal formée : fausse).

    Renvoie le score global (exactitude par champ) et les scores détaillés par clé, étiquette,
    famille de pièges, emplacement, style, prestataire, langue, nom vu ou inédit ; le taux
    d'invention ; et le détail par document (à ne pas diffuser : il révèle la vérité).
    """
    groupes = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    total = [0, 0]
    attendus_null, inventes = 0, 0
    detail = {}
    for i, att in attendus.items():
        v = verites[i]
        r = reponses.get(i) if isinstance(reponses, dict) else None
        present = isinstance(r, dict)
        detail[i] = {}
        for cle in CLES:
            rep = r.get(cle) if present else None
            ok = present and juste(cle, rep, att[cle])
            detail[i][cle] = ok
            total[0] += 1
            total[1] += ok
            if att[cle] is None:
                attendus_null += 1
                inventes += rep is not None
            cles_groupes = [("cle", cle), ("style", v["style"]), ("prestataire", v["prestataire"]),
                            ("langue", v["langue"]),
                            ("prestataire_vu", "vu" if v["prestataire_vu"] else "inedit"),
                            ("marque_vue", "vue" if v["marque_vue"] else "inedite"),
                            ("emplacement", v["champs"][cle]["emplacement"])]
            cles_groupes += [("etiquette", e) for e in etiquettes(v, cle)]
            cles_groupes += [("famille", f) for f in familles(v, cle)]
            for g, k in cles_groupes:
                groupes[g][k][0] += 1
                groupes[g][k][1] += ok
    return {
        "documents": len(attendus),
        "champs": total[0],
        "justes": total[1],
        "score": round(total[1] / total[0], 4) if total[0] else 0.0,
        "invention": {"null_attendus": attendus_null, "inventes": inventes,
                      "taux": round(inventes / attendus_null, 4) if attendus_null else None},
        "par": {g: {k: _score(c) for k, c in sorted(d.items())} for g, d in sorted(groupes.items())},
        "detail": detail,
    }
