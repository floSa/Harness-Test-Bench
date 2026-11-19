# Captures d'écran des manuels

Les harnais sont surtout des interfaces en terminal. Leurs captures suivent les règles de la série (rectangle rouge et pastille numérotée autour de chaque élément dont parle l'étape, tableau N° | Élément | Rôle) avec une chaîne propre au terminal.

| Fichier | Rôle |
|---|---|
| `terminal.py` | pilote une session tmux de taille fixe (lancer, attendre un texte, taper, touches), relève l'écran avec ses couleurs et le convertit en page HTML (une cellule de caractère par case, caractères de bloc dessinés en couleurs pleines, fond du thème de l'application) ; cibles d'annotation par texte, par lignes ou par zone ; chaînes qui ressemblent à une clé masquées |
| `rendre.py` | dans le conteneur Playwright : ouvre chaque page, annote les cibles, enregistre l'image recadrée sur la fenêtre |
| `annoter.py` | outil d'annotation de la série RAG (rectangle, pastille, masque), repris tel quel |
| `lancer.sh` | lance un script dans le conteneur officiel `mcr.microsoft.com/playwright/python:v1.65.1-noble` (réseau de l'hôte pour joindre les interfaces web sur 127.0.0.1, aucun port publié) |

Texte de chaque écran capturé et page HTML : `banc-essai/resultats/captures/<harnais>/<chapitre>/`.
