"""
Editor Event Handler delegate for the Enhanced Level Editor.

This module handles all event processing for the level editor,
including keyboard events, mouse clicks, mouse motion, mouse wheel,
window resize, and text input.
"""

import pygame
from ..core.constants import CELL_SIZE, FLOOR


class EditorEventHandler:
    """
    Handles all event processing for the EnhancedLevelEditor.

    Uses a back-reference to the editor instance to access shared state
    and call methods on the editor and other delegates.
    """

    def __init__(self, editor):
        """
        Initialize the event handler with a back-reference to the editor.

        Args:
            editor: The EnhancedLevelEditor instance.
        """
        self.editor = editor

    def handle_key_event(self, event):
        """Handle keyboard events."""
        # Handle text input if a text field is active
        if self.editor.active_text_field:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Apply the text input and clear the active text field
                self.apply_text_input()
                self.editor.active_text_field = None
            elif event.key == pygame.K_ESCAPE:
                # Cancel text input and revert to the current value
                self.editor.active_text_field = None
            elif event.key == pygame.K_BACKSPACE:
                # Remove the last character
                self.editor.text_input = self.editor.text_input[:-1]
                self.editor.text_input_cursor_visible = True
                self.editor.text_input_cursor_timer = 0
            elif event.unicode.isdigit():
                # Add the digit to the text input
                self.editor.text_input += event.unicode
                self.editor.text_input_cursor_visible = True
                self.editor.text_input_cursor_timer = 0
            return

        # Regular key handling
        if event.key == pygame.K_ESCAPE:
            if self.editor.show_help:
                self.editor.show_help = False
            elif self.editor.test_mode:
                self.editor._toggle_test_mode()
            else:
                self.editor._exit_editor()
        elif event.key == pygame.K_h:
            self.editor._toggle_help()
        elif event.key == pygame.K_g:
            self.editor._toggle_grid()
        elif event.key == pygame.K_t:
            self.editor._toggle_test_mode()
        elif event.key == pygame.K_m:
            self.editor._toggle_metrics()
        elif self.editor.test_mode:
            # Handle keyboard movement in test mode
            dx, dy = 0, 0
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                dy = -1
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                dy = 1
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                dx = -1
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                dx = 1

            if dx != 0 or dy != 0:
                self.editor.current_level.move(dx, dy)
        else:
            # Handle scrolling in edit mode
            scroll_speed = 20
            if event.key == pygame.K_UP:
                self.editor._handle_scroll(0, scroll_speed)
            elif event.key == pygame.K_DOWN:
                self.editor._handle_scroll(0, -scroll_speed)
            elif event.key == pygame.K_LEFT:
                self.editor._handle_scroll(scroll_speed, 0)
            elif event.key == pygame.K_RIGHT:
                self.editor._handle_scroll(-scroll_speed, 0)

    def handle_mouse_down(self, event):
        """Handle mouse button down events."""
        mouse_pos = pygame.mouse.get_pos()

        # Check button clicks
        for button in self.editor.buttons:
            if button['rect'].collidepoint(mouse_pos):
                button['action']()
                return

        # Check slider and text field clicks
        for slider in self.editor.sliders:
            # Check for text field clicks if this slider has a text field
            if slider.get('text_field'):
                # Calculate text field position (same as in draw_slider)
                label_text = f"{slider['label']}:"
                label_width = self.editor.text_font.size(label_text)[0]
                text_field_x = slider['rect'].x + label_width + 10
                text_field_y = slider['rect'].y - 25
                text_field_width = 50
                text_field_height = 22
                text_field_rect = pygame.Rect(text_field_x, text_field_y, text_field_width, text_field_height)

                if text_field_rect.collidepoint(mouse_pos):
                    # Clicked on text field
                    self.editor.active_text_field = slider
                    self.editor.text_input = str(slider['value'])
                    self.editor.text_input_cursor_visible = True
                    self.editor.text_input_cursor_timer = 0
                    return

            # Check for slider track clicks
            if slider['rect'].collidepoint(mouse_pos):
                self.editor.active_slider = slider
                self.handle_slider_click(mouse_pos, slider)
                return

        # Check palette clicks (left panel) or right panel clicks
        if mouse_pos[0] < self.editor.tool_panel_width:
            self.handle_palette_click(mouse_pos)
            return
        elif mouse_pos[0] > self.editor.screen_width - self.editor.right_panel_width:
            # Right panel clicks are handled by button checks above
            return

        # Check map area clicks
        if self.editor._is_in_map_area(mouse_pos):
            if event.button == 2:  # Middle mouse button - start dragging
                self.editor.mouse_dragging = True
                self.editor.drag_start_pos = mouse_pos
                self.editor.drag_start_scroll = (self.editor.scroll_x, self.editor.scroll_y)
            else:
                self.editor.paint_mode = True
                self.editor.last_painted_cell = None
                self.editor.active_mouse_button = event.button
                self.handle_grid_click(mouse_pos, event.button)

    def handle_mouse_up(self, event):
        """Handle mouse button up events."""
        if event.button == 2:  # Middle mouse button
            self.editor.mouse_dragging = False
            self.editor.drag_start_pos = None
            self.editor.drag_start_scroll = None
        else:
            self.editor.paint_mode = False
            self.editor.last_painted_cell = None
            self.editor.active_mouse_button = None
            self.editor.active_slider = None

            # If we have an active text field and clicked elsewhere, apply the value
            if self.editor.active_text_field:
                mouse_pos = pygame.mouse.get_pos()

                # Calculate text field position (same as in draw_slider)
                slider = self.editor.active_text_field
                label_text = f"{slider['label']}:"
                label_width = self.editor.text_font.size(label_text)[0]
                text_field_x = slider['rect'].x + label_width + 10
                text_field_y = slider['rect'].y - 25
                text_field_width = 50
                text_field_height = 22
                text_field_rect = pygame.Rect(text_field_x, text_field_y, text_field_width, text_field_height)

                # If clicked outside the text field, apply the value
                if not text_field_rect.collidepoint(mouse_pos):
                    self.apply_text_input()
                    self.editor.active_text_field = None

    def handle_mouse_motion(self, event):
        """Handle mouse motion events."""
        mouse_pos = pygame.mouse.get_pos()

        if self.editor.mouse_dragging and self.editor.drag_start_pos and self.editor.drag_start_scroll:
            # Handle middle mouse dragging for panning
            dx = mouse_pos[0] - self.editor.drag_start_pos[0]
            dy = mouse_pos[1] - self.editor.drag_start_pos[1]

            self.editor.scroll_x = self.editor.drag_start_scroll[0] + dx
            self.editor.scroll_y = self.editor.drag_start_scroll[1] + dy

            # No scroll limits - allow infinite scrolling in all directions

        elif self.editor.active_slider:
            # Continue adjusting slider while dragging
            self.handle_slider_click(mouse_pos, self.editor.active_slider)

        elif self.editor.paint_mode and self.editor._is_in_map_area(mouse_pos) and self.editor.active_mouse_button:
            # Continue painting while dragging
            self.handle_grid_click(mouse_pos, self.editor.active_mouse_button, is_drag=True)

    def handle_mouse_wheel(self, event):
        """Handle mouse wheel events for zooming."""
        if self.editor._is_in_map_area(pygame.mouse.get_pos()):
            if event.y > 0:
                self.editor._zoom_in()
            else:
                self.editor._zoom_out()

    def handle_resize(self, event):
        """Handle window resize events."""
        self.editor.screen_width, self.editor.screen_height = event.size
        if not self.editor.using_shared_screen:
            self.editor.screen = pygame.display.set_mode((self.editor.screen_width, self.editor.screen_height), pygame.RESIZABLE)

            # Save new dimensions to config
            from ..core.config_manager import get_config_manager
            config_manager = get_config_manager()
            config_manager.set_display_config(width=self.editor.screen_width, height=self.editor.screen_height)

        self.editor._update_ui_layout()

    def handle_grid_click(self, mouse_pos, mouse_button, is_drag=False):
        """Handle clicks on the grid with paint mode support."""
        if not self.editor.current_level:
            return

        # Convert screen coordinates to map coordinates
        cell_size = CELL_SIZE * self.editor.zoom_level
        map_start_x = self.editor.map_area_x + self.editor.scroll_x
        map_start_y = self.editor.map_area_y + self.editor.scroll_y

        grid_x = int((mouse_pos[0] - map_start_x) // cell_size)
        grid_y = int((mouse_pos[1] - map_start_y) // cell_size)

        # Check if click is within grid bounds
        if (0 <= grid_x < self.editor.current_level.width and
            0 <= grid_y < self.editor.current_level.height):

            # Avoid painting the same cell repeatedly during drag
            if is_drag and self.editor.last_painted_cell == (grid_x, grid_y):
                return

            self.editor.last_painted_cell = (grid_x, grid_y)

            # In test mode, handle player movement
            if self.editor.test_mode:
                if mouse_button == 1:  # Left click
                    player_x, player_y = self.editor.current_level.player_pos
                    dx = grid_x - player_x
                    dy = grid_y - player_y

                    # Only allow adjacent moves
                    if abs(dx) + abs(dy) == 1:
                        self.editor.current_level.move(dx, dy)
                return

            # In edit mode, place or clear elements
            if mouse_button == 1:  # Left click - place element
                self.editor._place_element(grid_x, grid_y)
            elif mouse_button == 3:  # Right click - always place floor
                self.editor._place_floor(grid_x, grid_y)

    def handle_palette_click(self, mouse_pos):
        """Handle clicks on the element palette."""
        # Calculate palette dimensions using the same logic as in draw_tool_panel
        # Find the Generate button to calculate spacing
        generate_button_bottom = 0
        for button in self.editor.buttons:
            if button.get('text') == 'Generate' and button.get('section') == 'tools':
                generate_button_bottom = button['rect'].y + button['rect'].height
                break

        # Calculate responsive palette dimensions based on screen size
        if self.editor.screen_width >= 1920 or self.editor.screen_height >= 1080:
            # High resolution
            palette_item_height = 52  # Increased height
            section_spacing = 80  # Increased spacing between sections
        elif self.editor.screen_width >= 1200 or self.editor.screen_height >= 800:
            # Medium resolution
            palette_item_height = 48  # Increased height
            section_spacing = 70  # Increased spacing between sections
        else:
            # Smaller resolutions
            palette_item_height = 44  # Increased height
            section_spacing = 60  # Increased spacing between sections

        # Calculate palette_start_y based on the Generate button position
        palette_start_y = generate_button_bottom + section_spacing

        for i, element in enumerate(self.editor.palette):
            y = palette_start_y + i * palette_item_height
            item_rect = pygame.Rect(self.editor.ui_margin + 5, y, self.editor.tool_panel_width - self.editor.ui_margin * 2 - 10, palette_item_height - 5)
            if item_rect.collidepoint(mouse_pos):
                self.editor.current_element = element['char']
                break

    def handle_slider_click(self, mouse_pos, slider):
        """Handle slider interaction."""
        if slider['rect'].collidepoint(mouse_pos):
            # Calculate new value based on mouse position
            relative_x = mouse_pos[0] - slider['rect'].x
            ratio = relative_x / slider['rect'].width
            ratio = max(0, min(1, ratio))  # Clamp to 0-1

            new_value = int(slider['min'] + ratio * (slider['max'] - slider['min']))
            if new_value != slider['value']:
                slider['value'] = new_value
                slider['callback'](new_value)

    def apply_text_input(self):
        """Apply the current text input to the active slider."""
        if not self.editor.active_text_field:
            return

        try:
            # Try to convert the text input to an integer
            value = int(self.editor.text_input)

            # Clamp the value to the slider's min and max
            value = max(self.editor.active_text_field['min'], min(self.editor.active_text_field['max'], value))

            # Update the slider's value
            if value != self.editor.active_text_field['value']:
                self.editor.active_text_field['value'] = value
                self.editor.active_text_field['callback'](value)
        except ValueError:
            # If the text input is not a valid integer, revert to the current value
            pass
