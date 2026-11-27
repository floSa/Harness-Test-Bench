"""Vérifie, sans passer par le banc, ce que le fournisseur du modèle sait faire.

    python3 banc-essai/traces/verifier_portail.py [--modele NOM] [--url URL] [--variable-cle NOM]

Appelle directement le fournisseur choisi dans banc-essai/modele.env (adresse et clé lues dans .env :
PORTAIL_URL et PORTAIL_CLE, ou OPENROUTER_API_KEY), par le mandataire BANC_MANDATAIRE et avec le
certificat BANC_CERTIFICAT s'ils sont définis dans .env. Sept vérifications, dans l'ordre :

    1. liste des modèles (GET /models) et présence du modèle demandé
    2. appel simple
    3. appel avec outil (tool calling) : indispensable, les harnais ne travaillent que par outils
    4. réponse en flux (streaming) : indispensable pour OpenCode, Goose, Cline et Pi
    5. flux avec appel d'outil : forme exacte utilisée par les harnais
    6. lecture d'une image (vision) : facultative, à reporter dans BANC_VISION
    7. jetons comptés dans la réponse (usage) : sans eux, ni coût ni plafond

La clé n'est jamais affichée ; les messages d'erreur du fournisseur sont tronqués et toute chaîne
qui ressemble à une clé est masquée. Rapport écrit dans banc-essai/traces/journaux/verification-portail.json
(hors git). Code de sortie 0 si les vérifications indispensables (1 à 5 et 7) réussissent.
Bibliothèque standard seulement ; coût : sept appels courts (400 jetons de sortie au plus : un
modèle qui raisonne avant de répondre consomme une partie de ce budget sans rien afficher).
"""
import argparse
import base64
import json
import re
import ssl
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
from generer_config import lire_modele  # noqa: E402

OUTIL = {"type": "function", "function": {
    "name": "lire_fichier", "description": "Lit un fichier du disque et renvoie son contenu.",
    "parameters": {"type": "object", "properties": {"chemin": {"type": "string"}}, "required": ["chemin"]}}}
DEMANDE_OUTIL = "Lis le fichier /tmp/notes.txt avec l'outil lire_fichier. N'écris rien d'autre."


def lire_env():
    v = {}
    f = RACINE / ".env"
    if f.exists():
        for ligne in f.read_text().splitlines():
            if "=" in ligne and not ligne.lstrip().startswith("#"):
                cle, valeur = ligne.split("=", 1)
                v[cle.strip()] = valeur.strip().strip('"').strip("'")
    return v


def masquer(texte):
    return re.sub(r"(sk-|Bearer\s+)?[A-Za-z0-9_\-]{24,}", "***", str(texte))[:300]


def png_rouge(n=16):
    def bloc(type_, data):
        return struct.pack(">I", len(data)) + type_ + data + struct.pack(">I", zlib.crc32(type_ + data))
    brut = b"".join(b"\x00" + b"\xff\x00\x00" * n for _ in range(n))
    return (b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
            + bloc(b"IDAT", zlib.compress(brut)) + bloc(b"IEND", b""))


class Client:
    def __init__(self, url, cle, mandataire=None, certificat=None):
        self.url, self.cle = url.rstrip("/"), cle
        gestionnaires = [urllib.request.ProxyHandler({"http": mandataire, "https": mandataire} if mandataire else {})]
        contexte = ssl.create_default_context(cafile=certificat) if certificat else ssl.create_default_context()
        gestionnaires.append(urllib.request.HTTPSHandler(context=contexte))
        self.ouvreur = urllib.request.build_opener(*gestionnaires)

    def requete(self, methode, chemin, corps=None, flux=False):
        req = urllib.request.Request(self.url + chemin, method=methode,
                                     data=None if corps is None else json.dumps(corps).encode(),
                                     headers={"Authorization": f"Bearer {self.cle}",
                                              "Content-Type": "application/json"})
        r = self.ouvreur.open(req, timeout=120)
        if not flux:
            return json.loads(r.read())
        evenements = []
        for ligne in r:
            ligne = ligne.decode("utf-8", "replace").strip()
            if ligne.startswith("data:"):
                donnee = ligne[5:].strip()
                if donnee == "[DONE]":
                    evenements.append("[DONE]")
                    break
                evenements.append(json.loads(donnee))
        return evenements


