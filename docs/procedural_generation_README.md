# Sokoban Procedural Level Generation System

Ce document fournit une vue d'ensemble du système de génération procédurale de niveaux implémenté pour le jeu Sokoban.

## Vue d'ensemble

Le système de génération procédurale crée des niveaux Sokoban aléatoires qui sont garantis d'être résolvables. Il utilise un solveur complet pour vérifier la résolvabilité et fournit des métriques pour évaluer la qualité et la difficulté des niveaux générés.

Basé sur l'approche suggérée dans le thread Reddit, le système génère des niveaux complètement aléatoires, vérifie qu'ils sont résolvables, et permet de découvrir des patterns intéressants qui pourraient ne pas être évidents lors d'une conception manuelle.

## Composants

Le système se compose des composants suivants:

1. **Générateur Procédural** (`procedural_generator.py`): Génère des niveaux aléatoires basés sur des paramètres configurables.
2. **Solveur de Niveau** (`level_solver.py`): Implémente un algorithme de recherche en largeur (BFS) complet pour vérifier que les niveaux sont résolvables.
3. **Métriques de Niveau** (`level_metrics.py`): Calcule diverses métriques pour évaluer la qualité et la difficulté des niveaux.
4. **Intégration avec les Éditeurs de Niveau**: Les éditeurs de niveau terminal et graphique ont été mis à jour pour prendre en charge la génération de niveaux aléatoires.
5. **Script de Test** (`test_procedural_generation.py`): Démontre le fonctionnement du système et permet de générer facilement des niveaux de test.

## Comment Utiliser

### Test en Ligne de Commande

Vous pouvez tester le système de génération procédurale en utilisant le script de test fourni:

```bash
python test_procedural_generation.py
```

Ce script va:
1. Tester le solveur avec un niveau simple
2. Tester le calculateur de métriques avec un niveau simple
3. Générer 3 niveaux aléatoires avec les paramètres par défaut

Les résultats des tests montrent que:
- Le solveur peut résoudre un niveau simple en 6 mouvements, explorant 60 états en 0.0056 secondes
- Le calculateur de métriques fonctionne correctement, fournissant des informations détaillées sur les niveaux
- Le générateur peut créer des niveaux de différentes tailles et complexités, avec des temps de génération variables (de 0.32 à 69.46 secondes)

### Éditeur de Niveau Terminal

Pour générer des niveaux dans l'éditeur de niveau basé sur le terminal:

1. Exécutez l'éditeur de niveau: `python level_editor.py`
2. Sélectionnez l'option 3 "Generate random level"
3. Entrez les paramètres de génération lorsque vous y êtes invité
4. Le niveau généré sera chargé dans l'éditeur pour une édition ou une sauvegarde ultérieure

### Éditeur de Niveau Graphique

Pour générer des niveaux dans l'éditeur de niveau graphique:

1. Exécutez l'éditeur de niveau graphique: `python graphical_level_editor.py`
2. Cliquez sur le bouton "Generate"
3. Entrez les paramètres de génération dans la boîte de dialogue
4. Cliquez sur "Generate" pour créer un niveau aléatoire
5. Le niveau généré sera chargé dans l'éditeur
6. Cliquez sur "Metrics" ou appuyez sur 'M' pour voir les métriques détaillées du niveau

Les métriques sont affichées dans un panneau semi-transparent sur le côté droit de l'écran, fournissant des informations détaillées sur la difficulté, l'efficacité spatiale, et les patterns du niveau.

## Paramètres de Génération

Les paramètres suivants peuvent être configurés pour la génération de niveaux:

- **min_width**: Largeur minimale du niveau (défaut: 7)
- **max_width**: Largeur maximale du niveau (défaut: 15)
- **min_height**: Hauteur minimale du niveau (défaut: 7)
- **max_height**: Hauteur maximale du niveau (défaut: 15)
- **min_boxes**: Nombre minimum de boîtes (défaut: 1)
- **max_boxes**: Nombre maximum de boîtes (défaut: 5)
- **wall_density**: Densité des murs internes (0-1, défaut: 0.2)
- **timeout**: Temps maximum en secondes pour la génération (défaut: 30)

Ces paramètres peuvent être ajustés pour contrôler la taille, la complexité et la difficulté des niveaux générés. Des valeurs plus élevées pour le nombre de boîtes et la densité des murs augmentent généralement la difficulté.

