"""
Procedural Level Generator for Sokoban.

This module provides functionality to generate random Sokoban levels
that are guaranteed to be solvable.
"""

import random
import copy
import time
from collections import deque
from src.core.level import Level
from src.generation.level_solver import SokobanSolver
from src.generation.level_metrics import LevelMetrics
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET


class ProceduralGenerator:
    """
    Class for generating random Sokoban levels.

    This class provides methods to create random levels with various parameters
    and ensures that the generated levels are solvable.
    """

    def __init__(self, min_width=7, max_width=15, min_height=7, max_height=15,
                 min_boxes=1, max_boxes=5, wall_density=0.2, timeout=30):
        """
        Initialize the generator with parameters.

        Args:
            min_width (int, optional): Minimum level width. Defaults to 7.
            max_width (int, optional): Maximum level width. Defaults to 15.
            min_height (int, optional): Minimum level height. Defaults to 7.
            max_height (int, optional): Maximum level height. Defaults to 15.
            min_boxes (int, optional): Minimum number of boxes. Defaults to 1.
            max_boxes (int, optional): Maximum number of boxes. Defaults to 5.
            wall_density (float, optional): Density of internal walls (0-1). Defaults to 0.2.
            timeout (int, optional): Maximum time in seconds to spend generating. Defaults to 30.
        """
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height
        self.min_boxes = min_boxes
        self.max_boxes = max_boxes
        self.wall_density = wall_density
        self.timeout = timeout
        # Use optimized solver settings for faster generation
        self.solver = SokobanSolver(max_states=25000, max_time=3.0)
        self.metrics = LevelMetrics()

        # Statistics
        self.attempts = 0
        self.generation_time = 0
        self.level_metrics = None

    def generate_level(self, progress_callback=None):
        """
        Generate a random solvable level based on parameters.

        Args:
            progress_callback (callable, optional): A function to call with progress updates.
                The function should accept a dictionary with progress information.

        Returns:
            Level: A randomly generated solvable level.

        Raises:
            RuntimeError: If a solvable level could not be generated within the timeout.
        """
        start_time = time.time()
        self.attempts = 0
        self.level_metrics = None
        last_progress_time = start_time
        progress_interval = 0.1  # Update progress every 0.1 seconds

        while time.time() - start_time < self.timeout:
            self.attempts += 1

            # Create a random level
            level = self._create_random_level()

            # Report progress periodically
            current_time = time.time()
            elapsed_time = current_time - start_time
            if progress_callback and (current_time - last_progress_time >= progress_interval):
                last_progress_time = current_time
                progress_percent = min(100, (elapsed_time / self.timeout) * 100)

                # Create progress info dictionary
                progress_info = {
                    'attempts': self.attempts,
                    'elapsed_time': elapsed_time,
                    'timeout': self.timeout,
                    'percent': progress_percent,
                    'width': level.width,
                    'height': level.height,
                    'boxes': len(level.boxes),
                    'status': 'generating'
                }

                # Call the progress callback
                progress_callback(progress_info)

            # Validate the level
            if self._validate_level(level):
                # Check if the level is solvable
                solve_start = time.time()
                if self.solver.is_solvable(level):
                    solve_time = time.time() - solve_start
                    # print(f"DEBUG: Level {self.attempts} solved in {solve_time:.2f}s with {self.solver.states_explored} states")
                    self.generation_time = time.time() - start_time

                    # Calculate metrics for the level
                    solution = self.solver.get_solution()
                    self.level_metrics = self.metrics.calculate_metrics(level, solution)

                    # Report final progress
                    if progress_callback:
                        progress_callback({
                            'attempts': self.attempts,
                            'elapsed_time': self.generation_time,
                            'timeout': self.timeout,
                            'percent': 100,
                            'width': level.width,
                            'height': level.height,
                            'boxes': len(level.boxes),
                            'status': 'success',
                            'solution_length': len(solution)
                        })

                    return level
                else:
                    solve_time = time.time() - solve_start
                    # print(f"DEBUG: Level {self.attempts} not solvable (checked in {solve_time:.2f}s, {self.solver.states_explored} states)")
            else:
                pass
                # print(f"DEBUG: Level {self.attempts} failed validation")

        # If we get here, we couldn't generate a solvable level within the timeout
        if progress_callback:
            progress_callback({
                'attempts': self.attempts,
                'elapsed_time': time.time() - start_time,
                'timeout': self.timeout,
                'percent': 100,
                'status': 'timeout'
            })

        raise RuntimeError(f"Could not generate a solvable level within {self.timeout} seconds. "
                          f"Attempted {self.attempts} levels.")

    def _create_random_level(self):
        """
        Create a random level with walls, player, boxes and targets.

        Returns:
            Level: A randomly generated level (not necessarily solvable).
        """
        # Determine level dimensions
        width = random.randint(self.min_width, self.max_width)
        height = random.randint(self.min_height, self.max_height)

        # Create an empty grid with walls around the perimeter
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    row.append(WALL)
                else:
                    row.append(FLOOR)
            grid.append(row)

        # Add random internal walls
        self._add_random_walls(grid, width, height)

        # Ensure the level is connected
        if not self._ensure_connected(grid, width, height):
            # If we couldn't make the level connected, try again
            return self._create_random_level()

        # Determine number of boxes
        num_boxes = random.randint(self.min_boxes, self.max_boxes)

        # Place player, boxes, and targets
        level_string = self._place_elements(grid, width, height, num_boxes)

        # Create and return the level
        return Level(level_data=level_string)

    def _add_random_walls(self, grid, width, height):
        """
        Add random internal walls to the grid.

        Args:
            grid (list): The grid to add walls to.
            width (int): The width of the grid.
            height (int): The height of the grid.
        """
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if random.random() < self.wall_density:
                    grid[y][x] = WALL

    def _ensure_connected(self, grid, width, height):
        """
        Ensure all floor tiles in the grid are connected.

        Args:
            grid (list): The grid to check.
            width (int): The width of the grid.
            height (int): The height of the grid.

        Returns:
            bool: True if the grid is connected, False otherwise.
        """
        # Find a floor tile to start from
        start_x, start_y = None, None
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if grid[y][x] == FLOOR:
                    start_x, start_y = x, y
                    break
            if start_x is not None:
                break

        # If no floor tile was found, the grid is all walls
        if start_x is None:
            return False

        # Use BFS to find all connected floor tiles
        visited = set()
        queue = deque([(start_x, start_y)])
        visited.add((start_x, start_y))

        while queue:
            x, y = queue.popleft()

            # Check all four adjacent tiles
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy

                # Skip if out of bounds
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue

                # Skip if not a floor tile or already visited
                if grid[ny][nx] != FLOOR or (nx, ny) in visited:
                    continue

                # Add to queue and visited set
                queue.append((nx, ny))
                visited.add((nx, ny))

        # Count all floor tiles
        floor_count = sum(row.count(FLOOR) for row in grid)

        # If the number of visited floor tiles equals the total number of floor tiles,
        # then all floor tiles are connected
        return len(visited) == floor_count

    def _place_elements(self, grid, width, height, num_boxes):
        """
        Place player, boxes, and targets in the grid.

        Args:
            grid (list): The grid to place elements in.
            width (int): The width of the grid.
            height (int): The height of the grid.
            num_boxes (int): The number of boxes to place.

        Returns:
            str: A string representation of the level.
        """
        # Get all floor positions
        floor_positions = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if grid[y][x] == FLOOR:
                    floor_positions.append((x, y))

        # Shuffle the positions
        random.shuffle(floor_positions)

        # Make sure we have enough floor positions
        if len(floor_positions) < num_boxes * 2 + 1:
            # Not enough floor tiles for player, boxes, and targets
            # Add more floor tiles by removing some walls
            self._add_more_floor(grid, width, height, num_boxes * 2 + 1 - len(floor_positions))

            # Recalculate floor positions
            floor_positions = []
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    if grid[y][x] == FLOOR:
                        floor_positions.append((x, y))

            random.shuffle(floor_positions)

        # Place player
        player_x, player_y = floor_positions.pop()
        grid[player_y][player_x] = PLAYER

        # Place boxes and targets
        for _ in range(num_boxes):
            if not floor_positions:
                # This shouldn't happen, but just in case
                break

            # Place a box
            box_x, box_y = floor_positions.pop()
            grid[box_y][box_x] = BOX

            # Place a target
            if not floor_positions:
                # This shouldn't happen, but just in case
                break

            target_x, target_y = floor_positions.pop()
            grid[target_y][target_x] = TARGET

        # Convert grid to string
        level_string = '\n'.join(''.join(row) for row in grid)
        return level_string

    def _add_more_floor(self, grid, width, height, num_needed):
        """
        Add more floor tiles by removing walls.

        Args:
            grid (list): The grid to modify.
            width (int): The width of the grid.
            height (int): The height of the grid.
            num_needed (int): The number of additional floor tiles needed.
        """
        # Get all wall positions (excluding perimeter)
        wall_positions = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if grid[y][x] == WALL:
                    wall_positions.append((x, y))

        # Shuffle the positions
        random.shuffle(wall_positions)

        # Convert walls to floor
        for i in range(min(num_needed, len(wall_positions))):
            x, y = wall_positions[i]
            grid[y][x] = FLOOR

    def _validate_level(self, level):
        """
        Perform basic validation on the level.

        Args:
            level (Level): The level to validate.

        Returns:
            bool: True if the level is valid, False otherwise.
        """
        # Check if level has a player
        if level.player_pos == (0, 0):
            return False

        # Check if level has at least one box and target
        if not level.boxes or not level.targets:
            return False

        # Check if number of boxes matches number of targets
        if len(level.boxes) != len(level.targets):
            return False

        # Check if level is too small
        if level.width < self.min_width or level.height < self.min_height:
            return False

        # Check if level is too large
        if level.width > self.max_width or level.height > self.max_height:
            return False

        return True


