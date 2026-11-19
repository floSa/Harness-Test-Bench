"""Plan du corpus, tiré avant tout rendu.

Pour chaque document : jeu, style, prestataire, marque, type d'équipement, langue, noms vus ou
inédits ; pour chaque champ : emplacement et pièges. Les parts visées sont tirées en nombre
exact par jeu (plus grand reste), puis réparties en équilibrant la charge des documents
(nombre de difficultés) et la répartition par style.

Usage (depuis banc-essai/corpus/) :
    uv run python plan.py            écrit plan-equilibre.md (agrégats, sans valeur ni identifiant)
"""
import random
from collections import Counter, defaultdict
from pathlib import Path

import univers
from donnees import CLES, CLES_NUMERIQUES, TYPES

GRAINE = 20261119
STYLES = ["grille", "classique", "compact", "recit", "reserve"]

# Parts visées des emplacements, par champ (en %). La première clé est l'emplacement par défaut.
EMPLACEMENTS = {
    "machine":           {"formulaire": 60, "phrase": 15, "paragraphe": 25},
    "constructeur":      {"formulaire": 55, "logo": 20, "phrase": 10, "paragraphe": 15},
    "numero_serie":      {"formulaire": 45, "plaque": 10, "phrase": 10, "paragraphe": 15, "absent": 20},
    "site":              {"formulaire": 50, "phrase": 10, "paragraphe": 20, "absent": 20},
    "reference_rapport": {"formulaire": 90, "phrase": 10},
    "date_intervention": {"formulaire": 45, "tableau": 10, "phrase": 20, "paragraphe": 25},
    "date_validation":   {"formulaire": 40, "tampon": 25, "phrase": 10, "paragraphe": 10, "absent": 15},
    "volume_dose_ml":    {"tableau": 45, "calcul": 15, "schema": 10, "phrase": 15, "paragraphe": 15},
    "volume_nominal_ml": {"tableau": 50, "formulaire": 15, "schema": 10, "phrase": 10, "paragraphe": 15},
    "tolerance_ml":      {"tableau": 55, "formulaire": 5, "phrase": 10, "paragraphe": 15, "absent": 15},
    "debit_ml_min":      {"tableau": 45, "schema": 15, "phrase": 10, "paragraphe": 15, "absent": 15},
    "pression_bar":      {"tableau": 45, "schema": 15, "phrase": 10, "paragraphe": 15, "absent": 15},
    "reference_piece":   {"tableau": 50, "phrase": 10, "paragraphe": 20, "absent": 20},
    "technicien":        {"formulaire": 45, "phrase": 15, "paragraphe": 25, "absent": 15},
    "statut":            {"formulaire": 50, "phrase": 25, "paragraphe": 25},
}
# Poids de difficulté d'un emplacement (équilibrage de la charge des documents).
POIDS = {"formulaire": 0, "tableau": 0, "phrase": 1, "paragraphe": 1.5, "schema": 1.5, "logo": 1.5,
         "plaque": 1.5, "tampon": 1.5, "calcul": 1.5, "absent": 1}
# Pièges de document (en % des documents du jeu) ; ceux qui visent une valeur numérique du
# tableau sont posés sur un champ dont l'emplacement est « tableau ».
DOCUMENT = {"scan": 20, "version_remplacee": 30, "tolerance_en_pourcent": 30,
            "redacteur_autre": 30, "conflit_regle": 10, "valeur_barree": 5, "erratum": 5}
SUR_TABLEAU = {"conflit_regle": ["debit_ml_min", "pression_bar", "volume_dose_ml"],
               "valeur_barree": ["volume_dose_ml", "debit_ml_min", "pression_bar"],
               "erratum": ["volume_dose_ml", "debit_ml_min", "pression_bar", "volume_nominal_ml"]}
# Pièges de valeur (en % des valeurs éligibles du jeu).
VALEUR = {"synonyme_cle": 30, "unite_a_convertir": 25}
AVEC_LIBELLE = {"formulaire", "tableau", "phrase", "schema"}
MAX_PIEGES = 2


def quotas(parts, n):
    """Parts (en %) -> effectifs entiers qui somment à n (plus grand reste)."""
    bruts = {k: p * n / 100 for k, p in parts.items()}
    q = {k: int(b) for k, b in bruts.items()}
    reste = n - sum(q.values())
    for k in sorted(bruts, key=lambda k: bruts[k] - q[k], reverse=True)[:reste]:
        q[k] += 1
    return q


