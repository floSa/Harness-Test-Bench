"""Relance du workflow livré sur un lot neuf (jeu « relance » du corpus), dans la cage, sans le harnais.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/relancer.py \
        --espace DOSSIER --essai banc-essai/resultats/<essai> [--commande "..."] \
        [--jeu banc-essai/corpus/relance]

La commande vient de la déclaration de fin (`<essai>/evaluation/fin.json`) sauf si elle est
donnée. Elle est lancée depuis l'espace de travail, `{entree}` (copie des PDF seuls) et
`{sortie}` remplacés. Toujours dans la cage (banc-essai/cage/cage.sh ; sans bubblewrap, la
relance refuse de tourner) : espace en /travail, PDF en /entree (lecture seule), sortie en
/sortie, réseau limité au modèle (clé --cle) et à PyPI. Résultat : `<essai>/relance/resultat.json`,
sorties et journaux de la commande. Seuls les fichiers ordinaires de /sortie sont lus (ni lien
symbolique, ni fichier spécial, 1 Mo au plus) : un lien posé par le workflow vers un fichier de
l'hôte est ignoré. Document sans JSON, JSON illisible ou fichier refusé : tous ses champs
comptent faux.
"""
import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import notation
import notation_dossiers

ICI = Path(__file__).resolve().parent
CAGE = ICI.parent / "cage" / "cage.sh"
DUREE_MAX = 3600
TAILLE_MAX = 1024 * 1024


def lire_sortie(f):
    """Contenu d'un fichier de sortie, sans suivre de lien : None s'il n'est pas un fichier ordinaire."""
    try:
        fd = os.open(f, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > TAILLE_MAX:
            return None
        with os.fdopen(fd, "rb") as h:
            fd = None
            return h.read(TAILLE_MAX + 1)[:TAILLE_MAX]
    finally:
        if fd is not None:
            os.close(fd)


def relancer(espace, essai, commande=None, jeu=None, duree_max=DUREE_MAX, cle=None, maison=None,
             tache="extraction"):
    essai = Path(essai)
    if shutil.which("bwrap") is None or not CAGE.exists():
        raise SystemExit("relance refusée : bubblewrap ou banc-essai/cage/cage.sh absent")
    defaut = ICI.parent / "corpus" / ("dossiers/relance" if tache == "dossiers" else "relance")
    jeu = Path(jeu or defaut)
    module = notation_dossiers if tache == "dossiers" else notation
    if commande is None:
        commande = json.loads((essai / "evaluation" / "fin.json").read_text())["commande"]
    ids, attendus, verites = module.charger_jeu(jeu)
    sortie_essai = essai / "relance"
    if sortie_essai.exists():
        shutil.rmtree(sortie_essai)
    (sortie_essai / "sorties").mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="relance-") as tmp:
        entree = Path(tmp) / "entree"
        entree.mkdir()
        for i in ids:
            if tache == "dossiers":   # pièces seules, ni réponses ni vérité
                (entree / i).mkdir()
                for piece in sorted((jeu / i).glob("piece-*.pdf")):
                    shutil.copy2(piece, entree / i / piece.name)
            else:
                shutil.copy2(jeu / f"{i}.pdf", entree / f"{i}.pdf")
        sortie = Path(tmp) / "sortie"
        sortie.mkdir()
        m = Path(maison) if maison else Path(tmp) / "maison"
        m.mkdir(exist_ok=True)
        interne = commande.replace("{entree}", "/entree").replace("{sortie}", "/sortie")
        cmd = [str(CAGE), "--espace", str(espace), "--maison", str(m), "--entree", str(entree),
               "--sortie", str(sortie), "--journal-reseau", str(sortie_essai / "reseau.jsonl"),
               "--duree", str(duree_max), "--gpu", "--memoire", "16G",
               "--memoire-pic", str(sortie_essai / "memoire.json")]
        if cle:
            cmd += ["--cle", str(cle)]
        cmd += ["--", "bash", "-c", interne]
        debut = time.monotonic()
        try:
            p = subprocess.run(cmd, cwd=espace, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                               timeout=duree_max + 60)
            code, out, err = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            code, out, err = "délai dépassé", e.stdout or "", e.stderr or ""
            out, err = (x.decode() if isinstance(x, bytes) else x for x in (out, err))
        duree = time.monotonic() - debut
        reponses, illisibles, refuses = {}, [], []
        for i in ids:
            f = sortie / f"{i}.json"
            if not os.path.lexists(f):
                continue
            octets = lire_sortie(f)
            if octets is None:
                refuses.append(i)
                continue
            (sortie_essai / "sorties" / f.name).write_bytes(octets)
            try:
                reponses[i] = json.loads(octets.decode())
            except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
                illisibles.append(i)
    (sortie_essai / "stdout.txt").write_text(out)
    (sortie_essai / "stderr.txt").write_text(err)
    erreurs = module.valider(reponses, ids)
    produits = len(reponses) + len(illisibles)
    # Une réponse mal formée (nombre immense, type faux…) compte faux, sans faire échouer la relance.
    for i in list(reponses):
        r = reponses[i]
        if tache == "dossiers":
            if notation_dossiers.erreurs_dossier(r):
                reponses.pop(i)
        elif not isinstance(r, dict) or any(notation.erreurs_valeur(k, r.get(k)) for k in notation.CLES if k in r):
            reponses.pop(i)
    note = module.noter(reponses, attendus, verites)
    note.pop("detail")
    resultat = {
        "commande": commande, "cage": True, "code_retour": code, "duree_s": round(duree, 1),
        "tache": tache, "duree_par_document_s": round(duree / len(ids), 2), "documents": len(ids),
        "json_produits": produits, "json_illisibles": illisibles,
        "fichiers_refuses": refuses,
        "erreurs_format": erreurs[:50],
        "note": note,
    }
    (sortie_essai / "resultat.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=2) + "\n")
    return resultat


def main():
    a = argparse.ArgumentParser(description="Relance du workflow livré sur un lot neuf")
    a.add_argument("--espace", required=True)
    a.add_argument("--essai", required=True)
    a.add_argument("--commande")
    a.add_argument("--jeu")
    a.add_argument("--duree-max", type=int, default=DUREE_MAX)
    a.add_argument("--cle", help="fichier de clé virtuelle (appels au modèle du workflow)")
    a.add_argument("--maison", help="dossier personnel du harnais pendant l'essai")
    a.add_argument("--tache", choices=["extraction", "dossiers"], default="extraction")
    o = a.parse_args()
    r = relancer(o.espace, o.essai, o.commande, o.jeu, o.duree_max, o.cle, o.maison, o.tache)
    print(f"relance : {r['json_produits']}/{r['documents']} JSON, score {r['note']['score']}, "
          f"{r['duree_par_document_s']} s par document, code {r['code_retour']}")


if __name__ == "__main__":
    sys.exit(main())
