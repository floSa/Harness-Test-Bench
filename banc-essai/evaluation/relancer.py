"""Relance du workflow livré sur un lot neuf (jeu « relance » du corpus), hors cage.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/relancer.py \
        --espace DOSSIER --essai banc-essai/resultats/<essai> [--commande "..."] \
        [--jeu banc-essai/corpus/relance]

La commande vient de la déclaration de fin (`<essai>/evaluation/fin.json`) sauf si elle est
donnée. Elle est lancée depuis l'espace de travail, `{entree}` (copie des PDF seuls) et
`{sortie}` remplacés. Résultat : `<essai>/relance/resultat.json`, sorties et journaux de la
commande. Document sans JSON ou JSON illisible : tous ses champs comptent faux.
"""
import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import notation

ICI = Path(__file__).resolve().parent
DUREE_MAX = 3600


def relancer(espace, essai, commande=None, jeu=None, duree_max=DUREE_MAX):
    essai = Path(essai)
    jeu = Path(jeu or ICI.parent / "corpus" / "relance")
    if commande is None:
        commande = json.loads((essai / "evaluation" / "fin.json").read_text())["commande"]
    ids, attendus, verites = notation.charger_jeu(jeu)
    sortie_essai = essai / "relance"
    if sortie_essai.exists():
        shutil.rmtree(sortie_essai)
    (sortie_essai / "sorties").mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="relance-") as tmp:
        entree = Path(tmp) / "entree"
        entree.mkdir()
        for i in ids:
            shutil.copy2(jeu / f"{i}.pdf", entree / f"{i}.pdf")
        sortie = Path(tmp) / "sortie"
        sortie.mkdir()
        cmd = commande.replace("{entree}", shlex.quote(str(entree))).replace("{sortie}", shlex.quote(str(sortie)))
        debut = time.monotonic()
        try:
            p = subprocess.run(cmd, shell=True, cwd=espace, capture_output=True, text=True, timeout=duree_max)
            code, out, err = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            code, out, err = "délai dépassé", e.stdout or "", e.stderr or ""
            out, err = (x.decode() if isinstance(x, bytes) else x for x in (out, err))
        duree = time.monotonic() - debut
        reponses, illisibles = {}, []
        for i in ids:
            f = sortie / f"{i}.json"
            if f.exists():
                shutil.copy2(f, sortie_essai / "sorties" / f.name)
                try:
                    reponses[i] = json.loads(f.read_text())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    illisibles.append(i)
    (sortie_essai / "stdout.txt").write_text(out)
    (sortie_essai / "stderr.txt").write_text(err)
    note = notation.noter(reponses, attendus, verites)
    note.pop("detail")
    resultat = {
        "commande": commande, "code_retour": code, "duree_s": round(duree, 1),
        "duree_par_document_s": round(duree / len(ids), 2), "documents": len(ids),
        "json_produits": len(reponses) + len(illisibles), "json_illisibles": illisibles,
        "erreurs_format": notation.valider(reponses, ids)[:50],
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
    o = a.parse_args()
    r = relancer(o.espace, o.essai, o.commande, o.jeu, o.duree_max)
    print(f"relance : {r['json_produits']}/{r['documents']} JSON, score {r['note']['score']}, "
          f"{r['duree_par_document_s']} s par document, code {r['code_retour']}")


if __name__ == "__main__":
    sys.exit(main())
