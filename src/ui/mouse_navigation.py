"""
Mouse Navigation System for Sokoban Game.

YASC-style mouse controls:
- Click on empty cell: player pathfinds there (A* shortest path)
- Click on box: "lifts" it (selects it visually)
- Click on destination (while box lifted): plans and executes full push sequence
- Right-click / click same box: cancels lift
- White guideline overlay showing planned path
"""

import heapq
import pygame
import math
from enum import Enum, auto
from collections import deque
from typing import List, Tuple, Optional
from src.core.config_manager import get_config_manager


class MouseMode(Enum):
    """State machine for mouse interaction modes."""
    IDLE = auto()
    BOX_LIFTED = auto()
    PATH_EXECUTING = auto()


class BoxPushPathfinder:
    """
    BFS pathfinder that computes a sequence of pushes to move a box from
    position A to position B, including the player walks between pushes.

    State: (box_pos, player_pos)
    """

    MAX_PUSHES = 50  # Safety bound

    def __init__(self, level, player_path_func):
        """
        Args:
            level: The Level object.
            player_path_func: Callable(start, goal) -> list[(x,y)] or []
                              A* path for the player avoiding boxes.
        """
        self.level = level
        self._player_path = player_path_func

    def find_push_path(self, box_start, box_goal, player_pos):
        """
        Find a sequence of pushes to move a box from box_start to box_goal.

        Returns:
            list of (push_direction, player_walk_path) tuples, or
            [] if box is already at goal, or
            None if no path exists.
        """
        if box_start == box_goal:
            return []

        # The box at box_start is in self.level.boxes. During simulation it
        # moves, so we must exclude its *original* position from level.boxes
        # and track its *current* BFS position separately.
        self._original_box_pos = box_start

        # BFS on (box_pos, player_pos) states
        start_state = (box_start, player_pos)
        queue = deque([(start_state, [])])
        visited = {start_state}

        while queue:
            (box_pos, p_pos), pushes = queue.popleft()

            if len(pushes) >= self.MAX_PUSHES:
                continue

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_box = (box_pos[0] + dx, box_pos[1] + dy)
                push_origin = (box_pos[0] - dx, box_pos[1] - dy)

                # Validate positions
                if not self._is_free(new_box[0], new_box[1], box_pos):
                    continue
                if not self._is_free_for_player(push_origin[0], push_origin[1], box_pos):
                    continue

                # Can the player reach the push origin?
                walk_path = self._player_path_avoiding_box(
                    p_pos, push_origin, box_pos
                )
                if walk_path is None:
                    continue

                new_pushes = pushes + [((dx, dy), walk_path)]
                new_state = (new_box, box_pos)  # player ends at old box pos

                if new_box == box_goal:
                    return new_pushes

                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_state, new_pushes))

        return None

    def _is_free(self, x, y, current_box_pos):
        """Check if position is free for a box (not wall, not another box)."""
        if not (0 <= x < self.level.width and 0 <= y < self.level.height):
            return False
        if self.level.is_wall(x, y):
            return False
        # Check other boxes — skip the moved box's original position in
        # level.boxes (it's no longer there in the simulation)
        for bx, by in self.level.boxes:
            if (bx, by) == self._original_box_pos:
                continue
            if (bx, by) == (x, y):
                return False
        return True

    def _is_free_for_player(self, x, y, current_box_pos):
        """Check if position is free for player movement."""
        if not (0 <= x < self.level.width and 0 <= y < self.level.height):
            return False
        if self.level.is_wall(x, y):
            return False
        # Check other boxes — skip the moved box's original position
        for bx, by in self.level.boxes:
            if (bx, by) == self._original_box_pos:
                continue
            if (bx, by) == (x, y):
                return False
        # Player can't stand on the box's current simulated position
        if (x, y) == current_box_pos:
            return False
        return True

    def _player_path_avoiding_box(self, start, goal, current_box_pos):
        """BFS path for player, avoiding the box at its current simulated position."""
        if start == goal:
            return [start]

        queue = deque([start])
        visited = {start}
        parent = {start: None}

        while queue:
            current = queue.popleft()
            if current == goal:
                path = []
                c = current
                while c is not None:
                    path.append(c)
                    c = parent[c]
                return list(reversed(path))

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = current[0] + dx, current[1] + dy
                npos = (nx, ny)
                if npos in visited:
                    continue
                if not (0 <= nx < self.level.width and 0 <= ny < self.level.height):
                    continue
                if self.level.is_wall(nx, ny):
                    continue
                # Can't walk through the box's current position
                if npos == current_box_pos:
                    continue
                # Check other boxes — skip the moved box's original position
                is_other_box = False
                for bx, by in self.level.boxes:
                    if (bx, by) == self._original_box_pos:
                        continue
                    if (bx, by) == npos:
                        is_other_box = True
                        break
                if is_other_box:
                    continue
                visited.add(npos)
                parent[npos] = current
                queue.append(npos)

            if len(visited) > 500:
                break

        return None


