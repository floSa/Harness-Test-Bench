"""Rend les captures de terminal en images annotées (dans le conteneur Playwright, voir lancer.sh).

    banc-essai/captures/lancer.sh banc-essai/captures/rendre.py [scenario.jsonl]

Pour chaque entrée du scénario (écrit par terminal.py) : ouvre la page HTML de l'écran, entoure
les cibles (.cible-1, .cible-2…) d'un rectangle rouge avec pastille numérotée (annoter.py), et
enregistre l'image recadrée sur la fenêtre du terminal.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import annoter

RACINE = Path("/depot")
scenario = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "banc-essai/resultats/captures/scenario.jsonl"
entrees = [json.loads(l) for l in scenario.read_text().splitlines() if l.strip()]
with sync_playwright() as p:
    nav = p.chromium.launch()
    page = nav.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    for e in entrees:
        page.goto((RACINE / e["html"]).as_uri())
        page.wait_for_selector("#ecran")
        cibles = [(page.locator(f".cible-{n}"), lib) for n, lib in enumerate(e["libelles"], 1)]
        fenetre = page.locator(".fenetre").bounding_box()
        clip = {"x": 0, "y": 0, "width": fenetre["x"] + fenetre["width"] + 18,
                "height": fenetre["y"] + fenetre["height"] + 18}
        page.set_viewport_size({"width": max(1440, int(clip["width"]) + 1), "height": max(900, int(clip["height"]) + 1)})
        annoter.capture(page, RACINE / e["image"], cibles, clip=clip)
    nav.close()