def composition(u, r):
    """Documents sans pièges : jeu, style, prestataire, marque."""
    docs = []
    f, t, rl = u["fourni"], u["test"], u["relance"]
    # Types d'équipement répartis à parts égales dans chaque univers.
    for part in (f, t, rl):
        types = (list(TYPES) * 3)[:len(part["marques"])]
        r.shuffle(types)
        for m, typ in zip(part["marques"], types):
            m["type"] = typ
    styles_f = ["grille", "grille", "classique", "classique", "compact", "compact", "recit", "recit"]
    for p, s in zip(f["prestataires"], styles_f):
        p["style_page"] = s
    nb_f = [5, 4, 5, 4, 5, 4, 4, 4]
    marques_f = f["marques"] * 4
    r.shuffle(marques_f)
    for p, n in zip(f["prestataires"], nb_f):
        for _ in range(n):
            docs.append({"jeu": "fourni", "presta": p, "marque": marques_f.pop(), "presta_vu": True})
    # Test : 2 prestataires déjà vus (2 documents chacun), 3 nouveaux dans les styles connus
    # (2 chacun), 2 nouveaux dans le style réservé (3 et 2).
    vus = [f["prestataires"][0], f["prestataires"][5]]
    for p, s in zip(t["prestataires"], ["classique", "recit", "grille", "reserve", "reserve"]):
        p["style_page"] = s
    plan_t = [(vus[0], 2, True), (vus[1], 2, True)] + \
             [(p, 2, False) for p in t["prestataires"][:3]] + \
             [(t["prestataires"][3], 3, False), (t["prestataires"][4], 2, False)]
    marques_t = t["marques"] * 2
    r.shuffle(marques_t)
    vues_t = r.sample(f["marques"], 5)
    k = 0
    for p, n, vu in plan_t:
        for _ in range(n):
            m = vues_t.pop() if k % 3 == 2 else marques_t.pop()
            docs.append({"jeu": "test", "presta": p, "marque": m, "presta_vu": vu})
            k += 1
    for p, s, n in zip(rl["prestataires"], ["reserve", "grille", "recit", "compact"], [3, 3, 2, 2]):
        p["style_page"] = s
        for _ in range(n):
            docs.append({"jeu": "relance", "presta": p, "marque": r.choice(rl["marques"]),
                         "presta_vu": False})
    noms_fourni = {m["nom"] for m in f["marques"]}
    for d in docs:
        d["style"] = d["presta"]["style_page"]
        d["langue"] = d["presta"]["langue"]
        d["type"] = d["marque"]["type"]
        d["marque_vue"] = d["jeu"] == "fourni" or d["marque"]["nom"] in noms_fourni
        d["emplacements"] = {}
        d["pieges"] = {c: [] for c in CLES}
        d["pieges_doc"] = {}
        d["charge"] = 0.0
    return docs


def _choisir(docs, r, compte_style, cle_compte, filtre=lambda d: True):
    candidats = [d for d in docs if filtre(d)]
    if not candidats:
        return None
    return min(candidats, key=lambda d: d["charge"] + 0.8 * compte_style[(d["style"], cle_compte)]
               + r.uniform(0, 0.6))


def placer_emplacements(docs, r):
    compte_style = Counter()
    cles = list(EMPLACEMENTS)
    r.shuffle(cles)
    for cle in cles:
        parts = dict(EMPLACEMENTS[cle])
        defaut = next(iter(parts))
        q = quotas(parts, len(docs))
        jetons = [e for e, n in q.items() if e != defaut for _ in range(n)]
        jetons.sort(key=lambda e: -POIDS[e])
        libres = list(docs)
        for e in jetons:
            d = _choisir(libres, r, compte_style, (cle, e))
            libres = [x for x in libres if x is not d]  # identité : deux plans peuvent être égaux
            d["emplacements"][cle] = e
            d["charge"] += POIDS[e]
            compte_style[(d["style"], (cle, e))] += 1
        for d in libres:
            d["emplacements"][cle] = defaut


def _nb_pieges(d, cle):
    e = d["emplacements"][cle]
    return (0 if POIDS[e] == 0 else 1) + len(d["pieges"][cle])


