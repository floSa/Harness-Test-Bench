"""Dans la cage : seul pont entre le harnais et l'extérieur. Bibliothèque standard seulement.

La cage n'a aucun réseau (ni route, ni DNS). Ce script y ouvre deux adresses locales, reliées chacune
à une socket Unix montée depuis la machine :
  127.0.0.1:8080  ->  /run/kit/relais.sock  (appels au modèle)
  127.0.0.1:3128  ->  /run/kit/filtre.sock  (téléchargements autorisés)
puis lance la commande demandée et rend son code de sortie.

    python3 -I /opt/passerelle.py -- commande [arguments]
"""
import os
import signal
import socket
import subprocess
import sys
import threading

PONTS = {8080: "/run/kit/relais.sock", 3128: "/run/kit/filtre.sock"}


def recopier(source, destination):
    try:
        while donnees := source.recv(65536):
            destination.sendall(donnees)
    except OSError:
        pass
    try:
        destination.shutdown(socket.SHUT_WR)
    except OSError:
        pass


def relier(client, chemin):
    unix = socket.socket(socket.AF_UNIX)
    try:
        unix.connect(chemin)
    except OSError:
        client.close()
        return
    retour = threading.Thread(target=recopier, args=(unix, client), daemon=True)
    retour.start()
    recopier(client, unix)
    retour.join()
    client.close()
    unix.close()


def ecouter(serveur, chemin):
    while True:
        client, _ = serveur.accept()
        threading.Thread(target=relier, args=(client, chemin), daemon=True).start()


if __name__ == "__main__":
    for port, chemin in PONTS.items():
        serveur = socket.create_server(("127.0.0.1", port))   # ouvert avant de lancer la commande
        threading.Thread(target=ecouter, args=(serveur, chemin), daemon=True).start()
    commande = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["bash"]
    # La commande passe au premier plan du terminal : Ctrl+C l'atteint, elle seule, et la cage reste ouverte.
    terminal = os.isatty(0)

    def premier_plan():
        os.setpgrp()
        if terminal:
            signal.signal(signal.SIGTTOU, signal.SIG_IGN)
            try:
                os.tcsetpgrp(0, os.getpgrp())
            except OSError:
                pass
            signal.signal(signal.SIGTTOU, signal.SIG_DFL)

    enfant = subprocess.Popen(commande or ["bash"], preexec_fn=premier_plan)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    code = enfant.wait()
    if terminal:
        signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        try:
            os.tcsetpgrp(0, os.getpgrp())
        except OSError:
            pass
    sys.exit(code)
