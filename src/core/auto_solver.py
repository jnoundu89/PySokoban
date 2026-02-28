"""
Auto Solver for Sokoban levels.

This module provides functionality to automatically solve Sokoban levels
and animate the solution step by step, delegating to EnhancedSokolutionSolver.
"""

import time
import pygame
from src.ai.algorithm_selector import AlgorithmSelector, Algorithm
from src.ai.enhanced_sokolution_solver import EnhancedSokolutionSolver, SearchMode, SolutionData


# Map Algorithm enum to human-readable solver type strings
_SOLVER_TYPE_NAMES = {
    Algorithm.BFS: "Basic BFS",
    Algorithm.ASTAR: "Advanced A*",
    Algorithm.IDA_STAR: "Expert IDA*",
    Algorithm.GREEDY: "Greedy",
    Algorithm.BIDIRECTIONAL_GREEDY: "Sokolution Bidirectional Greedy",
}

# Solver limits per algorithm: (max_states, time_limit)
_SOLVER_LIMITS = {
    Algorithm.BFS: (75000, 10.0),
    Algorithm.ASTAR: (1000000, 120.0),
    Algorithm.IDA_STAR: (2000000, 300.0),
    Algorithm.GREEDY: (2000000, 600.0),
    Algorithm.BIDIRECTIONAL_GREEDY: (2000000, 600.0),
}


class AutoSolver:
    """
    Class for automatically solving Sokoban levels and animating the solution.
    Delegates to EnhancedSokolutionSolver with algorithm selection via AlgorithmSelector.
    """

    def __init__(self, level, renderer=None, skin_manager=None):
        self.level = level
        self.renderer = renderer
        self.skin_manager = skin_manager

        self.selector = AlgorithmSelector()
        self.complexity_score = self.selector.complexity_analyzer.calculate_complexity_score(level)
        self.algorithm = self.selector.select_optimal_algorithm(level)
        self.solver_type = _SOLVER_TYPE_NAMES.get(self.algorithm, self.algorithm.value)

        self.solution = None
        self._last_result = None  # SolutionData from last solve
        self.is_solving = False
        self.is_animating = False

        category = self.selector._get_complexity_category(self.complexity_score)
        max_states, time_limit = _SOLVER_LIMITS.get(self.algorithm, (1000000, 120.0))
        print(f"Level complexity: {category} (score: {self.complexity_score:.1f})")
        print(f"Using {self.solver_type} solver")
        print(f"Solver limits: {max_states} states, {time_limit}s timeout")

    def solve_level(self, progress_callback=None):
        """
        Solve the current level.

        Args:
            progress_callback (callable, optional): Function to call with progress updates.

        Returns:
            bool: True if the level was solved, False otherwise.
        """
        if self.is_solving:
            return False

        self.is_solving = True
        self.solution = None
        self._last_result = None

        try:
            if progress_callback:
                progress_callback("Analyzing level...")

            max_states, time_limit = _SOLVER_LIMITS.get(self.algorithm, (1000000, 120.0))
            solver = EnhancedSokolutionSolver(self.level, max_states, time_limit)

            mode = SearchMode.BIDIRECTIONAL if self.algorithm == Algorithm.BIDIRECTIONAL_GREEDY else SearchMode.FORWARD
            algorithm = Algorithm.GREEDY if self.algorithm == Algorithm.BIDIRECTIONAL_GREEDY else self.algorithm

            result = solver.solve(algorithm, mode, progress_callback)

            if result and result.moves:
                self.solution = result.moves
                self._last_result = result

                if progress_callback:
                    progress_callback(f"Solution found! {len(self.solution)} moves")

                self.is_solving = False
                return True
            else:
                if progress_callback:
                    progress_callback("No solution found")

                self.is_solving = False
                return False

        except Exception as e:
            if progress_callback:
                progress_callback(f"Error during solving: {e}")

            self.is_solving = False
            return False

    def get_solution_info(self):
        """
        Get information about the current solution.

        Returns:
            dict: Dictionary containing solution information.
        """
        if not self.solution:
            return None

        return {
            'moves': len(self.solution),
            'solution': self.solution.copy(),
            'complexity_score': self.complexity_score,
            'solver_type': self.solver_type
        }

    def execute_solution_live(self, move_delay=500, show_grid=False, zoom_level=1.0,
                            scroll_x=0, scroll_y=0, level_manager=None):
        """
        Execute the solution by taking control of the level and animating moves.

        Args:
            move_delay (int): Delay between moves in milliseconds.
            show_grid (bool): Whether to show grid.
            zoom_level (float): Zoom level for rendering.
            scroll_x (int): Horizontal scroll offset.
            scroll_y (int): Vertical scroll offset.
            level_manager: Level manager for rendering context.
        """
        if not self.solution or not self.renderer:
            return False

        self.is_animating = True

        try:
            print(f"AI executing solution: {len(self.solution)} moves")

            for i, move in enumerate(self.solution):
                # Check for quit events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.is_animating = False
                        return False

                # Convert move to direction
                direction_map = {
                    'UP': (0, -1),
                    'DOWN': (0, 1),
                    'LEFT': (-1, 0),
                    'RIGHT': (1, 0)
                }

                if move in direction_map:
                    dx, dy = direction_map[move]

                    # Execute the move
                    moved = self.level.move(dx, dy)

                    print(f"AI Move {i+1}/{len(self.solution)}: {move} -> {'OK' if moved else 'FAIL'}")

                    # Render the current state
                    if self.renderer and level_manager:
                        self.renderer.render_level(
                            self.level, level_manager, show_grid,
                            zoom_level, scroll_x, scroll_y, self.skin_manager,
                            show_completion_message=False
                        )
                        pygame.display.flip()

                    # Wait before next move
                    pygame.time.wait(move_delay)

                    # Check if level is completed
                    if self.level.is_completed():
                        print("Level solved by AI!")
                        pygame.time.wait(1000)
                        if hasattr(level_manager, '_show_level_completion_screen'):
                            level_manager._show_level_completion_screen()
                        self.is_animating = False
                        return True

        except Exception as e:
            print(f"Error during solution execution: {e}")
            return False
        finally:
            self.is_animating = False
            return True

    def stop_solving(self):
        """Stop the current solving process."""
        self.is_solving = False
        self.is_animating = False
