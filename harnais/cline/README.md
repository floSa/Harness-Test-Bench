# Cline (CLI)

| Élément | Valeur |
|---|---|
| Version | 3.0.74 (`version`), paquet npm `cline` (binaire Linux x64 du paquet `@cline/cli-linux-x64`, lancé par un script Node), intégrité vérifiée par npm |
| Installation | `harnais/cline/installer.sh` : Node.js 26.13.1 (`harnais/commun/installer-node.sh`) et le paquet dans `installe/` (hors git), scripts d'installation désactivés |
| Configuration | `configurer.sh` : `cline auth -p openai-compatible -b <LiteLLM du banc>/v1 -m <modèle> -k <clé de l'essai>` ; la clé est enregistrée dans `$HOME/.cline` (dossier personnel de l'essai, hors du dépôt), et supprimée du relais à la fin de l'essai |
| Lancement | `lancer.sh "<message>"` (dans la cage) : `cline --json -y` ; sortie standard = événements NDJSON (dont `run_result` : itérations, jetons, coût, durée), sessions dans `$HOME/.cline/data/sessions/` |

Constats (essais du 19/11/2026) :

| Constat | Détail |
|---|---|
| Adresse du LiteLLM du banc | acceptée (point à vérifier du lot 4) : appels journalisés sous la clé de l'essai, pas besoin d'OpenRouter direct |
| Identifiant du fournisseur | `openai` et `openai-compatible` donnent le même fournisseur « openai-compatible » |
| Approbation | `-y` (« yolo ») : outils approuvés automatiquement, outils d'équipe et de sous-agents désactivés par défaut |
| Réseau au démarrage | `data.cline.bot` et `registry.npmjs.org` refusés par la cage, sans effet sur l'essai |
| Tâche jouet | 100 % aux cas cachés, 29 s, 8 appels, 0,0016 $ (`banc-essai/resultats/cline-jouet-1/`) |
