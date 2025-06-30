#!/usr/bin/env python3
"""
Test script for the Expert Sokoban Solver on the most challenging levels.
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.auto_solver import AutoSolver
from src.generation.expert_solver import ExpertSokobanSolver

def test_expert_solver_on_original():
    """Test the expert solver specifically on Original.txt first level."""
    print("🎯 Testing Expert IDA* Solver on Original.txt Level 1")
    print("=" * 70)
    
    # Load the Original.txt collection
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ File not found: {original_path}")
        return False
    
    try:
        # Parse the collection
        collection = LevelCollectionParser.parse_file(original_path)
        print(f"📁 Collection: {collection.title}")
        print(f"📊 Total levels: {collection.get_level_count()}")
        
        # Test the first level specifically
        level_title, level = collection.get_level(0)
        print(f"\n🎮 Testing: {level_title}")
        print(f"📏 Size: {level.width}x{level.height} ({level.width * level.height} cells)")
        print(f"📦 Boxes: {len(level.boxes)}")
        print(f"🎯 Targets: {len(level.targets)}")
        
        # Show level layout
        print(f"\n📋 Level layout:")
        level_lines = level.get_state_string().strip().split('\n')
        for i, line in enumerate(level_lines, 1):
            print(f"   {i:2d}: {line}")
        
        # Test with AutoSolver (should choose Expert solver)
        print(f"\n🤖 Testing with AutoSolver (automatic solver selection)...")
        auto_solver = AutoSolver(level, renderer=None)
        
        def progress_callback(message):
            print(f"  🔍 {message}")
        
        print(f"\n⏱️  Starting solve attempt...")
        start_time = time.time()
        
        success = auto_solver.solve_level(progress_callback)
        elapsed_time = time.time() - start_time
        
        if success:
            solution_info = auto_solver.get_solution_info()
            print(f"\n🎉 SUCCESS!")
            print(f"   Solution: {solution_info['moves']} moves")
            print(f"   Time: {elapsed_time:.2f} seconds")
            print(f"   Solver: {solution_info['solver_type']}")
            
            # Show solution moves
            solution = solution_info['solution']
            if len(solution) <= 30:
                print(f"   Moves: {' '.join(solution)}")
            else:
                print(f"   First 15 moves: {' '.join(solution[:15])}...")
                print(f"   Last 15 moves: {' '.join(solution[-15:])}")
            
            return True
        else:
            print(f"\n❌ FAILED: No solution found")
            print(f"   Time: {elapsed_time:.2f} seconds")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_expert_solver():
    """Test the expert solver directly on a simpler level first."""
    print(f"\n{'='*70}")
    print("🧪 Testing Expert Solver Directly on Simple Level")
    print("=" * 70)
    
    # Create a simple test level
    simple_level_data = """#######
#     #
# $ $ #
# . . #
#  @  #
#######"""
    
    from src.core.level import Level
    level = Level(level_data=simple_level_data)
    
    print(f"📋 Test level: {level.width}x{level.height}, {len(level.boxes)} boxes")
    
    # Test with expert solver directly
    expert_solver = ExpertSokobanSolver(level, time_limit=30.0)
    
    def progress_callback(message):
        print(f"  🔬 {message}")
    
    start_time = time.time()
    solution = expert_solver.solve(progress_callback)
    elapsed_time = time.time() - start_time
    
    if solution:
        stats = expert_solver.get_statistics()
        print(f"\n✅ Expert solver works!")
        print(f"   Solution: {len(solution)} moves")
        print(f"   Time: {elapsed_time:.3f} seconds")
        print(f"   Nodes explored: {stats['nodes_explored']}")
        print(f"   Deadlocks pruned: {stats['deadlocks_pruned']}")
        print(f"   Final threshold: {stats['final_threshold']}")
        print(f"   Moves: {' '.join(solution)}")
        return True
    else:
        print(f"\n❌ Expert solver failed on simple level")
        return False

def test_complexity_progression():
    """Test solver selection on levels of increasing complexity."""
    print(f"\n{'='*70}")
    print("📈 Testing Solver Selection on Different Complexity Levels")
    print("=" * 70)
    
    test_levels = [
        {
            "name": "Very Simple (1 box)",
            "data": """#####
#   #
# $ #
# . #
# @ #
#####""",
        },
        {
            "name": "Simple (2 boxes)",
            "data": """#######
#     #
# $$ #
# .. #
#  @ #
#######""",
        },
        {
            "name": "Medium (3 boxes)",
            "data": """########
#      #
# $$$  #
# ...  #
#   @  #
########""",
        },
        {
            "name": "Complex (4 boxes, tight space)",
            "data": """#########
#   #   #
# $ # $ #
# . # . #
#   #   #
# $ # $ #
# . # . #
#   @   #
#########""",
        }
    ]
    
    results = []
    
    for test_case in test_levels:
        print(f"\n--- {test_case['name']} ---")
        
        from src.core.level import Level
        level = Level(level_data=test_case['data'])
        
        # Create auto solver to see which solver is chosen
        auto_solver = AutoSolver(level, renderer=None)
        
        def progress_callback(message):
            print(f"  🤖 {message}")
        
        start_time = time.time()
        success = auto_solver.solve_level(progress_callback)
        elapsed_time = time.time() - start_time
        
        if success:
            solution_info = auto_solver.get_solution_info()
            print(f"  ✅ SOLVED in {elapsed_time:.3f}s")
            print(f"     Solver: {solution_info['solver_type']}")
            print(f"     Moves: {solution_info['moves']}")
            results.append(True)
        else:
            print(f"  ❌ FAILED in {elapsed_time:.3f}s")
            results.append(False)
    
    return results

if __name__ == "__main__":
    print("🧠 Expert Sokoban Solver Test Suite")
    print("=" * 70)
    
    # Test expert solver on simple level first
    simple_success = test_direct_expert_solver()
    
    # Test complexity progression
    progression_results = test_complexity_progression()
    
    # Test on Original.txt if basic tests pass
    if simple_success and all(progression_results):
        print(f"\n🚀 Basic tests passed! Now testing on Original.txt...")
        original_success = test_expert_solver_on_original()
    else:
        print(f"\n⚠️  Basic tests failed, skipping Original.txt test")
        original_success = False
    
    print(f"\n{'='*70}")
    print("📊 FINAL RESULTS:")
    print(f"   Expert solver basic test: {'✅ PASSED' if simple_success else '❌ FAILED'}")
    print(f"   Complexity progression: {sum(progression_results)}/{len(progression_results)} passed")
    print(f"   Original.txt Level 1: {'✅ SOLVED' if original_success else '❌ UNSOLVED'}")
    
    if original_success:
        print(f"\n🎉 MISSION ACCOMPLISHED!")
        print(f"   The Expert IDA* solver successfully solved Original.txt Level 1!")
        print(f"   This proves our advanced algorithms can handle professional Sokoban levels.")
    else:
        print(f"\n💡 PROGRESS MADE!")
        print(f"   While Original.txt Level 1 remains challenging, we've implemented")
        print(f"   state-of-the-art solving techniques that work on simpler levels.")
    
    print(f"\n🎮 To test in the game, run:")
    print(f"   python -m src.main --levels src/levels")
    print(f"   The system will automatically choose the best solver for each level!")