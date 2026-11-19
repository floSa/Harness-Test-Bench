"""Rapport d'essai (JSON et Markdown) à partir des journaux de l'API et de la relance.

    uv run --project banc-essai/evaluation python banc-essai/evaluation/rapport.py \
        --essai banc-essai/resultats/<essai>

Lit `<essai>/evaluation/soumissions.jsonl`, `fin.json`, `<essai>/essai.json` et, s'ils existent,
`<essai>/relance/resultat.json` et `<essai>/relance/appels.jsonl`. Écrit `<essai>/rapport.json` et
`<essai>/rapport.md` (scores agrégés seulement, aucun détail par document du test caché).

Sans déclaration de fin (harnais arrêté, garde-fou atteint), la dernière soumission acceptée tient
lieu de soumission finale et le rapport l'indique ; aucune relance n'a lieu (protocole, section 7).
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
STYLE_INEDIT = "reserve"
GROUPES = [("cle", "Clé"), ("famille", "Famille de pièges"), ("etiquette", "Étiquette"),
           ("emplacement", "Emplacement"), ("style", "Style de mise en page"),
           ("prestataire_vu", "Prestataire vu ou inédit"), ("marque_vue", "Marque vue ou inédite"),
           ("langue", "Langue"), ("prestataire", "Prestataire")]


def versions():
    v = {}
    emp = ICI.parent / "corpus" / "empreintes.sha256"
    if emp.exists():
        v["corpus_empreintes_sha256"] = hashlib.sha256(emp.read_bytes()).hexdigest()
    try:
        v["evaluateur_commit"] = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ICI,
                                                capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        v["evaluateur_commit"] = None
    return v


def construire(essai):
    essai = Path(essai)
    ev = essai / "evaluation"
    lignes = [json.loads(l) for l in (ev / "soumissions.jsonl").read_text().splitlines()] \
        if (ev / "soumissions.jsonl").exists() else []
    acceptees = [l for l in lignes if l["statut"] == "acceptee"]
    fin = json.loads((ev / "fin.json").read_text()) if (ev / "fin.json").exists() else None
    construction = json.loads((essai / "essai.json").read_text()) if (essai / "essai.json").exists() else None
    relance = json.loads((essai / "relance" / "resultat.json").read_text()) \
        if (essai / "relance" / "resultat.json").exists() else None
    if fin:
        finale = next((l for l in acceptees if l["numero"] == fin["soumission_finale"]), None)
    else:
        finale = acceptees[-1] if acceptees else None
    meilleur = max((l["score"] for l in acceptees), default=None)
    note = finale["note"] if finale else None
    if construction and construction.get("tache"):
        tache = construction["tache"]
    else:
        tache = "jouet" if note and "tests" in note else "extraction"
    f_ra = essai / "relance" / "appels.jsonl"
    appels_relance = [json.loads(l) for l in f_ra.read_text().splitlines()] if f_ra.exists() else []
    if relance is not None:
        cout = sum(a.get("cout") or 0 for a in appels_relance)
        relance = relance | {"appels_modele": len(appels_relance), "cout_usd": round(cout, 6),
                             "cout_par_document_usd": round(cout / relance["documents"], 6)}
    r = {
        "essai": essai.name,
        "tache": tache,
        "versions": versions(),
        "soumissions": [{"numero": l.get("numero"), "heure": l["heure"], "statut": l["statut"],
                         "score": l.get("score")} for l in lignes],
        "soumissions_acceptees": len(acceptees),
        "refus_format": sum(l["statut"] == "refusee_format" for l in lignes),
        "refus_limite": sum(l["statut"] == "refusee_limite" for l in lignes),
        "fin": fin,
        "fin_declaree": fin is not None,
        "soumission_finale": finale["numero"] if finale else None,
        "score_final": finale["score"] if finale else None,
        "meilleur_score": meilleur,
        "score_validation_annonce": fin.get("score_validation") if fin else None,
        "ecart_validation_test": round(fin["score_validation"] - finale["score"], 4)
        if fin and finale and fin.get("score_validation") is not None else None,
        "note_finale": note,
        "relance": relance,
        "construction": construction,
    }
    if tache == "extraction" and note:
        r["taux_invention"] = note["invention"]["taux"]
        r["score_style_inedit"] = note["par"].get("style", {}).get(STYLE_INEDIT, {}).get("score")
    return r


def pc(x):
    return "" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def markdown(r):
    L = [f"# Rapport d'essai : {r['essai']}", ""]
    L += ["## Versions", "", "| Élément | Valeur |", "|---|---|"]
    L += [f"| Tâche | {r['tache']} |"] + [f"| {k} | `{v}` |" for k, v in r["versions"].items()] + [""]
    L += ["## Résultat", "", "| Mesure | Valeur |", "|---|---|"]
    titre_final = "Score final (soumission déclarée)" if r["fin_declaree"] else \
        "Score final (fin non déclarée : dernière soumission acceptée)"
    lignes = [(titre_final, pc(r["score_final"])),
              ("Meilleur score", pc(r["meilleur_score"])),
              ("Score de validation annoncé", pc(r["score_validation_annonce"])),
              ("Écart annoncé moins test", pc(r["ecart_validation_test"])),
              ("Soumissions acceptées", r["soumissions_acceptees"]),
              ("Soumissions refusées (format)", r["refus_format"]),
              ("Soumissions refusées (limite)", r["refus_limite"]),
              ("Soumission finale", r["soumission_finale"] or ""),
              ("Fin déclarée", "oui" if r["fin_declaree"] else "non")]
    if r["tache"] == "extraction":
        lignes += [("Taux d'invention", pc(r.get("taux_invention"))),
                   ("Score sur le style jamais vu", pc(r.get("score_style_inedit")))]
    if r["relance"]:
        rl = r["relance"]
        lignes += [("Relance : score", pc(rl["note"]["score"])),
                   ("Relance : JSON produits", f"{rl['json_produits']} sur {rl['documents']}"),
                   ("Relance : durée par document", f"{rl['duree_par_document_s']} s"),
                   ("Relance : appels au modèle", rl.get("appels_modele", "")),
                   ("Relance : coût par document", f"{rl['cout_par_document_usd']} $" if "cout_par_document_usd" in rl else ""),
                   ("Relance : fichiers refusés (lien, fichier spécial)", len(rl.get("fichiers_refuses", []))),
                   ("Relance : code de retour", rl["code_retour"])]
    L += [f"| {a} | {b} |" for a, b in lignes] + [""]
    c = r.get("construction")
    if c:
        L += ["## Construction", "", "| Mesure | Valeur |", "|---|---|"]
        L += [f"| {a} | {b} |" for a, b in [
            ("Harnais", c["harnais"]), ("Version du harnais", c.get("version_harnais") or ""),
            ("Modèle (journal)", ", ".join(c.get("modeles") or [])),
            ("Fournisseur (journal)", ", ".join(c.get("fournisseurs") or [])),
            ("Recette", c["recette"]), ("Début", c["debut"]), ("Fin", c["fin"]),
            ("Durée totale", f"{c['duree_s']} s"), ("Garde-fou atteint", "oui" if c["garde_fou_atteint"] else "non"),
            ("Code de retour du harnais", c["code_retour"]), ("Appels au modèle", c["appels_modele"]),
            ("Appels échoués", c["appels_echoues"]), ("Appels refusés pour quota (429)", c["appels_429"]),
            ("Temps d'attente après un 429", f"{c.get('attente_429_s', '')} s"),
            ("Appels avec image", c["appels_avec_image"]), ("Jetons d'entrée", c["jetons_entree"]),
            ("Dont jetons lus dans le cache", c.get("jetons_cache", "")),
            ("Jetons de sortie", c["jetons_sortie"]), ("Temps dans le modèle", f"{c['temps_modele_s']} s"),
            ("Coût calculé par le relais", f"{c.get('cout_usd', '')} $"),
            ("Coût facturé par OpenRouter", f"{c.get('cout_openrouter_usd', '')} $"),
            ("Dépense de la clé (LiteLLM)", f"{c.get('depense_cle_usd', '')} $"),
            ("Demandes réseau (mandataire PyPI)", c["demandes_reseau"]),
            ("Demandes réseau refusées", c["demandes_reseau_refusees"])]] + [""]
    if r["soumissions"]:
        S = r["soumissions"]
        L += ["## Soumissions", "", "| Critère | " + " | ".join(f"Requête {k + 1}" for k in range(len(S))) + " |",
              "|---|" + "---|" * len(S)]
        L.append("| Heure | " + " | ".join(s["heure"] for s in S) + " |")
        L.append("| Statut | " + " | ".join(s["statut"] for s in S) + " |")
        L.append("| Numéro | " + " | ".join(str(s["numero"] or "") for s in S) + " |")
        L.append("| Score | " + " | ".join(pc(s["score"]) for s in S) + " |")
        L.append("")
    note = r["note_finale"]
    if r["tache"] == "extraction" and note:
        L += ["## Scores détaillés de la soumission finale", ""]
        for g, titre in GROUPES:
            d = note["par"].get(g, {})
            L += [f"### {titre}", "", f"| {titre} | Champs | Justes | Score |", "|---|---|---|---|"]
            L += [f"| {k} | {v['n']} | {v['justes']} | {pc(v['score'])} |" for k, v in d.items()] + [""]
    if r["tache"] == "jouet" and note:
        L += ["## Tests cachés de la soumission finale", "", "| Mesure | Valeur |", "|---|---|",
              f"| Tests | {note['tests']} |", f"| Réussis | {note['reussis']} |",
              f"| Échoués | {', '.join(note['echecs'])} |", ""]
    return "\n".join(L)


def main():
    a = argparse.ArgumentParser(description="Rapport d'essai")
    a.add_argument("--essai", required=True)
    o = a.parse_args()
    r = construire(o.essai)
    e = Path(o.essai)
    (e / "rapport.json").write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    (e / "rapport.md").write_text(markdown(r))
    print(f"rapport écrit : {e / 'rapport.md'}")


if __name__ == "__main__":
    sys.exit(main())
