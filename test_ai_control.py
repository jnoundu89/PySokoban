#!/usr/bin/env python3
"""
Test script for the AI control feature.

This script tests that the AI can take control and solve levels automatically.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.level import Level
from src.core.auto_solver import AutoSolver

def test_ai_control():
    """Test that AI can take control and solve a level."""
    print("Testing AI Control functionality...")
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
    
    print(f"Initial state:")
    print(f"Player position: {level.player_pos}")
    print(f"Boxes: {level.boxes}")
    print(f"Targets: {level.targets}")
    print(f"Moves: {level.moves}")
    print(f"Completed: {level.is_completed()}")
    
    # Create auto solver (without renderer for testing)
    auto_solver = AutoSolver(level, renderer=None)
    
    # Progress callback
    def progress_callback(message):
        print(f"AI: {message}")
    
    print("\nAI analyzing level...")
    success = auto_solver.solve_level(progress_callback)
    
    if success:
        solution_info = auto_solver.get_solution_info()
        print(f"\n✅ AI found solution!")
        print(f"Solution length: {solution_info['moves']} moves")
        print(f"Solution: {' -> '.join(solution_info['solution'])}")
        
        print(f"\n🤖 AI taking control of the level...")
        
        # Let AI execute the solution live
        ai_success = auto_solver.execute_solution_live(
            move_delay=100,  # Fast for testing
            show_grid=False,
            zoom_level=1.0,
            scroll_x=0,
            scroll_y=0,
            level_manager=None
        )
        
        print(f"\nFinal state after AI control:")
        print(f"Player position: {level.player_pos}")
        print(f"Boxes: {level.boxes}")
        print(f"Targets: {level.targets}")
        print(f"Moves: {level.moves}")
        print(f"Completed: {level.is_completed()}")
        
        if ai_success and level.is_completed():
            print("\n🎉 SUCCESS: AI successfully took control and solved the level!")
            return True
        else:
            print("\n❌ FAILED: AI could not complete the level")
            return False
    else:
        print("❌ FAILED: AI could not find a solution")
        return False

def test_ai_control_complex():
    """Test AI control with a more complex level."""
    print("\n" + "=" * 50)
    print("Testing AI Control with complex level...")
    
    # A more complex level
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
    auto_solver = AutoSolver(level, renderer=None)
    
    def progress_callback(message):
        print(f"AI: {message}")
    
    print(f"Initial state:")
    print(f"Player: {level.player_pos}, Boxes: {level.boxes}, Moves: {level.moves}")
    
    print("\nAI analyzing complex level...")
    success = auto_solver.solve_level(progress_callback)
    
    if success:
        solution_info = auto_solver.get_solution_info()
        print(f"\n✅ AI found solution!")
        print(f"Solution length: {solution_info['moves']} moves")
        
        print(f"\n🤖 AI taking control of complex level...")
        
        ai_success = auto_solver.execute_solution_live(
            move_delay=50,  # Very fast for testing
            show_grid=False,
            zoom_level=1.0,
            scroll_x=0,
            scroll_y=0,
            level_manager=None
        )
        
        print(f"\nFinal state:")
        print(f"Player: {level.player_pos}, Boxes: {level.boxes}, Moves: {level.moves}")
        print(f"Completed: {level.is_completed()}")
        
        if ai_success and level.is_completed():
            print("\n🎉 SUCCESS: AI solved complex level!")
            return True
        else:
            print("\n❌ FAILED: AI could not complete complex level")
            return False
    else:
        print("❌ FAILED: AI could not find solution for complex level")
        return False

def test_ai_partial_solve():
    """Test AI control when level is partially solved."""
    print("\n" + "=" * 50)
    print("Testing AI Control from partial state...")
    
    level_string = """
#######
#     #
# $$  #
# ..  #
#  @  #
#     #
#######
"""
    
    level = Level(level_data=level_string)
    
    # Make some manual moves first
    print("Making some manual moves first...")
    level.move(0, -1)  # up
    level.move(1, 0)   # right
    
    print(f"After manual moves:")
    print(f"Player: {level.player_pos}, Boxes: {level.boxes}, Moves: {level.moves}")
    
    # Now let AI take over
    auto_solver = AutoSolver(level, renderer=None)
    
    def progress_callback(message):
        print(f"AI: {message}")
    
    print("\nAI analyzing partially solved level...")
    success = auto_solver.solve_level(progress_callback)
    
    if success:
        print(f"\n🤖 AI taking control from current state...")
        
        ai_success = auto_solver.execute_solution_live(
            move_delay=50,
            show_grid=False,
            zoom_level=1.0,
            scroll_x=0,
            scroll_y=0,
            level_manager=None
        )
        
        print(f"\nFinal state:")
        print(f"Player: {level.player_pos}, Boxes: {level.boxes}, Moves: {level.moves}")
        print(f"Completed: {level.is_completed()}")
        
        if ai_success and level.is_completed():
            print("\n🎉 SUCCESS: AI completed partially solved level!")
            return True
        else:
            print("\n❌ FAILED: AI could not complete from partial state")
            return False
    else:
        print("❌ FAILED: AI could not find solution from partial state")
        return False

if __name__ == "__main__":
    print("🤖 AI Control Test Suite")
    print("=" * 50)
    
    # Test simple level
    simple_success = test_ai_control()
    
    # Test complex level
    complex_success = test_ai_control_complex()
    
    # Test partial solve
    partial_success = test_ai_partial_solve()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Simple AI control: {'✅ PASS' if simple_success else '❌ FAIL'}")
    print(f"Complex AI control: {'✅ PASS' if complex_success else '❌ FAIL'}")
    print(f"Partial AI control: {'✅ PASS' if partial_success else '❌ FAIL'}")
    
    if simple_success and complex_success and partial_success:
        print("\n🎉 All AI control tests passed! The AI can successfully take control and solve levels.")
    else:
        print("\n⚠️  Some AI control tests failed. Please check the implementation.")