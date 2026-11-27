"""Écrit la configuration du LiteLLM du banc (config.yaml) à partir de banc-essai/modele.env.

    python3 banc-essai/traces/generer_config.py        (appelé par demarrer.sh)

Le portail compatible OpenAI est appelé en mode générique (openai/<BANC_MODELE_FOURNISSEUR>,
api_base) ; adresse et clé lues dans l'environnement du conteneur (BANC_FOURNISSEUR_URL,
BANC_FOURNISSEUR_CLE, écrits par demarrer.sh depuis .env). Aucune clé n'est écrite dans config.yaml.
Bibliothèque standard seulement.
"""
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
MODELE_ENV = ICI.parent / "modele.env"


def lire_modele(chemin=MODELE_ENV):
    """Variables de modele.env (lignes CLE=valeur ; commentaires et lignes vides ignorés)."""
    v = {}
    for ligne in Path(chemin).read_text().splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, valeur = ligne.split("=", 1)
            v[cle.strip()] = valeur.strip().strip('"').strip("'")
    return v


def verifier(v):
    err = []
    if not v.get("BANC_MODELE_FOURNISSEUR"):
        err.append("BANC_MODELE_FOURNISSEUR à remplir (nom du modèle chez le portail)")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", v.get("BANC_MODELE", "")):
        err.append("BANC_MODELE : lettres, chiffres, points et tirets seulement")
    for cle in ("BANC_CONTEXTE", "BANC_SORTIE_MAX"):
        if not v.get(cle, "").isdigit():
            err.append(f"{cle} : nombre entier de jetons")
    if v.get("BANC_VISION") not in ("0", "1"):
        err.append("BANC_VISION : 0 ou 1")
    for cle in ("BANC_PRIX_ENTREE", "BANC_PRIX_CACHE", "BANC_PRIX_SORTIE", "BANC_BUDGET_ESSAI"):
        try:
            float(v.get(cle, ""))
        except ValueError:
            err.append(f"{cle} : nombre (point décimal)")
    return err


def config(v):
    """Texte YAML de la configuration (écrit à la main : pas de dépendance)."""
    # Notation avec point décimal : sans lui, le YAML de LiteLLM lirait « 5e-08 » comme du texte.
    par_jeton = lambda cle: f"{float(v[cle]) / 1e6:.4e}"
    p = [f"      model: openai/{v['BANC_MODELE_FOURNISSEUR']}",
         "      api_base: os.environ/BANC_FOURNISSEUR_URL",
         "      api_key: os.environ/BANC_FOURNISSEUR_CLE"]
    p.append(f"      input_cost_per_token: {par_jeton('BANC_PRIX_ENTREE')}")
    p.append(f"      output_cost_per_token: {par_jeton('BANC_PRIX_SORTIE')}")
    p.append(f"      cache_read_input_token_cost: {par_jeton('BANC_PRIX_CACHE')}")
    return "\n".join([
        "# Écrit par banc-essai/traces/generer_config.py depuis banc-essai/modele.env : ne pas modifier à la main.",
        f"# Portail compatible OpenAI ; modèle exposé aux harnais : {v['BANC_MODELE']}.",
        "# Prix (dollars par jeton) donnés au relais : sans eux, LiteLLM ne calcule aucun coût et le",
        "# plafond par clé ne bloque rien.",
        "model_list:",
        f"  - model_name: {v['BANC_MODELE']}",
        "    litellm_params:",
        *p,
        "",
        "litellm_settings:",
        "  callbacks: journal_appels.journal",
        "  drop_params: true",
        "",
        "general_settings:",
        "  master_key: os.environ/LITELLM_MASTER_KEY",
        "  database_url: os.environ/DATABASE_URL",
        "  # Dépense des clés écrite en base toutes les 1 à 6 s : lancer.sh la relit 10 s après l'essai.",
        "  proxy_batch_write_at: 1",
        "",
        "# Un seul déploiement : pas de mise en pause après une erreur (le harnais reçoit le vrai 429,",
        "# relevé dans le rapport d'essai), pas de nouvelle tentative cachée par le relais.",
        "router_settings:",
        "  disable_cooldowns: true",
        "  num_retries: 0",
        "",
    ])


if __name__ == "__main__":
    v = lire_modele()
    err = verifier(v)
    if err:
        sys.exit("banc-essai/modele.env : " + " ; ".join(err))
    (ICI / "config.yaml").write_text(config(v))
    print(f"config.yaml écrit : modèle {v['BANC_MODELE']} (portail : {v['BANC_MODELE_FOURNISSEUR']})")
