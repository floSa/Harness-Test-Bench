"""Captures d'écran d'interfaces en terminal (TUI et ligne de commande) pour les manuels des harnais.

Principe : le harnais tourne dans une session tmux de taille fixe ; l'écran est relevé avec ses
couleurs (`tmux capture-pane -e`), converti en page HTML (une cellule de caractère = une case de
grille), puis rendu et annoté par Playwright (`rendre.py`, dans le conteneur officiel, voir
`lancer.sh`) avec l'outil d'annotation de la série (`annoter.py`).

Sur l'hôte (Python standard) :

    t = Terminal("essai", largeur=150, hauteur=42, dossier="/tmp/x", env={...})
    t.lancer(["opencode"])                 # commande dans la session tmux
    t.attendre("Ask anything")             # attend un texte à l'écran
    t.taper("bonjour", entree=True)        # frappe au clavier
    t.capturer("documentations/manuels/opencode/img/03/01-accueil.png",
               cibles=[("Ask anything", "zone de saisie"), (("ligne", 0, 2), "en-tête")],
               titre="OpenCode, écran d'accueil")
    t.fermer()

`capturer` écrit la page HTML et son texte brut à côté de l'image attendue (dossier
banc-essai/resultats/captures/) et ajoute l'entrée au fichier de travail `scenario.jsonl` ;
`lancer.sh rendre.py <scenario.jsonl>` produit ensuite les images.

Cibles d'annotation : texte (« première occurrence », éventuellement (texte, n) pour la n-ième),
ou ("ligne", début, fin) pour des lignes entières, ou ("zone", l1, c1, l2, c2).
Secrets : toute chaîne qui ressemble à une clé (sk-…) est masquée dans le HTML avant le rendu.
"""
import html
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
TEXTES = RACINE / "banc-essai/resultats/captures"
CLE_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
FOND, ENCRE = "#1e1f22", "#d6d6d6"
# Caractères de bloc : (première moitié pleine, seconde moitié pleine), haut/bas ou gauche/droite.
BLOCS = {"▀": (True, False), "▄": (False, True), "█": (True, True), "▌": (True, False), "▐": (False, True)}
PALETTE16 = ["#1e1f22", "#e06c75", "#98c379", "#e5c07b", "#61afef", "#c678dd", "#56b6c2", "#d6d6d6",
             "#5c6370", "#ff7b86", "#b5e890", "#ffd88a", "#82c4ff", "#e19bff", "#7fd6e0", "#ffffff"]


