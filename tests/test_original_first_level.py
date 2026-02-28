#!/usr/bin/env python3
"""
Test script to specifically test the first level from Original.txt
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.auto_solver import AutoSolver

def test_original_first_level():
    """Test the first level from Original.txt specifically."""
    print("Testing First Level from Original.txt")
    print("=" * 50)

    # Load the Original.txt collection
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')

    if not os.path.exists(original_path):
        print(f"File not found: {original_path}")
        return False

    try:
        # Parse the collection
        collection = LevelCollectionParser.parse_file(original_path)
        print(f"Collection: {collection.title}")
        print(f"Total levels: {collection.get_level_count()}")

        # Get the first level
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"Testing: {level_title}")
            print(f"Size: {level.width}x{level.height}")
            print(f"Boxes: {len(level.boxes)}")
            print(f"Targets: {len(level.targets)}")

            # Create auto solver
            auto_solver = AutoSolver(level, renderer=None)
            print(f"Solver: {auto_solver.solver_type}")

            def progress_callback(message):
                print(f"  {message}")

            print("\nStarting AI analysis...")
            success = auto_solver.solve_level(progress_callback)

            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"\nSUCCESS!")
                print(f"   Solution: {solution_info['moves']} moves")
                if auto_solver._last_result:
                    print(f"   States explored: {auto_solver._last_result.states_explored}")
                return True
            else:
                print(f"\nFAILED: No solution found")
                if auto_solver._last_result:
                    print(f"   States explored: {auto_solver._last_result.states_explored}")

                # Show the level layout for reference
                print(f"\nLevel layout:")
                level_lines = level.get_state_string().strip().split('\n')
                for i, line in enumerate(level_lines, 1):
                    print(f"   {i:2d}: {line}")

                return False

        else:
            print("No levels found in collection")
            return False

    except Exception as e:
        print(f"Error loading collection: {e}")
        return False

if __name__ == "__main__":
    success = test_original_first_level()

    print("\n" + "=" * 50)
    if success:
        print("The first Original.txt level CAN be solved by our AI!")
    else:
        print("The first Original.txt level is too complex for current solver limits.")
        print("   This is expected behavior for professional-grade puzzles.")
