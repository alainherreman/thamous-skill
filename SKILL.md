---
name: thamous-api-v2
description: Interroger l’API Thamous v2 logique (logic_context, text_to_structure, ask_logic, compile_logic, search_logic, replay_logic, save_logic), utiliser trace/indication/feedback, ouvrir ou enregistrer des fiches et des listes.
---

# Skill: Thamous API v2 (logique)

## Objectif

Utiliser un client CLI local pour interroger l’API Thamous v2 logique.

Cette skill sert quand il faut :

- exécuter une recherche logique ;
- diagnostiquer une mauvaise structure ;
- ouvrir une fiche ou une liste Thamous ;
- enregistrer une liste Thamous ;
- réutiliser un résultat précédent ;
- suivre un type de lien à partir d’une liste précédente.

## Principe d'exécution

- la skill doit fonctionner **sans validation intermédiaire** pour les opérations standard ;
- elle doit exécuter directement les actions normales : ouverture, enregistrement de liste, ajout à une liste, suivi de liens, préparation d'une fiche, mutations de mots-clefs et de remarques ;
- elle ne doit pas demander à l'utilisateur de confirmer une étape standard déjà demandée ;
- elle ne doit demander quelque chose que s'il manque une information indispensable ou s'il existe un vrai choix utilisateur à trancher ;
- exemple : si le nom d'une liste à enregistrer manque, il faut le demander ; sinon il faut agir directement.
- les ouvertures standard (`open-fiche`, `open-list`, `prepare-ref` quand il renvoie un formulaire) doivent lancer directement l’ouverture locale du navigateur, sans validation intermédiaire.

## Actions prises en charge

Actions actuellement prises en charge :

- **ouvrir**
  - une fiche ;
  - une liste.
- **enregistrer une liste**
  - en **extension** ;
  - en **compréhension**.
- **analyser / diagnostiquer**
  - une structure logique ;
  - une réponse ;
  - une trace.
- **nommer et réutiliser localement un résultat**
  - un résultat peut être stocké dans un historique local ;
  - la skill affiche son nom quand elle le stocke ;
  - l'historique est local au client.
- **ajouter à une liste existante**
  - à partir d’une nouvelle demande.
- **suivre un type de lien**
  - à partir d’une liste locale existante.
- **créer et supprimer des liens**
  - créer un lien entre une source et un but ;
  - supprimer un lien seulement si l’API confirme les conditions de sécurité ;
  - quand la suppression est refusée, rapporter les raisons renvoyées par l’API.
- **modifier les mots-clefs et remarques**
  - sur une référence ;
  - plusieurs mots-clefs peuvent être ajoutés en une seule opération sur une même référence ;
  - l’ajout de mots-clefs est idempotent : ne jamais retirer un mot-clef déjà présent, et ne pas créer de doublon ;
  - sans `publicite`, l’ajout d’un mot-clef se fait par défaut en `privé`, et une suppression retire toutes les occurrences du projet ;
  - sur la liste de projet ;
  - avec avertissement si le mot-clef ou la remarque est encore utilisé sur des références, puis possibilité de forcer la suppression.

Action distincte, à ne pas confondre avec l’enregistrement d’une liste :

- **préparer une fiche ou une entrée**
  - en ouvrant le formulaire Thamous prérempli avant enregistrement.

Si la demande de l’utilisateur ne correspond pas à une action réellement prise en charge par la skill et l’API, il faut le dire explicitement et ne pas improviser une autre action à la place.

## Règle importante sur le nom de liste

Si l’utilisateur demande **d’enregistrer une liste** et ne donne pas son nom, l’agent doit **demander le nom de la liste**.

Il ne doit pas inventer ce nom.

## Historique local des résultats

L’historique n’est pas un simple journal : c’est un **mécanisme général de reprise contextuelle**.

### 1. Stockage

- les résultats utiles sont stockés localement dans un historique ;
- chaque résultat stocké a :
  - un `name`
  - un `type`
  - une `value`
- les types actuellement gérés sont :
  - une table Thamous (`tbiblio`, `tpersonnes`, `tinstitutions`, `trevues`, `tliens`) avec une liste d'ids
  - `mots_clefs` avec une liste de chaînes
  - `remarques` avec une liste de chaînes
- la skill peut afficher cet historique via la commande `history`
- le stockage est local ; il ne dépend pas de l'API

### 2. Résolution des références à un résultat précédent

