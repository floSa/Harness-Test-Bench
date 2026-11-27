"""Écrit les consignes données aux harnais pour un goldset importé, à partir de son schéma validé.

    python3 banc-essai/corpus/consignes_goldset.py [--goldset banc-essai/corpus/goldset]

Lit `<goldset>/schema.json` (« valide »: true exigé), compte les documents des jeux fourni,
test-cache et relance, et remplit banc-essai/recettes/goldset/consignes.modele.md :
description des documents, tableau des champs (chemin, type, définition), structure de la réponse,
règles de notation propres au schéma, carte graphique de la machine, vision du modèle
(banc-essai/modele.env). Résultat : `<goldset>/recette/consignes.md` (hors git, comme le goldset),
copié dans l'espace de chaque essai par banc-essai/evaluation/preparer.py. Bibliothèque standard seulement.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
BANC = ICI.parent
sys.path.insert(0, str(BANC / "evaluation"))
sys.path.insert(0, str(BANC / "traces"))
import notation_goldset as ng  # noqa: E402
from generer_config import lire_modele  # noqa: E402

LIBELLES = {"texte": "texte", "nombre": "nombre", "date": "date (AAAA-MM-JJ)", "booleen": "booléen",
            "liste": "liste", "enum": "une valeur de la liste"}


def virgule(x):
    return f"{x:g}".replace(".", ",")


def gpu():
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=20)
        if r.returncode == 0 and r.stdout.strip():
            nom, mem = r.stdout.strip().splitlines()[0].rsplit(",", 1)
            return f"{nom.strip()} (CUDA) : {mem.strip()} de mémoire"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "aucune"


def tableau(schema):
    L = ["| Champ | Type | Définition |", "|---|---|---|"]
    for chemin, d in schema["champs"].items():
        t = LIBELLES[d["type"]]
        if d["type"] == "enum":
            t += " : " + ", ".join(f"`{v}`" for v in d["valeurs"])
        if d["type"] == "nombre" and d.get("tolerance") is not None:
            t += f" (tolérance {virgule(d['tolerance'])})"
        L.append(f"| `{chemin}` | {t} | {d.get('description') or ''} |")
    return "\n".join(L)


def regles(schema):
    types = {d["type"] for d in schema["champs"].values()}
    r = []
    if types & {"texte", "enum"}:
        r.append("texte égal après normalisation de la casse, des espaces et des accents")
    if "nombre" in types:
        tol = sorted({d.get("tolerance", ng.TOLERANCE) for d in schema["champs"].values() if d["type"] == "nombre"})
        r.append("nombre égal à la tolérance du champ près" if len(tol) > 1 else f"nombre égal à {virgule(tol[0])} près")
    if "date" in types:
        r.append("date égale")
    if "booleen" in types:
        r.append("booléen égal")
    if "liste" in types:
        r.append("liste comparée sans ordre, avec un crédit partiel (F1 entre éléments répondus et attendus)")
    return " ; ".join(r) + "."


def structure(schema):
    imbriques = sorted({c.split(ng.SEPARATEUR)[0] for c in schema["champs"] if ng.SEPARATEUR in c})
    if not imbriques:
        return "un objet JSON dont les clés sont les champs ci-dessus."
    return ("un objet JSON ; un champ écrit `a.b` est la clé `b` de l'objet `a` "
            f"(objets imbriqués : {', '.join(f'`{x}`' for x in imbriques)}).")


def generer(goldset):
    g = Path(goldset)
    schema = ng.charger_schema(g / "schema.json")
    if not schema.get("valide"):
        raise SystemExit(f"{g / 'schema.json'} n'est pas validé (« valide »: false) : le relire, puis mettre true")
    manquent = [c for c, d in schema["champs"].items() if not (d.get("description") or "").strip()]
    if manquent:
        print(f"attention : champs sans description : {', '.join(manquent[:15])}", file=sys.stderr)
    n = {j: len(list((g / j).glob("doc-*.pdf"))) for j in ("fourni", "test-cache", "relance")}
    exemple = sorted(p.stem for p in (g / "fourni").glob("doc-*.pdf"))[0]
    vision = lire_modele().get("BANC_VISION") == "1"
    remplacements = {
        "{DESCRIPTION}": schema.get("description") or "documents PDF.",
        "{N_FOURNI}": str(n["fourni"]), "{N_TEST}": str(n["test-cache"]),
        "{TABLEAU_CLES}": tableau(schema), "{STRUCTURE}": structure(schema), "{REGLES}": regles(schema),
        "{EXEMPLE_ID}": exemple, "{GPU}": gpu(),
        "{VISION}": ("Le modèle accepte des images (messages avec `image_url`)." if vision else
                     "Le modèle ne lit pas les images : texte seulement."),
    }
    texte = (BANC / "recettes" / "goldset" / "consignes.modele.md").read_text()
    for k, v in remplacements.items():
        texte = texte.replace(k, v)
    (g / "recette").mkdir(exist_ok=True)
    (g / "recette" / "consignes.md").write_text(texte)
    return g / "recette" / "consignes.md", n


def main():
    a = argparse.ArgumentParser(description="Consignes d'un goldset importé")
    a.add_argument("--goldset", default=str(ICI / "goldset"))
    o = a.parse_args()
    f, n = generer(o.goldset)
    print(f"consignes écrites : {f} (fourni {n['fourni']}, test caché {n['test-cache']}, relance {n['relance']})")


if __name__ == "__main__":
    main()
