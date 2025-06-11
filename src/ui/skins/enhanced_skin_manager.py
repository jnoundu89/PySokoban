"""
Enhanced Skin Manager for the Sokoban game.

This module provides an improved skin management system with support for:
- Multiple tile sizes (8x8, 16x16, 32x32, 64x64)
- Directional player sprites
- Custom sprite loading
- Background support
- Animation states
- Layer-based rendering
- Animation sequences for player movement
"""

import os
import pygame
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE
from src.core.config_manager import get_config_manager

class EnhancedSkinManager:
    """
    Enhanced class for managing game skins and sprites.

    Features:
    - Multiple tile sizes (8x8, 16x16, 32x32, 64x64, 128x128)
    - Directional player sprites (up, down, left, right)
    - Player state support (idle, walking, pushing, blocked)
    - Layer-based rendering (background and foreground layers)
    - Animation sequences for player movement
    - Custom sprite loading
    - Background support

    Layer System:
    - Background layer: Contains floor sprites
    - Foreground layer: Contains walls, targets, player, and boxes

    Animation Support:
    - Detects numbered sprites (e.g., player_down_1.png, player_down_2.png)
    - Plays animations during player movement
    - Falls back to single sprite when animations aren't available
    """

    def __init__(self, skins_dir='skins'):
        """
        Initialize the enhanced skin manager.

        Args:
            skins_dir (str): Directory containing skin files.
        """
        # Update the skins directory to be relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.skins_dir = os.path.join(project_root, skins_dir)

        # Get configuration manager
        self.config_manager = get_config_manager()

        # Load settings from configuration
        skin_config = self.config_manager.get_skin_config()
        self.current_skin = skin_config.get('current_skin', 'default')
        self.tile_size = skin_config.get('tile_size', 64)
        self.available_tile_sizes = [8, 16, 32, 64, 128]

        # Player states for directional sprites
        self.player_states = {
            'idle': 'player',
            'walking_up': 'player_up',
            'walking_down': 'player_down', 
            'walking_left': 'player_left',
            'walking_right': 'player_right',
            'pushing_up': 'player_push_up',
            'pushing_down': 'player_push_down',
            'pushing_left': 'player_push_left',
            'pushing_right': 'player_push_right',
            'against_wall': 'player_blocked'
        }

        # Current player state
        self.current_player_state = 'idle'
        self.last_move_direction = None
        self.is_pushing = False

        # Animation support
        self.animation_frames = {}
        self.current_animation_frame = 0
        self.animation_speed = 3  # Frames to show each animation image
        self.animation_counter = 0

        # Layer system
        self.layers = {
            'background': {},  # Floor layer
            'foreground': {}   # Walls, targets, player, boxes layer
        }

        # Loaded skins cache
        self.skins_cache = {}
        self.available_skins = []

        # Background
        self.background = None

        # Initialize
        self._discover_skins()
        self._load_current_skin()

    def _discover_skins(self):
        """Discover available skins in the skins directory."""
        self.available_skins = ['default']

        if os.path.exists(self.skins_dir):
            for item in os.listdir(self.skins_dir):
                skin_path = os.path.join(self.skins_dir, item)
                if os.path.isdir(skin_path) and item != 'default':
                    self.available_skins.append(item)

    def _load_current_skin(self):
        """Load the current skin."""
        if self.current_skin in self.skins_cache:
            return self.skins_cache[self.current_skin]

        skin_data = {}
        skin_path = os.path.join(self.skins_dir, self.current_skin)

        if os.path.exists(skin_path):
            # Try to load sprites from files
            skin_data = self._load_skin_from_files(skin_path)

        if not skin_data:
            # Create default skin
            skin_data = self._create_default_skin()

        # Cache the skin
        self.skins_cache[self.current_skin] = skin_data
        return skin_data

    def _load_skin_from_files(self, skin_path):
        """Load skin sprites from image files."""
        skin_data = {}

        # Reset layers and animation frames
        self.layers = {
            'background': {},  # Floor layer
            'foreground': {}   # Walls, targets, player, boxes layer
        }
        self.animation_frames = {}

        # Basic sprites
        sprite_files = {
            WALL: 'wall.png',
            FLOOR: 'floor.png',
            PLAYER: 'player.png',
            BOX: 'box.png',
            TARGET: 'target.png',
            BOX_ON_TARGET: 'box_on_target.png'
        }

        # Note: player_on_target.png is no longer needed as we use layers now
        # We'll still load it for backward compatibility if it exists

        # Directional player sprites
        directional_sprites = {
            'player_up': 'player_up.png',
            'player_down': 'player_down.png',
            'player_left': 'player_left.png',
            'player_right': 'player_right.png',
            'player_push_up': 'player_push_up.png',
            'player_push_down': 'player_push_down.png',
            'player_push_left': 'player_push_left.png',
            'player_push_right': 'player_push_right.png',
            'player_blocked': 'player_blocked.png'
        }

        # Load basic sprites and assign to layers
        for sprite_key, filename in sprite_files.items():
            file_path = os.path.join(skin_path, filename)
            if os.path.exists(file_path):
                try:
                    sprite = pygame.image.load(file_path)
                    sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
                    skin_data[sprite_key] = sprite

                    # Assign to appropriate layer
                    if sprite_key == FLOOR:
                        self.layers['background'][sprite_key] = sprite
                    else:
                        self.layers['foreground'][sprite_key] = sprite
                except pygame.error:
                    continue

        # Check for player_on_target.png for backward compatibility
        player_on_target_path = os.path.join(skin_path, 'player_on_target.png')
        if os.path.exists(player_on_target_path):
            try:
                sprite = pygame.image.load(player_on_target_path)
                sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
                skin_data[PLAYER_ON_TARGET] = sprite
                # We don't add it to layers as we'll use the layer system instead
            except pygame.error:
                pass

        # Load directional sprites
        for sprite_key, filename in directional_sprites.items():
            file_path = os.path.join(skin_path, filename)
            if os.path.exists(file_path):
                try:
                    sprite = pygame.image.load(file_path)
                    sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
                    skin_data[sprite_key] = sprite
                    self.layers['foreground'][sprite_key] = sprite
                except pygame.error:
                    continue

        # Check for animation sequences (e.g., player_down_1.png, player_down_2.png, etc.)
        for base_sprite in ['player_up', 'player_down', 'player_left', 'player_right',
                           'player_push_up', 'player_push_down', 'player_push_left', 'player_push_right']:
            # Look for numbered animation frames
            frame_index = 1
            animation_frames = []

            while True:
                frame_filename = f"{base_sprite}_{frame_index}.png"
                frame_path = os.path.join(skin_path, frame_filename)

                if os.path.exists(frame_path):
                    try:
                        frame = pygame.image.load(frame_path)
                        frame = pygame.transform.scale(frame, (self.tile_size, self.tile_size))
                        animation_frames.append(frame)
                        frame_index += 1
                    except pygame.error:
                        break
                else:
                    break

            # If we found animation frames, store them
            if animation_frames:
                self.animation_frames[base_sprite] = animation_frames
                # Use the first frame as the default sprite if we don't already have one
                if base_sprite not in skin_data:
                    skin_data[base_sprite] = animation_frames[0]
                    self.layers['foreground'][base_sprite] = animation_frames[0]

        # Load background if available
        bg_path = os.path.join(skin_path, 'background.png')
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path)
            except pygame.error:
                self.background = None

        return skin_data

    def _create_default_skin(self):
        """Create default skin sprites."""
        skin_data = {}

        # Reset layers
        self.layers = {
            'background': {},  # Floor layer
            'foreground': {}   # Walls, targets, player, boxes layer
        }

        # Colors for default sprites
        colors = {
            'wall': (100, 100, 100),
            'floor': (220, 220, 220),
            'player': (0, 100, 255),
            'box': (139, 69, 19),
            'target': (255, 0, 0),
            'background': (240, 240, 240)
        }

        # Create basic sprites and assign to layers
        wall_sprite = self._create_wall_sprite(colors)
        floor_sprite = self._create_floor_sprite(colors)
        player_sprite = self._create_player_sprite(colors)
        box_sprite = self._create_box_sprite(colors)
        target_sprite = self._create_target_sprite(colors)
        player_on_target_sprite = self._create_player_on_target_sprite(colors)
        box_on_target_sprite = self._create_box_on_target_sprite(colors)

        # Assign to skin_data
        skin_data[WALL] = wall_sprite
        skin_data[FLOOR] = floor_sprite
        skin_data[PLAYER] = player_sprite
        skin_data[BOX] = box_sprite
        skin_data[TARGET] = target_sprite
        skin_data[PLAYER_ON_TARGET] = player_on_target_sprite
        skin_data[BOX_ON_TARGET] = box_on_target_sprite

        # Assign to layers
        self.layers['background'][FLOOR] = floor_sprite
        self.layers['foreground'][WALL] = wall_sprite
        self.layers['foreground'][PLAYER] = player_sprite
        self.layers['foreground'][BOX] = box_sprite
        self.layers['foreground'][TARGET] = target_sprite
        self.layers['foreground'][PLAYER_ON_TARGET] = player_on_target_sprite
        self.layers['foreground'][BOX_ON_TARGET] = box_on_target_sprite

        # Create directional player sprites
        directional_sprites = {
            'player_up': 'up',
            'player_down': 'down',
            'player_left': 'left',
            'player_right': 'right',
            'player_push_up': 'push_up',
            'player_push_down': 'push_down',
            'player_push_left': 'push_left',
            'player_push_right': 'push_right',
            'player_blocked': 'blocked'
        }

        # Create and assign directional sprites
        for sprite_key, direction in directional_sprites.items():
            sprite = self._create_directional_player_sprite(colors, direction)
            skin_data[sprite_key] = sprite
            self.layers['foreground'][sprite_key] = sprite

        return skin_data

    def _create_wall_sprite(self, colors):
        """Create a wall sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['wall'])

        # Add some texture
        border_size = max(1, self.tile_size // 16)
        inner_rect = pygame.Rect(border_size, border_size, 
                                self.tile_size - 2 * border_size, 
                                self.tile_size - 2 * border_size)
        pygame.draw.rect(surface, (120, 120, 120), inner_rect)

        return surface

    def _create_floor_sprite(self, colors):
        """Create a floor sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['floor'])
        return surface

    def _create_player_sprite(self, colors):
        """Create a player sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['floor'])  # Floor background

        # Draw player as a circle
        center = self.tile_size // 2
        radius = self.tile_size // 3
        pygame.draw.circle(surface, colors['player'], (center, center), radius)

        # Add eyes
        eye_size = max(1, self.tile_size // 16)
        eye_offset = radius // 3
        pygame.draw.circle(surface, (255, 255, 255), 
                          (center - eye_offset, center - eye_offset), eye_size)
        pygame.draw.circle(surface, (255, 255, 255), 
                          (center + eye_offset, center - eye_offset), eye_size)

        return surface

    def _create_directional_player_sprite(self, colors, direction):
        """Create a directional player sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['floor'])  # Floor background

        center = self.tile_size // 2
        radius = self.tile_size // 3

        # Base color depends on state
        if 'push' in direction:
            player_color = (min(255, colors['player'][0] + 30), colors['player'][1], colors['player'][2])
        elif 'blocked' in direction:
            player_color = (colors['player'][0], colors['player'][1], min(255, colors['player'][2] + 30))
        else:
            player_color = colors['player']

        pygame.draw.circle(surface, player_color, (center, center), radius)

        # Add directional indicator
        indicator_size = max(2, self.tile_size // 8)
        if direction in ['up', 'push_up']:
            pygame.draw.polygon(surface, (255, 255, 255), [
                (center, center - radius // 2),
                (center - indicator_size, center),
                (center + indicator_size, center)
            ])
        elif direction in ['down', 'push_down']:
            pygame.draw.polygon(surface, (255, 255, 255), [
                (center, center + radius // 2),
                (center - indicator_size, center),
                (center + indicator_size, center)
            ])
        elif direction in ['left', 'push_left']:
            pygame.draw.polygon(surface, (255, 255, 255), [
                (center - radius // 2, center),
                (center, center - indicator_size),
                (center, center + indicator_size)
            ])
        elif direction in ['right', 'push_right']:
            pygame.draw.polygon(surface, (255, 255, 255), [
                (center + radius // 2, center),
                (center, center - indicator_size),
                (center, center + indicator_size)
            ])
        else:  # blocked
            # Draw X
            pygame.draw.line(surface, (255, 0, 0), 
                           (center - indicator_size, center - indicator_size),
                           (center + indicator_size, center + indicator_size), 2)
            pygame.draw.line(surface, (255, 0, 0), 
                           (center - indicator_size, center + indicator_size),
                           (center + indicator_size, center - indicator_size), 2)

        return surface

    def _create_box_sprite(self, colors):
        """Create a box sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['floor'])  # Floor background

        # Draw box
        margin = self.tile_size // 6
        box_rect = pygame.Rect(margin, margin, 
                              self.tile_size - 2 * margin, 
                              self.tile_size - 2 * margin)
        pygame.draw.rect(surface, colors['box'], box_rect)

        # Add border
        pygame.draw.rect(surface, (100, 50, 0), box_rect, max(1, self.tile_size // 32))

        return surface

    def _create_target_sprite(self, colors):
        """Create a target sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['floor'])  # Floor background

        # Draw target as concentric circles
        center = self.tile_size // 2
        outer_radius = self.tile_size // 4
        inner_radius = self.tile_size // 8

        pygame.draw.circle(surface, colors['target'], (center, center), outer_radius)
        pygame.draw.circle(surface, colors['floor'], (center, center), inner_radius)

        return surface

    def _create_player_on_target_sprite(self, colors):
        """Create a player on target sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['floor'])  # Floor background

        # Draw target first
        center = self.tile_size // 2
        target_radius = self.tile_size // 4
        pygame.draw.circle(surface, colors['target'], (center, center), target_radius)

        # Draw player on top
        player_radius = self.tile_size // 3
        pygame.draw.circle(surface, colors['player'], (center, center), player_radius)

        return surface

    def _create_box_on_target_sprite(self, colors):
        """Create a box on target sprite."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(colors['floor'])  # Floor background

        # Draw target first
        center = self.tile_size // 2
        target_radius = self.tile_size // 4
        pygame.draw.circle(surface, colors['target'], (center, center), target_radius)

        # Draw box on top
        margin = self.tile_size // 6
        box_rect = pygame.Rect(margin, margin, 
                              self.tile_size - 2 * margin, 
                              self.tile_size - 2 * margin)
        pygame.draw.rect(surface, (0, 200, 0), box_rect)  # Green box when on target
        pygame.draw.rect(surface, (0, 150, 0), box_rect, max(1, self.tile_size // 32))

        return surface

    def set_tile_size(self, size):
        """Set the tile size and reload skins."""
        if size in self.available_tile_sizes:
            self.tile_size = size
            # Save to configuration
            self.config_manager.set_skin_config(self.current_skin, self.tile_size)
            # Clear cache to force reload
            self.skins_cache.clear()
            self._load_current_skin()

    def set_skin(self, skin_name):
        """Set the current skin."""
        if skin_name in self.available_skins:
            self.current_skin = skin_name
            # Save to configuration
            self.config_manager.set_skin_config(self.current_skin, self.tile_size)
            self._load_current_skin()

    def update_player_state(self, direction=None, is_pushing=False, is_blocked=False):
        """Update the player state for directional sprites."""
        self.last_move_direction = direction
        self.is_pushing = is_pushing

        if is_blocked:
            self.current_player_state = 'against_wall'
        elif is_pushing and direction:
            self.current_player_state = f'pushing_{direction}'
        elif direction:
            self.current_player_state = f'walking_{direction}'
        else:
            self.current_player_state = 'idle'

    def get_player_sprite(self):
        """
        Get the current player sprite based on state, with animation support.

        Returns:
            pygame.Surface: The player sprite to display.
        """
        skin_data = self._load_current_skin()

        # Try to get directional sprite
        sprite_key = self.player_states.get(self.current_player_state, 'player')

        # Check if we have an animation for this sprite
        if sprite_key in self.animation_frames and self.animation_frames[sprite_key]:
            # Get the current frame from the animation sequence
            frames = self.animation_frames[sprite_key]
            if frames:
                # Advance animation counter
                self.animation_counter += 1
                if self.animation_counter >= self.animation_speed:
                    self.animation_counter = 0
                    self.current_animation_frame = (self.current_animation_frame + 1) % len(frames)

                return frames[self.current_animation_frame]

        # If no animation or animation failed, use static sprite
        if sprite_key in skin_data:
            return skin_data[sprite_key]

        # Fallback to basic player sprite
        return skin_data.get(PLAYER, skin_data.get('player'))

    def get_skin(self):
        """
        Get the current skin data.

        Returns:
            dict: Dictionary containing all skin sprites.
        """
        return self._load_current_skin()

    def get_layer(self, layer_name):
        """
        Get sprites for a specific layer.

        Args:
            layer_name (str): Name of the layer ('background' or 'foreground').

        Returns:
            dict: Dictionary containing sprites for the specified layer.
        """
        if layer_name in self.layers:
            return self.layers[layer_name]
        return {}

    def get_background(self):
        """Get the background image if available."""
        return self.background

    def get_available_skins(self):
        """Get list of available skins."""
        return self.available_skins.copy()

    def get_available_tile_sizes(self):
        """Get list of available tile sizes."""
        return self.available_tile_sizes.copy()

    def get_current_tile_size(self):
        """Get the current tile size."""
        return self.tile_size

    def get_current_skin_name(self):
        """Get the current skin name."""
        return self.current_skin
