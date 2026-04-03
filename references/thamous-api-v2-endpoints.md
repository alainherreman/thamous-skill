# Thamous API v2 — endpoints utiles

## Base URL par défaut

- Prod : `https://thamous.ouvaton.org/thamous/php/api/v2/index.php`

Le client accepte `--base-url` ou `THAMOUS_V2_BASE_URL`.

## Auth

- `health` : sans auth
- le reste : Bearer token

Le client lit, dans cet ordre :

1. `THAMOUS_TOKEN`
2. `THAMOUS_TOKEN_FILE`
3. Bitwarden (`bw get item ...`)

## Format de sortie demandé

Toute requête doit préciser un paramètre `format` :

- `json` par défaut
- `url` quand l’endpoint sait retourner directement une URL

Dans le client CLI :

- `--response-format` = format demandé à l’API
- `--format` = format d’affichage local du client

Actuellement :

- `fiche_url` supporte `format=url`
- `ask_logic` supporte `format=url` pour une recherche directe (`mode=search`) et retourne alors l’URL de la liste Thamous correspondante
- les autres endpoints restent en pratique sur `json` tant qu’ils ne gèrent pas explicitement `url`

## GET

### `health`

Sans paramètres.

### `logic_context`

Paramètres :

- `projet` facultatif

Retourne :

- `default_project`
- `project`
- `projects`
- `types_biblio`
- `types_lien`
- `mots_clefs`
- `mots_clefs_details`

## POST JSON

### `text_to_structure`

Payload fréquent :

```json
{
  "q": "Les articles de Klein ayant été traduits",
  "project": "perso",
  "provider": "OpenAI",
  "model": "GPT-5.2",
  "trace": true
}
```

Clés utiles supplémentaires :

- `indication`
- `feedback`
- `reformulation_precedente`
- `structure_response_precedente`

Retourne notamment :

- `mode`
- `derive`
- `structure_response`
- `trace.text_to_structure`

### `ask_logic`

Même entrée de base que `text_to_structure`, plus éventuellement :

- `limit`
- `offset`
- `order1`
- `order2`
- `asc_desc1`
- `asc_desc2`
- `derive_limit`

Retourne notamment :

- en `json` :
  - `mode`
  - `derive`
  - `structure_response`
  - `compiled`
  - `results`
  - `total`
- en `url` (si `mode=search`) :
  - l’URL texte brut de la liste Thamous correspondant au résultat

### `compile_logic`

Payload :

```json
{
  "project": "HilbertGG",
  "structure": { "...": "..." }
}
```

Retourne :

- `compiled.sql`
- `compiled.params`

### `search_logic`

Payload :

```json
{
  "project": "HilbertGG",
  "structure": { "...": "..." },
  "limit": 20,
  "offset": 0
}
```

Retourne :

- `results`
- `total`
- `compiled`

### `replay_logic`

Utilisé pour rejouer un JSON déjà édité, typiquement depuis Trace API v2.

## Modes

- `search` : recherche directe
- `derive` : liste fermée de post-traitements
  - `derive_coauthors`
  - `derive_translators`
  - `derive_editors`
  - `derive_prefacers`
- `clarify` : l’agent demande une précision

## Conseils de diagnostic

- Si la compréhension est mauvaise, commencer par `text_to_structure --trace`.
- Si le JSON est bon mais pas le résultat, passer par `compile_logic` ou `replay_logic`.
- Si le vocabulaire projet semble en cause, commencer par `logic_context`.

### `fiche_url`

Paramètres :

- `id` requis
- `table` requis
- `projet` facultatif
- `format` facultatif (`json` par défaut, `url` possible)

Retourne :

- en `json` :
  - `session_ref`
  - `form_url`
  - `ref_url`
- en `url` :
  - l’URL `form_url` seule, en texte brut
