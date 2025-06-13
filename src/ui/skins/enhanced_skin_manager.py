"""
Enhanced Skin Manager for the Sokoban game.

This module provides an improved skin management system with support for:
- Multiple tile sizes (8x8, 16x16, 32x32, 64x64)
- Directional player sprites
- Custom sprite loading
- Background support
- Layer-based rendering
- Sequential sprite animation (one sprite per movement)
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
    - Advanced undo sprite restoration system

    Layer System:
    - Background layer: Contains floor sprites
    - Foreground layer: Contains walls, targets, player, and boxes

    Sprite Support:
    - Uses sequential sprites for each direction
    - One sprite per movement in sequence
    - Cycles through available sprites for each direction
    - Tracks sprite history for undo functionality with detailed debugging
    - Supports undo mode for accurate sprite restoration
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
        self.first_movement = True  # Track if this is the first movement

        # Animation support
        self.animation_frames = {}
        self.current_frame_indices = {  # Track current frame index for each direction
            'walking_up': 0,
            'walking_down': 0,
            'walking_left': 0,
            'walking_right': 0,
            'pushing_up': 0,
            'pushing_down': 0,
            'pushing_left': 0,
            'pushing_right': 0
        }
        
        # Enhanced sprite history and undo system
        self.sprite_history = []  # Track sprites used for undo functionality
        self.detailed_sprite_history = []  # Detailed history with metadata
        self.undo_mode = False  # Flag to indicate we're in undo mode
        self.undo_sprite = None  # The sprite to use during undo mode
        self.move_counter = 0  # Track move numbers for debugging
        
        # Debugging support
        import time
        self.debug_timestamps = {}
        self.start_time = time.time()

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

                # Debug output to help diagnose issues
                # print(f"Loaded {len(animation_frames)} animation frames for {base_sprite}")

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

    def _log_debug(self, message, category="GENERAL"):
        """
        Log debug message with timestamp and category.
        
        Args:
            message (str): Debug message to log
            category (str): Category of the debug message
        """
        import time
        current_time = time.time()
        elapsed = current_time - self.start_time
        timestamp = f"[{elapsed:.3f}s]"
        print(f"{timestamp} [{category}] {message}")

    def get_sprite_info(self, sprite):
        """
        Get identifying information about a sprite for debugging.
        
        Args:
            sprite (pygame.Surface): The sprite to identify
            
        Returns:
            str: Human-readable sprite identifier
        """
        if not sprite:
            return "None"
        
        # Try to find the sprite in our known sprites
        skin_data = self._load_current_skin()
        for key, value in skin_data.items():
            if value is sprite:
                return f"sprite_{key}"
        
        # Check animation frames
        for base_key, frames in self.animation_frames.items():
            for i, frame in enumerate(frames):
                if frame is sprite:
                    return f"anim_{base_key}_frame_{i}"
        
        # Fallback to memory address
        return f"sprite_{id(sprite)}"

    def enter_undo_mode(self, undo_sprite):
        """
        Enter undo mode with a specific sprite to display.
        
        Args:
            undo_sprite (pygame.Surface): The sprite to use during undo mode
        """
        self.undo_mode = True
        self.undo_sprite = undo_sprite
        sprite_info = self.get_sprite_info(undo_sprite)
        self._log_debug(f"Entering undo mode with sprite: {sprite_info}", "UNDO_MODE")
        self._log_debug(f"Current sprite history length: {len(self.sprite_history)}", "UNDO_MODE")
        self._log_debug(f"Detailed history length: {len(self.detailed_sprite_history)}", "UNDO_MODE")

    def exit_undo_mode(self):
        """
        Exit undo mode and return to normal sprite calculation.
        """
        if self.undo_mode:
            self._log_debug("Exiting undo mode", "UNDO_MODE")
            self.undo_mode = False
            self.undo_sprite = None

    def get_previous_sprite(self):
        """
        Get the previous sprite from the history for undo functionality.

        When undoing multiple moves, this will return each previous sprite
        in reverse order, allowing the player to see the exact sequence
        of sprites that were used during the original moves.

        Returns:
            pygame.Surface: The previous sprite, or None if history is empty.
        """
        self._log_debug(f"get_previous_sprite called", "UNDO")
        self._log_debug(f"Sprite history length: {len(self.sprite_history)}", "UNDO")
        self._log_debug(f"Detailed history length: {len(self.detailed_sprite_history)}", "UNDO")
        
        if not self.sprite_history:
            self._log_debug("Sprite history is empty, returning None", "UNDO")
            return None

        # Pop the current sprite from history
        current_sprite = self.sprite_history.pop()
        current_sprite_info = self.get_sprite_info(current_sprite)
        self._log_debug(f"Popped current sprite: {current_sprite_info}", "UNDO")

        # Also pop from detailed history if available
        if self.detailed_sprite_history:
            detailed_entry = self.detailed_sprite_history.pop()
            self._log_debug(f"Popped detailed entry: move_{detailed_entry['move_number']}, state_{detailed_entry['player_state']}, sprite_{self.get_sprite_info(detailed_entry['sprite'])}", "UNDO")
            # Adjust move counter to maintain consistency
            if self.detailed_sprite_history:
                self.move_counter = self.detailed_sprite_history[-1]['move_number'] + 1
            else:
                self.move_counter = 0

        # If there are no more sprites in history, return the current sprite
        if not self.sprite_history:
            # Add it back to history so we don't lose it
            self.sprite_history.append(current_sprite)
            if 'detailed_entry' in locals():
                self.detailed_sprite_history.append(detailed_entry)
                # Restore move counter
                self.move_counter = detailed_entry['move_number'] + 1
            self._log_debug(f"Only one sprite in history, returning it: {current_sprite_info}", "UNDO")
            self._log_debug(f"Updated sprite history length: {len(self.sprite_history)}", "UNDO")
            # Enter undo mode with this sprite
            self.enter_undo_mode(current_sprite)
            return current_sprite

        # Return the previous sprite (now the last one in history)
        previous_sprite = self.sprite_history[-1]
        previous_sprite_info = self.get_sprite_info(previous_sprite)
        self._log_debug(f"Returning previous sprite from history: {previous_sprite_info}", "UNDO")
        self._log_debug(f"Remaining sprite history length: {len(self.sprite_history)}", "UNDO")
        
        # Enter undo mode with the previous sprite
        self.enter_undo_mode(previous_sprite)
        return previous_sprite

    def reset_sprite_history(self):
        """Reset the sprite history when starting a new level."""
        self._log_debug("Resetting sprite history", "RESET")
        self.sprite_history = []
        self.detailed_sprite_history = []
        self.first_movement = True
        self.current_player_state = 'idle'  # Reset to idle state
        self.last_move_direction = None  # Reset direction
        self.move_counter = 0
        self.exit_undo_mode()  # Make sure we're not in undo mode
        
        # Reset all frame indices
        for state in self.current_frame_indices:
            self.current_frame_indices[state] = 0

        self._log_debug("Sprite history reset completed", "RESET")
        self._log_debug(f"All frame indices reset: {self.current_frame_indices}", "RESET")

    def update_player_state(self, direction=None, is_pushing=False, is_blocked=False):
        """Update the player state for directional sprites."""
        # Exit undo mode when player makes a new move
        if direction and self.undo_mode:
            self.exit_undo_mode()
        
        self._log_debug(f"update_player_state called: direction={direction}, pushing={is_pushing}, blocked={is_blocked}", "STATE_UPDATE")
        
        # If this is the first movement, set first_movement to False
        if direction and self.first_movement:
            self.first_movement = False
            self._log_debug("First movement detected, setting first_movement=False", "STATE_UPDATE")

        # Check if direction changed
        direction_changed = direction != self.last_move_direction
        self.last_move_direction = direction
        self.is_pushing = is_pushing

        # Store previous state to check if it changed
        previous_state = self.current_player_state

        if is_blocked:
            self.current_player_state = 'against_wall'
        elif is_pushing and direction:
            state = f'pushing_{direction}'
            self.current_player_state = state
            # Reset frame index if direction changed
            if direction_changed and state in self.current_frame_indices:
                self.current_frame_indices[state] = 0
                self._log_debug(f"Reset frame index for {state} due to direction change", "STATE_UPDATE")
        elif direction:
            state = f'walking_{direction}'
            self.current_player_state = state
            # Reset frame index if direction changed
            if direction_changed and state in self.current_frame_indices:
                self.current_frame_indices[state] = 0
                self._log_debug(f"Reset frame index for {state} due to direction change", "STATE_UPDATE")
        else:
            self.current_player_state = 'idle'

        self._log_debug(f"Player state updated: {previous_state} -> {self.current_player_state}", "STATE_UPDATE")
        self._log_debug(f"Direction changed: {direction_changed}, Last direction: {self.last_move_direction}", "STATE_UPDATE")

    def get_player_sprite(self, advance_animation=False):
        """
        Get the current player sprite based on state, with sequential animation.

        For movement animations, shows one sprite per tile movement in sequence.
        Cycles through available sprites for each direction.
        Tracks sprite history for undo functionality.

        Args:
            advance_animation (bool): Whether to advance to the next animation frame.
                                     Set to True only when called for a new movement.

        Returns:
            pygame.Surface: The player sprite to display.
        """
        # Only log when advancing animation (not every frame)
        if advance_animation:
            self._log_debug(f"get_player_sprite called: advance_animation={advance_animation}, undo_mode={self.undo_mode}", "SPRITE_GET")
        
        # If we're in undo mode, return the undo sprite
        if self.undo_mode and self.undo_sprite is not None:
            return self.undo_sprite
        
        skin_data = self._load_current_skin()

        # If this is the first movement (game just started), use the default player sprite
        if self.first_movement:
            default_sprite = skin_data.get(PLAYER, skin_data.get('player'))
            sprite_info = self.get_sprite_info(default_sprite)
            # Only add to history if not already there
            if not self.sprite_history or self.sprite_history[-1] != default_sprite:
                self.sprite_history.append(default_sprite)
                # Add to detailed history
                self._add_to_detailed_history(default_sprite, "idle", "first_movement")
                self._log_debug(f"Added default sprite to history: {sprite_info}", "SPRITE_GET")
            return default_sprite

        # Try to get directional sprite
        sprite_key = self.player_states.get(self.current_player_state, 'player')
        # Only log state changes during animation advancement
        if advance_animation:
            self._log_debug(f"Current player state: {self.current_player_state}, sprite_key: {sprite_key}", "SPRITE_GET")

        # Get the sprite based on the current state
        if self.current_player_state in ['walking_up', 'walking_down', 'walking_left', 'walking_right',
                                        'pushing_up', 'pushing_down', 'pushing_left', 'pushing_right']:
            # Check if we have numbered frames for this direction
            base_sprite_key = sprite_key
            if base_sprite_key in self.animation_frames and self.animation_frames[base_sprite_key]:
                frames = self.animation_frames[base_sprite_key]
                if frames:
                    # Get the current frame index for this direction
                    frame_index = self.current_frame_indices[self.current_player_state]
                    
                    # Only log animation details when advancing
                    if advance_animation:
                        self._log_debug(f"Animation frames available for {base_sprite_key}: {len(frames)} frames, current index: {frame_index}", "SPRITE_GET")

                    # Make sure frame_index is within bounds
                    if frame_index >= len(frames):
                        frame_index = 0
                        self.current_frame_indices[self.current_player_state] = 0
                        if advance_animation:
                            self._log_debug(f"Frame index out of bounds, reset to 0", "SPRITE_GET")

                    # Get the sprite for this frame
                    sprite = frames[frame_index]
                    sprite_info = self.get_sprite_info(sprite)

                    # Only increment the frame index if advance_animation is True
                    if advance_animation:
                        # Increment the frame index for next movement in this direction
                        next_frame_index = (frame_index + 1) % len(frames)
                        self.current_frame_indices[self.current_player_state] = next_frame_index
                        # Add to sprite history only when advancing animation
                        self.sprite_history.append(sprite)
                        # Add to detailed history
                        self._add_to_detailed_history(sprite, self.current_player_state, f"animation_frame_{frame_index}")
                        self._log_debug(f"Advanced animation: added frame sprite to history: {sprite_info}", "SPRITE_GET")

                    return sprite

            # If no animation frames, use the basic directional sprite
            if sprite_key in skin_data:
                sprite = skin_data[sprite_key]
                sprite_info = self.get_sprite_info(sprite)
                # Only add to history if advance_animation is True
                if advance_animation:
                    self.sprite_history.append(sprite)
                    # Add to detailed history
                    self._add_to_detailed_history(sprite, self.current_player_state, "basic_directional")
                    self._log_debug(f"Added basic directional sprite to history: {sprite_info}", "SPRITE_GET")
                return sprite

        # For other states (idle, blocked, etc.)
        if sprite_key in skin_data:
            sprite = skin_data[sprite_key]
            sprite_info = self.get_sprite_info(sprite)
            # Only add to history if advance_animation is True
            if advance_animation:
                self.sprite_history.append(sprite)
                # Add to detailed history
                self._add_to_detailed_history(sprite, self.current_player_state, "other_state")
                self._log_debug(f"Added other state sprite to history: {sprite_info}", "SPRITE_GET")
            return sprite

        # Fallback to basic player sprite
        default_sprite = skin_data.get(PLAYER, skin_data.get('player'))
        sprite_info = self.get_sprite_info(default_sprite)
        # Only add to history if advance_animation is True
        if advance_animation:
            self.sprite_history.append(default_sprite)
            # Add to detailed history
            self._add_to_detailed_history(default_sprite, self.current_player_state, "fallback")
            self._log_debug(f"Added fallback sprite to history: {sprite_info}", "SPRITE_GET")
        return default_sprite

    def _add_to_detailed_history(self, sprite, player_state, sprite_type):
        """
        Add entry to detailed sprite history with metadata.
        
        Args:
            sprite (pygame.Surface): The sprite being added
            player_state (str): Current player state
            sprite_type (str): Type/source of the sprite
        """
        import time
        entry = {
            'move_number': self.move_counter,
            'sprite': sprite,
            'player_state': player_state,
            'sprite_type': sprite_type,
            'timestamp': time.time(),
            'frame_indices': self.current_frame_indices.copy()
        }
        self.detailed_sprite_history.append(entry)
        self.move_counter += 1
        
        # Only log detailed history additions during important operations
        if sprite_type in ["first_movement"] or "undo" in sprite_type.lower():
            sprite_info = self.get_sprite_info(sprite)
            self._log_debug(f"Added to detailed history: move_{entry['move_number']}, state_{player_state}, type_{sprite_type}, sprite_{sprite_info}", "DETAILED_HISTORY")

    def get_undo_debug_info(self):
        """
        Get comprehensive debug information about sprite history.
        
        Returns:
            dict: Debug information about current sprite state
        """
        return {
            'sprite_history_length': len(self.sprite_history),
            'detailed_history_length': len(self.detailed_sprite_history),
            'current_player_state': self.current_player_state,
            'undo_mode': self.undo_mode,
            'move_counter': self.move_counter,
            'frame_indices': self.current_frame_indices.copy(),
            'last_move_direction': self.last_move_direction,
            'undo_sprite_info': self.get_sprite_info(self.undo_sprite) if self.undo_sprite else None
        }

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
    
    def print_sprite_history_debug(self):
        """
        Print detailed debug information about the complete sprite history.
        """
        self._log_debug("=== SPRITE HISTORY DEBUG START ===", "DEBUG")
        self._log_debug(f"Basic sprite history length: {len(self.sprite_history)}", "DEBUG")
        self._log_debug(f"Detailed sprite history length: {len(self.detailed_sprite_history)}", "DEBUG")
        self._log_debug(f"Undo mode: {self.undo_mode}", "DEBUG")
        self._log_debug(f"Current player state: {self.current_player_state}", "DEBUG")
        self._log_debug(f"Move counter: {self.move_counter}", "DEBUG")
        
        if self.sprite_history:
            self._log_debug("Basic sprite history (recent to old):", "DEBUG")
            for i, sprite in enumerate(reversed(self.sprite_history)):
                sprite_info = self.get_sprite_info(sprite)
                self._log_debug(f"  [{i}] {sprite_info}", "DEBUG")
        
        if self.detailed_sprite_history:
            self._log_debug("Detailed sprite history (recent to old):", "DEBUG")
            for i, entry in enumerate(reversed(self.detailed_sprite_history)):
                sprite_info = self.get_sprite_info(entry['sprite'])
                self._log_debug(f"  [{i}] Move #{entry['move_number']}: {sprite_info} (state={entry['player_state']}, type={entry['sprite_type']})", "DEBUG")
        
        self._log_debug(f"Current frame indices: {self.current_frame_indices}", "DEBUG")
        
        if self.undo_sprite:
            undo_sprite_info = self.get_sprite_info(self.undo_sprite)
            self._log_debug(f"Undo sprite: {undo_sprite_info}", "DEBUG")
        
        self._log_debug("=== SPRITE HISTORY DEBUG END ===", "DEBUG")
    
    def validate_sprite_history_integrity(self):
        """
        Validate that sprite history is in a consistent state.
        
        Returns:
            bool: True if history is consistent, False otherwise
        """
        try:
            # Check that basic and detailed histories have same length
            if len(self.sprite_history) != len(self.detailed_sprite_history):
                self._log_debug(f"INTEGRITY ERROR: History length mismatch - basic: {len(self.sprite_history)}, detailed: {len(self.detailed_sprite_history)}", "VALIDATION")
                return False
            
            # Check that sprites match between basic and detailed histories
            for i, (basic_sprite, detailed_entry) in enumerate(zip(self.sprite_history, self.detailed_sprite_history)):
                if basic_sprite != detailed_entry['sprite']:
                    basic_info = self.get_sprite_info(basic_sprite)
                    detailed_info = self.get_sprite_info(detailed_entry['sprite'])
                    self._log_debug(f"INTEGRITY ERROR: Sprite mismatch at index {i} - basic: {basic_info}, detailed: {detailed_info}", "VALIDATION")
                    return False
            
            # Check move counter consistency
            if self.detailed_sprite_history:
                last_move = self.detailed_sprite_history[-1]['move_number']
                if last_move + 1 != self.move_counter:
                    self._log_debug(f"INTEGRITY ERROR: Move counter inconsistent - last move: {last_move}, counter: {self.move_counter}", "VALIDATION")
                    return False
            
            self._log_debug("Sprite history integrity validation passed", "VALIDATION")
            return True
            
        except Exception as e:
            self._log_debug(f"INTEGRITY ERROR: Exception during validation: {e}", "VALIDATION")
            return False