def test_generator():
    """
    Test the generator by creating a random level.
    """
    # Create a generator
    generator = ProceduralGenerator(
        min_width=8,
        max_width=12,
        min_height=8,
        max_height=12,
        min_boxes=2,
        max_boxes=4,
        wall_density=0.2
    )

    # Generate a level
    try:
        level = generator.generate_level()

        # Print statistics
        print(f"Generated level in {generator.generation_time:.2f} seconds after {generator.attempts} attempts.")
        print(f"Level dimensions: {level.width}x{level.height}")
        print(f"Number of boxes: {len(level.boxes)}")
        print(f"Solution length: {len(generator.solver.get_solution())}")

        # Print metrics
        if generator.level_metrics:
            print("\nLevel Metrics:")
            print(f"Difficulty score: {generator.level_metrics['difficulty']['overall_score']:.1f}/100")
            print(f"Space efficiency: {generator.level_metrics['space_efficiency']:.2f}")
            print(f"Box density: {generator.level_metrics['box_density']:.2f}")
            print("Patterns:")
            print(f"  Corners: {generator.level_metrics['patterns']['corners']}")
            print(f"  Corridors: {generator.level_metrics['patterns']['corridors']}")
            print(f"  Rooms: {generator.level_metrics['patterns']['rooms']}")
            print(f"  Dead ends: {generator.level_metrics['patterns']['dead_ends']}")

        # Print the level
        print("\nGenerated Level:")
        print(level.get_state_string())

    except RuntimeError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_generator()
