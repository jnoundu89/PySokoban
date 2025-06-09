"""
Enhanced Level Editor for the Sokoban game.

This module provides an improved GUI-based level editor with advanced features:
- Paint mode (click and drag)
- Responsive interface with specialized tool sections
- Grid toggle functionality
- Zoom and scroll capabilities
- Centered map with tools around
- Size sliders for map creation
- Better popup handling
"""

import os
import sys
import pygame
import math
from ..core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE, TITLE
from ..core.level import Level
from ..level_management.level_manager import LevelManager
from ..ui.skins.enhanced_skin_manager import EnhancedSkinManager
from ..generation.procedural_generator import ProceduralGenerator
from ..core.auto_solver import AutoSolver

class EnhancedLevelEditor:
    """
    Enhanced class for creating and editing Sokoban levels with improved interface.
    """

    def __init__(self, levels_dir='levels', screen=None):
        """
        Initialize the enhanced level editor.

        Args:
            levels_dir (str, optional): Directory containing level files.
            screen (pygame.Surface, optional): Existing pygame surface to use.
        """
        # Only initialize pygame if not already initialized
        if not pygame.get_init():
            pygame.init()

        # Initialize window
        self.screen_width = 1200
        self.screen_height = 800

        # Use existing screen if provided, otherwise create a new one
        if screen is not None:
            self.screen = screen
            self.screen_width, self.screen_height = self.screen.get_size()
            self.using_shared_screen = True
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
            pygame.display.set_caption(f"{TITLE} - Enhanced Level Editor")
            self.using_shared_screen = False

        # Initialize managers
        self.levels_dir = levels_dir
        self.level_manager = LevelManager(levels_dir)
        self.skin_manager = EnhancedSkinManager()

        # Check if levels directory exists, create it if not
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)

        # Editor state
        self.current_level = None
        self.current_element = WALL
        self.unsaved_changes = False
        self.show_help = False
        self.show_grid = True
        self.show_metrics = False
        self.test_mode = False
        self.player_pos_in_test = None
        self.initial_level_state = None  # Store initial state for test mode reset
        self.running = False
        self.exit_requested = False  # Flag to indicate if exit was requested

        # Mouse drag for panning
        self.mouse_dragging = False
        self.drag_start_pos = None
        self.drag_start_scroll = None

        # Paint mode (click and drag)
        self.paint_mode = False
        self.last_painted_cell = None

        # Zoom and scroll
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        self.scroll_x = 0
        self.scroll_y = 0

        # Map dimensions
        self.map_width = 20
        self.map_height = 15
        self.min_map_size = 5
        self.max_map_size = 50

        # UI Layout - improved responsive design
        self.ui_margin = 15
        self.tool_panel_width = 280  # Increased width for better spacing
        self.right_panel_width = 200  # New right panel for additional tools
        self.bottom_panel_height = 80  # Reduced height for more map space

        # Calculate map area (centered and larger)
        self.map_area_x = self.tool_panel_width + self.ui_margin
        self.map_area_y = self.ui_margin
        self.map_area_width = self.screen_width - self.tool_panel_width - self.right_panel_width - self.ui_margin * 3
        self.map_area_height = self.screen_height - self.bottom_panel_height - self.ui_margin * 2

        # Element palette
        self.palette = [
            {'char': WALL, 'name': 'Wall', 'color': (100, 100, 100)},
            {'char': FLOOR, 'name': 'Floor', 'color': (220, 220, 220)},
            {'char': PLAYER, 'name': 'Player', 'color': (0, 100, 255)},
            {'char': BOX, 'name': 'Box', 'color': (139, 69, 19)},
            {'char': TARGET, 'name': 'Target', 'color': (255, 0, 0)}
        ]

        # UI Elements
        self.buttons = []
        self.sliders = []
        self._create_ui_elements()

        # Colors
        self.colors = {
            'background': (240, 240, 240),
            'panel': (220, 220, 220),
            'grid': (180, 180, 180),
            'text': (50, 50, 50),
            'button': (100, 100, 200),
            'button_hover': (130, 130, 255),
            'button_text': (255, 255, 255),
            'selected': (255, 255, 0),
            'border': (100, 100, 100)
        }

        # Fonts - responsive sizing based on screen dimensions
        self._update_fonts()

        # Create a new empty level by default
        self._create_new_level(self.map_width, self.map_height)

    def _create_ui_elements(self):
        """Create UI elements (buttons, sliders, etc.) with improved spacing."""
        self.buttons = []
        self.sliders = []

        # Calculate responsive button dimensions based on screen size
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution (e.g., 1920x1080)
            button_height = 38
            small_button_height = 30
            spacing = 45
            section_spacing = 60
            bottom_button_width = 100
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            # Medium resolution (e.g., 1200x800)
            button_height = 34
            small_button_height = 28
            spacing = 40
            section_spacing = 50
            bottom_button_width = 90
        else:
            # Smaller resolutions
            button_height = 30
            small_button_height = 25
            spacing = 36
            section_spacing = 45
            bottom_button_width = 80

        # Left panel buttons with better spacing
        button_width = self.tool_panel_width - 30
        button_x = self.ui_margin
        start_y = 50

        # File operations section
        file_section_y = start_y
        self.buttons.extend([
            {'rect': pygame.Rect(button_x, file_section_y, button_width, button_height),
             'text': 'New Level', 'action': self._show_new_level_dialog, 'section': 'file'},
            {'rect': pygame.Rect(button_x, file_section_y + spacing, button_width, button_height),
             'text': 'Open Level', 'action': self._show_open_level_dialog, 'section': 'file'},
            {'rect': pygame.Rect(button_x, file_section_y + spacing * 2, button_width, button_height),
             'text': 'Save Level', 'action': self._show_save_level_dialog, 'section': 'file'},
        ])

        # Tools section - with proper spacing between sections
        tools_section_y = file_section_y + spacing * 2 + section_spacing
        self.buttons.extend([
            {'rect': pygame.Rect(button_x, tools_section_y, button_width, button_height),
             'text': 'Test Level', 'action': self._toggle_test_mode, 'section': 'tools'},
            {'rect': pygame.Rect(button_x, tools_section_y + spacing, button_width, button_height),
             'text': 'Validate', 'action': self._validate_level, 'section': 'tools'},
            {'rect': pygame.Rect(button_x, tools_section_y + spacing * 2, button_width, button_height),
             'text': 'Solve Level', 'action': self._solve_level, 'section': 'tools'},
            {'rect': pygame.Rect(button_x, tools_section_y + spacing * 3, button_width, button_height),
             'text': 'Generate', 'action': self._show_generate_dialog, 'section': 'tools'},
        ])

        # View controls section - moved to right panel
        right_panel_x = self.screen_width - self.right_panel_width + self.ui_margin
        view_section_y = start_y
        view_button_width = self.right_panel_width - self.ui_margin * 2

        self.buttons.extend([
            {'rect': pygame.Rect(right_panel_x, view_section_y, view_button_width, button_height),
             'text': 'Toggle Grid', 'action': self._toggle_grid, 'section': 'right'},
            {'rect': pygame.Rect(right_panel_x, view_section_y + spacing, view_button_width // 2 - 5, button_height),
             'text': 'Zoom In', 'action': self._zoom_in, 'section': 'right'},
            {'rect': pygame.Rect(right_panel_x + view_button_width // 2 + 5, view_section_y + spacing, view_button_width // 2 - 5, button_height),
             'text': 'Zoom Out', 'action': self._zoom_out, 'section': 'right'},
            {'rect': pygame.Rect(right_panel_x, view_section_y + spacing * 2, view_button_width, button_height),
             'text': 'Reset View', 'action': self._reset_view, 'section': 'right'},
        ])

        # Bottom panel buttons - evenly distributed
        bottom_y = self.screen_height - self.bottom_panel_height + (self.bottom_panel_height - small_button_height) // 2

        # Calculate button spacing to distribute evenly
        available_width = self.screen_width - 2 * self.ui_margin - 3 * bottom_button_width
        button_spacing = available_width // 4  # Divide remaining space

        self.buttons.extend([
            {'rect': pygame.Rect(self.ui_margin, bottom_y, bottom_button_width, small_button_height),
             'text': 'Help', 'action': self._toggle_help, 'section': 'bottom'},
            {'rect': pygame.Rect(self.ui_margin + bottom_button_width + button_spacing, bottom_y, bottom_button_width, small_button_height),
             'text': 'Metrics', 'action': self._toggle_metrics, 'section': 'bottom'},
            {'rect': pygame.Rect(self.screen_width - self.ui_margin - bottom_button_width, bottom_y, bottom_button_width, small_button_height),
             'text': 'Exit', 'action': self._exit_editor, 'section': 'bottom'}
        ])

        # Size sliders - moved to right panel with proper spacing
        slider_y = view_section_y + spacing * 3 + section_spacing
        slider_width = view_button_width
        slider_height = max(18, button_height // 2)  # Responsive slider height

        self.sliders = [
            {'rect': pygame.Rect(right_panel_x, slider_y, slider_width, slider_height),
             'label': 'Width', 'value': self.map_width, 'min': self.min_map_size, 'max': self.max_map_size,
             'callback': self._on_width_change},
            {'rect': pygame.Rect(right_panel_x, slider_y + spacing, slider_width, slider_height),
             'label': 'Height', 'value': self.map_height, 'min': self.min_map_size, 'max': self.max_map_size,
             'callback': self._on_height_change}
        ]

    def _update_fonts(self):
        """Update fonts based on screen size."""
        # Responsive font sizing based on both width and height
        # This ensures better scaling for different aspect ratios
        base_dimension = min(self.screen_width, self.screen_height)

        # Scale font sizes based on screen dimensions
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution (e.g., 1920x1080)
            title_size = min(max(28, base_dimension // 25), 36)
            text_size = min(max(20, base_dimension // 40), 24)
            small_size = min(max(16, base_dimension // 50), 20)
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            # Medium resolution (e.g., 1200x800)
            title_size = min(max(26, base_dimension // 30), 32)
            text_size = min(max(18, base_dimension // 45), 22)
            small_size = min(max(14, base_dimension // 55), 18)
        else:
            # Smaller resolutions
            title_size = min(max(24, base_dimension // 35), 28)
            text_size = min(max(16, base_dimension // 50), 20)
            small_size = min(max(12, base_dimension // 60), 16)

        # Create fonts with the calculated sizes
        self.title_font = pygame.font.Font(None, title_size)
        self.text_font = pygame.font.Font(None, text_size)
        self.small_font = pygame.font.Font(None, small_size)

        # Print font sizes for debugging
        print(f"Updated editor fonts - Title: {title_size}, Text: {text_size}, Small: {small_size}")

    def _update_ui_layout(self):
        """Update UI layout when screen is resized."""
        # Update fonts first
        self._update_fonts()

        # Adjust panel dimensions based on screen size
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution (e.g., 1920x1080)
            self.tool_panel_width = 320  # Wider panel for high-res
            self.right_panel_width = 240  # Wider right panel
            self.bottom_panel_height = 90  # Taller bottom panel
            self.ui_margin = 20  # Larger margins
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            # Medium resolution (e.g., 1200x800)
            self.tool_panel_width = 280  # Standard panel width
            self.right_panel_width = 200  # Standard right panel
            self.bottom_panel_height = 80  # Standard bottom panel
            self.ui_margin = 15  # Standard margins
        else:
            # Smaller resolutions
            self.tool_panel_width = 250  # Narrower panel for small screens
            self.right_panel_width = 180  # Narrower right panel
            self.bottom_panel_height = 70  # Shorter bottom panel
            self.ui_margin = 10  # Smaller margins

        # Recalculate areas with improved spacing
        self.map_area_x = self.tool_panel_width + self.ui_margin
        self.map_area_y = self.ui_margin
        self.map_area_width = self.screen_width - self.tool_panel_width - self.right_panel_width - self.ui_margin * 3
        self.map_area_height = self.screen_height - self.bottom_panel_height - self.ui_margin * 2

        # Recreate UI elements
        self._create_ui_elements()

    def _create_new_level(self, width, height):
        """Create a new empty level."""
        # Create an empty level with walls around the perimeter
        level_data = []
        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    row.append(WALL)
                else:
                    row.append(FLOOR)
            level_data.append(''.join(row))

        level_string = '\n'.join(level_data)
        self.current_level = Level(level_data=level_string)
        self.unsaved_changes = True
        self._reset_view()  # Auto-fit the new level

    def _toggle_grid(self):
        """Toggle grid display."""
        self.show_grid = not self.show_grid

    def _zoom_in(self):
        """Zoom in on the map."""
        if self.zoom_level < self.max_zoom:
            old_zoom = self.zoom_level
            self.zoom_level = min(self.max_zoom, self.zoom_level * 1.2)
            # Adjust scroll to keep center point stable
            zoom_factor = self.zoom_level / old_zoom
            center_x = self.map_area_width // 2
            center_y = self.map_area_height // 2
            self.scroll_x = (self.scroll_x + center_x) * zoom_factor - center_x
            self.scroll_y = (self.scroll_y + center_y) * zoom_factor - center_y

    def _zoom_out(self):
        """Zoom out on the map."""
        if self.zoom_level > self.min_zoom:
            old_zoom = self.zoom_level
            self.zoom_level = max(self.min_zoom, self.zoom_level / 1.2)
            # Adjust scroll to keep center point stable
            zoom_factor = self.zoom_level / old_zoom
            center_x = self.map_area_width // 2
            center_y = self.map_area_height // 2
            self.scroll_x = (self.scroll_x + center_x) * zoom_factor - center_x
            self.scroll_y = (self.scroll_y + center_y) * zoom_factor - center_y

    def _reset_view(self):
        """Reset zoom and scroll to default with auto-fit."""
        if self.current_level:
            # Calculate zoom to fit the level perfectly in the map area
            zoom_x = self.map_area_width / (self.current_level.width * CELL_SIZE)
            zoom_y = self.map_area_height / (self.current_level.height * CELL_SIZE)
            self.zoom_level = min(zoom_x, zoom_y, self.max_zoom)  # Use the smaller zoom to fit both dimensions
            self.zoom_level = max(self.zoom_level, self.min_zoom)  # Ensure it's not too small

            # Center the map perfectly
            map_pixel_width = self.current_level.width * CELL_SIZE * self.zoom_level
            map_pixel_height = self.current_level.height * CELL_SIZE * self.zoom_level
            self.scroll_x = (self.map_area_width - map_pixel_width) // 2
            self.scroll_y = (self.map_area_height - map_pixel_height) // 2
        else:
            self.zoom_level = 1.0
            self.scroll_x = 0
            self.scroll_y = 0

    def _on_width_change(self, new_width):
        """Handle width slider change."""
        if new_width != self.map_width:
            self.map_width = new_width
            self._create_new_level(self.map_width, self.map_height)

    def _on_height_change(self, new_height):
        """Handle height slider change."""
        if new_height != self.map_height:
            self.map_height = new_height
            self._create_new_level(self.map_width, self.map_height)

    def _handle_grid_click(self, mouse_pos, mouse_button, is_drag=False):
        """Handle clicks on the grid with paint mode support."""
        if not self.current_level:
            return

        # Convert screen coordinates to map coordinates
        cell_size = CELL_SIZE * self.zoom_level
        map_start_x = self.map_area_x + self.scroll_x
        map_start_y = self.map_area_y + self.scroll_y

        grid_x = int((mouse_pos[0] - map_start_x) // cell_size)
        grid_y = int((mouse_pos[1] - map_start_y) // cell_size)

        # Check if click is within grid bounds
        if (0 <= grid_x < self.current_level.width and
            0 <= grid_y < self.current_level.height):

            # Avoid painting the same cell repeatedly during drag
            if is_drag and self.last_painted_cell == (grid_x, grid_y):
                return

            self.last_painted_cell = (grid_x, grid_y)

            # In test mode, handle player movement
            if self.test_mode:
                if mouse_button == 1:  # Left click
                    player_x, player_y = self.current_level.player_pos
                    dx = grid_x - player_x
                    dy = grid_y - player_y

                    # Only allow adjacent moves
                    if abs(dx) + abs(dy) == 1:
                        self.current_level.move(dx, dy)
                return

            # In edit mode, place or clear elements
            if mouse_button == 1:  # Left click - place element
                self._place_element(grid_x, grid_y)
            elif mouse_button == 3:  # Right click - always place floor
                self._place_floor(grid_x, grid_y)

    def _place_element(self, x, y):
        """Place the current element at the specified grid coordinates."""
        if self.current_element == PLAYER:
            # Remove existing player
            self.current_level.player_pos = (x, y)
        elif self.current_element == BOX:
            # Add box if not already there
            if (x, y) not in self.current_level.boxes:
                self.current_level.boxes.append((x, y))
        elif self.current_element == TARGET:
            # Add target if not already there
            if (x, y) not in self.current_level.targets:
                self.current_level.targets.append((x, y))
        elif self.current_element == WALL:
            # Set cell to wall
            self.current_level.map_data[y][x] = WALL

            # Remove any objects at this position
            if (x, y) == self.current_level.player_pos:
                self.current_level.player_pos = (0, 0)
            if (x, y) in self.current_level.boxes:
                self.current_level.boxes.remove((x, y))
            if (x, y) in self.current_level.targets:
                self.current_level.targets.remove((x, y))
        elif self.current_element == FLOOR:
            # Set cell to floor
            self.current_level.map_data[y][x] = FLOOR

        self.unsaved_changes = True

    def _place_floor(self, x, y):
        """Place floor at the specified coordinates, removing any existing elements."""
        # Remove any objects at this position
        if (x, y) == self.current_level.player_pos:
            # Find a safe position for the player (first floor tile)
            for py in range(self.current_level.height):
                for px in range(self.current_level.width):
                    if (self.current_level.map_data[py][px] == FLOOR and
                        (px, py) not in self.current_level.boxes and
                        (px, py) not in self.current_level.targets):
                        self.current_level.player_pos = (px, py)
                        break
                else:
                    continue
                break
            else:
                # If no safe position found, place at (1,1)
                self.current_level.player_pos = (1, 1)

        if (x, y) in self.current_level.boxes:
            self.current_level.boxes.remove((x, y))
        if (x, y) in self.current_level.targets:
            self.current_level.targets.remove((x, y))

        # Always set cell to floor
        self.current_level.map_data[y][x] = FLOOR

        self.unsaved_changes = True

    def _clear_element(self, x, y):
        """Clear the element at the specified grid coordinates and set to floor."""
        # This method now just calls _place_floor for consistency
        self._place_floor(x, y)

    def _handle_palette_click(self, mouse_pos):
        """Handle clicks on the element palette."""
        # Palette is in the tool panel - updated position
        palette_start_y = 320
        palette_item_height = 38

        for i, element in enumerate(self.palette):
            item_rect = pygame.Rect(20, palette_start_y + i * palette_item_height,
                                  self.tool_panel_width - 40, palette_item_height - 5)
            if item_rect.collidepoint(mouse_pos):
                self.current_element = element['char']
                break

    def _is_in_map_area(self, pos):
        """Check if position is in the map area."""
        return (self.map_area_x <= pos[0] <= self.map_area_x + self.map_area_width and
                self.map_area_y <= pos[1] <= self.map_area_y + self.map_area_height)

    def _handle_scroll(self, dx, dy):
        """Handle scrolling the map view."""
        self.scroll_x += dx
        self.scroll_y += dy

        # Limit scrolling to reasonable bounds
        max_scroll_x = max(0, self.current_level.width * CELL_SIZE * self.zoom_level - self.map_area_width)
        max_scroll_y = max(0, self.current_level.height * CELL_SIZE * self.zoom_level - self.map_area_height)

        self.scroll_x = max(-self.map_area_width // 2, min(max_scroll_x, self.scroll_x))
        self.scroll_y = max(-self.map_area_height // 2, min(max_scroll_y, self.scroll_y))

    def _draw_editor(self):
        """Draw the enhanced editor interface."""
        # Clear the screen
        self.screen.fill(self.colors['background'])

        # Draw tool panel
        self._draw_tool_panel()

        # Draw map area
        self._draw_map_area()

        # Draw bottom panel
        self._draw_bottom_panel()

        # Draw overlays
        if self.show_help:
            self._draw_help_overlay()
        if self.show_metrics:
            self._draw_metrics_overlay()

        # Update the display
        pygame.display.flip()

    def _draw_tool_panel(self):
        """Draw the improved tool panel on the left side."""
        # Left panel background
        left_panel_rect = pygame.Rect(0, 0, self.tool_panel_width, self.screen_height)
        pygame.draw.rect(self.screen, self.colors['panel'], left_panel_rect)
        pygame.draw.line(self.screen, self.colors['border'],
                        (self.tool_panel_width, 0), (self.tool_panel_width, self.screen_height), 2)

        # Right panel background
        right_panel_x = self.screen_width - self.right_panel_width
        right_panel_rect = pygame.Rect(right_panel_x, 0, self.right_panel_width, self.screen_height)
        pygame.draw.rect(self.screen, self.colors['panel'], right_panel_rect)
        pygame.draw.line(self.screen, self.colors['border'],
                        (right_panel_x, 0), (right_panel_x, self.screen_height), 2)

        # Left panel title with shadow effect for better visibility
        title_text = "Level Editor"

        # Draw shadow
        shadow_color = (50, 50, 100)
        shadow_offset = 2
        title_shadow = self.title_font.render(title_text, True, shadow_color)
        self.screen.blit(title_shadow, (self.ui_margin + shadow_offset, 15 + shadow_offset))

        # Draw main title
        title_surface = self.title_font.render(title_text, True, self.colors['text'])
        self.screen.blit(title_surface, (self.ui_margin, 15))

        # Right panel title with shadow effect
        view_title_text = "View & Size"

        # Draw shadow
        view_title_shadow = self.text_font.render(view_title_text, True, shadow_color)
        self.screen.blit(view_title_shadow, (right_panel_x + self.ui_margin + shadow_offset, 15 + shadow_offset))

        # Draw main title
        view_title_surface = self.text_font.render(view_title_text, True, self.colors['text'])
        self.screen.blit(view_title_surface, (right_panel_x + self.ui_margin, 15))

        # Calculate responsive palette dimensions based on screen size
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution
            palette_start_y = 350
            palette_item_height = 42
            icon_size = 30
            icon_margin = 6
            text_offset_y = 10
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            # Medium resolution
            palette_start_y = 330
            palette_item_height = 38
            icon_size = 28
            icon_margin = 5
            text_offset_y = 9
        else:
            # Smaller resolutions
            palette_start_y = 320
            palette_item_height = 34
            icon_size = 25
            icon_margin = 4
            text_offset_y = 8

        # Element palette - better positioned with section title
        palette_title = self.text_font.render("Elements:", True, self.colors['text'])
        self.screen.blit(palette_title, (self.ui_margin + 5, palette_start_y - 25))

        # Draw palette items with responsive sizing
        for i, element in enumerate(self.palette):
            y = palette_start_y + i * palette_item_height
            item_rect = pygame.Rect(self.ui_margin + 5, y, self.tool_panel_width - self.ui_margin * 2 - 10, palette_item_height - 5)

            # Highlight selected element with gradient effect
            if element['char'] == self.current_element:
                # Create gradient effect for selected item
                for j in range(item_rect.width):
                    # Calculate gradient color (yellow to white)
                    gradient_factor = j / item_rect.width
                    r = int(self.colors['selected'][0] * (1 - gradient_factor) + 255 * gradient_factor)
                    g = int(self.colors['selected'][1] * (1 - gradient_factor) + 255 * gradient_factor)
                    b = int(self.colors['selected'][2] * (1 - gradient_factor) + 255 * gradient_factor)
                    pygame.draw.line(self.screen, (r, g, b), 
                                    (item_rect.x + j, item_rect.y), 
                                    (item_rect.x + j, item_rect.y + item_rect.height))
            else:
                pygame.draw.rect(self.screen, (255, 255, 255), item_rect)

            # Draw border with rounded corners
            pygame.draw.rect(self.screen, self.colors['border'], item_rect, 1, 5)

            # Draw element icon
            icon_rect = pygame.Rect(item_rect.x + icon_margin, item_rect.y + (item_rect.height - icon_size) // 2, 
                                   icon_size, icon_size)
            pygame.draw.rect(self.screen, element['color'], icon_rect)
            pygame.draw.rect(self.screen, self.colors['border'], icon_rect, 1)

            # Draw element name
            name_surface = self.text_font.render(element['name'], True, self.colors['text'])
            self.screen.blit(name_surface, (item_rect.x + icon_size + icon_margin * 2, 
                                          item_rect.y + text_offset_y))

        # Draw buttons
        for button in self.buttons:
            if button['section'] in ['file', 'tools', 'right']:
                self._draw_button(button)

        # Draw sliders
        for slider in self.sliders:
            self._draw_slider(slider)

    def _draw_map_area(self):
        """Draw the map area in the center with proper clipping."""
        if not self.current_level:
            return

        # Map area background
        map_rect = pygame.Rect(self.map_area_x, self.map_area_y,
                              self.map_area_width, self.map_area_height)
        pygame.draw.rect(self.screen, (255, 255, 255), map_rect)
        pygame.draw.rect(self.screen, self.colors['border'], map_rect, 2)

        # Set clipping to ensure content stays within the map area
        self.screen.set_clip(map_rect)

        # Calculate cell size with zoom
        cell_size = int(CELL_SIZE * self.zoom_level)

        # Calculate map position
        map_start_x = self.map_area_x + self.scroll_x
        map_start_y = self.map_area_y + self.scroll_y

        # Draw grid if enabled
        if self.show_grid and self.zoom_level >= 0.3:  # Show grid at lower zoom levels
            self._draw_grid(map_start_x, map_start_y, cell_size)

        # Draw level elements
        skin = self.skin_manager.get_skin()
        for y in range(self.current_level.height):
            for x in range(self.current_level.width):
                cell_x = map_start_x + x * cell_size
                cell_y = map_start_y + y * cell_size

                # Skip if cell is outside visible area (with clipping this is less critical)
                if (cell_x + cell_size < self.map_area_x or
                    cell_x > self.map_area_x + self.map_area_width or
                    cell_y + cell_size < self.map_area_y or
                    cell_y > self.map_area_y + self.map_area_height):
                    continue

                # Get cell character
                char = self.current_level.get_display_char(x, y)

                # Draw cell
                if char in skin:
                    scaled_sprite = pygame.transform.scale(skin[char], (cell_size, cell_size))
                    self.screen.blit(scaled_sprite, (cell_x, cell_y))

        # Remove clipping
        self.screen.set_clip(None)

    def _draw_grid(self, start_x, start_y, cell_size):
        """Draw white grid lines between tiles."""
        # Use white grid color for better visibility
        grid_color = (255, 255, 255)

        # Vertical lines - draw between tiles
        for x in range(self.current_level.width + 1):
            line_x = start_x + x * cell_size
            if self.map_area_x <= line_x <= self.map_area_x + self.map_area_width:
                pygame.draw.line(self.screen, grid_color,
                               (line_x, max(self.map_area_y, start_y)),
                               (line_x, min(self.map_area_y + self.map_area_height,
                                          start_y + self.current_level.height * cell_size)), 2)

        # Horizontal lines - draw between tiles
        for y in range(self.current_level.height + 1):
            line_y = start_y + y * cell_size
            if self.map_area_y <= line_y <= self.map_area_y + self.map_area_height:
                pygame.draw.line(self.screen, grid_color,
                               (max(self.map_area_x, start_x), line_y),
                               (min(self.map_area_x + self.map_area_width,
                                   start_x + self.current_level.width * cell_size), line_y), 2)

    def _draw_bottom_panel(self):
        """Draw the improved bottom panel with status and controls."""
        # Panel background
        panel_rect = pygame.Rect(0, self.screen_height - self.bottom_panel_height,
                                self.screen_width, self.bottom_panel_height)
        pygame.draw.rect(self.screen, self.colors['panel'], panel_rect)
        pygame.draw.line(self.screen, self.colors['border'],
                        (0, self.screen_height - self.bottom_panel_height),
                        (self.screen_width, self.screen_height - self.bottom_panel_height), 2)

        # Status information - positioned to avoid button overlap
        status_y = self.screen_height - self.bottom_panel_height + 45  # Moved down to avoid button overlap
        status_lines = [
            f"Mode: {'Test' if self.test_mode else 'Edit'}",
            f"Element: {next((e['name'] for e in self.palette if e['char'] == self.current_element), 'None')}",
            f"Zoom: {self.zoom_level:.1f}x",
            f"Grid: {'On' if self.show_grid else 'Off'}",
            f"Unsaved: {'Yes' if self.unsaved_changes else 'No'}"
        ]

        # Calculate spacing to distribute status info evenly, avoiding button areas
        available_width = self.screen_width - 300  # Leave more space for buttons
        status_spacing = available_width // len(status_lines)

        for i, line in enumerate(status_lines):
            status_surface = self.small_font.render(line, True, self.colors['text'])
            x_pos = self.ui_margin + i * status_spacing
            self.screen.blit(status_surface, (x_pos, status_y))

        # Draw bottom buttons
        for button in self.buttons:
            if button['section'] == 'bottom':
                self._draw_button(button)

    def _draw_button(self, button):
        """Draw a button with enhanced visual effects."""
        is_hovered = button['rect'].collidepoint(pygame.mouse.get_pos())

        # Determine button color based on hover state
        base_color = self.colors['button_hover'] if is_hovered else self.colors['button']

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
            pygame.draw.line(self.screen, (r, g, b),
                           (button['rect'].x, button['rect'].y + i),
                           (button['rect'].x + button['rect'].width, button['rect'].y + i))

        # Draw button border with rounded corners
        border_color = (180, 180, 220) if is_hovered else self.colors['border']
        pygame.draw.rect(self.screen, border_color, button['rect'], 2, 5)

        # Draw button text with shadow for better visibility
        shadow_offset = 1
        shadow_color = (30, 30, 50, 128)

        # Use appropriate font based on button section
        if button['section'] == 'bottom':
            font = self.small_font
        else:
            font = self.text_font

        # Draw text shadow
        text_shadow = font.render(button['text'], True, shadow_color)
        text_shadow_rect = text_shadow.get_rect(center=(button['rect'].centerx + shadow_offset, 
                                                      button['rect'].centery + shadow_offset))
        self.screen.blit(text_shadow, text_shadow_rect)

        # Draw main text
        text_surface = font.render(button['text'], True, self.colors['button_text'])
        text_rect = text_surface.get_rect(center=button['rect'].center)
        self.screen.blit(text_surface, text_rect)

    def _draw_slider(self, slider):
        """Draw a slider with enhanced visual effects."""
        # Label with shadow for better visibility
        shadow_offset = 1
        shadow_color = (30, 30, 50, 128)

        # Draw label shadow
        label_shadow = self.text_font.render(f"{slider['label']}: {slider['value']}",
                                          True, shadow_color)
        self.screen.blit(label_shadow, (slider['rect'].x + shadow_offset, slider['rect'].y - 25 + shadow_offset))

        # Draw main label
        label_surface = self.text_font.render(f"{slider['label']}: {slider['value']}",
                                           True, self.colors['text'])
        self.screen.blit(label_surface, (slider['rect'].x, slider['rect'].y - 25))

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
            pygame.draw.line(self.screen, (r, g, b),
                           (track_rect.x + track_radius, track_rect.y + i),
                           (track_rect.x + track_rect.width - track_radius, track_rect.y + i))

            # Draw rounded ends
            if i < track_radius or i >= track_rect.height - track_radius:
                continue

            # Left rounded end
            pygame.draw.line(self.screen, (r, g, b),
                           (track_rect.x, track_rect.y + i),
                           (track_rect.x + track_radius, track_rect.y + i))

            # Right rounded end
            pygame.draw.line(self.screen, (r, g, b),
                           (track_rect.x + track_rect.width - track_radius, track_rect.y + i),
                           (track_rect.x + track_rect.width, track_rect.y + i))

        # Draw track border with rounded corners
        pygame.draw.rect(self.screen, self.colors['border'], track_rect, 1, track_radius)

        # Calculate filled portion of track (progress)
        handle_pos = (slider['value'] - slider['min']) / (slider['max'] - slider['min'])
        progress_width = int(handle_pos * track_rect.width)

        # Draw progress indicator (subtle)
        progress_rect = pygame.Rect(track_rect.x, track_rect.y, progress_width, track_rect.height)
        progress_color = (180, 180, 220, 128)  # Semi-transparent blue
        pygame.draw.rect(self.screen, progress_color, progress_rect, 0, track_radius)

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
            r = int(self.colors['button'][0] * (1 - gradient_factor * 0.3))
            g = int(self.colors['button'][1] * (1 - gradient_factor * 0.3))
            b = int(self.colors['button'][2] * (1 - gradient_factor * 0.3))

            # Draw horizontal line with gradient color
            pygame.draw.line(self.screen, (r, g, b),
                           (handle_rect.x, handle_rect.y + i),
                           (handle_rect.x + handle_rect.width, handle_rect.y + i))

        # Draw handle border with rounded corners
        pygame.draw.rect(self.screen, self.colors['border'], handle_rect, 1, 5)

    def _draw_help_overlay(self):
        """Draw the help overlay with responsive sizing and enhanced visuals."""
        # Semi-transparent overlay with blur effect simulation
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Calculate responsive help panel dimensions
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution
            help_width = 700
            help_height = 600
            title_padding = 50
            content_padding = 40
            line_spacing = 28
        elif self.screen_width >= 1200 or self.screen_height >= 800:
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
        help_x = (self.screen_width - help_width) // 2
        help_y = (self.screen_height - help_height) // 2

        # Draw panel with shadow effect
        shadow_offset = 8
        shadow_rect = pygame.Rect(help_x + shadow_offset, help_y + shadow_offset, help_width, help_height)
        pygame.draw.rect(self.screen, (20, 20, 20, 100), shadow_rect, 0, 10)

        # Main panel with gradient background
        help_rect = pygame.Rect(help_x, help_y, help_width, help_height)

        # Draw gradient background
        for i in range(help_height):
            # Calculate gradient color (lighter at top, darker at bottom)
            gradient_factor = i / help_height
            r = int(240 - gradient_factor * 20)
            g = int(240 - gradient_factor * 20)
            b = int(250 - gradient_factor * 10)  # Slightly blue tint

            pygame.draw.line(self.screen, (r, g, b),
                           (help_x, help_y + i),
                           (help_x + help_width, help_y + i))

        # Draw border with rounded corners
        pygame.draw.rect(self.screen, self.colors['border'], help_rect, 2, 10)

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
        title_shadow = self.title_font.render(title_line, True, shadow_color)
        title_shadow_rect = title_shadow.get_rect(center=(help_x + help_width // 2 + shadow_offset, 
                                                       help_y + title_padding + shadow_offset))
        self.screen.blit(title_shadow, title_shadow_rect)

        # Draw main title
        title_surface = self.title_font.render(title_line, True, (0, 100, 200))
        title_rect = title_surface.get_rect(center=(help_x + help_width // 2, help_y + title_padding))
        self.screen.blit(title_surface, title_rect)

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
                section_surface = self.subtitle_font.render(line, True, (80, 80, 180))
                self.screen.blit(section_surface, (help_x + content_padding, content_y))
                content_y += line_spacing + 5  # Extra space after section header
            else:
                # Regular content line
                # Draw with shadow for better readability
                shadow_offset = 1
                text_shadow = self.text_font.render(line, True, (50, 50, 50, 128))
                self.screen.blit(text_shadow, (help_x + content_padding + shadow_offset, 
                                             content_y + shadow_offset))

                # Main text
                text_surface = self.text_font.render(line, True, self.colors['text'])
                self.screen.blit(text_surface, (help_x + content_padding, content_y))
                content_y += line_spacing

    def _draw_metrics_overlay(self):
        """Draw the metrics overlay with current level information and enhanced visuals."""
        if not self.current_level:
            return

        # Calculate responsive metrics panel dimensions
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution
            metrics_width = 350
            metrics_height = 450
            title_padding = 40
            content_padding = 30
            line_spacing = 28
            margin = 30
        elif self.screen_width >= 1200 or self.screen_height >= 800:
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
        metrics_x = self.screen_width - metrics_width - margin
        metrics_y = 100

        # Draw panel with shadow effect
        shadow_offset = 8
        shadow_rect = pygame.Rect(metrics_x + shadow_offset, metrics_y + shadow_offset, metrics_width, metrics_height)
        pygame.draw.rect(self.screen, (20, 20, 20, 100), shadow_rect, 0, 10)

        # Main panel with gradient background
        metrics_rect = pygame.Rect(metrics_x, metrics_y, metrics_width, metrics_height)

        # Draw gradient background
        for i in range(metrics_height):
            # Calculate gradient color (darker at top, lighter at bottom)
            gradient_factor = i / metrics_height
            r = int(40 + gradient_factor * 40)
            g = int(40 + gradient_factor * 40)
            b = int(80 + gradient_factor * 40)  # Blue tint

            pygame.draw.line(self.screen, (r, g, b),
                           (metrics_x, metrics_y + i),
                           (metrics_x + metrics_width, metrics_y + i))

        # Draw border with rounded corners
        pygame.draw.rect(self.screen, self.colors['border'], metrics_rect, 2, 10)

        # Draw title with shadow effect
        title_text = "Level Metrics"
        shadow_color = (20, 20, 50)
        shadow_offset = 2

        # Draw title shadow
        title_shadow = self.title_font.render(title_text, True, shadow_color)
        title_shadow_rect = title_shadow.get_rect(center=(metrics_x + metrics_width // 2 + shadow_offset, 
                                                       metrics_y + title_padding + shadow_offset))
        self.screen.blit(title_shadow, title_shadow_rect)

        # Draw main title
        title_surface = self.title_font.render(title_text, True, (180, 180, 255))
        title_rect = title_surface.get_rect(center=(metrics_x + metrics_width // 2, metrics_y + title_padding))
        self.screen.blit(title_surface, title_rect)

        # Calculate level statistics
        wall_count = sum(row.count(WALL) for row in self.current_level.map_data)
        floor_count = sum(row.count(FLOOR) for row in self.current_level.map_data)
        total_cells = self.current_level.width * self.current_level.height

        # Check if level is valid
        is_valid = (len(self.current_level.boxes) == len(self.current_level.targets) and 
                   len(self.current_level.boxes) > 0 and 
                   self.current_level.player_pos != (0, 0))

        # Metrics content with sections
        metrics_sections = [
            {
                'title': 'Level Size',
                'items': [
                    f"Dimensions: {self.current_level.width}x{self.current_level.height}",
                    f"Total cells: {total_cells}"
                ]
            },
            {
                'title': 'Elements',
                'items': [
                    f"Walls: {wall_count}",
                    f"Floors: {floor_count}",
                    f"Boxes: {len(self.current_level.boxes)}",
                    f"Targets: {len(self.current_level.targets)}",
                    f"Player: {'Set' if self.current_level.player_pos != (0, 0) else 'Not set'}"
                ]
            },
            {
                'title': 'View',
                'items': [
                    f"Zoom: {self.zoom_level:.2f}x",
                    f"Grid: {'On' if self.show_grid else 'Off'}"
                ]
            },
            {
                'title': 'Status',
                'items': [
                    f"Valid: {'Yes' if is_valid else 'No'}",
                    f"Mode: {'Test' if self.test_mode else 'Edit'}"
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
            section_shadow = self.subtitle_font.render(section_title, True, shadow_color)
            self.screen.blit(section_shadow, (metrics_x + content_padding + shadow_offset, 
                                           content_y + shadow_offset))

            section_surface = self.subtitle_font.render(section_title, True, section_color)
            self.screen.blit(section_surface, (metrics_x + content_padding, content_y))

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
                text_shadow = self.text_font.render(item, True, (0, 0, 0, 150))
                self.screen.blit(text_shadow, (metrics_x + content_padding + 10 + shadow_offset, 
                                             content_y + shadow_offset))

                # Draw main text
                text_surface = self.text_font.render(item, True, text_color)
                self.screen.blit(text_surface, (metrics_x + content_padding + 10, content_y))

                # Draw highlight indicator for important items
                if highlight:
                    indicator_rect = pygame.Rect(metrics_x + content_padding, content_y + 2, 
                                               5, self.text_font.get_height() - 4)
                    pygame.draw.rect(self.screen, text_color, indicator_rect)

                content_y += line_spacing

            # Add space between sections
            content_y += line_spacing // 2

    # Dialog methods
    def _show_new_level_dialog(self):
        """Show dialog to create a new level."""
        self._create_new_level(self.map_width, self.map_height)

    def _show_open_level_dialog(self):
        """Show dialog to open an existing level."""
        # Get list of level files
        level_files = self.level_manager.level_files
        if not level_files:
            return

        # Create a dialog
        dialog_width = 600
        dialog_height = 500
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2

        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

        # Create level buttons
        level_buttons = []
        button_height = 30
        button_spacing = 10

        for i, level_file in enumerate(level_files):
            level_name = os.path.basename(level_file)
            level_rect = pygame.Rect(
                dialog_x + 50,
                dialog_y + 80 + i * (button_height + button_spacing),
                dialog_width - 100,
                button_height
            )

            level_buttons.append({
                'text': level_name,
                'rect': level_rect,
                'file': level_file
            })

        # Create cancel button
        cancel_rect = pygame.Rect(dialog_x + dialog_width // 2 - 50, dialog_y + dialog_height - 50, 100, 30)

        # Draw the editor once to create a background
        self._draw_editor()
        # Create a copy of the screen to use as background
        background = self.screen.copy()

        # Dialog loop
        dialog_running = True
        while dialog_running and not self.exit_requested:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_requested = True
                    dialog_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        dialog_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    # Check if a level button was clicked
                    for button in level_buttons:
                        if button['rect'].collidepoint(mouse_pos):
                            try:
                                self.current_level = Level(level_file=button['file'])
                                self.unsaved_changes = False
                                self._reset_view()
                                dialog_running = False
                                break
                            except Exception as e:
                                print(f"Error opening level: {e}")

                    # Check if cancel button was clicked
                    if cancel_rect.collidepoint(mouse_pos):
                        dialog_running = False

            # Restore the background instead of redrawing everything
            self.screen.blit(background, (0, 0))

            # Draw dialog box
            pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)

            # Draw title
            title_surface = self.title_font.render("Open Level", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)

            # Draw level buttons
            for button in level_buttons:
                pygame.draw.rect(self.screen, (200, 200, 200), button['rect'])
                pygame.draw.rect(self.screen, (0, 0, 0), button['rect'], 1)

                text_surface = self.text_font.render(button['text'], True, (0, 0, 0))
                text_rect = text_surface.get_rect(midleft=(button['rect'].left + 10, button['rect'].centery))
                self.screen.blit(text_surface, text_rect)

            # Draw cancel button
            pygame.draw.rect(self.screen, (200, 100, 100), cancel_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), cancel_rect, 1)

            cancel_text = self.text_font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            self.screen.blit(cancel_text, cancel_text_rect)

            pygame.display.flip()

    def _show_save_level_dialog(self):
        """Show dialog to save the current level."""
        if not self.current_level:
            return

        # Create a dialog
        dialog_width = 500
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2

        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

        # Create input field
        input_rect = pygame.Rect(dialog_x + 50, dialog_y + 100, dialog_width - 100, 30)
        input_text = ""
        input_active = True

        # Create buttons
        save_rect = pygame.Rect(dialog_x + dialog_width // 2 - 110, dialog_y + dialog_height - 50, 100, 30)
        cancel_rect = pygame.Rect(dialog_x + dialog_width // 2 + 10, dialog_y + dialog_height - 50, 100, 30)

        # Draw the editor once to create a background
        self._draw_editor()
        # Create a copy of the screen to use as background
        background = self.screen.copy()

        # Dialog loop
        dialog_running = True
        while dialog_running and not self.exit_requested:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_requested = True
                    dialog_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        dialog_running = False
                    elif event.key == pygame.K_RETURN:
                        if input_text:
                            self._save_level(input_text)
                            dialog_running = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        # Add character to input text if it's valid for a filename
                        if event.unicode.isalnum() or event.unicode in "-_. ":
                            input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    # Check if input field was clicked
                    input_active = input_rect.collidepoint(mouse_pos)

                    # Check if save button was clicked
                    if save_rect.collidepoint(mouse_pos) and input_text:
                        self._save_level(input_text)
                        dialog_running = False

                    # Check if cancel button was clicked
                    elif cancel_rect.collidepoint(mouse_pos):
                        dialog_running = False

            # Restore the background instead of redrawing everything
            self.screen.blit(background, (0, 0))

            # Draw dialog box
            pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)

            # Draw title
            title_surface = self.title_font.render("Save Level", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)

            # Draw input label
            label_surface = self.text_font.render("Filename:", True, (0, 0, 0))
            label_rect = label_surface.get_rect(midright=(input_rect.left - 10, input_rect.centery))
            self.screen.blit(label_surface, label_rect)

            # Draw input field
            pygame.draw.rect(self.screen, (255, 255, 255), input_rect)
            pygame.draw.rect(self.screen, (0, 0, 0) if input_active else (100, 100, 100), input_rect, 2)

            # Draw input text
            input_surface = self.text_font.render(input_text, True, (0, 0, 0))
            input_text_rect = input_surface.get_rect(midleft=(input_rect.left + 5, input_rect.centery))
            self.screen.blit(input_surface, input_text_rect)

            # Draw save button
            pygame.draw.rect(self.screen, (100, 200, 100), save_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), save_rect, 1)

            save_text = self.text_font.render("Save", True, (255, 255, 255))
            save_text_rect = save_text.get_rect(center=save_rect.center)
            self.screen.blit(save_text, save_text_rect)

            # Draw cancel button
            pygame.draw.rect(self.screen, (200, 100, 100), cancel_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), cancel_rect, 1)

            cancel_text = self.text_font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            self.screen.blit(cancel_text, cancel_text_rect)

            pygame.display.flip()

    def _save_level(self, filename):
        """Save the current level to a file."""
        if not filename:
            return

        # Add .txt extension if not provided
        if not filename.endswith('.txt'):
            filename += '.txt'

        # Create full path
        level_path = os.path.join(self.levels_dir, filename)

        # Save the level
        level_string = self.current_level.get_state_string()

        try:
            with open(level_path, 'w') as file:
                file.write(level_string)

            self.unsaved_changes = False

            # Reload level files in level manager
            self.level_manager._load_level_files()
        except Exception as e:
            print(f"Error saving level: {e}")

    def _toggle_test_mode(self):
        """Toggle test mode to play the current level."""
        if self._validate_level(show_dialog=False):
            self.test_mode = not self.test_mode

            if self.test_mode:
                # Save complete initial state for testing
                self.initial_level_state = {
                    'player_pos': self.current_level.player_pos,
                    'boxes': self.current_level.boxes.copy(),
                    'targets': self.current_level.targets.copy(),
                    'map_data': [row[:] for row in self.current_level.map_data]  # Deep copy
                }
            else:
                # Restore complete initial state after testing
                if self.initial_level_state:
                    self.current_level.player_pos = self.initial_level_state['player_pos']
                    self.current_level.boxes = self.initial_level_state['boxes'].copy()
                    self.current_level.targets = self.initial_level_state['targets'].copy()
                    self.current_level.map_data = [row[:] for row in self.initial_level_state['map_data']]

    def _validate_level(self, show_dialog=True):
        """Validate the current level."""
        if not self.current_level:
            return False

        # Check if level has a player
        has_player = self.current_level.player_pos != (0, 0)

        # Check if level has at least one box and target
        has_boxes = len(self.current_level.boxes) > 0
        has_targets = len(self.current_level.targets) > 0

        # Check if number of boxes matches number of targets
        boxes_match_targets = len(self.current_level.boxes) == len(self.current_level.targets)

        # Check if level is valid
        is_valid = has_player and has_boxes and has_targets and boxes_match_targets

        if show_dialog:
            # Simple validation message (in a full implementation, this would be a proper dialog)
            status = "Valid" if is_valid else "Invalid"
            print(f"Level validation: {status}")
            if not is_valid:
                print(f"Player: {has_player}, Boxes: {has_boxes}, Targets: {has_targets}, Match: {boxes_match_targets}")

        return is_valid

    def _solve_level(self):
        """Solve the current level and let AI take control to solve it automatically."""
        if not self.current_level:
            print("No level to solve")
            return

        if not self._validate_level(show_dialog=False):
            print("Level is not valid - cannot solve")
            return

        try:
            # Create a renderer for the editor context
            class EditorRenderer:
                def __init__(self, editor):
                    self.editor = editor
                    self.screen = editor.screen

                def render_level(self, level, level_manager, show_grid, zoom_level, scroll_x, scroll_y, skin_manager):
                    # Use the editor's drawing method
                    self.editor._draw_editor()

                def get_size(self):
                    return self.screen.get_size()

            # Create auto solver with editor renderer
            auto_solver = AutoSolver(self.current_level, EditorRenderer(self), self.skin_manager)

            # Show solving message
            print("\n" + "="*60)
            print("AI TAKING CONTROL OF LEVEL")
            print("="*60)

            def progress_callback(message):
                print(f"AI: {message}")

            # Solve the level
            success = auto_solver.solve_level(progress_callback)

            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"SUCCESS: Solution found!")
                print(f"Solution length: {solution_info['moves']} moves")
                print(f"AI will now take control and solve the level...")
                print("="*60)

                # Let AI take control and solve the level
                ai_success = auto_solver.execute_solution_live(
                    move_delay=600,  # Slightly slower for editor visibility
                    show_grid=self.show_grid,
                    zoom_level=self.zoom_level,
                    scroll_x=self.scroll_x,
                    scroll_y=self.scroll_y,
                    level_manager=None
                )

                if ai_success:
                    print("AI successfully solved the level!")
                    self.unsaved_changes = True  # Mark as changed since level state changed
                else:
                    print("AI failed to execute the solution")

            else:
                print("FAILED: No solution found for this level")
                print("The level might be unsolvable or too complex")
                print("="*60)

        except Exception as e:
            print(f"ERROR: Exception during AI level solving: {e}")
            import traceback
            traceback.print_exc()
            print("="*60)

    def _show_generate_dialog(self):
        """Show dialog to generate a random level."""
        # Simple implementation - generate with default parameters
        try:
            params = {
                'min_width': 8,
                'max_width': 12,
                'min_height': 8,
                'max_height': 12,
                'min_boxes': 2,
                'max_boxes': 4,
                'wall_density': 0.15,
                'timeout': 30.0  # Increased timeout for better chance of success
            }

            # Show a message to indicate generation is in progress
            print("\n" + "="*60)
            print("LEVEL GENERATION STARTED")
            print("="*60)
            print("Parameters:")
            print(f"  Size: {params['min_width']}x{params['min_height']} to {params['max_width']}x{params['max_height']}")
            print(f"  Boxes: {params['min_boxes']} to {params['max_boxes']}")
            print(f"  Wall density: {params['wall_density']}")
            print(f"  Timeout: {params['timeout']} seconds")
            print("-"*60)

            # Define a custom progress callback with more detailed information
            def enhanced_progress_callback(progress_info):
                status = progress_info.get('status', 'unknown')
                attempts = progress_info.get('attempts', 0)
                elapsed = progress_info.get('elapsed_time', 0)
                percent = progress_info.get('percent', 0)

                # Create a progress bar
                bar_length = 40
                filled_length = int(bar_length * percent / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)

                if status == 'generating':
                    width = progress_info.get('width', 0)
                    height = progress_info.get('height', 0)
                    boxes = progress_info.get('boxes', 0)
                    timeout = progress_info.get('timeout', 0)
                    remaining = max(0, timeout - elapsed)

                    print(f"\rGenerating level... [{bar}] {percent:.1f}% | Attempts: {attempts} | Time: {elapsed:.1f}s | Remaining: {remaining:.1f}s | Current: {width}x{height} with {boxes} boxes", end='')

                elif status == 'success':
                    solution_length = progress_info.get('solution_length', 0)
                    width = progress_info.get('width', 0)
                    height = progress_info.get('height', 0)
                    boxes = progress_info.get('boxes', 0)

                    print(f"\rGeneration complete! [{bar}] 100% | Attempts: {attempts} | Time: {elapsed:.1f}s | Size: {width}x{height} | Boxes: {boxes} | Solution: {solution_length} moves")
                    print("\nSUCCESS: Level generated successfully!")
                    print("="*60)

                elif status == 'timeout':
                    print(f"\rGeneration timed out! [{bar}] 100% | Attempts: {attempts} | Time: {elapsed:.1f}s | Could not find a solvable level")
                    print("\nWARNING: Could not generate a solvable level within the timeout period.")
                    print("Try again with different parameters or a longer timeout.")
                    print("="*60)

            # Generate the level with our enhanced progress callback
            if self.level_manager.generate_random_level(params, enhanced_progress_callback):
                self.current_level = self.level_manager.current_level
                self.unsaved_changes = True
                self._reset_view()

                # Additional metrics display
                if self.level_manager.current_level_metrics:
                    metrics = self.level_manager.current_level_metrics
                    print("\nLevel Metrics:")
                    print(f"  Difficulty: {metrics['difficulty']['overall_score']:.1f}/100")
                    if 'space_efficiency' in metrics:
                        print(f"  Space efficiency: {metrics['space_efficiency']:.2f}")
                    if 'box_density' in metrics:
                        print(f"  Box density: {metrics['box_density']:.2f}")
                    if 'patterns' in metrics:
                        print("  Patterns:")
                        patterns = metrics['patterns']
                        if 'corners' in patterns:
                            print(f"    Corners: {patterns['corners']}")
                        if 'corridors' in patterns:
                            print(f"    Corridors: {patterns['corridors']}")
                        if 'rooms' in patterns:
                            print(f"    Rooms: {patterns['rooms']}")
                        if 'dead_ends' in patterns:
                            print(f"    Dead ends: {patterns['dead_ends']}")
                    print("="*60)
            else:
                print("\nERROR: Failed to generate a level. Please try again.")
                print("="*60)
        except Exception as e:
            print(f"\nERROR: Exception during level generation: {e}")
            import traceback
            traceback.print_exc()
            print("="*60)

    def _toggle_help(self):
        """Toggle help screen."""
        self.show_help = not self.show_help

    def _toggle_metrics(self):
        """Toggle metrics display."""
        self.show_metrics = not self.show_metrics

    def _exit_editor(self):
        """Exit the editor."""
        if self.unsaved_changes:
            # In a full implementation, this would show a confirmation dialog
            print("Warning: Unsaved changes will be lost!")
        self.running = False
        self.exit_requested = True

    def _handle_slider_click(self, mouse_pos, slider):
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

    def start(self):
        """Start the enhanced level editor."""
        try:
            self.running = True
            clock = pygame.time.Clock()

            # Store the current display caption to restore it later
            original_caption = pygame.display.get_caption()[0]
            if not self.using_shared_screen:
                pygame.display.set_caption(f"{TITLE} - Enhanced Level Editor")

            while self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._exit_editor()
                    elif event.type == pygame.KEYDOWN:
                        self._handle_key_event(event)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self._handle_mouse_down(event)
                    elif event.type == pygame.MOUSEBUTTONUP:
                        self._handle_mouse_up(event)
                    elif event.type == pygame.MOUSEMOTION:
                        self._handle_mouse_motion(event)
                    elif event.type == pygame.MOUSEWHEEL:
                        self._handle_mouse_wheel(event)
                    elif event.type == pygame.VIDEORESIZE:
                        self._handle_resize(event)

                # Draw the editor
                self._draw_editor()

                # Cap the frame rate
                clock.tick(60)

            # Restore original caption when exiting
            if not self.using_shared_screen:
                pygame.display.set_caption(original_caption)
                pygame.quit()

        except Exception as e:
            print(f"Error in enhanced level editor: {e}")
            import traceback
            traceback.print_exc()

    def _handle_key_event(self, event):
        """Handle keyboard events."""
        if event.key == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
            elif self.test_mode:
                self._toggle_test_mode()
            else:
                self._exit_editor()
        elif event.key == pygame.K_h:
            self._toggle_help()
        elif event.key == pygame.K_g:
            self._toggle_grid()
        elif event.key == pygame.K_t:
            self._toggle_test_mode()
        elif event.key == pygame.K_m:
            self._toggle_metrics()
        elif self.test_mode:
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
                self.current_level.move(dx, dy)
        else:
            # Handle scrolling in edit mode
            scroll_speed = 20
            if event.key == pygame.K_UP:
                self._handle_scroll(0, scroll_speed)
            elif event.key == pygame.K_DOWN:
                self._handle_scroll(0, -scroll_speed)
            elif event.key == pygame.K_LEFT:
                self._handle_scroll(scroll_speed, 0)
            elif event.key == pygame.K_RIGHT:
                self._handle_scroll(-scroll_speed, 0)

    def _handle_mouse_down(self, event):
        """Handle mouse button down events."""
        mouse_pos = pygame.mouse.get_pos()

        # Check button clicks
        for button in self.buttons:
            if button['rect'].collidepoint(mouse_pos):
                button['action']()
                return

        # Check slider clicks
        for slider in self.sliders:
            if slider['rect'].collidepoint(mouse_pos):
                self._handle_slider_click(mouse_pos, slider)
                return

        # Check palette clicks (left panel) or right panel clicks
        if mouse_pos[0] < self.tool_panel_width:
            self._handle_palette_click(mouse_pos)
            return
        elif mouse_pos[0] > self.screen_width - self.right_panel_width:
            # Right panel clicks are handled by button checks above
            return

        # Check map area clicks
        if self._is_in_map_area(mouse_pos):
            if event.button == 2:  # Middle mouse button - start dragging
                self.mouse_dragging = True
                self.drag_start_pos = mouse_pos
                self.drag_start_scroll = (self.scroll_x, self.scroll_y)
            else:
                self.paint_mode = True
                self.last_painted_cell = None
                self._handle_grid_click(mouse_pos, event.button)

    def _handle_mouse_up(self, event):
        """Handle mouse button up events."""
        if event.button == 2:  # Middle mouse button
            self.mouse_dragging = False
            self.drag_start_pos = None
            self.drag_start_scroll = None
        else:
            self.paint_mode = False
            self.last_painted_cell = None

    def _handle_mouse_motion(self, event):
        """Handle mouse motion events."""
        mouse_pos = pygame.mouse.get_pos()

        if self.mouse_dragging and self.drag_start_pos and self.drag_start_scroll:
            # Handle middle mouse dragging for panning
            dx = mouse_pos[0] - self.drag_start_pos[0]
            dy = mouse_pos[1] - self.drag_start_pos[1]

            self.scroll_x = self.drag_start_scroll[0] + dx
            self.scroll_y = self.drag_start_scroll[1] + dy

            # Apply scroll limits
            if self.current_level:
                max_scroll_x = max(0, self.current_level.width * CELL_SIZE * self.zoom_level - self.map_area_width)
                max_scroll_y = max(0, self.current_level.height * CELL_SIZE * self.zoom_level - self.map_area_height)

                self.scroll_x = max(-self.map_area_width // 2, min(max_scroll_x, self.scroll_x))
                self.scroll_y = max(-self.map_area_height // 2, min(max_scroll_y, self.scroll_y))

        elif self.paint_mode and self._is_in_map_area(mouse_pos):
            # Continue painting while dragging
            self._handle_grid_click(mouse_pos, 1, is_drag=True)

    def _handle_mouse_wheel(self, event):
        """Handle mouse wheel events for zooming."""
        if self._is_in_map_area(pygame.mouse.get_pos()):
            if event.y > 0:
                self._zoom_in()
            else:
                self._zoom_out()

    def _handle_resize(self, event):
        """Handle window resize events."""
        self.screen_width, self.screen_height = event.size
        if not self.using_shared_screen:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self._update_ui_layout()


# Main function to run the enhanced level editor standalone
def main():
    """Main function to run the enhanced level editor."""
    editor = EnhancedLevelEditor()
    editor.start()


if __name__ == "__main__":
    main()
