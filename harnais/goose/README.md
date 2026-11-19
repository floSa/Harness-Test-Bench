# Goose

| Élément | Valeur |
|---|---|
| Version | 1.60.1 (`version`), binaire officiel `goose-x86_64-unknown-linux-gnu.tar.gz` de github.com/aaif-goose/goose, empreinte SHA-256 vérifiée ; dépend seulement des bibliothèques du système (glibc, libstdc++) |
| Installation | `harnais/goose/installer.sh` : binaire dans `installe/` (hors git) |
| Configuration | `configurer.sh` : écrit `$HOME/.config/goose/config.yaml` (fournisseur `openai` pointé sur le LiteLLM du banc, `OPENAI_BASE_PATH: v1/chat/completions`, mode `auto`, télémétrie et nommage des sessions coupés) ; la clé vient de `OPENAI_API_KEY`, jamais du fichier |
| Lancement | `lancer.sh "<message>"` (dans la cage) : `goose run --with-builtin developer --output-format stream-json` ; sortie standard = événements JSON, session exportée dans `$HOME/goose-session.json` |

Constats (essai du 19/11/2026) :

| Constat | Détail |
|---|---|
| Configuration | entièrement par variables d'environnement, sans `goose configure` (vérifié hors cage puis dans la cage) |
| Trousseau système | désactivé (`GOOSE_DISABLE_KEYRING=1`) |
| Réseau au démarrage | catalogue `models.dev` refusé par la cage, sans effet sur l'essai |
| Tâche jouet | 100 % aux cas cachés, 22 s, 8 appels, 0,0014 $ (`banc-essai/resultats/goose-jouet-1/`) |
