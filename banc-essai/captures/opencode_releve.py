"""Relevé des écrans en terminal du manuel d'OpenCode (étape 1 : écrans bruts, sans annotation).

    python3 banc-essai/captures/opencode_releve.py

Prérequis : LiteLLM du banc démarré. Crée la clé « manuel-opencode » (supprimée à la fin), un projet
d'exemple /tmp/manuel/dosage (copie du paquet de la tâche jouet) et un dossier personnel neutre
/tmp/manuel/home. Les écrans vont dans banc-essai/resultats/captures/opencode/<chapitre>/.
L'étape 2 (annotations et rendu) est opencode_annoter.py.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terminal import Terminal, RACINE  # noqa: E402

IMG = "documentations/manuels/opencode/img"
MANUEL = Path("/tmp/manuel")
PROJET, MAISON = MANUEL / "dosage", MANUEL / "home"
CHEMIN_DEPOT = str(RACINE)
# Invite neutre : le chemin du dépôt s'affiche « ~/Harness-Test-Bench », sans nom d'utilisateur.
PS1 = r'$(pwd | sed "s#^' + str(RACINE.parent) + r'#~#")\$ '


def preparer():
    if MANUEL.exists():
        shutil.rmtree(MANUEL)
    MAISON.mkdir(parents=True)
    shutil.copytree(RACINE / "banc-essai/recettes/jouet", PROJET, ignore=shutil.ignore_patterns("consignes.md", "soumettre.py"))
    # configuration de la syntaxe en ligne (version 2), pour l'écran d'erreur du chapitre 09
    (MANUEL / "home-v2/.config/opencode").mkdir(parents=True)
    (MANUEL / "home-v2/.config/opencode/opencode.json").write_text(
        '{\n  "model": "banc/deepseek-v4.1-flash",\n  "providers": {\n    "banc": {\n'
        '      "package": "@opencode/ai/providers/openai-compatible",\n'
        '      "settings": {"baseURL": "http://127.0.0.1:4100/v1"},\n'
        '      "models": {"deepseek-v4.1-flash": {}}\n    }\n  }\n}\n')


def bash(nom, largeur=120, hauteur=34, **autres):
    env = {"HOME": str(MAISON), "PATH": "/usr/bin:/bin", "TERM": "xterm-256color", "COLORTERM": "truecolor",
           "PS1": PS1, "LANG": "C.UTF-8"} | autres
    t = Terminal(nom, largeur, hauteur, CHEMIN_DEPOT, env)
    t.lancer(["bash", "--noprofile", "--norc"])
    t.attendre(r"\$ $|\$\s*$", 10)
    return t


def cmd(t, texte, attendre=None, delai=120, stable=1.5):
    t.taper(texte, entree=True)
    if attendre:
        t.attendre(attendre, delai)
    t.attendre_stable(stable, delai)


def main():
    preparer()
    shutil.rmtree(RACINE / "harnais/opencode/installe", ignore_errors=True)

    # 02. Installer
    t = bash("oc02")
    cmd(t, "harnais/opencode/installer.sh", "installé dans", 300)
    cmd(t, "harnais/opencode/installe/opencode --version", r"1\.19")
    t.capturer(f"{IMG}/02-installer/01-installer.png")
    t.fermer()

    # 03. Brancher le modèle
    t = bash("oc03", 120, 46)
    cmd(t, 'export PATH="$PWD/harnais/opencode/installe:$PATH"')
    cmd(t, "export BANC_MODELE_URL=http://127.0.0.1:4100 BANC_MODELE=deepseek-v4.1-flash")
    cmd(t, "harnais/opencode/configurer.sh", "configuration écrite")
    cmd(t, "cat ~/.config/opencode/opencode.json", "webfetch")
    t.capturer(f"{IMG}/03-brancher-un-modele/01-configuration.png")
    cmd(t, "clear")
    cmd(t, "python3 banc-essai/traces/cles.py manuel-opencode", "clé")
    cmd(t, "set -a; . banc-essai/traces/secrets/cle-manuel-opencode.env; set +a")
    cmd(t, "opencode models banc", "banc/deepseek")
    t.capturer(f"{IMG}/03-brancher-un-modele/02-modeles.png")

    # 04. Première tâche, dans le projet d'exemple
    cmd(t, "clear")
    cmd(t, "cd /tmp/manuel/dosage && ls -R")
    t.capturer(f"{IMG}/04-premiere-tache/01-projet.png")
    t.fermer()
    t = bash("oc04", 140, 40)
    cmd(t, 'export PATH="$PWD/harnais/opencode/installe:$PATH"; set -a; . banc-essai/traces/secrets/cle-manuel-opencode.env; set +a; cd /tmp/manuel/dosage; clear')
    t.taper("opencode", entree=True)
    t.attendre("Ask anything", 60); t.attendre_stable(2)
    t.capturer(f"{IMG}/04-premiere-tache/02-accueil.png")
    t.taper('Corrige le bug : vers_ml(250, "µl") renvoie 250000.0 au lieu de 0.25. Vérifie ensuite par un petit essai en Python.')
    t.attendre_stable(1.5)
    t.capturer(f"{IMG}/04-premiere-tache/03-demande.png")
    t.touche("Enter")
    try:
        t.attendre("esc", 40)
    except TimeoutError:
        pass
    time.sleep(4)
    t.capturer(f"{IMG}/04-premiere-tache/04-en-cours.png")
    t.attendre_stable(8, 400)
    t.capturer(f"{IMG}/04-premiere-tache/05-resultat.png")

    # 05. Agents, commandes, modèles (même session)
    t.touche("Tab"); time.sleep(1.5)
    t.capturer(f"{IMG}/05-agents-et-commandes/01-agent-plan.png")
    t.touche("Tab"); time.sleep(1)
    t.touche("C-p"); time.sleep(2)
    t.capturer(f"{IMG}/05-agents-et-commandes/02-palette.png")
    t.touche("Escape"); time.sleep(1)
    t.taper("/"); time.sleep(2)
    t.capturer(f"{IMG}/05-agents-et-commandes/03-commandes.png")
    t.taper("models"); time.sleep(1); t.touche("Enter"); time.sleep(2.5)
    t.capturer(f"{IMG}/05-agents-et-commandes/04-modeles.png")
    t.touche("Escape"); time.sleep(1)
    t.taper("/s"); time.sleep(2)
    t.capturer(f"{IMG}/05-agents-et-commandes/05-commandes-s.png")
    t.touche("Escape"); time.sleep(0.5); t.touche("BSpace", "BSpace"); time.sleep(1)
    t.taper("/exit"); time.sleep(1); t.touche("Enter"); time.sleep(2)
    t.fermer()

    # 06. Sans interaction
    t = bash("oc06", 120, 34)
    cmd(t, 'export PATH="$PWD/harnais/opencode/installe:$PATH"; set -a; . banc-essai/traces/secrets/cle-manuel-opencode.env; set +a; cd /tmp/manuel/dosage; clear')
    cmd(t, 'opencode run "Combien de fichiers Python contient ce dossier ? Réponds en une phrase." < /dev/null', None, 180, 6)
    t.capturer(f"{IMG}/06-sans-interaction/01-run.png")
    cmd(t, "clear")
    cmd(t, 'opencode run --format json "Réponds seulement : OK" < /dev/null | cut -c1-112 | head -12', None, 180, 6)
    t.capturer(f"{IMG}/06-sans-interaction/02-json.png")
    cmd(t, "clear")
    cmd(t, "opencode session list", "ses_")
    t.capturer(f"{IMG}/06-sans-interaction/03-sessions.png")
    t.fermer()

    # 08. Dans le banc
    t = bash("oc08", 120, 40, HOME=os.environ["HOME"],
             PATH=f"{os.environ['HOME']}/.local/bin:/usr/lib/wsl/lib:/usr/bin:/bin")
    cmd(t, "banc-essai/cage/lancer.sh opencode jouet --essai manuel-opencode-jouet --duree 1800 | cut -c1-118 | head -3", "essai manuel", 900, 5)
    cmd(t, "python3 -m json.tool banc-essai/resultats/manuel-opencode-jouet/essai.json | head -26")
    t.capturer(f"{IMG}/08-dans-le-banc/01-essai.png")
    t.fermer()

    # 09. En cas de problème
    t = bash("oc09", 120, 30)
    cmd(t, 'export PATH="$PWD/harnais/opencode/installe:$PATH"; clear')
    cmd(t, "HOME=/tmp/manuel/home-v2 opencode models banc", "Provider not found")
    t.capturer(f"{IMG}/09-en-cas-de-probleme/01-fournisseur-introuvable.png")
    cmd(t, "clear")
    cmd(t, 'grep -h -o -E "message=\\"[^\\"]*\\"[^ ]* error=.{0,60}|Failed to fetch models.dev" banc-essai/resultats/opencode-jouet-1/harnais/stderr.log | cut -c1-118')
    t.capturer(f"{IMG}/09-en-cas-de-probleme/02-reseau-refuse.png")
    t.fermer()

    subprocess.run([sys.executable, str(RACINE / "banc-essai/traces/cles.py"), "--supprimer", "manuel-opencode"])
    print("relevé terminé")


if __name__ == "__main__":
    main()
