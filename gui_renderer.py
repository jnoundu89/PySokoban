"""
GUI renderer module for the Sokoban game.

This module provides functionality for rendering the game with a graphical user interface
using Pygame.
"""

import os
import pygame
from constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE


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
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
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
    
    def render_level(self, level, level_manager=None):
        """
        Render the current level state in the GUI.
        
        Args:
            level: The Level object to render.
            level_manager: Optional LevelManager object for additional information.
            
        Returns:
            pygame.Surface: The updated screen surface.
        """
        # Get current screen size
        current_screen_width, current_screen_height = self.screen.get_size()
        
        # Calculate base window size needed for the level
        base_window_width = level.width * CELL_SIZE
        base_window_height = level.height * CELL_SIZE + 50  # Extra space for stats
        
        # Check if we're in a resized window (including fullscreen)
        if current_screen_width > base_window_width or current_screen_height > base_window_height:
            # We're in a larger window, calculate scaling
            width_scale = current_screen_width / base_window_width
            height_scale = current_screen_height / base_window_height
            self.scale_factor = min(width_scale, height_scale) * 0.9  # Use 90% of available space
            
            # Calculate centered position
            offset_x = (current_screen_width - (base_window_width * self.scale_factor)) // 2
            offset_y = (current_screen_height - (base_window_height * self.scale_factor)) // 2
        else:
            # We're in a normal window, use default size
            self.window_size = (base_window_width, base_window_height)
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
            self.scale_factor = 1.0
            offset_x = 0
            offset_y = 0
        
        # Clear the screen
        self.screen.fill(self.colors['background'])
        
        # Scale assets if needed
        scaled_assets = {}
        if self.scale_factor != 1.0:
            scaled_size = int(CELL_SIZE * self.scale_factor)
            for key, asset in self.assets.items():
                scaled_assets[key] = pygame.transform.scale(asset, (scaled_size, scaled_size))
        else:
            scaled_assets = self.assets
        
        # Render the level
        for y in range(level.height):
            for x in range(level.width):
                char = level.get_display_char(x, y)
                pos_x = offset_x + int(x * CELL_SIZE * self.scale_factor)
                pos_y = offset_y + int(y * CELL_SIZE * self.scale_factor)
                pos = (pos_x, pos_y)
                
                if char == WALL:
                    self.screen.blit(scaled_assets['wall'], pos)
                elif char == PLAYER:
                    self.screen.blit(scaled_assets['floor'], pos)
                    self.screen.blit(scaled_assets['player'], pos)
                elif char == BOX:
                    self.screen.blit(scaled_assets['floor'], pos)
                    self.screen.blit(scaled_assets['box'], pos)
                elif char == TARGET:
                    self.screen.blit(scaled_assets['floor'], pos)
                    self.screen.blit(scaled_assets['target'], pos)
                elif char == PLAYER_ON_TARGET:
                    self.screen.blit(scaled_assets['floor'], pos)
                    self.screen.blit(scaled_assets['player_on_target'], pos)
                elif char == BOX_ON_TARGET:
                    self.screen.blit(scaled_assets['floor'], pos)
                    self.screen.blit(scaled_assets['box_on_target'], pos)
                else:  # FLOOR
                    self.screen.blit(scaled_assets['floor'], pos)
        
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
    
    def render_welcome_screen(self):
        """
        Render the welcome screen in the GUI.
        
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
        
        # Render the instructions
        instructions = [
            "Controls:",
            "Arrow Keys or WASD: Move the player",
            "R: Reset level",
            "U: Undo move",
            "N: Next level",
            "P: Previous level",
            "H: Show help",
            "Q: Quit game",
            "F11: Toggle fullscreen",
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
    
    def render_help(self):
        """
        Render the help information in the GUI.
        
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
        
        # Render the instructions
        instructions = [
            "Controls:",
            "Arrow Keys or WASD: Move the player",
            "R: Reset level",
            "U: Undo move",
            "N: Next level",
            "P: Previous level",
            "H: Show/hide help",
            "Q: Quit game",
            "F11: Toggle fullscreen",
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