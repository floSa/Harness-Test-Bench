"""Exécutant des cas cachés de la tâche jouet, lancé dans la cage (sans réseau).

    python3 -I -B /opt/jouet/executant.py

Lit /opt/jouet/appels.json ({"marque": ..., "appels": [{"fonction", "args"}]}) : les appels
seulement, jamais les valeurs attendues, qui restent hors de la cage. Importe le paquet soumis
depuis /travail, exécute chaque appel et écrit une ligne « <marque> <JSON> » : pour chaque appel,
la valeur obtenue ou la lignée de l'exception levée. La comparaison se fait hors de la cage.
"""
import importlib
import json
import sys

sys.path.insert(0, "/travail")
donnees = json.load(open("/opt/jouet/appels.json"))
paquet = donnees["paquet"]
resultats = []
try:
    module = importlib.import_module(paquet)
    erreur_import = None
except BaseException as e:  # noqa: BLE001 - tout échec d'import compte faux
    module, erreur_import = None, f"{type(e).__name__}: {e}"[:200]
for a in donnees["appels"]:
    if module is None:
        resultats.append({"erreur": erreur_import})
        continue
    try:
        v = getattr(module, a["fonction"])(*a["args"])
        try:
            v = float(v)
        except (TypeError, ValueError, OverflowError):
            v = repr(v)[:200]
        resultats.append({"valeur": v})
    except BaseException as e:  # noqa: BLE001
        resultats.append({"exception": [c.__name__ for c in type(e).__mro__]})
sys.stdout.write(donnees["marque"] + " " + json.dumps(resultats) + "\n")
sys.stdout.flush()
