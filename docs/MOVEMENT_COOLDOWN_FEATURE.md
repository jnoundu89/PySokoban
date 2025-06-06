# Fonctionnalité de Cooldown des Mouvements

## Description

Cette fonctionnalité permet aux joueurs d'ajuster la vitesse de répétition des mouvements lorsqu'une touche de direction reste enfoncée. Cela améliore l'expérience de jeu en permettant un contrôle plus précis du joueur.

## Fonctionnalités Implémentées

### 1. Configuration Persistante
- Ajout du paramètre `movement_cooldown` dans la section `game` du fichier `config.json`
- Valeur par défaut : 200ms
- Plage de valeurs : 50ms à 500ms
- Configuration sauvegardée automatiquement et persistante entre les sessions

### 2. Interface Utilisateur - Slider dans Settings
- Nouveau slider dans le menu Settings pour ajuster le cooldown
- Interface intuitive avec curseur déplaçable
- Affichage en temps réel de la valeur sélectionnée
- Sauvegarde automatique lors du changement de valeur

### 3. Système de Cooldown Intelligent
- **Premier appui** : Réponse immédiate (sans cooldown)
- **Maintien de la touche** : Répétition contrôlée selon le cooldown configuré
- Différenciation entre les mouvements immédiats et continus
- Système optimisé pour une expérience de jeu fluide

### 4. Gestion des Touches
- Support des touches fléchées et des touches de direction selon le layout clavier
- Système de suivi des touches enfoncées (`held_keys`)
- Gestion des événements `KEYDOWN` et `KEYUP`
- Actualisation automatique des paramètres depuis la configuration

## Architecture Technique

### Fichiers Modifiés

1. **`config.json`**
   - Ajout du paramètre `movement_cooldown: 200`

2. **`src/core/config_manager.py`**
   - Mise à jour de la configuration par défaut
   - Extension de `set_game_config()` pour supporter le nouveau paramètre

3. **`src/ui/menu_system.py`**
   - Nouvelle classe `Slider` pour l'interface utilisateur
   - Intégration du slider dans le menu Settings
   - Gestion des événements du slider
   - Sauvegarde automatique des changements

4. **`sokoban_gui.py`**
   - Ajout du système de cooldown dans `SokobanGUIGame`
   - Gestion des touches maintenues enfoncées
   - Distinction entre mouvements immédiats et continus
   - Actualisation dynamique des paramètres

### Classes et Méthodes Principales

#### Classe `Slider`
- `__init__()` : Initialisation du slider avec paramètres visuels
- `draw()` : Rendu graphique du slider
- `handle_event()` : Gestion des interactions souris
- `get_handle_x()` : Calcul de la position du curseur

#### Modifications `SokobanGUIGame`
- `movement_cooldown` : Stockage du cooldown actuel
- `last_movement_time` : Timestamp du dernier mouvement
- `held_keys` : Set des touches actuellement enfoncées
- `_handle_held_keys()` : Gestion des mouvements continus
- `_handle_movement(immediate=False)` : Logique de mouvement avec cooldown

## Utilisation

### Pour les Joueurs
1. Lancer le jeu via `python enhanced_sokoban.py`
2. Aller dans le menu "Settings"
3. Utiliser le slider "Movement Cooldown (ms)" pour ajuster la vitesse
4. Les changements sont appliqués immédiatement et sauvegardés automatiquement

### Valeurs Recommandées
- **50ms** : Mouvement très rapide (pour joueurs expérimentés)
- **200ms** : Vitesse par défaut (équilibrée)
- **500ms** : Mouvement lent (pour joueurs débutants ou contrôle précis)

## Avantages

1. **Personnalisation** : Chaque joueur peut ajuster selon ses préférences
2. **Accessibilité** : Permet d'adapter le jeu à différents niveaux de compétence
3. **Contrôle Précis** : Évite les mouvements accidentels
4. **Persistance** : Configuration sauvegardée entre les sessions
5. **Interface Intuitive** : Slider facile à utiliser
6. **Performance** : Système optimisé sans impact sur les performances

## Tests

Pour tester la fonctionnalité :
1. Lancer le jeu
2. Aller dans Settings
3. Modifier le slider de cooldown
4. Jouer un niveau et maintenir une touche de direction enfoncée
5. Observer la différence de vitesse selon la configuration
6. Vérifier que les paramètres sont sauvegardés après redémarrage

La fonctionnalité est entièrement opérationnelle et intégrée dans l'architecture existante du jeu.