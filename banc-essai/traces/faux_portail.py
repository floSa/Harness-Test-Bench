"""Faux point d'accès compatible OpenAI, pour vérifier la configuration du relais sans rien dépenser.

    python3 banc-essai/traces/faux_portail.py [port, 4198 par défaut]

Répond « OK » à tout POST sur .../chat/completions et affiche, pour chaque requête reçue du relais,
le chemin appelé, la présence d'une clé (jamais sa valeur), les en-têtes ajoutés par la
configuration (X-*), le nom de modèle transmis et les champs du corps. Écoute sur 127.0.0.1
seulement. Le relais doit alors être lancé avec `api_base: http://127.0.0.1:<port>/v1` et le réseau
de l'hôte (voir documentations/adapter-point-d-acces.md, section 6). Bibliothèque standard seulement.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4198


class Portail(BaseHTTPRequestHandler):
    def do_POST(self):
        corps = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        print(json.dumps({
            "chemin": self.path,
            "cle_presente": self.headers.get("Authorization", "").startswith("Bearer "),
            "entetes_x": {k: v for k, v in self.headers.items() if k.lower().startswith("x-")},
            "modele": corps.get("model"),
            "champs": sorted(corps),
            "outils": len(corps.get("tools") or []),
        }, ensure_ascii=False), flush=True)
        reponse = {"id": "faux", "object": "chat.completion", "created": 0, "model": corps.get("model"),
                   "choices": [{"index": 0, "finish_reason": "stop",
                                "message": {"role": "assistant", "content": "OK"}}],
                   "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}}
        octets = json.dumps(reponse).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(octets)))
        self.end_headers()
        self.wfile.write(octets)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"faux point d'accès : http://127.0.0.1:{PORT}/v1", flush=True)
    HTTPServer(("127.0.0.1", PORT), Portail).serve_forever()
