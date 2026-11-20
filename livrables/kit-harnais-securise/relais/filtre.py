"""Filtre de téléchargements : seule sortie du harnais vers Internet, limitée à une liste de domaines.

Pourquoi : un harnais installe souvent des paquets (pip, npm) pendant son travail. Lui ouvrir tout
Internet lui permettrait aussi d'envoyer le contenu de l'espace de travail n'importe où, ou de
télécharger n'importe quoi. Ce filtre ne relaie que les connexions HTTPS (méthode CONNECT, port 443)
vers les domaines autorisés, plafonne le volume total reçu et note chaque demande, acceptée ou non.
Le contenu chiffré n'est ni lu ni modifié. Bibliothèque standard seulement.

Variables : DOMAINES_AUTORISES (liste séparée par des virgules ; « .exemple.org » autorise aussi
les sous-domaines), QUOTA_TELECHARGEMENT_MO (volume reçu maximal, pour toute la durée du filtre).
Si HTTPS_PROXY est défini (mandataire d'entreprise), les connexions passent par lui.
Journal : /journaux/telechargements.jsonl.
"""
import base64
import datetime
import json
import os
import socket
import socketserver
import threading
import urllib.parse

DOMAINES = [d.strip().lower() for d in os.environ.get("DOMAINES_AUTORISES", "").split(",") if d.strip()]
QUOTA = int(os.environ.get("QUOTA_TELECHARGEMENT_MO") or 5000) * 1024 * 1024
PARENT = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
JOURNAL = "/journaux/telechargements.jsonl"
verrou = threading.Lock()
recus_total = 0


def autorise(hote):
    hote = hote.lower().rstrip(".")
    return any(hote == d.lstrip(".") or (d.startswith(".") and hote.endswith(d)) for d in DOMAINES)


def noter(**champs):
    champs["heure"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with verrou, open(JOURNAL, "a") as f:
        f.write(json.dumps(champs, ensure_ascii=False) + "\n")


def ouvrir(hote, port):
    """Connexion vers la cible, directe ou par le mandataire d'entreprise."""
    if not PARENT:
        return socket.create_connection((hote, port), timeout=30)
    p = urllib.parse.urlsplit(PARENT)
    s = socket.create_connection((p.hostname, p.port or 8080), timeout=30)
    demande = f"CONNECT {hote}:{port} HTTP/1.1\r\nHost: {hote}:{port}\r\n"
    if p.username:
        jeton = base64.b64encode(f"{urllib.parse.unquote(p.username)}:{urllib.parse.unquote(p.password or '')}".encode())
        demande += f"Proxy-Authorization: Basic {jeton.decode()}\r\n"
    s.sendall((demande + "\r\n").encode())
    reponse = b""
    while b"\r\n\r\n" not in reponse:
        morceau = s.recv(4096)
        if not morceau:
            raise OSError("mandataire d'entreprise : connexion fermée")
        reponse += morceau
    if b" 200" not in reponse.split(b"\r\n", 1)[0]:
        raise OSError("mandataire d'entreprise : " + reponse.split(b"\r\n", 1)[0].decode(errors="replace"))
    return s


class Filtre(socketserver.StreamRequestHandler):
    def repondre(self, code, texte):
        self.wfile.write(f"HTTP/1.1 {code} {texte}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".encode())

    def handle(self):
        global recus_total
        ligne = self.rfile.readline(8192).decode(errors="replace").split()
        while self.rfile.readline(8192) not in (b"\r\n", b"\n", b""):
            pass
        if len(ligne) < 2 or ligne[0] != "CONNECT":
            noter(demande=" ".join(ligne[:2]), verdict="refusé", raison="seul HTTPS (CONNECT) est relayé")
            return self.repondre(403, "Forbidden")
        hote, _, port = ligne[1].rpartition(":")
        hote = hote.strip("[]")
        if port != "443" or not autorise(hote):
            noter(hote=hote, port=port, verdict="refusé", raison="domaine ou port non autorisé")
            return self.repondre(403, "Forbidden")
        if recus_total >= QUOTA:
            noter(hote=hote, verdict="refusé", raison="quota de téléchargement atteint")
            return self.repondre(403, "Forbidden")
        try:
            cible = ouvrir(hote, 443)
        except OSError as e:
            noter(hote=hote, verdict="échec", raison=str(e)[:200])
            return self.repondre(502, "Bad Gateway")
        self.repondre_tunnel()
        compte = {"envoyes": 0, "recus": 0}

        def copier(source, destination, cle):
            global recus_total
            try:
                while True:
                    morceau = source.recv(65536)
                    if not morceau:
                        break
                    compte[cle] += len(morceau)
                    if cle == "recus":
                        with verrou:
                            recus_total += len(morceau)
                            depasse = recus_total > QUOTA
                        if depasse:
                            break
                    destination.sendall(morceau)
            except OSError:
                pass
            finally:
                for s in (source, destination):
                    try:
                        s.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass

        cible.settimeout(None)
        self.connection.settimeout(None)
        montant = threading.Thread(target=copier, args=(self.connection, cible, "envoyes"), daemon=True)
        montant.start()
        copier(cible, self.connection, "recus")
        montant.join(5)
        cible.close()
        noter(hote=hote, verdict="accepté", octets_envoyes=compte["envoyes"], octets_recus=compte["recus"],
              quota_atteint=recus_total > QUOTA)

    def repondre_tunnel(self):
        self.wfile.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
        self.wfile.flush()


class Serveur(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"filtre prêt : domaines {DOMAINES}, quota {QUOTA // (1024 * 1024)} Mo, "
          f"mandataire d'entreprise {'oui' if PARENT else 'non'}", flush=True)
    Serveur(("0.0.0.0", 3128), Filtre).serve_forever()
