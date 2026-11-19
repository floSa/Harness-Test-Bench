# OpenCode

| Élément | Valeur |
|---|---|
| Version | 1.19.6 (`version`), binaire officiel `opencode-linux-x64.tar.gz` de github.com/anomalyco/opencode, empreinte SHA-256 vérifiée |
| Installation | `harnais/opencode/installer.sh` : binaire dans `installe/` (hors git) |
| Configuration | `configurer.sh` : écrit `$HOME/.config/opencode/opencode.json` (fournisseur compatible OpenAI = LiteLLM du banc, clé lue dans `BANC_CLE_MODELE`, éditions et commandes permises, accès web du harnais refusé, mise à jour et partage coupés) |
| Lancement | `lancer.sh "<message>"` (dans la cage) : `opencode run --format json --print-logs --auto` ; sortie standard = événements JSON de la session, sortie d'erreur = journaux ; sessions exportées dans `$HOME/opencode-sessions/` |

Constats (essais du 19/11/2026) :

| Constat | Détail |
|---|---|
| Syntaxe de configuration | la version 1.19.6 lit la syntaxe « provider », « npm », « options » ; elle ignore la syntaxe « providers » de la documentation en ligne (vérifié avec `opencode debug config`) |
| Réseau au démarrage | catalogue `models.opencode.ai` et paquet `@opencode-ai/plugin` sur `registry.npmjs.org` : refusés par la cage, sans effet sur l'essai |
| Entrée standard | `opencode run` attend la fin de l'entrée standard si elle reste ouverte : le lanceur du banc la ferme (`< /dev/null`) |
