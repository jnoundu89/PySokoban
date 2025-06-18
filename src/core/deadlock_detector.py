"""
Deadlock detector module for the Sokoban game.

This module provides functionality to detect deadlocks in Sokoban levels.
A deadlock is a situation where the level becomes unsolvable.

Types of deadlocks detected:
1. Dead square deadlocks (simple deadlocks): Squares where a box can never be pushed to a goal
2. Freeze deadlocks: Boxes that become immovable and are not on targets
3. Corral deadlocks: Areas the player can't reach with boxes that can't be solved
4. Closed diagonal deadlocks: Boxes forming a diagonal pattern that can't be solved
5. Bipartite deadlocks: Not every box can reach every goal
6. Square deadlocks: 2x2 squares of boxes that can't be moved
"""

from typing import Set, Tuple, FrozenSet, List, Dict, Optional
from collections import defaultdict, deque


class DeadlockDetector:
    """
    Class for detecting deadlocks in Sokoban levels.

    This class implements various deadlock detection techniques to identify
    situations where a level becomes unsolvable:
    - Simple deadlocks (Dead square deadlocks): Squares where a box can never be pushed to a goal
    - Freeze deadlocks: Boxes that become immovable and are not on targets
    - Corral deadlocks: Areas the player can't reach with boxes that can't be solved
    - Square deadlocks: 2x2 squares of boxes that can't be moved
    - Line deadlocks: Boxes in a line against a wall
    - Bipartite deadlocks: Not every box can reach every goal
    """

    def __init__(self, level):
        """
        Initialize the deadlock detector.

        Args:
            level: The level to check for deadlocks.
        """
        self.level = level
        self.targets = set(level.targets)

        # Precomputed deadlock positions
        self.simple_deadlocks = self._find_simple_deadlocks()
        self.corner_deadlocks = self._find_corner_deadlocks()
        self.wall_deadlocks = self._find_wall_deadlocks()

        # Cache for deadlock checks
        self.deadlock_cache = {}

    def _find_simple_deadlocks(self) -> Set[Tuple[int, int]]:
        """
        Find all simple deadlock positions (dead squares).

        A simple deadlock is a position from which a box can never be pushed to a goal.
        The algorithm works by:
        1. For each goal, place a box on it
        2. Pull the box from the goal to every possible square and mark all reached squares as visited
        3. After doing this for all goals, any square not marked as visited is a simple deadlock square

        Returns:
            Set of (x, y) coordinates representing simple deadlock positions.
        """
        # Initialize all non-wall squares as potential deadlocks
        potential_deadlocks = set()
        for x in range(self.level.width):
            for y in range(self.level.height):
                if not self.level.is_wall(x, y):
                    potential_deadlocks.add((x, y))

        # For each goal, find all squares from which a box can be pushed to that goal
        reachable_squares = set()
        for target in self.targets:
            # Start with a box at the target
            visited = set()
            queue = deque([target])
            visited.add(target)

            while queue:
                x, y = queue.popleft()

                # Try to pull the box in all four directions
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    # Position of the player to pull the box
                    player_x, player_y = x + dx, y + dy

                    # Position the box would be pulled to
                    new_x, new_y = x - dx, y - dy

                    # Check if the pull is valid:
                    # 1. Player position must be within bounds and not a wall
                    # 2. New box position must be within bounds and not a wall
                    if (0 <= player_x < self.level.width and 
                        0 <= player_y < self.level.height and 
                        not self.level.is_wall(player_x, player_y) and
                        0 <= new_x < self.level.width and 
                        0 <= new_y < self.level.height and 
                        not self.level.is_wall(new_x, new_y) and
                        (new_x, new_y) not in visited):

                        # Mark the new position as visited
                        visited.add((new_x, new_y))
                        queue.append((new_x, new_y))

            # Add all visited squares to the reachable squares
            reachable_squares.update(visited)

        # Simple deadlocks are squares that are not reachable from any goal
        simple_deadlocks = potential_deadlocks - reachable_squares

        # Remove targets from simple deadlocks (targets can't be deadlocks)
        simple_deadlocks -= self.targets

        return simple_deadlocks

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

    def _is_box_frozen(self, box: Tuple[int, int], checked_boxes: Optional[Set[Tuple[int, int]]] = None) -> bool:
        """
        Check if a box is frozen (can't move in any direction).

        A box is frozen if it's blocked along both axes (horizontal and vertical).
        A box is blocked along an axis if:
        1. There's a wall on one side of the box
        2. There's a simple deadlock square on both sides of the box
        3. There's a box on one side that is itself blocked

        Args:
            box: The position of the box to check.
            checked_boxes: Set of boxes already checked to avoid circular checks.

        Returns:
            bool: True if the box is frozen, False otherwise.
        """
        if checked_boxes is None:
            checked_boxes = set()

        # If we've already checked this box, treat it as a wall to avoid circular checks
        if box in checked_boxes:
            return True

        checked_boxes.add(box)
        x, y = box

        # Check if the box is blocked horizontally
        blocked_horizontally = self._is_box_blocked_along_axis(box, True, checked_boxes)

        # Check if the box is blocked vertically
        blocked_vertically = self._is_box_blocked_along_axis(box, False, checked_boxes)

        # Box is frozen if blocked along both axes
        return blocked_horizontally and blocked_vertically

    def _is_box_blocked_along_axis(self, box: Tuple[int, int], is_horizontal: bool, 
                                  checked_boxes: Set[Tuple[int, int]]) -> bool:
        """
        Check if a box is blocked along a specific axis.

        A box is blocked along an axis if:
        1. There's a wall on one side of the box
        2. There's a simple deadlock square on both sides of the box
        3. There's a box on one side that is itself blocked along the perpendicular axis

        Args:
            box: The position of the box to check.
            is_horizontal: True to check horizontal axis, False for vertical.
            checked_boxes: Set of boxes already checked to avoid circular checks.

        Returns:
            bool: True if the box is blocked along the specified axis, False otherwise.
        """
        x, y = box

        # Define the directions to check based on the axis
        if is_horizontal:
            directions = [(-1, 0), (1, 0)]  # Left and right
        else:
            directions = [(0, -1), (0, 1)]  # Up and down

        # Check if there's a wall on either side
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx < 0 or nx >= self.level.width or 
                ny < 0 or ny >= self.level.height or 
                self.level.is_wall(nx, ny)):
                return True  # Blocked by a wall

        # Check if there are simple deadlock squares on both sides
        if all((x + dx, y + dy) in self.simple_deadlocks for dx, dy in directions):
            return True  # Blocked by simple deadlocks on both sides

        # Check if there's a box on either side that is blocked along the perpendicular axis
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx, ny) in self.level.boxes:
                # Check if this box is blocked along the perpendicular axis
                # We need to create a new set to avoid modifying the original
                new_checked_boxes = checked_boxes.copy()
                if self._is_box_blocked_along_axis((nx, ny), not is_horizontal, new_checked_boxes):
                    return True  # Blocked by another box that is itself blocked

        return False  # Not blocked along this axis

    def _has_closed_diagonal_deadlock(self) -> bool:
        """
        Check if there's a closed diagonal deadlock in the level.

        A closed diagonal deadlock occurs when boxes form a diagonal pattern that can't be solved.
        This can happen in "checkerboard" levels or when boxes form a diagonal with walls.

        Returns:
            bool: True if a closed diagonal deadlock is detected, False otherwise.
        """
        # Get all box positions
        boxes = set(self.level.boxes)

        # Check each box
        for box in boxes:
            x, y = box

            # Skip boxes on targets
            if box in self.targets:
                continue

            # Check for diagonal patterns in all four directions
            for dx1, dy1, dx2, dy2 in [
                (1, 1, -1, 1),    # Top-right and top-left
                (1, 1, 1, -1),    # Top-right and bottom-right
                (-1, -1, 1, -1),  # Bottom-left and bottom-right
                (-1, -1, -1, 1)   # Bottom-left and top-left
            ]:
                # Check if there are boxes or walls in the diagonal pattern
                pos1 = (x + dx1, y + dy1)
                pos2 = (x + dx2, y + dy2)

                # Check if the diagonal positions are boxes or walls
                is_pos1_blocked = (pos1 in boxes or 
                                  pos1[0] < 0 or pos1[0] >= self.level.width or 
                                  pos1[1] < 0 or pos1[1] >= self.level.height or 
                                  self.level.is_wall(pos1[0], pos1[1]))

                is_pos2_blocked = (pos2 in boxes or 
                                  pos2[0] < 0 or pos2[0] >= self.level.width or 
                                  pos2[1] < 0 or pos2[1] >= self.level.height or 
                                  self.level.is_wall(pos2[0], pos2[1]))

                # If both diagonal positions are blocked, check if the corner position is also blocked
                if is_pos1_blocked and is_pos2_blocked:
                    corner_pos = (x + dx1 + dx2, y + dy1 + dy2)

                    # Check if the corner position is a box or wall
                    is_corner_blocked = (corner_pos in boxes or 
                                        corner_pos[0] < 0 or corner_pos[0] >= self.level.width or 
                                        corner_pos[1] < 0 or corner_pos[1] >= self.level.height or 
                                        self.level.is_wall(corner_pos[0], corner_pos[1]))

                    # If the corner is also blocked, we have a closed diagonal deadlock
                    if is_corner_blocked:
                        # Check if any of the boxes in the pattern are on targets
                        # If all boxes are on targets, it's not a deadlock
                        pattern_boxes = [box, pos1, pos2, corner_pos]
                        pattern_boxes = [b for b in pattern_boxes if b in boxes]

                        if not all(b in self.targets for b in pattern_boxes):
                            return True

        return False

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

    def _has_corral_deadlock(self, max_search_time: float = 0.1) -> bool:
        """
        Check if there's a corral deadlock in the level.

        A corral is an area the player can't reach. This function checks if the boxes
        in the corral can be solved (pushed to goals or out of the corral).

        Args:
            max_search_time: Maximum time in seconds to spend searching for a solution.

        Returns:
            bool: True if a corral deadlock is detected, False otherwise.
        """
        import time
        start_time = time.time()

        # 1. Calculate the reachable player squares
        reachable = self._get_reachable_squares()

        # If all squares are reachable, there's no corral
        if len(reachable) == self.level.width * self.level.height - sum(1 for x in range(self.level.width) 
                                                                       for y in range(self.level.height) 
                                                                       if self.level.is_wall(x, y)):
            return False

        # 2. Identify boxes in the corral (boxes in unreachable squares)
        corral_boxes = [box for box in self.level.boxes if box not in reachable]

        # If there are no boxes in the corral, there's no corral deadlock
        if not corral_boxes:
            return False

        # 3. Identify boxes that can't be pushed without pushing a corral box first
        unpushable_boxes = set()
        for box in self.level.boxes:
            if box not in corral_boxes:  # Only consider boxes outside the corral
                can_push = False
                x, y = box

                # Check if the box can be pushed in any direction
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    # Position of the player to push the box
                    player_x, player_y = x - dx, y - dy

                    # Position the box would be pushed to
                    new_x, new_y = x + dx, y + dy

                    # Check if the push is valid and doesn't involve a corral box
                    if (0 <= player_x < self.level.width and 
                        0 <= player_y < self.level.height and 
                        not self.level.is_wall(player_x, player_y) and
                        (player_x, player_y) in reachable and
                        0 <= new_x < self.level.width and 
                        0 <= new_y < self.level.height and 
                        not self.level.is_wall(new_x, new_y) and
                        (new_x, new_y) not in self.level.boxes):

                        can_push = True
                        break

                if not can_push:
                    unpushable_boxes.add(box)

        # 4. Create a simplified level with only corral boxes and unpushable boxes
        from copy import deepcopy
        simplified_level = deepcopy(self.level)
        simplified_level.boxes = [box for box in self.level.boxes if box in corral_boxes or box in unpushable_boxes]

        # 5. Check if all boxes in the corral can be pushed to goals or out of the corral
        # This is a simplified search that doesn't consider all possible moves
        visited_states = set()
        queue = deque([(tuple(sorted(simplified_level.boxes)), simplified_level.player_pos)])

        while queue and time.time() - start_time < max_search_time:
            boxes_tuple, player_pos = queue.popleft()
            boxes = list(boxes_tuple)

            # Check if all corral boxes are on goals
            if all(box in self.targets for box in boxes if box in corral_boxes):
                return False  # Not a deadlock, all corral boxes can be pushed to goals

            # Try all possible moves
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                new_player_x, new_player_y = player_pos[0] + dx, player_pos[1] + dy

                # Check if the move is valid
                if (0 <= new_player_x < self.level.width and 
                    0 <= new_player_y < self.level.height and 
                    not self.level.is_wall(new_player_x, new_player_y)):

                    # Check if there's a box at the new position
                    box_idx = None
                    for i, box in enumerate(boxes):
                        if box == (new_player_x, new_player_y):
                            box_idx = i
                            break

                    if box_idx is not None:
                        # Try to push the box
                        new_box_x, new_box_y = new_player_x + dx, new_player_y + dy

                        # Check if the push is valid
                        if (0 <= new_box_x < self.level.width and 
                            0 <= new_box_y < self.level.height and 
                            not self.level.is_wall(new_box_x, new_box_y) and
                            (new_box_x, new_box_y) not in boxes):

                            # Check if the box is being pushed out of the corral
                            if (new_box_x, new_box_y) in reachable and (new_player_x, new_player_y) in corral_boxes:
                                return False  # Not a deadlock, a box can be pushed out of the corral

                            # Update the box position
                            new_boxes = boxes.copy()
                            new_boxes[box_idx] = (new_box_x, new_box_y)
                            new_boxes_tuple = tuple(sorted(new_boxes))

                            # Check if we've seen this state before
                            new_state = (new_boxes_tuple, (new_player_x, new_player_y))
                            if new_state not in visited_states:
                                visited_states.add(new_state)
                                queue.append(new_state)
                    else:
                        # Move the player without pushing a box
                        new_state = (boxes_tuple, (new_player_x, new_player_y))
                        if new_state not in visited_states:
                            visited_states.add(new_state)
                            queue.append(new_state)

        # If we've exhausted all possible moves or run out of time, and haven't found a solution,
        # then the corral is a deadlock
        return len(queue) == 0

    def _get_reachable_squares(self) -> Set[Tuple[int, int]]:
        """
        Calculate the squares reachable by the player.

        Returns:
            Set of (x, y) coordinates representing reachable squares.
        """
        reachable = set()
        queue = deque([self.level.player_pos])
        reachable.add(self.level.player_pos)

        while queue:
            x, y = queue.popleft()

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy

                # Check if the new position is valid and not already visited
                if (0 <= nx < self.level.width and 
                    0 <= ny < self.level.height and 
                    not self.level.is_wall(nx, ny) and 
                    (nx, ny) not in self.level.boxes and
                    (nx, ny) not in reachable):

                    reachable.add((nx, ny))
                    queue.append((nx, ny))

        return reachable

    def is_deadlock(self) -> bool:
        """
        Check if the current level state contains a deadlock.

        This method checks for various types of deadlocks in order of increasing computational complexity:
        1. Simple deadlocks (dead squares): Squares where a box can never be pushed to a goal
        2. Corner deadlocks: Boxes stuck in corners without targets
        3. Wall deadlocks: Boxes against walls that can't reach targets
        4. Square deadlocks: 2x2 squares of boxes that can't be moved
        5. Frozen box deadlocks: Boxes that become immovable and are not on targets
        6. Line deadlocks: Boxes in a line against a wall
        7. Closed diagonal deadlocks: Boxes forming a diagonal pattern that can't be solved
        8. Bipartite deadlocks: Not every box can reach every goal
        9. Corral deadlocks: Areas the player can't reach with boxes that can't be solved

        Returns:
            bool: True if a deadlock is detected, False otherwise.
        """
        # Use cache if available
        boxes_hash = hash(frozenset(self.level.boxes))
        if boxes_hash in self.deadlock_cache:
            return self.deadlock_cache[boxes_hash]

        # 1. Check simple deadlocks (dead squares)
        for box in self.level.boxes:
            if box in self.simple_deadlocks:
                self.deadlock_cache[boxes_hash] = True
                return True

        # 2. Check corner deadlocks
        for box in self.level.boxes:
            if box in self.corner_deadlocks:
                self.deadlock_cache[boxes_hash] = True
                return True

        # 3. Check wall deadlocks
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

        # 4. Check for 2x2 square deadlocks
        if self._has_square_deadlock():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 5. Check for frozen boxes
        if self._has_frozen_boxes():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 6. Check for line deadlocks
        if self._has_line_deadlock():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 7. Check for closed diagonal deadlocks
        if self._has_closed_diagonal_deadlock():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 8. Check for bipartite matching impossibility
        if self._is_bipartite_impossible():
            self.deadlock_cache[boxes_hash] = True
            return True

        # 9. Check for corral deadlocks (this is the most expensive check, so do it last)
        if self._has_corral_deadlock():
            self.deadlock_cache[boxes_hash] = True
            return True

        # No deadlock detected
        self.deadlock_cache[boxes_hash] = False
        return False
