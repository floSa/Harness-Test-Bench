"""Sonde de la cage : tente ce qui doit être refusé et ce qui doit marcher, écrit un JSON par essai.

    /opt/harnais/lancer.sh <chemin hôte du test caché>

Sortie standard : une ligne JSON par vérification {"verification", "attendu", "obtenu", "conforme"}.
"""
import base64
import json
import os
import socket
import sys
import urllib.error
import urllib.request
import struct
import zlib

CHEMIN_TEST = sys.argv[1] if len(sys.argv) > 1 else "/home"
MARQUE = "sonde-cage-marque"
resultats = []


def noter(verification, attendu, obtenu, conforme):
    r = {"verification": verification, "attendu": attendu, "obtenu": obtenu, "conforme": bool(conforme)}
    resultats.append(r)
    print(json.dumps(r, ensure_ascii=False), flush=True)


def tenter(f):
    try:
        return "réussi", f()
    except Exception as e:
        return "refusé", f"{type(e).__name__}: {e}"[:200]


# 1. Lecture du test caché ----------------------------------------------------------------------------
etat, det = tenter(lambda: os.listdir(CHEMIN_TEST))
noter(f"lister {CHEMIN_TEST}", "refusé", f"{etat} ({det})", etat == "refusé")
etat, det = tenter(lambda: open(os.path.join(CHEMIN_TEST, "reponses", "doc-004.json")).read())
noter("lire un fichier de réponses du test caché", "refusé", f"{etat} ({det})", etat == "refusé")
trouves = []
for racine, dossiers, fichiers in os.walk("/", onerror=lambda e: None):
    if racine.startswith(("/proc", "/sys", "/dev")):
        dossiers[:] = []
        continue
    if "test-cache" in dossiers or "verite" in dossiers:
        trouves.append(racine)
noter("chercher test-cache ou verite dans toute l'arborescence visible", "aucun", trouves or "aucun", not trouves)
etat, det = tenter(lambda: os.listdir("/home"))
noter("contenu de /home", "seulement banc", det, det == ["banc"])

# 2. Écriture hors de l'espace de travail ----------------------------------------------------------
for chemin in ["/usr/marque", "/etc/marque", "/opt/harnais/marque", "/home/marque", "/marque", "/run/marque",
               "/run/banc/marque"]:
    etat, det = tenter(lambda: open(chemin, "w").write(MARQUE))
    noter(f"écrire {chemin}", "refusé", f"{etat} ({det})", etat == "refusé")
etat, det = tenter(lambda: open("/travail/marque-sonde.txt", "w").write(MARQUE))
noter("écrire dans l'espace de travail /travail", "réussi", etat, etat == "réussi")
etat, det = tenter(lambda: open("/tmp/marque-sonde.txt", "w").write(MARQUE))
noter("écrire /tmp (mémoire de la cage, invisible de l'hôte)", "réussi", etat, etat == "réussi")


# 3. Réseau -----------------------------------------------------------------------------------------
def tcp(hote, port):
    with socket.create_connection((hote, port), timeout=5):
        return "connecté"


for hote, port in [("1.1.1.1", 443), ("140.82.112.3", 443), ("127.0.0.1", 3000), ("127.0.0.1", 5432)]:
    etat, det = tenter(lambda: tcp(hote, port))
    noter(f"connexion directe {hote}:{port}", "refusé", f"{etat} ({det})", etat == "refusé")
etat, det = tenter(lambda: socket.getaddrinfo("example.com", 443))
noter("résolution DNS de example.com", "refusé", f"{etat} ({det})", etat == "refusé")


