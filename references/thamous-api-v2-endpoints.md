# Thamous API v2 — endpoints utiles

## Base URL par défaut

- Prod : `https://thamous.ouvaton.org/thamous/php/api/v2/index.php`

## Auth

- `health` : sans auth
- `login_token` : sans Bearer token, avec `login` + `password`
- le reste : Bearer token

Le client lit, dans cet ordre :

1. `THAMOUS_TOKEN`
2. `THAMOUS_TOKEN_FILE`
3. Bitwarden (`bw get item ...`)

## Formats de sortie

- `json` par défaut
- `url` quand l’endpoint sait retourner directement une URL Thamous

## Actions explicites

Actions actuellement prises en charge :

- ouvrir une fiche ;
- ouvrir une liste ;
- enregistrer une liste en extension ;
- enregistrer une liste en compréhension ;
- ajouter à une liste précédente ;
- suivre un type de lien depuis une liste précédente ;
- diagnostiquer une structure ou une réponse.

Si l’utilisateur demande d’enregistrer une liste sans donner son nom, il faut demander ce nom.

Pour les mutations de mots-clefs/remarques de projet, l’utilisateur doit être administrateur du projet.
Pour les mutations sur une référence, le mot-clef ou la remarque doit appartenir au projet.

## Endpoints utiles

### `login_token`

POST JSON.

Entrée :
- `login`
- `password`

Retourne :
- `token`
- `signature`
- `login`
- `nom`
- `projects`

### `fiche_url`

GET.

Paramètres :
- `id`
- `table`
- `projet` facultatif
- `format` (`json` ou `url`)

### `logic_context`

GET.

Paramètres :
- `projet` facultatif

### `text_to_structure`

POST JSON.

Entrée fréquente :
- `q`
- `project`
- `provider`
- `model`
- `trace`
- `indication`
- `feedback`
- `reformulation_precedente`

### `ask_logic`

POST JSON.

Entrée fréquente :
- `q`
- `project`
- `provider`
- `model`
- `format`
- `trace`

Retourne :
- résultats JSON ;
- ou URL d’une liste Thamous si `format=url`.

### `save_logic`

POST JSON.

Entrée :
- `q`
- `project`
- `provider`
- `model`
- `nom_liste`
- `save_mode` : `extension` ou `comprehension`
- `format` : `json` ou `url`

Retourne :
- en `json` : `id_sql`, `url`, `save_mode`, `nom_liste` ;
- en `url` : l’URL de la liste enregistrée dans Thamous.

Règle :
- `save_mode=comprehension` n’est pris en charge que pour `mode=search`.

### `follow_links`

POST JSON.

Entrée :
- `project`
- `input_table`
- `input_ids`
- `link_type`
- `from` : `source` ou `but`
- `to` : `source` ou `but`
- `output_table`

Retourne :
- `type`
- `value` (liste d’ids)
- `total`
- `meta`


### `keywords_ref`

POST JSON.

Entrée :
- `project`
- `table`
- `id`
- `action` : `add` ou `remove`
- `mot_clef`
- `publicite` facultative

Contrôles :
- utilisateur administrateur du projet ;
- le mot-clef doit appartenir à la liste du projet.

Retour :
- `mots_clefs` mis à jour ;
- `suggestions` si le mot-clef demandé n'existe pas dans le projet.

### `keywords_project`

POST JSON.

Entrée :
- `project`
- `action` : `add` ou `remove`
- `mot_clef`
- `definition` facultative
- `force` facultatif

Contrôles :
- utilisateur administrateur du projet ;
- suppression avec avertissement si le mot-clef est encore utilisé sur des références du projet ; possibilité de forcer.

### `remarks_ref`

POST JSON.

Entrée :
- `project`
- `table`
- `id`
- `action` : `add` ou `remove`
- `remarque`
- `publicite` facultative

Contrôles :
- utilisateur administrateur du projet ;
- la remarque doit appartenir à la liste du projet.

Retour :
- `remarques` mises à jour ;
- `suggestions` si la remarque demandée n'existe pas dans le projet.

### `remarks_project`

POST JSON.

Entrée :
- `project`
- `action` : `add` ou `remove`
- `remarque`
- `force` facultatif

Contrôles :
- utilisateur administrateur du projet ;
- suppression avec avertissement si la remarque est encore utilisée sur des références du projet ; possibilité de forcer.
