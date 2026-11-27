# PIAG : mettre en place le banc sur un poste d'entreprise

Branche `PIAG` : le banc des harnais, préparé pour un poste d'entreprise sous WSL, où le modèle (Gemini 3.7 Flash) est servi par le portail IAG, compatible OpenAI, et où les documents sont un goldset de l'équipe.

| Fichier | Rôle |
|---|---|
| [AMORCAGE.md](AMORCAGE.md) | consigne à donner à un agent de code sur le poste : mise en place et vérifications, sans aucun essai (diagnostic du poste, portail, tests, données du goldset, API de test, branchement de chaque harnais, documentation mise à jour pour ce poste, bilan) |
| [identite.exemple](identite.exemple) | modèle de `identite.local` : identité git du poste (utilisateur, adresse, co-auteur des commits) |
| `identite.local`, `etat-du-poste.md` | remplis sur le poste, jamais versionnés |

## Mise en route sur le poste

```bash
git clone --depth 1 --single-branch -b PIAG https://github.com/floSa/Harness-Test-Bench.git
cd Harness-Test-Bench
outils/installer-garde-fous.sh --poste-entreprise
cp piag/identite.exemple piag/identite.local      # puis le remplir
```

`--depth 1 --single-branch` : seul le dernier état de la branche est téléchargé, sans l'historique du dépôt.

Copier ensuite le goldset dans `goldset/` à la racine (forme attendue : [banc-essai/documentation/goldset.md](../banc-essai/documentation/goldset.md)), puis donner à l'agent de code :

```text
Lis piag/AMORCAGE.md et exécute-le niveau par niveau, en t'arrêtant à chaque décision réservée.
```

À la fin, `piag/etat-du-poste.md` dit, point par point, ce qui est en place et vérifié ; le premier essai se lance ensuite à la main (commande donnée dans ce bilan).
