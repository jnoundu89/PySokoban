"""
Menu System for the Sokoban game.

This module provides a central hub for players to navigate between different parts of the game,
including playing levels, editing levels, changing settings, and more.
"""

import os
import sys
import pygame
from src.core.constants import TITLE, CELL_SIZE
from src.level_management.level_selector import LevelSelector

# Forward declaration to avoid circular import
# This will be used in the _run_loop method to find the EnhancedSokoban instance
EnhancedSokoban = None
try:
    from src.core.game import EnhancedSokoban
except ImportError:
    pass  # Will be resolved at runtime

class Button:
    """
    A clickable button for the menu system.
    """

    def __init__(self, text, x, y, width, height, action=None, color=(100, 100, 200), hover_color=(130, 130, 255), text_color=(255, 255, 255), font_size=None):
        """
        Initialize a button.

        Args:
            text (str): The text to display on the button.
            x (int): X position of the button.
            y (int): Y position of the button.
            width (int): Width of the button.
            height (int): Height of the button.
            action: Function to call when the button is clicked.
            color: RGB color tuple for the button.
            hover_color: RGB color tuple for the button when hovered.
            text_color: RGB color tuple for the button text.
            font_size: Optional specific font size. If None, calculated based on button height.
        """
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

        # Responsive font size based on button height
        if font_size is None:
            # Calculate font size based on button dimensions
            # Ensure text fits well within the button
            font_size = min(max(16, height // 2), min(36, width // (len(text) // 2 + 1)))

        self.font = pygame.font.Font(None, font_size)

    def draw(self, screen):
        """
        Draw the button on the screen.

        Args:
            screen: Pygame surface to draw on.
        """
        # Draw button rectangle
        pygame.draw.rect(screen, self.current_color, (self.x, self.y, self.width, self.height), 0, 10)

        # Draw button text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        """
        Check if the mouse is hovering over the button.

        Args:
            pos: (x, y) tuple of mouse position.

        Returns:
            bool: True if the mouse is hovering over the button, False otherwise.
        """
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

    def update(self, mouse_pos):
        """
        Update the button's appearance based on mouse position.

        Args:
            mouse_pos: (x, y) tuple of mouse position.
        """
        if self.is_hovered(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

    def handle_event(self, event):
        """
        Handle mouse events for the button.

        Args:
            event: Pygame event to handle.

        Returns:
            bool: True if the button was clicked, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered(pygame.mouse.get_pos()):
                if self.action:
                    self.action()
                return True
        return False

class ToggleButton(Button):
    """
    A toggle button that can be switched between two states.
    """

    def __init__(self, text_on, text_off, x, y, width, height, is_on=False, action=None, 
                 color_on=(100, 180, 100), color_off=(180, 100, 100), 
                 hover_color_on=(120, 220, 120), hover_color_off=(220, 120, 120),
                 text_color=(255, 255, 255), font_size=None):
        """
        Initialize a toggle button.

        Args:
            text_on (str): The text to display when the button is in the 'on' state.
            text_off (str): The text to display when the button is in the 'off' state.
            x (int): X position of the button.
            y (int): Y position of the button.
            width (int): Width of the button.
            height (int): Height of the button.
            is_on (bool): Whether the button starts in the 'on' state.
            action: Function to call when the button is toggled.
            color_on: RGB color tuple for the button when 'on'.
            color_off: RGB color tuple for the button when 'off'.
            hover_color_on: RGB color tuple for the button when 'on' and hovered.
            hover_color_off: RGB color tuple for the button when 'off' and hovered.
            text_color: RGB color tuple for the button text.
            font_size: Optional specific font size. If None, calculated based on button height.
        """
        self.text_on = text_on
        self.text_off = text_off
        self.is_on = is_on
        self.color_on = color_on
        self.color_off = color_off
        self.hover_color_on = hover_color_on
        self.hover_color_off = hover_color_off

        # Initialize with the current state
        current_text = text_on if is_on else text_off
        current_color = color_on if is_on else color_off
        current_hover_color = hover_color_on if is_on else hover_color_off

        super().__init__(current_text, x, y, width, height, action, 
                         current_color, current_hover_color, text_color, font_size)

    def toggle(self):
        """Toggle the button state."""
        self.is_on = not self.is_on
        self.text = self.text_on if self.is_on else self.text_off
        self.color = self.color_on if self.is_on else self.color_off
        self.hover_color = self.hover_color_on if self.is_on else self.hover_color_off
        self.current_color = self.color

        # Call the action with the new state
        if self.action:
            self.action(self.is_on)

    def handle_event(self, event):
        """
        Handle mouse events for the toggle button.

        Args:
            event: Pygame event to handle.

        Returns:
            bool: True if the button was clicked, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered(pygame.mouse.get_pos()):
                self.toggle()
                return True
        return False

class Slider:
    """
    A slider component for adjusting numerical values.
    """

    def __init__(self, x, y, width, height, min_value, max_value, current_value, label="",
                 color=(100, 100, 200), handle_color=(255, 255, 255), text_color=(255, 255, 255)):
        """
        Initialize a slider.

        Args:
            x (int): X position of the slider.
            y (int): Y position of the slider.
            width (int): Width of the slider.
            height (int): Height of the slider.
            min_value (float): Minimum value.
            max_value (float): Maximum value.
            current_value (float): Current value.
            label (str): Label text for the slider.
            color: RGB color tuple for the slider track.
            handle_color: RGB color tuple for the slider handle.
            text_color: RGB color tuple for the text.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.label = label
        self.color = color
        self.handle_color = handle_color
        self.text_color = text_color
        self.dragging = False

        # Calculate handle properties
        self.handle_width = 20
        self.handle_height = height + 4
        self.track_height = height // 3

        # Font for text
        font_size = min(max(14, height), 24)
        self.font = pygame.font.Font(None, font_size)

    def get_handle_x(self):
        """Get the X position of the handle based on current value."""
        ratio = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        return self.x + ratio * (self.width - self.handle_width)

    def draw(self, screen):
        """
        Draw the slider on the screen.

        Args:
            screen: Pygame surface to draw on.
        """
        # Draw label
        if self.label:
            label_surface = self.font.render(self.label, True, self.text_color)
            screen.blit(label_surface, (self.x, self.y - 25))

        # Draw track
        track_y = self.y + (self.height - self.track_height) // 2
        pygame.draw.rect(screen, self.color,
                        (self.x, track_y, self.width, self.track_height), 0, 5)

        # Draw handle
        handle_x = self.get_handle_x()
        handle_y = self.y - 2
        pygame.draw.rect(screen, self.handle_color,
                        (handle_x, handle_y, self.handle_width, self.handle_height), 0, 8)

        # Draw current value
        value_text = f"{int(self.current_value)}"
        value_surface = self.font.render(value_text, True, self.text_color)
        value_rect = value_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height + 20))
        screen.blit(value_surface, value_rect)

    def handle_event(self, event):
        """
        Handle mouse events for the slider.

        Args:
            event: Pygame event to handle.

        Returns:
            bool: True if the value changed, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            handle_x = self.get_handle_x()

            # Check if clicking on handle
            if (handle_x <= mouse_x <= handle_x + self.handle_width and
                self.y - 2 <= mouse_y <= self.y + self.handle_height - 2):
                self.dragging = True
                return False

            # Check if clicking on track
            elif (self.x <= mouse_x <= self.x + self.width and
                  self.y <= mouse_y <= self.y + self.height):
                # Set value based on click position
                ratio = (mouse_x - self.x) / self.width
                old_value = self.current_value
                self.current_value = self.min_value + ratio * (self.max_value - self.min_value)
                self.current_value = max(self.min_value, min(self.max_value, self.current_value))
                return old_value != self.current_value

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            ratio = (mouse_x - self.x) / self.width
            old_value = self.current_value
            self.current_value = self.min_value + ratio * (self.max_value - self.min_value)
            self.current_value = max(self.min_value, min(self.max_value, self.current_value))
            return old_value != self.current_value

        return False

class TextInput:
    """
    A text input component for entering numerical values.
    """

    def __init__(self, x, y, width, height, min_value, max_value, current_value, label="",
                 color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)):
        """
        Initialize a text input field.

        Args:
            x (int): X position of the text input.
            y (int): Y position of the text input.
            width (int): Width of the text input.
            height (int): Height of the text input.
            min_value (int): Minimum allowed value.
            max_value (int): Maximum allowed value.
            current_value (int): Current value.
            label (str): Label text for the text input.
            color: RGB color tuple for the border.
            text_color: RGB color tuple for the text.
            bg_color: RGB color tuple for the background.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.label = label
        self.color = color
        self.text_color = text_color
        self.bg_color = bg_color
        self.active = False
        self.text = str(current_value)

        # Font for text
        font_size = min(max(14, height - 4), 24)
        self.font = pygame.font.Font(None, font_size)

        # Cursor properties
        self.cursor_visible = True
        self.cursor_blink_time = 500  # milliseconds
        self.last_blink_time = pygame.time.get_ticks()

    def draw(self, screen):
        """
        Draw the text input on the screen.

        Args:
            screen: Pygame surface to draw on.
        """
        # Draw label
        if self.label:
            label_surface = self.font.render(self.label, True, self.text_color)
            screen.blit(label_surface, (self.x, self.y - 25))

        # Draw text input box
        border_color = (150, 150, 255) if self.active else self.color
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height), 0, 5)
        pygame.draw.rect(screen, border_color, (self.x, self.y, self.width, self.height), 2, 5)

        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

        # Draw cursor if active
        if self.active:
            # Blink cursor
            current_time = pygame.time.get_ticks()
            if current_time - self.last_blink_time > self.cursor_blink_time:
                self.cursor_visible = not self.cursor_visible
                self.last_blink_time = current_time

            if self.cursor_visible:
                text_width = text_surface.get_width()
                cursor_x = text_rect.right + 2
                if cursor_x > self.x + self.width - 5:
                    cursor_x = self.x + self.width - 5
                pygame.draw.line(screen, self.text_color, 
                                (cursor_x, self.y + 5), 
                                (cursor_x, self.y + self.height - 5), 2)

        # Draw min/max values below
        range_text = f"Range: {self.min_value}-{self.max_value}"
        range_surface = pygame.font.Font(None, 18).render(range_text, True, (100, 100, 100))
        range_rect = range_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height + 15))
        screen.blit(range_surface, range_rect)

    def handle_event(self, event):
        """
        Handle events for the text input.

        Args:
            event: Pygame event to handle.

        Returns:
            bool: True if the value changed and is valid, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicking on the text input
            if (self.x <= event.pos[0] <= self.x + self.width and
                self.y <= event.pos[1] <= self.y + self.height):
                self.active = True
                return False
            else:
                # If clicking outside and active, validate and update value
                if self.active:
                    self.active = False
                    return self._validate_and_update()

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self.active = False
                return self._validate_and_update()
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.active = False
                self.text = str(self.current_value)  # Reset to original value
            else:
                # Only allow digits
                if event.unicode.isdigit():
                    self.text += event.unicode

        return False

    def _validate_and_update(self):
        """
        Validate the entered text and update the current value if valid.

        Returns:
            bool: True if the value changed and is valid, False otherwise.
        """
        if not self.text:
            self.text = str(self.current_value)
            return False

        try:
            new_value = int(self.text)
            if self.min_value <= new_value <= self.max_value:
                old_value = self.current_value
                self.current_value = new_value
                return old_value != new_value
            else:
                # Value out of range, reset to current value
                self.text = str(self.current_value)
        except ValueError:
            # Not a valid number, reset to current value
            self.text = str(self.current_value)

        return False

class MenuSystem:
    """
    Main menu system for the Sokoban game.

    This class manages the different menu screens and transitions between them.
    """

    def __init__(self, screen=None, screen_width=800, screen_height=600, levels_dir='levels', skin_manager=None):
        """
        Initialize the menu system.

        Args:
            screen: Pygame surface to draw on (optional, will create if None).
            screen_width (int): Width of the screen.
            screen_height (int): Height of the screen.
            levels_dir (str): Directory containing level files.
            skin_manager: Shared skin manager instance.
        """
        # pygame.init() # Should be initialized by the main game
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.levels_dir = levels_dir
        self.skin_manager = skin_manager

        # Initialize config manager
        from src.core.config_manager import get_config_manager
        self.config_manager = get_config_manager()

        # Keyboard layout toggle button
        self.keyboard_layout_toggle = None

        if screen is None:
            # Standalone mode - create our own screen
            pygame.init()
            self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            pygame.display.set_caption(f"{TITLE} - Menu")
        else:
            # Integrated mode - use provided screen
            self.screen = screen

        # Define colors
        self.colors = {
            'background': (240, 240, 240),
            'text': (50, 50, 50),
            'button': (100, 100, 200),
            'button_hover': (130, 130, 255),
            'button_text': (255, 255, 255),
            'title': (70, 70, 150)
        }

        # Load fonts (will be updated in _update_fonts)
        self.title_font = None
        self.subtitle_font = None
        self.text_font = None
        self._update_fonts()

        # Menu states
        self.states = {
            'main': self._main_menu,
            'play': self._play_menu,
            'editor': self._editor_menu,
            'settings': self._settings_menu,
            'skins': self._skins_menu,
            'credits': self._credits_menu,
            'start_game': self._start_game_state
        }
        self.current_state = 'main'
        self.running = False

        # Level selector
        self.level_selector = None
        self.selected_level_path = None
        self.selected_level_info = None

        # Create buttons for all menu states
        self.main_menu_buttons = []
        self.play_menu_buttons = []
        self.editor_menu_buttons = []
        self.settings_menu_buttons = []
        self.skins_menu_buttons = []
        self.credits_menu_buttons = []

        # Create input field for movement cooldown
        self.movement_cooldown_input = None

        # Background surface for dialogs
        self.background_surface = None

        self._recreate_all_buttons()

    def _update_fonts(self):
        """Update fonts based on screen size."""
        # Responsive font sizing based on both width and height
        # This ensures better scaling for different aspect ratios
        base_dimension = min(self.screen_width, self.screen_height)

        # Scale font sizes based on screen dimensions
        title_size = min(max(32, base_dimension // 15), 80)
        subtitle_size = min(max(24, base_dimension // 25), 48)
        text_size = min(max(16, base_dimension // 40), 32)

        # Create fonts with the calculated sizes
        self.title_font = pygame.font.Font(None, title_size)
        self.subtitle_font = pygame.font.Font(None, subtitle_size)
        self.text_font = pygame.font.Font(None, text_size)

        # Print font sizes for debugging
        print(f"Updated fonts - Title: {title_size}, Subtitle: {subtitle_size}, Text: {text_size}")

    def _recreate_all_buttons(self):
        """Recreate all buttons, typically after a resize."""
        self._update_fonts()
        self._create_main_menu_buttons()
        self._create_play_menu_buttons()
        self._create_editor_menu_buttons()
        self._create_settings_menu_buttons()
        self._create_skins_menu_buttons()
        self._create_credits_menu_buttons()

    def _create_main_menu_buttons(self):
        """Create buttons for the main menu."""
        # Responsive button sizing based on screen size and resolution
        # For higher resolutions, use larger buttons
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # For high resolution screens (e.g., 1920x1080)
            button_width = min(max(300, self.screen_width // 5), 400)
            button_height = min(max(60, self.screen_height // 15), 80)
            title_offset = 180  # More space below title for high-res
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            # For medium resolution screens (e.g., 1200x800)
            button_width = min(max(250, self.screen_width // 5.5), 350)
            button_height = min(max(50, self.screen_height // 18), 70)
            title_offset = 160  # Space below title for medium-res
        else:
            # For smaller screens
            button_width = min(max(200, self.screen_width // 6), 300)
            button_height = min(max(40, self.screen_height // 20), 60)
            title_offset = 150  # Default space below title

        # Calculate button positions
        button_x = (self.screen_width - button_width) // 2

        # Calculate total menu height and center it vertically
        num_buttons = 6
        button_spacing = button_height + max(15, self.screen_height // 40)  # Responsive spacing
        total_menu_height = num_buttons * button_height + (num_buttons - 1) * button_spacing

        # Start buttons at a position that centers the entire menu block
        button_y_start = (self.screen_height - total_menu_height) // 2

        # Ensure buttons start below the title
        if button_y_start < title_offset:
            button_y_start = title_offset

        # Calculate font size based on button dimensions
        button_font_size = min(max(24, button_height // 2), 42)

        # Create buttons with consistent styling
        self.main_menu_buttons = [
            Button("Play Game", button_x, button_y_start, button_width, button_height,
                   action=None, font_size=button_font_size),  # Action will be set by EnhancedSokoban
            Button("Level Editor", button_x, button_y_start + button_spacing, button_width, button_height,
                   action=None, font_size=button_font_size),  # Action will be set by EnhancedSokoban
            Button("Settings", button_x, button_y_start + button_spacing * 2, button_width, button_height,
                   action=lambda: self._change_state('settings'), font_size=button_font_size),
            Button("Skins", button_x, button_y_start + button_spacing * 3, button_width, button_height,
                   action=None, font_size=button_font_size),  # Action will be set by EnhancedSokoban
            Button("Credits", button_x, button_y_start + button_spacing * 4, button_width, button_height,
                   action=lambda: self._change_state('credits'), font_size=button_font_size),
            Button("Exit", button_x, button_y_start + button_spacing * 5, button_width, button_height,
                   action=self._exit_game, color=(200, 100, 100), hover_color=(255, 130, 130), 
                   font_size=button_font_size)
        ]

        # Print debug info
        print(f"Created main menu buttons - Width: {button_width}, Height: {button_height}, Font: {button_font_size}")

    def _create_play_menu_buttons(self):
        """Create buttons for the play menu."""
        # Responsive button sizing based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            button_width = min(max(120, self.screen_width // 10), 180)
            button_height = min(max(50, self.screen_height // 20), 70)
            margin = max(25, self.screen_width // 50)
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            button_width = min(max(100, self.screen_width // 11), 150)
            button_height = min(max(40, self.screen_height // 22), 60)
            margin = max(20, self.screen_width // 55)
        else:
            button_width = min(max(80, self.screen_width // 12), 120)
            button_height = min(max(30, self.screen_height // 25), 50)
            margin = max(15, self.screen_width // 60)

        # Calculate font size based on button dimensions
        button_font_size = min(max(18, button_height // 2), 36)

        self.play_menu_buttons = [
            Button("Back", margin, self.screen_height - button_height - margin, 
                   button_width, button_height, 
                   action=lambda: self._change_state('main'),
                   font_size=button_font_size)
        ]

    def _create_editor_menu_buttons(self):
        """Create buttons for the editor menu."""
        # Responsive button sizing based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            button_width = min(max(120, self.screen_width // 10), 180)
            button_height = min(max(50, self.screen_height // 20), 70)
            margin = max(25, self.screen_width // 50)
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            button_width = min(max(100, self.screen_width // 11), 150)
            button_height = min(max(40, self.screen_height // 22), 60)
            margin = max(20, self.screen_width // 55)
        else:
            button_width = min(max(80, self.screen_width // 12), 120)
            button_height = min(max(30, self.screen_height // 25), 50)
            margin = max(15, self.screen_width // 60)

        # Calculate font size based on button dimensions
        button_font_size = min(max(18, button_height // 2), 36)

        self.editor_menu_buttons = [
            Button("Back", margin, self.screen_height - button_height - margin, 
                   button_width, button_height, 
                   action=lambda: self._change_state('main'),
                   font_size=button_font_size)
        ]

    def _create_settings_menu_buttons(self):
        """Create buttons for the settings menu."""
        # Responsive button sizing based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            button_width = min(max(120, self.screen_width // 10), 180)
            button_height = min(max(50, self.screen_height // 20), 70)
            margin = max(25, self.screen_width // 50)
            input_width = min(max(200, self.screen_width // 5), 300)
            input_height = 40
            input_y = self.screen_height // 2
            keybind_button_width = min(max(250, self.screen_width // 6), 350)
            section2_y = 350
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            button_width = min(max(100, self.screen_width // 11), 150)
            button_height = min(max(40, self.screen_height // 22), 60)
            margin = max(20, self.screen_width // 55)
            input_width = min(max(180, self.screen_width // 6), 250)
            input_height = 35
            input_y = self.screen_height // 2
            keybind_button_width = min(max(200, self.screen_width // 7), 300)
            section2_y = 320
        else:
            button_width = min(max(80, self.screen_width // 12), 120)
            button_height = min(max(30, self.screen_height // 25), 50)
            margin = max(15, self.screen_width // 60)
            input_width = min(max(150, self.screen_width // 7), 200)
            input_height = 30
            input_y = 300
            keybind_button_width = min(max(150, self.screen_width // 8), 250)
            section2_y = 300

        # Calculate font size based on button dimensions
        button_font_size = min(max(18, button_height // 2), 36)

        # Create main settings buttons
        self.settings_menu_buttons = [
            Button("Back", margin, self.screen_height - button_height - margin, 
                   button_width, button_height, 
                   action=lambda: self._change_state('main'),
                   font_size=button_font_size),
            Button("Keyboard Settings", (self.screen_width - keybind_button_width) // 2, 
                   self.screen_height - button_height * 2 - margin * 2,
                   keybind_button_width, button_height,
                   action=self._show_keybinding_dialog,
                   font_size=button_font_size)
        ]

        # Create movement cooldown text input
        input_x = (self.screen_width - input_width) // 2

        current_cooldown = self.config_manager.get('game', 'movement_cooldown', 200)
        self.movement_cooldown_input = TextInput(
            input_x, input_y, input_width, input_height,
            min_value=50, max_value=500, current_value=current_cooldown,
            label="Movement Cooldown (ms)",
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        # Create keyboard layout toggle button
        current_layout = self.config_manager.get('game', 'keyboard_layout', 'qwerty')
        is_azerty = current_layout.lower() == 'azerty'

        toggle_width = min(max(200, self.screen_width // 7), 300)
        toggle_height = button_height
        toggle_x = (self.screen_width - toggle_width) // 2
        toggle_y = section2_y + 150  # Position below movement cooldown

        self.keyboard_layout_toggle = ToggleButton(
            "AZERTY", "QWERTY", toggle_x, toggle_y, toggle_width, toggle_height,
            is_on=is_azerty, action=self._toggle_keyboard_layout,
            color_on=(100, 180, 100), color_off=(100, 100, 180),
            hover_color_on=(120, 220, 120), hover_color_off=(120, 120, 220),
            font_size=button_font_size
        )

    def _create_skins_menu_buttons(self):
        """Create buttons for the skins menu."""
        # Responsive button sizing based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            button_width = min(max(120, self.screen_width // 10), 180)
            button_height = min(max(50, self.screen_height // 20), 70)
            margin = max(25, self.screen_width // 50)
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            button_width = min(max(100, self.screen_width // 11), 150)
            button_height = min(max(40, self.screen_height // 22), 60)
            margin = max(20, self.screen_width // 55)
        else:
            button_width = min(max(80, self.screen_width // 12), 120)
            button_height = min(max(30, self.screen_height // 25), 50)
            margin = max(15, self.screen_width // 60)

        # Calculate font size based on button dimensions
        button_font_size = min(max(18, button_height // 2), 36)

        self.skins_menu_buttons = [
            Button("Back", margin, self.screen_height - button_height - margin, 
                   button_width, button_height, 
                   action=lambda: self._change_state('main'),
                   font_size=button_font_size)
        ]

    def _create_credits_menu_buttons(self):
        """Create buttons for the credits menu."""
        # Responsive button sizing based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            button_width = min(max(120, self.screen_width // 10), 180)
            button_height = min(max(50, self.screen_height // 20), 70)
            margin = max(25, self.screen_width // 50)
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            button_width = min(max(100, self.screen_width // 11), 150)
            button_height = min(max(40, self.screen_height // 22), 60)
            margin = max(20, self.screen_width // 55)
        else:
            button_width = min(max(80, self.screen_width // 12), 120)
            button_height = min(max(30, self.screen_height // 25), 50)
            margin = max(15, self.screen_width // 60)

        # Calculate font size based on button dimensions
        button_font_size = min(max(18, button_height // 2), 36)

        self.credits_menu_buttons = [
            Button("Back", margin, self.screen_height - button_height - margin, 
                   button_width, button_height, 
                   action=lambda: self._change_state('main'),
                   font_size=button_font_size)
        ]

    def _change_state(self, new_state):
        """
        Change the current menu state.

        Args:
            new_state (str): The new state to change to.
        """
        if new_state in self.states:
            self.current_state = new_state

    def _exit_game(self):
        """Exit the game."""
        self.running = False

    def start(self):
        """Start the menu system."""
        self.running = True
        self._run_loop()

    def _run_loop(self):
        """Run the main menu loop."""
        clock = pygame.time.Clock()

        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size
                    # Screen is resized by the main game, MenuSystem just needs to know
                    # self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                    self._recreate_all_buttons()  # Recreate buttons for new size
                elif event.type == pygame.KEYDOWN:
                    # Check for ESC to return to main menu if not already there
                    if event.key == pygame.K_ESCAPE and self.current_state != 'main':
                        self._change_state('main')

                # Handle button events based on current state
                active_buttons = []
                if self.current_state == 'main':
                    active_buttons = self.main_menu_buttons
                elif self.current_state == 'play':
                    active_buttons = self.play_menu_buttons
                elif self.current_state == 'editor':
                    active_buttons = self.editor_menu_buttons
                elif self.current_state == 'settings':
                    active_buttons = self.settings_menu_buttons
                elif self.current_state == 'skins':
                    active_buttons = self.skins_menu_buttons
                elif self.current_state == 'credits':
                    active_buttons = self.credits_menu_buttons

                for button in active_buttons:
                    button.handle_event(event)

                # Handle text input events in settings menu
                if self.current_state == 'settings':
                    if self.movement_cooldown_input and self.movement_cooldown_input.handle_event(event):
                        # Input value changed, update config
                        new_value = int(self.movement_cooldown_input.current_value)
                        self.config_manager.set('game', 'movement_cooldown', new_value, save=True)

                    # Handle keyboard layout toggle button events
                    if self.keyboard_layout_toggle:
                        self.keyboard_layout_toggle.handle_event(event)

            # Update current state
            self.states[self.current_state]()

            # Cap the frame rate
            clock.tick(60)

    def _main_menu(self):
        """Display the main menu."""
        # Clear the screen
        self.screen.fill(self.colors['background'])

        # Calculate responsive title position based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            title_y = 120
            subtitle_y = 200
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            title_y = 110
            subtitle_y = 180
        else:
            title_y = 100
            subtitle_y = 150

        # Draw title with shadow effect for better visibility
        title_text = "SOKOBAN"

        # Draw shadow
        shadow_color = (50, 50, 100)
        shadow_offset = 2
        title_shadow = self.title_font.render(title_text, True, shadow_color)
        shadow_rect = title_shadow.get_rect(center=(self.screen_width // 2 + shadow_offset, title_y + shadow_offset))
        self.screen.blit(title_shadow, shadow_rect)

        # Draw main title
        title_surface = self.title_font.render(title_text, True, self.colors['title'])
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        self.screen.blit(title_surface, title_rect)

        # Draw subtitle
        subtitle_surface = self.subtitle_font.render("Main Menu", True, self.colors['text'])
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width // 2, subtitle_y))
        self.screen.blit(subtitle_surface, subtitle_rect)

        # Update and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.main_menu_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)

        # Draw fullscreen instruction at the bottom of the screen
        instruction_text = "Press F11 to toggle fullscreen mode"
        instruction_surface = self.text_font.render(instruction_text, True, self.colors['text'])
        instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
        self.screen.blit(instruction_surface, instruction_rect)

        # Draw version info in the bottom-right corner
        version_text = "v1.0"
        version_surface = pygame.font.Font(None, 20).render(version_text, True, (100, 100, 100))
        version_rect = version_surface.get_rect(bottomright=(self.screen_width - 10, self.screen_height - 10))
        self.screen.blit(version_surface, version_rect)

        # Update the display
        pygame.display.flip()

    def _play_menu(self):
        """Display the play menu (level selection)."""
        # Create level selector if it doesn't exist
        if self.level_selector is None:
            self.level_selector = LevelSelector(
                self.screen, self.screen_width, self.screen_height, self.levels_dir
            )

        # Start the level selector
        selected_level = self.level_selector.start()

        if selected_level:
            # A level was selected, store it and signal to start the game
            self.selected_level_info = selected_level
            self.current_state = 'start_game'
        else:
            # No level selected (user went back), return to main menu
            self.current_state = 'main'

    def _editor_menu(self):
        """Display the editor menu."""
        self.screen.fill(self.colors['background'])

        # Draw title
        title_surface = self.title_font.render("Level Editor", True, self.colors['title'])
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Draw placeholder text
        placeholder_text = self.text_font.render("Level editor interface will be here.", True, self.colors['text'])
        placeholder_rect = placeholder_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(placeholder_text, placeholder_rect)

        # Update and draw buttons for this state
        mouse_pos = pygame.mouse.get_pos()
        for button in self.editor_menu_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)

        pygame.display.flip()

    def _toggle_keyboard_layout(self, is_azerty):
        """
        Toggle between QWERTY and AZERTY keyboard layouts.

        Args:
            is_azerty (bool): True if AZERTY layout is selected, False for QWERTY.
        """
        layout = 'azerty' if is_azerty else 'qwerty'
        self.config_manager.set('game', 'keyboard_layout', layout, save=False)

        # Get current keybindings
        keybindings = self.config_manager.get_keybindings()

        # Check if movement keys are set to default values for the previous layout
        # If they are, update them to the default values for the new layout
        from src.core.constants import KEY_BINDINGS, QWERTY, AZERTY

        old_layout = AZERTY if layout == QWERTY else QWERTY

        # For each movement direction, check if it's using a default key from the old layout
        # If so, update it to the default key for the new layout
        movement_keys = ['up', 'down', 'left', 'right']
        for direction in movement_keys:
            # Get the default key for this direction in the old layout
            old_default_key = None
            for key, action in KEY_BINDINGS[old_layout].items():
                if action == direction and key not in ['up', 'down', 'left', 'right']:
                    old_default_key = key
                    break

            # Get the default key for this direction in the new layout
            new_default_key = None
            for key, action in KEY_BINDINGS[layout].items():
                if action == direction and key not in ['up', 'down', 'left', 'right']:
                    new_default_key = key
                    break

            # If the current keybinding matches the old default, update it to the new default
            if keybindings.get(direction) == old_default_key and new_default_key:
                self.config_manager.set_keybinding(direction, new_default_key, save=False)

        # Save all changes
        self.config_manager.save()
        print(f"Keyboard layout changed to {layout}")

    def _settings_menu(self):
        """Display the settings menu."""
        self.screen.fill(self.colors['background'])

        # Calculate responsive positions based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            title_y = 120
            section1_y = 220
            instruction_y = 270
            section2_y = 350
            section3_y = 500
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            title_y = 110
            section1_y = 200
            instruction_y = 240
            section2_y = 320
            section3_y = 450
        else:
            title_y = 100
            section1_y = 180
            instruction_y = 220
            section2_y = 300
            section3_y = 400

        # Draw title with shadow effect
        title_text = "Settings"

        # Draw shadow
        shadow_color = (50, 50, 100)
        shadow_offset = 2
        title_shadow = self.title_font.render(title_text, True, shadow_color)
        shadow_rect = title_shadow.get_rect(center=(self.screen_width // 2 + shadow_offset, title_y + shadow_offset))
        self.screen.blit(title_shadow, shadow_rect)

        # Draw main title
        title_surface = self.title_font.render(title_text, True, self.colors['title'])
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        self.screen.blit(title_surface, title_rect)

        # Add fullscreen toggle option
        fullscreen_text = "Fullscreen Mode"
        fullscreen_surface = self.subtitle_font.render(fullscreen_text, True, self.colors['text'])
        fullscreen_rect = fullscreen_surface.get_rect(center=(self.screen_width // 2, section1_y))
        self.screen.blit(fullscreen_surface, fullscreen_rect)

        # Add instruction for fullscreen toggle
        instruction_text = "Press F11 to toggle fullscreen mode"
        instruction_surface = self.text_font.render(instruction_text, True, self.colors['text'])
        instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, instruction_y))
        self.screen.blit(instruction_surface, instruction_rect)

        # Add movement cooldown section title
        cooldown_title = "Movement Speed"
        cooldown_surface = self.subtitle_font.render(cooldown_title, True, self.colors['text'])
        cooldown_rect = cooldown_surface.get_rect(center=(self.screen_width // 2, section2_y))
        self.screen.blit(cooldown_surface, cooldown_rect)

        # Draw movement cooldown text input
        if self.movement_cooldown_input:
            # Update text input position based on current screen size
            self.movement_cooldown_input.y = section2_y + 50
            self.movement_cooldown_input.x = (self.screen_width - self.movement_cooldown_input.width) // 2
            self.movement_cooldown_input.draw(self.screen)

        # Add keyboard layout section title
        layout_title = "Keyboard Layout"
        layout_surface = self.subtitle_font.render(layout_title, True, self.colors['text'])
        layout_rect = layout_surface.get_rect(center=(self.screen_width // 2, section3_y))
        self.screen.blit(layout_surface, layout_rect)

        # Draw keyboard layout toggle button
        if self.keyboard_layout_toggle:
            # Update toggle button position based on current screen size
            self.keyboard_layout_toggle.y = section3_y + 50
            self.keyboard_layout_toggle.x = (self.screen_width - self.keyboard_layout_toggle.width) // 2

            # Update and draw the toggle button
            mouse_pos = pygame.mouse.get_pos()
            self.keyboard_layout_toggle.update(mouse_pos)
            self.keyboard_layout_toggle.draw(self.screen)

        # Update and draw buttons for this state
        mouse_pos = pygame.mouse.get_pos()
        for button in self.settings_menu_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)

        # Draw help text at the bottom
        help_text = "Lower values = faster movement"
        help_surface = self.text_font.render(help_text, True, self.colors['text'])
        help_rect = help_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 80))
        self.screen.blit(help_surface, help_rect)

        # Update the display (only once)
        pygame.display.flip()

    def _show_keybinding_dialog(self):
        """Show the key rebinding dialog."""
        # Get current keybindings
        keybindings = self.config_manager.get_keybindings()

        # Define the actions that can be rebound
        actions = [
            ('up', 'Move Up'),
            ('down', 'Move Down'),
            ('left', 'Move Left'),
            ('right', 'Move Right'),
            ('reset', 'Reset Level'),
            ('quit', 'Quit Game'),
            ('next', 'Next Level'),
            ('previous', 'Previous Level'),
            ('undo', 'Undo Move'),
            ('help', 'Show Help'),
            ('grid', 'Toggle Grid'),
            ('solve', 'Solve Level')
        ]

        # First, render the settings menu to a background surface to prevent flickering
        # This is done only once before entering the dialog loop
        self._settings_menu()
        self.background_surface = pygame.Surface((self.screen_width, self.screen_height))
        self.background_surface.blit(self.screen, (0, 0))

        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark semi-transparent background

        # Create a dialog box
        dialog_width = min(600, self.screen_width - 40)
        dialog_height = min(500, self.screen_height - 40)
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2

        # Variables for scrolling
        scroll_offset = 0
        max_scroll = max(0, len(actions) * 40 - (dialog_height - 120))

        # Font for the dialog
        title_font = pygame.font.Font(None, 36)
        text_font = pygame.font.Font(None, 24)

        # Create buttons for the dialog
        button_width = 100
        button_height = 40
        save_button = Button(
            "Save", dialog_x + dialog_width - button_width - 20, 
            dialog_y + dialog_height - button_height - 20,
            button_width, button_height, color=(100, 180, 100), hover_color=(120, 220, 120)
        )
        cancel_button = Button(
            "Cancel", dialog_x + dialog_width - button_width * 2 - 30, 
            dialog_y + dialog_height - button_height - 20,
            button_width, button_height, color=(180, 100, 100), hover_color=(220, 120, 120)
        )
        reset_button = Button(
            "Reset", dialog_x + 20, 
            dialog_y + dialog_height - button_height - 20,
            button_width, button_height, color=(100, 100, 180), hover_color=(120, 120, 220)
        )

        # Variables for key rebinding
        waiting_for_key = False
        current_action = None
        temp_keybindings = keybindings.copy()

        # Dialog loop
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if waiting_for_key:
                        # Capture the key and assign it to the current action
                        key_name = pygame.key.name(event.key)
                        if key_name != 'escape':  # Escape cancels the rebinding
                            temp_keybindings[current_action] = key_name
                        waiting_for_key = False
                        current_action = None
                    elif event.key == pygame.K_ESCAPE:
                        # Exit dialog on Escape
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        # Check if a button was clicked
                        mouse_pos = pygame.mouse.get_pos()
                        if save_button.is_hovered(mouse_pos):
                            # Save keybindings and exit
                            for action, key in temp_keybindings.items():
                                self.config_manager.set_keybinding(action, key, save=False)
                            self.config_manager.save()
                            running = False
                        elif cancel_button.is_hovered(mouse_pos):
                            # Exit without saving
                            running = False
                        elif reset_button.is_hovered(mouse_pos):
                            # Reset to defaults
                            temp_keybindings = self.config_manager.default_config['keybindings'].copy()
                        else:
                            # Check if an action row was clicked
                            for i, (action, _) in enumerate(actions):
                                row_y = dialog_y + 80 + i * 40 - scroll_offset
                                if row_y >= dialog_y + 80 and row_y <= dialog_y + dialog_height - 80:
                                    key_rect = pygame.Rect(
                                        dialog_x + dialog_width - 150, row_y, 
                                        120, 30
                                    )
                                    if key_rect.collidepoint(mouse_pos):
                                        waiting_for_key = True
                                        current_action = action
                    elif event.button == 4:  # Mouse wheel up
                        scroll_offset = max(0, scroll_offset - 20)
                    elif event.button == 5:  # Mouse wheel down
                        scroll_offset = min(max_scroll, scroll_offset + 20)

            # Draw the static background (settings menu)
            self.screen.blit(self.background_surface, (0, 0))

            # Draw the overlay
            self.screen.blit(overlay, (0, 0))

            # Draw the dialog box
            pygame.draw.rect(self.screen, (240, 240, 240), 
                            (dialog_x, dialog_y, dialog_width, dialog_height), 0, 10)
            pygame.draw.rect(self.screen, (100, 100, 100), 
                            (dialog_x, dialog_y, dialog_width, dialog_height), 2, 10)

            # Draw the title
            title_text = "Keyboard Settings"
            title_surface = title_font.render(title_text, True, (50, 50, 50))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)

            # Draw the action rows
            for i, (action, label) in enumerate(actions):
                row_y = dialog_y + 80 + i * 40 - scroll_offset

                # Only draw rows that are visible in the dialog
                if row_y >= dialog_y + 80 and row_y <= dialog_y + dialog_height - 80:
                    # Draw action label
                    label_surface = text_font.render(label, True, (50, 50, 50))
                    self.screen.blit(label_surface, (dialog_x + 20, row_y + 5))

                    # Draw key binding
                    key_text = temp_keybindings.get(action, "")
                    if waiting_for_key and action == current_action:
                        key_text = "Press a key..."

                    key_rect = pygame.Rect(dialog_x + dialog_width - 150, row_y, 120, 30)
                    pygame.draw.rect(self.screen, (230, 230, 230), key_rect, 0, 5)
                    pygame.draw.rect(self.screen, (100, 100, 100), key_rect, 1, 5)

                    key_surface = text_font.render(key_text, True, (50, 50, 50))
                    key_text_rect = key_surface.get_rect(center=key_rect.center)
                    self.screen.blit(key_surface, key_text_rect)

            # Draw scrollbar if needed
            if max_scroll > 0:
                scrollbar_height = dialog_height - 160
                thumb_height = scrollbar_height * (dialog_height - 160) / (len(actions) * 40)
                thumb_pos = dialog_y + 80 + (scrollbar_height - thumb_height) * (scroll_offset / max_scroll)

                # Draw scrollbar track
                pygame.draw.rect(self.screen, (200, 200, 200), 
                                (dialog_x + dialog_width - 20, dialog_y + 80, 
                                 10, scrollbar_height), 0, 5)

                # Draw scrollbar thumb
                pygame.draw.rect(self.screen, (150, 150, 150), 
                                (dialog_x + dialog_width - 20, thumb_pos, 
                                 10, thumb_height), 0, 5)

            # Draw buttons
            mouse_pos = pygame.mouse.get_pos()
            save_button.update(mouse_pos)
            cancel_button.update(mouse_pos)
            reset_button.update(mouse_pos)

            save_button.draw(self.screen)
            cancel_button.draw(self.screen)
            reset_button.draw(self.screen)

            # Update the display
            pygame.display.flip()

        # Clean up
        self.background_surface = None

    def _skins_menu(self):
        """Display the skins menu."""
        # Import here to avoid circular imports
        from src.ui.skins_menu import SkinsMenu

        # Use the shared skin manager or create one if not provided
        if self.skin_manager:
            skin_manager = self.skin_manager
        else:
            from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
            skin_manager = EnhancedSkinManager()

        # Create and run the skins menu
        skins_menu = SkinsMenu(self.screen, self.screen_width, self.screen_height, skin_manager)
        skins_menu.start()

        # Return to main menu after skins menu closes
        self.current_state = 'main'

    def _credits_menu(self):
        """Display the credits menu."""
        self.screen.fill(self.colors['background'])

        # Calculate responsive positions based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            title_y = 120
            min_text_y = 200
            line_spacing = 40
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            title_y = 110
            min_text_y = 180
            line_spacing = 35
        else:
            title_y = 100
            min_text_y = 150
            line_spacing = 30

        # Draw title with shadow effect
        title_text = "Credits"

        # Draw shadow
        shadow_color = (50, 50, 100)
        shadow_offset = 2
        title_shadow = self.title_font.render(title_text, True, shadow_color)
        shadow_rect = title_shadow.get_rect(center=(self.screen_width // 2 + shadow_offset, title_y + shadow_offset))
        self.screen.blit(title_shadow, shadow_rect)

        # Draw main title
        title_surface = self.title_font.render(title_text, True, self.colors['title'])
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        self.screen.blit(title_surface, title_rect)

        # Draw credits text
        credits = [
            "Sokoban Game",
            "",
            "Original game concept by Hiroyuki Imabayashi",
            "This implementation by Yassine EL IDRISSI",
            "",
            "Thanks for playing!"
        ]

        # Calculate vertical position to center the credits text
        total_text_height = len(credits) * line_spacing
        text_y_start = self.screen_height // 2 - total_text_height // 2

        # Ensure text starts below the title
        if text_y_start < min_text_y:
            text_y_start = min_text_y

        # Draw each line of credits
        for i, line in enumerate(credits):
            # Use different font sizes for different types of text
            if i == 0:  # Title line
                text_surface = self.subtitle_font.render(line, True, self.colors['title'])
            elif line == "":  # Empty line
                continue  # Skip rendering empty lines, just add space
            else:  # Regular text
                text_surface = self.text_font.render(line, True, self.colors['text'])

            text_rect = text_surface.get_rect(center=(self.screen_width // 2, text_y_start + i * line_spacing))
            self.screen.blit(text_surface, text_rect)

        # Update and draw buttons for this state
        mouse_pos = pygame.mouse.get_pos()
        for button in self.credits_menu_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)

        # Draw version info in the bottom-right corner
        version_text = "v1.0"
        version_surface = pygame.font.Font(None, 20).render(version_text, True, (100, 100, 100))
        version_rect = version_surface.get_rect(bottomright=(self.screen_width - 10, self.screen_height - 10))
        self.screen.blit(version_surface, version_rect)

        # Update the display
        pygame.display.flip()

    def _start_game_state(self):
        """Handle the start game state - this signals to the parent that a game should start."""
        # This state is handled by the parent EnhancedSokoban class
        # We just need to stop the menu loop so the parent can take over
        self.running = False


# Main function to run the menu system standalone
def main():
    """Main function to run the menu system."""
    menu = MenuSystem()
    menu.start()


if __name__ == "__main__":
    main()
