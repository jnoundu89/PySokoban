"""
GUI renderer module for the Sokoban game.

This module provides functionality for rendering the game with a graphical user interface
using Pygame.
"""

import os
import pygame
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE


class GUIRenderer:
    """
    Class for rendering the Sokoban game with a GUI using Pygame.

    This class is responsible for rendering the game state, level information,
    and game statistics in a graphical window.
    """

    def __init__(self, window_title="Sokoban"):
        """
        Initialize the GUI renderer.

        Args:
            window_title (str, optional): The title of the game window.
                                        Defaults to "Sokoban".
        """
        pygame.init()
        pygame.display.set_caption(window_title)

        # Define colors
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (100, 100, 100),
            'dark_gray': (50, 50, 50),
            'light_gray': (200, 200, 200),
            'brown': (139, 69, 19),
            'yellow': (255, 255, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'red': (255, 0, 0),
            'background': (240, 240, 240)
        }

        # Load assets (images)
        self.assets = self._load_assets()

        # Set default window size (will be adjusted based on level size)
        self.window_size = (800, 600)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        self.scale_factor = 1.0  # For scaling elements in fullscreen mode

        # Font for rendering text
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

    def _load_assets(self):
        """
        Load game assets (images).

        Returns:
            dict: Dictionary containing loaded assets.
        """
        assets = {}

        # Check if assets directory exists, if not create default assets
        assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            return self._create_default_assets()

        # Try to load assets from files
        try:
            assets['wall'] = pygame.image.load(os.path.join(assets_dir, 'wall.png'))
            assets['floor'] = pygame.image.load(os.path.join(assets_dir, 'floor.png'))
            assets['player'] = pygame.image.load(os.path.join(assets_dir, 'player.png'))
            assets['box'] = pygame.image.load(os.path.join(assets_dir, 'box.png'))
            assets['target'] = pygame.image.load(os.path.join(assets_dir, 'target.png'))
            assets['player_on_target'] = pygame.image.load(os.path.join(assets_dir, 'player_on_target.png'))
            assets['box_on_target'] = pygame.image.load(os.path.join(assets_dir, 'box_on_target.png'))

            # Resize all assets to CELL_SIZE
            for key in assets:
                assets[key] = pygame.transform.scale(assets[key], (CELL_SIZE, CELL_SIZE))

            return assets
        except (pygame.error, FileNotFoundError):
            # If any asset is missing, use default assets
            return self._create_default_assets()

    def _create_default_assets(self):
        """
        Create default assets if image files are not available.

        Returns:
            dict: Dictionary containing created assets.
        """
        assets = {}

        # Create surfaces for each game element
        assets['wall'] = self._create_wall_surface()
        assets['floor'] = self._create_floor_surface()
        assets['player'] = self._create_player_surface()
        assets['box'] = self._create_box_surface()
        assets['target'] = self._create_target_surface()
        assets['player_on_target'] = self._create_player_on_target_surface()
        assets['box_on_target'] = self._create_box_on_target_surface()

        return assets

    def _create_wall_surface(self):
        """Create a surface for a wall."""
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill(self.colors['dark_gray'])
        pygame.draw.rect(surface, self.colors['gray'], 
                         pygame.Rect(2, 2, CELL_SIZE-4, CELL_SIZE-4))
        return surface

    def _create_floor_surface(self):
        """Create a surface for a floor tile."""
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill(self.colors['light_gray'])
        return surface

    def _create_player_surface(self):
        """Create a surface for the player."""
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill(self.colors['light_gray'])  # Floor background
        pygame.draw.circle(surface, self.colors['blue'], 
                          (CELL_SIZE // 2, CELL_SIZE // 2), CELL_SIZE // 3)
        return surface

    def _create_box_surface(self):
        """Create a surface for a box."""
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill(self.colors['light_gray'])  # Floor background
        pygame.draw.rect(surface, self.colors['brown'], 
                         pygame.Rect(CELL_SIZE//6, CELL_SIZE//6, 
                                     CELL_SIZE*2//3, CELL_SIZE*2//3))
        return surface

    def _create_target_surface(self):
        """Create a surface for a target."""
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill(self.colors['light_gray'])  # Floor background
        pygame.draw.circle(surface, self.colors['red'], 
                          (CELL_SIZE // 2, CELL_SIZE // 2), CELL_SIZE // 6)
        return surface

    def _create_player_on_target_surface(self):
        """Create a surface for the player on a target."""
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill(self.colors['light_gray'])  # Floor background
        pygame.draw.circle(surface, self.colors['red'], 
                          (CELL_SIZE // 2, CELL_SIZE // 2), CELL_SIZE // 6)
        pygame.draw.circle(surface, self.colors['blue'], 
                          (CELL_SIZE // 2, CELL_SIZE // 2), CELL_SIZE // 3)
        return surface

    def _create_box_on_target_surface(self):
        """Create a surface for a box on a target."""
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill(self.colors['light_gray'])  # Floor background
        pygame.draw.circle(surface, self.colors['red'], 
                          (CELL_SIZE // 2, CELL_SIZE // 2), CELL_SIZE // 4)
        pygame.draw.rect(surface, self.colors['green'], 
                         pygame.Rect(CELL_SIZE//6, CELL_SIZE//6, 
                                     CELL_SIZE*2//3, CELL_SIZE*2//3))
        return surface

    def render_level(self, level, level_manager=None, show_grid=False, zoom_level=1.0, scroll_x=0, scroll_y=0, skin_manager=None):
        """
        Render the current level state in the GUI.

        Args:
            level: The Level object to render.
            level_manager: Optional LevelManager object for additional information.
            show_grid: Whether to show grid lines.
            zoom_level: Zoom level for the display.
            scroll_x: Horizontal scroll offset.
            scroll_y: Vertical scroll offset.
            skin_manager: Optional enhanced skin manager for directional sprites.

        Returns:
            pygame.Surface: The updated screen surface.
        """
        # Get current screen size
        current_screen_width, current_screen_height = self.screen.get_size()

        # Calculate base window size needed for the level
        base_cell_size = CELL_SIZE * zoom_level
        base_window_width = level.width * base_cell_size
        base_window_height = level.height * base_cell_size + 100  # Extra space for stats

        # Check if we're in a resized window (including fullscreen)
        if current_screen_width > base_window_width or current_screen_height > base_window_height:
            # We're in a larger window, calculate scaling
            width_scale = current_screen_width / base_window_width
            height_scale = current_screen_height / base_window_height
            self.scale_factor = min(width_scale, height_scale, zoom_level) * 0.9  # Use 90% of available space

            # Calculate centered position with scroll offset
            offset_x = (current_screen_width - (base_window_width * self.scale_factor / zoom_level)) // 2 + scroll_x
            offset_y = (current_screen_height - (base_window_height * self.scale_factor / zoom_level)) // 2 + scroll_y
        else:
            # We're in a normal window, use zoom level directly
            if base_window_width <= current_screen_width and base_window_height <= current_screen_height:
                self.scale_factor = zoom_level
                offset_x = (current_screen_width - base_window_width) // 2 + scroll_x
                offset_y = (current_screen_height - base_window_height) // 2 + scroll_y
            else:
                # Need to fit in window
                width_scale = current_screen_width / base_window_width
                height_scale = (current_screen_height - 100) / (base_window_height - 100)
                self.scale_factor = min(width_scale, height_scale) * 0.9
                offset_x = (current_screen_width - (level.width * CELL_SIZE * self.scale_factor)) // 2 + scroll_x
                offset_y = (current_screen_height - (level.height * CELL_SIZE * self.scale_factor + 100)) // 2 + scroll_y

        # Clear the screen
        self.screen.fill(self.colors['background'])

        # Get assets from skin manager if available, otherwise use default
        if skin_manager:
            assets_to_use = skin_manager.get_skin()
            # Update tile size if different
            if skin_manager.get_current_tile_size() != CELL_SIZE:
                # Scale assets to match expected cell size
                scaled_assets = {}
                target_size = int(CELL_SIZE * self.scale_factor)
                for key, asset in assets_to_use.items():
                    scaled_assets[key] = pygame.transform.scale(asset, (target_size, target_size))
            else:
                # Scale assets if needed
                scaled_assets = {}
                if self.scale_factor != 1.0:
                    scaled_size = int(CELL_SIZE * self.scale_factor)
                    for key, asset in assets_to_use.items():
                        scaled_assets[key] = pygame.transform.scale(asset, (scaled_size, scaled_size))
                else:
                    scaled_assets = assets_to_use
        else:
            # Use default assets
            scaled_assets = {}
            if self.scale_factor != 1.0:
                scaled_size = int(CELL_SIZE * self.scale_factor)
                for key, asset in self.assets.items():
                    scaled_assets[key] = pygame.transform.scale(asset, (scaled_size, scaled_size))
            else:
                scaled_assets = self.assets

        # Render the level
        cell_size_scaled = int(CELL_SIZE * self.scale_factor)
        for y in range(level.height):
            for x in range(level.width):
                char = level.get_display_char(x, y)
                pos_x = offset_x + int(x * CELL_SIZE * self.scale_factor)
                pos_y = offset_y + int(y * CELL_SIZE * self.scale_factor)
                pos = (pos_x, pos_y)

                if char == WALL:
                    if WALL in scaled_assets:
                        self.screen.blit(scaled_assets[WALL], pos)
                elif char == PLAYER:
                    if FLOOR in scaled_assets:
                        self.screen.blit(scaled_assets[FLOOR], pos)
                    # Use directional player sprite if available
                    if skin_manager:
                        player_sprite = skin_manager.get_player_sprite()
                        if player_sprite:
                            # Scale the sprite if needed
                            if self.scale_factor != 1.0:
                                target_size = int(CELL_SIZE * self.scale_factor)
                                player_sprite = pygame.transform.scale(player_sprite, (target_size, target_size))
                            self.screen.blit(player_sprite, pos)
                    elif PLAYER in scaled_assets:
                        self.screen.blit(scaled_assets[PLAYER], pos)
                elif char == BOX:
                    if FLOOR in scaled_assets:
                        self.screen.blit(scaled_assets[FLOOR], pos)
                    if BOX in scaled_assets:
                        self.screen.blit(scaled_assets[BOX], pos)
                elif char == TARGET:
                    if FLOOR in scaled_assets:
                        self.screen.blit(scaled_assets[FLOOR], pos)
                    if TARGET in scaled_assets:
                        self.screen.blit(scaled_assets[TARGET], pos)
                elif char == PLAYER_ON_TARGET:
                    if FLOOR in scaled_assets:
                        self.screen.blit(scaled_assets[FLOOR], pos)
                    if PLAYER_ON_TARGET in scaled_assets:
                        self.screen.blit(scaled_assets[PLAYER_ON_TARGET], pos)
                elif char == BOX_ON_TARGET:
                    if FLOOR in scaled_assets:
                        self.screen.blit(scaled_assets[FLOOR], pos)
                    if BOX_ON_TARGET in scaled_assets:
                        self.screen.blit(scaled_assets[BOX_ON_TARGET], pos)
                else:  # FLOOR
                    if FLOOR in scaled_assets:
                        self.screen.blit(scaled_assets[FLOOR], pos)

        # Draw grid if enabled
        if show_grid and self.scale_factor >= 0.5:  # Only show grid when zoomed in enough
            grid_color = (100, 100, 100, 128)  # Semi-transparent gray

            # Vertical lines
            for x in range(level.width + 1):
                line_x = offset_x + int(x * CELL_SIZE * self.scale_factor)
                start_y = offset_y
                end_y = offset_y + int(level.height * CELL_SIZE * self.scale_factor)
                if 0 <= line_x <= current_screen_width:
                    pygame.draw.line(self.screen, grid_color[:3], (line_x, start_y), (line_x, end_y), 1)

            # Horizontal lines
            for y in range(level.height + 1):
                line_y = offset_y + int(y * CELL_SIZE * self.scale_factor)
                start_x = offset_x
                end_x = offset_x + int(level.width * CELL_SIZE * self.scale_factor)
                if 0 <= line_y <= current_screen_height:
                    pygame.draw.line(self.screen, grid_color[:3], (start_x, line_y), (end_x, line_y), 1)

        # Render game statistics
        stats_text = f"Moves: {level.moves}  Pushes: {level.pushes}"
        stats_font = pygame.font.Font(None, int(24 * max(1, self.scale_factor)))
        stats_surface = stats_font.render(stats_text, True, self.colors['black'])
        stats_pos = (offset_x + 10, offset_y + int(level.height * CELL_SIZE * self.scale_factor) + 10)
        self.screen.blit(stats_surface, stats_pos)

        # Render level information if level manager is provided
        if level_manager:
            level_info = f"Level {level_manager.get_current_level_number()} of {level_manager.get_level_count()}"
            level_surface = stats_font.render(level_info, True, self.colors['black'])
            level_rect = level_surface.get_rect()
            level_rect.right = current_screen_width - 10
            level_rect.top = offset_y + int(level.height * CELL_SIZE * self.scale_factor) + 10
            self.screen.blit(level_surface, level_rect)

            # Render collection information if available
            collection_info = level_manager.get_current_collection_info()
            if collection_info:
                collection_text = f"Collection: {collection_info['title']}"
                if collection_info['current_level_title']:
                    collection_text += f" - {collection_info['current_level_title']}"
                collection_surface = stats_font.render(collection_text, True, self.colors['blue'])
                collection_pos = (offset_x + 10, offset_y + int(level.height * CELL_SIZE * self.scale_factor) + 35)
                self.screen.blit(collection_surface, collection_pos)

                # Show collection progress
                progress_text = f"Level {collection_info['current_level_index']} of {collection_info['level_count']} in collection"
                progress_surface = stats_font.render(progress_text, True, self.colors['gray'])
                progress_rect = progress_surface.get_rect()
                progress_rect.right = current_screen_width - 10
                progress_rect.top = offset_y + int(level.height * CELL_SIZE * self.scale_factor) + 35
                self.screen.blit(progress_surface, progress_rect)

        # Render level metadata (title, description, author)
        metadata = level_manager.get_level_metadata() if level_manager else {}
        y_offset = offset_y + int(level.height * CELL_SIZE * self.scale_factor) + (60 if level_manager and level_manager.get_current_collection_info() else 35)

        if metadata.get('title') and metadata['title'] != '':
            title_text = f"Title: {metadata['title']}"
            title_surface = stats_font.render(title_text, True, self.colors['black'])
            title_pos = (offset_x + 10, y_offset)
            self.screen.blit(title_surface, title_pos)
            y_offset += 25

        if metadata.get('author') and metadata['author'] != '':
            author_text = f"Author: {metadata['author']}"
            author_surface = stats_font.render(author_text, True, self.colors['black'])
            author_pos = (offset_x + 10, y_offset)
            self.screen.blit(author_surface, author_pos)
            y_offset += 25

        if metadata.get('description') and metadata['description'] != '':
            # Handle long descriptions by wrapping text
            description = metadata['description']
            max_chars_per_line = 60  # Adjust based on screen width
            if len(description) > max_chars_per_line:
                # Simple word wrapping
                words = description.split(' ')
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + word) <= max_chars_per_line:
                        current_line += word + " "
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    lines.append(current_line.strip())

                for i, line in enumerate(lines[:2]):  # Show max 2 lines
                    desc_text = f"Description: {line}" if i == 0 else f"             {line}"
                    desc_surface = stats_font.render(desc_text, True, self.colors['black'])
                    desc_pos = (offset_x + 10, y_offset + i * 20)
                    self.screen.blit(desc_surface, desc_pos)
            else:
                desc_text = f"Description: {description}"
                desc_surface = stats_font.render(desc_text, True, self.colors['black'])
                desc_pos = (offset_x + 10, y_offset)
                self.screen.blit(desc_surface, desc_pos)

        # Render completion message if level is completed
        if level.is_completed():
            completion_text = "Level completed!"
            if level_manager and level_manager.has_next_level():
                completion_text += " Press 'n' for next level."

            # Create a semi-transparent overlay
            overlay = pygame.Surface((current_screen_width, current_screen_height))
            overlay.set_alpha(150)
            overlay.fill(self.colors['black'])
            self.screen.blit(overlay, (0, 0))

            # Render the completion message with scaled font
            completion_font = pygame.font.Font(None, int(36 * max(1, self.scale_factor)))
            completion_surface = completion_font.render(completion_text, True, self.colors['white'])
            completion_rect = completion_surface.get_rect(center=(current_screen_width // 2, current_screen_height // 2))
            self.screen.blit(completion_surface, completion_rect)

        # Update the display
        pygame.display.flip()

        return self.screen

    def render_welcome_screen(self, keybindings=None):
        """
        Render the welcome screen in the GUI.

        Args:
            keybindings (dict, optional): Dictionary of custom keybindings.
                                         Defaults to None (use hardcoded keys).

        Returns:
            pygame.Surface: The updated screen surface.
        """
        # Get current screen size
        current_screen_width, current_screen_height = self.screen.get_size()

        # Check if we need to adjust for fullscreen
        if current_screen_width > 800 or current_screen_height > 600:
            # We're in a larger window, calculate scaling
            self.scale_factor = min(current_screen_width / 800, current_screen_height / 600)
        else:
            # Set up a standard window size for the welcome screen
            window_width, window_height = 800, 600
            if (window_width, window_height) != self.window_size:
                self.window_size = (window_width, window_height)
                self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
            self.scale_factor = 1.0

        # Clear the screen
        self.screen.fill(self.colors['background'])

        # Render the title
        title_text = "SOKOBAN"
        title_font = pygame.font.Font(None, int(72 * self.scale_factor))
        title_surface = title_font.render(title_text, True, self.colors['blue'])
        title_rect = title_surface.get_rect(center=(current_screen_width // 2, current_screen_height // 4))
        self.screen.blit(title_surface, title_rect)

        # Render the subtitle
        subtitle_text = "A puzzle game where you push boxes to their targets!"
        subtitle_font = pygame.font.Font(None, int(24 * self.scale_factor))
        subtitle_surface = subtitle_font.render(subtitle_text, True, self.colors['black'])
        subtitle_rect = subtitle_surface.get_rect(center=(current_screen_width // 2, current_screen_height // 4 + int(50 * self.scale_factor)))
        self.screen.blit(subtitle_surface, subtitle_rect)

        # Prepare the instructions with current keybindings
        if keybindings:
            # Use custom keybindings
            up_key = keybindings.get('up', 'up').upper()
            down_key = keybindings.get('down', 'down').upper()
            left_key = keybindings.get('left', 'left').upper()
            right_key = keybindings.get('right', 'right').upper()
            reset_key = keybindings.get('reset', 'r').upper()
            undo_key = keybindings.get('undo', 'u').upper()
            next_key = keybindings.get('next', 'n').upper()
            prev_key = keybindings.get('previous', 'p').upper()
            solve_key = keybindings.get('solve', 's').upper()
            help_key = keybindings.get('help', 'h').upper()
            quit_key = keybindings.get('quit', 'q').upper()
            fullscreen_key = keybindings.get('fullscreen', 'f11').upper()
        else:
            # Use default keys
            up_key, down_key, left_key, right_key = "UP", "DOWN", "LEFT", "RIGHT"
            reset_key, undo_key, next_key, prev_key = "R", "U", "N", "P"
            solve_key, help_key, quit_key = "S", "H", "Q"
            fullscreen_key = "F11"

        # Render the instructions
        instructions = [
            "Controls:",
            f"Arrow Keys or {up_key}/{left_key}/{down_key}/{right_key}: Move the player",
            f"{reset_key}: Reset level",
            f"{undo_key}: Undo move",
            f"{next_key}: Next level",
            f"{prev_key}: Previous level",
            f"{solve_key}: AI takes control and solves level",
            f"{help_key}: Show help",
            f"{quit_key}: Quit game",
            f"{fullscreen_key}: Toggle fullscreen",
            "",
            "Press any key to start..."
        ]

        instruction_font = pygame.font.Font(None, int(24 * self.scale_factor))
        for i, line in enumerate(instructions):
            line_surface = instruction_font.render(line, True, self.colors['black'])
            line_rect = line_surface.get_rect(center=(current_screen_width // 2, current_screen_height // 2 + int(i * 30 * self.scale_factor)))
            self.screen.blit(line_surface, line_rect)

        # Update the display
        pygame.display.flip()

        return self.screen

    def render_game_over_screen(self, completed_all=False):
        """
        Render the game over screen in the GUI.

        Args:
            completed_all (bool, optional): Whether all levels were completed.
                                          Defaults to False.

        Returns:
            pygame.Surface: The updated screen surface.
        """
        # Get current screen size
        current_screen_width, current_screen_height = self.screen.get_size()

        # Check if we need to adjust for fullscreen
        if current_screen_width > 800 or current_screen_height > 600:
            # We're in a larger window, calculate scaling
            self.scale_factor = min(current_screen_width / 800, current_screen_height / 600)
        else:
            # Set up a standard window size for the game over screen
            window_width, window_height = 800, 600
            if (window_width, window_height) != self.window_size:
                self.window_size = (window_width, window_height)
                self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
            self.scale_factor = 1.0

        # Clear the screen
        self.screen.fill(self.colors['background'])

        # Render the title
        if completed_all:
            title_text = "CONGRATULATIONS!"
            message = "You have completed all levels! Well done!"
        else:
            title_text = "GAME OVER"
            message = "Thanks for playing Sokoban!"

        title_font = pygame.font.Font(None, int(72 * self.scale_factor))
        title_surface = title_font.render(title_text, True, self.colors['blue'])
        title_rect = title_surface.get_rect(center=(current_screen_width // 2, current_screen_height // 3))
        self.screen.blit(title_surface, title_rect)

        # Render the message
        message_font = pygame.font.Font(None, int(36 * self.scale_factor))
        message_surface = message_font.render(message, True, self.colors['black'])
        message_rect = message_surface.get_rect(center=(current_screen_width // 2, current_screen_height // 2))
        self.screen.blit(message_surface, message_rect)

        # Render the exit instruction
        exit_text = "Press any key to quit..."
        exit_font = pygame.font.Font(None, int(24 * self.scale_factor))
        exit_surface = exit_font.render(exit_text, True, self.colors['black'])
        exit_rect = exit_surface.get_rect(center=(current_screen_width // 2, current_screen_height * 2 // 3))
        self.screen.blit(exit_surface, exit_rect)

        # Update the display
        pygame.display.flip()

        return self.screen

    def render_help(self, keybindings=None):
        """
        Render the help information in the GUI.

        Args:
            keybindings (dict, optional): Dictionary of custom keybindings.
                                         Defaults to None (use hardcoded keys).

        Returns:
            pygame.Surface: The updated screen surface.
        """
        # Get current screen size
        current_screen_width, current_screen_height = self.screen.get_size()

        # Create a semi-transparent overlay
        overlay = pygame.Surface((current_screen_width, current_screen_height))
        overlay.set_alpha(200)
        overlay.fill(self.colors['black'])
        self.screen.blit(overlay, (0, 0))

        # Calculate scale factor for text
        self.scale_factor = min(current_screen_width / 800, current_screen_height / 600)

        # Render the title
        title_text = "HELP"
        title_font = pygame.font.Font(None, int(36 * self.scale_factor))
        title_surface = title_font.render(title_text, True, self.colors['white'])
        title_rect = title_surface.get_rect(center=(current_screen_width // 2, int(50 * self.scale_factor)))
        self.screen.blit(title_surface, title_rect)

        # Prepare the instructions with current keybindings
        if keybindings:
            # Use custom keybindings
            up_key = keybindings.get('up', 'up').upper()
            down_key = keybindings.get('down', 'down').upper()
            left_key = keybindings.get('left', 'left').upper()
            right_key = keybindings.get('right', 'right').upper()
            reset_key = keybindings.get('reset', 'r').upper()
            undo_key = keybindings.get('undo', 'u').upper()
            next_key = keybindings.get('next', 'n').upper()
            prev_key = keybindings.get('previous', 'p').upper()
            solve_key = keybindings.get('solve', 's').upper()
            help_key = keybindings.get('help', 'h').upper()
            quit_key = keybindings.get('quit', 'q').upper()
            fullscreen_key = keybindings.get('fullscreen', 'f11').upper()
            grid_key = keybindings.get('grid', 'g').upper()
        else:
            # Use default keys
            up_key, down_key, left_key, right_key = "UP", "DOWN", "LEFT", "RIGHT"
            reset_key, undo_key, next_key, prev_key = "R", "U", "N", "P"
            solve_key, help_key, quit_key = "S", "H", "Q"
            fullscreen_key, grid_key = "F11", "G"

        # Render the instructions
        instructions = [
            "Controls:",
            f"Arrow Keys or {up_key}/{left_key}/{down_key}/{right_key}: Move the player",
            f"{reset_key}: Reset level",
            f"{undo_key}: Undo move",
            f"{next_key}: Next level",
            f"{prev_key}: Previous level",
            f"{solve_key}: AI takes control and solves level",
            f"{help_key}: Show/hide help",
            f"{quit_key}: Quit game",
            f"{fullscreen_key}: Toggle fullscreen",
            f"{grid_key}: Toggle grid",
            "",
            "Game Rules:",
            "1. Push all boxes onto the target spots",
            "2. You can only push one box at a time",
            "3. You cannot pull boxes",
            "4. You cannot push a box if another box or a wall is behind it",
            "",
            "Press any key to continue..."
        ]

        help_font = pygame.font.Font(None, int(24 * self.scale_factor))
        for i, line in enumerate(instructions):
            line_surface = help_font.render(line, True, self.colors['white'])
            line_rect = line_surface.get_rect(center=(current_screen_width // 2, int(100 * self.scale_factor) + int(i * 25 * self.scale_factor)))
            self.screen.blit(line_surface, line_rect)

        # Update the display
        pygame.display.flip()

        return self.screen

    def cleanup(self):
        """
        Clean up resources used by the GUI renderer.
        """
        pygame.quit()
