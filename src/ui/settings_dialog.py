"""
General Settings Dialog for the Sokoban game.

This module provides a modal dialog for editing general game settings
such as fullscreen mode, window size, movement speed, keyboard layout, etc.
Extracted from MenuSystem to reduce class complexity.
"""

import pygame
from src.ui.widgets import Button, ToggleButton, TextInput


class GeneralSettingsDialog:
    """
    Modal dialog for general game settings.

    Displays a scrollable dialog with controls for fullscreen mode,
    window size, movement speed, mouse movement speed, keyboard layout,
    and deadlock display settings.
    """

    def __init__(self, screen, config_manager, screen_width, screen_height):
        """
        Initialize the general settings dialog.

        Args:
            screen: Pygame surface to draw on.
            config_manager: ConfigManager instance for reading/writing settings.
            screen_width (int): Width of the screen.
            screen_height (int): Height of the screen.
        """
        self.screen = screen
        self.config_manager = config_manager
        self.screen_width = screen_width
        self.screen_height = screen_height

    def show(self):
        """
        Show the general settings dialog and run its event loop.

        Returns:
            dict or None: A dict with settings values if saved, None if cancelled.
                Keys: 'fullscreen', 'window_width', 'window_height',
                      'movement_cooldown', 'mouse_movement_speed',
                      'keyboard_layout_is_azerty', 'show_deadlocks'
        """
        # Capture the background surface from the screen
        background_surface = pygame.Surface((self.screen_width, self.screen_height))
        background_surface.blit(self.screen, (0, 0))

        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark semi-transparent background

        # Create a dialog box
        dialog_width = min(700, self.screen_width - 40)
        dialog_height = min(600, self.screen_height - 40)
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2

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

        # Calculate section positions with more spacing to prevent overlaps
        section_padding = 40  # Increased padding
        base_section1_y = 80  # Fullscreen toggle
        base_section2_y = base_section1_y + 120  # Window size (increased spacing)
        base_section3_y = base_section2_y + 120  # Movement speed (increased spacing)
        base_section4_y = base_section3_y + 140  # Mouse movement speed (increased spacing for help text)
        base_section5_y = base_section4_y + 140  # Keyboard layout (increased spacing for help text)
        base_section6_y = base_section5_y + 120  # Deadlock toggle (increased spacing)

        # Variables for scrolling
        scroll_offset = 0
        # Calculate total content height and maximum scroll value
        total_content_height = base_section6_y + 60  # Add some padding at the bottom
        visible_content_height = dialog_height - 160  # Subtract space for title and buttons
        max_scroll = max(0, total_content_height - visible_content_height)

        # Define two-column layout
        left_column_x = dialog_x + 40  # Left column for labels
        right_column_x = dialog_x + dialog_width // 2  # Right column for interactive elements

        # Create temporary copies of UI elements for the dialog
        # Fullscreen toggle
        current_fullscreen = self.config_manager.get('display', 'fullscreen', False)
        toggle_width = min(200, dialog_width // 2 - 60)  # Adjusted width for right column
        toggle_height = button_height
        toggle_x = right_column_x  # Use right column position
        section1_y = dialog_y + base_section1_y - scroll_offset
        fullscreen_toggle = ToggleButton(
            "ON", "OFF", toggle_x, section1_y,  # Align vertically with the label
            toggle_width, toggle_height,
            is_on=current_fullscreen, action=None,
            color_on=(100, 180, 100), color_off=(180, 100, 100),
            hover_color_on=(120, 220, 120), hover_color_off=(220, 120, 120)
        )

        # Window size inputs
        window_width = self.config_manager.get('display', 'window_width', 900)
        window_height = self.config_manager.get('display', 'window_height', 700)
        input_width = min(80, dialog_width // 6)  # Smaller width for each input
        input_height = 40

        # Position inputs in the right column with space for the "x" between them
        width_input_x = right_column_x
        height_input_x = right_column_x + input_width + 30  # Space for "x" between inputs
        section2_y = dialog_y + base_section2_y - scroll_offset

        width_input = TextInput(
            width_input_x, section2_y,  # Align vertically with the label
            input_width, input_height,
            min_value=800, max_value=3840, current_value=window_width,
            label="",  # Remove label as it's now in the left column
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        height_input = TextInput(
            height_input_x, section2_y,  # Align vertically with the label
            input_width, input_height,
            min_value=600, max_value=2160, current_value=window_height,
            label="",  # Remove label as it's now in the left column
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        # Movement cooldown input
        current_cooldown = self.config_manager.get('game', 'movement_cooldown', 200)
        section3_y = dialog_y + base_section3_y - scroll_offset
        cooldown_input = TextInput(
            right_column_x, section3_y,  # Align vertically with the label
            input_width * 2, input_height,  # Wider input for movement cooldown
            min_value=50, max_value=500, current_value=current_cooldown,
            label="",  # Remove label as it's now in the left column
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        # Mouse movement speed input
        current_mouse_speed = self.config_manager.get('game', 'mouse_movement_speed', 100)
        section4_y = dialog_y + base_section4_y - scroll_offset
        mouse_speed_input = TextInput(
            right_column_x, section4_y,  # Align vertically with the label
            input_width * 2, input_height,  # Wider input for mouse movement speed
            min_value=50, max_value=500, current_value=current_mouse_speed,
            label="",  # Remove label as it's now in the left column
            color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)
        )

        # Keyboard layout toggle
        current_layout = self.config_manager.get('game', 'keyboard_layout', 'qwerty')
        is_azerty = current_layout.lower() == 'azerty'
        section5_y = dialog_y + base_section5_y - scroll_offset
        keyboard_toggle = ToggleButton(
            "AZERTY", "QWERTY", right_column_x, section5_y,  # Align vertically with the label
            toggle_width, toggle_height,
            is_on=is_azerty, action=None,
            color_on=(100, 180, 100), color_off=(100, 100, 180),
            hover_color_on=(120, 220, 120), hover_color_off=(120, 120, 220)
        )

        # Deadlock toggle
        show_deadlocks = self.config_manager.get('game', 'show_deadlocks', True)
        section6_y = dialog_y + base_section6_y - scroll_offset
        deadlock_toggle = ToggleButton(
            "ON", "OFF", right_column_x, section6_y,  # Align vertically with the label
            toggle_width, toggle_height,
            is_on=show_deadlocks, action=None,
            color_on=(100, 180, 100), color_off=(180, 100, 100),
            hover_color_on=(120, 220, 120), hover_color_off=(220, 120, 120)
        )

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
                    if event.key == pygame.K_ESCAPE:
                        # Exit dialog on Escape
                        running = False
                    else:
                        # Pass keyboard events to text inputs
                        width_input.handle_event(event)
                        height_input.handle_event(event)
                        cooldown_input.handle_event(event)
                        mouse_speed_input.handle_event(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        # Check if a button was clicked
                        mouse_pos = pygame.mouse.get_pos()
                        if save_button.is_hovered(mouse_pos):
                            # Save settings and exit
                            # Print the current keyboard layout before changing it
                            current_layout = self.config_manager.get('game', 'keyboard_layout', 'qwerty')
                            print(f"Current keyboard layout before save: {current_layout}")

                            # Update all settings in the config manager
                            self.config_manager.set('display', 'fullscreen', fullscreen_toggle.is_on, save=False)
                            self.config_manager.set('display', 'window_width', width_input.current_value, save=False)
                            self.config_manager.set('display', 'window_height', height_input.current_value, save=False)
                            self.config_manager.set('game', 'movement_cooldown', cooldown_input.current_value, save=False)
                            self.config_manager.set('game', 'mouse_movement_speed', mouse_speed_input.current_value, save=False)
                            self.config_manager.set('game', 'show_deadlocks', deadlock_toggle.is_on, save=False)

                            # Save all settings except keyboard layout
                            self.config_manager.save()

                            # Handle keyboard layout separately to avoid toggling
                            # Just set the value in the config file without calling the toggle method
                            layout = 'azerty' if keyboard_toggle.is_on else 'qwerty'
                            print(f"Setting keyboard layout to: {layout} (toggle is_on: {keyboard_toggle.is_on})")

                            # Update the config file with the new keyboard layout
                            self.config_manager.config['game']['keyboard_layout'] = layout
                            self.config_manager.save()

                            saved = True
                            running = False
                        elif cancel_button.is_hovered(mouse_pos):
                            # Exit without saving
                            running = False
                        else:
                            # Handle mouse down events for text inputs
                            width_input.handle_event(event)
                            height_input.handle_event(event)
                            cooldown_input.handle_event(event)
                            mouse_speed_input.handle_event(event)
                    elif event.button == 4:  # Mouse wheel up
                        scroll_offset = max(0, scroll_offset - 20)
                        # Update section positions
                        section1_y = dialog_y + base_section1_y - scroll_offset
                        section2_y = dialog_y + base_section2_y - scroll_offset
                        section3_y = dialog_y + base_section3_y - scroll_offset
                        section4_y = dialog_y + base_section4_y - scroll_offset
                        section5_y = dialog_y + base_section5_y - scroll_offset
                        section6_y = dialog_y + base_section6_y - scroll_offset

                        # Update UI element positions
                        fullscreen_toggle.y = section1_y
                        width_input.y = section2_y
                        height_input.y = section2_y
                        cooldown_input.y = section3_y
                        mouse_speed_input.y = section4_y
                        keyboard_toggle.y = section5_y
                        deadlock_toggle.y = section6_y
                    elif event.button == 5:  # Mouse wheel down
                        scroll_offset = min(max_scroll, scroll_offset + 20)
                        # Update section positions
                        section1_y = dialog_y + base_section1_y - scroll_offset
                        section2_y = dialog_y + base_section2_y - scroll_offset
                        section3_y = dialog_y + base_section3_y - scroll_offset
                        section4_y = dialog_y + base_section4_y - scroll_offset
                        section5_y = dialog_y + base_section5_y - scroll_offset
                        section6_y = dialog_y + base_section6_y - scroll_offset

                        # Update UI element positions
                        fullscreen_toggle.y = section1_y
                        width_input.y = section2_y
                        height_input.y = section2_y
                        cooldown_input.y = section3_y
                        mouse_speed_input.y = section4_y
                        keyboard_toggle.y = section5_y
                        deadlock_toggle.y = section6_y
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button
                        # Handle mouse up events for toggle buttons
                        fullscreen_toggle.handle_event(event)
                        keyboard_toggle.handle_event(event)
                        deadlock_toggle.handle_event(event)

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
            title_text = "General Settings"
            title_surface = title_font.render(title_text, True, (50, 50, 50))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)

            # Define the visible area for content
            content_top = dialog_y + 80
            content_bottom = dialog_y + dialog_height - 80

            # Draw section titles and UI elements only if they are visible
            # Fullscreen section
            if section1_y + toggle_height >= content_top and section1_y <= content_bottom:
                fullscreen_title = text_font.render("Fullscreen Mode:", True, (50, 50, 50))
                # Right-align the text in the left column
                fullscreen_rect = fullscreen_title.get_rect(right=right_column_x - 20, centery=section1_y + toggle_height // 2)
                self.screen.blit(fullscreen_title, fullscreen_rect)
                fullscreen_toggle.draw(self.screen)

            # Window size section
            if section2_y + input_height >= content_top and section2_y <= content_bottom:
                window_size_title = text_font.render("Window Size:", True, (50, 50, 50))
                window_size_rect = window_size_title.get_rect(right=right_column_x - 20, centery=section2_y + input_height // 2)
                self.screen.blit(window_size_title, window_size_rect)
                width_input.draw(self.screen)
                height_input.draw(self.screen)

                # Draw "x" between width and height inputs
                x_text = "x"
                x_surface = text_font.render(x_text, True, (50, 50, 50))
                # Position "x" between the two inputs
                x_rect = x_surface.get_rect(center=(width_input_x + input_width + 15, section2_y + input_height // 2))
                self.screen.blit(x_surface, x_rect)

            # Movement speed section
            if section3_y + input_height >= content_top and section3_y <= content_bottom:
                movement_title = text_font.render("Movement Speed:", True, (50, 50, 50))
                movement_rect = movement_title.get_rect(right=right_column_x - 20, centery=section3_y + input_height // 2)
                self.screen.blit(movement_title, movement_rect)
                cooldown_input.draw(self.screen)

                # Draw help text below movement speed section with better visibility
                help_text = "Lower values = faster movement"
                help_surface = text_font.render(help_text, True, (50, 50, 50))
                # Position it below the input field in the right column
                help_rect = help_surface.get_rect(left=right_column_x, top=section3_y + input_height + 30)
                # Only draw help text if it's visible
                if help_rect.top <= content_bottom:
                    # Draw a light background behind the text for better readability
                    bg_rect = pygame.Rect(help_rect.x - 5, help_rect.y - 5, help_rect.width + 10, help_rect.height + 10)
                    pygame.draw.rect(self.screen, (230, 230, 250), bg_rect, 0, 5)
                    pygame.draw.rect(self.screen, (200, 200, 220), bg_rect, 1, 5)
                    self.screen.blit(help_surface, help_rect)

            # Mouse movement speed section
            if section4_y + input_height >= content_top and section4_y <= content_bottom:
                mouse_movement_title = text_font.render("Mouse Movement Speed:", True, (50, 50, 50))
                mouse_movement_rect = mouse_movement_title.get_rect(right=right_column_x - 20, centery=section4_y + input_height // 2)
                self.screen.blit(mouse_movement_title, mouse_movement_rect)
                mouse_speed_input.draw(self.screen)

                # Draw help text below mouse movement speed section with better visibility
                help_text = "Lower values = faster movement"
                help_surface = text_font.render(help_text, True, (50, 50, 50))
                # Position it below the input field in the right column
                help_rect = help_surface.get_rect(left=right_column_x, top=section4_y + input_height + 30)
                # Only draw help text if it's visible
                if help_rect.top <= content_bottom:
                    # Draw a light background behind the text for better readability
                    bg_rect = pygame.Rect(help_rect.x - 5, help_rect.y - 5, help_rect.width + 10, help_rect.height + 10)
                    pygame.draw.rect(self.screen, (230, 230, 250), bg_rect, 0, 5)
                    pygame.draw.rect(self.screen, (200, 200, 220), bg_rect, 1, 5)
                    self.screen.blit(help_surface, help_rect)

            # Keyboard layout section
            if section5_y + toggle_height >= content_top and section5_y <= content_bottom:
                keyboard_title = text_font.render("Keyboard Layout:", True, (50, 50, 50))
                keyboard_rect = keyboard_title.get_rect(right=right_column_x - 20, centery=section5_y + toggle_height // 2)
                self.screen.blit(keyboard_title, keyboard_rect)
                keyboard_toggle.draw(self.screen)

            # Deadlock section
            if section6_y + toggle_height >= content_top and section6_y <= content_bottom:
                deadlock_title = text_font.render("Show Deadlocks:", True, (50, 50, 50))
                deadlock_rect = deadlock_title.get_rect(right=right_column_x - 20, centery=section6_y + toggle_height // 2)
                self.screen.blit(deadlock_title, deadlock_rect)
                deadlock_toggle.draw(self.screen)

            # Draw scrollbar if needed
            if max_scroll > 0:
                scrollbar_height = dialog_height - 160
                thumb_height = max(30, scrollbar_height * (dialog_height - 160) / total_content_height)
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
            fullscreen_toggle.update(mouse_pos)
            width_input.update(mouse_pos)
            height_input.update(mouse_pos)
            cooldown_input.update(mouse_pos)
            mouse_speed_input.update(mouse_pos)
            keyboard_toggle.update(mouse_pos)
            deadlock_toggle.update(mouse_pos)

            save_button.draw(self.screen)
            cancel_button.draw(self.screen)

            # Update the display
            pygame.display.flip()

        if saved:
            return {
                'fullscreen': fullscreen_toggle.is_on,
                'window_width': width_input.current_value,
                'window_height': height_input.current_value,
                'movement_cooldown': cooldown_input.current_value,
                'mouse_movement_speed': mouse_speed_input.current_value,
                'keyboard_layout_is_azerty': keyboard_toggle.is_on,
                'show_deadlocks': deadlock_toggle.is_on,
                'quit_app': quit_app,
            }
        else:
            if quit_app:
                return {'quit_app': True}
            return None
