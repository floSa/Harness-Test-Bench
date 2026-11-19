import pytest

from dosage import lire_nombre, moyenne, vers_ml


def test_millilitres():
    assert vers_ml(12.5, "ml") == pytest.approx(12.5)


def test_centilitres():
    assert vers_ml(2, "cl") == pytest.approx(20)


def test_litres():
    assert vers_ml(1.2, "L") == pytest.approx(1200)


def test_lire_nombre():
    assert lire_nombre("1 250,5") == pytest.approx(1250.5)


def test_moyenne():
    assert moyenne([1.0, 2.0, 3.0]) == pytest.approx(2.0)
