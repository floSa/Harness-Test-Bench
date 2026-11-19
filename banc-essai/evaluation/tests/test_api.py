"""Tests de l'API : documents, refus de format, notation sur réponses connues, limite de 5, fin."""
import copy
import json

import api
import notation
from conftest import FOURNI, JOUET, demarrer

IDS, ATTENDUS, VERITES = notation.charger_jeu(FOURNI)
N = len(IDS) * len(notation.CLES)


def soumettre(c, reponses):
    return c.appel("POST", "/soumissions", {"reponses": reponses})


def faux_juste(cle, v):
    """Valeur fausse mais bien formée."""
    if v is None:
        return 1.0 if cle in notation.NOMBRES else ("2000-01-01" if cle in notation.DATES else
                                                     "conforme" if cle == "statut" else "invention")
    if cle in notation.NOMBRES:
        return v + 0.02
    if cle in notation.DATES:
        return "1999-12-31"
    if cle == "statut":
        return "a_revoir" if v != "a_revoir" else "conforme"
    return v + " X"


# Documents -----------------------------------------------------------------------------------------

def test_etat_initial(extraction):
    c, _ = extraction
    code, e = c.appel("GET", "/etat")
    assert code == 200
    assert e == {"tache": "extraction", "limite": 5, "soumissions_utilisees": 0, "soumissions_restantes": 5,
                 "fin_declaree": False, "documents": 35}


def test_documents_sans_reponses(extraction):
    c, _ = extraction
    code, r = c.appel("GET", "/documents")
    assert code == 200 and r["documents"] == IDS
    code, pdf = c.appel("GET", f"/documents/{IDS[0]}.pdf", brut=True)
    assert code == 200 and pdf == (FOURNI / f"{IDS[0]}.pdf").read_bytes()
    for chemin in ["/documents/doc-999.pdf", "/documents/../reponses/doc-001.json.pdf",
                   f"/reponses/{IDS[0]}.json", f"/verite/{IDS[0]}.json", "/documents/%2e%2e%2fverite.pdf"]:
        assert c.appel("GET", chemin)[0] == 404


# Format --------------------------------------------------------------------------------------------

def test_refus_de_format_sans_decompte(extraction):
    c, tmp = extraction
    mauvais = []
    r = copy.deepcopy(ATTENDUS)
    del r[IDS[0]]
    mauvais.append(r)                                        # document manquant
    r = copy.deepcopy(ATTENDUS)
    r["doc-999"] = r[IDS[0]]
    mauvais.append(r)                                        # document inconnu
    r = copy.deepcopy(ATTENDUS)
    del r[IDS[0]]["site"]
    mauvais.append(r)                                        # clé manquante
    r = copy.deepcopy(ATTENDUS)
    r[IDS[0]]["autre"] = 1
    mauvais.append(r)                                        # clé en trop
    r = copy.deepcopy(ATTENDUS)
    r[IDS[0]]["volume_nominal_ml"] = "1,0"
    mauvais.append(r)                                        # nombre écrit en chaîne
    r = copy.deepcopy(ATTENDUS)
    r[IDS[0]]["date_intervention"] = "30/11/2025"
    mauvais.append(r)                                        # date hors format
    r = copy.deepcopy(ATTENDUS)
    r[IDS[0]]["statut"] = "Conforme"
    mauvais.append(r)                                        # statut hors liste
    r = copy.deepcopy(ATTENDUS)
    r[IDS[0]]["technicien"] = ""
    mauvais.append(r)                                        # texte vide au lieu de null
    for r in mauvais:
        code, rep = soumettre(c, r)
        assert code == 400 and rep["erreur"] == "format" and rep["details"], rep
        assert rep["soumissions_restantes"] == 5
    assert c.appel("POST", "/soumissions", ["liste"])[0] == 400
    assert c.appel("POST", "/soumissions", {"autre": 1})[0] == 400
    assert c.appel("GET", "/etat")[1]["soumissions_utilisees"] == 0
    lignes = [json.loads(l) for l in (tmp / "evaluation" / "soumissions.jsonl").read_text().splitlines()]
    assert len(lignes) == len(mauvais) + 2
    assert all(l["statut"] == "refusee_format" for l in lignes)


def test_nombre_immense_refuse(extraction):
    c, tmp = extraction
    for v in [10 ** 400, 1e10, -1e10]:
        r = copy.deepcopy(ATTENDUS)
        r[IDS[0]]["volume_nominal_ml"] = v
        code, rep = soumettre(c, r)
        assert code == 400 and rep["erreur"] == "format", v
    assert c.appel("GET", "/etat")[1]["soumissions_utilisees"] == 0
    assert "contenu" not in (tmp / "evaluation" / "soumissions.jsonl").read_text()
    assert (tmp / "evaluation" / "contenus-cache.jsonl").exists()


