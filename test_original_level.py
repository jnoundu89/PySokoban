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
from src.generation.level_solver import SokobanSolver

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
    
    # Test with different solver configurations
    configs = [
        {"max_states": 50000, "max_time": 5.0, "name": "Current (Fast)"},
        {"max_states": 100000, "max_time": 10.0, "name": "Medium"},
        {"max_states": 200000, "max_time": 20.0, "name": "Slow"},
        {"max_states": 500000, "max_time": 30.0, "name": "Very Slow"},
    ]
    
    for config in configs:
        print(f"\n--- Testing with {config['name']} settings ---")
        print(f"Max states: {config['max_states']}, Max time: {config['max_time']}s")
        
        # Create solver with specific config
        solver = SokobanSolver(max_states=config['max_states'], max_time=config['max_time'])
        
        # Create auto solver
        auto_solver = AutoSolver(level, renderer=None)
        auto_solver.solver = solver  # Use our custom solver
        
        def progress_callback(message):
            print(f"  {message}")
        
        try:
            success = auto_solver.solve_level(progress_callback)
            
            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"  ✅ SUCCESS! Solution found:")
                print(f"  Solution length: {solution_info['moves']} moves")
                print(f"  States explored: {solver.states_explored}")
                return True
            else:
                print(f"  ❌ FAILED: No solution found")
                print(f"  States explored: {solver.states_explored}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
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
    
    # Test with medium settings
    solver = SokobanSolver(max_states=100000, max_time=15.0)
    auto_solver = AutoSolver(level, renderer=None)
    auto_solver.solver = solver
    
    def progress_callback(message):
        print(f"  {message}")
    
    try:
        success = auto_solver.solve_level(progress_callback)
        
        if success:
            solution_info = auto_solver.get_solution_info()
            print(f"  ✅ SUCCESS! Solution found:")
            print(f"  Solution length: {solution_info['moves']} moves")
            print(f"  States explored: {solver.states_explored}")
            return True
        else:
            print(f"  ❌ FAILED: No solution found")
            print(f"  States explored: {solver.states_explored}")
            return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🧩 Original Sokoban Level Test")
    print("=" * 50)
    
    # Test the problematic level
    level1_success = test_original_level()
    
    # Test a simpler level
    level2_success = test_simpler_original_level()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Original Level 1: {'✅ SOLVED' if level1_success else '❌ TOO COMPLEX'}")
    print(f"Original Level 2: {'✅ SOLVED' if level2_success else '❌ FAILED'}")
    
    if not level1_success:
        print("\n💡 RECOMMENDATION:")
        print("The first level from Original.txt is extremely complex.")
        print("Consider increasing solver limits or using a more powerful algorithm.")
        print("Many classic Sokoban levels require advanced solving techniques.")