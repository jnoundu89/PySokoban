"""
Test script for the EnhancedSokolutionSolver.
Tests different algorithm/mode combinations via the unified solver.
"""

import time
from src.core.level import Level
from src.ai.enhanced_sokolution_solver import EnhancedSokolutionSolver, SearchMode
from src.ai.algorithm_selector import Algorithm

def test_sokolution_solver():
    """Test the EnhancedSokolutionSolver with different algorithms and modes."""
    # Create a solvable test level
    level_data = """########
#      #
# $$   #
# ..   #
#   @  #
#      #
########"""

    level = Level(level_data=level_data)

    print(f"Created level with {len(level.boxes)} boxes and {len(level.targets)} targets")

    # Test different algorithms and modes
    algorithms = [Algorithm.GREEDY, Algorithm.ASTAR]
    modes = [SearchMode.FORWARD, SearchMode.BIDIRECTIONAL]

    for algorithm in algorithms:
        for mode in modes:
            print(f"\nTesting EnhancedSokolutionSolver with {algorithm.value} algorithm in {mode.value} mode...")

            # Create solver
            solver = EnhancedSokolutionSolver(level, max_states=100000, time_limit=30.0)

            # Progress callback
            def progress_callback(message):
                print(f"Progress: {message}")

            # Solve level
            start_time = time.time()
            result = solver.solve(algorithm, mode, progress_callback)
            elapsed_time = time.time() - start_time

            # Print results
            if result:
                print(f"Solution found! {len(result.moves)} moves in {elapsed_time:.2f} seconds")
                print(f"States explored: {result.states_explored}")
                print(f"States generated: {result.states_generated}")
                print(f"Deadlocks pruned: {result.deadlocks_pruned}")
                print(f"First 10 moves: {result.moves[:10]}")
            else:
                print(f"No solution found after {elapsed_time:.2f} seconds")

def test_with_auto_solver():
    """Test the integration with AutoSolver."""
    from src.core.auto_solver import AutoSolver

    # Create a test level
    level_data = """########
#      #
# $$   #
# ..   #
#   @  #
#      #
########"""

    level = Level(level_data=level_data)

    print(f"\nTesting AutoSolver with a test level ({len(level.boxes)} boxes)")

    # Create auto solver
    auto_solver = AutoSolver(level)

    # Print complexity score and solver type
    print(f"Complexity score: {auto_solver.complexity_score:.1f}")
    print(f"Selected solver: {auto_solver.solver_type}")

    # Progress callback
    def progress_callback(message):
        print(f"Progress: {message}")

    # Solve level
    start_time = time.time()
    success = auto_solver.solve_level(progress_callback)
    elapsed_time = time.time() - start_time

    # Print results
    if success:
        solution_info = auto_solver.get_solution_info()
        print(f"Solution found! {solution_info['moves']} moves in {elapsed_time:.2f} seconds")
        print(f"Solver type: {solution_info['solver_type']}")
    else:
        print(f"No solution found after {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    test_sokolution_solver()
    test_with_auto_solver()
