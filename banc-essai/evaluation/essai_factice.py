"""Essai complet avec de fausses solutions, sans harnais ni modèle : vérifie la chaîne du banc.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/essai_factice.py

Extraction (recette « sans aide », test caché réel) : espace préparé, API lancée comme processus,
PDF du test téléchargés par le client, fausse solution exécutée, une soumission mal formée,
5 soumissions, une sixième refusée, déclaration de fin, relance sur le jeu « relance », rapport.
Tâche jouet : soumission du code d'origine et d'une correction trop ciblée, fin, rapport.
Résultats : banc-essai/resultats/essai-factice/ et banc-essai/resultats/jouet-factice/.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import notation
import preparer
import rapport
import relancer

ICI = Path(__file__).resolve().parent
BANC = ICI.parent
PORT = 8765


def lancer_api(tache, jeu, sortie):
    p = subprocess.Popen([sys.executable, str(ICI / "api.py"), "--tache", tache, "--jeu", str(jeu),
                          "--sortie", str(sortie), "--port", str(PORT)], cwd=ICI)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/etat", timeout=1)
            return p
        except OSError:
            time.sleep(0.1)
    p.terminate()
    raise SystemExit("l'API ne répond pas")


def client(espace, *args):
    """Lance le client depuis l'espace de travail, comme le ferait un harnais."""
    env = os.environ | {"BANC_API": f"http://127.0.0.1:{PORT}"}
    r = subprocess.run([sys.executable, "soumettre.py", *args], cwd=espace, env=env, capture_output=True, text=True)
    sortie = r.stdout.strip()
    print(f"  soumettre.py {' '.join(args)} -> code {r.returncode}")
    return r.returncode, sortie


def extraction(tmp):
    essai = BANC / "resultats" / "essai-factice"
    shutil.rmtree(essai, ignore_errors=True)
    espace = preparer.preparer("sans-aide", Path(tmp) / "espace-extraction")
    shutil.copy2(ICI / "tests" / "solutions" / "extraction_fausse" / "faux_workflow.py", espace)
    api = lancer_api("extraction", BANC / "corpus" / "test-cache", essai / "evaluation")
    try:
        client(espace, "documents", "test")
        subprocess.run([sys.executable, "faux_workflow.py", "test", "sorties"], cwd=espace, check=True)
        # Score de validation mesuré sur les documents fournis, comme le ferait le harnais.
        subprocess.run([sys.executable, "faux_workflow.py", "fourni", "validation"], cwd=espace, check=True)
        ids, attendus, verites = notation.charger_jeu(BANC / "corpus" / "fourni")
        val = {i: json.loads((espace / "validation" / f"{i}.json").read_text()) for i in ids}
        score_val = notation.noter(val, attendus, verites)["score"]
        # Soumission mal formée : refusée, non décomptée.
        mal = espace / "sorties-mal"
        shutil.copytree(espace / "sorties", mal)
        f = sorted(mal.glob("*.json"))[0]
        r = json.loads(f.read_text())
        r["pression_bar"] = "2,5 bar"
        f.write_text(json.dumps(r))
        client(espace, "soumettre", "sorties-mal")
        for _ in range(6):
            client(espace, "soumettre", "sorties")
        client(espace, "fin", "--soumission", "2", "--score-validation", str(score_val),
               "--commande", "python3 faux_workflow.py {entree} {sortie}")
        _, etat = client(espace, "etat")
    finally:
        api.terminate()
        api.wait()
    relancer.relancer(espace, essai)
    r = rapport.construire(essai)
    (essai / "rapport.json").write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    (essai / "rapport.md").write_text(rapport.markdown(r))
    return r, json.loads(etat)


def jouet(tmp):
    essai = BANC / "resultats" / "jouet-factice"
    shutil.rmtree(essai, ignore_errors=True)
    espace = preparer.preparer("jouet", Path(tmp) / "espace-jouet")
    api = lancer_api("jouet", ICI / "taches" / "jouet", essai / "evaluation")
    try:
        client(espace, "soumettre", "dosage")
        shutil.copy2(ICI / "tests" / "solutions" / "jouet_fausse" / "dosage" / "unites.py", espace / "dosage")
        client(espace, "soumettre", "dosage")
        client(espace, "fin", "--soumission", "2", "--score-validation", "1.0")
    finally:
        api.terminate()
        api.wait()
    r = rapport.construire(essai)
    (essai / "rapport.json").write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    (essai / "rapport.md").write_text(rapport.markdown(r))
    return r


def main():
    with tempfile.TemporaryDirectory(prefix="essai-factice-") as tmp:
        print("Extraction :")
        r, etat = extraction(tmp)
        print(f"  soumissions : {[(s['statut'], s['score']) for s in r['soumissions']]}")
        print(f"  état final : {etat}")
        print(f"  score final {r['score_final']}, validation annoncée {r['score_validation_annonce']}, "
              f"invention {r['taux_invention']}, style inédit {r['score_style_inedit']}")
        rl = r["relance"]
        print(f"  relance : {rl['json_produits']}/{rl['documents']} JSON, score {rl['note']['score']}, "
              f"code {rl['code_retour']}")
        print("Tâche jouet :")
        j = jouet(tmp)
        print(f"  soumissions : {[(s['statut'], s['score']) for s in j['soumissions']]}, "
              f"échecs finaux : {j['note_finale']['echecs']}")


if __name__ == "__main__":
    sys.exit(main())
