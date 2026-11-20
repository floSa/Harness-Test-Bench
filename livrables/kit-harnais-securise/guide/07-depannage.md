# 7. Dépannage

[Retour au sommaire](../README.md)

## Points à confirmer au premier lancement

Ces points dépendent de la configuration du poste. Le vérificateur les signale.

| Point | Risque | Signe | Que faire |
|---|---|---|---|
| Limites de mémoire et de processus sous Podman | un harnais qui s'emballe peut saturer le poste | « mémoire plafonnée » ou « nombre de processus plafonné » `NON CONFORME` | demander au service informatique la délégation cgroups v2 (mémoire, processus) pour `user@.service`, ou passer en mode sans conteneur |
| Autorisation AppArmor de bubblewrap | le mode sans conteneur ne démarre pas | `setting up uid map: Permission denied` | activer le profil `bwrap-userns-restrict` ([04-installation-sans-conteneur.md](04-installation-sans-conteneur.md), étape 0) |
| Proxy et autorité de certification de l'entreprise | ni portail ni paquets accessibles | appel réel au modèle en 502, ou site autorisé refusé | renseigner `HTTPS_PROXY` et `SSL_CERT_FILE` ([06-reglages.md](06-reglages.md)) |
| Accès au portail IAG depuis le poste | aucun appel possible | appel réel au modèle en erreur | vérifier l'adresse, la clé et l'accès réseau avec les administrateurs du portail |

## Problèmes fréquents

| Symptôme | Cause probable | Correction |
|---|---|---|
| `relais : clé du relais invalide` (401) | `.env` modifié sans redémarrer le relais | `docker compose up -d relais` (sans conteneur : nouvelle session) |
| 404 venant du portail | `IAG_URL` sans `/v1`, ou avec un chemin en trop | `https://…/v1`, sans `/chat/completions` |
| 401 ou 403 venant du portail | clé refusée, ou mauvais en-tête | vérifier `IAG_CLE` et `IAG_ENTETE_CLE` |
| `relais : portail injoignable` (502) | proxy ou certificat d'entreprise | `HTTPS_PROXY`, `SSL_CERT_FILE` ; journal : `docker compose logs relais` ou `journaux/relais.log` |
| `relais : modèle non autorisé` (403) | le harnais demande un autre nom de modèle | lui donner exactement `$MODELE`, ou ajouter le modèle à `IAG_MODELES` |
| 400 sur `stream_options` | portail qui refuse ce champ | `COMPTER_FLUX=0` |
| le harnais répond mais n'agit pas | modèle sans appel d'outils | changer de modèle ; vérifier avec le portail |
| `pip install` ou `npm install` échoue | site absent de la liste, ou quota atteint | `journaux/telechargements.jsonl`, puis `DOMAINES_AUTORISES` |
| fichiers de `espace/` non modifiables | Docker : `preparer.sh` non relancé ; Podman : complément oublié | Docker : `bash preparer.sh`, puis `docker compose build` ; Podman : `export COMPOSE_FILE=compose.yaml:compose.podman.yaml` |
| Podman : `invalid choice: 'essai'` | podman-compose 1.0.6 sans option `--profile` | `podman compose up -d relais filtre faux-portail` |
| `systemd-run --user indisponible` | WSL sans systemd | `[boot] systemd=true` dans `/etc/wsl.conf`, puis redémarrer WSL |
| le harnais signale un catalogue ou une mise à jour injoignable | sortie vers l'éditeur refusée par le filtre | normal, sans effet sur son travail |
