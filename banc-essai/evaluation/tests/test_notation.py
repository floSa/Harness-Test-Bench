"""Règles de comparaison (cahier des charges du corpus, section 8)."""
import notation as n


def test_texte_normalise():
    assert n.juste("site", "usine de CHOLET", "Usine de Cholet")
    assert n.juste("technicien", "Hélène  Dürr", "Helene Durr")
    assert not n.juste("machine", "Kaltis 86", "Kaltis 85")


def test_nombres_a_0_01_pres():
    assert n.juste("pression_bar", 2.5, 2.51)
    assert not n.juste("pression_bar", 2.5, 2.52)
    assert n.juste("volume_dose_ml", 1, 1.0)
    assert not n.juste("volume_dose_ml", "1.0", 1.0)
    assert not n.juste("volume_dose_ml", True, 1.0)


def test_dates_iso():
    assert n.juste("date_validation", "2025-12-03", "2025-12-03")
    assert not n.juste("date_validation", "03/12/2025", "2025-12-03")
    assert n.erreurs_valeur("date_validation", "2025-02-30")


def test_null():
    assert n.juste("tolerance_ml", None, None)
    assert not n.juste("tolerance_ml", 0.0, None)
    assert not n.juste("tolerance_ml", None, 0.5)


def test_statut():
    assert n.juste("statut", "a_revoir", "a_revoir")
    assert n.erreurs_valeur("statut", "À revoir")


def test_familles_couvrent_les_etiquettes():
    ids, _, v = n.charger_jeu(n.Path(__file__).resolve().parents[2] / "corpus" / "fourni")
    for i in ids:
        for cle in n.CLES:
            assert "autre" not in n.familles(v[i], cle), (i, cle, n.etiquettes(v[i], cle))
