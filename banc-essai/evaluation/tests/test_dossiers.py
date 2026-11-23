"""Tâche « dossiers » : notation, API (pièces servies, refus de format, score), relance dans la cage."""
import copy
import json
import shutil

import pytest

import notation_dossiers as nd
from conftest import EVAL, demarrer

DOSSIERS = EVAL.parent / "corpus" / "dossiers" / "fourni"
IDS, ATTENDUS, VERITES = nd.charger_jeu(DOSSIERS)


@pytest.fixture
def api_dossiers(tmp_path):
    s, c = demarrer("dossiers", DOSSIERS, tmp_path / "evaluation")
    yield c, tmp_path
    s.shutdown()
    s.server_close()


def note(reponses):
    n = nd.noter(reponses, ATTENDUS, VERITES)
    n.pop("detail")
    return n


def test_verite_parfaite():
    n = note(ATTENDUS)
    assert n["score"] == 1.0 and n["dossiers_parfaits"] == len(IDS)
    assert all(v["inclus_a_tort"] == 0 for v in n["pieges"].values())


def test_intervention_en_trop_et_oubliee():
    i = next(k for k in IDS if len(ATTENDUS[k]["interventions"]) >= 2)
    rep = copy.deepcopy(ATTENDUS)
    en_trop = copy.deepcopy(rep[i]["interventions"][0]) | {"reference_rapport": "XX-RI-0000-0000"}
    rep[i]["interventions"].append(en_trop)
    n = note(rep)
    total = sum(5 + 11 * len(a["interventions"]) for a in ATTENDUS.values())
    assert n["score"] == round(2 * total / (2 * total + 11), 4)
    rep = copy.deepcopy(ATTENDUS)
    rep[i]["interventions"].pop()
    n = note(rep)
    assert n["interventions"]["oubliees"] == 1 and n["dossiers_parfaits"] == len(IDS) - 1


def test_ordre_et_rectificatif():
    i = next(k for k in IDS if VERITES[k]["rectificatif"])
    rect = VERITES[i]["rectificatif"]
    piece = next(p for p in VERITES[i]["pieces"] if p["nature"] == "rectificatif")
    rep = copy.deepcopy(ATTENDUS)
    it = next(x for x in rep[i]["interventions"] if x["reference_rapport"] == rect["reference"])
    it[rect["champ"]] = piece["ancienne"]
    n = note(rep)
    assert n["rectificatifs"]["ignore"] == 1
    rep = copy.deepcopy(ATTENDUS)
    rep[i]["interventions"].reverse()
    d = nd.noter(rep, ATTENDUS, VERITES)["detail"][i]
    assert d["ordre"] is False and d["vp"] == d["attendus"] and not d["parfait"]


def test_format():
    rep = copy.deepcopy(ATTENDUS)
    i = IDS[0]
    rep[i]["interventions"][0]["volume_dose_ml"] = "12,5"
    del rep[IDS[1]]["statut_actuel"]
    err = nd.valider(rep, IDS)
    assert any("volume_dose_ml" in e for e in err) and any("statut_actuel" in e for e in err)
    assert nd.valider({**ATTENDUS, "dos-999": ATTENDUS[i]}, IDS)


def test_api_dossiers(api_dossiers):
    c, _ = api_dossiers
    code, r = c.appel("GET", "/dossiers")
    assert code == 200 and sorted(r["dossiers"]) == IDS
    i = IDS[0]
    code, pdf = c.appel("GET", f"/dossiers/{i}/{r['dossiers'][i][0]}", brut=True)
    assert code == 200 and pdf[:4] == b"%PDF"
    assert c.appel("GET", f"/dossiers/{i}/../reponses/{i}.json")[0] == 404
    assert c.appel("GET", "/documents")[0] == 404
    code, r = c.appel("POST", "/soumissions", {"reponses": {i: ATTENDUS[i]}})
    assert code == 400
    code, r = c.appel("POST", "/soumissions", {"reponses": ATTENDUS})
    assert code == 200 and r["score"] == 1.0 and r["soumissions_restantes"] == 4
    code, r = c.appel("POST", "/fin", {"soumission_finale": 1, "score_validation": 0.9,
                                       "commande": "python3 w.py {entree} {sortie}"})
    assert code == 200


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bubblewrap absent")
def test_relance_dossiers(tmp_path):
    """Workflow factice : réponse parfaite pour un dossier (lue dans ses pièces), vide pour les autres."""
    import relancer
    espace = tmp_path / "espace"
    espace.mkdir()
    i = IDS[0]
    (espace / "attendu.json").write_text(json.dumps({i: ATTENDUS[i]}))
    (espace / "w.py").write_text(
        "import json, pathlib, sys\n"
        "e, s = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])\n"
        "a = json.loads(pathlib.Path('attendu.json').read_text())\n"
        "for d in sorted(e.iterdir()):\n"
        "    assert all(p.name.startswith('piece-') for p in d.iterdir())\n"
        "    r = a.get(d.name) or {k: None for k in ['machine','constructeur','numero_serie','site','statut_actuel']}"
        " | ({} if d.name in a else {'interventions': []})\n"
        "    (s / (d.name + '.json')).write_text(json.dumps(r))\n")
    essai = tmp_path / "essai"
    r = relancer.relancer(espace, essai, "python3 w.py {entree} {sortie}", jeu=DOSSIERS, duree_max=120,
                          tache="dossiers")
    assert r["json_produits"] == len(IDS) and r["erreurs_format"] == []
    assert r["note"]["dossiers_parfaits"] == 1 and 0 < r["note"]["score"] < 1
