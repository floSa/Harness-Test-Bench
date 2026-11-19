"""Relance d'un workflow et rapport d'essai, de bout en bout, avec la fausse solution."""
import json
import sys

import notation
import rapport
import relancer
from conftest import FOURNI, ICI, demarrer

FAUX = ICI / "solutions" / "extraction_fausse"


def test_relance_et_rapport(tmp_path):
    essai = tmp_path / "essai"
    s, c = demarrer("extraction", FOURNI, essai / "evaluation")
    try:
        ids, attendus, _ = notation.charger_jeu(FOURNI)
        faux = {i: dict.fromkeys(notation.CLES) | {"statut": "conforme"} for i in ids}
        code, r = c.appel("POST", "/soumissions", {"reponses": faux})
        assert code == 200
        attendu = sum((a[k] is None) or (k == "statut" and a[k] == "conforme")
                      for a in attendus.values() for k in notation.CLES) / (len(ids) * 15)
        assert r["score"] == round(attendu, 4)
        cmd = f"{sys.executable} faux_workflow.py {{entree}} {{sortie}}"
        assert c.appel("POST", "/fin", {"soumission_finale": 1, "score_validation": 0.5, "commande": cmd})[0] == 200
    finally:
        s.shutdown()
        s.server_close()
    rl = relancer.relancer(FAUX, essai, jeu=FOURNI)
    assert rl["code_retour"] == 0 and rl["json_produits"] == len(ids) and not rl["erreurs_format"]
    assert rl["note"]["score"] == r["score"]
    assert rl["note"]["invention"]["taux"] == 0.0
    rp = rapport.construire(essai)
    assert rp["score_final"] == r["score"] and rp["meilleur_score"] == r["score"]
    assert rp["ecart_validation_test"] == round(0.5 - r["score"], 4)
    assert rp["relance"]["note"]["score"] == r["score"]
    md = rapport.markdown(rp)
    assert "Taux d'invention" in md and "Famille de pièges" in md
    assert "detail" not in json.dumps(rp)


def test_relance_sans_sortie(tmp_path):
    rl = relancer.relancer(FAUX, tmp_path, commande="true {entree} {sortie}", jeu=FOURNI)
    assert rl["json_produits"] == 0 and rl["note"]["score"] == 0.0
