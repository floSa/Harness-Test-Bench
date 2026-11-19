"""API de soumission du banc (127.0.0.1 seulement).

Usage (depuis la racine du dépôt) :
    uv run --project banc-essai/evaluation python banc-essai/evaluation/api.py \
        --tache extraction --jeu banc-essai/corpus/test-cache --sortie banc-essai/resultats/<essai>/evaluation
    ... --tache jouet --jeu banc-essai/evaluation/taches/jouet --sortie ...

Routes :
    GET  /etat                     tâche, soumissions utilisées et restantes, fin déclarée
    GET  /documents                identifiants des documents à traiter (extraction)
    GET  /documents/<id>.pdf       PDF d'un document (jamais ses réponses)
    POST /soumissions              {"reponses": {id: {clé: valeur}}} (extraction)
                                   {"fichiers": {chemin: contenu}} (jouet) ; renvoie le score global
    POST /fin                      {"soumission_finale": n, "score_validation": x, "commande": "..."}

Une soumission au mauvais format est refusée (400) et ne compte pas ; au-delà de 5 soumissions
acceptées, refus (429). Chaque requête est journalisée (acces.jsonl), chaque soumission aussi
(soumissions.jsonl : heure, contenu, score et scores agrégés). Le détail par document, qui révèle
la vérité, va dans detail-cache.jsonl, hors git. L'état survit à un redémarrage.
"""
import argparse
import datetime
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import jouet
import notation

HOTE = "127.0.0.1"
LIMITE = 5
TAILLE_MAX_CORPS = 8 * 1024 * 1024


def maintenant():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")


class Etat:
    def __init__(self, tache, jeu, sortie, limite=LIMITE):
        self.tache, self.jeu, self.sortie, self.limite = tache, Path(jeu), Path(sortie), limite
        self.sortie.mkdir(parents=True, exist_ok=True)
        self.verrou = threading.Lock()
        if tache == "extraction":
            self.ids, self.attendus, self.verites = notation.charger_jeu(self.jeu)
            if not self.ids:
                raise SystemExit(f"aucun document dans {self.jeu}")
        else:
            self.ids = []
            jouet.config(self.jeu)
        self.f_soum = self.sortie / "soumissions.jsonl"
        self.f_detail = self.sortie / "detail-cache.jsonl"
        self.f_acces = self.sortie / "acces.jsonl"
        self.f_fin = self.sortie / "fin.json"
        self.scores = {}
        if self.f_soum.exists():
            for ligne in self.f_soum.read_text().splitlines():
                s = json.loads(ligne)
                if s["statut"] == "acceptee":
                    self.scores[s["numero"]] = s["score"]

    def ecrire(self, f, obj):
        with f.open("a") as h:
            h.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def etat(self):
        return {"tache": self.tache, "limite": self.limite, "soumissions_utilisees": len(self.scores),
                "soumissions_restantes": self.limite - len(self.scores), "fin_declaree": self.f_fin.exists(),
                "documents": len(self.ids) if self.ids else None}

    def soumettre(self, corps):
        with self.verrou:
            base = {"heure": maintenant(), "contenu": corps}
            if len(self.scores) >= self.limite:
                self.ecrire(self.f_soum, base | {"statut": "refusee_limite"})
                return 429, {"erreur": f"limite de {self.limite} soumissions atteinte"}
            if self.f_fin.exists():
                self.ecrire(self.f_soum, base | {"statut": "refusee_fin"})
                return 409, {"erreur": "fin déjà déclarée"}
            if not isinstance(corps, dict):
                err = ["objet JSON attendu"]
            elif self.tache == "extraction":
                err = notation.valider(corps.get("reponses"), self.ids)
            else:
                err = jouet.valider(corps.get("fichiers"), self.jeu)
            if err:
                self.ecrire(self.f_soum, base | {"statut": "refusee_format", "erreurs": err})
                return 400, {"erreur": "format", "details": err[:50],
                             "soumissions_restantes": self.limite - len(self.scores)}
            numero = len(self.scores) + 1
            if self.tache == "extraction":
                note = notation.noter(corps["reponses"], self.attendus, self.verites)
                detail = note.pop("detail")
                self.ecrire(self.f_detail, {"numero": numero, "detail": detail})
            else:
                note = jouet.noter(corps["fichiers"], self.jeu)
            self.scores[numero] = note["score"]
            self.ecrire(self.f_soum, base | {"statut": "acceptee", "numero": numero, "score": note["score"],
                                             "note": note})
            return 200, {"soumission": numero, "score": note["score"],
                         "soumissions_restantes": self.limite - len(self.scores)}

    def fin(self, corps):
        with self.verrou:
            if self.f_fin.exists():
                return 409, {"erreur": "fin déjà déclarée"}
            err = []
            if not isinstance(corps, dict):
                return 400, {"erreur": "format", "details": ["objet JSON attendu"]}
            n = corps.get("soumission_finale")
            if isinstance(n, bool) or n not in self.scores:
                err.append(f"soumission_finale : numéro d'une soumission acceptée attendu "
                           f"({sorted(self.scores) or 'aucune'})")
            sv = corps.get("score_validation")
            if sv is not None and (isinstance(sv, bool) or not isinstance(sv, (int, float)) or not 0 <= sv <= 1):
                err.append("score_validation : nombre entre 0 et 1, ou null")
            if self.tache == "extraction" and not (isinstance(corps.get("commande"), str)
                                                   and "{entree}" in corps["commande"]
                                                   and "{sortie}" in corps["commande"]):
                err.append("commande : texte contenant {entree} et {sortie}")
            if err:
                return 400, {"erreur": "format", "details": err}
            fin = {"heure": maintenant(), "soumission_finale": n, "score_validation": sv,
                   "commande": corps.get("commande"), "commentaire": corps.get("commentaire")}
            self.f_fin.write_text(json.dumps(fin, ensure_ascii=False, indent=2) + "\n")
            return 200, {"enregistree": True}


