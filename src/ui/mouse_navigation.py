"""
Advanced Mouse Navigation System for Sokoban Game.

This module implements a sophisticated mouse navigation system with:
- Dynamic white guideline from player to cursor
- Intelligent pathfinding with optimal route calculation
- Left-click navigation along calculated path
- Automatic obstacle handling (stops before boxes when no bypass possible)
- Drag-and-drop box manipulation system
- Seamless integration with existing game mechanics
"""

import pygame
import math
from collections import deque
from typing import List, Tuple, Optional, Set
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET
from src.core.config_manager import get_config_manager


class PathNode:
    """Represents a node in the pathfinding algorithm."""

    def __init__(self, x: int, y: int, g_cost: float = 0, h_cost: float = 0, parent=None):
        self.x = x
        self.y = y
        self.g_cost = g_cost  # Distance from start
        self.h_cost = h_cost  # Heuristic distance to goal
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent = parent

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class MouseNavigationSystem:
    """
    Advanced mouse navigation system for Sokoban with pathfinding and drag-drop.
    """

    def __init__(self):
        """Initialize the mouse navigation system."""
        self.enabled = True
        self.current_path = []  # List of (x, y) coordinates
        self.target_position = None  # Current mouse target position
        self.player_position = None  # Current player position
        self.level = None  # Reference to current level

        # Pathfinding settings
        self.max_path_length = 100  # Maximum path length to prevent infinite searches

        # Guideline rendering settings
        self.guideline_color = (255, 255, 255)  # White color (no alpha for main color)
        self.guideline_width = 5  # Increased width for better visibility
        self.highlight_color = (255, 255, 255, 100)  # Highlighted tiles

        # Drag and drop system
        self.is_dragging = False
        self.drag_start_pos = None
        self.dragged_box_pos = None
        self.drag_direction = None
        self.last_drag_pos = None
        self.drag_threshold = 10  # Minimum pixels to start drag

        # Animation and movement
        self.is_moving = False
        self.movement_queue = []  # Queue of movements to execute
        # Get mouse movement speed from config, default to 100ms if not set
        self.movement_speed = get_config_manager().get('game', 'mouse_movement_speed', 100)
        self.last_move_time = 0
        self.last_movement_direction = None  # Track last movement direction

        # Visual feedback
        self.show_path_tiles = False  # Disable yellow square highlights
        self.show_guideline = True    # Enable white path line

        # Box navigation
        self.hovering_over_movable_box = False
        self.movable_box_position = None

    def set_enabled(self, enabled: bool):
        """Enable or disable the mouse navigation system."""
        self.enabled = enabled
        if not enabled:
            self.clear_navigation()

    def set_level(self, level):
        """Set the current level for navigation calculations."""
        self.level = level
        self.player_position = level.player_pos if level else None

    def update_movement_speed(self):
        """Update the movement speed from the configuration."""
        self.movement_speed = get_config_manager().get('game', 'mouse_movement_speed', 100)

    def clear_navigation(self):
        """Clear all navigation data."""
        self.current_path = []
        self.target_position = None
        self.is_dragging = False
        self.drag_start_pos = None
        self.dragged_box_pos = None
        self.movement_queue = []
        self.is_moving = False

    def update_mouse_position(self, mouse_pos: Tuple[int, int], map_area_x: int, 
                            map_area_y: int, cell_size: int, scroll_x: int = 0, 
                            scroll_y: int = 0) -> Optional[Tuple[int, int]]:
        """
        Update navigation based on mouse position.

        Returns:
            Grid coordinates of mouse position if valid, None otherwise.
        """
        if not self.enabled or not self.level:
            return None

        # Convert screen coordinates to grid coordinates
        map_start_x = map_area_x + scroll_x
        map_start_y = map_area_y + scroll_y

        grid_x = int((mouse_pos[0] - map_start_x) // cell_size)
        grid_y = int((mouse_pos[1] - map_start_y) // cell_size)

        # Check if position is within level bounds
        if not (0 <= grid_x < self.level.width and 0 <= grid_y < self.level.height):
            self.target_position = None
            self.current_path = []
            self.hovering_over_movable_box = False
            self.movable_box_position = None
            return None

        grid_pos = (grid_x, grid_y)

        # Update player position
        self.player_position = self.level.player_pos

        # Check if hovering over a movable box
        is_box = self._is_box_at(grid_pos)
        is_movable = is_box and self._is_box_movable(grid_pos)

        # Update box hovering state
        self.hovering_over_movable_box = is_movable
        self.movable_box_position = grid_pos if is_movable else None

        # Only recalculate path if target changed and player is not currently moving
        if grid_pos != self.target_position and not self.is_moving:
            self.target_position = grid_pos
            if not self.is_dragging:
                if self.hovering_over_movable_box:
                    # First calculate path from player to box
                    path_to_box = self._calculate_path(self.player_position, self.movable_box_position)

                    # If we can reach the box, calculate the box path
                    if path_to_box:
                        # Get the direction to push the box
                        push_direction = self._get_box_push_direction(self.movable_box_position, grid_pos)

                        if push_direction:
                            # Calculate the path the box can take
                            box_path = self._calculate_box_path(self.movable_box_position, push_direction)

                            # Set the current path to the box path
                            self.current_path = box_path
                        else:
                            # If we can't push the box in any direction, just show the box
                            self.current_path = [self.movable_box_position]
                    else:
                        # If we can't reach the box, calculate normal path from player
                        self.current_path = self._calculate_path(self.player_position, grid_pos)
                else:
                    # Normal path calculation from player
                    self.current_path = self._calculate_path(self.player_position, grid_pos)

        return grid_pos

    def handle_mouse_click(self, mouse_pos: Tuple[int, int], button: int, 
                          map_area_x: int, map_area_y: int, cell_size: int,
                          scroll_x: int = 0, scroll_y: int = 0) -> bool:
        """
        Handle mouse click events for navigation and drag-drop.

        Returns:
            True if the click was handled, False otherwise.
        """
        if not self.enabled or not self.level or self.is_moving:
            return False

        grid_pos = self.update_mouse_position(mouse_pos, map_area_x, map_area_y, 
                                            cell_size, scroll_x, scroll_y)

        if not grid_pos:
            return False

        if button == 1:  # Left click
            return self._handle_left_click(grid_pos)

        return False

    def handle_mouse_drag_start(self, mouse_pos: Tuple[int, int], map_area_x: int,
                               map_area_y: int, cell_size: int, scroll_x: int = 0,
                               scroll_y: int = 0) -> bool:
        """
        Handle start of mouse drag for box manipulation.

        Returns:
            True if drag started successfully, False otherwise.
        """
        if not self.enabled or not self.level or self.is_moving:
            return False

        grid_pos = self.update_mouse_position(mouse_pos, map_area_x, map_area_y,
                                            cell_size, scroll_x, scroll_y)

        if not grid_pos:
            return False

        # Check if clicking on a movable box
        if self._is_box_at(grid_pos) and self._is_box_movable(grid_pos):
            self.is_dragging = True
            self.drag_start_pos = grid_pos
            self.dragged_box_pos = grid_pos
            self.last_drag_pos = mouse_pos

            # Initialize drag direction as None - will be set on first drag movement
            self.drag_direction = None
            return True

        return False

    def handle_mouse_drag(self, mouse_pos: Tuple[int, int], map_area_x: int,
                         map_area_y: int, cell_size: int, scroll_x: int = 0,
                         scroll_y: int = 0) -> bool:
        """
        Handle mouse drag for box manipulation.

        Returns:
            True if drag was handled, False otherwise.
        """
        if not self.is_dragging or not self.level:
            return False

        # Get the current grid position of the mouse
        grid_pos = self.update_mouse_position(mouse_pos, map_area_x, map_area_y,
                                            cell_size, scroll_x, scroll_y)
        if not grid_pos:
            return False

        # If this is the first drag movement, determine the drag direction
        if self.drag_direction is None:
            # Calculate direction from box to mouse
            box_x, box_y = self.dragged_box_pos
            mouse_x, mouse_y = grid_pos

            # Determine primary direction (cardinal direction only)
            dx = mouse_x - box_x
            dy = mouse_y - box_y

            # Handle the case where dx and dy are equal
            if abs(dx) == abs(dy):
                # Choose based on which is further from zero
                if abs(dx) > 0:
                    # Prefer horizontal movement if both are equal and non-zero
                    self.drag_direction = (1 if dx > 0 else -1, 0)
                else:
                    # Both are zero, default to up
                    self.drag_direction = (0, -1)
            elif abs(dx) > abs(dy):
                # Horizontal movement dominates
                self.drag_direction = (1 if dx > 0 else -1, 0)
            else:
                # Vertical movement dominates
                self.drag_direction = (0, 1 if dy > 0 else -1)

            # No need to check if player can move to the position needed to push the box
            # since we're directly swapping player and box positions

            # Convert direction tuple to string for _try_drag_box
            dir_map = {
                (0, -1): 'up',
                (0, 1): 'down',
                (-1, 0): 'left',
                (1, 0): 'right'
            }
            direction_str = dir_map.get(self.drag_direction)

            # Try to move the box in the determined direction
            if direction_str:
                success = self._try_drag_box(direction_str)
                if success:
                    self.last_drag_pos = mouse_pos
                    return True
                else:
                    self.is_dragging = False
                    self.drag_direction = None
                    return False
        else:
            # For subsequent movements, check if the mouse has moved in the same direction
            box_x, box_y = self.dragged_box_pos
            next_box_pos = (box_x + self.drag_direction[0], box_y + self.drag_direction[1])

            # Check if the next position is in the same direction as the mouse
            dx = grid_pos[0] - box_x
            dy = grid_pos[1] - box_y

            # Only continue dragging if mouse is in the same direction as the drag
            if (self.drag_direction[0] * dx >= 0 and self.drag_direction[1] * dy >= 0):
                # Convert direction tuple to string for _try_drag_box
                dir_map = {
                    (0, -1): 'up',
                    (0, 1): 'down',
                    (-1, 0): 'left',
                    (1, 0): 'right'
                }
                direction_str = dir_map.get(self.drag_direction)

                # Try to move the box in the determined direction
                if direction_str:
                    success = self._try_drag_box(direction_str)
                    if success:
                        self.last_drag_pos = mouse_pos
                        return True

        return False

    def handle_mouse_drag_end(self) -> bool:
        """
        Handle end of mouse drag.

        Returns:
            True if drag end was handled, False otherwise.
        """
        if not self.is_dragging:
            return False

        self.is_dragging = False
        self.drag_start_pos = None
        self.dragged_box_pos = None
        self.last_drag_pos = None
        self.drag_direction = None

        # Recalculate path to current mouse target
        if self.target_position and self.player_position:
            self.current_path = self._calculate_path(self.player_position, self.target_position)

        return True

    def update_movement(self, current_time: int) -> bool:
        """
        Update automatic movement along calculated path.

        Returns:
            True if a movement was executed, False otherwise.
        """
        if (not self.movement_queue or self.is_dragging or 
            current_time - self.last_move_time < self.movement_speed):
            return False

        # Execute next movement
        direction = self.movement_queue.pop(0)
        success = self._execute_movement(direction)

        if success:
            self.last_move_time = current_time
            self.player_position = self.level.player_pos

            # If movement queue is empty, we've reached the destination
            if not self.movement_queue:
                self.is_moving = False
                # Recalculate path from new player position to target if we have a target
                if self.target_position:
                    self.current_path = self._calculate_path(self.player_position, self.target_position)
        else:
            # Movement failed, stop navigation
            self.movement_queue = []
            self.is_moving = False

        return success

    def render_navigation(self, screen: pygame.Surface, map_area_x: int, 
                         map_area_y: int, cell_size: int, scroll_x: int = 0,
                         scroll_y: int = 0):
        """Render the navigation guideline and highlighted tiles."""
        if not self.enabled or not self.level:
            return

        # Render highlighted path tiles
        if self.show_path_tiles and self.current_path:
            self._render_path_tiles(screen, map_area_x, map_area_y, cell_size, 
                                  scroll_x, scroll_y)

        # Render guideline
        if self.show_guideline and self.current_path and len(self.current_path) > 1:
            self._render_guideline(screen, map_area_x, map_area_y, cell_size,
                                 scroll_x, scroll_y)

    def _handle_left_click(self, grid_pos: Tuple[int, int]) -> bool:
        """Handle left mouse click for navigation."""
        if self.is_moving:
            return False

        # Check if clicking on current player position - do nothing
        if grid_pos == self.player_position:
            return False

        # Check if we have a valid path
        if not self.current_path or len(self.current_path) < 2:
            return False

        # Convert path to movement directions
        movements = self._path_to_movements(self.current_path)

        if movements:
            self.movement_queue = movements
            self.is_moving = True
            return True

        return False

    def _calculate_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Calculate optimal path using A* algorithm with obstacle handling.

        Returns:
            List of grid coordinates representing the path.
        """
        if not start or not goal:
            return []

        # If start and goal are the same, return empty path
        if start == goal:
            return []

        # A* pathfinding implementation
        open_set = []
        closed_set = set()

        start_node = PathNode(start[0], start[1], 0, self._heuristic(start, goal))
        open_set.append(start_node)

        nodes_dict = {start: start_node}

        while open_set:
            # Get node with lowest f_cost
            current = min(open_set, key=lambda n: n.f_cost)
            open_set.remove(current)
            closed_set.add((current.x, current.y))

            # Check if we reached the goal
            if (current.x, current.y) == goal:
                return self._reconstruct_path(current)

            # Check neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_x = current.x + dx
                neighbor_y = current.y + dy
                neighbor_pos = (neighbor_x, neighbor_y)

                # Skip if out of bounds or already processed
                if (neighbor_pos in closed_set or 
                    not self._is_valid_position(neighbor_x, neighbor_y)):
                    continue

                # Calculate costs
                g_cost = current.g_cost + 1
                h_cost = self._heuristic(neighbor_pos, goal)

                # Check if this path to neighbor is better
                if neighbor_pos in nodes_dict:
                    neighbor_node = nodes_dict[neighbor_pos]
                    if g_cost < neighbor_node.g_cost:
                        neighbor_node.g_cost = g_cost
                        neighbor_node.f_cost = g_cost + h_cost
                        neighbor_node.parent = current
                else:
                    neighbor_node = PathNode(neighbor_x, neighbor_y, g_cost, h_cost, current)
                    nodes_dict[neighbor_pos] = neighbor_node
                    open_set.append(neighbor_node)

                # Prevent infinite searches
                if len(closed_set) > self.max_path_length:
                    break

        # No path found, try to get as close as possible
        return self._find_closest_reachable_path(start, goal)

    def _find_closest_reachable_path(self, start: Tuple[int, int], 
                                   goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Find path to closest reachable position to goal."""
        # Use BFS to find closest reachable position
        queue = deque([start])
        visited = {start}
        parent_map = {start: None}
        closest_pos = start
        closest_distance = self._heuristic(start, goal)

        while queue:
            current = queue.popleft()

            # Check if this is closer to goal
            distance = self._heuristic(current, goal)
            if distance < closest_distance:
                closest_distance = distance
                closest_pos = current

            # Explore neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_x = current[0] + dx
                neighbor_y = current[1] + dy
                neighbor_pos = (neighbor_x, neighbor_y)

                if (neighbor_pos not in visited and 
                    self._is_valid_position(neighbor_x, neighbor_y)):
                    visited.add(neighbor_pos)
                    parent_map[neighbor_pos] = current
                    queue.append(neighbor_pos)

                    # Limit search area
                    if len(visited) > self.max_path_length:
                        break

        # Reconstruct path to closest position
        if closest_pos == start:
            return []

        path = []
        current = closest_pos
        while current is not None:
            path.append(current)
            current = parent_map[current]

        return list(reversed(path))

    def _is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is valid for pathfinding."""
        if not (0 <= x < self.level.width and 0 <= y < self.level.height):
            return False

        # Can't move through walls
        if self.level.is_wall(x, y):
            return False

        # Can't move through boxes (they're obstacles for pathfinding)
        if self.level.is_box(x, y):
            return False

        return True

    def _heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Manhattan distance heuristic."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _reconstruct_path(self, node: PathNode) -> List[Tuple[int, int]]:
        """Reconstruct path from goal node to start."""
        path = []
        current = node
        while current:
            path.append((current.x, current.y))
            current = current.parent
        return list(reversed(path))

    def _path_to_movements(self, path: List[Tuple[int, int]]) -> List[str]:
        """Convert path coordinates to movement directions."""
        if len(path) < 2:
            return []

        movements = []
        for i in range(1, len(path)):
            prev_x, prev_y = path[i-1]
            curr_x, curr_y = path[i]

            dx = curr_x - prev_x
            dy = curr_y - prev_y

            if dx == 1:
                movements.append('right')
            elif dx == -1:
                movements.append('left')
            elif dy == 1:
                movements.append('down')
            elif dy == -1:
                movements.append('up')

        return movements

    def _execute_movement(self, direction: str) -> bool:
        """Execute a single movement in the specified direction."""
        direction_map = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }

        if direction not in direction_map:
            return False

        dx, dy = direction_map[direction]

        # Store the direction for animation purposes
        self.last_movement_direction = direction

        return self.level.move(dx, dy)

    def _is_box_at(self, pos: Tuple[int, int]) -> bool:
        """Check if there's a box at the specified position."""
        return self.level.is_box(pos[0], pos[1])

    def _is_adjacent_to_player(self, pos: Tuple[int, int]) -> bool:
        """Check if position is adjacent to player."""
        if not self.player_position:
            return False

        px, py = self.player_position
        bx, by = pos

        return abs(px - bx) + abs(py - by) == 1

    def _is_box_movable(self, pos: Tuple[int, int]) -> bool:
        """
        Check if a box at the given position is movable.
        A box is movable if it can be pushed in at least one direction.

        Args:
            pos (Tuple[int, int]): Position of the box to check

        Returns:
            bool: True if the box is movable, False otherwise
        """
        if not self.level or not self._is_box_at(pos):
            return False

        # Check if the box can be pushed in any direction
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            # Position behind the box (where it would be pushed to)
            push_x, push_y = pos[0] + dx, pos[1] + dy

            # Position in front of the box (where the player needs to be)
            player_x, player_y = pos[0] - dx, pos[1] - dy

            # Check if the player can stand in front of the box
            if (0 <= player_x < self.level.width and 
                0 <= player_y < self.level.height and
                not self.level.is_wall(player_x, player_y) and
                not self.level.is_box(player_x, player_y)):

                # Check if the box can be pushed to the position behind it
                if (0 <= push_x < self.level.width and 
                    0 <= push_y < self.level.height and
                    not self.level.is_wall(push_x, push_y) and
                    not self.level.is_box(push_x, push_y)):

                    return True

        return False

    def _get_box_push_direction(self, box_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Determine the direction to push a box based on the target position.

        Args:
            box_pos (Tuple[int, int]): Position of the box
            target_pos (Tuple[int, int]): Target position (where the mouse is)

        Returns:
            Optional[Tuple[int, int]]: Direction vector (dx, dy) or None if no valid direction
        """
        # Calculate the direction from box to target
        dx = target_pos[0] - box_pos[0]
        dy = target_pos[1] - box_pos[1]

        # Normalize to a cardinal direction (up, down, left, right)
        if abs(dx) > abs(dy):
            # Horizontal movement dominates
            direction = (1 if dx > 0 else -1, 0)
        else:
            # Vertical movement dominates
            direction = (0, 1 if dy > 0 else -1)

        # Check if the box can be pushed in this direction
        push_x, push_y = box_pos[0] + direction[0], box_pos[1] + direction[1]
        player_x, player_y = box_pos[0] - direction[0], box_pos[1] - direction[1]

        # Check if the player can stand in front of the box
        if (0 <= player_x < self.level.width and 
            0 <= player_y < self.level.height and
            not self.level.is_wall(player_x, player_y) and
            not self.level.is_box(player_x, player_y)):

            # Check if the box can be pushed in this direction
            if (0 <= push_x < self.level.width and 
                0 <= push_y < self.level.height and
                not self.level.is_wall(push_x, push_y) and
                not self.level.is_box(push_x, push_y)):

                return direction

        # Try other cardinal directions if the primary direction doesn't work
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            if (dx, dy) != direction:
                push_x, push_y = box_pos[0] + dx, box_pos[1] + dy
                player_x, player_y = box_pos[0] - dx, box_pos[1] - dy

                # Check if the player can stand in front of the box
                if (0 <= player_x < self.level.width and 
                    0 <= player_y < self.level.height and
                    not self.level.is_wall(player_x, player_y) and
                    not self.level.is_box(player_x, player_y)):

                    # Check if the box can be pushed in this direction
                    if (0 <= push_x < self.level.width and 
                        0 <= push_y < self.level.height and
                        not self.level.is_wall(push_x, push_y) and
                        not self.level.is_box(push_x, push_y)):

                        return (dx, dy)

        return None

    def _calculate_box_path(self, box_pos: Tuple[int, int], direction: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Calculate the path a box can take when pushed in a specific direction.

        Args:
            box_pos (Tuple[int, int]): Starting position of the box
            direction (Tuple[int, int]): Direction vector (dx, dy)

        Returns:
            List[Tuple[int, int]]: Path the box can take, including the starting position
        """
        if not self.level or not direction:
            return [box_pos]

        path = [box_pos]
        current_pos = box_pos
        dx, dy = direction

        # Keep pushing the box until it hits an obstacle
        while True:
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)

            # Check if the next position is valid
            if (0 <= next_pos[0] < self.level.width and 
                0 <= next_pos[1] < self.level.height and
                not self.level.is_wall(next_pos[0], next_pos[1]) and
                not self.level.is_box(next_pos[0], next_pos[1])):

                path.append(next_pos)
                current_pos = next_pos
            else:
                break

        return path

    def _try_drag_box(self, direction: str) -> bool:
        """
        Try to drag box in specified direction.

        For the new box dragging behavior, we need to:
        1. Check if the box can be moved in the specified direction
        2. Swap the player and box positions
        3. Move the box one tile further in the drag direction
        """
        if not self.dragged_box_pos:
            return False

        direction_map = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }

        if direction not in direction_map:
            return False

        dx, dy = direction_map[direction]

        # Calculate positions
        box_x, box_y = self.dragged_box_pos
        new_box_x, new_box_y = box_x + dx, box_y + dy

        # Check if the box can be moved to the new position
        if not (0 <= new_box_x < self.level.width and 
                0 <= new_box_y < self.level.height and
                not self.level.is_wall(new_box_x, new_box_y) and
                not self.level.is_box(new_box_x, new_box_y)):
            return False

        # Save current state for undo
        self.level._save_state()

        # Find the box in the level's boxes list
        box_index = -1
        for i, (bx, by) in enumerate(self.level.boxes):
            if (bx, by) == (box_x, box_y):
                box_index = i
                break

        if box_index == -1:
            return False  # Box not found

        # Swap player and box positions
        old_player_pos = self.level.player_pos
        self.level.player_pos = (box_x, box_y)
        self.level.boxes[box_index] = (new_box_x, new_box_y)

        # Update our tracking variables
        self.player_position = self.level.player_pos
        self.dragged_box_pos = (new_box_x, new_box_y)

        # Update move and push counters
        self.level.moves += 1
        self.level.pushes += 1

        return True

    def _render_path_tiles(self, screen: pygame.Surface, map_area_x: int,
                          map_area_y: int, cell_size: int, scroll_x: int,
                          scroll_y: int):
        """Render highlighted tiles along the path."""
        if not self.current_path:
            return

        highlight_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        highlight_surface.fill(self.highlight_color)

        map_start_x = map_area_x + scroll_x
        map_start_y = map_area_y + scroll_y

        for x, y in self.current_path[1:]:  # Skip player position
            screen_x = map_start_x + x * cell_size
            screen_y = map_start_y + y * cell_size
            screen.blit(highlight_surface, (screen_x, screen_y))

    def _render_guideline(self, screen: pygame.Surface, map_area_x: int,
                         map_area_y: int, cell_size: int, scroll_x: int,
                         scroll_y: int):
        """Render the white guideline along the path."""
        if len(self.current_path) < 2:
            return

        map_start_x = map_area_x + scroll_x
        map_start_y = map_area_y + scroll_y

        # Convert path to screen coordinates
        screen_points = []
        for x, y in self.current_path:
            screen_x = map_start_x + x * cell_size + cell_size // 2
            screen_y = map_start_y + y * cell_size + cell_size // 2
            screen_points.append((screen_x, screen_y))

        # Draw the guideline directly on the screen
        if len(screen_points) >= 2:
            # Draw line segments directly
            for i in range(len(screen_points) - 1):
                start_pos = screen_points[i]
                end_pos = screen_points[i + 1]

                # Draw main line with anti-aliasing
                try:
                    pygame.draw.aaline(screen, self.guideline_color, start_pos, end_pos, self.guideline_width)
                except:
                    # Fallback to regular line if aaline fails
                    pygame.draw.line(screen, self.guideline_color, start_pos, end_pos, self.guideline_width)

                # Draw direction arrow at end of each segment
                if i == len(screen_points) - 2:  # Last segment
                    self._draw_arrow(screen, start_pos, end_pos)

    def _draw_arrow(self, surface: pygame.Surface, start: Tuple[int, int],
                   end: Tuple[int, int]):
        """Draw an arrow at the end of the guideline."""
        # Calculate arrow direction
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        if dx == 0 and dy == 0:
            return

        # Normalize direction
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return

        dx /= length
        dy /= length

        # Arrow parameters
        arrow_length = 8
        arrow_angle = math.pi / 4  # 45 degrees for better visibility

        # Calculate arrow points
        arrow_x1 = end[0] - arrow_length * (dx * math.cos(arrow_angle) - dy * math.sin(arrow_angle))
        arrow_y1 = end[1] - arrow_length * (dy * math.cos(arrow_angle) + dx * math.sin(arrow_angle))

        arrow_x2 = end[0] - arrow_length * (dx * math.cos(-arrow_angle) - dy * math.sin(-arrow_angle))
        arrow_y2 = end[1] - arrow_length * (dy * math.cos(-arrow_angle) + dx * math.sin(-arrow_angle))

        # Draw arrow with thicker lines for better visibility
        pygame.draw.line(surface, self.guideline_color, end, (int(arrow_x1), int(arrow_y1)), 3)
        pygame.draw.line(surface, self.guideline_color, end, (int(arrow_x2), int(arrow_y2)), 3)
