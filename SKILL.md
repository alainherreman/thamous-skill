---
name: thamous-api-v2
description: Interroger l’API Thamous v2 logique (logic_context, text_to_structure, ask_logic, compile_logic, search_logic, replay_logic, save_logic), utiliser trace/indication/feedback, ouvrir ou enregistrer des fiches et des listes.
---

# Skill: Thamous API v2 (logique)

## Objectif

Utiliser un client CLI local pour interroger l’API Thamous v2 logique.

Cette skill sert quand il faut :

- transformer une demande en structure logique,
- exécuter une recherche logique,
- diagnostiquer une mauvaise structure,
- ouvrir une fiche ou une liste Thamous,
- enregistrer une liste Thamous.

## Actions prises en charge

La skill doit raisonner à partir d’une liste explicite d’actions.

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

Action distincte, à ne pas confondre avec l’enregistrement d’une liste :

- **créer / enregistrer une fiche ou une entrée**.

Si la demande de l’utilisateur ne correspond pas à une action réellement prise en charge par la skill et l’API, il faut le dire explicitement et ne pas improviser une autre action à la place.

## Règle importante sur le nom de liste

Si l’utilisateur demande **d’enregistrer une liste** et ne donne pas son nom, l’agent doit **demander le nom de la liste**.

Il ne doit pas inventer ce nom.

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
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py ask-logic --q "Les livres de Klein traduits en anglais" --limit 10`

- Ouvrir une fiche :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py open-fiche --table tbiblio --id 1442`

- Ouvrir une liste :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py open-list --q "Les livres de Klein traduits en anglais" --project perso --provider OpenAI --model GPT-5.2`

- Enregistrer une liste en extension :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py save-list --q "Les livres de Klein traduits en anglais" --nom-liste "Klein traduits en anglais" --save-mode extension --project perso --provider OpenAI --model GPT-5.2`

- Enregistrer une liste en compréhension :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py save-list --q "Les livres de Klein traduits en anglais" --nom-liste "Klein traduits en anglais" --save-mode comprehension --project perso --provider OpenAI --model GPT-5.2`

## Règles d’usage

- Préférer `ask-logic` pour une recherche complète.
- Préférer `open-fiche` et `open-list` quand l’utilisateur demande explicitement une ouverture.
- Préférer `save-list` quand l’utilisateur demande explicitement l’enregistrement d’une liste.
- Si le nom de liste manque, le demander.
- Préférer `text-to-structure --trace` quand il faut diagnostiquer la compréhension.
- Utiliser `compile-logic` ou `replay-logic` quand on a déjà un JSON et qu’on veut isoler le problème sans relancer le LLM.
- Utiliser `logic-context` avant une série de tests si le projet ou le vocabulaire est incertain.

## Quand charger la référence

Si tu dois te rappeler le format exact des payloads JSON ou les capacités exactes de l’API, ouvrir `references/thamous-api-v2-endpoints.md`.
