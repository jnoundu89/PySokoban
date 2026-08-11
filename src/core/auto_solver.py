"""
Auto Solver for Sokoban levels.

This module provides functionality to automatically solve Sokoban levels
and animate the solution step by step.

Solveur préféré : **Festival** (FESS, Yaron Shoham, MIT), quand son binaire est
présent. Repli sur EnhancedSokolutionSolver sinon, pour que le jeu marche sans
dépendance externe.

L'écart entre les deux n'est pas une nuance. Mesuré le 2026-08-11, XSokoban,
60 s par niveau : EnhancedSokolutionSolver résout **1 niveau sur 10**, Festival
les **90 sur 90**. Voir src/ai/festival_solver.py pour le pourquoi et
l'installation du binaire.
"""

import time
import pygame
from src.ai.algorithm_selector import AlgorithmSelector, Algorithm
from src.ai.enhanced_sokolution_solver import EnhancedSokolutionSolver, SearchMode, SolutionData
from src.ai.festival_solver import FestivalSolver, SolutionRefusee, disponible as festival_disponible


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

# Budget accordé à Festival, en secondes. 600 s est la convention de la
# recherche Sokoban pour un niveau. En pratique la médiane des 90 XSokoban est
# à 1 s et le pire niveau à 101 s : le budget ne sert qu'aux cas pathologiques.
_FESTIVAL_BUDGET = 600.0


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

        # Festival d'abord s'il est installé. Le sélecteur d'algorithme reste
        # calculé : il sert au repli, et son score de complexité est affiché
        # ailleurs dans l'interface.
        self.use_festival = festival_disponible()
        self.solver_type = ("Festival 3.1 (FESS)" if self.use_festival
                            else _SOLVER_TYPE_NAMES.get(self.algorithm, self.algorithm.value))

        self.solution = None
        self._last_result = None  # SolutionData from last solve
        self.is_solving = False
        self.is_animating = False

        category = self.selector._get_complexity_category(self.complexity_score)
        max_states, time_limit = _SOLVER_LIMITS.get(self.algorithm, (1000000, 120.0))
        print(f"Level complexity: {category} (score: {self.complexity_score:.1f})")
        print(f"Using {self.solver_type} solver")
        if self.use_festival:
            print(f"Solver limits: {_FESTIVAL_BUDGET}s timeout, 1 core")
        else:
            print(f"Solver limits: {max_states} states, {time_limit}s timeout")
            print("Festival introuvable — repli sur le solveur interne, qui "
                  "résout 1 XSokoban sur 10. Voir src/ai/festival_solver.py.")

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

            if self.use_festival:
                return self._solve_with_festival(progress_callback)

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

    def _solve_with_festival(self, progress_callback=None):
        """Résoudre via Festival. Rend True si une solution VÉRIFIÉE existe.

        Une solution que Festival annonce mais que le moteur de ce dépôt refuse
        de rejouer n'est pas retournée : FestivalSolver lève SolutionRefusee, et
        on retombe sur le solveur interne. C'est le contrôle qui manquait à la
        tentative FESS précédente, où un benchmark de 90 échecs sur 90 a
        coexisté des mois avec une documentation annonçant la réussite.
        """
        try:
            result = FestivalSolver(self.level, time_limit=_FESTIVAL_BUDGET).solve(
                progress_callback)
        except SolutionRefusee as e:
            # Cas grave : le solveur marche, mais nos règles et les siennes ne
            # s'accordent pas. Le dire fort, et ne pas livrer la solution.
            print(f"[Festival] SOLUTION REFUSÉE — {e}")
            if progress_callback:
                progress_callback("Festival : solution incohérente, repli")
            self.use_festival = False
            self.is_solving = False
            return self.solve_level(progress_callback)
        except Exception as e:
            print(f"[Festival] indisponible ({e}) — repli sur le solveur interne")
            self.use_festival = False
            self.is_solving = False
            return self.solve_level(progress_callback)

        self.is_solving = False
        if result and result.moves:
            self.solution = result.moves
            self._last_result = result
            if progress_callback:
                progress_callback(f"Solution found! {len(self.solution)} moves")
            return True
        if progress_callback:
            progress_callback("No solution found")
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
