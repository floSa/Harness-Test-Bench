# gptme

| Élément | Valeur |
|---|---|
| Version | 0.37.0 (`version`), paquet PyPI `gptme`, sans extension facultative |
| Installation | `harnais/gptme/installer.sh` : environnement virtuel `installe/` (hors git) sur le Python du système (`/usr/bin/python3`, 3.12.3), visible dans la cage |
| Configuration | `configurer.sh` : écrit `$HOME/.config/gptme/config.toml` (fournisseur compatible OpenAI `banc` = LiteLLM du banc, clé lue dans `BANC_CLE_MODELE`, modèle `banc/<modèle>`) |
| Lancement | `lancer.sh "<message>"` (dans la cage) : `gptme --non-interactive --output-format json --tool-format tool` ; sortie standard = un objet JSON par message, conversation dans `$HOME/.local/share/gptme/logs/essai/` |

Constats (essai du 19/11/2026) :

| Constat | Détail |
|---|---|
| Lanceur de l'environnement virtuel | `installe/bin/gptme` désigne son interpréteur par le chemin de l'hôte, invisible dans la cage : `lancer.sh` appelle `installe/bin/python` et le module `gptme.cli.main` |
| Métadonnées du modèle | modèle inconnu de gptme : il emprunte celles d'un « modèle proche » ; contexte (1 000 000 jetons) et vision corrects, prix 100 fois trop hauts (5 $ et 30 $ par million de jetons au lieu de 0,05 $ et 0,30 $) ; le coût affiché par gptme est faux, le coût mesuré par le relais fait foi ; ses avertissements de coût ne sont injectés qu'après un message de l'utilisateur, donc pas en mode sans interaction |
| Réseau au démarrage | téléchargement du découpeur tiktoken et recherche de serveurs locaux coupés par variables d'environnement |
| Tâche jouet | 100 % aux cas cachés, 48 s, 15 appels, 0,0022 $ (gptme affichait 0,61 $) (`banc-essai/resultats/gptme-jouet-1/`) |
