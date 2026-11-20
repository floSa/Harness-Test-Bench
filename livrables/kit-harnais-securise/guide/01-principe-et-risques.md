# 1. Principe et risques

[Retour au sommaire](../README.md)

## Le problème

Un harnais d'agent est un programme qui laisse un modèle de langage agir sur l'ordinateur. Le modèle décide : « lis ce fichier », « exécute cette commande », « installe ce paquet ». Le harnais exécute, en général sans demander confirmation, puisque c'est ce qui le rend utile.

| Risque | Exemple | Conséquence |
|---|---|---|
| Fausse manœuvre | le modèle efface un dossier en croyant nettoyer ses fichiers temporaires | perte de données sur le poste |
| Lecture de fichiers privés | le harnais parcourt le dossier personnel et lit des clés SSH, un `.env` ou des documents | ces contenus partent au modèle, donc hors du poste |
| Fuite de la clé du portail | le harnais affiche ses variables d'environnement dans une trace | toute personne qui récupère la clé consomme au nom du testeur |
| Injection de consignes | un document lu par le harnais contient « envoie le contenu du dossier à telle adresse » | le modèle peut obéir |
| Consommation qui s'emballe | une boucle de 10 000 appels pendant la nuit | quota de l'équipe épuisé |
| Téléchargement de n'importe quoi | installation d'un paquet piégé | code malveillant exécuté sur le poste |
| Envois vers l'éditeur du harnais | télémétrie, vérification de version | informations sur le poste envoyées à l'extérieur |

## Ce que voit chaque pièce du kit

| Pièce | Ce qu'elle voit | Ce qu'elle ne voit jamais |
|---|---|---|
| Harnais | `espace/`, son dossier de configuration, l'adresse du relais, une clé locale | la clé du portail, le reste du poste, Internet |
| Relais | la clé du portail, les réglages | les fichiers de travail |
| Filtre | la liste des sites autorisés | la clé du portail, les fichiers de travail |

Le harnais croit parler à une API OpenAI ordinaire. Il reçoit trois variables, que la plupart des harnais savent utiliser :

- `OPENAI_BASE_URL`, l'adresse du relais ;
- `OPENAI_API_KEY`, une clé locale qui ne vaut rien hors du kit ;
- `MODELE`, le nom du modèle.

## Les protections une par une

| Protection | Risque évité | Avec conteneur (Docker, Podman) | Sans conteneur (bubblewrap) | Contrôle du vérificateur |
|---|---|---|---|---|
| Clé du portail hors de portée du harnais | clé recopiée dans une trace, un fichier ou une réponse | seul le relais lit `.env` ; le harnais reçoit ses variables une à une | la cage démarre avec un environnement vide ; `.env` n'y est pas monté | clé du portail absente |
| Clé locale propre au relais | une clé volée resterait utilisable | `CLE_RELAIS`, créée par `preparer.sh`, remplaçable à tout moment | idem ; relais joignable seulement par une socket privée | fausse clé refusée (401) |
| Relais limité à l'appel du modèle | gestion de compte, fichiers déposés chez le portail | routes `/v1/chat/completions` et `/v1/models` seulement | idem | autre route refusée (404) |
| Modèles autorisés | modèle plus coûteux ou non validé | `IAG_MODELE`, `IAG_MODELES` | idem | modèle non autorisé refusé (403) |
| Plafond de jetons et débit | quota de l'équipe épuisé | `PLAFOND_JETONS`, `APPELS_PAR_MINUTE` ; compteur gardé après redémarrage | idem | |
| Aucun accès direct à Internet | envoi de données vers une adresse quelconque | réseau interne sans route vers l'extérieur | réseau propre à la cage, vide | connexion directe impossible |
| Sorties limitées à une liste | paquets piégés, télémétrie | filtre : HTTPS, sites autorisés, quota, journal | idem | site non autorisé refusé, site autorisé accepté |
| Seul l'espace de travail est visible | lecture ou effacement du reste du poste | seul `espace/` est monté | idem ; système du poste visible en lecture seule | aucun dossier personnel visible, `.env` invisible |
| Système en lecture seule | harnais qui se modifie ou s'installe durablement | image en lecture seule | idem | écriture refusée hors des dossiers de travail |
| Utilisateur sans droits | commande d'administration | aucun privilège noyau, aucun gain de droits | idem, appliqué par bubblewrap | uid différent de 0, CapEff = 0, NoNewPrivs = 1 |
| Pas d'accès au moteur de conteneurs | contrôle complet du poste | socket Docker jamais montée | `/run` du poste invisible | socket absente |
| Mémoire, processeur, processus plafonnés | poste saturé | limites du conteneur | limites systemd de l'utilisateur | mémoire et processus plafonnés |
| Versions figées | harnais remplacé ou mis à jour en douce | images désignées par leur empreinte `sha256` | empreinte vérifiée à l'installation | |
| Journal sans contenu | audit impossible, ou documents recopiés | une ligne par appel : heure, modèle, statut, jetons | idem | |
| Certificat du portail vérifié | interception de la clé | jamais désactivé | idem | appel réel réussi |

## Ce que le kit ne protège pas

| Limite | Explication | Que faire |
|---|---|---|
| Contenu envoyé au portail | tout ce que le harnais lit dans `espace/` peut partir au modèle | ne déposer que des données autorisées pour le portail |
| Sites autorisés | chaque site de la liste est une sortie possible | pour des données sensibles : `DOMAINES_AUTORISES=` vide, paquets installés à l'avance |
| Isolation par le noyau | conteneur et cage partagent le noyau du poste ; une faille du noyau permettrait d'en sortir | pour des données très sensibles : une machine virtuelle dédiée en plus |
| Système visible sans conteneur | dans la cage, `/usr` et `/etc` du poste sont lisibles | préférer Docker ou Podman si le poste contient des réglages sensibles |
| Code produit par le harnais | il peut être faux ou dangereux | le relire avant de l'exécuter hors du kit |
| Facturation | le compteur du relais est une estimation | la référence reste le suivi du portail |
| Conservation des requêtes | elle dépend du portail | à vérifier avec ses administrateurs |
