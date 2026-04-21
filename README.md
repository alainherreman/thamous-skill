# thamous-skill

Skill Codex pour interroger l’API Thamous v2 logique.

Contenu :
- `SKILL.md`
- `references/`
- `scripts/thamous_api_v2.py`
- `agents/openai.yaml`
- `references/exemples-tests-v2.md`

## Utilisation réelle

Prérequis :
- un **compte Thamous** (login + mot de passe) ;
- une **clé API fournisseur LLM** enregistrée dans Thamous.

L’utilisateur n’a pas à manipuler directement un token.

Procédure simple :

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 save-credentials --login VOTRE_LOGIN
~/.codex/skills/thamous-api-v2/bin/thamous-v2 token-status
```

Le client :
- récupère automatiquement un token via `login_token` ;
- le stocke localement ;
- le renouvelle automatiquement s’il expire.

En secours, on peut toujours fournir `--login` et `--password` à la commande, ou utiliser un token déjà présent.

## Principe d'usage

- la skill doit fonctionner **sans validation intermédiaire** pour les opérations standard ;
- si l'utilisateur demande une action normale prise en charge, il faut l'exécuter directement ;
- ne demander quelque chose que s'il manque une information indispensable ou s'il y a un vrai choix utilisateur à trancher.
- les ouvertures standard (`open-fiche`, `open-list`, `prepare-ref` quand il renvoie un formulaire) doivent lancer directement `xdg-open`, sans validation intermédiaire.

## Actions explicites actuellement prises en charge

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

L’historique local sert aussi à résoudre les références au **résultat précédent**.

Les résultats de `ask-logic` peuvent être stockés localement :
- avec un nom automatique ;
- ou avec `--result-name`.

Commandes utiles :
- `~/.codex/skills/thamous-api-v2/bin/thamous-v2 --format table history`
- `~/.codex/skills/thamous-api-v2/bin/thamous-v2 project-keywords --project HilbertGG`
- `~/.codex/skills/thamous-api-v2/bin/thamous-v2 refs-by-keyword --project HilbertGG --table tbiblio --mot-clef "Axiome Archimède"`
- `~/.codex/skills/thamous-api-v2/bin/thamous-v2 add-to-list --previous --q "..." --project ... --provider ... --model ...`
- `~/.codex/skills/thamous-api-v2/bin/thamous-v2 follow-links --previous --link-type Cite --from source --to but --output-table tbiblio --project ...`

## Exemples et tests représentatifs

Voir :
- `references/exemples-tests-v2.md`

Ce document distingue :
- les **exemples d’usage utilisateur** ;
- les **tests automatiques réellement exécutés** ;
- les **tests fonctionnels à faire avec un vrai compte Thamous**.
