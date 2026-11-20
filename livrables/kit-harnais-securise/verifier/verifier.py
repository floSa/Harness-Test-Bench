"""Vérifie, depuis l'intérieur du conteneur du harnais, que chaque protection du kit est en place.

    docker compose run --rm harnais python3 /kit/verifier.py            sans appel payant
    docker compose run --rm harnais python3 /kit/verifier.py --appel    plus un vrai appel au modèle

Chaque ligne : la protection, le résultat attendu, le résultat obtenu, CONFORME ou NON CONFORME.
Code de sortie 0 si tout est conforme. Bibliothèque standard seulement.
"""
import json
import os
import socket
import sys
import urllib.error
import urllib.request

RELAIS = os.environ.get("OPENAI_BASE_URL", "http://relais:8080/v1")
CLE = os.environ.get("OPENAI_API_KEY", "")
MODELE = os.environ.get("MODELE", "")
resultats = []


def noter(protection, attendu, obtenu, conforme):
    resultats.append(conforme)
    print(f"{'CONFORME    ' if conforme else 'NON CONFORME'} | {protection} | attendu : {attendu} | obtenu : {obtenu}")


def statut_http(methode, url, corps=None, cle=CLE, delai=30):
    """Code HTTP d'une requête au relais (sans passer par le filtre)."""
    entetes = {"Content-Type": "application/json"}
    if cle:
        entetes["Authorization"] = f"Bearer {cle}"
    req = urllib.request.Request(url, method=methode, headers=entetes,
                                 data=None if corps is None else json.dumps(corps).encode())
    ouvreur = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with ouvreur.open(req, timeout=delai) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def tunnel(hote):
    """Demande au filtre un tunnel HTTPS vers hote ; renvoie la ligne de statut."""
    try:
        s = socket.create_connection(("filtre", 3128), timeout=15)
        s.sendall(f"CONNECT {hote}:443 HTTP/1.1\r\nHost: {hote}:443\r\n\r\n".encode())
        ligne = s.recv(200).split(b"\r\n", 1)[0].decode(errors="replace")
        s.close()
        return ligne
    except OSError as e:
        return f"erreur {type(e).__name__}"


def connexion_directe(hote, port):
    try:
        socket.create_connection((hote, port), timeout=5).close()
        return "ouverte"
    except OSError as e:
        return f"impossible ({type(e).__name__})"


# 1. Identité et droits
noter("utilisateur sans droits d'administration", "uid différent de 0", f"uid {os.getuid()}", os.getuid() != 0)
statut = dict(l.split(":", 1) for l in open("/proc/self/status") if ":" in l)
noter("aucun privilège noyau", "CapEff = 0", statut["CapEff"].strip(), int(statut["CapEff"], 16) == 0)
noter("aucun gain de droits possible", "NoNewPrivs = 1", statut["NoNewPrivs"].strip(), statut["NoNewPrivs"].strip() == "1")

# 2. Fichiers
try:
    open("/usr/local/bin/essai-ecriture", "w").close()
    obtenu = "écriture réussie"
except OSError:
    obtenu = "écriture refusée"
noter("système de l'image en lecture seule", "écriture refusée", obtenu, obtenu == "écriture refusée")
try:
    with open("/travail/.verif-ecriture", "w") as f:
        f.write("x")
    os.remove("/travail/.verif-ecriture")
    obtenu = "écriture réussie"
except OSError:
    obtenu = "écriture refusée"
noter("espace de travail modifiable", "écriture réussie", obtenu, obtenu == "écriture réussie")
noter("socket Docker absente (pas de contrôle de la machine)", "absente",
      "présente" if os.path.exists("/var/run/docker.sock") else "absente", not os.path.exists("/var/run/docker.sock"))
visibles = sorted(os.listdir("/home"))
noter("aucun dossier personnel de la machine visible", "/home = [agent]", f"/home = {visibles}", visibles == ["agent"])
noter("réglages et clés du kit invisibles", ".env absent de /travail et de /kit",
      "absent" if not any(os.path.exists(p) for p in ("/travail/.env", "/kit/.env")) else "présent",
      not any(os.path.exists(p) for p in ("/travail/.env", "/kit/.env")))

# 3. Ressources
try:
    memoire = open("/sys/fs/cgroup/memory.max").read().strip()
except OSError:
    memoire = "illisible"
noter("mémoire plafonnée", "un nombre d'octets", memoire, memoire.isdigit())
try:
    processus = open("/sys/fs/cgroup/pids.max").read().strip()
except OSError:
    processus = "illisible"
noter("nombre de processus plafonné", "un nombre", processus, processus.isdigit())

# 4. Secrets
suspects = [k for k in os.environ if k.startswith("IAG_") or k in ("CLE_RELAIS",)]
noter("clé du portail absente de l'environnement", "aucune variable IAG_*", suspects or "aucune", not suspects)
noter("clé locale du relais fournie au harnais", "OPENAI_API_KEY commence par relais-",
      "oui" if CLE.startswith("relais-") else "non", CLE.startswith("relais-"))

# 5. Réseau
noter("aucune sortie directe vers Internet (IP)", "impossible", connexion_directe("1.1.1.1", 443),
      connexion_directe("1.1.1.1", 443).startswith("impossible"))
noter("aucune sortie directe vers Internet (nom)", "impossible", connexion_directe("pypi.org", 443),
      connexion_directe("pypi.org", 443).startswith("impossible"))
ligne = tunnel("example.com")
noter("filtre : domaine non autorisé refusé", "403", ligne, " 403" in ligne)
ligne = tunnel("pypi.org")
noter("filtre : domaine autorisé accepté (pypi.org)", "200", ligne, " 200" in ligne)

# 6. Relais
code, _ = statut_http("GET", RELAIS + "/models")
noter("relais : liste des modèles avec la clé locale", "200", code, code == 200)
code, _ = statut_http("GET", RELAIS + "/models", cle="relais-fausse")
noter("relais : fausse clé refusée", "401", code, code == 401)
code, _ = statut_http("POST", RELAIS + "/files", {})
noter("relais : route hors appel au modèle refusée", "404", code, code == 404)
code, _ = statut_http("POST", RELAIS + "/chat/completions",
                      {"model": "modele-non-autorise", "messages": [{"role": "user", "content": "x"}]})
noter("relais : modèle non autorisé refusé", "403", code, code == 403)

if "--appel" in sys.argv:
    code, corps = statut_http("POST", RELAIS + "/chat/completions",
                              {"model": MODELE, "max_tokens": 20,
                               "messages": [{"role": "user", "content": "Réponds seulement : OK"}]}, delai=120)
    try:
        texte = json.loads(corps)["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        texte = corps[:200].decode(errors="replace")
    noter(f"appel réel au modèle {MODELE} par le relais", "200", f"{code}, réponse {texte!r}", code == 200)

n = sum(resultats)
print(f"\nBilan : {n} sur {len(resultats)} protections conformes.")
sys.exit(0 if n == len(resultats) else 1)
