"""Captures annotées de l'interface web d'OpenCode (chapitre 07 du manuel), dans le conteneur Playwright.

    banc-essai/captures/opencode_web.sh      (démarre `opencode web` sans accès au navigateur de
                                              Windows, lance ce scénario, arrête le serveur)

Le serveur écoute sur http://127.0.0.1:4321 ; la liste des projets est gardée par le navigateur :
le scénario ouvre le projet d'exemple /tmp/manuel/dosage puis crée une session.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import annoter

RACINE = Path("/depot")
IMG = RACINE / "documentations/manuels/opencode/img/07-interface-web"
TXT = RACINE / "banc-essai/resultats/captures/opencode/07-interface-web"
URL = "http://127.0.0.1:4321/"

with sync_playwright() as p:
    nav = p.chromium.launch()
    pg = nav.new_page(viewport={"width": 1440, "height": 900}, locale="fr-FR")
    pg.goto(URL)
    pg.get_by_text("Add project").first.wait_for()
    annoter.capture(pg, IMG / "01-accueil.png", [
        (pg.get_by_text("Add project").first, "Add project"),
        (pg.get_by_placeholder("Search sessions"), "Search sessions"),
        (pg.get_by_text("Settings").first, "Settings"),
        (pg.get_by_text("Help").first, "Help")], texte=TXT / "01-accueil.txt")

    pg.get_by_text("Add project").first.click()
    champ = pg.get_by_placeholder("Search folders")
    champ.wait_for()
    champ.fill("/tmp/manuel/dosage")
    pg.wait_for_timeout(1500)
    annoter.capture(pg, IMG / "02-ouvrir-projet.png", [
        (champ, "Search folders"),
        (pg.get_by_text("dosage", exact=True).first, "dossier dosage")], texte=TXT / "02-ouvrir-projet.txt")
    pg.keyboard.press("Enter")
    pg.get_by_text("New session").first.wait_for()
    pg.wait_for_timeout(1000)
    annoter.capture(pg, IMG / "03-projet-ouvert.png", [
        (pg.get_by_text("New session").first, "New session")], texte=TXT / "03-projet-ouvert.txt")

    pg.get_by_text("New session").first.click()
    saisie = pg.get_by_label("Prompt")
    saisie.wait_for()
    saisie.click()
    pg.keyboard.type("Combien de fichiers Python contient le dossier dosage ? Réponds en une phrase.")
    pg.wait_for_timeout(800)
    annoter.capture(pg, IMG / "04-nouvelle-session.png", [
        (saisie, "Prompt"),
        (pg.get_by_role("button", name="Add images and files"), "Add images and files"),
        (pg.get_by_role("button", name="deepseek-v4.1-flash").first, "deepseek-v4.1-flash"),
        (pg.get_by_role("button", name="Send"), "Send")], texte=TXT / "04-nouvelle-session.txt")

    pg.keyboard.press("Enter")
    pg.get_by_text("Shell").first.wait_for(timeout=120000)
    pg.get_by_text("Build · deepseek-v4.1-flash ·").last.wait_for(timeout=180000)
    pg.wait_for_timeout(2000)
    annoter.capture(pg, IMG / "05-reponse.png", [
        (pg.get_by_text("Combien de fichiers Python contient le dossier dosage").last, "question"),
        (pg.get_by_text("Shell").first, "Shell"),
        (pg.get_by_text("Build · deepseek-v4.1-flash ·").last, "Build · deepseek-v4.1-flash")],
        texte=TXT / "05-reponse.txt")
    nav.close()
print("captures web terminées")
