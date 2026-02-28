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

The editor is decomposed into an orchestrator (this class) plus three delegate
classes using composition:
- EditorRenderer: handles all drawing/rendering
- EditorEventHandler: handles all event processing
- EditorOperations: handles level manipulation operations
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
from ..ui.interactive_highlight import EditorHighlight
from .editor_renderer import EditorRenderer
from .editor_event_handler import EditorEventHandler
from .editor_operations import EditorOperations

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

        # Interactive highlighting system for editor
        self.highlight_system = EditorHighlight()

        # Initialize delegate objects (composition pattern)
        # Must be created before _update_fonts() and _create_new_level() which delegate to them
        self.renderer = EditorRenderer(self)
        self.event_handler = EditorEventHandler(self)
        self.operations = EditorOperations(self)

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

    # ---- Delegation wrappers for renderer methods ----

    def _update_fonts(self):
        """Update fonts based on screen size."""
        self.renderer.update_fonts()

    def _draw_editor(self):
        """Draw the enhanced editor interface."""
        self.renderer.draw_editor()

    def _draw_tool_panel(self):
        """Draw the improved tool panel on the left side."""
        self.renderer.draw_tool_panel()

    def _draw_map_area(self):
        """Draw the map area in the center with proper clipping."""
        self.renderer.draw_map_area()

    def _draw_grid(self, start_x, start_y, cell_size):
        """Draw grid lines between tiles using color from config."""
        self.renderer.draw_grid(start_x, start_y, cell_size)

    def _draw_bottom_panel(self):
        """Draw the improved bottom panel with status and controls."""
        self.renderer.draw_bottom_panel()

    def _draw_button(self, button):
        """Draw a button with enhanced visual effects."""
        self.renderer.draw_button(button)

    def _draw_slider(self, slider):
        """Draw a slider with enhanced visual effects and text input field."""
        self.renderer.draw_slider(slider)

    def _draw_help_overlay(self):
        """Draw the help overlay with responsive sizing and enhanced visuals."""
        self.renderer.draw_help_overlay()

    def _draw_metrics_overlay(self):
        """Draw the metrics overlay with current level information and enhanced visuals."""
        self.renderer.draw_metrics_overlay()

    def _draw_metrics_panel(self):
        """Draw the metrics content in the right panel."""
        self.renderer.draw_metrics_panel()

    # ---- Delegation wrappers for event handler methods ----

    def _handle_key_event(self, event):
        """Handle keyboard events."""
        self.event_handler.handle_key_event(event)

    def _handle_mouse_down(self, event):
        """Handle mouse button down events."""
        self.event_handler.handle_mouse_down(event)

    def _handle_mouse_up(self, event):
        """Handle mouse button up events."""
        self.event_handler.handle_mouse_up(event)

    def _handle_mouse_motion(self, event):
        """Handle mouse motion events."""
        self.event_handler.handle_mouse_motion(event)

    def _handle_mouse_wheel(self, event):
        """Handle mouse wheel events for zooming."""
        self.event_handler.handle_mouse_wheel(event)

    def _handle_resize(self, event):
        """Handle window resize events."""
        self.event_handler.handle_resize(event)

    def _handle_grid_click(self, mouse_pos, mouse_button, is_drag=False):
        """Handle clicks on the grid with paint mode support."""
        self.event_handler.handle_grid_click(mouse_pos, mouse_button, is_drag)

    def _handle_palette_click(self, mouse_pos):
        """Handle clicks on the element palette."""
        self.event_handler.handle_palette_click(mouse_pos)

    def _handle_slider_click(self, mouse_pos, slider):
        """Handle slider interaction."""
        self.event_handler.handle_slider_click(mouse_pos, slider)

    def _apply_text_input(self):
        """Apply the current text input to the active slider."""
        self.event_handler.apply_text_input()

    # ---- Delegation wrappers for operations methods ----

    def _place_element(self, x, y):
        """Place the current element at the specified grid coordinates."""
        self.operations.place_element(x, y)

    def _place_floor(self, x, y):
        """Place floor at the specified coordinates, removing any existing elements."""
        self.operations.place_floor(x, y)

    def _clear_element(self, x, y):
        """Clear the element at the specified grid coordinates and set to floor."""
        self.operations.clear_element(x, y)

    def _create_new_level(self, width, height):
        """Create a new empty level."""
        self.operations.create_new_level(width, height)

    def _show_open_level_dialog(self):
        """Show dialog to open an existing level using a Windows file dialog."""
        self.operations.show_open_dialog()

    def _show_save_level_dialog(self):
        """Show dialog to save the current level using a Windows file dialog."""
        self.operations.show_save_dialog()

    def _save_level(self, file_path):
        """Save the current level to a file."""
        self.operations.save_level(file_path)

    def _validate_level(self, show_dialog=True):
        """Validate the current level."""
        return self.operations.validate_level(show_dialog)

    def _solve_level(self):
        """Solve the current level and let AI take control to solve it automatically."""
        self.operations.solve_level()

    def _show_generate_dialog(self):
        """Show dialog to generate a random level."""
        self.operations.show_generate_dialog()

    def _toggle_test_mode(self):
        """Toggle test mode to play the current level."""
        self.operations.toggle_test_mode()

    # ---- Methods that remain directly in the orchestrator ----

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

    def _show_new_level_dialog(self):
        """Show dialog to create a new level."""
        self._create_new_level(self.map_width, self.map_height)

    def _toggle_grid(self):
        """Toggle grid display."""
        self.show_grid = not self.show_grid

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

    def _is_in_map_area(self, pos):
        """Check if position is in the map area."""
        return (self.map_area_x <= pos[0] <= self.map_area_x + self.map_area_width and
                self.map_area_y <= pos[1] <= self.map_area_y + self.map_area_height)

    def _handle_scroll(self, dx, dy):
        """Handle scrolling the map view."""
        self.scroll_x += dx
        self.scroll_y += dy

        # No scroll limits - allow infinite scrolling in all directions

    # ---- Highlight API ----

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

    # ---- Main loop ----

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


# Main function to run the enhanced level editor standalone
def main():
    """Main function to run the enhanced level editor."""
    editor = EnhancedLevelEditor()
    editor.start()


if __name__ == "__main__":
    main()
