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
- diagnostiquer une structure ou une réponse.

Si une demande ne correspond pas à l’une de ces actions, la skill doit le dire explicitement au lieu d’improviser.