class PathNode:
    """Node for A* pathfinding."""
    __slots__ = ('x', 'y', 'g_cost', 'h_cost', 'f_cost', 'parent')

    def __init__(self, x, y, g_cost, h_cost, parent=None):
        self.x = x
        self.y = y
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.f_cost = g_cost + h_cost
        self.parent = parent


class MouseNavigationSystem:
    """
    Mouse navigation system for Sokoban with pathfinding, click-to-move,
    and box push interaction.
    """

    def __init__(self):
        self.enabled = True
        self.current_path = []
        self.target_position = None
        self.player_position = None
        self.level = None

        # Pathfinding
        self.max_path_length = 100

        # Guideline rendering
        self.guideline_color = (255, 255, 255)
        self.guideline_width = 5

        # Movement queue
        self.is_moving = False
        self.movement_queue = []
        self.movement_speed = get_config_manager().get('game', 'mouse_movement_speed', 100)
        self.last_move_time = 0
        self.last_movement_direction = None

        # Lift-and-drop state machine (YASC-style)
        self.mouse_mode = MouseMode.IDLE
        self.lifted_box_pos = None
        self.lift_push_path = None
        self.lift_target_pos = None

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.clear_navigation()

    def set_level(self, level):
        self.level = level
        self.player_position = level.player_pos if level else None

    def update_movement_speed(self):
        self.movement_speed = get_config_manager().get('game', 'mouse_movement_speed', 100)

    def clear_navigation(self):
        """Clear all navigation state."""
        self.current_path = []
        self.target_position = None
        self.movement_queue = []
        self.is_moving = False
        self.mouse_mode = MouseMode.IDLE
        self.lifted_box_pos = None
        self.lift_push_path = None
        self.lift_target_pos = None

    # ------------------------------------------------------------------
    # Mouse position update (called every frame)
    # ------------------------------------------------------------------

    def update_mouse_position(self, mouse_pos: Tuple[int, int], map_area_x: int,
                              map_area_y: int, cell_size: int) -> Optional[Tuple[int, int]]:
        """
        Update navigation based on current mouse screen position.
        Recalculates the guideline path.

        Returns grid coordinates or None.
        """
        if not self.enabled or not self.level:
            return None

        grid_x = int((mouse_pos[0] - map_area_x) // cell_size)
        grid_y = int((mouse_pos[1] - map_area_y) // cell_size)

        if not (0 <= grid_x < self.level.width and 0 <= grid_y < self.level.height):
            self.target_position = None
            self.current_path = []
            return None

        grid_pos = (grid_x, grid_y)
        self.player_position = self.level.player_pos

        # --- BOX_LIFTED mode: show push-path preview ---
        if self.mouse_mode == MouseMode.BOX_LIFTED and self.lifted_box_pos:
            self.target_position = grid_pos
            self.lift_target_pos = grid_pos
            self._update_lift_preview(grid_pos)
            return grid_pos

        # Only recalculate if target changed and not currently moving
        if grid_pos != self.target_position and not self.is_moving:
            self.target_position = grid_pos
            # Path from player to cursor (A* avoids walls and boxes)
            self.current_path = self._calculate_path(
                self.player_position, grid_pos
            )

        return grid_pos

    # ------------------------------------------------------------------
    # Lift-and-drop preview
    # ------------------------------------------------------------------

    def _update_lift_preview(self, target_pos):
        """Update the push path preview for lift-and-drop mode."""
        if not self.lifted_box_pos or target_pos == self.lifted_box_pos:
            self.lift_push_path = None
            self.current_path = [self.lifted_box_pos] if self.lifted_box_pos else []
            return

        pathfinder = BoxPushPathfinder(self.level, self._calculate_path)
        push_path = pathfinder.find_push_path(
            self.lifted_box_pos, target_pos, self.level.player_pos
        )
        self.lift_push_path = push_path

        if push_path is not None and len(push_path) > 0:
            preview = [self.lifted_box_pos]
            current_box = self.lifted_box_pos
            for (dx, dy), _ in push_path:
                current_box = (current_box[0] + dx, current_box[1] + dy)
                preview.append(current_box)
            self.current_path = preview
        else:
            # No valid push path: show only the lifted box (no line through walls)
            self.current_path = [self.lifted_box_pos]

    # ------------------------------------------------------------------
    # Click handling
    # ------------------------------------------------------------------

    def handle_mouse_click(self, mouse_pos: Tuple[int, int], button: int,
                           map_area_x: int, map_area_y: int, cell_size: int) -> bool:
        """Handle mouse click. Returns True if handled."""
        if not self.enabled or not self.level:
            return False

        if button == 3:
            return self.handle_right_click()

        if button != 1:
            return False

        if self.is_moving and self.mouse_mode != MouseMode.BOX_LIFTED:
            return False

        grid_pos = self.update_mouse_position(
            mouse_pos, map_area_x, map_area_y, cell_size
        )
        if not grid_pos:
            return False

        return self._handle_left_click(grid_pos)

    def _handle_left_click(self, grid_pos: Tuple[int, int]) -> bool:
        """
        YASC-style left-click:
        - If in BOX_LIFTED mode: drop box at target (execute push path)
        - If clicking a movable box: lift it (enter BOX_LIFTED mode)
        - If clicking empty cell: walk there
        """
        if self.is_moving:
            return False

        # --- Lift-and-drop: drop the box ---
        if self.mouse_mode == MouseMode.BOX_LIFTED:
            return self._handle_lift_drop(grid_pos)

        # Clicking on self: no-op
        if grid_pos == self.player_position:
            return False

        # --- Click on a box: LIFT it (YASC-style) ---
        if self._is_box_at(grid_pos) and self._is_box_movable(grid_pos):
            self.mouse_mode = MouseMode.BOX_LIFTED
            self.lifted_box_pos = grid_pos
            self.lift_push_path = None
            self.lift_target_pos = None
            self.current_path = [grid_pos]  # Show highlight on box
            return True

        # --- Click on empty cell: walk there ---
        if not self.current_path or len(self.current_path) < 2:
            return False

        movements = self._path_to_movements(self.current_path)
        if movements:
            self.movement_queue = movements
            self.is_moving = True
            return True

        return False

    def handle_right_click(self) -> bool:
        """Right-click: cancel lift-and-drop if active."""
        if self.mouse_mode == MouseMode.BOX_LIFTED:
            self.mouse_mode = MouseMode.IDLE
            self.lifted_box_pos = None
            self.lift_push_path = None
            self.lift_target_pos = None
            return True
        return False

    def _handle_lift_drop(self, target_pos: Tuple[int, int]) -> bool:
        """Execute lift-and-drop: push box from lifted position to target."""
        if not self.lifted_box_pos or not self.level:
            self.mouse_mode = MouseMode.IDLE
            return False

        # Clicking same box cancels
        if target_pos == self.lifted_box_pos:
            self.mouse_mode = MouseMode.IDLE
            self.lifted_box_pos = None
            self.lift_push_path = None
            return True

        pathfinder = BoxPushPathfinder(self.level, self._calculate_path)
        push_path = pathfinder.find_push_path(
            self.lifted_box_pos, target_pos, self.level.player_pos
        )

        if push_path is None:
            return True  # Stay in lift mode (visual feedback: red)

        # Convert push path to movement queue
        movements = []
        for (dx, dy), walk_path in push_path:
            if walk_path and len(walk_path) >= 2:
                walk_moves = self._path_to_movements(walk_path)
                movements.extend(walk_moves)
            push_dir = self._dir_to_str(dx, dy)
            if push_dir:
                movements.append(push_dir)

        self.movement_queue = movements
        self.is_moving = True
        self.mouse_mode = MouseMode.PATH_EXECUTING
        self.lifted_box_pos = None
        self.lift_push_path = None
        self.lift_target_pos = None
        return True

    # ------------------------------------------------------------------
    # Movement execution
    # ------------------------------------------------------------------

    def update_movement(self, current_time: int) -> bool:
        """Execute next queued movement. Returns True if a move happened."""
        if not self.movement_queue or current_time - self.last_move_time < self.movement_speed:
            return False

        direction = self.movement_queue.pop(0)
        success = self._execute_movement(direction)

        if success:
            self.last_move_time = current_time
            self.player_position = self.level.player_pos

            if not self.movement_queue:
                self.is_moving = False
                if self.mouse_mode == MouseMode.PATH_EXECUTING:
                    self.mouse_mode = MouseMode.IDLE
                if self.target_position:
                    self.current_path = self._calculate_path(
                        self.player_position, self.target_position
                    )
        else:
            self.movement_queue = []
            self.is_moving = False

        return success

    def _execute_movement(self, direction: str) -> bool:
        """Execute a single movement."""
        direction_map = {
            'up': (0, -1), 'down': (0, 1),
            'left': (-1, 0), 'right': (1, 0)
        }
        if direction not in direction_map:
            return False

        dx, dy = direction_map[direction]
        self.last_movement_direction = direction
        return self.level.move(dx, dy)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_navigation(self, screen: pygame.Surface, map_area_x: int,
                          map_area_y: int, cell_size: int):
        """Render guideline and visual feedback."""
        if not self.enabled or not self.level:
            return

        # Lifted box highlight
        if self.mouse_mode == MouseMode.BOX_LIFTED and self.lifted_box_pos:
            self._render_lifted_box(screen, map_area_x, map_area_y, cell_size)

        # Guideline
        if self.current_path and len(self.current_path) > 1:
            if self.mouse_mode == MouseMode.BOX_LIFTED:
                color = (100, 200, 255) if self.lift_push_path is not None else (255, 80, 80)
                self._render_guideline(screen, map_area_x, map_area_y, cell_size, color)
            else:
                self._render_guideline(screen, map_area_x, map_area_y, cell_size,
                                       self.guideline_color)

    def _render_lifted_box(self, screen, map_area_x, map_area_y, cell_size):
        bx, by = self.lifted_box_pos
        sx = map_area_x + bx * cell_size
        sy = map_area_y + by * cell_size

        t = pygame.time.get_ticks() % 1000
        alpha = 120 + int(80 * math.sin(t / 1000 * 2 * math.pi))

        highlight = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        highlight.fill((100, 200, 255, min(alpha, 200)))
        screen.blit(highlight, (sx, sy))
        pygame.draw.rect(screen, (100, 200, 255), (sx, sy, cell_size, cell_size), 3)

    def _render_guideline(self, screen, map_area_x, map_area_y, cell_size, color):
        if len(self.current_path) < 2:
            return

        screen_points = []
        for x, y in self.current_path:
            sx = map_area_x + x * cell_size + cell_size // 2
            sy = map_area_y + y * cell_size + cell_size // 2
            screen_points.append((sx, sy))

        for i in range(len(screen_points) - 1):
            start_pos = screen_points[i]
            end_pos = screen_points[i + 1]
            try:
                pygame.draw.aaline(screen, color, start_pos, end_pos, self.guideline_width)
            except Exception:
                pygame.draw.line(screen, color, start_pos, end_pos, self.guideline_width)

            if i == len(screen_points) - 2:
                self._draw_arrow(screen, start_pos, end_pos, color)

    def _draw_arrow(self, surface, start, end, color):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return

        dx /= length
        dy /= length

        arrow_length = 8
        angle = math.pi / 4

        ax1 = end[0] - arrow_length * (dx * math.cos(angle) - dy * math.sin(angle))
        ay1 = end[1] - arrow_length * (dy * math.cos(angle) + dx * math.sin(angle))
        ax2 = end[0] - arrow_length * (dx * math.cos(-angle) - dy * math.sin(-angle))
        ay2 = end[1] - arrow_length * (dy * math.cos(-angle) + dx * math.sin(-angle))

        pygame.draw.line(surface, color, end, (int(ax1), int(ay1)), 3)
        pygame.draw.line(surface, color, end, (int(ax2), int(ay2)), 3)

    # ------------------------------------------------------------------
    # A* Pathfinding
    # ------------------------------------------------------------------

    def _calculate_path(self, start: Tuple[int, int],
                        goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """A* pathfinding from start to goal, avoiding walls and boxes."""
        if not start or not goal or start == goal:
            return []

        counter = 0
        open_set = []
        closed_set = set()

        start_node = PathNode(start[0], start[1], 0, self._heuristic(start, goal))
        heapq.heappush(open_set, (start_node.f_cost, counter, start_node))
        counter += 1
        nodes_dict = {start: start_node}

        while open_set:
            _, _, current = heapq.heappop(open_set)
            current_pos = (current.x, current.y)

            if current_pos in closed_set:
                continue
            closed_set.add(current_pos)

            if current_pos == goal:
                return self._reconstruct_path(current)

            if len(closed_set) > self.max_path_length:
                break

            for ddx, ddy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = current.x + ddx, current.y + ddy
                npos = (nx, ny)

                if npos in closed_set or not self._is_valid_position(nx, ny):
                    continue

                g_cost = current.g_cost + 1
                h_cost = self._heuristic(npos, goal)

                if npos in nodes_dict:
                    if g_cost < nodes_dict[npos].g_cost:
                        node = PathNode(nx, ny, g_cost, h_cost, current)
                        nodes_dict[npos] = node
                        heapq.heappush(open_set, (node.f_cost, counter, node))
                        counter += 1
                else:
                    node = PathNode(nx, ny, g_cost, h_cost, current)
                    nodes_dict[npos] = node
                    heapq.heappush(open_set, (node.f_cost, counter, node))
                    counter += 1

        return self._find_closest_reachable_path(start, goal)

    def _find_closest_reachable_path(self, start, goal):
        """BFS fallback: find path to closest reachable position to goal."""
        queue = deque([start])
        visited = {start}
        parent_map = {start: None}
        closest_pos = start
        closest_dist = self._heuristic(start, goal)

        while queue:
            current = queue.popleft()
            dist = self._heuristic(current, goal)
            if dist < closest_dist:
                closest_dist = dist
                closest_pos = current

            for ddx, ddy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = current[0] + ddx, current[1] + ddy
                npos = (nx, ny)
                if npos not in visited and self._is_valid_position(nx, ny):
                    visited.add(npos)
                    parent_map[npos] = current
                    queue.append(npos)
                    if len(visited) > self.max_path_length:
                        break

        if closest_pos == start:
            return []

        path = []
        c = closest_pos
        while c is not None:
            path.append(c)
            c = parent_map[c]
        return list(reversed(path))

    def _is_valid_position(self, x, y):
        """Position is in bounds, not wall, not box."""
        if not (0 <= x < self.level.width and 0 <= y < self.level.height):
            return False
        return not self.level.is_wall(x, y) and not self.level.is_box(x, y)

    @staticmethod
    def _heuristic(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _reconstruct_path(self, node):
        path = []
        while node:
            path.append((node.x, node.y))
            node = node.parent
        return list(reversed(path))

    def _path_to_movements(self, path: List[Tuple[int, int]]) -> List[str]:
        """Convert path coordinates to direction strings."""
        if len(path) < 2:
            return []
        movements = []
        for i in range(1, len(path)):
            dx = path[i][0] - path[i - 1][0]
            dy = path[i][1] - path[i - 1][1]
            d = self._dir_to_str(dx, dy)
            if d:
                movements.append(d)
        return movements

    @staticmethod
    def _dir_to_str(dx: int, dy: int) -> Optional[str]:
        return {(0, -1): 'up', (0, 1): 'down', (-1, 0): 'left', (1, 0): 'right'}.get((dx, dy))

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _is_box_at(self, pos):
        return self.level.is_box(pos[0], pos[1])

    def _is_box_movable(self, pos):
        """A box is movable if it can be pushed in at least one direction."""
        if not self.level or not self._is_box_at(pos):
            return False
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            push_x, push_y = pos[0] + dx, pos[1] + dy
            player_x, player_y = pos[0] - dx, pos[1] - dy
            if (self._is_valid_position(player_x, player_y) and
                    self._is_valid_position(push_x, push_y)):
                return True
        return False
