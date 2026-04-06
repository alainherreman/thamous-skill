# thamous-skill

Skill Codex pour interroger l’API Thamous v2 logique.

Contenu :
- `SKILL.md`
- `references/`
- `scripts/thamous_api_v2.py`
- `agents/openai.yaml`

Utilisation réelle :
- nécessite un **token Thamous** ;
- nécessite aussi une **clé API fournisseur LLM** ;
- le token Thamous peut être obtenu par l'API via `login_token`, puis fourni par `THAMOUS_TOKEN`, `THAMOUS_TOKEN_FILE` ou éventuellement Bitwarden ;
- la clé fournisseur s'enregistre dans le menu `LLM`, où l'on choisit aussi le modèle.

Actions explicites actuellement prises en charge :
- ouvrir une fiche ;
- ouvrir une liste ;
- enregistrer une liste en extension ;
- enregistrer une liste en compréhension ;
- stocker localement un résultat nommé ;
- ajouter un résultat à une liste locale précédente ;
- suivre un type de lien depuis une liste locale précédente ;
- diagnostiquer une structure ou une réponse.

Si une demande ne correspond pas à l’une de ces actions, la skill doit le dire explicitement au lieu d’improviser.

## Historique local

Les résultats de `ask-logic` peuvent être stockés localement :
- avec un nom automatique ;
- ou avec `--result-name`.

Commandes utiles :
- `python3 scripts/thamous_api_v2.py --format table history`
- `python3 scripts/thamous_api_v2.py add-to-list --previous --q "..." --project ... --provider ... --model ...`
- `python3 scripts/thamous_api_v2.py follow-links --previous --link-type Cite --from source --to but --output-table tbiblio --project ...`

Par défaut, `add-to-list` et `follow-links` réutilisent la liste locale précédente compatible.
La “liste précédente” est le dernier résultat local dont le type est une table Thamous avec une liste d’ids.

## Dates

Le champ `annee` doit être traité comme un **texte**.

Donc :
- ne pas utiliser naïvement des comparaisons numériques ;
- reformuler les bornes chronologiques en contraintes textuelles adaptées.

Exemple :
- `antérieur à 1900` → préférer une contrainte du type `annee commence par 18`
