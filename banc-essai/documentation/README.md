# Documentation détaillée du banc d'essai

Pages de référence pour faire tourner le banc. Elles supposent lue la vue d'ensemble du [README du banc](../README.md).

| Page | Pour |
|---|---|
| [modele-et-fournisseur.md](modele-et-fournisseur.md) | brancher le modèle : OpenRouter ou portail compatible OpenAI, mandataire et certificat d'entreprise, vérification du portail, prix et plafonds |
| [goldset.md](goldset.md) | faire tourner le banc sur un jeu de PDF et de réponses attendues : forme attendue, import, validation du schéma, consignes, démonstration |
| [lancer-un-essai.md](lancer-un-essai.md) | lancer un essai, le suivre, l'arrêter proprement, lire ses résultats |
| [securite-et-donnees.md](securite-et-donnees.md) | ce que la cage et le relais protègent, garde-fous git, données qui ne quittent pas le poste, limites |

Pages techniques de chaque composant, à côté de son code :

| Composant | Page |
|---|---|
| Cage (bubblewrap, réseau filtré, ressources, preuves) | [`banc-essai/cage/README.md`](../cage/README.md) |
| Relais du modèle (LiteLLM, clés, journal des appels) | [`banc-essai/traces/README.md`](../traces/README.md) |
| API de soumission et notation | [`banc-essai/evaluation/README.md`](../evaluation/README.md) |
| Corpus public (rapports fictifs, dossiers) | [`banc-essai/corpus/README.md`](../corpus/README.md) |
| Résultats des essais | [`banc-essai/resultats/README.md`](../resultats/README.md) |

Harnais (installation, configuration, lancement, constats) : [`harnais/README.md`](../../harnais/README.md).
