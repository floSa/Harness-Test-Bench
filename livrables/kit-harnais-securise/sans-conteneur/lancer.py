"""Mode sans conteneur : relais et filtre lancés sur la machine, harnais enfermé dans une cage bubblewrap.

    python3 sans-conteneur/lancer.py                                   interpréteur dans la cage
    python3 sans-conteneur/lancer.py python3 /kit/verifier.py --appel  vérification des protections
    python3 sans-conteneur/lancer.py goose session                     le harnais lui-même

Ce que voit le harnais dans la cage :
  /travail      dossier espace/ du kit (lecture et écriture)
  /home/agent   dossier sans-conteneur/maison/ (configuration et caches du harnais)
  /opt/harnais  dossier sans-conteneur/harnais/ (le harnais installé, lecture seule)
  /usr, /etc    système de la machine, lecture seule
  aucun autre dossier de la machine, aucun réseau sauf le relais et le filtre (voir passerelle.py).
Limites de mémoire, de processeur et de processus : unité systemd de l'utilisateur (MEMOIRE_MAX, CPU_MAX).

Prérequis : Linux ou WSL2, bubblewrap, python3, session systemd de l'utilisateur. Une seule session à la
fois. Relais et filtre sont arrêtés à la sortie. Bibliothèque standard seulement.
"""
import fcntl
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
ICI = KIT / "sans-conteneur"
JOURNAUX = KIT / "journaux"


def lire_reglages():
    reglages = {}
    for ligne in (KIT / ".env").read_text().splitlines():
        if "=" in ligne and not ligne.lstrip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            reglages[cle.strip()] = valeur.strip()
    return reglages


def arreter(message):
    sys.exit(f"lancer.py : {message}")


def demarrer(nom, script, environnement, socket_, services):
    sortie = open(JOURNAUX / f"{nom}.log", "a")
    processus = subprocess.Popen([sys.executable, "-I", str(KIT / "relais" / script)], env=environnement,
                                 stdout=sortie, stderr=subprocess.STDOUT, start_new_session=True)
    services.append(processus)
    for _ in range(100):
        if socket_.exists():
            return processus
        if processus.poll() is not None:
            arreter(f"le {nom} s'est arrêté au démarrage ; voir journaux/{nom}.log")
        time.sleep(0.1)
    arreter(f"le {nom} ne répond pas ; voir journaux/{nom}.log")


def limites_systemd(reglages):
    """Préfixe systemd-run qui plafonne mémoire, processeur et processus, ou [] si indisponible."""
    if not shutil.which("systemd-run") or subprocess.run(
            ["systemd-run", "--user", "--scope", "--quiet", "true"], capture_output=True).returncode:
        print("Attention : systemd-run --user indisponible, aucune limite de mémoire ni de processeur.",
              file=sys.stderr)
        return []
    memoire = (reglages.get("MEMOIRE_MAX") or "8g").upper()
    cpu = int(float(reglages.get("CPU_MAX") or 4) * 100)
    return ["systemd-run", "--user", "--scope", "--quiet", "--collect",
            "-p", f"MemoryMax={memoire}", "-p", "MemorySwapMax=0", "-p", "TasksMax=2048",
            "-p", f"CPUQuota={cpu}%", "--"]


