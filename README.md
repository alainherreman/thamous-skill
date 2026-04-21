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
- la solution la plus simple est d’utiliser le **même token partagé stable** que vos autres clients Thamous, puis de l’enregistrer localement avec :
  - `python3 scripts/thamous_api_v2.py save-token --token VOTRE_TOKEN`
- il est alors stocké par défaut dans `~/.config/thamous/token`, relu automatiquement par les commandes normales ;
- son état se vérifie avec :
  - `python3 scripts/thamous_api_v2.py token-status`
- si `token-status` indique `expired_or_invalid`, il faut d’abord vérifier que la skill utilise bien le **bon token partagé** ;
- l’API v2 accepte à nouveau correctement le header `Authorization: Bearer ...` côté serveur ;
- la clé fournisseur s'enregistre dans le menu `LLM`, où l'on choisit aussi le modèle.

Principe d'usage :
- la skill doit fonctionner **sans validation intermédiaire** pour les opérations standard ;
- si l'utilisateur demande une action normale prise en charge, il faut l'exécuter directement ;
- ne demander quelque chose que s'il manque une information indispensable ou s'il y a un vrai choix utilisateur à trancher.
- les ouvertures standard (`open-fiche`, `open-list`, `prepare-ref` quand il renvoie un formulaire) doivent lancer directement `xdg-open`, sans validation intermédiaire.

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

L’historique local sert aussi à résoudre les références au **résultat précédent**.

Les résultats de `ask-logic` peuvent être stockés localement :
- avec un nom automatique ;
- ou avec `--result-name`.

Commandes utiles :
- `python3 scripts/thamous_api_v2.py --format table history`
- `python3 scripts/thamous_api_v2.py project-keywords --project HilbertGG`
- `python3 scripts/thamous_api_v2.py refs-by-keyword --project HilbertGG --table tbiblio --mot-clef "Axiome Archimède"`
- `python3 scripts/thamous_api_v2.py add-to-list --previous --q "..." --project ... --provider ... --model ...`
- `python3 scripts/thamous_api_v2.py follow-links --previous --link-type Cite --from source --to but --output-table tbiblio --project ...`

Règle générale :
- une expression comme `la liste précédente`, `les références précédentes`, `le résultat précédent` ou une formulation équivalente doit être résolue **localement** dans l’historique ;
- la skill doit choisir le **dernier résultat compatible**, pas simplement le dernier résultat quelconque ;
- un résultat nommé explicitement a priorité ;
- si aucun antécédent compatible n’existe, la skill doit le dire explicitement.

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
- si le moteur produit seulement une recherche directe dans `tbiblio` sans lien `Traduction`, il faut considérer cela comme suspect et utiliser la rétroaction pour corriger

## Dates

Le champ `annee` doit être traité comme un **texte**.

Donc :
- ne pas utiliser naïvement des comparaisons numériques ;
- reformuler les bornes chronologiques en contraintes textuelles adaptées.

Exemple :
- `antérieur à 1900` → préférer une contrainte du type `annee commence par 18`

## Revues, auteurs, et champs textuels

- dans `tbiblio`, le champ `editeur` d'un **article** contient en pratique le titre de la revue où l'article est publié
- de même, le champ `nom` d'une publication contient en pratique le nom de ses auteurs, en correspondance avec `tpersonnes`
- ce problème concerne surtout l'ouverture d'une liste Thamous ou toute demande dont le résultat doit être une vraie table Thamous (`trevues`, `tpersonnes`)
- dans ce cas, il faut résoudre les chaînes de `tbiblio.editeur` vers `trevues`, ou celles de `tbiblio.nom` vers `tpersonnes`
- en revanche, pour une réponse JSON, on peut retourner directement les chaînes de `tbiblio.editeur` ou `tbiblio.nom` si c'est bien cela que demande l'utilisateur

## Authentification utilisateur

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
