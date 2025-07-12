"""
Interactive highlighting system for the Sokoban game.

This module provides functionality for displaying a semi-transparent yellow overlay
on the tile currently hovered by the mouse cursor. The highlighting works in both
gameplay and level editor contexts with smooth transitions and optimized performance.
"""

import pygame
from src.core.constants import CELL_SIZE


class InteractiveHighlight:
    """
    Class for managing interactive tile highlighting with mouse hover effects.

    This class handles mouse position tracking, screen-to-grid coordinate conversion,
    and rendering of semi-transparent highlighting overlays.
    """

    def __init__(self, alpha=128):
        """
        Initialize the interactive highlight system.

        Args:
            alpha (int, optional): Alpha transparency value (0-255). Defaults to 128.
        """
        self.alpha = alpha
        self.highlight_color = (255, 255, 0, alpha)  # Yellow with alpha
        self.current_highlight_pos = None  # (grid_x, grid_y) or None
        self.last_mouse_pos = None
        self.enabled = True

        # Create a reusable surface for the highlight overlay
        self.highlight_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        self.highlight_surface.fill(self.highlight_color)

    def set_enabled(self, enabled):
        """
        Enable or disable the highlighting system.

        Args:
            enabled (bool): Whether highlighting should be active.
        """
        self.enabled = enabled
        if not enabled:
            self.current_highlight_pos = None

    def set_alpha(self, alpha):
        """
        Update the alpha transparency of the highlight.

        Args:
            alpha (int): Alpha transparency value (0-255).
        """
        self.alpha = max(0, min(255, alpha))
        self.highlight_color = (255, 255, 0, self.alpha)
        self.highlight_surface.fill(self.highlight_color)

    def update_mouse_position(self, mouse_pos, map_area_x, map_area_y, map_area_width, 
                            map_area_height, level_width, level_height, cell_size, 
                            scroll_x=0, scroll_y=0):
        """
        Update the highlighting based on current mouse position.

        Args:
            mouse_pos (tuple): Current mouse position (x, y).
            map_area_x (int): X coordinate of the map area.
            map_area_y (int): Y coordinate of the map area.
            map_area_width (int): Width of the map area.
            map_area_height (int): Height of the map area.
            level_width (int): Width of the level in tiles.
            level_height (int): Height of the level in tiles.
            cell_size (int): Size of each cell in pixels.
            scroll_x (int, optional): Horizontal scroll offset. Defaults to 0.
            scroll_y (int, optional): Vertical scroll offset. Defaults to 0.
        """
        if not self.enabled:
            self.current_highlight_pos = None
            return

        self.last_mouse_pos = mouse_pos

        # Check if mouse is within the map area
        if not (map_area_x <= mouse_pos[0] <= map_area_x + map_area_width and
                map_area_y <= mouse_pos[1] <= map_area_y + map_area_height):
            self.current_highlight_pos = None
            return

        # Convert screen coordinates to grid coordinates
        map_start_x = map_area_x + scroll_x
        map_start_y = map_area_y + scroll_y

        grid_x = int((mouse_pos[0] - map_start_x) // cell_size)
        grid_y = int((mouse_pos[1] - map_start_y) // cell_size)

        # Check if the calculated grid position is within level bounds
        if 0 <= grid_x < level_width and 0 <= grid_y < level_height:
            new_pos = (grid_x, grid_y)
            # Only update if position changed to avoid unnecessary redraws
            if new_pos != self.current_highlight_pos:
                self.current_highlight_pos = new_pos
        else:
            self.current_highlight_pos = None

    def render_highlight(self, screen, map_area_x, map_area_y, cell_size, scroll_x=0, scroll_y=0):
        """
        Render the highlight overlay on the screen.

        Args:
            screen (pygame.Surface): The screen surface to draw on.
            map_area_x (int): X coordinate of the map area.
            map_area_y (int): Y coordinate of the map area.
            cell_size (int): Size of each cell in pixels.
            scroll_x (int, optional): Horizontal scroll offset. Defaults to 0.
            scroll_y (int, optional): Vertical scroll offset. Defaults to 0.
        """
        if not self.enabled or self.current_highlight_pos is None:
            return

        grid_x, grid_y = self.current_highlight_pos

        # Calculate screen position for the highlight
        map_start_x = map_area_x + scroll_x
        map_start_y = map_area_y + scroll_y

        highlight_x = map_start_x + grid_x * cell_size
        highlight_y = map_start_y + grid_y * cell_size

        # Scale the highlight surface if cell size is different from default
        if cell_size != CELL_SIZE:
            scaled_highlight = pygame.transform.scale(self.highlight_surface, (cell_size, cell_size))
            screen.blit(scaled_highlight, (highlight_x, highlight_y))
        else:
            screen.blit(self.highlight_surface, (highlight_x, highlight_y))

    def get_highlighted_tile(self):
        """
        Get the currently highlighted tile coordinates.

        Returns:
            tuple or None: (grid_x, grid_y) if a tile is highlighted, None otherwise.
        """
        return self.current_highlight_pos

    def clear_highlight(self):
        """
        Clear the current highlight.
        """
        self.current_highlight_pos = None


class EditorHighlight(InteractiveHighlight):
    """
    Extended highlighting system specifically for the level editor.

    This class adds editor-specific features like different highlight colors
    for different modes and preview functionality.
    """

    def __init__(self, alpha=128):
        """
        Initialize the editor highlight system.

        Args:
            alpha (int, optional): Alpha transparency value (0-255). Defaults to 128.
        """
        super().__init__(alpha)

        # Different highlight colors for different editor modes
        self.mode_colors = {
            'edit': (255, 255, 0, alpha),      # Yellow for edit mode
            'test': (0, 255, 255, alpha),      # Cyan for test mode
            'paint': (255, 128, 0, alpha),     # Orange for paint mode
        }

        self.current_mode = 'edit'
        self.show_element_preview = True

        # Create surfaces for different modes
        self.mode_surfaces = {}
        for mode, color in self.mode_colors.items():
            surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            surface.fill(color)
            self.mode_surfaces[mode] = surface

    def set_mode(self, mode):
        """
        Set the current editor mode for appropriate highlight color.

        Args:
            mode (str): Editor mode ('edit', 'test', 'paint').
        """
        if mode in self.mode_colors:
            self.current_mode = mode

    def set_element_preview(self, enabled):
        """
        Enable or disable element preview in the highlight.

        Args:
            enabled (bool): Whether to show element preview.
        """
        self.show_element_preview = enabled

    def render_highlight(self, screen, map_area_x, map_area_y, cell_size, scroll_x=0, scroll_y=0, 
                        current_element=None, skin_manager=None):
        """
        Render the editor highlight overlay with optional element preview.

        Args:
            screen (pygame.Surface): The screen surface to draw on.
            map_area_x (int): X coordinate of the map area.
            map_area_y (int): Y coordinate of the map area.
            cell_size (int): Size of each cell in pixels.
            scroll_x (int, optional): Horizontal scroll offset. Defaults to 0.
            scroll_y (int, optional): Vertical scroll offset. Defaults to 0.
            current_element (str, optional): Current selected element for preview.
            skin_manager (object, optional): Skin manager for element sprites.
        """
        if not self.enabled or self.current_highlight_pos is None:
            return

        grid_x, grid_y = self.current_highlight_pos

        # Calculate screen position for the highlight
        map_start_x = map_area_x + scroll_x
        map_start_y = map_area_y + scroll_y

        highlight_x = map_start_x + grid_x * cell_size
        highlight_y = map_start_y + grid_y * cell_size

        # Get the appropriate highlight surface for current mode
        highlight_surface = self.mode_surfaces.get(self.current_mode, self.highlight_surface)

        # Scale the highlight surface if needed
        if cell_size != CELL_SIZE:
            scaled_highlight = pygame.transform.scale(highlight_surface, (cell_size, cell_size))
        else:
            scaled_highlight = highlight_surface

        # Draw the base highlight
        screen.blit(scaled_highlight, (highlight_x, highlight_y))

        # Draw element preview if enabled and in edit mode
        if (self.show_element_preview and self.current_mode == 'edit' and 
            current_element and skin_manager):

            skin = skin_manager.get_skin()
            if current_element in skin:
                # Get the element sprite
                element_sprite = skin[current_element]

                # Scale the sprite if needed
                if cell_size != CELL_SIZE:
                    element_sprite = pygame.transform.scale(element_sprite, (cell_size, cell_size))

                # Create a semi-transparent version for preview
                preview_surface = element_sprite.copy()
                preview_surface.set_alpha(128)  # Make it semi-transparent

                # Draw the preview
                screen.blit(preview_surface, (highlight_x, highlight_y))


class GameplayHighlight(InteractiveHighlight):
    """
    Highlighting system specifically for gameplay mode.

    This class provides gameplay-specific highlighting features like
    movement hints and interaction feedback.
    """

    def __init__(self, alpha=96):
        """
        Initialize the gameplay highlight system.

        Args:
            alpha (int, optional): Alpha transparency value (0-255). Defaults to 96.
        """
        super().__init__(alpha)

        # Slightly more subtle highlighting for gameplay
        self.highlight_color = (255, 255, 0, alpha)
        self.highlight_surface.fill(self.highlight_color)

        # Additional features for gameplay
        self.show_movement_hints = False
        self.player_pos = None

    def set_player_position(self, player_pos):
        """
        Set the current player position for movement hint calculations.

        Args:
            player_pos (tuple): Player position (x, y).
        """
        self.player_pos = player_pos

    def set_movement_hints(self, enabled):
        """
        Enable or disable movement hints.

        Args:
            enabled (bool): Whether to show movement hints.
        """
        self.show_movement_hints = enabled

    def is_adjacent_to_player(self):
        """
        Check if the currently highlighted tile is adjacent to the player.

        Returns:
            bool: True if highlighted tile is adjacent to player, False otherwise.
        """
        if not self.current_highlight_pos or not self.player_pos:
            return False

        hx, hy = self.current_highlight_pos
        px, py = self.player_pos

        # Check if tiles are adjacent (Manhattan distance = 1)
        return abs(hx - px) + abs(hy - py) == 1

    def render_highlight(self, screen, map_area_x, map_area_y, cell_size, scroll_x=0, scroll_y=0):
        """
        Render the gameplay highlight with optional movement hints.

        Args:
            screen (pygame.Surface): The screen surface to draw on.
            map_area_x (int): X coordinate of the map area.
            map_area_y (int): Y coordinate of the map area.
            cell_size (int): Size of each cell in pixels.
            scroll_x (int, optional): Horizontal scroll offset. Defaults to 0.
            scroll_y (int, optional): Vertical scroll offset. Defaults to 0.
        """
        # Disabled yellow square highlight as per requirements
        # The white path line from MouseNavigationSystem will be used instead
        return