Quand l’utilisateur emploie une expression anaphorique comme :
- **`la liste précédente`**
- **`les références précédentes`**
- **`le résultat précédent`**
- **`la liste antérieure`**
- ou une formulation équivalente,

la skill ne doit pas traiter cela comme une nouvelle recherche autonome.
Elle doit d’abord **résoudre localement** cette expression vers un résultat déjà stocké.

### 3. Règle de compatibilité

- si l’action attend une **liste de références** ou une **liste d’ids**, la skill doit chercher dans l’historique le dernier résultat compatible de type table Thamous avec liste d’ids ;
- si l’action attend un autre type de résultat, la skill doit chercher le dernier résultat compatible avec ce type ;
- elle ne doit pas sélectionner un résultat incompatible juste parce qu’il est le plus récent.

### 4. Priorité de résolution

Ordre de priorité :
1. un résultat explicitement nommé par l’utilisateur ;
2. sinon le dernier résultat local compatible ;
3. sinon échec explicite.

Donc :
- `--base-name NOM` a priorité sur `--previous` ;
- sans nom explicite, la skill doit prendre le dernier résultat compatible, pas le dernier résultat arbitraire.

### 5. Opérations utilisant ce mécanisme

- pour ajouter un nouveau résultat à une liste stockée :
  - `add-to-list --previous --q "..."`
  - ou `add-to-list --base-name NOM --q "..."`
- pour suivre un type de lien à partir d'une liste stockée :
  - `follow-links --previous --link-type Cite --from source --to but --output-table tbiblio`
  - ou `follow-links --base-name NOM --link-type Cite --from source --to but --output-table tbiblio`
- ces opérations modifient la liste existante sauf si un autre nom est explicitement demandé.

### 6. Règle d’échec

- si aucun antécédent compatible n’existe dans l’historique, la skill doit le dire explicitement ;
- elle ne doit ni improviser un autre antécédent, ni relancer une recherche vague à la place.

## Revues, auteurs, et champs textuels

- dans `tbiblio`, le champ `editeur` d'un **article** contient en pratique le titre de la revue où l'article est publié
- de même, le champ `nom` d'une publication contient en pratique le nom de ses auteurs, en correspondance avec `tpersonnes`
- ce problème concerne surtout l'ouverture d'une liste Thamous ou toute demande dont le résultat doit être une vraie table Thamous (`trevues`, `tpersonnes`)
- dans ce cas, il faut résoudre les chaînes de `tbiblio.editeur` vers `trevues`, ou celles de `tbiblio.nom` vers `tpersonnes`
- en revanche, pour une réponse JSON, on peut retourner directement les chaînes de `tbiblio.editeur` ou `tbiblio.nom` si c'est bien cela que demande l'utilisateur

## Traductions

- une demande portant sur des **traductions** est une opération de base de Thamous ; elle doit être comprise comme telle
- quand l'utilisateur demande des *traductions de X* ou des *traductions en [langue] de X*, la recherche doit en principe passer par le **lien `Traduction`**
- il ne faut donc pas réduire cela par défaut à un simple filtre direct sur `tbiblio.langue` ou sur le titre
- sémantiquement :
  - la **source** du lien `Traduction` est la **traduction**
  - le **but** est le **texte traduit / l'œuvre d'origine**
- si l'utilisateur précise une langue, cette langue porte en principe sur la **traduction**
- si l'utilisateur précise un auteur et un titre pour l'œuvre visée, il faut comprendre :
  - `nom` = auteur de l'œuvre d'origine
  - `titre` = titre de l'œuvre d'origine
- en conséquence, pour une demande du type :
  - `les traductions en anglais de [titre] de [auteur]`
  il faut en principe chercher :
  - des `tbiblio` en anglais
  - qui sont en lien `Traduction`
  - avec une `tbiblio` dont `titre` correspond à l'œuvre visée et `nom` à son auteur
- si le moteur produit seulement une recherche directe dans `tbiblio` sans lien `Traduction`, il faut considérer cela comme suspect et utiliser la rétroaction pour corriger

## Dates et années

- dans Thamous, le champ `annee` doit être traité comme un **texte**
- une contrainte chronologique sur `annee` demande donc toujours un **traitement particulier**
- la skill ne doit pas raisonner naïvement avec :
  - `<`
  - `>`
  - `<=`
  - `>=`

