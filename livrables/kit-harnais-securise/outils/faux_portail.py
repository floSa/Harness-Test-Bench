"""Faux portail compatible OpenAI : permet de vérifier tout le kit sans clé du portail et sans dépense.

Lancé par `docker compose --profile essai up -d faux-portail` ; dans .env :
IAG_URL=http://faux-portail:4198/v1, IAG_CLE=cle-factice, IAG_MODELE=modele-factice.

Répond « OK » (en flux ou non) à toute requête POST .../chat/completions et affiche sur sa sortie,
pour chaque requête reçue du relais : chemin, présence de la clé du portail (jamais sa valeur), en-têtes
X-*, modèle, champs du corps. Lecture : `docker compose logs faux-portail`.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Portail(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_POST(self):
        corps = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        print(json.dumps({"chemin": self.path, "cle_du_portail_recue": "Authorization" if self.headers.get("Authorization") == "Bearer cle-factice"
                          else "api-key" if self.headers.get("api-key") == "cle-factice" else "non",
                          "entetes_x": {k: v for k, v in self.headers.items() if k.lower().startswith("x-")},
                          "modele": corps.get("model"), "champs": sorted(corps)}, ensure_ascii=False), flush=True)
        usage = {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}
        if corps.get("stream"):
            morceaux = [{"choices": [{"index": 0, "delta": {"role": "assistant", "content": "O"}}]},
                        {"choices": [{"index": 0, "delta": {"content": "K"}, "finish_reason": "stop"}]}]
            if (corps.get("stream_options") or {}).get("include_usage"):
                morceaux.append({"choices": [], "usage": usage})
            texte = "".join(f"data: {json.dumps(dict(m, id='faux', object='chat.completion.chunk', model=corps.get('model')))}\n\n"
                            for m in morceaux) + "data: [DONE]\n\n"
            octets, type_ = texte.encode(), "text/event-stream"
        else:
            octets = json.dumps({"id": "faux", "object": "chat.completion", "created": 0, "model": corps.get("model"),
                                 "choices": [{"index": 0, "finish_reason": "stop",
                                              "message": {"role": "assistant", "content": "OK"}}],
                                 "usage": usage}).encode()
            type_ = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(octets)))
        self.end_headers()
        self.wfile.write(octets)


if __name__ == "__main__":
    print("faux portail prêt : http://faux-portail:4198/v1", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 4198), Portail).serve_forever()
