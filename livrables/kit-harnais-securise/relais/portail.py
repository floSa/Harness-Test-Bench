"""Relais entre le harnais et le portail IAG (API compatible OpenAI). Bibliothèque standard seulement.

Pourquoi : le harnais est un programme qui exécute des commandes décidées par un modèle. Il ne doit
jamais détenir la vraie clé du portail. Il reçoit une clé locale (CLE_RELAIS), valable seulement
auprès de ce relais, qui ajoute lui-même la clé du portail à chaque requête.

Ce que fait le relais, dans l'ordre, pour chaque requête :
  1. refuse toute route autre que l'appel au modèle (ROUTES) et la liste des modèles ;
  2. refuse une clé autre que CLE_RELAIS (comparaison à temps constant) ;
  3. refuse un modèle hors de la liste autorisée (IAG_MODELES) ;
  4. refuse au-delà du plafond de jetons (PLAFOND_JETONS, compté sur toute la durée du test)
     et du débit (APPELS_PAR_MINUTE) ; limite les appels simultanés (APPELS_SIMULTANES) ;
  5. transmet au portail avec la clé du portail, réponse en flux comprise ;
  6. écrit une ligne par appel dans /journaux/appels.jsonl : heure, durée, modèle, statut,
     jetons. Jamais de contenu ni de clé.

Variables : IAG_URL (avec /v1), IAG_CLE, IAG_MODELE, IAG_MODELES (facultatif, liste séparée par des
virgules), CLE_RELAIS, PLAFOND_JETONS, APPELS_PAR_MINUTE, APPELS_SIMULTANES, TAILLE_MAX_MO,
ROUTES_SUPPLEMENTAIRES (ex. /v1/responses), IAG_ENTETE_CLE (en-tête de la clé si le portail
n'utilise pas « Authorization: Bearer »), IAG_ENTETES (en-têtes fixes, en JSON), COMPTER_FLUX,
ECOUTE (adresse d'écoute, 0.0.0.0:8080 par défaut ; un chemin pour une socket Unix), JOURNAUX (dossier).
Le mandataire d'entreprise (HTTPS_PROXY, NO_PROXY) et le certificat interne (SSL_CERT_FILE) sont
pris dans l'environnement.
"""
import collections
import datetime
import hmac
import json
import os
import socketserver
import ssl
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

URL = os.environ["IAG_URL"].rstrip("/")
CLE_IAG = os.environ["IAG_CLE"]
CLE_RELAIS = os.environ["CLE_RELAIS"].encode()
MODELES = [m.strip() for m in (os.environ.get("IAG_MODELES") or os.environ["IAG_MODELE"]).split(",") if m.strip()]
ROUTES = {"/v1/chat/completions"} | {r.strip() for r in os.environ.get("ROUTES_SUPPLEMENTAIRES", "").split(",") if r.strip()}
PLAFOND = int(os.environ.get("PLAFOND_JETONS") or 30_000_000)
PAR_MINUTE = int(os.environ.get("APPELS_PAR_MINUTE") or 60)
SIMULTANES = threading.BoundedSemaphore(int(os.environ.get("APPELS_SIMULTANES") or 4))
TAILLE_MAX = int(os.environ.get("TAILLE_MAX_MO") or 20) * 1024 * 1024
ENTETE_CLE = os.environ.get("IAG_ENTETE_CLE") or "Authorization"
ENTETES = json.loads(os.environ.get("IAG_ENTETES") or "{}")
COMPTER_FLUX = (os.environ.get("COMPTER_FLUX") or "1") == "1"
ECOUTE = os.environ.get("ECOUTE") or "0.0.0.0:8080"
JOURNAUX = os.environ.get("JOURNAUX") or "/journaux"
JOURNAL = os.path.join(JOURNAUX, "appels.jsonl")
COMPTEUR = os.path.join(JOURNAUX, "compteur.json")
CONTEXTE_TLS = ssl.create_default_context()   # lit SSL_CERT_FILE s'il est défini

verrou = threading.Lock()
recents = collections.deque()
try:
    with open(COMPTEUR) as f:
        cumul = json.load(f)["jetons"]
except (OSError, ValueError, KeyError):
    cumul = 0


def masquer(octets):
    """Retire la clé du portail de tout texte renvoyé au harnais (message d'erreur par exemple)."""
    return octets.replace(CLE_IAG.encode(), b"***")


def jetons(usage):
    """Jetons envoyés et produits, que la réponse suive le format chat ou le format responses."""
    if not isinstance(usage, dict):
        return 0, 0
    return (usage.get("prompt_tokens") or usage.get("input_tokens") or 0,
            usage.get("completion_tokens") or usage.get("output_tokens") or 0)


def journaliser(ligne):
    global cumul
    with verrou:
        cumul += (ligne.get("jetons_entree") or 0) + (ligne.get("jetons_sortie") or 0)
        ligne["jetons_cumules"] = cumul
        with open(JOURNAL, "a") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        with open(COMPTEUR + ".tmp", "w") as f:
            json.dump({"jetons": cumul}, f)
        os.replace(COMPTEUR + ".tmp", COMPTEUR)


def debit_depasse():
    with verrou:
        maintenant = time.monotonic()
        while recents and maintenant - recents[0] > 60:
            recents.popleft()
        if len(recents) >= PAR_MINUTE:
            return True
        recents.append(maintenant)
        return False