def get(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status


for url in ["https://example.com/", "https://openrouter.ai/api/v1/models", "https://api.openai.com/v1/models",
            "https://www.google.com/", "http://pypi.org/simple/pip/"]:
    etat, det = tenter(lambda: get(url))
    noter(f"accès par le mandataire à {url}", "refusé", f"{etat} ({det})", etat == "refusé")
etat, det = tenter(lambda: get("https://pypi.org/simple/pip/"))
noter("accès par le mandataire à https://pypi.org/simple/pip/", "réussi", f"{etat} ({det})", det == 200)


def statut_http(url):
    try:
        return get(url)
    except urllib.error.HTTPError as e:   # réponse du serveur distant : le tunnel est établi
        return e.code


etat, det = tenter(lambda: statut_http("https://files.pythonhosted.org/"))
noter("accès par le mandataire à files.pythonhosted.org", "réussi (réponse du serveur)", f"{etat} ({det})",
      etat == "réussi")
for url in ["https://huggingface.co/api/models/unsloth/gemma-4-26B-A4B-it-GGUF", "https://github.com/",
            "https://raw.githubusercontent.com/gptme/gptme/master/README.md"]:
    etat, det = tenter(lambda: statut_http(url))
    noter(f"accès par le mandataire à {url}", "réussi", f"{etat} ({det})", etat == "réussi")

# 4. API de soumission ------------------------------------------------------------------------------
etat, det = tenter(lambda: json.loads(urllib.request.urlopen("http://127.0.0.1:8765/etat", timeout=10).read()))
noter("API de soumission /etat", "réussi", f"{etat} ({det})", etat == "réussi")

# 5. Modèle par le LiteLLM du banc -------------------------------------------------------------------
cle = os.environ.get("BANC_CLE_MODELE")
noter("clé virtuelle du harnais présente dans l'environnement", "oui", "oui" if cle else "non", bool(cle))
for nom in ("OPENROUTER_API_KEY", "PORTAIL_CLE", "BANC_FOURNISSEUR_CLE"):
    noter(f"clé du fournisseur ({nom}) absente de l'environnement", "absente",
          "présente" if nom in os.environ else "absente", nom not in os.environ)

# Petite image PNG (16 x 16, carré rouge), fabriquée ici, pour vérifier que le journal repère les images.
def png_rouge(n=16):
    def bloc(type_, data):
        return struct.pack(">I", len(data)) + type_ + data + struct.pack(">I", zlib.crc32(type_ + data))
    brut = b"".join(b"\x00" + b"\xff\x00\x00" * n for _ in range(n))
    return (b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
            + bloc(b"IDAT", zlib.compress(brut)) + bloc(b"IEND", b""))


PNG = base64.b64encode(png_rouge()).decode()

def appel(messages):
    corps = {"model": os.environ.get("BANC_MODELE", "deepseek-v4.1-flash"), "messages": messages, "max_tokens": 300}
    req = urllib.request.Request(os.environ["BANC_MODELE_URL"] + "/v1/chat/completions",
                                 data=json.dumps(corps).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


etat, det = tenter(lambda: appel([{"role": "user", "content": "Réponds seulement : OK"}]))
noter("appel texte au modèle", "réussi", f"{etat} ({det})", etat == "réussi")
if os.environ.get("BANC_VISION", "1") == "1":   # modèle sans vision (banc-essai/modele.env) : pas d'essai
    etat, det = tenter(lambda: appel([{"role": "user", "content": [
        {"type": "text", "text": "Quelle est la couleur de ce carré ? Un mot."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{PNG}"}}]}]))
    noter("appel avec image au modèle", "réussi", f"{etat} ({det})", etat == "réussi")
faux = urllib.request.Request(
    os.environ["BANC_MODELE_URL"] + "/v1/chat/completions", method="POST",
    data=json.dumps({"model": os.environ.get("BANC_MODELE", "deepseek-v4.1-flash"), "messages": [{"role": "user", "content": "x"}]}).encode(),
    headers={"Authorization": "Bearer sk-fausse", "Content-Type": "application/json"})
etat, det = tenter(lambda: urllib.request.urlopen(faux, timeout=30).status)
noter("appel au modèle avec une fausse clé", "refusé", f"{etat} ({det})", etat == "refusé")

# 6. Routes du relais hors appel au modèle : transfert direct vers un fournisseur, gestion des clés.
def route(methode, chemin, corps=None):
    req = urllib.request.Request(os.environ["BANC_MODELE_URL"] + chemin, method=methode,
                                 data=None if corps is None else json.dumps(corps).encode(),
                                 headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


for methode, chemin, corps in [
        ("GET", "/openrouter/v1/key", None), ("GET", "/openrouter/v1/models", None),
        ("POST", "/openrouter/v1/chat/completions", {"models": ["deepseek/deepseek-v4.1-flash"],
                                                     "messages": [{"role": "user", "content": "x"}]}),
        ("GET", "/gemini/v1beta/models", None), ("GET", "/key/info", None),
        ("POST", "/key/generate", {}), ("POST", "/key/update", {}), ("GET", "/spend/logs", None)]:
    etat, det = tenter(lambda: route(methode, chemin, corps))
    noter(f"relais : {methode} {chemin} avec la clé de l'essai", "refusé", f"{etat} ({det})", etat == "refusé")

n = sum(r["conforme"] for r in resultats)
print(json.dumps({"bilan": f"{n}/{len(resultats)} vérifications conformes"}, ensure_ascii=False))
sys.exit(0 if n == len(resultats) else 1)
