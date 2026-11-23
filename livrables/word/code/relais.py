"""Relais : seul programme qui connaît la clé du portail IAG. Le harnais n'a qu'une clé locale."""
import hmac
import os
import socketserver
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

URL = os.environ["IAG_URL"].rstrip("/")          # adresse du portail, avec /v1
CLE_IAG = os.environ["IAG_CLE"]                  # vraie clé, jamais transmise au harnais
CLE_LOCALE = os.environ["CLE_LOCALE"].encode()   # clé donnée au harnais, valable ici seulement
ROUTES = {"/v1/chat/completions", "/v1/models"}  # seules routes relayées


class Relais(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def refuser(self, code, texte):
        self.send_response(code)
        self.send_header("Content-Length", str(len(texte.encode())))
        self.end_headers()
        self.wfile.write(texte.encode())

    def relayer(self):
        route = self.path.split("?")[0]
        if route not in ROUTES:
            return self.refuser(404, "route non relayée")
        cle = self.headers.get("Authorization", "").removeprefix("Bearer ").encode()
        if not hmac.compare_digest(cle, CLE_LOCALE):
            return self.refuser(401, "clé locale invalide")
        corps = self.rfile.read(int(self.headers.get("Content-Length") or 0)) if self.command == "POST" else None
        requete = urllib.request.Request(URL + route.removeprefix("/v1"), data=corps, method=self.command,
                                         headers={"Authorization": f"Bearer {CLE_IAG}",
                                                  "Content-Type": "application/json"})
        try:
            reponse = urllib.request.urlopen(requete, timeout=600)
        except urllib.error.HTTPError as erreur:
            reponse = erreur
        except OSError as erreur:
            return self.refuser(502, f"portail injoignable ({type(erreur).__name__})")
        self.send_response(reponse.status)
        self.send_header("Content-Type", reponse.headers.get("Content-Type", "application/json"))
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        while bloc := reponse.read1(65536):   # recopie au fil de l'eau (réponses en flux)
            self.wfile.write(b"%x\r\n%s\r\n" % (len(bloc), bloc))
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")

    do_GET = do_POST = relayer


class ServeurUnix(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


if __name__ == "__main__":
    ecoute = os.environ.get("ECOUTE", "0.0.0.0:8080")   # un chemin = socket Unix (mode sans conteneur)
    if ecoute.startswith("/"):
        if os.path.exists(ecoute):
            os.remove(ecoute)
        serveur = ServeurUnix(ecoute, Relais)
    else:
        hote, port = ecoute.rsplit(":", 1)
        serveur = ThreadingHTTPServer((hote, int(port)), Relais)
        serveur.daemon_threads = True
    serveur.serve_forever()
