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
from src.ui.widgets import Button, ToggleButton, TextInput
from src.ui.settings_dialog import GeneralSettingsDialog
from src.ui.keybinding_dialog import KeybindingDialog


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

        # UI elements for settings
        self.keyboard_layout_toggle = None
        self.fullscreen_toggle = None
        self.window_width_input = None
        self.window_height_input = None

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

        # No UI layout containers needed in the original implementation

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

        # Variables for save success message
        self.show_save_success_message = False
        self.save_message_time = 0

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


    def _recreate_all_buttons(self):
        """Recreate all buttons, typically after a resize."""
        # Update fonts
        self._update_fonts()

        # Recreate all buttons
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
        num_buttons = 7  # Updated to 7 buttons (added AI Features)
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
            Button("AI Features", button_x, button_y_start + button_spacing * 2, button_width, button_height,
                   action=None, color=(100, 150, 200), hover_color=(130, 180, 255),
                   font_size=button_font_size),  # Action will be set by EnhancedSokoban
            Button("Settings", button_x, button_y_start + button_spacing * 3, button_width, button_height,
                   action=lambda: self._change_state('settings'), font_size=button_font_size),
            Button("Skins", button_x, button_y_start + button_spacing * 4, button_width, button_height,
                   action=None, font_size=button_font_size),  # Action will be set by EnhancedSokoban
            Button("Credits", button_x, button_y_start + button_spacing * 5, button_width, button_height,
                   action=lambda: self._change_state('credits'), font_size=button_font_size),
            Button("Exit", button_x, button_y_start + button_spacing * 6, button_width, button_height,
                   action=self._exit_game, color=(200, 100, 100), hover_color=(255, 130, 130),
                   font_size=button_font_size)
        ]


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
            save_button_width = min(max(150, self.screen_width // 8), 200)
            section1_y = 180
            section2_y = 350
            section3_y = 500
            section4_y = 650
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            button_width = min(max(100, self.screen_width // 11), 150)
            button_height = min(max(40, self.screen_height // 22), 60)
            margin = max(20, self.screen_width // 55)
            input_width = min(max(180, self.screen_width // 6), 250)
            input_height = 35
            input_y = self.screen_height // 2
            keybind_button_width = min(max(200, self.screen_width // 7), 300)
            save_button_width = min(max(120, self.screen_width // 9), 180)
            section1_y = 160
            section2_y = 320
            section3_y = 450
            section4_y = 580
        else:
            button_width = min(max(80, self.screen_width // 12), 120)
            button_height = min(max(30, self.screen_height // 25), 50)
            margin = max(15, self.screen_width // 60)
            input_width = min(max(150, self.screen_width // 7), 200)
            input_height = 30
            input_y = 300
            keybind_button_width = min(max(150, self.screen_width // 8), 250)
            save_button_width = min(max(100, self.screen_width // 10), 150)
            section1_y = 140
            section2_y = 300
            section3_y = 400
            section4_y = 500

        # Calculate font size based on button dimensions
        button_font_size = min(max(18, button_height // 2), 36)

        # Create main settings buttons
        self.settings_menu_buttons = [
            Button("Back", margin, self.screen_height - button_height * 2 - margin * 2, 
                   button_width, button_height, 
                   action=lambda: self._change_state('main'),
                   font_size=button_font_size),
            Button("Keyboard Settings", (self.screen_width - keybind_button_width) // 2, 
                   self.screen_height // 2 - button_height,
                   keybind_button_width, button_height,
                   action=self._show_keybinding_dialog,
                   font_size=button_font_size),
            Button("General Settings", (self.screen_width - keybind_button_width) // 2, 
                   self.screen_height // 2 + button_height,
                   keybind_button_width, button_height,
                   action=self._show_general_settings_dialog,
                   font_size=button_font_size),
            Button("Save", (self.screen_width - save_button_width) // 2, 
                   self.screen_height - button_height * 2 - margin * 2,
                   save_button_width, button_height,
                   action=self._save_settings,
                   color=(100, 180, 100), hover_color=(120, 220, 120),
                   font_size=button_font_size)
        ]

        # Create fullscreen toggle button
        current_fullscreen = self.config_manager.get('display', 'fullscreen', False)
        toggle_width = min(max(200, self.screen_width // 7), 300)
        toggle_height = button_height
        toggle_x = (self.screen_width - toggle_width) // 2
        toggle_y = section1_y + 50  # Position below fullscreen title

        self.fullscreen_toggle = ToggleButton(
            "ON", "OFF", toggle_x, toggle_y, toggle_width, toggle_height,
            is_on=current_fullscreen, action=self._toggle_fullscreen,
            color_on=(100, 180, 100), color_off=(180, 100, 100),
            hover_color_on=(120, 220, 120), hover_color_off=(220, 120, 120),
            font_size=button_font_size
        )

        # Create window size text inputs
        window_width = self.config_manager.get('display', 'window_width', 900)
        window_height = self.config_manager.get('display', 'window_height', 700)

        # Width input
        width_input_x = (self.screen_width - input_width) // 2 - input_width // 2 - 10
        width_input_y = section2_y + 50
        self.window_width_input = TextInput(
            width_input_x, width_input_y, input_width, input_height,
            min_value=800, max_value=3840, current_value=window_width,
            label="Window Width",
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        # Height input
        height_input_x = (self.screen_width - input_width) // 2 + input_width // 2 + 10
        height_input_y = section2_y + 50
        self.window_height_input = TextInput(
            height_input_x, height_input_y, input_width, input_height,
            min_value=600, max_value=2160, current_value=window_height,
            label="Window Height",
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        # Create movement cooldown text input
        input_x = (self.screen_width - input_width) // 2
        cooldown_input_y = section3_y + 50

        current_cooldown = self.config_manager.get('game', 'movement_cooldown', 200)
        self.movement_cooldown_input = TextInput(
            input_x, cooldown_input_y, input_width, input_height,
            min_value=50, max_value=500, current_value=current_cooldown,
            label="Movement Cooldown (ms)",
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        # Create keyboard layout toggle button
        current_layout = self.config_manager.get('game', 'keyboard_layout', 'qwerty')
        is_azerty = current_layout.lower() == 'azerty'

        toggle_x = (self.screen_width - toggle_width) // 2
        toggle_y = section4_y + 50  # Position below keyboard layout title

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

    def handle_events(self, events):
        """Process a pre-filtered list of events (global events already handled).

        Args:
            events: List of pygame events (QUIT/VIDEORESIZE/F11 already consumed).
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.current_state != 'main':
                    self._change_state('main')

            for button in self._get_active_buttons():
                button.handle_event(event)

            if self.current_state == 'settings':
                self._handle_settings_event(event)

    def _get_active_buttons(self):
        """Return the button list for the current menu state."""
        return {
            'main': self.main_menu_buttons,
            'play': self.play_menu_buttons,
            'editor': self.editor_menu_buttons,
            'settings': self.settings_menu_buttons,
            'skins': self.skins_menu_buttons,
            'credits': self.credits_menu_buttons,
        }.get(self.current_state, [])

    def _handle_settings_event(self, event):
        """Distribute an event to ALL settings widgets."""
        if self.movement_cooldown_input and self.movement_cooldown_input.handle_event(event):
            new_value = int(self.movement_cooldown_input.current_value)
            self.config_manager.set('game', 'movement_cooldown', new_value, save=False)

        if self.window_width_input and self.window_width_input.handle_event(event):
            new_width = int(self.window_width_input.current_value)
            self.config_manager.set('display', 'window_width', new_width, save=False)

        if self.window_height_input and self.window_height_input.handle_event(event):
            new_height = int(self.window_height_input.current_value)
            self.config_manager.set('display', 'window_height', new_height, save=False)

        if self.fullscreen_toggle and self.fullscreen_toggle.handle_event(event):
            self.config_manager.set('display', 'fullscreen', self.fullscreen_toggle.is_on, save=False)

        if self.keyboard_layout_toggle and self.keyboard_layout_toggle.handle_event(event):
            layout = 'azerty' if self.keyboard_layout_toggle.is_on else 'qwerty'
            self.config_manager.set('game', 'keyboard_layout', layout, save=True)

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

    def _toggle_fullscreen(self, is_fullscreen):
        """
        Toggle fullscreen mode.

        Args:
            is_fullscreen (bool): True if fullscreen mode is enabled, False otherwise.
        """
        # Update the config manager with the new fullscreen state
        self.config_manager.set('display', 'fullscreen', is_fullscreen, save=False)

        # Actually toggle fullscreen mode
        if is_fullscreen:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)


    def _toggle_keyboard_layout(self, is_azerty):
        """
        Toggle between QWERTY and AZERTY keyboard layouts.

        Args:
            is_azerty (bool): True if AZERTY layout is selected, False for QWERTY.
        """
        layout = 'azerty' if is_azerty else 'qwerty'

        # Force direct update of the config file
        self.config_manager.config['game']['keyboard_layout'] = layout
        self.config_manager.save()

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


    def _save_settings(self):
        """Save all settings to the config file."""
        # Ensure the current value of the movement cooldown input field is saved to the config manager
        if self.movement_cooldown_input:
            # Get the current value from the input field
            current_value = int(self.movement_cooldown_input.current_value)
            # Update the config manager with the current value
            self.config_manager.set('game', 'movement_cooldown', current_value, save=False)

        # Ensure the current fullscreen toggle state is saved to the config manager
        if self.fullscreen_toggle:
            # Get the current state from the toggle button
            is_fullscreen = self.fullscreen_toggle.is_on
            # Update the config manager with the current state
            self.config_manager.set('display', 'fullscreen', is_fullscreen, save=False)

        # Ensure the current window size values are saved to the config manager
        if self.window_width_input and self.window_height_input:
            # Get the current values from the input fields
            window_width = int(self.window_width_input.current_value)
            window_height = int(self.window_height_input.current_value)
            # Update the config manager with the current values
            self.config_manager.set('display', 'window_width', window_width, save=False)
            self.config_manager.set('display', 'window_height', window_height, save=False)

        # Save keyboard layout separately to avoid toggling
        if self.keyboard_layout_toggle:
            layout = 'azerty' if self.keyboard_layout_toggle.is_on else 'qwerty'
            self.config_manager.config['game']['keyboard_layout'] = layout

        # Save all changes to the config file
        success = self.config_manager.save()

        if success:
            # Show a temporary success message
            self.show_save_success_message = True
            self.save_message_time = pygame.time.get_ticks()

    def _settings_menu(self):
        """Display the settings menu."""
        self.screen.fill(self.colors['background'])

        # Calculate responsive positions based on screen resolution
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            title_y = 120
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            title_y = 110
        else:
            title_y = 100

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

        # Update and draw buttons for this state
        mouse_pos = pygame.mouse.get_pos()
        for button in self.settings_menu_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)



        # Show save success message if needed
        if hasattr(self, 'show_save_success_message') and self.show_save_success_message:
            current_time = pygame.time.get_ticks()
            # Show message for 2 seconds
            if current_time - self.save_message_time < 2000:
                # Draw a semi-transparent background for the message
                message_width = 300
                message_height = 50
                message_x = (self.screen_width - message_width) // 2
                message_y = 20

                # Create a semi-transparent surface
                message_bg = pygame.Surface((message_width, message_height), pygame.SRCALPHA)
                message_bg.fill((0, 150, 0, 180))  # Green with alpha
                self.screen.blit(message_bg, (message_x, message_y))

                # Draw the message text
                message_text = "Settings saved successfully!"
                message_surface = self.text_font.render(message_text, True, (255, 255, 255))
                message_rect = message_surface.get_rect(center=(self.screen_width // 2, message_y + message_height // 2))
                self.screen.blit(message_surface, message_rect)
            else:
                # Time's up, hide the message
                self.show_save_success_message = False

        # Update the display (only once)
        pygame.display.flip()

    def _show_general_settings_dialog(self):
        """Show the general settings dialog."""
        # First, render the settings menu to a background surface to prevent flickering
        self._settings_menu()

        # Delegate to the extracted dialog class
        dialog = GeneralSettingsDialog(self.screen, self.config_manager, self.screen_width, self.screen_height)
        result = dialog.show()

        if result is not None:
            # Check if the app should quit
            if result.get('quit_app', False):
                self.running = False
                # If only quit_app is set (no other keys), it was a cancel with QUIT event
                if len(result) <= 1:
                    return

            # Update the actual UI elements with the returned settings
            self.fullscreen_toggle.is_on = result['fullscreen']
            self.window_width_input.current_value = result['window_width']
            self.window_width_input.text = str(result['window_width'])
            self.window_height_input.current_value = result['window_height']
            self.window_height_input.text = str(result['window_height'])
            self.movement_cooldown_input.current_value = result['movement_cooldown']
            self.movement_cooldown_input.text = str(result['movement_cooldown'])

            # Update mouse navigation system with new speed
            if hasattr(self, 'game_instance') and self.game_instance and hasattr(self.game_instance, 'mouse_navigation'):
                self.game_instance.mouse_navigation.update_movement_speed()

            # Update keyboard layout toggle without calling the toggle method
            # This prevents the toggle from happening when saving
            if self.keyboard_layout_toggle.is_on != result['keyboard_layout_is_azerty']:
                # Only update if the state has changed
                self.keyboard_layout_toggle.is_on = result['keyboard_layout_is_azerty']
                self.keyboard_layout_toggle.text = self.keyboard_layout_toggle.text_on if result['keyboard_layout_is_azerty'] else self.keyboard_layout_toggle.text_off
                self.keyboard_layout_toggle.color = self.keyboard_layout_toggle.color_on if result['keyboard_layout_is_azerty'] else self.keyboard_layout_toggle.color_off
                self.keyboard_layout_toggle.hover_color = self.keyboard_layout_toggle.hover_color_on if result['keyboard_layout_is_azerty'] else self.keyboard_layout_toggle.hover_color_off
                self.keyboard_layout_toggle.current_color = self.keyboard_layout_toggle.color

            # Apply fullscreen change immediately
            self._toggle_fullscreen(result['fullscreen'])

    def _show_keybinding_dialog(self):
        """Show the key rebinding dialog."""
        # First, render the settings menu to a background surface to prevent flickering
        self._settings_menu()

        # Delegate to the extracted dialog class
        dialog = KeybindingDialog(self.screen, self.config_manager, self.screen_width, self.screen_height)
        dialog.show()

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
    from src.ui.event_dispatcher import EventDispatcher

    menu = MenuSystem()
    menu.running = True
    dispatcher = EventDispatcher(on_quit=menu._exit_game)
    clock = pygame.time.Clock()
    while menu.running:
        events = dispatcher.pump()
        menu.handle_events(events)
        menu.states[menu.current_state]()
        clock.tick(60)


if __name__ == "__main__":
    main()