def placer_pieges(docs, r):
    n = len(docs)
    compte_style = Counter()
    for nom, part in DOCUMENT.items():
        k = quotas({nom: part}, n)[nom]
        for _ in range(k):
            if nom in SUR_TABLEAU:
                def ok(d, nom=nom):
                    return not any(x in d["pieges_doc"] for x in SUR_TABLEAU) and any(
                        d["emplacements"][c] == "tableau" and _nb_pieges(d, c) < MAX_PIEGES
                        for c in SUR_TABLEAU[nom])
            elif nom == "tolerance_en_pourcent":
                def ok(d, nom=nom):
                    return nom not in d["pieges_doc"] and d["emplacements"]["tolerance_ml"] != "absent" \
                        and _nb_pieges(d, "tolerance_ml") < MAX_PIEGES
            elif nom == "redacteur_autre":
                def ok(d, nom=nom):
                    return nom not in d["pieges_doc"] and d["emplacements"]["technicien"] != "absent"
            else:
                def ok(d, nom=nom):
                    return nom not in d["pieges_doc"]
            d = _choisir(docs, r, compte_style, nom, ok)
            if d is None:
                raise RuntimeError(f"{nom} : plus de document compatible")
            if nom in SUR_TABLEAU:
                cle = r.choice([c for c in SUR_TABLEAU[nom] if d["emplacements"][c] == "tableau"
                                and _nb_pieges(d, c) < MAX_PIEGES])
                d["pieges"][cle].append(nom)
                d["pieges_doc"][nom] = cle
            elif nom == "tolerance_en_pourcent":
                d["pieges"]["tolerance_ml"].append(nom)
                d["pieges_doc"][nom] = True
            else:
                d["pieges_doc"][nom] = True
            d["charge"] += 1
            compte_style[(d["style"], nom)] += 1
    # Pièges de valeur.
    for nom, part in VALEUR.items():
        if nom == "synonyme_cle":
            elig = [(d, c) for d in docs for c in CLES if d["emplacements"][c] in AVEC_LIBELLE]
        else:
            elig = [(d, c) for d in docs for c in CLES_NUMERIQUES
                    if d["emplacements"][c] != "absent" and "tolerance_en_pourcent" not in d["pieges"][c]]
        k = quotas({nom: part}, len(elig))[nom]
        elig = [(d, c) for d, c in elig if _nb_pieges(d, c) < MAX_PIEGES]
        if len(elig) < k:
            raise RuntimeError(f"{nom} : {len(elig)} candidats pour {k}")
        elig.sort(key=lambda dc: dc[0]["charge"] + r.uniform(0, 1.5))
        for d, c in elig[:k]:
            d["pieges"][c].append(nom)
            d["charge"] += 1


def planifier(graine=GRAINE):
    u = univers.construire(graine)
    r = random.Random(f"{graine}/plan")
    docs = composition(u, r)
    for jeu in ["fourni", "test", "relance"]:
        sous = [d for d in docs if d["jeu"] == jeu]
        placer_emplacements(sous, r)
        placer_pieges(sous, r)
    ordre = list(range(len(docs)))
    r.shuffle(ordre)
    for num, i in enumerate(ordre, start=1):
        docs[i]["id"] = f"doc-{num:03d}"
    docs.sort(key=lambda d: d["id"])
    return docs, u


# Rapport d'équilibre -----------------------------------------------------------------------

JEUX = ["fourni", "test", "relance"]


def _pct(a, b):
    return f"{a} ({100 * a / b:.0f} %)" if b else "0"


