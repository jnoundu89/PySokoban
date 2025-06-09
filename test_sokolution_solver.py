"""
Test script for the Sokolution solver.
This script loads a complex level and uses the Sokolution solver to solve it.
"""

import time
import pygame
from src.core.level import Level
from src.generation.sokolution_solver import SokolutionSolver, ALGORITHM_GREEDY, ALGORITHM_ASTAR, MODE_FORWARD, MODE_BIDIRECTIONAL

def test_sokolution_solver():
    """Test the Sokolution solver on a complex level."""
    # Create a complex level
    level_string = """
    #################
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    #################
    """
    
    # Add boxes and targets
    level_with_boxes = level_string.replace("               ", "  $ $ $ $ $ $  ")
    level_with_boxes_and_targets = level_with_boxes.replace("# # # # # # # #", "# . . . . . . #")
    
    # Add player
    level_data = level_with_boxes_and_targets.replace("#               #\n    #####", "#       @       #\n    #####")
    
    # Create level
    level = Level(level_data=level_data)
    
    print(f"Created level with {len(level.boxes)} boxes and {len(level.targets)} targets")
    
    # Initialize pygame (needed for time.Clock)
    pygame.init()
    
    # Test different algorithms and modes
    algorithms = [ALGORITHM_GREEDY, ALGORITHM_ASTAR]
    modes = [MODE_FORWARD, MODE_BIDIRECTIONAL]
    
    for algorithm in algorithms:
        for mode in modes:
            print(f"\nTesting Sokolution solver with {algorithm} algorithm in {mode} mode...")
            
            # Create solver
            solver = SokolutionSolver(level, algorithm=algorithm, mode=mode, max_states=100000, time_limit=30.0)
            
            # Progress callback
            def progress_callback(message):
                print(f"Progress: {message}")
            
            # Solve level
            start_time = time.time()
            solution = solver.solve(progress_callback)
            elapsed_time = time.time() - start_time
            
            # Print results
            if solution:
                print(f"Solution found! {len(solution)} moves in {elapsed_time:.2f} seconds")
                print(f"States explored: {solver.states_explored}")
                print(f"States generated: {solver.states_generated}")
                print(f"Deadlocks pruned: {solver.deadlocks_pruned}")
                print(f"First 10 moves: {solution[:10]}")
            else:
                print(f"No solution found after {elapsed_time:.2f} seconds")
                print(f"States explored: {solver.states_explored}")
    
    pygame.quit()

def test_with_auto_solver():
    """Test the integration with AutoSolver."""
    from src.core.auto_solver import AutoSolver
    
    # Create a complex level
    level_string = """
    #################
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #               #
    # # # # # # # # #
    #       @       #
    #################
    """
    
    # Add boxes and targets to make it very complex
    level_with_boxes = level_string.replace("               ", "  $ $ $ $ $ $  ")
    level_with_boxes_and_targets = level_with_boxes.replace("# # # # # # # #", "# . . . . . . #")
    
    # Create level
    level = Level(level_data=level_with_boxes_and_targets)
    
    print(f"\nTesting AutoSolver with a complex level ({len(level.boxes)} boxes)")
    
    # Create auto solver
    auto_solver = AutoSolver(level)
    
    # Print complexity score and solver type
    print(f"Complexity score: {auto_solver.complexity_score:.1f}")
    print(f"Selected solver: {type(auto_solver.solver).__name__}")
    
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