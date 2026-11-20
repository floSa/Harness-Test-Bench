# 8. Organiser un test à plusieurs

[Retour au sommaire](../README.md)

| Point | Recommandation | Pourquoi |
|---|---|---|
| Clés du portail | une clé personnelle par testeur ; jamais une seule clé pour l'équipe | révocation individuelle, quota par personne, consommation attribuable |
| Kit | une copie par testeur, sur son poste | personne ne partage son espace de travail ni sa clé |
| Réglages communs | même `.env.exemple` (sans clé), mêmes plafonds, même modèle | comparer les harnais à conditions égales |
| Version du harnais | figée dans `harnais/Dockerfile`, ou même archive et même empreinte sans conteneur | même comportement pour tous |
| Résultats à collecter | `journaux/` (aucun contenu) et le code produit dans `espace/` | mesurer et relire, sans transmettre de clé |
| Fin du test | révoquer la clé du portail, supprimer `.env` et la configuration du harnais (`down -v`, ou `sans-conteneur/maison/`) | plus aucune clé valable sur les postes |
