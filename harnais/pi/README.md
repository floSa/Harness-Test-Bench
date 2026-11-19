# Pi

| Élément | Valeur |
|---|---|
| Version | 1.5.2 (`version`), paquet npm `@earendil-works/pi-coding-agent` (projet repris de `@mariozechner/pi-coding-agent`, dépôt github.com/earendil-works/pi), intégrité vérifiée par npm |
| Installation | `harnais/pi/installer.sh` : Node.js 26.13.1 (`harnais/commun/installer-node.sh`, empreinte vérifiée) et le paquet dans `installe/` (hors git), scripts d'installation désactivés |
| Configuration | `configurer.sh` : `$HOME/.pi/agent/models.json` (fournisseur `banc`, API `openai-completions`, clé `$BANC_CLE_MODELE` lue au lancement, contexte, vision, prix) et `settings.json` (modèle par défaut, télémétrie coupée) |
| Lancement | `lancer.sh "<message>"` (dans la cage) : `pi --mode json` ; sortie standard = événements JSONL, session dans `$HOME/.pi/agent/sessions/` |

Constats (essai du 19/11/2026) :

| Constat | Détail |
|---|---|
| Approbation | aucune : Pi n'a pas de système de permission, ses outils s'exécutent directement |
| Réseau au démarrage | aucun avec `PI_OFFLINE=1`, `PI_SKIP_VERSION_CHECK=1`, `PI_TELEMETRY=0` (aucune demande refusée par la cage) |
| Tâche jouet | 100 % aux cas cachés, 23 s, 11 appels, 0,0013 $ (`banc-essai/resultats/pi-jouet-1/`) |