Règle :
- pour une demande comme `antérieur à 1900`, il faut chercher une reformulation textuelle adaptée, par exemple `annee commence par 18`
- plus généralement, il faut raisonner sur la **forme textuelle** de l'année
- quand cette règle peut être utilement contrôlée dans la boucle de rétroaction, il faut ajouter ce contrôle

## Chemin du client

Commande canonique locale sur cet ordinateur :

- `thamous-v2 ...`

Ce wrapper est installé dans :

- `/home/alain/.local/bin/thamous-v2`

Il pointe explicitement vers le client de cette skill :

- `/media/alain/ssd2/Dropbox/programmation/skills/thamous-skill/scripts/thamous_api_v2.py`

Conséquence : la skill doit pouvoir être utilisée avec Codex lancé depuis **n’importe quel répertoire** de cet ordinateur, sans dépendre du `cwd`.

Chemins de secours, à n’utiliser que si le wrapper global est indisponible :

- `~/.codex/skills/thamous-api-v2/bin/thamous-v2 ...`
- `/media/alain/ssd2/Dropbox/programmation/skills/thamous-skill/bin/thamous-v2 ...`

Script sous-jacent, à n’utiliser qu’en secours ou pour maintenance explicite :

- `python3 /media/alain/ssd2/Dropbox/programmation/skills/thamous-skill/scripts/thamous_api_v2.py ...`


### Usage dans Codex sur cet ordinateur

Pour éviter toute validation inutile dans Codex, utiliser en priorité la commande absolue déjà autorisée :

- `python3 /media/alain/ssd2/Dropbox/programmation/skills/thamous-skill/scripts/thamous_api_v2.py ...`

Cette commande fonctionne quel que soit le répertoire courant.

Le wrapper global `thamous-v2` existe pour le terminal et les usages humains ; dans Codex, si le sandbox réclame une validation pour `thamous-v2`, revenir immédiatement à la commande absolue ci-dessus au lieu de demander une validation.

## Verrou structurel contre les variantes

Pour cette skill, il faut aligner la règle métier et la mécanique technique :

1. **une famille de commandes canonique**
   - dans Codex sur cet ordinateur, utiliser la commande absolue `python3 /media/alain/ssd2/Dropbox/programmation/skills/thamous-skill/scripts/thamous_api_v2.py ...` pour éviter les validations ;
   - dans un terminal humain, utiliser le wrapper global `thamous-v2` ;
   - ne pas improviser de `curl`, de `python -c`, ni de variante shell si le wrapper couvre le besoin ;
2. **des sous-commandes canoniques**
   - utiliser les sous-commandes réellement exposées par le client (`health`, `save-token`, `save-credentials`, `login`, `token-status`, `logic-context`, `fiche-url`, `open-fiche`, `open-list`, `text-to-structure`, `ask-logic`, `compile-logic`, `search-logic`, `replay-logic`) ;
3. **une discipline d’approbation**
   - pour l’usage standard de la skill, ne pas passer par `require_escalated` ;
   - ne pas changer de forme de commande juste pour “faire plus riche” ;
   - si une ouverture navigateur n’est pas explicitement demandée, préférer une commande qui renvoie l’URL ou le JSON plutôt qu’une ouverture locale ;
   - si un doute d’exécution apparaît, préférer la forme canonique la plus simple déjà prévue par la skill.

Conséquence pratique : dans Codex, la commande absolue Python ci-dessus est l’entrée normale sans validation ; dans un terminal humain, `thamous-v2` est l’entrée normale.

## Pré-requis

- Python 3
- `requests`
- pour utiliser réellement la skill :
  - un **compte Thamous** (login + mot de passe)
  - une **clé API fournisseur LLM**

### Obtenir les accès

- **Compte Thamous** :
  - l’utilisateur enregistre une fois ses identifiants :
    - `thamous-v2 save-credentials --login VOTRE_LOGIN`
  - puis vérifie avec :
    - `thamous-v2 token-status`
  - le client récupère automatiquement un token via `login_token`, le stocke localement et le renouvelle automatiquement si nécessaire.
- **Clé API fournisseur** : dans Thamous, ouvrir le menu `LLM`, enregistrer une clé API pour le fournisseur voulu, puis choisir un modèle. Cette clé reste enregistrée dans Thamous pour le compte utilisateur.

### Important

La skill peut être chargée sans erreur même si ces accès ne sont pas encore configurés, mais elle ne peut pas être utilisée réellement sans :

- un compte Thamous valide ;
- une clé API fournisseur LLM.

