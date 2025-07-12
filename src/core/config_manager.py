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
                'zoom_level': 1.0,
                'movement_cooldown': 200,
                'mouse_movement_speed': 100,
                'grid_color': [255, 255, 255],
                'show_deadlocks': True
            },
            'keybindings': {
                'up': 'up',
                'down': 'down',
                'left': 'left',
                'right': 'right',
                'reset': 'r',
                'quit': 'q',
                'next': 'n',
                'previous': 'p',
                'undo': 'u',
                'help': 'h',
                'grid': 'g',
                'fullscreen': 'f11',
                'solve': 's'
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
            # Print the current keyboard layout before saving
            keyboard_layout = self.config.get('game', {}).get('keyboard_layout', 'unknown')
            print(f"ConfigManager: Saving keyboard_layout={keyboard_layout} to {self.config_file}")

            # Check if the config file exists and is writable
            if os.path.exists(self.config_file):
                if not os.access(self.config_file, os.W_OK):
                    print(f"ConfigManager: WARNING - Config file {self.config_file} is not writable!")
                    # Try to make the file writable
                    try:
                        import stat
                        current_permissions = os.stat(self.config_file).st_mode
                        os.chmod(self.config_file, current_permissions | stat.S_IWUSR)
                        print(f"ConfigManager: Attempted to make config file writable")
                    except Exception as e:
                        print(f"ConfigManager: Failed to make config file writable: {e}")

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # Print the full config for debugging
            print(f"ConfigManager: Full config to save: {self.config}")

            # Try to create a backup of the config file first
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.bak"
                try:
                    import shutil
                    shutil.copy2(self.config_file, backup_file)
                    print(f"ConfigManager: Created backup of config file at {backup_file}")
                except Exception as e:
                    print(f"ConfigManager: Failed to create backup of config file: {e}")

            # Write the config file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            # Verify the file was written correctly
            print(f"ConfigManager: Config file saved successfully")

            # Read the file back to verify the changes were saved
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    saved_keyboard_layout = saved_config.get('game', {}).get('keyboard_layout', 'unknown')
                    print(f"ConfigManager: Verified saved keyboard_layout={saved_keyboard_layout}")
                    if saved_keyboard_layout != keyboard_layout:
                        print(f"ConfigManager: WARNING - Saved keyboard layout ({saved_keyboard_layout}) does not match expected value ({keyboard_layout})")
            except Exception as e:
                print(f"ConfigManager: Error verifying saved config: {e}")
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
                       zoom_level: float = None, movement_cooldown: int = None, 
                       mouse_movement_speed: int = None, grid_color: list = None, 
                       show_deadlocks: bool = None, save: bool = True) -> bool:
        """
        Set game configuration.

        Args:
            keyboard_layout (str, optional): Keyboard layout.
            show_grid (bool, optional): Whether to show grid.
            zoom_level (float, optional): Zoom level.
            movement_cooldown (int, optional): Movement cooldown in milliseconds for keyboard movement.
            mouse_movement_speed (int, optional): Movement speed in milliseconds for mouse navigation.
            grid_color (list, optional): Grid color as [r, g, b] list.
            show_deadlocks (bool, optional): Whether to show deadlock notifications.
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
        if movement_cooldown is not None:
            self.set('game', 'movement_cooldown', movement_cooldown, save=False)
        if mouse_movement_speed is not None:
            self.set('game', 'mouse_movement_speed', mouse_movement_speed, save=False)
        if grid_color is not None:
            self.set('game', 'grid_color', grid_color, save=False)
        if show_deadlocks is not None:
            self.set('game', 'show_deadlocks', show_deadlocks, save=False)

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

    def get_keybindings(self) -> Dict[str, str]:
        """
        Get keybindings configuration.

        Returns:
            Dict[str, str]: Keybindings configuration.
        """
        return self.config.get('keybindings', self.default_config['keybindings'].copy())

    def set_keybinding(self, action: str, key: str, save: bool = True) -> bool:
        """
        Set a keybinding for a specific action.

        Args:
            action (str): Action name (e.g., 'up', 'down', 'reset', etc.).
            key (str): Key name to bind to the action.
            save (bool): Whether to save immediately.

        Returns:
            bool: True if set successfully, False otherwise.
        """
        return self.set('keybindings', action, key, save)

    def reset_keybindings(self, save: bool = True) -> bool:
        """
        Reset keybindings to defaults.

        Args:
            save (bool): Whether to save immediately.

        Returns:
            bool: True if reset successfully, False otherwise.
        """
        self.config['keybindings'] = self.default_config['keybindings'].copy()
        if save:
            return self._save_config()
        return True

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
