---
name: thamous-api-v2
description: Interroger l’API Thamous v2 logique (logic_context, text_to_structure, ask_logic, compile_logic, search_logic, replay_logic), utiliser trace/indication/feedback, et diagnostiquer une structure ou une réponse.
---

# Skill: Thamous API v2 (logique)

## Objectif

Utiliser un client CLI local pour interroger l’API Thamous v2 logique :

- `health`
- `logic_context`
- `text_to_structure`
- `ask_logic`
- `compile_logic`
- `search_logic`
- `replay_logic`

Cette skill sert quand il faut :

- transformer une demande en structure logique,
- exécuter une recherche logique,
- diagnostiquer une mauvaise structure,
- comparer des modèles,
- utiliser `trace`, `indication` ou `feedback`.

## Chemin du client

Après installation de la skill, utiliser :

- `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py ...`

## Pré-requis

- Python 3
- `requests`
- un token Thamous pour la prod :
  - `THAMOUS_TOKEN`
  - ou `THAMOUS_TOKEN_FILE`
  - ou Bitwarden, comme dans la skill v1

## Endpoints utiles

- `logic_context` : vocabulaire et projets
- `text_to_structure` : texte -> structure logique
- `ask_logic` : texte -> résultats
- `compile_logic` : structure -> SQL
- `search_logic` : structure -> résultats
- `replay_logic` : rejouer un JSON édité
- `fiche_url` : obtenir l’URL d’ouverture d’une fiche à partir de `id` et `table`

## Détermination de la sortie

Toute demande à l’API doit préciser un **format de sortie demandé** :

- `json` par défaut
- `url` quand le but est d’ouvrir dans Thamous une fiche ou une liste

La skill doit donc toujours raisonner en deux temps :

1. déterminer l’objet demandé ;
2. déterminer le **format de sortie** attendu.

Règles :

- pour analyser, diagnostiquer, comparer, inspecter : demander `format=json` ;
- pour ouvrir dans Thamous : demander `format=url` ;
- `--format` du client CLI ne règle que **l’affichage local** ;
- `--response-format` règle le **format demandé à l’API**.

## Recettes minimales

- Santé :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py health`

- Contexte logique :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py logic-context --projet HilbertGG`

- Texte -> structure :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py text-to-structure --q "Les articles de Klein ayant été traduits" --trace`

- Texte -> résultats :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py ask-logic --q "Les livres de Klein traduits en anglais" --limit 10`

- Avec indication/feedback :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py text-to-structure --q "Traductions par Stillwell" --indication "lever l'ambiguïté entre texte traduit et traduction produite" --trace`
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py text-to-structure --q "Les études en anglais sur la controverse entre Leibniz et Newton" --feedback "la structure précédente visait les personnes au lieu du lien Controverse" --reformulation-precedente "je cherche des études sur Leibniz et Newton"`

- Compiler une structure stockée dans un fichier JSON :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py compile-logic --payload-file structure.json`

- Rejouer un JSON édité :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py replay-logic --payload-file replay.json`

- Obtenir l’URL d’une fiche :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py fiche-url --table tbiblio --id 1442 --response-format url`

- Ouvrir une fiche dans le navigateur :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py open-fiche --table tbiblio --id 1442`

- Obtenir l’URL d’une liste logique :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py ask-logic --q "Les livres de Klein traduits en anglais" --project perso --provider OpenAI --model GPT-5.2 --response-format url`

- Ouvrir une liste logique dans le navigateur :
  - `python3 ~/.codex/skills/thamous-api-v2/scripts/thamous_api_v2.py open-list --q "Les livres de Klein traduits en anglais" --project perso --provider OpenAI --model GPT-5.2`

## Règles d’usage

- Préférer `ask-logic` pour une recherche complète.
- Toujours choisir explicitement un format de sortie API : `json` par défaut, `url` pour une ouverture.
- Quand il faut ouvrir une fiche Thamous, utiliser `fiche-url --response-format url` pour récupérer l’URL canonique ; si l’utilisateur demande explicitement l’ouverture, utiliser `open-fiche`.
- Quand il faut ouvrir une liste de résultats Thamous, utiliser `ask-logic --response-format url` ; si l’utilisateur demande explicitement l’ouverture, utiliser `open-list`.
- Préférer `text-to-structure --trace` quand il faut diagnostiquer la compréhension.
- Utiliser `compile-logic` ou `replay-logic` quand on a déjà un JSON et qu’on veut isoler le problème sans relancer le LLM.
- Utiliser `logic-context` avant une série de tests si le projet ou le vocabulaire est incertain.

## Quand charger la référence

Si tu dois :

- te rappeler le format exact des payloads JSON,
- comparer `search` / `derive` / `clarify`,
- comprendre `trace`, `indication`, `feedback`,

alors ouvre `references/thamous-api-v2-endpoints.md`.

## Limites actuelles à garder en tête

- La logique sur les objets `tliens` imbriqués est encore plus fragile que les cas simples sur `tbiblio`.
- Les cas dérivés (`derive_*`) sont une liste fermée ; ne pas les utiliser comme fourre-tout.
- Pour un diagnostic fin, préférer `trace=true` et, si nécessaire, `replay_logic`.