def rapport(docs):
    par_jeu = {j: [d for d in docs if d["jeu"] == j] for j in JEUX}
    L = ["# Équilibre du plan du corpus", "",
         "Généré par `plan.py` (graine fixe). Agrégats seulement : aucune valeur, aucun "
         "identifiant de document du test caché ni de la relance.", "",
         "## Composition", "",
         "| Critère | " + " | ".join(JEUX) + " |", "|---|" + "---|" * len(JEUX)]
    lig = lambda nom, f: L.append(f"| {nom} | " + " | ".join(str(f(par_jeu[j])) for j in JEUX) + " |")
    lig("Documents", len)
    for s in STYLES:
        lig(f"Style {s}", lambda ds, s=s: sum(d["style"] == s for d in ds))
    lig("Langue fr", lambda ds: sum(d["langue"] == "fr" for d in ds))
    lig("Langue en", lambda ds: sum(d["langue"] == "en" for d in ds))
    lig("Prestataires distincts", lambda ds: len({d["presta"]["nom"] for d in ds}))
    lig("Documents d'un prestataire vu", lambda ds: sum(d["presta_vu"] for d in ds))
    lig("Documents d'une marque vue", lambda ds: sum(d["marque_vue"] for d in ds))
    for t in TYPES:
        lig(f"Type {t}", lambda ds, t=t: sum(d["type"] == t for d in ds))

    L += ["", "## Emplacements par champ (tous jeux)", "",
          "Effectifs sur 60 documents. Case vide : emplacement non prévu pour ce champ.", ""]
    tous = ["formulaire", "tableau", "phrase", "paragraphe", "schema", "logo", "plaque", "tampon",
            "calcul", "absent"]
    L += ["| Champ | " + " | ".join(tous) + " |", "|---|" + "---|" * len(tous)]
    for cle in CLES:
        c = Counter(d["emplacements"][cle] for d in docs)
        L.append(f"| `{cle}` | " + " | ".join(str(c[e]) if e in EMPLACEMENTS[cle] else ""
                                                for e in tous) + " |")
    L += ["", "## Emplacements par jeu (toutes valeurs)", "",
          "| Emplacement | " + " | ".join(JEUX) + " |", "|---|" + "---|" * len(JEUX)]
    for e in tous:
        L.append(f"| {e} | " + " | ".join(
            _pct(sum(d["emplacements"][c] == e for d in par_jeu[j] for c in CLES),
                 len(par_jeu[j]) * len(CLES)) for j in JEUX) + " |")

    L += ["", "## Pièges par jeu", "", "| Piège | Part visée | " + " | ".join(JEUX) + " |",
          "|---|---|" + "---|" * len(JEUX)]
    for nom, part in DOCUMENT.items():
        L.append(f"| {nom} | {part} % des documents | " + " | ".join(
            _pct(sum(nom in d["pieges_doc"] for d in par_jeu[j]), len(par_jeu[j])) for j in JEUX) + " |")
    for nom, part in VALEUR.items():
        L.append(f"| {nom} | {part} % des valeurs éligibles | " + " | ".join(
            str(sum(nom in d["pieges"][c] for d in par_jeu[j] for c in CLES)) for j in JEUX) + " |")

    L += ["", "## Répartition par style (jeu fourni et test)", "",
          "| Critère | " + " | ".join(STYLES) + " |", "|---|" + "---|" * len(STYLES)]
    ft = [d for d in docs if d["jeu"] != "relance"]
    par_style = {s: [d for d in ft if d["style"] == s] for s in STYLES}
    L.append("| Documents | " + " | ".join(str(len(par_style[s])) for s in STYLES) + " |")
    for e in ["phrase", "paragraphe", "schema", "absent", "calcul", "tampon", "logo"]:
        L.append(f"| Valeurs en {e} (moyenne par document) | " + " | ".join(
            f"{sum(d['emplacements'][c] == e for d in par_style[s] for c in CLES) / max(1, len(par_style[s])):.1f}".replace(".", ",")
            for s in STYLES) + " |")
    for nom in ["scan", "version_remplacee", "conflit_regle", "valeur_barree", "erratum"]:
        L.append(f"| {nom} | " + " | ".join(str(sum(nom in d["pieges_doc"] for d in par_style[s]))
                                            for s in STYLES) + " |")

    L += ["", "## Charge des documents", "",
          "Charge : somme des difficultés d'un document (emplacement hors défaut : 1 à 1,5 ; "
          "piège : 1).", "", "| Critère | " + " | ".join(JEUX) + " |", "|---|" + "---|" * len(JEUX)]
    for nom, f in [("Minimum", min), ("Moyenne", lambda x: sum(x) / len(x)), ("Maximum", max)]:
        L.append(f"| {nom} | " + " | ".join(f"{f([d['charge'] for d in par_jeu[j]]):.1f}".replace(".", ",")
                                            for j in JEUX) + " |")
    L.append(f"| Pièges par valeur, maximum | " + " | ".join(
        str(max(_nb_pieges(d, c) for d in par_jeu[j] for c in CLES if d["emplacements"][c] != "absent"))
        for j in JEUX) + " |")
    return "\n".join(L) + "\n"


def controler(docs):
    """Contraintes du plan ; renvoie la liste des écarts."""
    ecarts = []
    for j in JEUX:
        ds = [d for d in docs if d["jeu"] == j]
        for cle, parts in EMPLACEMENTS.items():
            attendu = quotas(parts, len(ds))
            obtenu = Counter(d["emplacements"][cle] for d in ds)
            if any(obtenu[e] != n for e, n in attendu.items()):
                ecarts.append(f"{j} {cle} : {dict(obtenu)} au lieu de {attendu}")
        for nom, part in DOCUMENT.items():
            if sum(nom in d["pieges_doc"] for d in ds) != quotas({nom: part}, len(ds))[nom]:
                ecarts.append(f"{j} {nom} : part non atteinte")
        for d in ds:
            for c in CLES:
                if d["emplacements"][c] != "absent" and _nb_pieges(d, c) > MAX_PIEGES:
                    ecarts.append(f"{d['id']} {c} : plus de {MAX_PIEGES} pièges")
                if d["emplacements"][c] == "absent" and d["pieges"][c]:
                    ecarts.append(f"{d['id']} {c} : piège sur un champ absent")
    return ecarts


if __name__ == "__main__":
    docs, _ = planifier()
    ecarts = controler(docs)
    sortie = Path(__file__).resolve().parent / "plan-equilibre.md"
    sortie.write_text(rapport(docs), encoding="utf-8")
    print(f"{len(docs)} documents planifiés ; {len(ecarts)} écart(s) ; rapport : {sortie.name}")
    for e in ecarts:
        print("  ", e)
