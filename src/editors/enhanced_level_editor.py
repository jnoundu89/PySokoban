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
import tkinter as tk
from tkinter import filedialog, messagebox
from ..core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE, TITLE
from ..core.level import Level
from ..level_management.level_manager import LevelManager
from ..ui.skins.enhanced_skin_manager import EnhancedSkinManager
from ..generation.procedural_generator import ProceduralGenerator
from ..core.auto_solver import AutoSolver
from ..ui.interactive_highlight import EditorHighlight

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

        # Load configuration
        from src.core.config_manager import get_config_manager
        self.config_manager = get_config_manager()

        # Check if levels directory exists, create it if not
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)

        # Editor state
        self.current_level = None
        self.current_element = WALL
        self.unsaved_changes = False
        self.show_help = False
        self.show_grid = False
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
        self.active_mouse_button = None  # Track which mouse button is being used for painting
        self.active_slider = None  # Track which slider is currently being adjusted

        # Text input for width and height
        self.active_text_field = None  # Track which text field is currently active
        self.text_input = ""  # Current text input
        self.text_input_cursor_visible = True  # For cursor blinking
        self.text_input_cursor_timer = 0  # For cursor blinking timing

        # Zoom and scroll
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        self.scroll_x = 0
        self.scroll_y = 0

        # Map dimensions
        self.map_width = 10
        self.map_height = 10
        self.min_map_size = 5
        self.max_map_size = 255

        # UI Layout - improved responsive design
        self.ui_margin = 15
        self.tool_panel_width = 280  # Increased width for better spacing
        self.right_panel_width = 280  # Increased width for metrics content
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
            'text': (50, 50, 50),
            'button': (100, 100, 200),
            'button_hover': (130, 130, 255),
            'button_text': (255, 255, 255),
            'selected': (255, 255, 0),
            'border': (100, 100, 100)
        }

        # Fonts - responsive sizing based on screen dimensions
        self._update_fonts()

        # Interactive highlighting system for editor
        self.highlight_system = EditorHighlight()

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

        # Bottom panel buttons - only Exit button
        bottom_y = self.screen_height - self.bottom_panel_height + (self.bottom_panel_height - small_button_height) // 2

        self.buttons.extend([
            {'rect': pygame.Rect(self.screen_width - self.ui_margin - bottom_button_width, bottom_y, bottom_button_width, small_button_height),
             'text': 'Exit', 'action': self._exit_editor, 'section': 'bottom'}
        ])

        # Size sliders - moved to right panel with proper spacing and increased size
        slider_y = view_section_y + spacing * 3 + section_spacing
        slider_width = view_button_width
        slider_height = max(24, button_height // 2 + 6)  # Increased responsive slider height
        slider_spacing = spacing + 10  # Increased spacing between sliders

        self.sliders = [
            {'rect': pygame.Rect(right_panel_x, slider_y, slider_width, slider_height),
             'label': 'Width', 'value': self.map_width, 'min': self.min_map_size, 'max': self.max_map_size,
             'callback': self._on_width_change, 'text_field': True},
            {'rect': pygame.Rect(right_panel_x, slider_y + slider_spacing, slider_width, slider_height),
             'label': 'Height', 'value': self.map_height, 'min': self.min_map_size, 'max': self.max_map_size,
             'callback': self._on_height_change, 'text_field': True}
        ]

        # Help button - moved to right panel below sliders
        help_y = slider_y + slider_spacing * 2 + section_spacing

        self.buttons.extend([
            {'rect': pygame.Rect(right_panel_x, help_y, view_button_width, button_height),
             'text': 'Help', 'action': self._toggle_help, 'section': 'right'}
        ])

        # Store the position for metrics section
        self.metrics_y = help_y + spacing + section_spacing

    def _update_fonts(self):
        """Update fonts based on screen size."""
        # Responsive font sizing based on both width and height
        # This ensures better scaling for different aspect ratios
        base_dimension = min(self.screen_width, self.screen_height)

        # Scale font sizes based on screen dimensions
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution (e.g., 1920x1080)
            title_size = min(max(28, base_dimension // 25), 36)
            subtitle_size = min(max(24, base_dimension // 35), 30)
            text_size = min(max(20, base_dimension // 40), 24)
            small_size = min(max(16, base_dimension // 50), 20)
        elif self.screen_width >= 1200 or self.screen_height >= 800:
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
        self.title_font = pygame.font.Font(None, title_size)
        self.subtitle_font = pygame.font.Font(None, subtitle_size)
        self.text_font = pygame.font.Font(None, text_size)
        self.small_font = pygame.font.Font(None, small_size)

        # Print font sizes for debugging
        print(f"Updated editor fonts - Title: {title_size}, Subtitle: {subtitle_size}, Text: {text_size}, Small: {small_size}")

    def _update_ui_layout(self):
        """Update UI layout when screen is resized."""
        # Update fonts first
        self._update_fonts()

        # Adjust panel dimensions based on screen size
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution (e.g., 1920x1080)
            self.tool_panel_width = 320  # Wider panel for high-res
            self.right_panel_width = 320  # Increased width for metrics content
            self.bottom_panel_height = 90  # Taller bottom panel
            self.ui_margin = 20  # Larger margins
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            # Medium resolution (e.g., 1200x800)
            self.tool_panel_width = 280  # Standard panel width
            self.right_panel_width = 280  # Increased width for metrics content
            self.bottom_panel_height = 80  # Standard bottom panel
            self.ui_margin = 15  # Standard margins
        else:
            # Smaller resolutions
            self.tool_panel_width = 250  # Narrower panel for small screens
            self.right_panel_width = 250  # Increased width for metrics content
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
        # Calculate palette dimensions using the same logic as in _draw_tool_panel
        # Find the Generate button to calculate spacing
        generate_button_bottom = 0
        for button in self.buttons:
            if button.get('text') == 'Generate' and button.get('section') == 'tools':
                generate_button_bottom = button['rect'].y + button['rect'].height
                break

        # Calculate responsive palette dimensions based on screen size
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution
            palette_item_height = 52  # Increased height
            section_spacing = 80  # Increased spacing between sections
        elif self.screen_width >= 1200 or self.screen_height >= 800:
            # Medium resolution
            palette_item_height = 48  # Increased height
            section_spacing = 70  # Increased spacing between sections
        else:
            # Smaller resolutions
            palette_item_height = 44  # Increased height
            section_spacing = 60  # Increased spacing between sections

        # Calculate palette_start_y based on the Generate button position
        palette_start_y = generate_button_bottom + section_spacing

        for i, element in enumerate(self.palette):
            y = palette_start_y + i * palette_item_height
            item_rect = pygame.Rect(self.ui_margin + 5, y, self.tool_panel_width - self.ui_margin * 2 - 10, palette_item_height - 5)
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

        # No scroll limits - allow infinite scrolling in all directions

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

        # Left panel title - simple text without shadow
        title_text = "Level Editor"
        title_surface = self.title_font.render(title_text, True, self.colors['text'])
        self.screen.blit(title_surface, (self.ui_margin, 15))

        # Right panel title - simple text without shadow
        view_title_text = "View & Size"
        view_title_surface = self.text_font.render(view_title_text, True, self.colors['text'])
        self.screen.blit(view_title_surface, (right_panel_x + self.ui_margin, 15))

        # Store right_panel_x for use in other methods
        self.right_panel_x = right_panel_x

        # Find the Generate button to calculate spacing
        generate_button_bottom = 0
        for button in self.buttons:
            if button.get('text') == 'Generate' and button.get('section') == 'tools':
                generate_button_bottom = button['rect'].y + button['rect'].height
                break

        # Calculate responsive palette dimensions based on screen size
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution
            palette_item_height = 52  # Increased height
            icon_size = 36  # Increased icon size
            icon_margin = 8
            text_offset_y = 15
            section_spacing = 80  # Increased spacing between sections
        elif self.screen_width >= 1200 or self.screen_height >= 800:
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
        pygame.draw.line(self.screen, self.colors['border'],
                        (self.ui_margin, separator_y), 
                        (self.tool_panel_width - self.ui_margin, separator_y), 2)

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

            # Draw element icon using skin manager
            icon_rect = pygame.Rect(item_rect.x + icon_margin, item_rect.y + (item_rect.height - icon_size) // 2, 
                                   icon_size, icon_size)

            # Get the skin from the skin manager
            skin = self.skin_manager.get_skin()

            # Draw the element using the skin
            if element['char'] in skin:
                # Scale the sprite to the icon size
                scaled_sprite = pygame.transform.scale(skin[element['char']], (icon_size, icon_size))
                self.screen.blit(scaled_sprite, icon_rect)
            else:
                # Fallback to the hardcoded color if sprite not found
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

        # Draw metrics panel in the right panel
        if hasattr(self, 'metrics_y') and self.current_level:
            self._draw_metrics_panel()

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

        # Draw grid if enabled (moved after drawing level elements to be in foreground)
        if self.show_grid and self.zoom_level >= 0.3:  # Show grid at lower zoom levels
            self._draw_grid(map_start_x, map_start_y, cell_size)

        # Update and render interactive highlighting
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos:
            # Set the appropriate mode for highlighting
            if self.test_mode:
                self.highlight_system.set_mode('test')
            elif self.paint_mode:
                self.highlight_system.set_mode('paint')
            else:
                self.highlight_system.set_mode('edit')

            # Update highlight position based on mouse
            self.highlight_system.update_mouse_position(
                mouse_pos, self.map_area_x, self.map_area_y,
                self.map_area_width, self.map_area_height,
                self.current_level.width, self.current_level.height,
                cell_size, self.scroll_x, self.scroll_y
            )

            # Render the highlight overlay with element preview
            self.highlight_system.render_highlight(
                self.screen, self.map_area_x, self.map_area_y, cell_size,
                self.scroll_x, self.scroll_y, self.current_element, self.skin_manager
            )

        # Remove clipping
        self.screen.set_clip(None)

    def _draw_grid(self, start_x, start_y, cell_size):
        """Draw grid lines between tiles using color from config."""
        # Get grid color from config
        grid_color_list = self.config_manager.get('game', 'grid_color', [255, 255, 255])
        grid_color = tuple(grid_color_list)

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
        """Draw a slider with enhanced visual effects and text input field."""
        # Draw label without shadow
        label_text = f"{slider['label']}:"
        label_surface = self.text_font.render(label_text, True, self.colors['text'])
        self.screen.blit(label_surface, (slider['rect'].x, slider['rect'].y - 25))

        # Draw text input field if this slider has one
        if slider.get('text_field'):
            # Calculate text field position (to the right of the label)
            label_width = self.text_font.size(label_text)[0]
            text_field_x = slider['rect'].x + label_width + 10
            text_field_y = slider['rect'].y - 25
            text_field_width = 50
            text_field_height = 22

            # Draw text field background
            text_field_rect = pygame.Rect(text_field_x, text_field_y, text_field_width, text_field_height)
            text_field_color = (255, 255, 255)  # White background

            # Highlight if this is the active text field
            if self.active_text_field == slider:
                pygame.draw.rect(self.screen, (220, 220, 255), text_field_rect)  # Light blue highlight
            else:
                pygame.draw.rect(self.screen, text_field_color, text_field_rect)

            # Draw border
            pygame.draw.rect(self.screen, self.colors['border'], text_field_rect, 1)

            # Draw text
            if self.active_text_field == slider:
                # Show current text input with cursor
                display_text = self.text_input
                if self.text_input_cursor_visible:
                    display_text += "|"  # Simple cursor
            else:
                # Show current value
                display_text = str(slider['value'])

            text_surface = self.text_font.render(display_text, True, self.colors['text'])
            # Center text vertically and align left horizontally with padding
            text_x = text_field_x + 5
            text_y = text_field_y + (text_field_height - text_surface.get_height()) // 2
            self.screen.blit(text_surface, (text_x, text_y))

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
        """Show dialog to open an existing level using a Windows file dialog."""
        try:
            # Initialize tkinter
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Make sure the dialog appears in front of the pygame window
            root.attributes('-topmost', True)

            # Show the file open dialog
            file_path = filedialog.askopenfilename(
                title="Open Level",
                initialdir=self.levels_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            # If a file was selected, open it
            if file_path:
                try:
                    self.current_level = Level(level_file=file_path)
                    # Update the editor's internal dimensions to match the loaded level
                    self.map_width = self.current_level.width
                    self.map_height = self.current_level.height
                    # Update slider values to match the new dimensions
                    for slider in self.sliders:
                        if slider['label'] == 'Width':
                            slider['value'] = self.map_width
                        elif slider['label'] == 'Height':
                            slider['value'] = self.map_height
                    self.unsaved_changes = False
                    self._reset_view()
                except Exception as e:
                    print(f"Error opening level: {e}")
        finally:
            # Clean up tkinter
            try:
                root.destroy()
            except:
                pass

    def _show_save_level_dialog(self):
        """Show dialog to save the current level using a Windows file dialog."""
        if not self.current_level:
            return

        # Check if the level is valid before allowing save
        if not self._validate_level(show_dialog=False):
            try:
                # Initialize tkinter
                root = tk.Tk()
                root.withdraw()  # Hide the main window

                # Make sure the dialog appears in front of the pygame window
                root.attributes('-topmost', True)

                # Show warning message
                messagebox.showwarning(
                    "Invalid Level",
                    "Cannot save an invalid level. Please ensure:\n\n"
                    "- The level has a player\n"
                    "- The level has at least one box\n"
                    "- The level has at least one target\n"
                    "- The number of boxes matches the number of targets"
                )
            finally:
                # Clean up tkinter
                try:
                    root.destroy()
                except:
                    pass
            return

        try:
            # Initialize tkinter
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Make sure the dialog appears in front of the pygame window
            root.attributes('-topmost', True)

            # Show the file save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Level",
                initialdir=self.levels_dir,
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            # If a file was selected, save it
            if file_path:
                # Pass the full file path to _save_level
                self._save_level(file_path)
        finally:
            # Clean up tkinter
            try:
                root.destroy()
            except:
                pass

    def _save_level(self, file_path):
        """Save the current level to a file."""
        if not file_path:
            return

        # Add .txt extension if not provided
        if not file_path.endswith('.txt'):
            file_path += '.txt'

        # Save the level without FESS coordinate labels
        level_string = self.current_level.get_state_string(show_fess_coordinates=False)

        try:
            with open(file_path, 'w') as file:
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

    def _draw_metrics_panel(self):
        """Draw the metrics content in the right panel."""
        if not self.current_level:
            return

        # Calculate responsive metrics panel dimensions based on screen size
        if self.screen_width >= 1920 or self.screen_height >= 1080:
            # High resolution
            title_padding = 25
            content_padding = 20
            line_spacing = 24
        elif self.screen_width >= 1200 or self.screen_height >= 800:
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
        separator_y = self.metrics_y - title_padding
        pygame.draw.line(self.screen, self.colors['border'],
                        (self.right_panel_x + self.ui_margin, separator_y), 
                        (self.right_panel_x + self.right_panel_width - self.ui_margin, separator_y), 2)

        # Draw metrics title
        metrics_title = self.text_font.render("Level Metrics", True, self.colors['text'])
        self.screen.blit(metrics_title, (self.right_panel_x + self.ui_margin, self.metrics_y))

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

        # Draw metrics content
        content_y = self.metrics_y + title_padding + 5

        for section in metrics_sections:
            # Draw section title
            section_title = section['title']
            section_color = (100, 100, 200)  # Light blue

            section_surface = self.text_font.render(section_title, True, section_color)
            self.screen.blit(section_surface, (self.right_panel_x + self.ui_margin, content_y))

            content_y += line_spacing

            # Draw section items
            for item in section['items']:
                # Determine if this is a status item that needs highlighting
                if "Valid: No" in item:
                    text_color = (255, 100, 100)  # Red for invalid
                elif "Valid: Yes" in item:
                    text_color = (100, 255, 100)  # Green for valid
                else:
                    text_color = self.colors['text']  # Default color

                # Draw item text
                text_surface = self.small_font.render(item, True, text_color)
                self.screen.blit(text_surface, (self.right_panel_x + self.ui_margin + content_padding, content_y))

                content_y += line_spacing

            # Add space between sections
            content_y += line_spacing // 2

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

                # Handle cursor blinking for text input
                if self.active_text_field:
                    self.text_input_cursor_timer += 1
                    if self.text_input_cursor_timer >= 30:  # Toggle cursor every 30 frames (about 0.5 seconds at 60 FPS)
                        self.text_input_cursor_visible = not self.text_input_cursor_visible
                        self.text_input_cursor_timer = 0

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

    def _apply_text_input(self):
        """Apply the current text input to the active slider."""
        if not self.active_text_field:
            return

        try:
            # Try to convert the text input to an integer
            value = int(self.text_input)

            # Clamp the value to the slider's min and max
            value = max(self.active_text_field['min'], min(self.active_text_field['max'], value))

            # Update the slider's value
            if value != self.active_text_field['value']:
                self.active_text_field['value'] = value
                self.active_text_field['callback'](value)
        except ValueError:
            # If the text input is not a valid integer, revert to the current value
            pass

    def _handle_key_event(self, event):
        """Handle keyboard events."""
        # Handle text input if a text field is active
        if self.active_text_field:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Apply the text input and clear the active text field
                self._apply_text_input()
                self.active_text_field = None
            elif event.key == pygame.K_ESCAPE:
                # Cancel text input and revert to the current value
                self.active_text_field = None
            elif event.key == pygame.K_BACKSPACE:
                # Remove the last character
                self.text_input = self.text_input[:-1]
                self.text_input_cursor_visible = True
                self.text_input_cursor_timer = 0
            elif event.unicode.isdigit():
                # Add the digit to the text input
                self.text_input += event.unicode
                self.text_input_cursor_visible = True
                self.text_input_cursor_timer = 0
            return

        # Regular key handling
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

        # Check slider and text field clicks
        for slider in self.sliders:
            # Check for text field clicks if this slider has a text field
            if slider.get('text_field'):
                # Calculate text field position (same as in _draw_slider)
                label_text = f"{slider['label']}:"
                label_width = self.text_font.size(label_text)[0]
                text_field_x = slider['rect'].x + label_width + 10
                text_field_y = slider['rect'].y - 25
                text_field_width = 50
                text_field_height = 22
                text_field_rect = pygame.Rect(text_field_x, text_field_y, text_field_width, text_field_height)

                if text_field_rect.collidepoint(mouse_pos):
                    # Clicked on text field
                    self.active_text_field = slider
                    self.text_input = str(slider['value'])
                    self.text_input_cursor_visible = True
                    self.text_input_cursor_timer = 0
                    return

            # Check for slider track clicks
            if slider['rect'].collidepoint(mouse_pos):
                self.active_slider = slider
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
                self.active_mouse_button = event.button
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
            self.active_mouse_button = None
            self.active_slider = None

            # If we have an active text field and clicked elsewhere, apply the value
            if self.active_text_field:
                mouse_pos = pygame.mouse.get_pos()

                # Calculate text field position (same as in _draw_slider)
                slider = self.active_text_field
                label_text = f"{slider['label']}:"
                label_width = self.text_font.size(label_text)[0]
                text_field_x = slider['rect'].x + label_width + 10
                text_field_y = slider['rect'].y - 25
                text_field_width = 50
                text_field_height = 22
                text_field_rect = pygame.Rect(text_field_x, text_field_y, text_field_width, text_field_height)

                # If clicked outside the text field, apply the value
                if not text_field_rect.collidepoint(mouse_pos):
                    self._apply_text_input()
                    self.active_text_field = None

    def _handle_mouse_motion(self, event):
        """Handle mouse motion events."""
        mouse_pos = pygame.mouse.get_pos()

        if self.mouse_dragging and self.drag_start_pos and self.drag_start_scroll:
            # Handle middle mouse dragging for panning
            dx = mouse_pos[0] - self.drag_start_pos[0]
            dy = mouse_pos[1] - self.drag_start_pos[1]

            self.scroll_x = self.drag_start_scroll[0] + dx
            self.scroll_y = self.drag_start_scroll[1] + dy

            # No scroll limits - allow infinite scrolling in all directions

        elif self.active_slider:
            # Continue adjusting slider while dragging
            self._handle_slider_click(mouse_pos, self.active_slider)

        elif self.paint_mode and self._is_in_map_area(mouse_pos) and self.active_mouse_button:
            # Continue painting while dragging
            self._handle_grid_click(mouse_pos, self.active_mouse_button, is_drag=True)

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

            # Save new dimensions to config
            from ..core.config_manager import get_config_manager
            config_manager = get_config_manager()
            config_manager.set_display_config(width=self.screen_width, height=self.screen_height)

        self._update_ui_layout()

    def set_highlight_enabled(self, enabled):
        """
        Enable or disable the interactive highlighting system.

        Args:
            enabled (bool): Whether highlighting should be active.
        """
        self.highlight_system.set_enabled(enabled)

    def set_highlight_alpha(self, alpha):
        """
        Set the transparency level of the highlight overlay.

        Args:
            alpha (int): Alpha transparency value (0-255).
        """
        self.highlight_system.set_alpha(alpha)

    def set_element_preview(self, enabled):
        """
        Enable or disable element preview in the highlight.

        Args:
            enabled (bool): Whether to show element preview.
        """
        self.highlight_system.set_element_preview(enabled)

    def get_highlighted_tile(self):
        """
        Get the currently highlighted tile coordinates.

        Returns:
            tuple or None: (grid_x, grid_y) if a tile is highlighted, None otherwise.
        """
        return self.highlight_system.get_highlighted_tile()


# Main function to run the enhanced level editor standalone
def main():
    """Main function to run the enhanced level editor."""
    editor = EnhancedLevelEditor()
    editor.start()


if __name__ == "__main__":
    main()
