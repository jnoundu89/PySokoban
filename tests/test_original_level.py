#!/usr/bin/env python3
"""
Test script for the original Sokoban level that fails to solve.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.level import Level
from src.core.auto_solver import AutoSolver

def test_original_level():
    """Test the first level from Original.txt that fails to solve."""
    print("Testing Original Level 1...")
    print("=" * 50)

    # The problematic level from Original.txt
    level_string = """    #####
    #   #
    #$  #
  ###  $##
  #  $ $ #
### # ## #   ######
#   # ## #####  ..#
# $  $          ..#
##### ### #@##  ..#
    #     #########
    #######"""

    print("Level:")
    print(level_string)

    # Create level
    level = Level(level_data=level_string)

    print(f"\nLevel info:")
    print(f"Size: {level.width}x{level.height}")
    print(f"Player: {level.player_pos}")
    print(f"Boxes: {len(level.boxes)} - {level.boxes}")
    print(f"Targets: {len(level.targets)} - {level.targets}")

    # Test with AutoSolver (will select appropriate algorithm based on complexity)
    print(f"\n--- Testing with AutoSolver ---")

    auto_solver = AutoSolver(level, renderer=None)
    print(f"Solver type: {auto_solver.solver_type}")
    print(f"Complexity score: {auto_solver.complexity_score:.1f}")

    def progress_callback(message):
        print(f"  {message}")

    try:
        success = auto_solver.solve_level(progress_callback)

        if success:
            solution_info = auto_solver.get_solution_info()
            print(f"  SUCCESS! Solution found:")
            print(f"  Solution length: {solution_info['moves']} moves")
            if auto_solver._last_result:
                print(f"  States explored: {auto_solver._last_result.states_explored}")
            return True
        else:
            print(f"  FAILED: No solution found")
            if auto_solver._last_result:
                print(f"  States explored: {auto_solver._last_result.states_explored}")
    except Exception as e:
        print(f"  ERROR: {e}")

    return False

def test_simpler_original_level():
    """Test a simpler level from the Original collection."""
    print("\n" + "=" * 50)
    print("Testing a simpler Original level (Level 2)...")

    # Level 2 from Original.txt (should be easier)
    level_string = """############
#..  #     ###
#..  # $  $  #
#..  #$####  #
#..    @ ##  #
#..  # #  $ ##
###### ##$ $ #
  # $  $ $ $ #
  #    #     #
  ############"""

    print("Level:")
    print(level_string)

    level = Level(level_data=level_string)

    print(f"\nLevel info:")
    print(f"Size: {level.width}x{level.height}")
    print(f"Player: {level.player_pos}")
    print(f"Boxes: {len(level.boxes)} - {level.boxes}")
    print(f"Targets: {len(level.targets)} - {level.targets}")

    # Test with AutoSolver
    auto_solver = AutoSolver(level, renderer=None)
    print(f"Solver type: {auto_solver.solver_type}")

    def progress_callback(message):
        print(f"  {message}")

    try:
        success = auto_solver.solve_level(progress_callback)

        if success:
            solution_info = auto_solver.get_solution_info()
            print(f"  SUCCESS! Solution found:")
            print(f"  Solution length: {solution_info['moves']} moves")
            return True
        else:
            print(f"  FAILED: No solution found")
            return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Original Sokoban Level Test")
    print("=" * 50)

    # Test the problematic level
    level1_success = test_original_level()

    # Test a simpler level
    level2_success = test_simpler_original_level()

    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Original Level 1: {'SOLVED' if level1_success else 'TOO COMPLEX'}")
    print(f"Original Level 2: {'SOLVED' if level2_success else 'FAILED'}")