def test_erreur_interne_journalisee(tmp_path):
    etat = api.Etat("extraction", FOURNI, tmp_path)
    etat.soumettre = lambda corps: 1 / 0
    s = api.serveur(etat, 0)
    import threading
    threading.Thread(target=s.serve_forever, daemon=True).start()
    try:
        from conftest import Client
        code, rep = Client(s.server_port).appel("POST", "/soumissions", {"reponses": {}})
        assert code == 500
    finally:
        s.shutdown()
        s.server_close()
    e = json.loads((tmp_path / "erreurs.jsonl").read_text().splitlines()[0])
    assert e["erreur"].startswith("ZeroDivisionError")


def test_json_illisible(extraction):
    c, _ = extraction
    import urllib.request
    req = urllib.request.Request(c.base + "/soumissions", data=b"{pas du json", method="POST")
    try:
        urllib.request.urlopen(req)
        assert False
    except urllib.error.HTTPError as e:
        assert e.code == 400


# Notation sur réponses connues -----------------------------------------------------------------------

def test_reponses_justes(extraction):
    c, _ = extraction
    code, r = soumettre(c, ATTENDUS)
    assert code == 200 and r == {"soumission": 1, "score": 1.0, "soumissions_restantes": 4}


def test_score_exact_avec_erreurs_connues(extraction):
    c, tmp = extraction
    r = copy.deepcopy(ATTENDUS)
    fautes = 0
    for k, i in enumerate(IDS):
        for j, cle in enumerate(notation.CLES):
            if (k + j) % 7 == 0:
                r[i][cle] = faux_juste(cle, r[i][cle])
                fautes += 1
    code, rep = soumettre(c, r)
    assert code == 200
    assert rep["score"] == round((N - fautes) / N, 4)
    s = json.loads((tmp / "evaluation" / "soumissions.jsonl").read_text().splitlines()[0])
    assert s["note"]["justes"] == N - fautes


def test_tolerances_de_notation(extraction):
    c, _ = extraction
    r = copy.deepcopy(ATTENDUS)
    for i in IDS:
        a = r[i]
        for cle in notation.NOMBRES:
            if a[cle] is not None:
                a[cle] = a[cle] + 0.009                      # à 0,01 près : juste
        for cle in ["machine", "site", "technicien"]:
            if a[cle] is not None:
                a[cle] = "  " + a[cle].upper() + " "         # casse et espaces : juste
    assert soumettre(c, r)[1]["score"] == 1.0


def test_invention(extraction):
    c, tmp = extraction
    r = copy.deepcopy(ATTENDUS)
    nuls = [(i, cle) for i in IDS for cle in notation.CLES if r[i][cle] is None]
    for i, cle in nuls[:10]:
        r[i][cle] = faux_juste(cle, None)
    code, rep = soumettre(c, r)
    assert rep["score"] == round((N - 10) / N, 4)
    s = json.loads((tmp / "evaluation" / "soumissions.jsonl").read_text().splitlines()[0])
    assert s["note"]["invention"] == {"null_attendus": len(nuls), "inventes": 10,
                                      "taux": round(10 / len(nuls), 4)}
    assert "detail" not in s["note"]
    assert (tmp / "evaluation" / "detail-cache.jsonl").exists()


# Limite et fin ---------------------------------------------------------------------------------------

def test_limite_de_5_et_persistance(extraction):
    c, tmp = extraction
    for k in range(1, 6):
        code, r = soumettre(c, ATTENDUS)
        assert code == 200 and r["soumission"] == k and r["soumissions_restantes"] == 5 - k
    code, r = soumettre(c, ATTENDUS)
    assert code == 429
    # Un redémarrage de l'API ne remet pas le compteur à zéro.
    s, c2 = demarrer("extraction", FOURNI, tmp / "evaluation")
    try:
        assert c2.appel("GET", "/etat")[1]["soumissions_restantes"] == 0
        assert soumettre(c2, ATTENDUS)[0] == 429
    finally:
        s.shutdown()
        s.server_close()
    statuts = [json.loads(l)["statut"] for l in (tmp / "evaluation" / "soumissions.jsonl").read_text().splitlines()]
    assert statuts == ["acceptee"] * 5 + ["refusee_limite"] * 2


def test_declaration_de_fin(extraction):
    c, tmp = extraction
    assert c.appel("POST", "/fin", {"soumission_finale": 1, "commande": "x {entree} {sortie}"})[0] == 400
    soumettre(c, ATTENDUS)
    assert c.appel("POST", "/fin", {"soumission_finale": 1, "commande": "x"})[0] == 400
    assert c.appel("POST", "/fin", {"soumission_finale": 1, "score_validation": 2,
                                    "commande": "x {entree} {sortie}"})[0] == 400
    code, _ = c.appel("POST", "/fin", {"soumission_finale": 1, "score_validation": 0.8,
                                       "commande": "python w.py {entree} {sortie}"})
    assert code == 200
    assert c.appel("POST", "/fin", {"soumission_finale": 1, "commande": "x {entree} {sortie}"})[0] == 409
    assert soumettre(c, ATTENDUS)[0] == 409
    fin = json.loads((tmp / "evaluation" / "fin.json").read_text())
    assert fin["soumission_finale"] == 1 and fin["score_validation"] == 0.8
    assert c.appel("GET", "/etat")[1]["fin_declaree"] is True