## Métriques de Niveau

Le système calcule les métriques suivantes pour les niveaux générés:

- **Size**: Largeur, hauteur et zone jouable
- **Box Count**: Nombre de boîtes dans le niveau
- **Solution Length**: Nombre de mouvements dans la solution
- **Difficulty Score**: Score de difficulté global (0-100)
- **Space Efficiency**: Ratio de la zone jouable par rapport à la zone totale
- **Box Density**: Ratio des boîtes par rapport à la zone jouable
- **Patterns**: Comptage de divers motifs dans le niveau:
  - **Corners**: Nombre de coins (cellules avec deux murs adjacents)
  - **Corridors**: Nombre de couloirs (cellules avec deux murs opposés)
  - **Rooms**: Estimation du nombre de pièces
  - **Dead Ends**: Nombre d'impasses (cellules avec trois murs adjacents)

Ces métriques fournissent des informations précieuses sur la qualité et la difficulté des niveaux générés, et peuvent être utilisées pour filtrer ou classer les niveaux selon différents critères.

## Améliorations Futures

L'implémentation actuelle se concentre sur la génération aléatoire de base avec validation. Les améliorations futures pourraient inclure:

1. **Génération Basée sur des Patterns**: Utilisation d'une bibliothèque de patterns intéressants connus pour créer des niveaux
2. **Apprentissage Automatique**: Entraînement d'un modèle pour générer des niveaux basés sur les retours des joueurs
3. **Transfert de Style**: Génération de niveaux qui imitent le style de niveaux bien conçus existants
4. **Progression de Difficulté**: Création de séquences de niveaux avec une difficulté croissante
5. **Analyse de Jouabilité**: Évaluation plus sophistiquée de la qualité des niveaux en fonction de critères de jouabilité
6. **Génération Contrainte**: Création de niveaux avec des contraintes spécifiques (nombre minimum de mouvements, patterns spécifiques, etc.)

## Détails Techniques

### Algorithme de Génération

L'algorithme de génération actuel:

1. Crée une grille de la taille souhaitée avec des murs autour du périmètre
2. Place aléatoirement des murs internes en fonction de la densité des murs
3. S'assure que le niveau est connecté (toutes les cases de sol sont accessibles)
4. Place le joueur à une position aléatoire
5. Place les boîtes et les cibles à des positions aléatoires
6. Valide que le niveau répond aux exigences de base
7. Vérifie que le niveau est résolvable en utilisant le solveur

### Algorithme du Solveur

Le solveur utilise une approche de recherche en largeur (BFS):

1. Commencer avec l'état initial
2. Explorer tous les mouvements possibles (haut, bas, gauche, droite)
3. Pour chaque mouvement valide, créer un nouvel état
4. Vérifier si le nouvel état est une solution
5. Sinon, l'ajouter à la file d'attente des états à explorer
6. Continuer jusqu'à ce qu'une solution soit trouvée ou que tous les états soient explorés

Le solveur utilise une fonction de hachage pour suivre les états visités et implémente une détection de blocage de base pour élaguer l'arbre de recherche. Cette approche garantit que si une solution existe, elle sera trouvée, bien que cela puisse prendre du temps pour des niveaux complexes.

### Performances

Les tests montrent que:
- Le solveur peut résoudre des niveaux simples en quelques millisecondes
- La génération de niveaux peut prendre de quelques secondes à plus d'une minute, selon la complexité du niveau et le nombre de tentatives nécessaires
- En moyenne, il faut environ 4-5 tentatives pour générer un niveau valide et résolvable

Ces performances sont acceptables pour une utilisation dans un éditeur de niveau, où la génération n'est pas effectuée en temps réel pendant le jeu.

## Intégration dans le Jeu

Le système de génération procédurale est entièrement intégré dans le jeu Sokoban existant:

1. Le `LevelManager` peut générer et sauvegarder des niveaux aléatoires
2. Les éditeurs de niveau terminal et graphique offrent des interfaces utilisateur pour la génération
3. Les niveaux générés peuvent être sauvegardés et chargés comme des niveaux normaux
4. Les métriques de niveau peuvent être visualisées dans l'éditeur graphique

Cette intégration permet une expérience fluide pour la création, le test et l'ajustement de niveaux générés procéduralement.