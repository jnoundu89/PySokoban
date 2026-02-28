"""
Keybinding Dialog for the Sokoban game.

This module provides a modal dialog for rebinding keyboard controls.
Extracted from MenuSystem to reduce class complexity.
"""

import pygame
from src.ui.widgets import Button


class KeybindingDialog:
    """
    Modal dialog for keyboard keybinding configuration.

    Displays a scrollable dialog listing all rebindable actions,
    allowing the user to click on a key binding and press a new key
    to reassign it.
    """

    def __init__(self, screen, config_manager, screen_width, screen_height):
        """
        Initialize the keybinding dialog.

        Args:
            screen: Pygame surface to draw on.
            config_manager: ConfigManager instance for reading/writing keybindings.
            screen_width (int): Width of the screen.
            screen_height (int): Height of the screen.
        """
        self.screen = screen
        self.config_manager = config_manager
        self.screen_width = screen_width
        self.screen_height = screen_height

    def show(self):
        """
        Show the keybinding dialog and run its event loop.

        Returns:
            bool: True if keybindings were saved, False if cancelled.
        """
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

        # Capture the background surface from the screen
        background_surface = pygame.Surface((self.screen_width, self.screen_height))
        background_surface.blit(self.screen, (0, 0))

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
        # Increase max_scroll to ensure the last element is fully visible
        max_scroll = max(0, len(actions) * 40 - (dialog_height - 160))

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

        # Track whether the parent menu loop should also stop
        quit_app = False

        # Dialog loop
        running = True
        saved = False
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    quit_app = True
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
                            saved = True
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
            self.screen.blit(background_surface, (0, 0))

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
            # Update all buttons with current mouse position
            save_button.update(mouse_pos)
            cancel_button.update(mouse_pos)
            reset_button.update(mouse_pos)

            save_button.draw(self.screen)
            cancel_button.draw(self.screen)
            reset_button.draw(self.screen)

            # Update the display
            pygame.display.flip()

        return saved
