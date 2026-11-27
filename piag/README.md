# PIAG : faire tourner le banc sur un poste d'entreprise

Branche `PIAG` : le banc des harnais, préparé pour un poste d'entreprise où le modèle est servi par un portail compatible OpenAI et où les documents sont un goldset de l'équipe.

| Fichier | Rôle |
|---|---|
| [AMORCAGE.md](AMORCAGE.md) | consigne à donner à un agent de code sur le poste : sept niveaux, du diagnostic du poste à la comparaison des harnais |
| `journal-poste.md`, `diagnostic.md`, `comparaison.md` | écrits par l'agent sur le poste, jamais versionnés |

## Mise en route sur le poste

```bash
git clone -b PIAG https://github.com/floSa/Harness-Test-Bench.git
cd Harness-Test-Bench
outils/installer-garde-fous.sh --poste-entreprise
```

Puis copier le goldset dans `goldset/` à la racine (forme : [banc-essai/documentation/goldset.md](../banc-essai/documentation/goldset.md)) et donner à l'agent de code :

```text
Lis piag/AMORCAGE.md et exécute-le niveau par niveau, en t'arrêtant à chaque décision réservée.
```
