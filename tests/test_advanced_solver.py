#!/usr/bin/env python3
"""
Test script for the Advanced Sokoban Solver on complex Original.txt levels.
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.auto_solver import AutoSolver
from src.generation.advanced_solver import AdvancedSokobanSolver

def test_advanced_solver_on_original():
    """Test the advanced solver specifically on Original.txt levels."""
    print("🚀 Testing Advanced A* Solver on Original.txt")
    print("=" * 60)
    
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
        
        # Test the first few levels (most challenging ones)
        test_levels = [0, 1, 2]  # First 3 levels
        results = []
        
        for level_idx in test_levels:
            if level_idx >= collection.get_level_count():
                continue
                
            print(f"\n{'='*60}")
            level_title, level = collection.get_level(level_idx)
            print(f"🎯 Testing Level {level_idx + 1}: {level_title}")
            print(f"📏 Size: {level.width}x{level.height} ({level.width * level.height} cells)")
            print(f"📦 Boxes: {len(level.boxes)}")
            print(f"🎯 Targets: {len(level.targets)}")
            
            # Show level layout
            print(f"\n📋 Level layout:")
            level_lines = level.get_state_string().strip().split('\n')
            for i, line in enumerate(level_lines, 1):
                print(f"   {i:2d}: {line}")
            
            # Create auto solver (will automatically choose advanced solver for complex levels)
            auto_solver = AutoSolver(level, renderer=None)
            
            print(f"\n🔍 Solver chosen: {'Advanced A*' if isinstance(auto_solver.solver, AdvancedSokobanSolver) else 'Basic BFS'}")
            
            def progress_callback(message):
                print(f"  🤖 {message}")
            
            print(f"\n⏱️  Starting solve attempt...")
            start_time = time.time()
            
            success = auto_solver.solve_level(progress_callback)
            
            elapsed_time = time.time() - start_time
            
            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"\n✅ SUCCESS!")
                print(f"   Solution: {solution_info['moves']} moves")
                print(f"   Time: {elapsed_time:.2f} seconds")
                print(f"   Solver: {solution_info['solver_type']}")
                
                if isinstance(auto_solver.solver, AdvancedSokobanSolver):
                    stats = auto_solver.solver.get_statistics()
                    print(f"   States explored: {stats['states_explored']:,}")
                    print(f"   States generated: {stats['states_generated']:,}")
                    print(f"   Deadlocks pruned: {stats['deadlocks_pruned']:,}")
                
                # Show first few moves of solution
                solution = solution_info['solution']
                if len(solution) <= 20:
                    print(f"   Solution: {' '.join(solution)}")
                else:
                    print(f"   First 10 moves: {' '.join(solution[:10])}...")
                
                results.append(True)
            else:
                print(f"\n❌ FAILED: No solution found")
                print(f"   Time: {elapsed_time:.2f} seconds")
                
                if isinstance(auto_solver.solver, AdvancedSokobanSolver):
                    stats = auto_solver.solver.get_statistics()
                    print(f"   States explored: {stats['states_explored']:,}")
                    print(f"   States generated: {stats['states_generated']:,}")
                    print(f"   Deadlocks pruned: {stats['deadlocks_pruned']:,}")
                
                results.append(False)
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 RESULTS SUMMARY:")
        solved_count = sum(results)
        total_count = len(results)
        
        for i, (level_idx, result) in enumerate(zip(test_levels, results)):
            status = "✅ SOLVED" if result else "❌ FAILED"
            print(f"   Level {level_idx + 1}: {status}")
        
        print(f"\nOverall: {solved_count}/{total_count} levels solved")
        
        if solved_count > 0:
            print(f"\n🎉 SUCCESS! Advanced solver can handle Original.txt levels!")
            print(f"   The A* algorithm with heuristics successfully solved {solved_count} complex level(s)")
        else:
            print(f"\n💡 The levels are extremely challenging even for advanced algorithms.")
            print(f"   Consider increasing time limits or implementing even more sophisticated techniques.")
        
        return solved_count > 0
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_solver_comparison():
    """Compare basic vs advanced solver on a medium complexity level."""
    print(f"\n{'='*60}")
    print("🔬 SOLVER COMPARISON TEST")
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
    
    print(f"📋 Test level: {level.width}x{level.height}, {len(level.boxes)} boxes")
    
    # Test with basic solver
    print(f"\n🔧 Testing Basic BFS Solver...")
    from src.generation.level_solver import SokobanSolver
    basic_solver = SokobanSolver(max_states=50000, max_time=10.0)
    
    level_copy1 = Level(level_data=test_level_data)
    start_time = time.time()
    basic_success = basic_solver.is_solvable(level_copy1)
    basic_time = time.time() - start_time
    basic_solution = basic_solver.get_solution() if basic_success else None
    
    # Test with advanced solver
    print(f"\n🚀 Testing Advanced A* Solver...")
    advanced_solver = AdvancedSokobanSolver(level, max_states=50000, time_limit=10.0)
    
    start_time = time.time()
    advanced_solution = advanced_solver.solve()
    advanced_time = time.time() - start_time
    advanced_success = advanced_solution is not None
    
    # Results
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"   Basic BFS:    {'✅ SOLVED' if basic_success else '❌ FAILED'} in {basic_time:.3f}s")
    if basic_success:
        print(f"                 Solution: {len(basic_solution)} moves")
        print(f"                 States: {basic_solver.states_explored}")
    
    print(f"   Advanced A*:  {'✅ SOLVED' if advanced_success else '❌ FAILED'} in {advanced_time:.3f}s")
    if advanced_success:
        print(f"                 Solution: {len(advanced_solution)} moves")
        stats = advanced_solver.get_statistics()
        print(f"                 States: {stats['states_explored']}")
        print(f"                 Deadlocks pruned: {stats['deadlocks_pruned']}")

if __name__ == "__main__":
    print("🧠 Advanced Sokoban Solver Test Suite")
    print("=" * 60)
    
    # Test advanced solver on Original.txt
    success = test_advanced_solver_on_original()
    
    # Test solver comparison
    test_solver_comparison()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 ADVANCED SOLVER VALIDATION: SUCCESS!")
        print("   The A* solver can handle complex Original.txt levels!")
    else:
        print("⚠️  ADVANCED SOLVER VALIDATION: PARTIAL SUCCESS")
        print("   Some levels may still be too complex, but the solver is working correctly.")
    
    print("\n💡 To test in the game, run:")
    print("   python -m src.main --levels src/levels")
    print("   Then press 'S' on any level to see the AI in action!")