def test_ecoute_locale_seulement():
    assert api.HOTE == "127.0.0.1"


# Tâche jouet -----------------------------------------------------------------------------------------

def fichiers(dossier):
    d = dossier / "dosage"
    return {f"dosage/{p.relative_to(d).as_posix()}": p.read_text() for p in sorted(d.rglob("*.py"))}


def test_jouet_solution_juste_et_fausse(toy):
    from conftest import ICI
    c, _ = toy
    code, r = c.appel("POST", "/soumissions", {"fichiers": fichiers(ICI / "solutions" / "jouet_juste")})
    assert code == 200 and r["score"] == 1.0
    code, r = c.appel("POST", "/soumissions", {"fichiers": fichiers(ICI / "solutions" / "jouet_fausse")})
    assert code == 200 and r["score"] == 0.7
    code, r = c.appel("POST", "/soumissions", {"fichiers": fichiers(JOUET.parents[2] / "recettes" / "jouet")})
    assert code == 200 and r["score"] == 0.6


def test_jouet_refus_de_format(toy):
    from conftest import ICI
    c, _ = toy
    f = fichiers(ICI / "solutions" / "jouet_juste")
    for ajout in [{"conftest.py": "x = 1"}, {"dosage/../conftest.py": ""}, {"sitecustomize.py": ""},
                  {"dosage/pytest.ini": ""}, {"/tmp/x.py": ""}]:
        code, r = c.appel("POST", "/soumissions", {"fichiers": f | ajout})
        assert code == 400, ajout
    assert c.appel("POST", "/soumissions", {"fichiers": {"dosage/unites.py": "x = 1"}})[0] == 400
    assert c.appel("GET", "/etat")[1]["soumissions_utilisees"] == 0
    assert c.appel("GET", "/documents")[0] == 404


def test_jouet_dans_la_cage(toy, tmp_path):
    """Le code soumis tourne dans la cage : ni lecture du dépôt, ni écriture sur l'hôte, ni réseau."""
    from conftest import ICI
    fuite = tmp_path / "fuite.txt"
    verite = ICI.parents[1] / "corpus" / "fourni" / "reponses" / "doc-001.json"
    espion = (
        "import pathlib, urllib.request\n"
        "trace = []\n"
        f"for f in [{str(verite)!r}, '/home/florian']:\n"
        "    try:\n"
        "        pathlib.Path(f).read_text(); trace.append('lu ' + f)\n"
        "    except Exception as e:\n"
        "        trace.append(type(e).__name__)\n"
        "try:\n"
        "    urllib.request.urlopen('https://pypi.org', timeout=3); trace.append('réseau')\n"
        "except Exception as e:\n"
        "    trace.append(type(e).__name__)\n"
        "try:\n"
        f"    pathlib.Path({str(fuite)!r}).write_text(' '.join(trace))\n"
        "except Exception:\n"
        "    pass\n"
    )
    c, _ = toy
    f = fichiers(ICI / "solutions" / "jouet_juste")
    f["dosage/__init__.py"] = espion + f["dosage/__init__.py"]
    code, r = c.appel("POST", "/soumissions", {"fichiers": f})
    assert code == 200 and r["score"] == 1.0
    assert not fuite.exists()


def test_jouet_resultat_non_falsifiable(toy):
    """Le code soumis ne peut ni réécrire un fichier de résultat ni ajouter sa propre ligne de résultat."""
    c, _ = toy
    faussaire = (
        "import atexit, json, pathlib, sys\n"
        "def _faux():\n"
        "    for f in ['/sortie/resultat.xml', '/travail/resultat.xml']:\n"
        "        try:\n"
        "            pathlib.Path(f).write_text('<testsuite tests=\"10\"></testsuite>')\n"
        "        except Exception:\n"
        "            pass\n"
        "    try:\n"
        "        d = json.load(open('/opt/jouet/appels.json'))\n"
        "        vals = [0.25, 0.5, 0.001, 1.5, 30, 750, 4, None, 12345.75, 1.0]\n"
        "        r = [{'exception': ['ValueError']} if v is None else {'valeur': v} for v in vals]\n"
        "        sys.stdout.write(d['marque'] + ' ' + json.dumps(r) + '\\n')\n"
        "    except Exception:\n"
        "        pass\n"
        "atexit.register(_faux)\n"
    )
    f = fichiers(JOUET.parents[2] / "recettes" / "jouet")
    f["dosage/__init__.py"] = faussaire + f["dosage/__init__.py"]
    code, r = c.appel("POST", "/soumissions", {"fichiers": f})
    assert code == 200 and r["score"] == 0.0