def essayer(nom, fonction, resultats, indispensable=True):
    t0 = time.time()
    try:
        ok, detail = fonction()
    except urllib.error.HTTPError as e:
        ok, detail = False, f"HTTP {e.code} : {masquer(e.read().decode('utf-8', 'replace'))}"
    except Exception as e:  # réseau, certificat, JSON
        ok, detail = False, f"{type(e).__name__} : {masquer(e)}"
    resultats.append({"verification": nom, "reussi": ok, "indispensable": indispensable,
                      "detail": detail, "duree_s": round(time.time() - t0, 1)})
    print(f"{'OK ' if ok else 'KO '} {'' if indispensable else '(facultatif) '}{nom} : {detail}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--modele", help="nom du modèle chez le fournisseur (défaut : BANC_MODELE_FOURNISSEUR)")
    p.add_argument("--url", help="adresse de base, avec le /v1 final (défaut : selon modele.env et .env)")
    p.add_argument("--variable-cle", help="nom de la variable de .env qui porte la clé")
    a = p.parse_args()
    m, env = lire_modele(), lire_env()
    modele = a.modele or m["BANC_MODELE_FOURNISSEUR"]
    if m["BANC_FOURNISSEUR"] == "openrouter":
        url, var = a.url or "https://openrouter.ai/api/v1", a.variable_cle or "OPENROUTER_API_KEY"
    else:
        url, var = a.url or env.get("PORTAIL_URL", ""), a.variable_cle or "PORTAIL_CLE"
    if not url or not env.get(var):
        sys.exit(f"adresse ou clé absente : URL={'oui' if url else 'non'}, {var} dans .env={'oui' if env.get(var) else 'non'}")
    print(f"fournisseur {m['BANC_FOURNISSEUR']}, adresse {url}, modèle {modele}, clé {var} (non affichée)")
    c = Client(url, env[var], env.get("BANC_MANDATAIRE") or None, env.get("BANC_CERTIFICAT") or None)
    res, usage_vu = [], {}

    def modeles():
        liste = c.requete("GET", "/models").get("data", [])
        ids = [x.get("id") for x in liste]
        info = next((x for x in liste if x.get("id") == modele), None)
        contexte = info.get("context_length") if info else None
        return modele in ids, (f"{len(ids)} modèles, « {modele} » {'présent' if modele in ids else 'ABSENT'}"
                               + (f", contexte annoncé {contexte} jetons" if contexte else "")
                               + ("" if modele in ids else f" ; exemples : {', '.join(map(str, ids[:8]))}"))

    def simple():
        r = c.requete("POST", "/chat/completions", {"model": modele, "max_tokens": 400,
                                                     "messages": [{"role": "user", "content": "Réponds seulement : OK"}]})
        usage_vu.update(r.get("usage") or {})
        texte = (r["choices"][0]["message"].get("content") or "").strip()
        return bool(texte), f"réponse « {texte[:40]} »"

    def outil():
        r = c.requete("POST", "/chat/completions", {"model": modele, "max_tokens": 400, "tools": [OUTIL],
                                                     "messages": [{"role": "user", "content": DEMANDE_OUTIL}]})
        appels = r["choices"][0]["message"].get("tool_calls") or []
        if not appels:
            return False, "aucun appel d'outil rendu (outils ignorés ou non pris en charge)"
        f = appels[0]["function"]
        return f["name"] == "lire_fichier", f"appel {f['name']}({f.get('arguments', '')[:60]})"

    def flux():
        ev = c.requete("POST", "/chat/completions", {"model": modele, "max_tokens": 400, "stream": True,
                                                      "stream_options": {"include_usage": True},
                                                      "messages": [{"role": "user", "content": "Réponds seulement : OK"}]},
                       flux=True)
        morceaux = [e for e in ev if isinstance(e, dict)]
        fin = [ch.get("finish_reason") for e in morceaux for ch in e.get("choices", []) if ch.get("finish_reason")]
        if any(e.get("usage") for e in morceaux):
            usage_vu.setdefault("flux", True)
        return bool(morceaux) and bool(fin), (f"{len(morceaux)} morceaux, fin « {fin[-1] if fin else 'ABSENTE'} », "
                                              f"[DONE] {'reçu' if '[DONE]' in ev else 'absent'}")

    def flux_outil():
        ev = c.requete("POST", "/chat/completions", {"model": modele, "max_tokens": 400, "stream": True,
                                                      "tools": [OUTIL],
                                                      "messages": [{"role": "user", "content": DEMANDE_OUTIL}]},
                       flux=True)
        noms = [tc.get("function", {}).get("name") for e in ev if isinstance(e, dict)
                for ch in e.get("choices", []) for tc in (ch.get("delta", {}).get("tool_calls") or [])]
        noms = [n for n in noms if n]
        return "lire_fichier" in noms, f"outil appelé en flux : {noms[0] if noms else 'aucun'}"

    def image():
        r = c.requete("POST", "/chat/completions", {"model": modele, "max_tokens": 400, "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Quelle est la couleur de ce carré ? Un mot."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png_rouge()).decode()}}]}]})
        texte = (r["choices"][0]["message"].get("content") or "").strip()
        return "rouge" in texte.lower() or "red" in texte.lower(), f"réponse « {texte[:40]} »"

    def jetons():
        ok = bool(usage_vu.get("prompt_tokens")) and bool(usage_vu.get("completion_tokens"))
        return ok, (f"jetons d'entrée {usage_vu.get('prompt_tokens')}, de sortie {usage_vu.get('completion_tokens')}"
                    + (", aussi en flux" if usage_vu.get("flux") else ", absents en flux (le relais les estime)"))

    essayer("liste des modèles", modeles, res)
    essayer("appel simple", simple, res)
    essayer("appel avec outil", outil, res)
    essayer("réponse en flux", flux, res)
    essayer("flux avec appel d'outil", flux_outil, res)
    essayer("lecture d'une image", image, res, indispensable=False)
    essayer("jetons comptés (usage)", jetons, res)
    vision = next(r["reussi"] for r in res if r["verification"] == "lecture d'une image")
    ok = all(r["reussi"] for r in res if r["indispensable"])
    print(f"\nbilan : {'utilisable par les harnais' if ok else 'NON utilisable en l état (voir les KO)'} ; "
          f"à reporter dans banc-essai/modele.env : BANC_VISION={1 if vision else 0}")
    (ICI / "journaux").mkdir(exist_ok=True)
    (ICI / "journaux" / "verification-portail.json").write_text(json.dumps(
        {"date": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "fournisseur": m["BANC_FOURNISSEUR"], "modele": modele,
         "utilisable": ok, "vision": vision, "resultats": res}, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
