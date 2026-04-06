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

Action distincte, à ne pas confondre avec l’enregistrement d’une liste :

- **créer / enregistrer une fiche ou une entrée**.

Si la demande de l’utilisateur ne correspond pas à une action réellement prise en charge par la skill et l’API, il faut le dire explicitement et ne pas improviser une autre action à la place.

## Règle importante sur le nom de liste

Si l’utilisateur demande **d’enregistrer une liste** et ne donne pas son nom, l’agent doit **demander le nom de la liste**.

Il ne doit pas inventer ce nom.

## Historique local des résultats

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
- pour ajouter un nouveau résultat à une liste stockée :
  - `add-to-list --previous --q "..."`
  - ou `add-to-list --base-name NOM --q "..."`
- pour suivre un type de lien à partir d'une liste stockée :
  - `follow-links --previous --link-type Cite --from source --to but --output-table tbiblio`
  - ou `follow-links --base-name NOM --link-type Cite --from source --to but --output-table tbiblio`
- ces opérations modifient la liste existante sauf si un autre nom est explicitement demandé
- la `liste précédente` désigne le dernier résultat local dont le type est une table Thamous avec une liste d'ids
- si l'utilisateur dit **`la liste précédente`**, **`la liste antérieure`**, **`le résultat précédent`** ou une formulation équivalente, la skill doit comprendre qu'il faut utiliser ce dernier résultat local compatible

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

Après installation de la skill, utiliser :

- `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py ...`

## Pré-requis

- Python 3
- `requests`
- pour utiliser réellement la skill :
  - un **token Thamous**
  - une **clé API fournisseur LLM**

### Obtenir les accès

- **Token Thamous** : soit l'obtenir directement par l'API avec `login_token` en fournissant `login` et `mot de passe`, soit le fournir à la skill de l'une des manières suivantes : `THAMOUS_TOKEN`, `THAMOUS_TOKEN_FILE`, ou éventuellement Bitwarden si cette solution est disponible.
- **Clé API fournisseur** : dans Thamous, ouvrir le menu `LLM`, enregistrer une clé API pour le fournisseur voulu, puis choisir un modèle. Cette clé reste enregistrée dans Thamous pour le compte utilisateur.

### Important

La skill peut être chargée sans erreur même si ces accès ne sont pas encore configurés, mais elle ne peut pas être utilisée réellement sans :

- un token Thamous ;
- une clé API fournisseur LLM.

Bitwarden peut être utilisé pour fournir le token Thamous, mais ce n'est qu'une possibilité parmi d'autres.

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

## Détermination de la sortie

Toute demande à l’API doit préciser un **format de sortie demandé** :

- `json` par défaut
- `url` quand le but est d’ouvrir dans Thamous une fiche ou une liste

## Recettes minimales

- Santé :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py health`

- Obtenir un token Thamous par l'API :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py login-token --login MON_LOGIN --password MON_MOT_DE_PASSE`

- Obtenir et enregistrer le token dans un fichier :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py login-token --login MON_LOGIN --password MON_MOT_DE_PASSE --write-token-file ~/.config/thamous/token`

- Contexte logique :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py logic-context --projet HilbertGG`

- Texte -> résultats :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py ask-logic --q "Les livres de Klein traduits en anglais"`
  - la skill affiche alors aussi un nom de résultat sur stderr, par ex. `[result_name] ...`

- Voir l'historique local :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py --format table history`

- Ouvrir une fiche :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py open-fiche --table tbiblio --id 1442`

- Ouvrir une liste :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py open-list --q "Les livres de Klein traduits en anglais" --project perso --provider OpenAI --model GPT-5.2`

- Enregistrer une liste en extension :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py save-list --q "Les livres de Klein traduits en anglais" --nom-liste "Klein traduits en anglais" --save-mode extension --project perso --provider OpenAI --model GPT-5.2`

- Enregistrer une liste en compréhension :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py save-list --q "Les livres de Klein traduits en anglais" --nom-liste "Klein traduits en anglais" --save-mode comprehension --project perso --provider OpenAI --model GPT-5.2`

- Suivre un lien depuis la liste précédente :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py follow-links --previous --link-type Cite --from source --to but --output-table tbiblio --project HilbertGG`

## Règles d’usage

- Préférer `ask-logic` pour une recherche complète.
- Les réponses de recherche sont limitées à **100 résultats** côté API ; la skill ne doit pas essayer de modifier cette limite.
- Préférer `open-fiche` et `open-list` quand l’utilisateur demande explicitement une ouverture.
- Préférer `save-list` quand l’utilisateur demande explicitement l’enregistrement d’une liste.
- Préférer `add-to-list` quand l’utilisateur veut enrichir une liste précédente.
- Préférer `follow-links` quand l’utilisateur veut appliquer un type de lien à une liste précédente.
- Si le nom de liste manque, le demander.
- Préférer `text-to-structure --trace` quand il faut diagnostiquer la compréhension.
- Utiliser `compile-logic` ou `replay-logic` quand on a déjà un JSON et qu’on veut isoler le problème sans relancer le LLM.
- Utiliser `logic-context` avant une série de tests si le projet ou le vocabulaire est incertain.

## Quand charger la référence

Si tu dois te rappeler le format exact des payloads JSON ou les capacités exactes de l’API, ouvrir `references/thamous-api-v2-endpoints.md`.
