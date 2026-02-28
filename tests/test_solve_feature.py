#!/usr/bin/env python3
"""
Test script for the new Solve feature.

This script tests the AutoSolver functionality with a simple level.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.level import Level
from src.core.auto_solver import AutoSolver

def test_auto_solver():
    """Test the AutoSolver with a simple level."""
    print("Testing AutoSolver functionality...")
    print("=" * 50)
    
    # Create a simple test level
    level_string = """
#####
#   #
# $ #
# . #
# @ #
#####
"""
    
    print("Test level:")
    print(level_string)
    
    # Create level
    level = Level(level_data=level_string)
    
    # Create auto solver
    auto_solver = AutoSolver(level)
    
    # Progress callback
    def progress_callback(message):
        print(f"Progress: {message}")
    
    print("\nSolving level...")
    success = auto_solver.solve_level(progress_callback)
    
    if success:
        solution_info = auto_solver.get_solution_info()
        print(f"\n✅ SUCCESS!")
        print(f"Solution length: {solution_info['moves']} moves")
        print(f"Solver: {solution_info['solver_type']}")
        print(f"Solution: {' -> '.join(solution_info['solution'])}")

        # Test that the solution actually works
        print("\nVerifying solution...")
        test_level = Level(level_data=level_string)

        direction_map = {
            'UP': (0, -1), 'DOWN': (0, 1),
            'LEFT': (-1, 0), 'RIGHT': (1, 0)
        }

        for i, move in enumerate(solution_info['solution']):
            if move in direction_map:
                dx, dy = direction_map[move]
            else:
                print(f"Unknown move: {move}")
                return False

            moved = test_level.move(dx, dy)
            if not moved:
                print(f"Move {i+1} ({move}) failed!")
                return False

        if test_level.is_completed():
            print("Solution verified successfully!")
            return True
        else:
            print("Solution does not complete the level!")
            return False
    else:
        print("❌ FAILED: No solution found")
        return False

def test_complex_level():
    """Test with a more complex level."""
    print("\n" + "=" * 50)
    print("Testing with a more complex level...")
    
    # A slightly more complex level
    complex_level = """
#######
#     #
# $$  #
# ..  #
#  @  #
#     #
#######
"""
    
    print("Complex test level:")
    print(complex_level)
    
    level = Level(level_data=complex_level)
    auto_solver = AutoSolver(level)
    
    def progress_callback(message):
        print(f"Progress: {message}")
    
    print("\nSolving complex level...")
    success = auto_solver.solve_level(progress_callback)
    
    if success:
        solution_info = auto_solver.get_solution_info()
        print(f"\n✅ SUCCESS!")
        print(f"Solution length: {solution_info['moves']} moves")
        print(f"Solver: {solution_info['solver_type']}")
        print(f"Solution: {' -> '.join(solution_info['solution'])}")
        return True
    else:
        print("❌ FAILED: No solution found")
        return False

if __name__ == "__main__":
    print("🧩 Sokoban AutoSolver Test")
    print("=" * 50)
    
    # Test simple level
    simple_success = test_auto_solver()
    
    # Test complex level
    complex_success = test_complex_level()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Simple level: {'✅ PASS' if simple_success else '❌ FAIL'}")
    print(f"Complex level: {'✅ PASS' if complex_success else '❌ FAIL'}")
    
    if simple_success and complex_success:
        print("\n🎉 All tests passed! The Solve feature is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")