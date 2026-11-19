"""Tests cachés de la tâche jouet (jamais copiés dans un espace de travail)."""
import pytest

from dosage import lire_nombre, moyenne, vers_ml


@pytest.mark.parametrize("valeur, unite, attendu", [
    (250, "µl", 0.25),
    (500, "µL", 0.5),
    (1, "ul", 0.001),
    (1500, "uL", 1.5),
])
def test_microlitres(valeur, unite, attendu):
    assert vers_ml(valeur, unite) == pytest.approx(attendu)


def test_centilitres():
    assert vers_ml(3, "cl") == pytest.approx(30)


def test_litres():
    assert vers_ml(0.75, "l") == pytest.approx(750)


def test_cm3():
    assert vers_ml(4, "cm³") == pytest.approx(4)


def test_unite_inconnue():
    with pytest.raises(ValueError):
        vers_ml(1, "gallon")


def test_lire_nombre():
    assert lire_nombre("12 345,75") == pytest.approx(12345.75)


def test_moyenne():
    assert moyenne([0.98, 1.02, 1.0]) == pytest.approx(1.0)