def couleur256(n):
    if n < 16:
        return PALETTE16[n]
    if n < 232:
        n -= 16
        v = [0, 95, 135, 175, 215, 255]
        return "#%02x%02x%02x" % (v[n // 36], v[(n // 6) % 6], v[n % 6])
    g = 8 + (n - 232) * 10
    return "#%02x%02x%02x" % (g, g, g)


def analyser_ansi(texte):
    """Lignes de cellules : [(caractère, style)] ; style = (avant, fond, gras, italique, souligné, atténué)."""
    lignes = []
    etat = {"fg": None, "bg": None, "gras": False, "ital": False, "soul": False, "att": False, "inv": False}
    for brute in texte.split("\n"):
        cellules = []
        i = 0
        while i < len(brute):
            m = re.match(r"\x1b\[([0-9;:]*)m", brute[i:])
            if m:
                codes = [int(x) if x.isdigit() else 0 for x in re.split("[;:]", m.group(1) or "0")]
                k = 0
                while k < len(codes):
                    c = codes[k]
                    if c == 0:
                        etat.update(fg=None, bg=None, gras=False, ital=False, soul=False, att=False, inv=False)
                    elif c == 1: etat["gras"] = True
                    elif c == 2: etat["att"] = True
                    elif c == 3: etat["ital"] = True
                    elif c == 4: etat["soul"] = True
                    elif c == 7: etat["inv"] = True
                    elif c == 22: etat.update(gras=False, att=False)
                    elif c == 23: etat["ital"] = False
                    elif c == 24: etat["soul"] = False
                    elif c == 27: etat["inv"] = False
                    elif 30 <= c <= 37: etat["fg"] = PALETTE16[c - 30]
                    elif 90 <= c <= 97: etat["fg"] = PALETTE16[c - 90 + 8]
                    elif 40 <= c <= 47: etat["bg"] = PALETTE16[c - 40]
                    elif 100 <= c <= 107: etat["bg"] = PALETTE16[c - 100 + 8]
                    elif c == 39: etat["fg"] = None
                    elif c == 49: etat["bg"] = None
                    elif c in (38, 48) and k + 1 < len(codes):
                        cle = "fg" if c == 38 else "bg"
                        if codes[k + 1] == 5 and k + 2 < len(codes):
                            etat[cle] = couleur256(codes[k + 2]); k += 2
                        elif codes[k + 1] == 2 and k + 4 < len(codes):
                            etat[cle] = "#%02x%02x%02x" % tuple(codes[k + 2:k + 5]); k += 4
                    k += 1
                i += m.end()
                continue
            m = re.match(r"\x1b[\[\]][^a-zA-Z\x07]*[a-zA-Z\x07]", brute[i:])
            if m:  # autre séquence de contrôle : ignorée
                i += m.end()
                continue
            fg, bg = etat["fg"], etat["bg"]
            if etat["inv"]:
                fg, bg = bg or FOND, fg or ENCRE
            cellules.append((brute[i], (fg, bg, etat["gras"], etat["ital"], etat["soul"], etat["att"])))
            i += 1
        lignes.append(cellules)
    while lignes and not lignes[-1]:
        lignes.pop()
    return lignes


def vers_html(lignes, cibles, titre, largeur):
    """Page HTML : grille de caractères, cibles d'annotation en éléments transparents .cible-N."""
    texte = ["".join(c for c, _ in l) for l in lignes]
    # Fond du terminal : la couleur de fond dominante de l'écran quand l'interface en peint une (thème
    # de l'application), sinon le fond par défaut ; les cellules non peintes prennent ce fond.
    comptes = {}
    for l in lignes:
        for _, st in l:
            if st[1]:
                comptes[st[1]] = comptes.get(st[1], 0) + 1
    total = sum(len(l) for l in lignes) or 1
    fond = max(comptes, key=comptes.get) if comptes and max(comptes.values()) > 0.05 * total else FOND
    zones = []
    for n, (cible, _) in enumerate(cibles, 1):
        if isinstance(cible, tuple) and cible and cible[0] == "ligne":
            _, a, b = cible
            zones.append((n, a, 0, b, largeur))
        elif isinstance(cible, tuple) and cible and cible[0] == "zone":
            _, l1, c1, l2, c2 = cible
            zones.append((n, l1, c1, l2, c2))
        else:
            mot, rang = (cible if isinstance(cible, tuple) else (cible, 1))
            trouve = 0
            for li, t in enumerate(texte):
                debut = 0
                while (j := t.find(mot, debut)) >= 0:
                    trouve += 1
                    if trouve == rang:
                        zones.append((n, li, j, li, j + len(mot) - 1))
                        break
                    debut = j + 1
                if trouve >= rang:
                    break
            else:
                raise ValueError(f"cible introuvable à l'écran : {mot!r}")
    corps = []
    for l in lignes:
        morceaux, cour, buf = [], None, ""
        for c, st in l + [(" ", (None, None, False, False, False, False))] * max(0, largeur - len(l)):
            if st != cour and buf:
                morceaux.append((cour, buf)); buf = ""
            cour = st; buf += c
        if buf:
            morceaux.append((cour, buf))
        spans = []
        for (fg, bg, gras, ital, soul, att), b in morceaux:
            b = CLE_RE.sub(lambda m: "•" * len(m.group(0)), b)
            css = []
            if fg: css.append(f"color:{fg}")
            if bg: css.append(f"background:{bg}")
            if gras: css.append("font-weight:bold")
            if ital: css.append("font-style:italic")
            if soul: css.append("text-decoration:underline")
            if att: css.append("opacity:.65")
            # Caractères de bloc (logos, barres) : dessinés en couleurs pleines, sans dépendre de la police.
            for morceau in re.split(r"([▀▄█▌▐]+)", b):
                if not morceau:
                    continue
                if morceau[0] in BLOCS:
                    for ch in morceau:
                        haut, bas = BLOCS[ch]
                        coul = lambda x: (fg or ENCRE) if x else (bg or "transparent")
                        degrade = (f"linear-gradient(to {'bottom' if ch in '▀▄█' else 'right'}, {coul(haut)} 50%, {coul(bas)} 50%)")
                        spans.append(f'<span class="b" style="background:{degrade}"> </span>')
                else:
                    spans.append(f'<span style="{";".join(css)}">{html.escape(morceau)}</span>')
        corps.append(f'<div class="l">{"".join(spans)}</div>')
    zones_js = json.dumps(zones)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{html.escape(titre)}</title>
<style>
body {{ margin:0; background:#3a3d44; font-family:'DejaVu Sans Mono','Liberation Mono',monospace; }}
.fenetre {{ display:inline-block; margin:18px; border-radius:8px; overflow:hidden; box-shadow:0 6px 24px rgba(0,0,0,.45); }}
.barre {{ background:#2b2d31; color:#b9bbbe; font:13px sans-serif; padding:7px 12px; }}
.ecran {{ position:relative; background:{fond}; color:{ENCRE}; padding:10px 12px; font-size:14px; line-height:19px; white-space:pre; }}
.l {{ height:19px; }}
.l span {{ display:inline-block; height:19px; vertical-align:top; }}
.cible {{ position:absolute; pointer-events:none; }}
</style></head><body><div class="fenetre"><div class="barre">{html.escape(titre)}</div>
<div class="ecran" id="ecran">{"".join(corps)}</div></div>
<script>
const e = document.getElementById('ecran');
const m = document.createElement('span'); m.textContent = 'M'.repeat(100); m.style.visibility = 'hidden';
e.appendChild(m); const cw = m.getBoundingClientRect().width / 100; m.remove();
for (const [n, l1, c1, l2, c2] of {zones_js}) {{
  const d = document.createElement('div'); d.className = 'cible cible-' + n;
  Object.assign(d.style, {{left: (12 + c1 * cw) + 'px', top: (10 + l1 * 19) + 'px',
    width: ((c2 - c1 + 1) * cw) + 'px', height: ((l2 - l1 + 1) * 19) + 'px'}});
  e.appendChild(d);
}}
</script></body></html>"""


class Terminal:
    def __init__(self, nom, largeur=150, hauteur=42, dossier=".", env=None):
        self.nom, self.largeur, self.hauteur, self.dossier = f"capture-{nom}", largeur, hauteur, str(dossier)
        self.env = env or {}
        self.scenario = Path(TEXTES) / "scenario.jsonl"

    def tmux(self, *args, sortie=False):
        r = subprocess.run(["tmux", *args], capture_output=True, text=True)
        if r.returncode != 0 and not sortie:
            raise RuntimeError(f"tmux {args[0]} : {r.stderr.strip()}")
        return r.stdout

    def lancer(self, commande):
        subprocess.run(["tmux", "kill-session", "-t", self.nom], capture_output=True)
        envs = []
        for k, v in self.env.items():
            envs += ["-e", f"{k}={v}"]
        self.tmux("new-session", "-d", "-s", self.nom, "-x", str(self.largeur), "-y", str(self.hauteur),
                  "-c", self.dossier, *envs, " ".join(_cite(c) for c in commande))
        self.tmux("set-option", "-t", self.nom, "status", "off")

    def ecran(self, couleurs=False):
        args = ["capture-pane", "-p", "-t", self.nom]
        if couleurs:
            args.insert(1, "-e")
        return self.tmux(*args)

    def attendre(self, texte, delai=120, pas=0.5):
        fin = time.time() + delai
        while time.time() < fin:
            if re.search(texte, self.ecran()):
                return True
            time.sleep(pas)
        raise TimeoutError(f"texte {texte!r} absent après {delai} s ; écran :\n{self.ecran()}")

    def attendre_stable(self, duree=2.0, delai=120):
        """Attend que l'écran ne change plus pendant `duree` secondes."""
        fin, avant, depuis = time.time() + delai, None, time.time()
        while time.time() < fin:
            e = self.ecran()
            if e != avant:
                avant, depuis = e, time.time()
            elif time.time() - depuis >= duree:
                return
            time.sleep(0.3)

    def taper(self, texte, entree=False):
        self.tmux("send-keys", "-t", self.nom, "-l", texte)
        if entree:
            time.sleep(0.3)
            self.tmux("send-keys", "-t", self.nom, "Enter")

    def touche(self, *touches):
        self.tmux("send-keys", "-t", self.nom, *touches)

    def capturer(self, image):
        """Relève l'écran (couleurs comprises) sous banc-essai/resultats/captures/<harnais>/<chapitre>/<nom>.ans
        et son texte (.txt). Les annotations se posent ensuite avec page(), sans relancer le harnais."""
        base = base_capture(image)
        base.parent.mkdir(parents=True, exist_ok=True)
        base.with_suffix(".ans").write_text(CLE_RE.sub(lambda m: "•" * len(m.group(0)), self.ecran(couleurs=True)))
        base.with_suffix(".txt").write_text(CLE_RE.sub("sk-•••", self.ecran()))
        base.with_suffix(".taille").write_text(f"{self.largeur} {self.hauteur}")
        return base

    def fermer(self):
        subprocess.run(["tmux", "kill-session", "-t", self.nom], capture_output=True)


def base_capture(image):
    image = Path(image)
    rel = image.relative_to(RACINE) if image.is_absolute() else image
    parts = [x for x in rel.parts[2:] if x != "img"]   # documentations/manuels/<harnais>/img/<chapitre>/<nom>
    return (TEXTES / Path(*parts) if rel.parts[:2] == ("documentations", "manuels") else TEXTES / rel).with_suffix("")


def page(image, cibles=(), titre="Terminal", largeur=None):
    """Construit la page HTML annotable d'un écran relevé et l'ajoute au scénario de rendu."""
    base = base_capture(image)
    brut = base.with_suffix(".ans").read_text()
    lignes = analyser_ansi(brut)
    taille = base.with_suffix(".taille")
    if not largeur and taille.exists():
        largeur = int(taille.read_text().split()[0])
    largeur = largeur or max((len(l) for l in lignes), default=80)
    base.with_suffix(".html").write_text(vers_html(lignes, list(cibles), titre, largeur))
    rel = Path(image).relative_to(RACINE) if Path(image).is_absolute() else Path(image)
    entree = {"html": str(base.with_suffix(".html").relative_to(RACINE)), "image": str(rel),
              "libelles": [lib for _, lib in cibles]}
    with open(TEXTES / "scenario.jsonl", "a") as f:
        f.write(json.dumps(entree, ensure_ascii=False) + "\n")
    return entree


def _cite(x):
    return x if re.fullmatch(r"[A-Za-z0-9_./:=@%+-]+", x) else "'" + x.replace("'", "'\\''") + "'"


def nouveau_scenario():
    TEXTES.mkdir(parents=True, exist_ok=True)
    (TEXTES / "scenario.jsonl").write_text("")


if __name__ == "__main__":
    print(__doc__)
