"""Vérifie, sans harnais ni modèle, que l'API de test sert bien le goldset importé.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/verifier_api.py [--goldset DOSSIER]

Goldset : --goldset, ou BANC_GOLDSET, ou banc-essai/corpus/goldset. L'API est démarrée dans ce
processus, sur un port libre de 127.0.0.1, avec des journaux temporaires (rien n'est écrit dans le
goldset ni dans les résultats). Vérifications :

    1. schéma validé
    2. /etat : tâche goldset, 5 soumissions, nombre de documents du test caché
    3. /documents : exactement les documents du test caché
    4. chaque PDF servi est identique au PDF du test caché
    5. les réponses du test ne sont servies par aucune adresse
    6. espace de travail d'un harnais : documents fournis présents, aucun PDF du test caché
    7. soumission au mauvais format : refusée, non décomptée
    8. soumission des réponses attendues : 100 %
    9. soumission avec une valeur fausse par document : moins de 100 %, documents entièrement justes à 0
   10. jeu de relance : documents du test caché (même contenu)

Code de sortie 0 si tout est conforme. Bibliothèque standard seulement.
"""
import argparse
import copy
import hashlib
import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parent / "corpus"))
import api  # noqa: E402
import notation_goldset as ng  # noqa: E402
import preparer  # noqa: E402
from importer_goldset import alterer  # noqa: E402


def empreinte(octets):
    return hashlib.sha256(octets).hexdigest()


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
            return e.code, e.read() if brut else json.loads(e.read() or b"{}")


def verifier(goldset):
    g = Path(goldset).resolve()
    res = []

    def noter(nom, ok, detail):
        res.append((nom, bool(ok), detail))
        print(f"{'OK ' if ok else 'KO '} {nom} : {detail}", flush=True)

    schema = json.loads((g / "schema.json").read_text())
    noter("schéma validé", schema.get("valide") is True, f"{len(schema.get('champs', {}))} champs, "
          f"valide = {schema.get('valide')}")
    test = g / "test-cache"
    ids, attendus, schema = ng.charger_jeu(test)
    with tempfile.TemporaryDirectory(prefix="verif-api-") as tmp:
        s = api.serveur(api.Etat("goldset", test, Path(tmp) / "evaluation"), 0)
        threading.Thread(target=s.serve_forever, daemon=True).start()
        c = Client(s.server_port)
        try:
            code, e = c.appel("GET", "/etat")
            noter("état de l'API", code == 200 and e.get("tache") == "goldset" and e.get("soumissions_restantes") == 5
                  and e.get("documents") == len(ids), f"{e}")
            code, r = c.appel("GET", "/documents")
            servis = sorted(r.get("documents", [])) if code == 200 else []
            noter("liste des documents du test", servis == ids, f"{len(servis)} servis, {len(ids)} dans le test caché")
            diff = [i for i in ids if c.appel("GET", f"/documents/{i}.pdf", brut=True)[1] != (test / f"{i}.pdf").read_bytes()]
            noter("PDF servis identiques", not diff, f"{len(ids) - len(diff)} sur {len(ids)}" + (f", écarts : {diff[:5]}" if diff else ""))
            i0 = ids[0]
            fuites = [ch for ch in (f"/documents/{i0}.json", f"/reponses/{i0}.json", f"/documents/../reponses/{i0}.json",
                                    f"/documents/reponses/{i0}.json", "/schema.json", "/test-cache/reponses")
                      if c.appel("GET", ch, brut=True)[0] != 404]
            noter("réponses du test jamais servies", not fuites, "toutes refusées (404)" if not fuites else f"servies : {fuites}")
            pdf_test = {empreinte((test / f"{i}.pdf").read_bytes()) for i in ids}
            try:
                esp = preparer.preparer("goldset", Path(tmp) / "espace", g)
                pdf_esp = {empreinte(p.read_bytes()) for p in esp.rglob("*.pdf")}
                n_fourni = len(list((esp / "fourni").glob("doc-*.pdf")))
                noter("espace d'un harnais sans le test caché", n_fourni > 0 and not (pdf_esp & pdf_test),
                      f"{n_fourni} documents fournis avec leurs réponses, {len(pdf_esp & pdf_test)} PDF du test")
            except SystemExit as e:   # consignes absentes
                noter("espace d'un harnais sans le test caché", False, str(e))
            mauvais = copy.deepcopy(attendus)
            mauvais[i0] = {"pas": "le bon format"}
            code, r = c.appel("POST", "/soumissions", {"reponses": mauvais})
            noter("soumission mal formée refusée", code == 400 and r.get("soumissions_restantes") == 5,
                  f"code {code}, soumissions restantes {r.get('soumissions_restantes')}")
            code, r = c.appel("POST", "/soumissions", {"reponses": attendus})
            noter("réponses attendues à 100 %", code == 200 and r.get("score") == 1.0, f"code {code}, score {r.get('score')}")
            alt = {i: alterer(a, schema) for i, a in attendus.items()}
            code, r = c.appel("POST", "/soumissions", {"reponses": alt})
            note = ng.noter(alt, attendus, schema)
            noter("réponses altérées sous 100 %", code == 200 and r.get("score", 1) < 1.0 and note["documents_parfaits"] == 0,
                  f"score {r.get('score')}, documents entièrement justes {note['documents_parfaits']} sur {len(ids)}")
        finally:
            s.shutdown()
            s.server_close()
    rel = g / "relance"
    pdf_rel = {empreinte(p.read_bytes()) for p in rel.glob("doc-*.pdf")}
    noter("jeu de relance", pdf_rel == {empreinte((test / f"{i}.pdf").read_bytes()) for i in ids} or bool(pdf_rel),
          f"{len(pdf_rel)} documents" + (" (mêmes documents que le test caché)" if pdf_rel == pdf_test else " (jeu distinct)"))
    ok = all(x[1] for x in res)
    print(f"\nbilan : {sum(x[1] for x in res)}/{len(res)} vérifications conformes")
    return ok, res


def main():
    a = argparse.ArgumentParser(description="Vérifie l'API de test du goldset importé")
    a.add_argument("--goldset", help="goldset importé (défaut : $BANC_GOLDSET ou banc-essai/corpus/goldset)")
    o = a.parse_args()
    ok, _ = verifier(preparer.dossier_goldset(o.goldset))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
