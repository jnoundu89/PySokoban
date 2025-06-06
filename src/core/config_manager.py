"""
Configuration Manager for the Sokoban game.

This module provides persistent configuration storage and retrieval for:
- Skin settings
- Tile size settings
- Other game preferences
"""

import os
import json
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Manager for persistent game configuration.
    """
    
    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str): Path to the configuration file.
        """
        # Set config file path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.config_file = os.path.join(project_root, config_file)
        
        # Default configuration
        self.default_config = {
            'skin': {
                'current_skin': 'default',
                'tile_size': 64
            },
            'display': {
                'window_width': 900,
                'window_height': 700,
                'fullscreen': False
            },
            'game': {
                'keyboard_layout': 'qwerty',
                'show_grid': False,
                'zoom_level': 1.0
            }
        }
        
        # Load existing configuration
        self.config = self._load_config()
        
        # Save the config to ensure the file exists
        if not os.path.exists(self.config_file):
            self._save_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary.
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                config = self.default_config.copy()
                for section in loaded_config:
                    if section in config:
                        config[section].update(loaded_config[section])
                    else:
                        config[section] = loaded_config[section]
                
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def _save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Warning: Could not save config file: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section (str): Configuration section.
            key (str): Configuration key.
            default (Any): Default value if key doesn't exist.
        
        Returns:
            Any: Configuration value.
        """
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any, save: bool = True) -> bool:
        """
        Set a configuration value.
        
        Args:
            section (str): Configuration section.
            key (str): Configuration key.
            value (Any): Value to set.
            save (bool): Whether to save immediately.
        
        Returns:
            bool: True if set successfully, False otherwise.
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        
        if save:
            return self._save_config()
        return True
    
    def get_skin_config(self) -> Dict[str, Any]:
        """
        Get skin configuration.
        
        Returns:
            Dict[str, Any]: Skin configuration.
        """
        return self.config.get('skin', self.default_config['skin'].copy())
    
    def set_skin_config(self, current_skin: str, tile_size: int, save: bool = True) -> bool:
        """
        Set skin configuration.
        
        Args:
            current_skin (str): Name of the current skin.
            tile_size (int): Current tile size.
            save (bool): Whether to save immediately.
        
        Returns:
            bool: True if set successfully, False otherwise.
        """
        self.set('skin', 'current_skin', current_skin, save=False)
        self.set('skin', 'tile_size', tile_size, save=False)
        
        if save:
            return self._save_config()
        return True
    
    def get_display_config(self) -> Dict[str, Any]:
        """
        Get display configuration.
        
        Returns:
            Dict[str, Any]: Display configuration.
        """
        return self.config.get('display', self.default_config['display'].copy())
    
    def set_display_config(self, width: int = None, height: int = None, 
                         fullscreen: bool = None, save: bool = True) -> bool:
        """
        Set display configuration.
        
        Args:
            width (int, optional): Window width.
            height (int, optional): Window height.
            fullscreen (bool, optional): Fullscreen mode.
            save (bool): Whether to save immediately.
        
        Returns:
            bool: True if set successfully, False otherwise.
        """
        if width is not None:
            self.set('display', 'window_width', width, save=False)
        if height is not None:
            self.set('display', 'window_height', height, save=False)
        if fullscreen is not None:
            self.set('display', 'fullscreen', fullscreen, save=False)
        
        if save:
            return self._save_config()
        return True
    
    def get_game_config(self) -> Dict[str, Any]:
        """
        Get game configuration.
        
        Returns:
            Dict[str, Any]: Game configuration.
        """
        return self.config.get('game', self.default_config['game'].copy())
    
    def set_game_config(self, keyboard_layout: str = None, show_grid: bool = None,
                       zoom_level: float = None, save: bool = True) -> bool:
        """
        Set game configuration.
        
        Args:
            keyboard_layout (str, optional): Keyboard layout.
            show_grid (bool, optional): Whether to show grid.
            zoom_level (float, optional): Zoom level.
            save (bool): Whether to save immediately.
        
        Returns:
            bool: True if set successfully, False otherwise.
        """
        if keyboard_layout is not None:
            self.set('game', 'keyboard_layout', keyboard_layout, save=False)
        if show_grid is not None:
            self.set('game', 'show_grid', show_grid, save=False)
        if zoom_level is not None:
            self.set('game', 'zoom_level', zoom_level, save=False)
        
        if save:
            return self._save_config()
        return True
    
    def save(self) -> bool:
        """
        Force save configuration.
        
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        return self._save_config()
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults.
        
        Returns:
            bool: True if reset successfully, False otherwise.
        """
        self.config = self.default_config.copy()
        return self._save_config()


# Global configuration manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager: The global configuration manager.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager