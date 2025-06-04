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

- `constants.py` - Définit toutes les constantes utilisées dans le jeu
- `level.py` - Classe pour gérer un niveau individuel et sa logique
- `level_manager.py` - Gère plusieurs niveaux et la navigation entre eux
- `terminal_renderer.py` - Affiche le jeu dans un terminal
- `gui_renderer.py` - Affiche le jeu avec une interface graphique
- `sokoban.py` - Point d'entrée pour jouer en mode terminal
- `sokoban_gui.py` - Point d'entrée pour jouer en mode graphique
- `level_editor.py` - Éditeur de niveaux en mode terminal
- `graphical_level_editor.py` - Éditeur de niveaux graphique avec drag-and-drop
- `menu_system.py` - Système de menu central (hub)
- `skin_manager.py` - Gestionnaire de skins/sprites
- `enhanced_sokoban.py` - Point d'entrée principal avec toutes les fonctionnalités améliorées
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

### Mode Amélioré (Recommandé)

Pour lancer le jeu avec toutes les fonctionnalités améliorées:

```bash
python enhanced_sokoban.py
```

### Mode Terminal

Pour jouer en mode terminal:

```bash
python sokoban.py
```

Vous pouvez spécifier un répertoire de niveaux différent:

```bash
python sokoban.py chemin/vers/niveaux
```

Ou avec des arguments nommés:

```bash
python sokoban.py --levels chemin/vers/niveaux
```

Pour choisir une disposition de clavier spécifique (qwerty ou azerty):

```bash
python sokoban.py --keyboard azerty
```

### Mode GUI (Interface graphique)

Pour jouer avec l'interface graphique:

```bash
python sokoban_gui.py
```

Les mêmes options de ligne de commande sont disponibles:

```bash
python sokoban_gui.py --levels chemin/vers/niveaux --keyboard azerty
```

### Éditeur de Niveaux Graphique

Pour lancer l'éditeur de niveaux graphique:

```bash
python graphical_level_editor.py
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