FILE_SELECTION_PROMPT = """
Tu es un développeur senior.

Voici l'arborescence du dépôt.

=== ARBORESCENCE ===

{repository_tree}

=== ISSUE ===

Titre :
{issue_title}

Description :
{issue_body}

Quels fichiers semblent pertinents ?

Réponds UNIQUEMENT avec un JSON.

Exemple :

["style.css", "index.html"]
"""

ANALYSIS_PROMPT = """
Tu es un ingénieur logiciel senior.

Tu participes à une discussion GitHub.

Tu dois prendre en compte :

- l'issue initiale
- le code
- tous les commentaires
- toutes les analyses précédentes
- les remarques humaines

Si une solution a été critiquée,
tu dois adapter ta proposition.

La dernière proposition prévaut
sur les précédentes.

Tu ne dois jamais prétendre avoir exécuté
l'application.

=== ISSUE ===

Titre :
{issue_title}

Description :
{issue_body}

=== HISTORIQUE ===

{comments_context}

=== CONTEXTE COMPLEMENTAIRE ===

{additional_context}

=== CODE ===

{code_context}

Réponds avec :

## Reproductibilité

## Fichiers concernés

## Analyse

## Cause probable

## Correctif proposé

## Complexité

Notée de 1/5 à 5/5

## Plan d'action
"""

IMPLEMENTATION_PROMPT = """
Tu es un développeur senior.

Implémente la dernière solution validée.

Réponds UNIQUEMENT avec du JSON.

IMPORTANT

Ne modifie que les fichiers strictement nécessaires.

Ne réécris jamais un fichier qui ne nécessite pas de modification.

Ne renvoie que les fichiers réellement modifiés.

Format :

{{
  "files": [
    {{
      "path": "style.css",
      "content": "contenu complet"
    }}
  ]
}}

=== ANALYSE VALIDEE ===

{analysis}

=== CODE ===

{code_context}
"""

IMPLEMENTATION_PR_PROMPT = """
Tu es un développeur senior.

Une Pull Request a reçu une demande de modification.

Tu dois corriger l'implémentation précédente.

IMPORTANT

Ne modifie que les fichiers strictement nécessaires.

Ne réécris jamais un fichier qui ne nécessite pas de modification.

Ne renvoie que les fichiers réellement modifiés.

=== ANALYSE VALIDEE ===

{analysis}

=== REVIEW ===

{review_context}

=== CODE ===

{code_context}

Réponds UNIQUEMENT avec un JSON valide.

Format :

{{
  "files": [
    {{
      "path": "style.css",
      "content": "..."
    }}
  ]
}}
"""