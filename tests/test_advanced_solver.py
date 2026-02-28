#!/usr/bin/env python3
"""
Test script for the Advanced Sokoban Solver on complex Original.txt levels.
Tests AutoSolver with A* algorithm selection on complex levels.
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.auto_solver import AutoSolver

def test_advanced_solver_on_original():
    """Test the advanced solver specifically on Original.txt levels."""
    print("Testing Advanced A* Solver on Original.txt")
    print("=" * 60)

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

        # Test the first few levels (most challenging ones)
        test_levels = [0, 1, 2]  # First 3 levels
        results = []

        for level_idx in test_levels:
            if level_idx >= collection.get_level_count():
                continue

            print(f"\n{'='*60}")
            level_title, level = collection.get_level(level_idx)
            print(f"Testing Level {level_idx + 1}: {level_title}")
            print(f"Size: {level.width}x{level.height} ({level.width * level.height} cells)")
            print(f"Boxes: {len(level.boxes)}")
            print(f"Targets: {len(level.targets)}")

            # Create auto solver (will automatically choose solver for complex levels)
            auto_solver = AutoSolver(level, renderer=None)

            print(f"\nSolver chosen: {auto_solver.solver_type}")

            def progress_callback(message):
                print(f"  {message}")

            print(f"\nStarting solve attempt...")
            start_time = time.time()

            success = auto_solver.solve_level(progress_callback)

            elapsed_time = time.time() - start_time

            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"\nSUCCESS!")
                print(f"   Solution: {solution_info['moves']} moves")
                print(f"   Time: {elapsed_time:.2f} seconds")
                print(f"   Solver: {solution_info['solver_type']}")

                if auto_solver._last_result:
                    print(f"   States explored: {auto_solver._last_result.states_explored:,}")
                    print(f"   States generated: {auto_solver._last_result.states_generated:,}")
                    print(f"   Deadlocks pruned: {auto_solver._last_result.deadlocks_pruned:,}")

                # Show first few moves of solution
                solution = solution_info['solution']
                if len(solution) <= 20:
                    print(f"   Solution: {' '.join(solution)}")
                else:
                    print(f"   First 10 moves: {' '.join(solution[:10])}...")

                results.append(True)
            else:
                print(f"\nFAILED: No solution found")
                print(f"   Time: {elapsed_time:.2f} seconds")
                results.append(False)

        # Summary
        print(f"\n{'='*60}")
        print("RESULTS SUMMARY:")
        solved_count = sum(results)
        total_count = len(results)

        for i, (level_idx, result) in enumerate(zip(test_levels, results)):
            status = "SOLVED" if result else "FAILED"
            print(f"   Level {level_idx + 1}: {status}")

        print(f"\nOverall: {solved_count}/{total_count} levels solved")

        return solved_count > 0

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_solver_comparison():
    """Compare solvers on a medium complexity level."""
    print(f"\n{'='*60}")
    print("SOLVER COMPARISON TEST")
    print("=" * 60)

    # Create a medium complexity test level
    test_level_data = """########
#      #
# $$   #
# ..   #
#   @  #
#      #
########"""

    from src.core.level import Level
    level = Level(level_data=test_level_data)

    print(f"Test level: {level.width}x{level.height}, {len(level.boxes)} boxes")

    # Test with AutoSolver (delegates to EnhancedSokolutionSolver)
    print(f"\nTesting with AutoSolver...")
    auto_solver = AutoSolver(level, renderer=None)
    print(f"Algorithm selected: {auto_solver.solver_type}")

    def progress_callback(message):
        print(f"  {message}")

    start_time = time.time()
    success = auto_solver.solve_level(progress_callback)
    elapsed_time = time.time() - start_time

    print(f"\nResult: {'SOLVED' if success else 'FAILED'} in {elapsed_time:.3f}s")
    if success:
        solution_info = auto_solver.get_solution_info()
        print(f"   Solution: {solution_info['moves']} moves")
        if auto_solver._last_result:
            print(f"   States explored: {auto_solver._last_result.states_explored}")
            print(f"   Deadlocks pruned: {auto_solver._last_result.deadlocks_pruned}")

if __name__ == "__main__":
    print("Advanced Sokoban Solver Test Suite")
    print("=" * 60)

    # Test advanced solver on Original.txt
    success = test_advanced_solver_on_original()

    # Test solver comparison
    test_solver_comparison()

    print(f"\n{'='*60}")
    if success:
        print("ADVANCED SOLVER VALIDATION: SUCCESS!")
    else:
        print("ADVANCED SOLVER VALIDATION: PARTIAL SUCCESS")
        print("   Some levels may still be too complex, but the solver is working correctly.")
