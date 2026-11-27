"""Tâche « goldset » : notation générique, import d'un goldset (formes de vérité, contrôles), API, relance."""
import copy
import json
import shutil
import sys

import pytest

import notation_goldset as ng
from conftest import EVAL, demarrer

sys.path.insert(0, str(EVAL.parent / "corpus"))
import importer_goldset as ig  # noqa: E402

SCHEMA = {"version": 1, "valide": True, "description": "essai", "champs": {
    "client.nom": {"type": "texte"}, "client.ville": {"type": "texte"},
    "montant": {"type": "nombre", "tolerance": 0.5}, "date": {"type": "date"},
    "signe": {"type": "booleen"}, "etat": {"type": "enum", "valeurs": ["ouvert", "clos"]},
    "lignes": {"type": "liste"}}}
ATT = {"client": {"nom": "Société Générale", "ville": None}, "montant": 1250.0, "date": "2026-03-01",
       "signe": True, "etat": "clos", "lignes": ["A1", "B2", "C3", "D4"]}


def test_notation_regles():
    assert ng.noter({"d": ATT}, {"d": ATT}, SCHEMA)["score"] == 1.0
    r = copy.deepcopy(ATT)
    r["client"]["nom"] = "  societe   GENERALE "       # normalisation : juste
    r["montant"] = 1250.4                              # dans la tolérance : juste
    r["lignes"] = ["D4", "C3", "A1", "Z9"]             # ordre libre, 3 sur 4 : F1 = 0,75
    n = ng.noter({"d": r}, {"d": ATT}, SCHEMA)
    assert n["par"]["cle"]["lignes"]["score"] == 0.75
    assert n["score"] == round((6 + 0.75) / 7, 4) and n["documents_parfaits"] == 0
    r["client"]["ville"] = "Paris"                     # valeur inventée là où null est attendu
    n = ng.noter({"d": r}, {"d": ATT}, SCHEMA)
    assert n["invention"]["inventes"] == 1 and n["par"]["cle"]["client.ville"]["score"] == 0.0
    r = copy.deepcopy(ATT) | {"montant": None}
    assert ng.noter({"d": r}, {"d": ATT}, SCHEMA)["omission"]["omises"] == 1


def test_format():
    r = copy.deepcopy(ATT) | {"montant": "1250", "date": "01/03/2026", "etat": "fermé"}
    del r["signe"]
    err = ng.valider({"d": r}, ["d"], SCHEMA)
    for attendu in ("montant", "date", "etat", "signe"):
        assert any(attendu in e for e in err), attendu
    assert ng.noter({"d": r}, {"d": ATT}, SCHEMA)["score"] == 0.0   # document mal formé : 0
    assert ng.valider({"d": ATT, "x": ATT}, ["d"], SCHEMA)


def pdf(chemin, contenu):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(b"%PDF-1.4\n" + contenu.encode() + b"\n%%EOF\n")


def goldset(tmp, forme="objet"):
    """Petit goldset : 4 documents par jeu, valeurs sous forme brute (dates JJ/MM, nombres en texte)."""
    src = tmp / "goldset"
    globale = {}
    for j in ig.JEUX_SOURCE:
        verite = {}
        for k in range(4):
            nom = f"{j}_{k}.pdf"
            pdf(src / "split" / j / nom, nom)
            verite[nom] = {"client": {"nom": f"Client {j} {k}", "ville": None if k == 0 else "Lyon"},
                           "montant": f"1 2{k}0,5", "date": f"1{k}/0{k + 1}/2026", "signe": "oui" if k % 2 else "non",
                           "etat": ["ouvert", "clos"][k % 2], "lignes": [f"L{k}", "X"]}
        globale |= verite
        if forme == "liste":
            contenu = {"documents": [{"filename": n} | v for n, v in verite.items()]}
        elif forme == "enveloppe":
            contenu = {n.removesuffix(".pdf"): {"fields": v} for n, v in verite.items()}
        else:
            contenu = verite
        (src / "split" / f"{j}_ground_truth.json").write_text(json.dumps(contenu, ensure_ascii=False))
    (src / "ground_truth.json").write_text(json.dumps(globale, ensure_ascii=False))
    return src


@pytest.mark.parametrize("forme", ["objet", "liste", "enveloppe"])
def test_import_formes(tmp_path, forme):
    src = goldset(tmp_path, forme)
    dest = tmp_path / "import"
    r = ig.importer(src, dest, verifier_git=False)
    assert r["documents"] == {"fourni": 4, "test-cache": 4, "relance": 4}
    assert r["controle_ok"] and r["echecs_conversion"] == 0
    s = json.loads((dest / "schema.json").read_text())
    types = {k: v["type"] for k, v in s["champs"].items()}
    assert types == {"client.nom": "texte", "client.ville": "texte", "montant": "nombre", "date": "date",
                     "signe": "texte", "etat": "texte", "lignes": "liste"}
    assert s["valide"] is False
    corr = json.loads((dest / "correspondance.json").read_text())
    i, c = next((i, c) for i, c in corr.items() if c["fichier"] == "train_1.pdf")
    rep = json.loads((dest / c["jeu_banc"] / "reponses" / f"{i}.json").read_text())
    assert rep["montant"] == 1210.5 and rep["date"] == "2026-02-11" and rep["client"]["ville"] == "Lyon"
    assert (dest / "fourni" / f"{i}.pdf").read_bytes().startswith(b"%PDF")
    assert "train_1" not in json.dumps(sorted(p.name for p in (dest / "fourni").iterdir()))