def gestionnaire(etat):
    class G(BaseHTTPRequestHandler):
        server_version = "banc-evaluation/1.0"

        def log_message(self, *a):
            pass

        def repondre(self, code, obj=None, octets=None, type_="application/json"):
            corps = octets if octets is not None else json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", type_)
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)
            etat.ecrire(etat.f_acces, {"heure": maintenant(), "methode": self.command, "chemin": self.path,
                                       "code": code})

        def do_GET(self):
            if self.path == "/etat":
                return self.repondre(200, etat.etat())
            if etat.tache == "extraction" and self.path == "/documents":
                return self.repondre(200, {"documents": etat.ids})
            if etat.tache == "extraction" and self.path.startswith("/documents/") and self.path.endswith(".pdf"):
                i = self.path[len("/documents/"):-len(".pdf")]
                if i in etat.ids:
                    return self.repondre(200, octets=(etat.jeu / f"{i}.pdf").read_bytes(),
                                         type_="application/pdf")
            return self.repondre(404, {"erreur": "introuvable"})

        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                n = -1
            if not 0 < n <= TAILLE_MAX_CORPS:
                return self.repondre(400, {"erreur": "corps absent ou trop lourd"})
            try:
                corps = json.loads(self.rfile.read(n))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self.repondre(400, {"erreur": "format", "details": ["JSON illisible"]})
            if self.path == "/soumissions":
                return self.repondre(*etat.soumettre(corps))
            if self.path == "/fin":
                return self.repondre(*etat.fin(corps))
            return self.repondre(404, {"erreur": "introuvable"})

    return G


def serveur(etat, port):
    return ThreadingHTTPServer((HOTE, port), gestionnaire(etat))


def main():
    a = argparse.ArgumentParser(description="API de soumission du banc")
    a.add_argument("--tache", choices=["extraction", "jouet"], required=True)
    a.add_argument("--jeu", required=True, help="dossier du jeu caché (PDF, reponses/, verite/) ou de la tâche jouet")
    a.add_argument("--sortie", required=True, help="dossier des journaux de l'essai")
    a.add_argument("--port", type=int, default=8765)
    o = a.parse_args()
    s = serveur(Etat(o.tache, o.jeu, o.sortie), o.port)
    print(f"API {o.tache} sur http://{HOTE}:{s.server_port}", flush=True)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
