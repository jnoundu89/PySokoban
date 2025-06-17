"""
Deadlock detector module for the Sokoban game.

This module provides functionality to detect deadlocks in Sokoban levels.
A deadlock is a situation where the level becomes unsolvable.
"""

from typing import Set, Tuple, FrozenSet, List, Dict
from collections import defaultdict, deque


class DeadlockDetector:
    """
    Class for detecting deadlocks in Sokoban levels.

    This class implements various deadlock detection techniques to identify
    situations where a level becomes unsolvable:
    - Corner deadlocks: boxes stuck in corners without targets
    - Wall deadlocks: boxes against walls that can't reach targets
    - Frozen box deadlocks: boxes that can't move anymore
    - Line deadlocks: boxes in a line against a wall
    - Square deadlocks: 2x2 squares of boxes
    - Bipartite deadlocks: boxes that can't reach any target
    """

    def __init__(self, level):
        """
        Initialize the deadlock detector.

        Args:
            level: The level to check for deadlocks.
        """
        self.level = level
        self.targets = set(level.targets)
        self.corner_deadlocks = self._find_corner_deadlocks()
        self.wall_deadlocks = self._find_wall_deadlocks()

        # Cache for deadlock checks
        self.deadlock_cache = {}

    def _find_corner_deadlocks(self) -> Set[Tuple[int, int]]:
        """
        Find all corner deadlock positions.

        A corner deadlock is a position where a box would be stuck if pushed there,
        typically formed by two adjacent walls.

        Returns:
            Set of (x, y) coordinates representing corner deadlock positions.
        """
        corners = set()

        for x in range(self.level.width):
            for y in range(self.level.height):
                # Skip walls and targets
                if self.level.is_wall(x, y) or (x, y) in self.targets:
                    continue

                # Check if it's a corner (two adjacent walls)
                wall_count = 0
                adjacent_walls = []

                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nx, ny = x + dx, y + dy
                    if (nx < 0 or nx >= self.level.width or 
                        ny < 0 or ny >= self.level.height or 
                        self.level.is_wall(nx, ny)):
                        wall_count += 1
                        adjacent_walls.append((dx, dy))

                # If there are two adjacent walls, it's a corner deadlock
                if wall_count >= 2:
                    # Check if walls are adjacent (forming a corner)
                    for i in range(len(adjacent_walls)):
                        for j in range(i + 1, len(adjacent_walls)):
                            dx1, dy1 = adjacent_walls[i]
                            dx2, dy2 = adjacent_walls[j]
                            # Check if they form a 90-degree angle
                            if dx1 * dx2 + dy1 * dy2 == 0:
                                corners.add((x, y))
                                break

        return corners

    def _find_wall_deadlocks(self) -> Set[Tuple[int, int, int, int]]:
        """
        Find all wall deadlock positions.

        A wall deadlock is a position where a box is against a wall and can move
        along the wall but not away from it, making it impossible to reach a target.

        Returns:
            Set of (x, y, dx, dy) tuples representing wall deadlock positions and directions.
            (x, y) is the position, (dx, dy) is the direction along the wall.
        """
        wall_deadlocks = set()

        # Check each position in the level
        for x in range(self.level.width):
            for y in range(self.level.height):
                # Skip walls and targets
                if self.level.is_wall(x, y) or (x, y) in self.targets:
                    continue

                # Check if there's a wall in one of the four directions
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nx, ny = x + dx, y + dy

                    # If there's a wall in this direction
                    if (nx < 0 or nx >= self.level.width or 
                        ny < 0 or ny >= self.level.height or 
                        self.level.is_wall(nx, ny)):

                        # Check if the perpendicular directions are both blocked
                        # For a horizontal wall (dx=0), check left and right (dx=±1)
                        # For a vertical wall (dy=0), check up and down (dy=±1)
                        perp_dx, perp_dy = -dy, dx  # Perpendicular direction

                        # Check both perpendicular directions
                        blocked_count = 0
                        for mult in [-1, 1]:
                            check_x, check_y = x + mult * perp_dx, y + mult * perp_dy

                            # If this direction is blocked by a wall or edge
                            if (check_x < 0 or check_x >= self.level.width or 
                                check_y < 0 or check_y >= self.level.height or 
                                self.level.is_wall(check_x, check_y)):
                                blocked_count += 1

                        # If both perpendicular directions are blocked, it's a wall deadlock
                        if blocked_count == 2:
                            # Store the position and the direction along the wall
                            wall_deadlocks.add((x, y, perp_dx, perp_dy))

        return wall_deadlocks

    def _has_square_deadlock(self) -> bool:
        """
        Check if there's a 2x2 square of boxes in the level.

        A 2x2 square of boxes is a deadlock because none of the boxes can be moved.

        Returns:
            bool: True if a square deadlock is detected, False otherwise.
        """
        # Get all box positions
        boxes = set(self.level.boxes)

        # Check each box
        for box in boxes:
            x, y = box

            # Check if there's a 2x2 square of boxes
            # We only need to check the box to the right, below, and diagonally down-right
            # to avoid counting the same square multiple times
            if ((x+1, y) in boxes and 
                (x, y+1) in boxes and 
                (x+1, y+1) in boxes):

                # Check if any of the boxes in the square is on a target
                # If all boxes are on targets, it's not a deadlock
                if not all(pos in self.targets for pos in [(x, y), (x+1, y), (x, y+1), (x+1, y+1)]):
                    return True

        return False

    def _has_frozen_boxes(self) -> bool:
        """
        Check if there are any frozen boxes in the level.

        A frozen box is a box that can't move in any direction and is not on a target.

        Returns:
            bool: True if a frozen box is detected, False otherwise.
        """
        for box in self.level.boxes:
            if box not in self.targets:  # Skip boxes on targets
                if self._is_box_frozen(box):
                    return True

        return False

    def _is_box_frozen(self, box: Tuple[int, int]) -> bool:
        """
        Check if a box is frozen (can't move in any direction).

        Args:
            box: The position of the box to check.

        Returns:
            bool: True if the box is frozen, False otherwise.
        """
        x, y = box

        # Count blocked directions
        blocked_directions = 0

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy

            # Direction is blocked if there's a wall or another box
            if (self.level.is_wall(nx, ny) or (nx, ny) in self.level.boxes):
                blocked_directions += 1

        # Box is frozen if blocked in at least 3 directions
        return blocked_directions >= 3

    def _has_line_deadlock(self) -> bool:
        """
        Check if there are any line deadlocks in the level.

        A line deadlock is a line of boxes against a wall that can't be moved.

        Returns:
            bool: True if a line deadlock is detected, False otherwise.
        """
        # Check horizontal line deadlocks
        if self._check_horizontal_line_deadlocks():
            return True

        # Check vertical line deadlocks
        if self._check_vertical_line_deadlocks():
            return True

        return False

    def _check_horizontal_line_deadlocks(self) -> bool:
        """
        Check for horizontal line deadlocks.

        Returns:
            bool: True if a horizontal line deadlock is detected, False otherwise.
        """
        # Group boxes by row
        boxes_by_row = defaultdict(list)
        for x, y in self.level.boxes:
            boxes_by_row[y].append(x)

        for y, x_positions in boxes_by_row.items():
            if len(x_positions) >= 2:  # At least 2 boxes in the row
                x_positions.sort()

                # Check for adjacent boxes
                for i in range(len(x_positions) - 1):
                    if x_positions[i+1] - x_positions[i] == 1:  # Adjacent boxes
                        # Check if there's a wall above or below
                        wall_above = all(self.level.is_wall(x, y-1) for x in x_positions[i:i+2])
                        wall_below = all(self.level.is_wall(x, y+1) for x in x_positions[i:i+2])

                        if wall_above or wall_below:
                            # Check if there are no targets in this line
                            targets_in_line = any((x, y) in self.targets for x in x_positions[i:i+2])
                            if not targets_in_line:
                                return True

        return False

    def _check_vertical_line_deadlocks(self) -> bool:
        """
        Check for vertical line deadlocks.

        Returns:
            bool: True if a vertical line deadlock is detected, False otherwise.
        """
        # Group boxes by column
        boxes_by_col = defaultdict(list)
        for x, y in self.level.boxes:
            boxes_by_col[x].append(y)

        for x, y_positions in boxes_by_col.items():
            if len(y_positions) >= 2:  # At least 2 boxes in the column
                y_positions.sort()

                # Check for adjacent boxes
                for i in range(len(y_positions) - 1):
                    if y_positions[i+1] - y_positions[i] == 1:  # Adjacent boxes
                        # Check if there's a wall to the left or right
                        wall_left = all(self.level.is_wall(x-1, y) for y in y_positions[i:i+2])
                        wall_right = all(self.level.is_wall(x+1, y) for y in y_positions[i:i+2])

                        if wall_left or wall_right:
                            # Check if there are no targets in this line
                            targets_in_line = any((x, y) in self.targets for y in y_positions[i:i+2])
                            if not targets_in_line:
                                return True

        return False

    def _is_bipartite_impossible(self) -> bool:
        """
        Check if it's impossible to match boxes to targets.

        This is a simplified check that verifies if each box can reach at least one target.

        Returns:
            bool: True if it's impossible to match boxes to targets, False otherwise.
        """
        for box in self.level.boxes:
            if box not in self.targets:  # Skip boxes already on targets
                if not self._box_can_reach_any_target(box):
                    return True

        return False

    def _box_can_reach_any_target(self, box: Tuple[int, int]) -> bool:
        """
        Check if a box can reach any target.

        Args:
            box: The position of the box to check.

        Returns:
            bool: True if the box can reach at least one target, False otherwise.
        """
        # Simple BFS to check if the box can reach any target
        queue = deque([box])
        visited = {box}

        while queue:
            x, y = queue.popleft()

            # If we reached a target, return True
            if (x, y) in self.targets:
                return True

            # Check all four directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy

                # Skip if out of bounds, wall, or already visited
                if (nx < 0 or nx >= self.level.width or 
                    ny < 0 or ny >= self.level.height or 
                    self.level.is_wall(nx, ny) or 
                    (nx, ny) in visited):
                    continue

                # Skip if there's a box (we can't push through boxes)
                if (nx, ny) in self.level.boxes:
                    continue

                # Add to queue and mark as visited
                queue.append((nx, ny))
                visited.add((nx, ny))

        # If we've exhausted all reachable positions and haven't found a target,
        # the box can't reach any target
        return False

    def is_deadlock(self) -> bool:
        """
        Check if the current level state contains a deadlock.

        Returns:
            bool: True if a deadlock is detected, False otherwise.
        """
        # Use cache if available
        boxes_hash = hash(frozenset(self.level.boxes))
        if boxes_hash in self.deadlock_cache:
            return self.deadlock_cache[boxes_hash]

        # 1. Check corner deadlocks
        for box in self.level.boxes:
            if box in self.corner_deadlocks:
                self.deadlock_cache[boxes_hash] = True
                return True

        # 2. Check wall deadlocks
        for box in self.level.boxes:
            for x, y, dx, dy in self.wall_deadlocks:
                if (box[0], box[1]) == (x, y):
                    # Check if there's another box or wall in both directions along the wall
                    blocked_count = 0
                    for mult in [-1, 1]:
                        check_x, check_y = x + mult * dx, y + mult * dy

                        # If this direction is blocked by a wall, edge, or another box
                        if (check_x < 0 or check_x >= self.level.width or 
                            check_y < 0 or check_y >= self.level.height or 
                            self.level.is_wall(check_x, check_y) or
                            (check_x, check_y) in self.level.boxes):
                            blocked_count += 1

                    # If both directions along the wall are blocked, it's a deadlock
                    if blocked_count == 2:
                        self.deadlock_cache[boxes_hash] = True
                        return True

        # 3. Check for 2x2 square deadlocks
        if self._has_square_deadlock():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 4. Check for frozen boxes
        if self._has_frozen_boxes():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 5. Check for line deadlocks
        if self._has_line_deadlock():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 6. Check for bipartite matching impossibility
        if self._is_bipartite_impossible():
            self.deadlock_cache[boxes_hash] = True
            return True

        # No deadlock detected
        self.deadlock_cache[boxes_hash] = False
        return False
