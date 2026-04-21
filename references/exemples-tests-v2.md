# Exemples représentatifs et tests — Thamous API v2

Ce document sert à deux choses :
- montrer aux utilisateurs des usages typiques ;
- fournir une petite batterie de tests représentatifs pour vérifier le comportement attendu.

## 1. Exemples d’usage utilisateur

Les commandes ci-dessous utilisent le wrapper canonique :

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 ...
```

### A. Première configuration

Enregistrer les identifiants Thamous :

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 save-credentials --login VOTRE_LOGIN
```

Vérifier que l’authentification fonctionne :

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 token-status
```

### B. Vérification minimale de l’API

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 health
~/.codex/skills/thamous-api-v2/bin/thamous-v2 logic-context --projet perso
```

### C. Ouvrir une fiche

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 fiche-url --id 1442 --table tbiblio
~/.codex/skills/thamous-api-v2/bin/thamous-v2 open-fiche --id 1442 --table tbiblio
```

### D. Ouvrir une liste issue d’une demande logique

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 open-list   --q "les ouvrages de Hilbert sur la géométrie"   --project HilbertGG   --provider xAI   --model "Grok 4"
```

### E. Obtenir une structure logique sans ouvrir de page

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 text-to-structure   --q "les articles en espagnol sur Hilbert"   --project HilbertGG   --provider xAI   --model "Grok 4"
```

### F. Recherche logique avec stockage local du résultat

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 ask-logic   --q "les traductions anglaises de Hilbert"   --project HilbertGG   --provider xAI   --model "Grok 4"   --result-name traductions_hilbert
```

Afficher ensuite l’historique local :

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 --format table history
```

### G. Ajouter un nouveau résultat à la liste précédente

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 add-to-list   --previous   --q "les éditions françaises"   --project HilbertGG   --provider xAI   --model "Grok 4"
```

### H. Suivre un type de lien depuis la liste précédente

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 follow-links   --previous   --link-type Cite   --from source   --to but   --output-table tbiblio   --project HilbertGG
```

## 2. Ce que l’on veut assurer comme usage

On veut garantir au minimum :

1. **authentification simple**
   - l’utilisateur fournit un login et un mot de passe ;
   - il n’a pas à manipuler lui-même de token.

2. **renouvellement automatique**
   - si le token local a expiré, le client le renouvelle automatiquement via `login_token`.

3. **commandes canoniques stables**
   - le wrapper `thamous-v2` suffit pour l’usage courant ;
   - pas besoin de `curl` manuel.

4. **usages principaux couverts**
   - vérifier l’API ;
   - ouvrir une fiche ;
   - ouvrir une liste ;
   - produire une structure logique ;
   - mémoriser un résultat ;
   - réutiliser le résultat précédent.

## 3. Tests automatiques réellement exécutés

Tests exécutés pendant cette mise au point :

### A. Santé de l’API (sans authentification)

Commande :

```bash
python3 scripts/thamous_api_v2.py --format json health
```

Résultat attendu :
- JSON avec `ok: true`.

### B. Aide CLI

Commandes :

```bash
python3 scripts/thamous_api_v2.py --help
python3 scripts/thamous_api_v2.py save-credentials --help
python3 scripts/thamous_api_v2.py login --help
```

Résultat attendu :
- présence des options `--credentials-file`, `--login`, `--password` ;
- présence des sous-commandes `save-credentials` et `login`.

### C. Écriture locale des identifiants

Commande testée :

```bash
python3 scripts/thamous_api_v2.py save-credentials   --login test-user   --password test-pass   --credentials-file /tmp/thamous_creds_test.json
```

Résultat attendu :
- fichier JSON créé avec `login` et `password`.

### D. Vérification syntaxique Python

Commande :

```bash
python3 -m py_compile scripts/thamous_api_v2.py
```

Résultat attendu :
- aucune erreur.

## 4. Tests fonctionnels à faire avec un vrai compte Thamous

Ces tests restent nécessaires avant diffusion large aux utilisateurs :

### A. Authentification réelle

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 save-credentials --login VOTRE_LOGIN
~/.codex/skills/thamous-api-v2/bin/thamous-v2 token-status
```

Attendu :
- `status: valid`
- `signature` renseignée
- `projects` renseignés

### B. Renouvellement automatique du token

Procédure :
- supprimer ou corrompre le token local ;
- relancer une commande authentifiée, par exemple :

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 logic-context --projet perso
```

Attendu :
- la commande fonctionne quand même ;
- le token est recréé automatiquement.

### C. Ouverture de fiche

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 open-fiche --id 1442 --table tbiblio
```

Attendu :
- ouverture de la bonne page Thamous.

### D. Recherche logique avec LLM

```bash
~/.codex/skills/thamous-api-v2/bin/thamous-v2 ask-logic   --q "les articles en espagnol sur Hilbert"   --project HilbertGG   --provider xAI   --model "Grok 4"
```

Attendu :
- réponse structurée cohérente ;
- pas d’erreur d’auth API ;
- pas d’erreur de clé fournisseur.

### E. Réutilisation de l’historique local

Procédure :
1. lancer `ask-logic --result-name ...` ;
2. lancer `add-to-list --previous ...` ;
3. lancer `follow-links --previous ...`.

Attendu :
- la résolution de `--previous` prend bien le dernier résultat compatible.
