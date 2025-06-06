# Système de Persistance des Skins - Implémentation

## Vue d'ensemble

Ce document décrit l'implémentation du système de persistance des skins pour le jeu Sokoban, permettant aux utilisateurs d'appliquer des skins qui persistent à travers les sessions de jeu.

## Fonctionnalités Implémentées

### ✅ Persistance des Paramètres
- Les skins sélectionnés sont sauvegardés automatiquement
- Les paramètres persistent entre les sessions de jeu
- Fichier de configuration JSON créé automatiquement

### ✅ Partage du Gestionnaire de Skins
- Un seul gestionnaire de skins partagé entre tous les composants
- Cohérence garantie dans tout le jeu
- Mise à jour automatique de tous les composants

### ✅ Interface Utilisateur Améliorée
- Message de confirmation lors de l'application des paramètres
- Interface responsive et intuitive
- Support pour l'importation de skins personnalisés

## Architecture

### Composants Principaux

#### 1. ConfigManager (`src/core/config_manager.py`)
```python
class ConfigManager:
    """Gestionnaire de configuration persistante."""
    
    def get_skin_config(self) -> Dict[str, Any]
    def set_skin_config(self, current_skin: str, tile_size: int, save: bool = True) -> bool
    def save(self) -> bool
```

**Responsabilités :**
- Lecture/écriture du fichier de configuration JSON
- Gestion des valeurs par défaut
- Validation et migration des configurations

#### 2. EnhancedSkinManager (`src/ui/skins/enhanced_skin_manager.py`)
```python
class EnhancedSkinManager:
    """Gestionnaire de skins avec persistance."""
    
    def set_skin(self, skin_name: str)
    def set_tile_size(self, size: int)
    def get_current_skin_name(self) -> str
    def get_current_tile_size(self) -> int
```

**Modifications :**
- Intégration avec `ConfigManager`
- Sauvegarde automatique lors des changements
- Chargement des paramètres sauvegardés à l'initialisation

#### 3. SkinsMenu (`src/ui/skins_menu.py`)
```python
class SkinsMenu:
    """Menu de gestion des skins avec persistance."""
    
    def _apply_changes(self)  # Sauvegarde et affiche confirmation
    def _draw_applied_message(self)  # Message de confirmation
```

**Améliorations :**
- Message de confirmation visuel
- Sauvegarde automatique des paramètres
- Interface utilisateur améliorée

### Flux de Données

```
1. Utilisateur sélectionne un skin dans SkinsMenu
2. Clique sur "Appliquer"
3. SkinsMenu → EnhancedSkinManager.set_skin()
4. EnhancedSkinManager → ConfigManager.set_skin_config()
5. ConfigManager → Sauvegarde dans config.json
6. Confirmation affichée à l'utilisateur
```

### Flux de Chargement

```
1. Démarrage du jeu
2. EnhancedSokoban crée EnhancedSkinManager
3. EnhancedSkinManager → ConfigManager.get_skin_config()
4. ConfigManager → Lecture de config.json
5. Application des paramètres sauvegardés
6. Partage du gestionnaire avec tous les composants
```

## Fichiers Modifiés

### Nouveaux Fichiers
- `src/core/config_manager.py` - Gestionnaire de configuration
- `test_skin_persistence.py` - Tests du système
- `demo_skin_persistence.py` - Démonstration
- `docs/SKIN_PERSISTENCE_IMPLEMENTATION.md` - Cette documentation

### Fichiers Modifiés
- `src/ui/skins/enhanced_skin_manager.py` - Intégration de la persistance
- `src/ui/skins_menu.py` - Interface utilisateur améliorée
- `src/ui/menu_system.py` - Partage du gestionnaire de skins
- `src/gui_main.py` - Support pour gestionnaire externe
- `src/enhanced_main.py` - Orchestration du partage

## Configuration JSON

Le fichier `config.json` est créé automatiquement dans le répertoire racine du projet :

