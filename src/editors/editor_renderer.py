"""
Editor Renderer delegate for the Enhanced Level Editor.

This module handles all drawing/rendering operations for the level editor,
including the tool panel, map area, grid, bottom panel, buttons, sliders,
help overlay, and metrics display.
"""

import pygame
from ..core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE


class EditorRenderer:
    """
    Handles all rendering/drawing for the EnhancedLevelEditor.

    Uses a back-reference to the editor instance to access shared state
    (screen, colors, fonts, buttons, sliders, current_level, etc.).
    """

    def __init__(self, editor):
        """
        Initialize the renderer with a back-reference to the editor.

        Args:
            editor: The EnhancedLevelEditor instance.
        """
        self.editor = editor

    def update_fonts(self):
        """Update fonts based on screen size."""
        # Responsive font sizing based on both width and height
        # This ensures better scaling for different aspect ratios
        base_dimension = min(self.editor.screen_width, self.editor.screen_height)

        # Scale font sizes based on screen dimensions
        if self.editor.screen_width >= 1920 or self.editor.screen_height >= 1080:
            # High resolution (e.g., 1920x1080)
            title_size = min(max(28, base_dimension // 25), 36)
            subtitle_size = min(max(24, base_dimension // 35), 30)
            text_size = min(max(20, base_dimension // 40), 24)
            small_size = min(max(16, base_dimension // 50), 20)
        elif self.editor.screen_width >= 1200 or self.editor.screen_height >= 800:
            # Medium resolution (e.g., 1200x800)
            title_size = min(max(26, base_dimension // 30), 32)
            subtitle_size = min(max(22, base_dimension // 40), 28)
            text_size = min(max(18, base_dimension // 45), 22)
            small_size = min(max(14, base_dimension // 55), 18)
        else:
            # Smaller resolutions
            title_size = min(max(24, base_dimension // 35), 28)
            subtitle_size = min(max(20, base_dimension // 45), 24)
            text_size = min(max(16, base_dimension // 50), 20)
            small_size = min(max(12, base_dimension // 60), 16)

        # Create fonts with the calculated sizes
        self.editor.title_font = pygame.font.Font(None, title_size)
        self.editor.subtitle_font = pygame.font.Font(None, subtitle_size)
        self.editor.text_font = pygame.font.Font(None, text_size)
        self.editor.small_font = pygame.font.Font(None, small_size)

        # Print font sizes for debugging
        print(f"Updated editor fonts - Title: {title_size}, Subtitle: {subtitle_size}, Text: {text_size}, Small: {small_size}")

    def draw_editor(self):
        """Draw the enhanced editor interface."""
        # Clear the screen
        self.editor.screen.fill(self.editor.colors['background'])

        # Draw tool panel
        self.draw_tool_panel()

        # Draw map area
        self.draw_map_area()

        # Draw bottom panel
        self.draw_bottom_panel()

        # Draw overlays
        if self.editor.show_help:
            self.draw_help_overlay()

        # Update the display
        pygame.display.flip()

    def draw_tool_panel(self):
        """Draw the improved tool panel on the left side."""
        # Left panel background
        left_panel_rect = pygame.Rect(0, 0, self.editor.tool_panel_width, self.editor.screen_height)
        pygame.draw.rect(self.editor.screen, self.editor.colors['panel'], left_panel_rect)
        pygame.draw.line(self.editor.screen, self.editor.colors['border'],
                        (self.editor.tool_panel_width, 0), (self.editor.tool_panel_width, self.editor.screen_height), 2)

        # Right panel background
        right_panel_x = self.editor.screen_width - self.editor.right_panel_width
        right_panel_rect = pygame.Rect(right_panel_x, 0, self.editor.right_panel_width, self.editor.screen_height)
        pygame.draw.rect(self.editor.screen, self.editor.colors['panel'], right_panel_rect)
        pygame.draw.line(self.editor.screen, self.editor.colors['border'],
                        (right_panel_x, 0), (right_panel_x, self.editor.screen_height), 2)

        # Left panel title - simple text without shadow
        title_text = "Level Editor"
        title_surface = self.editor.title_font.render(title_text, True, self.editor.colors['text'])
        self.editor.screen.blit(title_surface, (self.editor.ui_margin, 15))

        # Right panel title - simple text without shadow
        view_title_text = "View & Size"
        view_title_surface = self.editor.text_font.render(view_title_text, True, self.editor.colors['text'])
        self.editor.screen.blit(view_title_surface, (right_panel_x + self.editor.ui_margin, 15))

        # Store right_panel_x for use in other methods
        self.editor.right_panel_x = right_panel_x

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
            icon_size = 36  # Increased icon size
            icon_margin = 8
            text_offset_y = 15
            section_spacing = 80  # Increased spacing between sections
        elif self.editor.screen_width >= 1200 or self.editor.screen_height >= 800:
            # Medium resolution
            palette_item_height = 48  # Increased height
            icon_size = 34  # Increased icon size
            icon_margin = 7
            text_offset_y = 14
            section_spacing = 70  # Increased spacing between sections
        else:
            # Smaller resolutions
            palette_item_height = 44  # Increased height
            icon_size = 32  # Increased icon size
            icon_margin = 6
            text_offset_y = 12
            section_spacing = 60  # Increased spacing between sections

        # Calculate palette_start_y based on the Generate button position
        palette_start_y = generate_button_bottom + section_spacing

        # Draw a separator line between Generate button and Elements section
        separator_y = generate_button_bottom + section_spacing // 2
        pygame.draw.line(self.editor.screen, self.editor.colors['border'],
                        (self.editor.ui_margin, separator_y),
                        (self.editor.tool_panel_width - self.editor.ui_margin, separator_y), 2)

        # Element palette - better positioned with section title
        palette_title = self.editor.text_font.render("Elements:", True, self.editor.colors['text'])
        self.editor.screen.blit(palette_title, (self.editor.ui_margin + 5, palette_start_y - 25))

        # Draw palette items with responsive sizing
        for i, element in enumerate(self.editor.palette):
            y = palette_start_y + i * palette_item_height
            item_rect = pygame.Rect(self.editor.ui_margin + 5, y, self.editor.tool_panel_width - self.editor.ui_margin * 2 - 10, palette_item_height - 5)

            # Highlight selected element with gradient effect
            if element['char'] == self.editor.current_element:
                # Create gradient effect for selected item
                for j in range(item_rect.width):
                    # Calculate gradient color (yellow to white)
                    gradient_factor = j / item_rect.width
                    r = int(self.editor.colors['selected'][0] * (1 - gradient_factor) + 255 * gradient_factor)
                    g = int(self.editor.colors['selected'][1] * (1 - gradient_factor) + 255 * gradient_factor)
                    b = int(self.editor.colors['selected'][2] * (1 - gradient_factor) + 255 * gradient_factor)
                    pygame.draw.line(self.editor.screen, (r, g, b),
                                    (item_rect.x + j, item_rect.y),
                                    (item_rect.x + j, item_rect.y + item_rect.height))
            else:
                pygame.draw.rect(self.editor.screen, (255, 255, 255), item_rect)

            # Draw border with rounded corners
            pygame.draw.rect(self.editor.screen, self.editor.colors['border'], item_rect, 1, 5)

            # Draw element icon using skin manager
            icon_rect = pygame.Rect(item_rect.x + icon_margin, item_rect.y + (item_rect.height - icon_size) // 2,
                                   icon_size, icon_size)

            # Get the skin from the skin manager
            skin = self.editor.skin_manager.get_skin()

            # Draw the element using the skin
            if element['char'] in skin:
                # Scale the sprite to the icon size
                scaled_sprite = pygame.transform.scale(skin[element['char']], (icon_size, icon_size))
                self.editor.screen.blit(scaled_sprite, icon_rect)
            else:
                # Fallback to the hardcoded color if sprite not found
                pygame.draw.rect(self.editor.screen, element['color'], icon_rect)

            pygame.draw.rect(self.editor.screen, self.editor.colors['border'], icon_rect, 1)

            # Draw element name
            name_surface = self.editor.text_font.render(element['name'], True, self.editor.colors['text'])
            self.editor.screen.blit(name_surface, (item_rect.x + icon_size + icon_margin * 2,
                                          item_rect.y + text_offset_y))

        # Draw buttons
        for button in self.editor.buttons:
            if button['section'] in ['file', 'tools', 'right']:
                self.draw_button(button)

        # Draw sliders
        for slider in self.editor.sliders:
            self.draw_slider(slider)

        # Draw metrics panel in the right panel
        if hasattr(self.editor, 'metrics_y') and self.editor.current_level:
            self.draw_metrics_panel()

    def draw_map_area(self):
        """Draw the map area in the center with proper clipping."""
        if not self.editor.current_level:
            return

        # Map area background
        map_rect = pygame.Rect(self.editor.map_area_x, self.editor.map_area_y,
                              self.editor.map_area_width, self.editor.map_area_height)
        pygame.draw.rect(self.editor.screen, (255, 255, 255), map_rect)
        pygame.draw.rect(self.editor.screen, self.editor.colors['border'], map_rect, 2)

        # Set clipping to ensure content stays within the map area
        self.editor.screen.set_clip(map_rect)

        # Calculate cell size with zoom
        cell_size = int(CELL_SIZE * self.editor.zoom_level)

        # Calculate map position
        map_start_x = self.editor.map_area_x + self.editor.scroll_x
        map_start_y = self.editor.map_area_y + self.editor.scroll_y

        # Draw level elements
        skin = self.editor.skin_manager.get_skin()
        for y in range(self.editor.current_level.height):
            for x in range(self.editor.current_level.width):
                cell_x = map_start_x + x * cell_size
                cell_y = map_start_y + y * cell_size

                # Skip if cell is outside visible area (with clipping this is less critical)
                if (cell_x + cell_size < self.editor.map_area_x or
                    cell_x > self.editor.map_area_x + self.editor.map_area_width or
                    cell_y + cell_size < self.editor.map_area_y or
                    cell_y > self.editor.map_area_y + self.editor.map_area_height):
                    continue

                # Get cell character
                char = self.editor.current_level.get_display_char(x, y)

                # Draw cell
                if char in skin:
                    scaled_sprite = pygame.transform.scale(skin[char], (cell_size, cell_size))
                    self.editor.screen.blit(scaled_sprite, (cell_x, cell_y))

        # Draw grid if enabled (moved after drawing level elements to be in foreground)
        if self.editor.show_grid and self.editor.zoom_level >= 0.3:  # Show grid at lower zoom levels
            self.draw_grid(map_start_x, map_start_y, cell_size)

        # Update and render interactive highlighting
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos:
            # Set the appropriate mode for highlighting
            if self.editor.test_mode:
                self.editor.highlight_system.set_mode('test')
            elif self.editor.paint_mode:
                self.editor.highlight_system.set_mode('paint')
            else:
                self.editor.highlight_system.set_mode('edit')

            # Update highlight position based on mouse
            self.editor.highlight_system.update_mouse_position(
                mouse_pos, self.editor.map_area_x, self.editor.map_area_y,
                self.editor.map_area_width, self.editor.map_area_height,
                self.editor.current_level.width, self.editor.current_level.height,
                cell_size, self.editor.scroll_x, self.editor.scroll_y
            )

            # Render the highlight overlay with element preview
            self.editor.highlight_system.render_highlight(
                self.editor.screen, self.editor.map_area_x, self.editor.map_area_y, cell_size,
                self.editor.scroll_x, self.editor.scroll_y, self.editor.current_element, self.editor.skin_manager
            )

        # Remove clipping
        self.editor.screen.set_clip(None)

    def draw_grid(self, start_x, start_y, cell_size):
        """Draw grid lines between tiles using color from config."""
        # Get grid color from config
        grid_color_list = self.editor.config_manager.get('game', 'grid_color', [255, 255, 255])
        grid_color = tuple(grid_color_list)

        # Vertical lines - draw between tiles
        for x in range(self.editor.current_level.width + 1):
            line_x = start_x + x * cell_size
            if self.editor.map_area_x <= line_x <= self.editor.map_area_x + self.editor.map_area_width:
                pygame.draw.line(self.editor.screen, grid_color,
                               (line_x, max(self.editor.map_area_y, start_y)),
                               (line_x, min(self.editor.map_area_y + self.editor.map_area_height,
                                          start_y + self.editor.current_level.height * cell_size)), 2)

        # Horizontal lines - draw between tiles
        for y in range(self.editor.current_level.height + 1):
            line_y = start_y + y * cell_size
            if self.editor.map_area_y <= line_y <= self.editor.map_area_y + self.editor.map_area_height:
                pygame.draw.line(self.editor.screen, grid_color,
                               (max(self.editor.map_area_x, start_x), line_y),
                               (min(self.editor.map_area_x + self.editor.map_area_width,
                                   start_x + self.editor.current_level.width * cell_size), line_y), 2)

    def draw_bottom_panel(self):
        """Draw the improved bottom panel with status and controls."""
        # Panel background
        panel_rect = pygame.Rect(0, self.editor.screen_height - self.editor.bottom_panel_height,
                                self.editor.screen_width, self.editor.bottom_panel_height)
        pygame.draw.rect(self.editor.screen, self.editor.colors['panel'], panel_rect)
        pygame.draw.line(self.editor.screen, self.editor.colors['border'],
                        (0, self.editor.screen_height - self.editor.bottom_panel_height),
                        (self.editor.screen_width, self.editor.screen_height - self.editor.bottom_panel_height), 2)

        # Status information - positioned to avoid button overlap
        status_y = self.editor.screen_height - self.editor.bottom_panel_height + 45  # Moved down to avoid button overlap
        status_lines = [
            f"Mode: {'Test' if self.editor.test_mode else 'Edit'}",
            f"Element: {next((e['name'] for e in self.editor.palette if e['char'] == self.editor.current_element), 'None')}",
            f"Zoom: {self.editor.zoom_level:.1f}x",
            f"Grid: {'On' if self.editor.show_grid else 'Off'}",
            f"Unsaved: {'Yes' if self.editor.unsaved_changes else 'No'}"
        ]

        # Calculate spacing to distribute status info evenly, avoiding button areas
        available_width = self.editor.screen_width - 300  # Leave more space for buttons
        status_spacing = available_width // len(status_lines)

        for i, line in enumerate(status_lines):
            status_surface = self.editor.small_font.render(line, True, self.editor.colors['text'])
            x_pos = self.editor.ui_margin + i * status_spacing
            self.editor.screen.blit(status_surface, (x_pos, status_y))

        # Draw bottom buttons
        for button in self.editor.buttons:
            if button['section'] == 'bottom':
                self.draw_button(button)

    def draw_button(self, button):
        """Draw a button with enhanced visual effects."""
        is_hovered = button['rect'].collidepoint(pygame.mouse.get_pos())

        # Determine button color based on hover state
        base_color = self.editor.colors['button_hover'] if is_hovered else self.editor.colors['button']

        # Create gradient effect
        for i in range(button['rect'].height):
            # Calculate gradient color (darker at bottom)
            gradient_factor = i / button['rect'].height
            if is_hovered:
                # Brighter gradient for hover state
                r = min(255, int(base_color[0] * (1.1 - gradient_factor * 0.3)))
                g = min(255, int(base_color[1] * (1.1 - gradient_factor * 0.3)))
                b = min(255, int(base_color[2] * (1.1 - gradient_factor * 0.3)))
            else:
                # Normal gradient
                r = int(base_color[0] * (1 - gradient_factor * 0.4))
                g = int(base_color[1] * (1 - gradient_factor * 0.4))
                b = int(base_color[2] * (1 - gradient_factor * 0.4))

            # Draw horizontal line with gradient color
            pygame.draw.line(self.editor.screen, (r, g, b),
                           (button['rect'].x, button['rect'].y + i),
                           (button['rect'].x + button['rect'].width, button['rect'].y + i))

        # Draw button border with rounded corners
        border_color = (180, 180, 220) if is_hovered else self.editor.colors['border']
        pygame.draw.rect(self.editor.screen, border_color, button['rect'], 2, 5)

        # Draw button text with shadow for better visibility
        shadow_offset = 1
        shadow_color = (30, 30, 50, 128)

        # Use appropriate font based on button section
        if button['section'] == 'bottom':
            font = self.editor.small_font
        else:
            font = self.editor.text_font

        # Draw text shadow
        text_shadow = font.render(button['text'], True, shadow_color)
        text_shadow_rect = text_shadow.get_rect(center=(button['rect'].centerx + shadow_offset,
                                                      button['rect'].centery + shadow_offset))
        self.editor.screen.blit(text_shadow, text_shadow_rect)

        # Draw main text
        text_surface = font.render(button['text'], True, self.editor.colors['button_text'])
        text_rect = text_surface.get_rect(center=button['rect'].center)
        self.editor.screen.blit(text_surface, text_rect)

    def draw_slider(self, slider):
        """Draw a slider with enhanced visual effects and text input field."""
        # Draw label without shadow
        label_text = f"{slider['label']}:"
        label_surface = self.editor.text_font.render(label_text, True, self.editor.colors['text'])
        self.editor.screen.blit(label_surface, (slider['rect'].x, slider['rect'].y - 25))

        # Draw text input field if this slider has one
        if slider.get('text_field'):
            # Calculate text field position (to the right of the label)
            label_width = self.editor.text_font.size(label_text)[0]
            text_field_x = slider['rect'].x + label_width + 10
            text_field_y = slider['rect'].y - 25
            text_field_width = 50
            text_field_height = 22

            # Draw text field background
            text_field_rect = pygame.Rect(text_field_x, text_field_y, text_field_width, text_field_height)
            text_field_color = (255, 255, 255)  # White background

            # Highlight if this is the active text field
            if self.editor.active_text_field == slider:
                pygame.draw.rect(self.editor.screen, (220, 220, 255), text_field_rect)  # Light blue highlight
            else:
                pygame.draw.rect(self.editor.screen, text_field_color, text_field_rect)

            # Draw border
            pygame.draw.rect(self.editor.screen, self.editor.colors['border'], text_field_rect, 1)

            # Draw text
            if self.editor.active_text_field == slider:
                # Show current text input with cursor
                display_text = self.editor.text_input
                if self.editor.text_input_cursor_visible:
                    display_text += "|"  # Simple cursor
            else:
                # Show current value
                display_text = str(slider['value'])

            text_surface = self.editor.text_font.render(display_text, True, self.editor.colors['text'])
            # Center text vertically and align left horizontally with padding
            text_x = text_field_x + 5
            text_y = text_field_y + (text_field_height - text_surface.get_height()) // 2
            self.editor.screen.blit(text_surface, (text_x, text_y))

        # Slider track with gradient and rounded corners
        track_rect = pygame.Rect(slider['rect'])
        track_radius = min(5, slider['rect'].height // 2)

        # Draw track background with gradient
        for i in range(track_rect.height):
            # Calculate gradient color (lighter at top, darker at bottom)
            gradient_factor = i / track_rect.height
            r = int(220 - gradient_factor * 40)
            g = int(220 - gradient_factor * 40)
            b = int(220 - gradient_factor * 40)

            # Draw horizontal line with gradient color
            pygame.draw.line(self.editor.screen, (r, g, b),
                           (track_rect.x + track_radius, track_rect.y + i),
                           (track_rect.x + track_rect.width - track_radius, track_rect.y + i))

            # Draw rounded ends
            if i < track_radius or i >= track_rect.height - track_radius:
                continue

            # Left rounded end
            pygame.draw.line(self.editor.screen, (r, g, b),
                           (track_rect.x, track_rect.y + i),
                           (track_rect.x + track_radius, track_rect.y + i))

            # Right rounded end
            pygame.draw.line(self.editor.screen, (r, g, b),
                           (track_rect.x + track_rect.width - track_radius, track_rect.y + i),
                           (track_rect.x + track_rect.width, track_rect.y + i))

        # Draw track border with rounded corners
        pygame.draw.rect(self.editor.screen, self.editor.colors['border'], track_rect, 1, track_radius)

        # Calculate filled portion of track (progress)
        handle_pos = (slider['value'] - slider['min']) / (slider['max'] - slider['min'])
        progress_width = int(handle_pos * track_rect.width)

        # Draw progress indicator (subtle)
        progress_rect = pygame.Rect(track_rect.x, track_rect.y, progress_width, track_rect.height)
        progress_color = (180, 180, 220, 128)  # Semi-transparent blue
        pygame.draw.rect(self.editor.screen, progress_color, progress_rect, 0, track_radius)

        # Slider handle with enhanced styling
        handle_width = max(14, slider['rect'].height)
        handle_height = slider['rect'].height + 8
        handle_x = slider['rect'].x + handle_pos * (slider['rect'].width - handle_width)
        handle_y = slider['rect'].y - 4
        handle_rect = pygame.Rect(handle_x, handle_y, handle_width, handle_height)

        # Draw handle with gradient
        for i in range(handle_rect.height):
            # Calculate gradient color
            gradient_factor = i / handle_rect.height
            r = int(self.editor.colors['button'][0] * (1 - gradient_factor * 0.3))
            g = int(self.editor.colors['button'][1] * (1 - gradient_factor * 0.3))
            b = int(self.editor.colors['button'][2] * (1 - gradient_factor * 0.3))

            # Draw horizontal line with gradient color
            pygame.draw.line(self.editor.screen, (r, g, b),
                           (handle_rect.x, handle_rect.y + i),
                           (handle_rect.x + handle_rect.width, handle_rect.y + i))

        # Draw handle border with rounded corners
        pygame.draw.rect(self.editor.screen, self.editor.colors['border'], handle_rect, 1, 5)

    def draw_help_overlay(self):
        """Draw the help overlay with responsive sizing and enhanced visuals."""
        # Semi-transparent overlay with blur effect simulation
        overlay = pygame.Surface((self.editor.screen_width, self.editor.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.editor.screen.blit(overlay, (0, 0))

        # Calculate responsive help panel dimensions
        if self.editor.screen_width >= 1920 or self.editor.screen_height >= 1080:
            # High resolution
            help_width = 700
            help_height = 600
            title_padding = 50
            content_padding = 40
            line_spacing = 28
        elif self.editor.screen_width >= 1200 or self.editor.screen_height >= 800:
            # Medium resolution
            help_width = 650
            help_height = 550
            title_padding = 45
            content_padding = 35
            line_spacing = 25
        else:
            # Smaller resolutions
            help_width = 600
            help_height = 500
            title_padding = 40
            content_padding = 30
            line_spacing = 22

        # Center the help panel
        help_x = (self.editor.screen_width - help_width) // 2
        help_y = (self.editor.screen_height - help_height) // 2

        # Draw panel with shadow effect
        shadow_offset = 8
        shadow_rect = pygame.Rect(help_x + shadow_offset, help_y + shadow_offset, help_width, help_height)
        pygame.draw.rect(self.editor.screen, (20, 20, 20, 100), shadow_rect, 0, 10)

        # Main panel with gradient background
        help_rect = pygame.Rect(help_x, help_y, help_width, help_height)

        # Draw gradient background
        for i in range(help_height):
            # Calculate gradient color (lighter at top, darker at bottom)
            gradient_factor = i / help_height
            r = int(240 - gradient_factor * 20)
            g = int(240 - gradient_factor * 20)
            b = int(250 - gradient_factor * 10)  # Slightly blue tint

            pygame.draw.line(self.editor.screen, (r, g, b),
                           (help_x, help_y + i),
                           (help_x + help_width, help_y + i))

        # Draw border with rounded corners
        pygame.draw.rect(self.editor.screen, self.editor.colors['border'], help_rect, 2, 10)

        # Help text content
        help_lines = [
            "Enhanced Level Editor Help",
            "",
            "Mouse Controls:",
            "• Left Click: Place selected element",
            "• Right Click: Place floor (erase)",
            "• Middle Click + Drag: Pan view",
            "• Mouse Wheel: Zoom in/out",
            "",
            "Keyboard Shortcuts:",
            "• G: Toggle grid",
            "• T: Toggle test mode",
            "• H: Toggle help",
            "• M: Toggle metrics",
            "• Arrow Keys: Scroll map (in edit mode)",
            "• WASD: Move player (in test mode)",
            "• Escape: Exit test mode or editor",
            "",
            "Features:",
            "• Auto-fit zoom on level creation",
            "• White grid lines for visibility",
            "• Complete state restoration in test mode",
            "• Right-click always places floor",
            "",
            "Press any key to close help"
        ]

        # Draw title with shadow effect
        title_line = help_lines[0]
        shadow_color = (50, 50, 100)
        shadow_offset = 2

        # Draw title shadow
        title_shadow = self.editor.title_font.render(title_line, True, shadow_color)
        title_shadow_rect = title_shadow.get_rect(center=(help_x + help_width // 2 + shadow_offset,
                                                       help_y + title_padding + shadow_offset))
        self.editor.screen.blit(title_shadow, title_shadow_rect)

        # Draw main title
        title_surface = self.editor.title_font.render(title_line, True, (0, 100, 200))
        title_rect = title_surface.get_rect(center=(help_x + help_width // 2, help_y + title_padding))
        self.editor.screen.blit(title_surface, title_rect)

        # Draw help content with section highlighting
        content_y = help_y + title_padding * 2
        current_section = None

        for i, line in enumerate(help_lines[1:], 1):  # Skip title which we already rendered
            if line == "":
                content_y += line_spacing // 2  # Less space for empty lines
                continue

            # Determine if this is a section header
            is_section = line.endswith(':')

            if is_section:
                current_section = line
                # Draw section header with highlight
                section_surface = self.editor.subtitle_font.render(line, True, (80, 80, 180))
                self.editor.screen.blit(section_surface, (help_x + content_padding, content_y))
                content_y += line_spacing + 5  # Extra space after section header
            else:
                # Regular content line
                # Draw with shadow for better readability
                shadow_offset = 1
                text_shadow = self.editor.text_font.render(line, True, (50, 50, 50, 128))
                self.editor.screen.blit(text_shadow, (help_x + content_padding + shadow_offset,
                                             content_y + shadow_offset))

                # Main text
                text_surface = self.editor.text_font.render(line, True, self.editor.colors['text'])
                self.editor.screen.blit(text_surface, (help_x + content_padding, content_y))
                content_y += line_spacing

    def draw_metrics_overlay(self):
        """Draw the metrics overlay with current level information and enhanced visuals."""
        if not self.editor.current_level:
            return

        # Calculate responsive metrics panel dimensions
        if self.editor.screen_width >= 1920 or self.editor.screen_height >= 1080:
            # High resolution
            metrics_width = 350
            metrics_height = 450
            title_padding = 40
            content_padding = 30
            line_spacing = 28
            margin = 30
        elif self.editor.screen_width >= 1200 or self.editor.screen_height >= 800:
            # Medium resolution
            metrics_width = 320
            metrics_height = 420
            title_padding = 35
            content_padding = 25
            line_spacing = 25
            margin = 25
        else:
            # Smaller resolutions
            metrics_width = 300
            metrics_height = 400
            title_padding = 30
            content_padding = 20
            line_spacing = 22
            margin = 20

        # Position panel on the right side
        metrics_x = self.editor.screen_width - metrics_width - margin
        metrics_y = 100

        # Draw panel with shadow effect
        shadow_offset = 8
        shadow_rect = pygame.Rect(metrics_x + shadow_offset, metrics_y + shadow_offset, metrics_width, metrics_height)
        pygame.draw.rect(self.editor.screen, (20, 20, 20, 100), shadow_rect, 0, 10)

        # Main panel with gradient background
        metrics_rect = pygame.Rect(metrics_x, metrics_y, metrics_width, metrics_height)

        # Draw gradient background
        for i in range(metrics_height):
            # Calculate gradient color (darker at top, lighter at bottom)
            gradient_factor = i / metrics_height
            r = int(40 + gradient_factor * 40)
            g = int(40 + gradient_factor * 40)
            b = int(80 + gradient_factor * 40)  # Blue tint

            pygame.draw.line(self.editor.screen, (r, g, b),
                           (metrics_x, metrics_y + i),
                           (metrics_x + metrics_width, metrics_y + i))

        # Draw border with rounded corners
        pygame.draw.rect(self.editor.screen, self.editor.colors['border'], metrics_rect, 2, 10)

        # Draw title with shadow effect
        title_text = "Level Metrics"
        shadow_color = (20, 20, 50)
        shadow_offset = 2

        # Draw title shadow
        title_shadow = self.editor.title_font.render(title_text, True, shadow_color)
        title_shadow_rect = title_shadow.get_rect(center=(metrics_x + metrics_width // 2 + shadow_offset,
                                                       metrics_y + title_padding + shadow_offset))
        self.editor.screen.blit(title_shadow, title_shadow_rect)

        # Draw main title
        title_surface = self.editor.title_font.render(title_text, True, (180, 180, 255))
        title_rect = title_surface.get_rect(center=(metrics_x + metrics_width // 2, metrics_y + title_padding))
        self.editor.screen.blit(title_surface, title_rect)

        # Calculate level statistics
        wall_count = sum(row.count(WALL) for row in self.editor.current_level.map_data)
        floor_count = sum(row.count(FLOOR) for row in self.editor.current_level.map_data)
        total_cells = self.editor.current_level.width * self.editor.current_level.height

        # Check if level is valid
        is_valid = (len(self.editor.current_level.boxes) == len(self.editor.current_level.targets) and
                   len(self.editor.current_level.boxes) > 0 and
                   self.editor.current_level.player_pos != (0, 0))

        # Metrics content with sections
        metrics_sections = [
            {
                'title': 'Level Size',
                'items': [
                    f"Dimensions: {self.editor.current_level.width}x{self.editor.current_level.height}",
                    f"Total cells: {total_cells}"
                ]
            },
            {
                'title': 'Elements',
                'items': [
                    f"Walls: {wall_count}",
                    f"Floors: {floor_count}",
                    f"Boxes: {len(self.editor.current_level.boxes)}",
                    f"Targets: {len(self.editor.current_level.targets)}",
                    f"Player: {'Set' if self.editor.current_level.player_pos != (0, 0) else 'Not set'}"
                ]
            },
            {
                'title': 'View',
                'items': [
                    f"Zoom: {self.editor.zoom_level:.2f}x",
                    f"Grid: {'On' if self.editor.show_grid else 'Off'}"
                ]
            },
            {
                'title': 'Status',
                'items': [
                    f"Valid: {'Yes' if is_valid else 'No'}",
                    f"Mode: {'Test' if self.editor.test_mode else 'Edit'}"
                ]
            }
        ]

        # Draw metrics content with section highlighting
        content_y = metrics_y + title_padding * 2

        for section in metrics_sections:
            # Draw section title
            section_title = section['title']
            section_color = (180, 180, 255)  # Light blue

            # Draw section title with shadow
            shadow_offset = 1
            section_shadow = self.editor.subtitle_font.render(section_title, True, shadow_color)
            self.editor.screen.blit(section_shadow, (metrics_x + content_padding + shadow_offset,
                                           content_y + shadow_offset))

            section_surface = self.editor.subtitle_font.render(section_title, True, section_color)
            self.editor.screen.blit(section_surface, (metrics_x + content_padding, content_y))

            content_y += line_spacing

            # Draw section items
            for item in section['items']:
                # Determine if this is a status item that needs highlighting
                highlight = False
                if "Valid: No" in item:
                    text_color = (255, 100, 100)  # Red for invalid
                    highlight = True
                elif "Valid: Yes" in item:
                    text_color = (100, 255, 100)  # Green for valid
                    highlight = True
                else:
                    text_color = (220, 220, 220)  # Default light color

                # Draw item text with shadow for better readability
                text_shadow = self.editor.text_font.render(item, True, (0, 0, 0, 150))
                self.editor.screen.blit(text_shadow, (metrics_x + content_padding + 10 + shadow_offset,
                                             content_y + shadow_offset))

                # Draw main text
                text_surface = self.editor.text_font.render(item, True, text_color)
                self.editor.screen.blit(text_surface, (metrics_x + content_padding + 10, content_y))

                # Draw highlight indicator for important items
                if highlight:
                    indicator_rect = pygame.Rect(metrics_x + content_padding, content_y + 2,
                                               5, self.editor.text_font.get_height() - 4)
                    pygame.draw.rect(self.editor.screen, text_color, indicator_rect)

                content_y += line_spacing

            # Add space between sections
            content_y += line_spacing // 2

    def draw_metrics_panel(self):
        """Draw the metrics content in the right panel."""
        if not self.editor.current_level:
            return

        # Calculate responsive metrics panel dimensions based on screen size
        if self.editor.screen_width >= 1920 or self.editor.screen_height >= 1080:
            # High resolution
            title_padding = 25
            content_padding = 20
            line_spacing = 24
        elif self.editor.screen_width >= 1200 or self.editor.screen_height >= 800:
            # Medium resolution
            title_padding = 20
            content_padding = 15
            line_spacing = 20
        else:
            # Smaller resolutions
            title_padding = 15
            content_padding = 10
            line_spacing = 18

        # Draw a separator line above the metrics section
        separator_y = self.editor.metrics_y - title_padding
        pygame.draw.line(self.editor.screen, self.editor.colors['border'],
                        (self.editor.right_panel_x + self.editor.ui_margin, separator_y),
                        (self.editor.right_panel_x + self.editor.right_panel_width - self.editor.ui_margin, separator_y), 2)

        # Draw metrics title
        metrics_title = self.editor.text_font.render("Level Metrics", True, self.editor.colors['text'])
        self.editor.screen.blit(metrics_title, (self.editor.right_panel_x + self.editor.ui_margin, self.editor.metrics_y))

        # Calculate level statistics
        wall_count = sum(row.count(WALL) for row in self.editor.current_level.map_data)
        floor_count = sum(row.count(FLOOR) for row in self.editor.current_level.map_data)
        total_cells = self.editor.current_level.width * self.editor.current_level.height

        # Check if level is valid
        is_valid = (len(self.editor.current_level.boxes) == len(self.editor.current_level.targets) and
                   len(self.editor.current_level.boxes) > 0 and
                   self.editor.current_level.player_pos != (0, 0))

        # Metrics content with sections
        metrics_sections = [
            {
                'title': 'Level Size',
                'items': [
                    f"Dimensions: {self.editor.current_level.width}x{self.editor.current_level.height}",
                    f"Total cells: {total_cells}"
                ]
            },
            {
                'title': 'Elements',
                'items': [
                    f"Walls: {wall_count}",
                    f"Floors: {floor_count}",
                    f"Boxes: {len(self.editor.current_level.boxes)}",
                    f"Targets: {len(self.editor.current_level.targets)}",
                    f"Player: {'Set' if self.editor.current_level.player_pos != (0, 0) else 'Not set'}"
                ]
            },
            {
                'title': 'View',
                'items': [
                    f"Zoom: {self.editor.zoom_level:.2f}x",
                    f"Grid: {'On' if self.editor.show_grid else 'Off'}"
                ]
            },
            {
                'title': 'Status',
                'items': [
                    f"Valid: {'Yes' if is_valid else 'No'}",
                    f"Mode: {'Test' if self.editor.test_mode else 'Edit'}"
                ]
            }
        ]

        # Draw metrics content
        content_y = self.editor.metrics_y + title_padding + 5

        for section in metrics_sections:
            # Draw section title
            section_title = section['title']
            section_color = (100, 100, 200)  # Light blue

            section_surface = self.editor.text_font.render(section_title, True, section_color)
            self.editor.screen.blit(section_surface, (self.editor.right_panel_x + self.editor.ui_margin, content_y))

            content_y += line_spacing

            # Draw section items
            for item in section['items']:
                # Determine if this is a status item that needs highlighting
                if "Valid: No" in item:
                    text_color = (255, 100, 100)  # Red for invalid
                elif "Valid: Yes" in item:
                    text_color = (100, 255, 100)  # Green for valid
                else:
                    text_color = self.editor.colors['text']  # Default color

                # Draw item text
                text_surface = self.editor.small_font.render(item, True, text_color)
                self.editor.screen.blit(text_surface, (self.editor.right_panel_x + self.editor.ui_margin + content_padding, content_y))

                content_y += line_spacing

            # Add space between sections
            content_y += line_spacing // 2
