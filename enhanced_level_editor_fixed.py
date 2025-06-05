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
from constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE, TITLE
from level import Level
from level_manager import LevelManager
from enhanced_skin_manager import EnhancedSkinManager
from procedural_generator import ProceduralGenerator

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
        
        # Fonts
        self.title_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        
        # Create a new empty level by default
        self._create_new_level(self.map_width, self.map_height)
        
    def _create_ui_elements(self):
        """Create UI elements (buttons, sliders, etc.) with improved spacing."""
        self.buttons = []
        self.sliders = []
        
        # Left panel buttons with better spacing
        button_width = self.tool_panel_width - 30
        button_height = 32
        button_x = 15
        start_y = 50
        spacing = 38  # Reduced spacing to prevent overlap
        
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
        
        # Tools section - moved higher to prevent overlap
        tools_section_y = file_section_y + spacing * 3.5
        self.buttons.extend([
            {'rect': pygame.Rect(button_x, tools_section_y, button_width, button_height),
             'text': 'Test Level', 'action': self._toggle_test_mode, 'section': 'tools'},
            {'rect': pygame.Rect(button_x, tools_section_y + spacing, button_width, button_height),
             'text': 'Validate', 'action': self._validate_level, 'section': 'tools'},
            {'rect': pygame.Rect(button_x, tools_section_y + spacing * 2, button_width, button_height),
             'text': 'Generate', 'action': self._show_generate_dialog, 'section': 'tools'},
        ])
        
        # View controls section - moved to right panel
        right_panel_x = self.screen_width - self.right_panel_width + 10
        view_section_y = start_y
        view_button_width = self.right_panel_width - 20
        
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
        
        # Bottom panel buttons - better distributed
        bottom_y = self.screen_height - self.bottom_panel_height + 15
        button_spacing = 120
        self.buttons.extend([
            {'rect': pygame.Rect(self.ui_margin, bottom_y, 80, 25),
             'text': 'Help', 'action': self._toggle_help, 'section': 'bottom'},
            {'rect': pygame.Rect(self.ui_margin + button_spacing, bottom_y, 80, 25),
             'text': 'Metrics', 'action': self._toggle_metrics, 'section': 'bottom'},
            {'rect': pygame.Rect(self.screen_width - 100, bottom_y, 80, 25),
             'text': 'Exit', 'action': self._exit_editor, 'section': 'bottom'}
        ])
        
        # Size sliders - moved to right panel
        slider_y = view_section_y + spacing * 4
        slider_width = view_button_width
        self.sliders = [
            {'rect': pygame.Rect(right_panel_x, slider_y, slider_width, 18),
             'label': 'Width', 'value': self.map_width, 'min': self.min_map_size, 'max': self.max_map_size,
             'callback': self._on_width_change},
            {'rect': pygame.Rect(right_panel_x, slider_y + 35, slider_width, 18),
             'label': 'Height', 'value': self.map_height, 'min': self.min_map_size, 'max': self.max_map_size,
             'callback': self._on_height_change}
        ]
        
    def _update_ui_layout(self):
        """Update UI layout when screen is resized."""
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
        
        # Left panel title
        title_surface = self.title_font.render("Level Editor", True, self.colors['text'])
        self.screen.blit(title_surface, (15, 15))
        
        # Right panel title
        view_title_surface = self.text_font.render("View & Size", True, self.colors['text'])
        self.screen.blit(view_title_surface, (right_panel_x + 10, 15))
        
        # Element palette - better positioned
        palette_start_y = 320  # Moved down to avoid overlap with buttons
        palette_title = self.text_font.render("Elements:", True, self.colors['text'])
        self.screen.blit(palette_title, (20, palette_start_y - 25))
        
        for i, element in enumerate(self.palette):
            y = palette_start_y + i * 38  # Slightly reduced spacing
            item_rect = pygame.Rect(20, y, self.tool_panel_width - 40, 33)
            
            # Highlight selected element
            if element['char'] == self.current_element:
                pygame.draw.rect(self.screen, self.colors['selected'], item_rect)
            else:
                pygame.draw.rect(self.screen, (255, 255, 255), item_rect)
            
            pygame.draw.rect(self.screen, self.colors['border'], item_rect, 1)
            
            # Draw element icon
            icon_rect = pygame.Rect(item_rect.x + 5, item_rect.y + 4, 25, 25)
            pygame.draw.rect(self.screen, element['color'], icon_rect)
            pygame.draw.rect(self.screen, self.colors['border'], icon_rect, 1)
            
            # Draw element name
            name_surface = self.text_font.render(element['name'], True, self.colors['text'])
            self.screen.blit(name_surface, (item_rect.x + 35, item_rect.y + 8))
        
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
            f"Zoom: {self.zoom_level:.1f}x