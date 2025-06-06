# Sokoban

Un jeu de puzzle Sokoban complet développé en Python avec une approche modulaire pour la création de niveaux et de nombreuses fonctionnalités améliorées.

## Description

Sokoban ("gardien d'entrepôt" en japonais) est un jeu de puzzle classique où le joueur doit pousser des boîtes jusqu'à des emplacements cibles dans un entrepôt. Ce projet implémente le jeu avec:

- Un système de menu central (hub) pour naviguer entre les différentes fonctionnalités
- Un mode terminal pour jouer dans la console
- Un mode GUI utilisant Pygame pour une expérience graphique
- Un éditeur de niveaux graphique avec fonctionnalité drag-and-drop
- Un système de skins/sprites pour personnaliser l'apparence du jeu
- Un système de validation de niveaux pour vérifier qu'ils sont jouables
- Une structure modulaire permettant d'étendre facilement le jeu
- Support pour différentes dispositions de clavier (QWERTY et AZERTY)

## Structure du projet

Le projet est organisé de manière modulaire:

- `src/` - Package principal contenant tout le code source
  - `core/` - Contient les classes de base et les constantes
  - `renderers/` - Contient les différents renderers (terminal, GUI)
  - `level_management/` - Gestion des niveaux et collections
  - `editors/` - Éditeurs de niveaux
  - `ui/` - Interface utilisateur et système de menu
  - `generation/` - Génération procédurale de niveaux
  - `main.py` - Point d'entrée unique pour toutes les versions du jeu
- `levels/` - Répertoire contenant les fichiers de niveaux
- `skins/` - Répertoire contenant les différents thèmes visuels

## Nouvelles fonctionnalités

### Système de Menu (Hub)

Le système de menu central permet aux joueurs de naviguer facilement entre les différentes fonctionnalités du jeu:
- Jouer au jeu
- Éditer des niveaux
- Changer les paramètres
- Sélectionner des skins
- Voir les crédits

### Éditeur de Niveaux Graphique

L'éditeur de niveaux graphique offre une interface intuitive pour créer et modifier des niveaux:
- Interface drag-and-drop pour placer les éléments
- Validation des niveaux pour s'assurer qu'ils sont jouables
- Test en direct des niveaux
- Sauvegarde et chargement des niveaux

### Système de Skins/Sprites

Le système de skins permet de personnaliser l'apparence du jeu:
- Chargement de différents thèmes visuels
- Création de nouveaux thèmes
- Application des thèmes en temps réel

## Comment jouer

Le jeu dispose désormais d'un point d'entrée unique via le module `src.main`. Vous pouvez lancer différentes versions du jeu en utilisant l'option `--mode`.

### Mode Amélioré (Recommandé)

Pour lancer le jeu avec toutes les fonctionnalités améliorées (mode par défaut):

```bash
python -m src.main
```

ou explicitement:

```bash
python -m src.main --mode enhanced
```

### Mode Terminal

Pour jouer en mode terminal:

```bash
python -m src.main --mode terminal
```

### Mode GUI (Interface graphique)

Pour jouer avec l'interface graphique:

```bash
python -m src.main --mode gui
```

### Éditeur de Niveaux

Pour lancer l'éditeur de niveaux graphique:

```bash
python -m src.main --mode editor
```

### Options supplémentaires

Vous pouvez spécifier un répertoire de niveaux différent:

```bash
python -m src.main --levels chemin/vers/niveaux
```

Pour choisir une disposition de clavier spécifique (qwerty ou azerty):

```bash
python -m src.main --keyboard azerty
```

Toutes les options peuvent être combinées:

```bash
python -m src.main --mode gui --levels chemin/vers/niveaux --keyboard azerty
```

Pour voir toutes les options disponibles:

```bash
python -m src.main --help
```

## Contrôles

### Dans le jeu

#### Disposition QWERTY (par défaut):
- Flèches directionnelles ou WASD: Déplacer le joueur
- R: Réinitialiser le niveau
- U: Annuler le dernier mouvement
- N: Niveau suivant (si le niveau actuel est terminé)
- P: Niveau précédent
- H: Afficher l'aide
- Q: Quitter le jeu

#### Disposition AZERTY:
- Flèches directionnelles ou ZQSD: Déplacer le joueur
- R: Réinitialiser le niveau
- U: Annuler le dernier mouvement
- N: Niveau suivant (si le niveau actuel est terminé)
- P: Niveau précédent
- H: Afficher l'aide
- A: Quitter le jeu

### Dans l'éditeur de niveaux graphique

- Clic gauche: Placer l'élément sélectionné
- Clic droit: Effacer l'élément (mettre un sol)
- Clic sur la palette: Sélectionner un élément
- Boutons:
  - New: Créer un nouveau niveau
  - Open: Ouvrir un niveau existant
  - Save: Sauvegarder le niveau
  - Test: Tester le niveau
  - Validate: Vérifier si le niveau est valide
  - Help: Afficher l'aide
  - Exit: Quitter l'éditeur

## Création de niveaux

Les niveaux sont stockés sous forme de fichiers texte dans le répertoire `levels/`. Chaque caractère représente un élément du jeu:

- `#` - Mur
- ` ` - Sol vide
- `@` - Joueur
- `$` - Boîte
- `.` - Cible
- `+` - Joueur sur une cible
- `*` - Boîte sur une cible

Vous pouvez créer des niveaux manuellement en éditant ces fichiers ou utiliser l'éditeur de niveaux graphique inclus.

## Dépendances

Ce projet nécessite:

- Python 3.6 ou supérieur
- Bibliothèque `keyboard` pour le mode terminal
- Bibliothèque `pygame` pour le mode GUI et les fonctionnalités améliorées

Installation des dépendances:

```bash
pip install -r requirements.txt
```

## Fonctionnalités clés

- Architecture modulaire séparant la logique du jeu, le rendu et les entrées utilisateur
- Système de chargement de niveaux à partir de fichiers texte
- Système de menu central (hub) pour naviguer entre les fonctionnalités
- Éditeur de niveaux graphique avec drag-and-drop
- Système de skins/sprites pour personnaliser l'apparence du jeu
- Validation des niveaux pour s'assurer qu'ils sont jouables
- Test en direct des niveaux
- Deux modes de jeu: terminal et GUI
- Support pour les dispositions de clavier QWERTY et AZERTY
- Système d'annulation des mouvements
- Statistiques de jeu (mouvements, poussées)
- Détection automatique de la complétion des niveaux
- Navigation entre les niveaux
