#!/usr/bin/env python3
"""
Final validation test for the advanced Sokoban solver system.
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.auto_solver import AutoSolver

def test_solver_progression():
    """Test the complete solver progression from simple to expert levels."""
    print("FINAL VALIDATION: Advanced Sokoban Solver System")
    print("=" * 80)

    test_cases = [
        {
            "name": "Level 1: Simple (Basic BFS Expected)",
            "data": """#####
#   #
# $ #
# . #
# @ #
#####""",
            "expected_solver": "Basic BFS"
        },
        {
            "name": "Level 2: Medium (Basic BFS Expected)",
            "data": """#######
#     #
# $$  #
# ..  #
#  @  #
#######""",
            "expected_solver": "Basic BFS"
        },
        {
            "name": "Level 3: Complex (Advanced A* Expected)",
            "data": """########
#      #
# $$$  #
# ...  #
#   @  #
#      #
########""",
            "expected_solver": "Advanced A*"
        },
        {
            "name": "Level 4: Expert (Expert IDA* Expected)",
            "data": """##########
#        #
# $$$$$  #
# .....  #
#    @   #
#        #
##########""",
            "expected_solver": "Expert IDA*"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"  {test_case['name']}")
        print("=" * 80)

        from src.core.level import Level
        level = Level(level_data=test_case['data'])

        print(f"Level: {level.width}x{level.height} ({level.width * level.height} cells)")
        print(f"Boxes: {len(level.boxes)}")
        print(f"Targets: {len(level.targets)}")

        # Create auto solver
        auto_solver = AutoSolver(level, renderer=None)

        def progress_callback(message):
            print(f"  {message}")

        print(f"\nStarting solve attempt...")
        start_time = time.time()

        success = auto_solver.solve_level(progress_callback)
        elapsed_time = time.time() - start_time

        if success:
            solution_info = auto_solver.get_solution_info()
            solver_used = solution_info['solver_type']

            print(f"\nSUCCESS!")
            print(f"   Solver Used: {solver_used}")
            print(f"   Expected: {test_case['expected_solver']}")
            print(f"   Match: {'YES' if solver_used == test_case['expected_solver'] else 'NO'}")
            print(f"   Solution: {solution_info['moves']} moves")
            print(f"   Time: {elapsed_time:.3f} seconds")
            print(f"   Complexity Score: {solution_info['complexity_score']:.1f}")

            # Show solution for simple levels
            if solution_info['moves'] <= 15:
                print(f"   Moves: {' '.join(solution_info['solution'])}")

            results.append({
                'success': True,
                'solver_match': solver_used == test_case['expected_solver'],
                'solver_used': solver_used,
                'time': elapsed_time,
                'moves': solution_info['moves']
            })
        else:
            print(f"\nFAILED: No solution found")
            print(f"   Time: {elapsed_time:.3f} seconds")
            results.append({
                'success': False,
                'solver_match': False,
                'solver_used': 'N/A',
                'time': elapsed_time,
                'moves': 0
            })

    return results

def test_original_level_detection():
    """Test that Original.txt levels are correctly detected as Expert."""
    print(f"\n{'='*80}")
    print("Testing Original.txt Level Detection")
    print("=" * 80)

    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')

    if not os.path.exists(original_path):
        print(f"File not found: {original_path}")
        return False

    try:
        collection = LevelCollectionParser.parse_file(original_path)
        level_title, level = collection.get_level(0)  # First level

        print(f"Collection: {collection.title}")
        print(f"Level: {level_title}")
        print(f"Size: {level.width}x{level.height}")
        print(f"Boxes: {len(level.boxes)}")

        # Create auto solver to check detection
        auto_solver = AutoSolver(level, renderer=None)

        print(f"\nComplexity Analysis:")
        print(f"   Score: {auto_solver.complexity_score:.1f}")
        print(f"   Solver Selected: {auto_solver.solver_type}")
        print(f"   Expected: Expert IDA* or higher")

        is_expert = auto_solver.solver_type in ("Expert IDA*", "Sokolution Bidirectional Greedy")
        print(f"   Correct Detection: {'YES' if is_expert else 'NO'}")

        return is_expert

    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main validation function."""
    print("ADVANCED SOKOBAN SOLVER SYSTEM - FINAL VALIDATION")
    print("=" * 80)
    print("Testing automatic solver selection and performance...")

    # Test solver progression
    results = test_solver_progression()

    # Test Original.txt detection
    original_detection = test_original_level_detection()

    # Summary
    print(f"\n{'='*80}")
    print("FINAL VALIDATION RESULTS")
    print("=" * 80)

    solved_count = sum(1 for r in results if r['success'])
    solver_match_count = sum(1 for r in results if r['solver_match'])

    print(f"Levels Solved: {solved_count}/{len(results)}")
    print(f"Correct Solver Selection: {solver_match_count}/{len(results)}")
    print(f"Original.txt Detection: {'CORRECT' if original_detection else 'INCORRECT'}")

    print(f"\nPerformance Summary:")
    for i, result in enumerate(results, 1):
        status = "SOLVED" if result['success'] else "FAILED"
        solver = result['solver_used']
        time_str = f"{result['time']:.3f}s"
        moves = result['moves'] if result['success'] else 0
        print(f"   Level {i}: {status} | {solver} | {time_str} | {moves} moves")

    # Overall assessment
    overall_success = (solved_count >= 3 and solver_match_count >= 3 and original_detection)

    print(f"\n{'='*80}")
    if overall_success:
        print("VALIDATION SUCCESSFUL!")
        print("   Multi-tier solver system working correctly")
        print("   Automatic complexity detection functional")
    else:
        print("VALIDATION PARTIAL SUCCESS")
        print("   System is functional but may need fine-tuning for optimal performance")

    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