def test_import_schema_valide_et_booleens(tmp_path):
    src = goldset(tmp_path)
    dest = tmp_path / "import"
    ig.importer(src, dest, verifier_git=False)
    s = json.loads((dest / "schema.json").read_text())
    s["champs"]["signe"] = {"type": "booleen"}
    s["champs"]["etat"] = {"type": "enum", "valeurs": ["ouvert", "clos"]}
    s["valide"] = True
    (dest / "schema.json").write_text(json.dumps(s))
    r = ig.importer(src, dest, verifier_git=False)       # le schéma validé sert à la conversion
    assert r["schema"] == "existant, validé" and r["controle_ok"]
    rep = json.loads(next((dest / "fourni" / "reponses").iterdir()).read_text())
    assert isinstance(rep["signe"], bool)


def test_import_controles(tmp_path):
    src = goldset(tmp_path)
    shutil.copy2(src / "split" / "train" / "train_0.pdf", src / "split" / "test" / "copie.pdf")
    (src / "split" / "val" / "val_9.pdf").write_bytes(b"%PDF-1.4 orphelin")
    v = json.loads((src / "split" / "test_ground_truth.json").read_text())
    v["copie.pdf"] = v["test_0.pdf"]
    (src / "split" / "test_ground_truth.json").write_text(json.dumps(v))
    with pytest.raises(ig.ImportArrete, match="même contenu"):
        ig.importer(src, tmp_path / "import", verifier_git=False)
    with pytest.raises(ig.ImportArrete, match="ignoré par git"):
        ig.importer(src, tmp_path / "import")             # destination hors dépôt : non ignorée
    (src / "split" / "test" / "copie.pdf").unlink()
    r = ig.importer(src, tmp_path / "import", verifier_git=False)
    texte = (tmp_path / "import" / "rapport-import.md").read_text()
    assert "PDF sans vérité, écarté : val_9.pdf" in texte and "vérité sans PDF, écartée : copie.pdf" in texte
    assert r["documents"]["test-cache"] == 4


def test_import_forme_inconnue(tmp_path):
    src = goldset(tmp_path)
    (src / "split" / "val_ground_truth.json").write_text(json.dumps([{"x": 1}, {"x": 2}]))
    with pytest.raises(ig.ImportArrete, match="lire_verite"):
        ig.importer(src, tmp_path / "import", verifier_git=False)


@pytest.fixture
def jeu_goldset(tmp_path):
    src = goldset(tmp_path)
    dest = tmp_path / "import"
    ig.importer(src, dest, verifier_git=False)
    s = json.loads((dest / "schema.json").read_text()) | {"valide": True}
    (dest / "schema.json").write_text(json.dumps(s))
    return dest


def test_api_goldset(jeu_goldset, tmp_path):
    s, c = demarrer("goldset", jeu_goldset / "test-cache", tmp_path / "evaluation")
    try:
        code, r = c.appel("GET", "/documents")
        assert code == 200 and len(r["documents"]) == 4
        code, octets = c.appel("GET", f"/documents/{r['documents'][0]}.pdf", brut=True)
        assert code == 200 and octets.startswith(b"%PDF")
        ids, att, _ = ng.charger_jeu(jeu_goldset / "test-cache")
        mauvais = copy.deepcopy(att)
        mauvais[ids[0]]["montant"] = "12"
        assert c.appel("POST", "/soumissions", {"reponses": mauvais})[0] == 400
        code, r = c.appel("POST", "/soumissions", {"reponses": att})
        assert code == 200 and r["score"] == 1.0 and r["soumissions_restantes"] == 4
    finally:
        s.shutdown()
        s.server_close()


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bubblewrap absent")
def test_relance_goldset(jeu_goldset, tmp_path):
    """Workflow factice dans la cage : réponse juste pour un document, null partout pour les autres."""
    import relancer
    espace = tmp_path / "espace"
    espace.mkdir()
    ids, att, schema = ng.charger_jeu(jeu_goldset / "relance")
    (espace / "attendu.json").write_text(json.dumps({ids[0]: att[ids[0]]}))
    vide = ng.deplier({k: None for k in schema["champs"]})
    (espace / "w.py").write_text(
        "import json, pathlib, sys\n"
        "e, s = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])\n"
        "a = json.loads(pathlib.Path('attendu.json').read_text())\n"
        f"vide = {vide!r}\n"
        "for p in sorted(e.glob('*.pdf')):\n"
        "    (s / (p.stem + '.json')).write_text(json.dumps(a.get(p.stem, vide)))\n")
    r = relancer.relancer(espace, tmp_path / "essai", "python3 w.py {entree} {sortie}",
                          jeu=jeu_goldset / "relance", duree_max=120, tache="goldset")
    assert r["json_produits"] == 4 and r["erreurs_format"] == []
    assert r["note"]["documents_parfaits"] == 1 and 0 < r["note"]["score"] < 1