Un token déjà présent peut encore être utilisé en secours, mais ce n’est plus le mode normal pour les utilisateurs.

## Exemples représentatifs et tests

Voir `references/exemples-tests-v2.md`.

## Endpoints utiles

- `logic_context`
- `text_to_structure`
- `ask_logic`
- `compile_logic`
- `search_logic`
- `replay_logic`
- `save_logic`
- `fiche_url`
- `follow_links`
- `prepare_ref`
- `keywords_ref`
- `keywords_project`
- `remarks_ref`
- `remarks_project`

## Détermination de la sortie

Toute demande à l’API doit préciser un **format de sortie demandé** :

- `json` par défaut
- `url` quand le but est d’ouvrir dans Thamous une fiche ou une liste

## Recettes minimales

Les exemples complets et les tests représentatifs sont rassemblés dans `references/exemples-tests-v2.md`.

Rappel rapide des usages essentiels :

- Première configuration :
  - `thamous-v2 save-credentials --login VOTRE_LOGIN`
  - `thamous-v2 token-status`

- Santé :
  - `thamous-v2 health`

- Contexte logique :
  - `thamous-v2 logic-context --projet HilbertGG`

- Voir l'historique local :
  - `thamous-v2 --format table history`

- Ouvrir une fiche :
  - `thamous-v2 open-fiche --table tbiblio --id 1442`

- Ouvrir une liste :
  - `thamous-v2 open-list --q "Les livres de Klein traduits en anglais" --project perso --provider xAI --model "Grok 4"`

- Obtenir une structure logique :
  - `thamous-v2 text-to-structure --q "Les articles en espagnol sur Hilbert" --project HilbertGG --provider xAI --model "Grok 4"`

- Recherche logique avec stockage local :
  - `thamous-v2 ask-logic --q "Les livres de Klein traduits en anglais" --project HilbertGG --provider xAI --model "Grok 4" --result-name klein_traduits`

- Ajouter à la liste précédente :
  - `thamous-v2 add-to-list --previous --q "les éditions françaises" --project HilbertGG --provider xAI --model "Grok 4"`

- Suivre un lien depuis la liste précédente :
  - `thamous-v2 follow-links --previous --link-type Cite --from source --to but --output-table tbiblio --project HilbertGG`

## Règle de robustesse

- la boucle de rétroaction est bornée à **3** corrections
- au-delà, il ne faut pas insister
- il faut demander à l'utilisateur de **décomposer la demande** en étapes plus simples

## Règles d’usage

- Utiliser le wrapper canonique global `thamous-v2` ; éviter les variantes ad hoc tant qu’il couvre le besoin.
- Préférer `ask-logic` pour une recherche complète.
- Les réponses de recherche sont limitées à **100 résultats** côté API ; la skill ne doit pas essayer de modifier cette limite.
- Préférer `open-fiche` et `open-list` quand l’utilisateur demande explicitement une ouverture.
- Quand l’utilisateur ne demande pas explicitement l’ouverture, préférer l’URL canonique ou le JSON plutôt qu’une commande qui déclenche une ouverture locale du navigateur.
- Ne pas demander de validation intermédiaire pour une action standard déjà demandée ; l'exécuter directement.
- Préférer `save-list` quand l’utilisateur demande explicitement l’enregistrement d’une liste.
- Préférer `add-to-list` quand l’utilisateur veut enrichir une liste précédente.
- Préférer `follow-links` quand l’utilisateur veut appliquer un type de lien à une liste précédente.
- Si le nom de liste manque, le demander.
- Préférer `refs-by-keyword` quand l’utilisateur demande explicitement une liste d’ids pour une table, un projet et un mot-clef.
- Préférer `project-keywords` quand l’utilisateur demande simplement la liste des mots-clefs d’un projet.
- Préférer `text-to-structure --trace` quand il faut diagnostiquer la compréhension.
- Après 3 rétroactions/corrections infructueuses, arrêter la correction locale et demander à l'utilisateur de décomposer la demande en étapes plus simples.
- Utiliser `compile-logic` ou `replay-logic` quand on a déjà un JSON et qu’on veut isoler le problème sans relancer le LLM.
- Utiliser `logic-context` avant une série de tests si le projet ou le vocabulaire est incertain.

## Quand charger la référence

Si tu dois te rappeler le format exact des payloads JSON ou les capacités exactes de l’API, ouvrir `references/thamous-api-v2-endpoints.md`.
