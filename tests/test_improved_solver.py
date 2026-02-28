#!/usr/bin/env python3
"""
Test script for the improved AutoSolver with adaptive complexity.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.level import Level
from src.core.auto_solver import AutoSolver

def test_improved_solver():
    """Test the improved AutoSolver with adaptive complexity."""
    print("Testing Improved AutoSolver...")
    print("=" * 50)

    # Test levels of different complexity
    test_levels = [
        {
            "name": "Simple Test Level",
            "level": """#####
#   #
# $ #
# . #
# @ #
#####""",
        },
        {
            "name": "Medium Test Level",
            "level": """#######
#     #
# $$  #
# ..  #
#  @  #
#     #
#######""",
        },
        {
            "name": "Original Level 1 (Very Complex)",
            "level": """    #####
    #   #
    #$  #
  ###  $##
  #  $ $ #
### # ## #   ######
#   # ## #####  ..#
# $  $          ..#
##### ### #@##  ..#
    #     #########
    #######""",
        }
    ]

    results = []

    for test_case in test_levels:
        print(f"\n--- Testing: {test_case['name']} ---")

        # Create level
        level = Level(level_data=test_case['level'])

        print(f"Level info:")
        print(f"  Size: {level.width}x{level.height}")
        print(f"  Boxes: {len(level.boxes)}")
        print(f"  Targets: {len(level.targets)}")

        # Create improved auto solver (will auto-adjust complexity)
        auto_solver = AutoSolver(level, renderer=None)

        def progress_callback(message):
            print(f"  AI: {message}")

        try:
            success = auto_solver.solve_level(progress_callback)

            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"  SUCCESS!")
                print(f"  Solution length: {solution_info['moves']} moves")
                if auto_solver._last_result:
                    print(f"  States explored: {auto_solver._last_result.states_explored}")
                results.append(True)
            else:
                print(f"  FAILED: No solution found")
                results.append(False)

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(False)

    return results

def test_original_levels_sample():
    """Test a few levels from the original collection."""
    print("\n" + "=" * 50)
    print("Testing Sample Original Levels...")

    # Test some levels that might be solvable
    original_levels = [
        {
            "name": "Original Level 6",
            "level": """######  ###
#..  # ##@##
#..  ###   #
#..     $$ #
#..  # # $ #
#..### # $ #
#### $ #$  #
   #  $# $ #
   # $  $  #
   #  ##   #
   #########""",
        },
        {
            "name": "Original Level 32",
            "level": """       ####
   #####  #
  ##     $#
 ## $  ## ###
 #@$ $ # $  #
 #### ##   $#
  #....#$ $ #
  #....#   $#
  #....  $$ ##
  #... # $   #
  ######$ $  #
       #   ###
       #$ ###
       #  #
       ####""",
        }
    ]

    results = []

    for test_case in original_levels:
        print(f"\n--- Testing: {test_case['name']} ---")

        level = Level(level_data=test_case['level'])

        print(f"Level info:")
        print(f"  Size: {level.width}x{level.height}")
        print(f"  Boxes: {len(level.boxes)}")
        print(f"  Targets: {len(level.targets)}")

        auto_solver = AutoSolver(level, renderer=None)

        def progress_callback(message):
            print(f"  AI: {message}")

        try:
            success = auto_solver.solve_level(progress_callback)

            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"  SUCCESS!")
                print(f"  Solution length: {solution_info['moves']} moves")
                results.append(True)
            else:
                print(f"  FAILED: No solution found")
                results.append(False)

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(False)

    return results

if __name__ == "__main__":
    print("Improved AutoSolver Test")
    print("=" * 50)

    # Test improved solver
    main_results = test_improved_solver()

    # Test original levels
    original_results = test_original_levels_sample()

    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Simple level: {'SOLVED' if main_results[0] else 'FAILED'}")
    print(f"Medium level: {'SOLVED' if main_results[1] else 'FAILED'}")
    print(f"Complex original level: {'SOLVED' if main_results[2] else 'TOO COMPLEX'}")

    if len(original_results) > 0:
        print(f"Original Level 6: {'SOLVED' if original_results[0] else 'FAILED'}")
        print(f"Original Level 32: {'SOLVED' if original_results[1] else 'FAILED'}")

    solved_count = sum(main_results + original_results)
    total_count = len(main_results + original_results)

    print(f"\nOverall: {solved_count}/{total_count} levels solved")

    if main_results[0] and main_results[1]:
        print("\nImproved solver works well for simple and medium levels!")
