"""
Level Preview module for the Sokoban game.

This module provides a popup interface for previewing levels before playing them.
"""

import pygame
from src.core.level import Level
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET
from src.level_management.level_collection_parser import LevelCollectionParser

class LevelPreview:
    """
    Level preview popup for showing a miniature version of a level before playing.
    """

    def __init__(self, screen, screen_width, screen_height):
        """
        Initialize the level preview popup.

        Args:
            screen: Pygame surface to draw on
            screen_width (int): Width of the screen
            screen_height (int): Height of the screen
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Define colors
        self.colors = {
            'background': (240, 240, 240),
            'popup_bg': (255, 255, 255),
            'popup_border': (100, 100, 100),
            'text': (50, 50, 50),
            'title': (70, 70, 150),
            'play_button': (80, 150, 80),
            'play_button_hover': (100, 180, 100),
            'back_button': (200, 100, 100),
            'back_button_hover': (255, 130, 130),
            'button_text': (255, 255, 255),
            # Level preview colors
            'wall': (100, 50, 50),
            'floor': (220, 220, 220),
            'player': (100, 100, 255),
            'box': (139, 69, 19),
            'target': (255, 255, 0),
            'player_on_target': (150, 150, 255),
            'box_on_target': (255, 165, 0)
        }

        # State
        self.running = False
        self.selected_action = None  # 'play' or 'back'
        self.level = None
        self.level_info = None

        # Initialize UI elements
        self._update_ui_elements()

    def _update_ui_elements(self):
        """Update UI elements based on current screen size."""
        # Update font sizes based on screen dimensions
        title_size = min(max(32, self.screen_width // 20), 48)
        subtitle_size = min(max(24, self.screen_width // 30), 32)
        text_size = min(max(16, self.screen_width // 50), 24)
        button_size = min(max(24, self.screen_width // 40), 32)

        # Load fonts with responsive sizes
        self.title_font = pygame.font.Font(None, title_size)
        self.subtitle_font = pygame.font.Font(None, subtitle_size)
        self.text_font = pygame.font.Font(None, text_size)
        self.button_font = pygame.font.Font(None, button_size)

        # Calculate popup dimensions - responsive to screen size
        self.popup_width = min(800, self.screen_width - 100)
        self.popup_height = min(600, self.screen_height - 100)
        self.popup_x = (self.screen_width - self.popup_width) // 2
        self.popup_y = (self.screen_height - self.popup_height) // 2

        # Preview area dimensions
        self.preview_width = self.popup_width - 100
        self.preview_height = self.popup_height - 200
        self.preview_x = self.popup_x + 50
        self.preview_y = self.popup_y + 80

        # Button dimensions - responsive to screen size
        self.button_width = min(max(100, self.screen_width // 10), 120)
        self.button_height = min(max(40, self.screen_height // 20), 50)
        self.button_spacing = max(10, self.screen_width // 100)

        # Calculate button positions
        total_button_width = 2 * self.button_width + self.button_spacing
        button_start_x = self.popup_x + (self.popup_width - total_button_width) // 2
        button_y = self.popup_y + self.popup_height - 80

        self.play_button = Button(
            "Play", button_start_x, button_y, self.button_width, self.button_height,
            action=lambda: self._set_action('play'),
            color=self.colors['play_button'],
            hover_color=self.colors['play_button_hover'],
            text_color=self.colors['button_text'],
            font_size=button_size
        )

        self.back_button = Button(
            "Retour", button_start_x + self.button_width + self.button_spacing, 
            button_y, self.button_width, self.button_height,
            action=lambda: self._set_action('back'),
            color=self.colors['back_button'],
            hover_color=self.colors['back_button_hover'],
            text_color=self.colors['button_text'],
            font_size=button_size
        )

    def show_level_preview(self, level_info):
        """
        Show the level preview popup.

        Args:
            level_info: LevelInfo object containing level information

        Returns:
            str: 'play' if user wants to play, 'back' if user wants to go back
        """
        self.level_info = level_info
        self.running = True
        self.selected_action = None

        # Load the level
        try:
            if level_info.is_from_collection:
                collection = LevelCollectionParser.parse_file(level_info.collection_file)
                _, self.level = collection.get_level(level_info.level_index)
            else:
                self.level = Level(level_file=level_info.collection_file)
        except Exception as e:
            print(f"Error loading level: {e}")
            return 'back'

        clock = pygame.time.Clock()

        while self.running:
            # Handle events
            for event in pygame.event.get():
                event_handled = False

                if event.type == pygame.QUIT:
                    self.selected_action = 'back'
                    self.running = False
                    event_handled = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.selected_action = 'back'
                        self.running = False
                        event_handled = True
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.selected_action = 'play'
                        self.running = False
                        event_handled = True
                elif event.type == pygame.VIDEORESIZE:
                    # Update screen dimensions and UI elements
                    self.screen_width, self.screen_height = event.size
                    self._update_ui_elements()
                    event_handled = True
                elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left click
                        # First check if buttons handle the event
                        if self.play_button.handle_event(event) or self.back_button.handle_event(event):
                            event_handled = True
                        elif event.type == pygame.MOUSEBUTTONUP:
                            # Check if click release is outside popup to close (only on UP event)
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            if not (self.popup_x <= mouse_x <= self.popup_x + self.popup_width and
                                    self.popup_y <= mouse_y <= self.popup_y + self.popup_height):
                                self.selected_action = 'back'
                                self.running = False
                                event_handled = True

            # Render
            self._render()
            clock.tick(60)

        return self.selected_action or 'back'

    def _set_action(self, action):
        """Set the selected action and close the popup."""
        self.selected_action = action
        self.running = False

    def _render(self):
        """Render the level preview popup."""
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Draw popup background
        pygame.draw.rect(self.screen, self.colors['popup_bg'], 
                        (self.popup_x, self.popup_y, self.popup_width, self.popup_height), 0, 10)
        pygame.draw.rect(self.screen, self.colors['popup_border'], 
                        (self.popup_x, self.popup_y, self.popup_width, self.popup_height), 3, 10)

        # Draw title
        if self.level_info:
            title_text = f"Prévisualisation: {self.level_info.title}"
            title_surface = self.title_font.render(title_text, True, self.colors['title'])
            title_rect = title_surface.get_rect(center=(self.popup_x + self.popup_width // 2, self.popup_y + 30))
            self.screen.blit(title_surface, title_rect)

        # Draw level preview
        if self.level:
            self._render_level_preview()

        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        self.play_button.update(mouse_pos)
        self.play_button.draw(self.screen)
        self.back_button.update(mouse_pos)
        self.back_button.draw(self.screen)

        # Draw instructions
        instruction_text = "Cliquez Play pour jouer ou Retour pour revenir à la sélection"
        instruction_surface = self.text_font.render(instruction_text, True, self.colors['text'])
        instruction_rect = instruction_surface.get_rect(center=(self.popup_x + self.popup_width // 2, 
                                                              self.popup_y + self.popup_height - 30))
        self.screen.blit(instruction_surface, instruction_rect)

        pygame.display.flip()

    def _render_level_preview(self):
        """Render the miniature level preview."""
        if not self.level:
            return

        # Calculate cell size to fit the level in the preview area
        max_cell_width = self.preview_width // max(1, self.level.width)
        max_cell_height = self.preview_height // max(1, self.level.height)
        cell_size = min(max_cell_width, max_cell_height, 20)  # Max 20px per cell

        # Calculate actual preview dimensions
        actual_width = self.level.width * cell_size
        actual_height = self.level.height * cell_size

        # Center the preview
        preview_start_x = self.preview_x + (self.preview_width - actual_width) // 2
        preview_start_y = self.preview_y + (self.preview_height - actual_height) // 2

        # Draw border around preview
        border_margin = 5
        pygame.draw.rect(self.screen, self.colors['popup_border'], 
                        (preview_start_x - border_margin, preview_start_y - border_margin, 
                         actual_width + 2 * border_margin, actual_height + 2 * border_margin), 2)

        # Draw level cells
        for y in range(self.level.height):
            for x in range(self.level.width):
                cell_x = preview_start_x + x * cell_size
                cell_y = preview_start_y + y * cell_size

                # Get the display character for this position
                display_char = self.level.get_display_char(x, y)

                # Choose color based on the character
                color = self._get_cell_color(display_char)

                # Draw the cell
                pygame.draw.rect(self.screen, color, (cell_x, cell_y, cell_size, cell_size))

                # Draw grid lines for better visibility (only if cells are large enough)
                if cell_size > 8:
                    pygame.draw.rect(self.screen, (180, 180, 180), 
                                   (cell_x, cell_y, cell_size, cell_size), 1)

        # Draw level stats
        stats_y = preview_start_y + actual_height + 20
        stats_text = f"Taille: {self.level.width}x{self.level.height} | Boîtes: {len(self.level.boxes)} | Cibles: {len(self.level.targets)}"
        stats_surface = self.text_font.render(stats_text, True, self.colors['text'])
        stats_rect = stats_surface.get_rect(center=(self.preview_x + self.preview_width // 2, stats_y))
        self.screen.blit(stats_surface, stats_rect)

    def _get_cell_color(self, display_char):
        """
        Get the color for a display character.

        Args:
            display_char (str): The display character

        Returns:
            tuple: RGB color tuple
        """
        if display_char == WALL:
            return self.colors['wall']
        elif display_char == FLOOR:
            return self.colors['floor']
        elif display_char == PLAYER:
            return self.colors['player']
        elif display_char == BOX:
            return self.colors['box']
        elif display_char == TARGET:
            return self.colors['target']
        elif display_char == PLAYER_ON_TARGET:
            return self.colors['player_on_target']
        elif display_char == BOX_ON_TARGET:
            return self.colors['box_on_target']
        else:
            return self.colors['floor']  # Default


class Button:
    """A clickable button for the level preview."""

    def __init__(self, text, x, y, width, height, action=None, color=(100, 100, 200),
                 hover_color=(130, 130, 255), text_color=(255, 255, 255), font_size=32):
        """Initialize a button."""
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = self.color
        self.font = pygame.font.Font(None, font_size)
        self.is_pressed = False  # Track if button is being pressed

    def draw(self, screen):
        """Draw the button on the screen."""
        pygame.draw.rect(screen, self.current_color, (self.x, self.y, self.width, self.height), 0, 10)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        """Check if the mouse is hovering over the button."""
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

    def update(self, mouse_pos):
        """Update the button's appearance based on mouse position."""
        if self.is_hovered(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

    def handle_event(self, event):
        """Handle mouse events for the button."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered(pygame.mouse.get_pos()):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.is_hovered(pygame.mouse.get_pos()):
                self.is_pressed = False
                if self.action:
                    self.action()
                return True
            self.is_pressed = False
        return False
