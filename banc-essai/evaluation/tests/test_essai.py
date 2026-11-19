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
        cmd = "python3 faux_workflow.py {entree} {sortie}"
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


def test_relance_liens_refuses(tmp_path):
    """Un lien posé dans /sortie vers les réponses de l'hôte n'est pas suivi."""
    cmd = ("for f in {entree}/*.pdf; do i=$(basename $f .pdf); "
           f"ln -s {FOURNI}/reponses/$i.json {{sortie}}/$i.json; done; mkfifo {{sortie}}/doc-x.json")
    rl = relancer.relancer(FAUX, tmp_path, commande=cmd, jeu=FOURNI)
    ids = notation.charger_jeu(FOURNI)[0]
    assert rl["json_produits"] == 0 and rl["note"]["score"] == 0.0
    assert rl["fichiers_refuses"] == ids
    assert not any((tmp_path / "relance" / "sorties").iterdir())


def test_relance_reponse_mal_formee(tmp_path):
    """Un nombre immense dans un JSON de la relance compte faux sans faire échouer la relance."""
    cmd = ("for f in {entree}/*.pdf; do i=$(basename $f .pdf); "
           "printf '{\"volume_nominal_ml\": 1e400}' > {sortie}/$i.json; done")
    rl = relancer.relancer(FAUX, tmp_path, commande=cmd, jeu=FOURNI)
    assert rl["note"]["score"] == 0.0 and rl["erreurs_format"]
