"""Journal du banc : une ligne JSON par appel au modèle (succès ou échec), sans aucune clé.

Champs : heure de début et de fin, durée, clé virtuelle (alias = essai), modèle, fournisseur, statut,
jetons (dont jetons lus dans le cache), coût calculé par le relais et coût facturé par le fournisseur s'il le renvoie (champ usage.cost),
nombre de messages, présence et nombre d'images, type d'erreur (429 compris).
"""
import datetime
import json
import os
import re

from litellm.integrations.custom_logger import CustomLogger

FICHIER = os.environ.get("JOURNAL_APPELS", "/journaux/appels.jsonl")


def _masquer(texte):
    """Retire de tout message d'erreur ce qui ressemble à une clé ou à son empreinte."""
    texte = re.sub(r"sk-[A-Za-z0-9_\-]{6,}", "sk-***", texte or "")
    return re.sub(r"\b[0-9a-f]{32,}\b", "***", texte)


def _images(messages):
    n = 0
    for m in messages or []:
        contenu = m.get("content") if isinstance(m, dict) else None
        if isinstance(contenu, list):
            n += sum(1 for p in contenu if isinstance(p, dict) and p.get("type") in ("image_url", "image", "input_image"))
    return n


def _champ(o, *chemin):
    """Lit o.a.b... sur un objet ou un dictionnaire ; None si absent."""
    for c in chemin:
        if o is None:
            return None
        o = o.get(c) if isinstance(o, dict) else getattr(o, c, None)
    return o


def _heure(t):
    if isinstance(t, datetime.datetime):
        return t.astimezone().isoformat(timespec="milliseconds")
    if isinstance(t, (int, float)):
        return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec="milliseconds")
    return None


class Journal(CustomLogger):
    def _ecrire(self, kwargs, response_obj, debut, fin, statut):
        try:
            slo = kwargs.get("standard_logging_object") or {}
            meta = slo.get("metadata") or {}
            messages = kwargs.get("messages") or slo.get("messages") or []
            erreur = None
            if statut == "echec":
                e = kwargs.get("exception")
                erreur = {"type": type(e).__name__ if e else None,
                          "code": getattr(e, "status_code", None),
                          "message": _masquer(str(e) if e else slo.get("error_str"))[:300]}
            d = (fin - debut).total_seconds() if isinstance(debut, datetime.datetime) and \
                isinstance(fin, datetime.datetime) else None
            ligne = {
                "debut": _heure(debut), "fin": _heure(fin), "duree_s": round(d, 3) if d is not None else None,
                "cle": meta.get("user_api_key_alias"), "modele_demande": slo.get("model_group") or kwargs.get("model"),
                "modele": slo.get("model") or kwargs.get("model"), "statut": statut,
                "jetons_entree": slo.get("prompt_tokens"), "jetons_sortie": slo.get("completion_tokens"),
                "jetons_cache": _champ(response_obj, "usage", "prompt_tokens_details", "cached_tokens"),
                "cout": slo.get("response_cost") if slo else kwargs.get("response_cost"),
                "cout_fournisseur": _champ(response_obj, "usage", "cost"),
                "fournisseur": _champ(response_obj, "provider"),
                "messages": len(messages), "images": _images(messages),
                "flux": bool(kwargs.get("stream")), "outils": len(kwargs.get("tools") or []),
                "erreur": erreur,
            }
            with open(FICHIER, "a") as f:
                f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        except Exception as e:  # le journal ne doit jamais faire échouer un appel
            with open(FICHIER + ".erreurs", "a") as f:
                f.write(f"{datetime.datetime.now().isoformat()} {type(e).__name__}: {e}\n")

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        self._ecrire(kwargs, response_obj, start_time, end_time, "succes")

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        self._ecrire(kwargs, response_obj, start_time, end_time, "echec")


journal = Journal()