class Relais(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "relais-iag"
    sys_version = ""

    def log_message(self, *args):   # pas de journal d'accès sur la sortie standard
        pass

    def repondre(self, code, corps, entetes=None):
        octets = corps if isinstance(corps, bytes) else json.dumps(corps, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(octets)))
        for k, v in (entetes or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(octets)

    def refuser(self, code, message, route=None, modele=None):
        if route:
            journaliser({"debut": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                         "route": route, "modele": modele, "statut": code, "refus_du_relais": message})
        self.repondre(code, {"error": {"message": f"relais : {message}", "type": "relais", "code": code}},
                      {"Retry-After": "60"} if code == 429 else None)

    def cle_valide(self):
        donnee = self.headers.get("Authorization", "")
        donnee = donnee[7:] if donnee.startswith("Bearer ") else self.headers.get("api-key", "")
        return hmac.compare_digest(donnee.encode(), CLE_RELAIS)

    def do_GET(self):
        route = self.path.split("?")[0].rstrip("/")
        if route != "/v1/models":
            return self.refuser(404, "route non relayée")
        if not self.cle_valide():
            return self.refuser(401, "clé du relais invalide")
        self.repondre(200, {"object": "list", "data": [{"id": m, "object": "model", "owned_by": "portail-iag"}
                                                       for m in MODELES]})

    def do_POST(self):
        route = self.path.split("?")[0].rstrip("/")
        if route not in ROUTES:
            return self.refuser(404, "route non relayée")
        if not self.cle_valide():
            return self.refuser(401, "clé du relais invalide")
        taille = int(self.headers.get("Content-Length") or 0)
        if taille > TAILLE_MAX:
            return self.refuser(413, "requête trop lourde", route)
        try:
            corps = json.loads(self.rfile.read(taille))
        except ValueError:
            return self.refuser(400, "corps JSON illisible", route)
        modele = corps.get("model")
        if modele not in MODELES:
            return self.refuser(403, f"modèle non autorisé (autorisés : {', '.join(MODELES)})", route, modele)
        if cumul >= PLAFOND:
            return self.refuser(429, f"plafond de {PLAFOND} jetons atteint", route, modele)
        if debit_depasse():
            return self.refuser(429, f"plus de {PAR_MINUTE} appels par minute", route, modele)
        flux = bool(corps.get("stream"))
        if flux and COMPTER_FLUX and route == "/v1/chat/completions" and "stream_options" not in corps:
            corps["stream_options"] = {"include_usage": True}   # pour compter les jetons d'une réponse en flux
        messages = corps.get("messages") or []
        ligne = {"debut": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "route": route,
                 "modele": modele, "flux": flux, "outils": len(corps.get("tools") or []),
                 "images": sum(1 for m in messages if isinstance(m, dict) and isinstance(m.get("content"), list)
                               for p in m["content"] if isinstance(p, dict) and p.get("type") == "image_url")}
        entetes = {"Content-Type": "application/json", "Accept": self.headers.get("Accept", "application/json"),
                   **ENTETES}
        entetes[ENTETE_CLE] = f"Bearer {CLE_IAG}" if ENTETE_CLE.lower() == "authorization" else CLE_IAG
        requete = urllib.request.Request(URL + route[len("/v1"):], data=json.dumps(corps).encode(),
                                         headers=entetes, method="POST")
        debut = time.monotonic()
        with SIMULTANES:
            try:
                with urllib.request.urlopen(requete, timeout=600, context=CONTEXTE_TLS) as rep:
                    ligne["statut"] = rep.status
                    if flux:
                        self.relayer_flux(rep, ligne)
                    else:
                        octets = rep.read()
                        try:
                            ligne["jetons_entree"], ligne["jetons_sortie"] = jetons(json.loads(octets).get("usage"))
                        except ValueError:
                            pass
                        self.repondre(rep.status, octets)
            except urllib.error.HTTPError as e:
                ligne["statut"] = e.code
                self.repondre(e.code, masquer(e.read()))
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                ligne["statut"] = 502
                ligne["erreur"] = type(e).__name__
                if not self.wfile.closed:
                    try:
                        self.refuser(502, f"portail injoignable ({type(e).__name__})")
                    except OSError:
                        pass
        ligne["duree_s"] = round(time.monotonic() - debut, 3)
        journaliser(ligne)

    def relayer_flux(self, rep, ligne):
        """Recopie la réponse en flux (événements « data: ») au fil de l'eau, en comptant les jetons."""
        self.send_response(rep.status)
        self.send_header("Content-Type", rep.headers.get("Content-Type", "text/event-stream"))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            for brut in iter(rep.readline, b""):
                if brut.startswith(b"data: {"):
                    try:
                        usage = json.loads(brut[6:]).get("usage")
                        if usage:
                            ligne["jetons_entree"], ligne["jetons_sortie"] = jetons(usage)
                    except ValueError:
                        pass
                self.wfile.write(b"%x\r\n%s\r\n" % (len(brut), brut))
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            ligne["erreur"] = "harnais déconnecté pendant le flux"
            self.close_connection = True


class ServeurUnix(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


if __name__ == "__main__":
    if ECOUTE.startswith("/"):   # mode sans conteneur : socket Unix, seul passage depuis la cage
        if os.path.exists(ECOUTE):
            os.remove(ECOUTE)
        serveur = ServeurUnix(ECOUTE, Relais)
    else:
        hote, port = ECOUTE.rsplit(":", 1)
        serveur = ThreadingHTTPServer((hote, int(port)), Relais)
        serveur.daemon_threads = True
    print(f"relais prêt : modèles {MODELES}, routes {sorted(ROUTES)}, plafond {PLAFOND} jetons "
          f"(déjà consommés : {cumul}), {PAR_MINUTE} appels par minute", flush=True)
    serveur.serve_forever()