def cage(reglages, commande, sockets):
    bwrap = ["bwrap", "--die-with-parent", "--unshare-user", "--unshare-pid", "--unshare-ipc",
             "--unshare-uts", "--unshare-net", "--hostname", "cage"]
    # Sans protection du noyau contre l'injection de frappes dans le terminal, la cage prend sa propre
    # session (au prix du Ctrl+C, qui n'atteint plus le harnais).
    try:
        tiocsti_bloque = Path("/proc/sys/dev/tty/legacy_tiocsti").read_text().strip() == "0"
    except OSError:
        tiocsti_bloque = False
    if not tiocsti_bloque:
        bwrap.append("--new-session")
    bwrap += ["--ro-bind", "/usr", "/usr", "--ro-bind", "/etc", "/etc"]
    for nom in ("bin", "sbin", "lib", "lib32", "lib64"):
        chemin = Path("/") / nom
        if chemin.is_symlink():
            bwrap += ["--symlink", os.readlink(chemin), str(chemin)]
        elif chemin.is_dir():
            bwrap += ["--ro-bind", str(chemin), str(chemin)]
    bwrap += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--tmpfs", "/home", "--tmpfs", "/run",
              "--ro-bind", "/sys/fs/cgroup", "/sys/fs/cgroup",
              "--bind", str(KIT / "espace"), "/travail",
              "--bind", str(ICI / "maison"), "/home/agent",
              "--ro-bind", str(ICI / "harnais"), "/opt/harnais",
              "--ro-bind", str(KIT / "verifier"), "/kit",
              "--ro-bind", str(sockets), "/run/kit",
              "--ro-bind", str(ICI / "passerelle.py"), "/opt/passerelle.py",
              "--remount-ro", "/", "--chdir", "/travail", "--clearenv"]
    environnement = {
        "HOME": "/home/agent", "USER": "agent", "LANG": "C.UTF-8", "TERM": os.environ.get("TERM", "xterm"),
        "PATH": "/opt/harnais/bin:/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin",
        "OPENAI_BASE_URL": "http://127.0.0.1:8080/v1", "OPENAI_API_BASE": "http://127.0.0.1:8080/v1",
        "OPENAI_API_KEY": reglages["CLE_RELAIS"], "MODELE": reglages["IAG_MODELE"],
        "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost",
        "NODE_EXTRA_CA_CERTS": "/etc/ssl/certs/ca-certificates.crt",
    }
    for variable in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        environnement[variable] = "http://127.0.0.1:3128"
    for cle, valeur in environnement.items():
        bwrap += ["--setenv", cle, valeur]
    return bwrap + ["python3", "-I", "/opt/passerelle.py", "--"] + (commande or ["bash"])


def main():
    if not shutil.which("bwrap"):
        arreter("bubblewrap (bwrap) introuvable ; l'installer (paquet bubblewrap).")
    if not (KIT / ".env").exists():
        arreter("fichier .env absent ; lancer d'abord bash preparer.sh")
    reglages = lire_reglages()
    for cle in ("IAG_URL", "IAG_CLE", "IAG_MODELE", "CLE_RELAIS"):
        if not reglages.get(cle):
            arreter(f"{cle} vide dans .env ; compléter .env puis lancer bash preparer.sh")
    for dossier in (JOURNAUX, KIT / "espace", ICI / "maison", ICI / "harnais" / "bin"):
        dossier.mkdir(parents=True, exist_ok=True)
    verrou = open(ICI / ".verrou", "w")
    try:
        fcntl.flock(verrou, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        arreter("une session est déjà ouverte ; une seule à la fois.")

    # Sockets dans un dossier temporaire privé (0700) au chemin court (limite de 108 caractères).
    sockets = Path(tempfile.mkdtemp(prefix="kit-", dir=os.environ.get("XDG_RUNTIME_DIR")))
    base = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "JOURNAUX": str(JOURNAUX)}
    reseau = {k: reglages[k] for k in ("HTTPS_PROXY", "NO_PROXY", "SSL_CERT_FILE") if reglages.get(k)}
    services = []
    try:
        # Le relais reçoit les réglages du portail ; le filtre, seulement ceux qui le concernent.
        demarrer("relais", "portail.py", {**base, **reglages, "ECOUTE": str(sockets / "relais.sock")},
                 sockets / "relais.sock", services)
        demarrer("filtre", "filtre.py", {
            **base, **reseau, "ECOUTE": str(sockets / "filtre.sock"),
            "DOMAINES_AUTORISES": reglages.get("DOMAINES_AUTORISES") or "pypi.org,files.pythonhosted.org,registry.npmjs.org",
            "QUOTA_TELECHARGEMENT_MO": reglages.get("QUOTA_TELECHARGEMENT_MO") or "5000"},
            sockets / "filtre.sock", services)
        # L'environnement de la machine sert à systemd-run ; bwrap le vide (--clearenv) avant la cage.
        session = subprocess.Popen(limites_systemd(reglages) + cage(reglages, sys.argv[1:], sockets))
        signal.signal(signal.SIGINT, signal.SIG_IGN)   # Ctrl+C reste destiné au harnais
        code = session.wait()
    finally:
        for processus in services:
            processus.terminate()
            processus.wait(10)
        shutil.rmtree(sockets, ignore_errors=True)
    sys.exit(code)


if __name__ == "__main__":
    main()
