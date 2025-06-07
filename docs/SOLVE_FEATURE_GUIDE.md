# Guide de la Fonctionnalité "AI Solve" - PySokoban

## Vue d'ensemble

La nouvelle fonctionnalité "AI Solve" permet à une intelligence artificielle de prendre automatiquement le contrôle du jeu et de résoudre les niveaux de Sokoban en temps réel. L'IA utilise un algorithme de recherche en largeur (BFS) optimisé pour trouver la solution optimale, puis exécute chaque mouvement automatiquement sur le niveau en cours.

## Fonctionnalités

### 1. Contrôle Automatique par l'IA
- **Prise de contrôle**: L'IA prend le contrôle du joueur et résout le niveau automatiquement
- **Exécution en temps réel**: Chaque mouvement est exécuté directement sur le niveau en cours
- **Solution optimale**: Utilise le chemin le plus court trouvé par l'algorithme BFS
- **Feedback visuel**: Affichage en temps réel des mouvements de l'IA

### 2. Algorithme de Résolution Avancé
- **BFS optimisé**: Recherche en largeur avec détection de deadlocks
- **Performance**: Limité à 100,000 états et 10 secondes par tentative
- **Robustesse**: Gestion des erreurs et états partiels du niveau

### 3. Interface Utilisateur Interactive
- **Contrôle utilisateur**: Possibilité d'annuler l'IA avec la touche ESC
- **Feedback en temps réel**: Messages de progression et état de l'IA
- **Vitesse configurable**: Délai ajustable entre les mouvements (300-600ms)

## Utilisation

### Dans l'Éditeur de Niveau

1. **Accès**: Cliquez sur le bouton "Solve Level" dans la section des outils
2. **Prérequis**: Le niveau doit être valide (joueur, boîtes et cibles en nombre égal)
3. **Comportement**: L'IA prend le contrôle et résout automatiquement le niveau
4. **Résultat**: Le niveau est résolu en temps réel avec feedback console

```
============================================================
AI TAKING CONTROL OF LEVEL
============================================================
AI: Analyzing level...
AI: Solution found! 16 moves
SUCCESS: Solution found!
Solution length: 16 moves
AI will now take control and solve the level...
============================================================
🤖 AI executing solution: 16 moves
🤖 AI Move 1/16: DOWN -> ✅
🤖 AI Move 2/16: LEFT -> ✅
...
🤖 AI Move 16/16: UP -> ✅
🎉 Level solved by AI! Well done!
AI successfully solved the level!
============================================================
```

### Pendant le Jeu

1. **Raccourci clavier**: Appuyez sur la touche **S** pendant le jeu
2. **Prise de contrôle**: L'IA prend immédiatement le contrôle du joueur
3. **Exécution automatique**: L'IA déplace le joueur automatiquement pour résoudre le niveau
4. **Contrôles**:
   - **ESC**: Annuler et reprendre le contrôle manuel
   - **Observation**: Regarder l'IA résoudre le niveau

### Messages d'État de l'IA

- **"AI taking control..."**: L'IA commence à prendre le contrôle
- **"🤖 AI executing solution: X moves"**: L'IA commence l'exécution
- **"🤖 AI Move X/Y: DIRECTION -> ✅"**: Chaque mouvement réussi de l'IA
- **"🎉 Level solved by AI!"**: L'IA a résolu le niveau avec succès
- **"AI control cancelled by user"**: L'utilisateur a annulé l'IA avec ESC
- **"AI control failed - invalid move"**: Erreur dans l'exécution de l'IA

## Limitations

### Complexité des Niveaux
- **États maximum**: 100,000 états explorés par tentative
- **Temps maximum**: 10 secondes par tentative de résolution
- **Niveaux très complexes**: Peuvent ne pas être résolus dans les limites de temps

### Validation Requise
- Le niveau doit avoir exactement un joueur
- Le nombre de boîtes doit égaler le nombre de cibles
- Le niveau doit être connecté (tous les espaces accessibles)

## Architecture Technique

### Classes Principales

#### `AutoSolver` (`src/core/auto_solver.py`)
- **Responsabilité**: Interface principale pour la résolution automatique
- **Méthodes clés**:
  - `solve_level()`: Résout le niveau
  - `animate_solution()`: Anime la solution
  - `get_solution_info()`: Retourne les informations de la solution

#### `SokobanSolver` (`src/generation/level_solver.py`)
- **Responsabilité**: Algorithme de résolution BFS
- **Optimisations**:
  - Détection de deadlocks (boîtes coincées dans les coins)
  - Limites de temps et d'états
  - Hachage efficace des états

### Intégration

#### Éditeur de Niveau
- **Fichier**: `src/editors/enhanced_level_editor.py`
- **Méthode**: `_solve_level()`
- **Interface**: Bouton "Solve Level" dans la section des outils

#### Jeu Principal
- **Fichier**: `src/gui_main.py`
- **Méthode**: `_solve_current_level()`
- **Interface**: Touche "S" pendant le jeu

#### Interface Utilisateur
- **Fichiers**: `src/renderers/gui_renderer.py`
- **Mise à jour**: Écrans d'aide et de bienvenue incluent la touche "S"

## Exemples d'Utilisation

### Niveau Simple
```
#####
#   #
# $ #
# . #
# @ #
#####
```
**Solution**: `up -> left -> up -> up -> right -> down` (6 mouvements)

### Niveau Complexe
```
#######
#     #
# $$  #
# ..  #
#  @  #
#     #
#######
```
**Solution**: `up -> right -> up -> up -> left -> down -> up -> left -> down` (9 mouvements)

## Dépannage

### "No solution found"
- **Cause possible**: Niveau impossible à résoudre
- **Solution**: Vérifier que toutes les boîtes peuvent atteindre une cible

### "Level is not valid"
- **Cause possible**: Niveau mal formé
- **Solution**: Utiliser le bouton "Validate" pour identifier les problèmes

### Animation lente
- **Cause possible**: Niveau très complexe
- **Solution**: La vitesse d'animation peut être ajustée dans le code (paramètre `move_delay`)

## Tests

Un script de test est disponible pour vérifier le bon fonctionnement :

```bash
python test_solve_feature.py
```

Ce script teste la résolution sur des niveaux simples et complexes, et vérifie que les solutions trouvées sont correctes.

## Améliorations Futures

### Fonctionnalités Potentielles
- **Interface graphique**: Dialog box pour afficher la solution dans l'éditeur
- **Sauvegarde de solutions**: Possibilité de sauvegarder les solutions trouvées
- **Optimisation de solutions**: Recherche de solutions plus courtes
- **Hints**: Affichage du prochain mouvement seulement
- **Vitesse d'animation variable**: Contrôle utilisateur de la vitesse

### Optimisations Techniques
- **Algorithme A***: Pour des solutions plus optimales
- **Détection de deadlocks avancée**: Patterns plus complexes
- **Parallélisation**: Utilisation de plusieurs threads pour les gros niveaux
- **Cache de solutions**: Mémorisation des solutions déjà trouvées

---

*Cette fonctionnalité améliore significativement l'expérience utilisateur en permettant de résoudre automatiquement les niveaux difficiles et de comprendre les stratégies de résolution.*