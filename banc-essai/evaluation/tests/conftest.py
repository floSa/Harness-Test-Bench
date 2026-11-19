import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ICI = Path(__file__).resolve().parent
EVAL = ICI.parent
sys.path.insert(0, str(EVAL))

import api  # noqa: E402

FOURNI = EVAL.parent / "corpus" / "fourni"
JOUET = EVAL / "taches" / "jouet"


class Client:
    def __init__(self, port):
        self.base = f"http://127.0.0.1:{port}"

    def appel(self, methode, chemin, corps=None, brut=False):
        data = None if corps is None else json.dumps(corps).encode()
        req = urllib.request.Request(self.base + chemin, data=data, method=methode,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                c = r.read()
                return r.status, c if brut else json.loads(c)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")


def demarrer(tache, jeu, sortie):
    s = api.serveur(api.Etat(tache, jeu, sortie), 0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, Client(s.server_port)


@pytest.fixture
def extraction(tmp_path):
    s, c = demarrer("extraction", FOURNI, tmp_path / "evaluation")
    yield c, tmp_path
    s.shutdown()
    s.server_close()


@pytest.fixture
def toy(tmp_path):
    s, c = demarrer("jouet", JOUET, tmp_path / "evaluation")
    yield c, tmp_path
    s.shutdown()
    s.server_close()