```json
{
  "skin": {
    "current_skin": "default",
    "tile_size": 64
  },
  "display": {
    "window_width": 900,
    "window_height": 700,
    "fullscreen": false
  },
  "game": {
    "keyboard_layout": "qwerty",
    "show_grid": false,
    "zoom_level": 1.0
  }
}
```

## Utilisation

### Pour l'Utilisateur

1. **Changer les Skins :**
   - Menu principal → Skins
   - Sélectionner un skin et une taille de tuiles
   - Cliquer sur "Appliquer"
   - Message de confirmation affiché

2. **Jouer avec les Skins Appliqués :**
   - Menu principal → Play Game
   - Sélectionner un niveau
   - Le jeu utilise automatiquement les skins appliqués

3. **Importer des Skins Personnalisés :**
   - Menu Skins → Import Skin
   - Sélectionner les fichiers PNG requis
   - Les nouveaux skins sont disponibles immédiatement

### Pour les Développeurs

```python
# Obtenir le gestionnaire de configuration global
from src.core.config_manager import get_config_manager
config = get_config_manager()

# Lire les paramètres de skin
skin_config = config.get_skin_config()
current_skin = skin_config['current_skin']
tile_size = skin_config['tile_size']

# Modifier les paramètres
config.set_skin_config('nouveau_skin', 32)

# Créer un gestionnaire de skins avec paramètres persistants
from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
skin_manager = EnhancedSkinManager()  # Charge automatiquement la config

# Partager le gestionnaire entre composants
game = GUIGame(skin_manager=skin_manager)
menu = MenuSystem(skin_manager=skin_manager)
```

## Tests

### Exécution des Tests
```bash
# Tests complets du système
python test_skin_persistence.py

# Démonstration interactive
python demo_skin_persistence.py

# Test direct du gestionnaire
python demo_skin_persistence.py --test
```

### Tests Automatisés
- ✅ Sauvegarde et chargement de la configuration
- ✅ Persistance des paramètres de skin
- ✅ Partage du gestionnaire entre composants
- ✅ Création automatique du fichier de configuration

## Avantages

### Pour l'Utilisateur
- **Persistance** : Les skins choisis persistent entre les sessions
- **Simplicité** : Un clic sur "Appliquer" sauvegarde tout
- **Feedback** : Message de confirmation visuel
- **Cohérence** : Même skin dans tous les composants du jeu

### Pour les Développeurs
- **Modularité** : Système de configuration réutilisable
- **Extensibilité** : Facile d'ajouter de nouveaux paramètres
- **Robustesse** : Gestion d'erreurs et valeurs par défaut
- **Testabilité** : Tests automatisés complets

## Dépannage

### Problèmes Courants

**Q: Les skins ne persistent pas**
- Vérifiez que le fichier `config.json` est créé dans le répertoire racine
- Vérifiez les permissions d'écriture du répertoire

**Q: Erreur de chargement de configuration**
- Le fichier sera recréé automatiquement avec les valeurs par défaut
- Supprimez `config.json` pour réinitialiser

**Q: Skins non disponibles après importation**
- Vérifiez que les fichiers sont dans le bon répertoire `skins/`
- Redémarrez le jeu pour actualiser la liste

### Logs de Débogage

Les messages suivants indiquent un fonctionnement normal :
```
✓ Skin appliqué: nom_du_skin, taille des tuiles: 64x64
Warning: Could not load config file: [première fois seulement]
```

## Conclusion

Le système de persistance des skins est maintenant pleinement fonctionnel et offre une expérience utilisateur fluide tout en maintenant une architecture de code propre et extensible.

Les utilisateurs peuvent maintenant :
1. ✅ Importer des skins personnalisés
2. ✅ Les appliquer via l'interface
3. ✅ Les voir dans tous les nouveaux niveaux lancés
4. ✅ Conserver leurs choix entre les sessions

Le système est prêt pour la production et peut être facilement étendu pour d'autres types de préférences utilisateur.