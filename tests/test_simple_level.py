import os
import time
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess import FESSSearchEngine

def test_simple_level():
    """Test the enhanced FESS on the simple level."""
    print("🎯 Testing Enhanced FESS on Simple Level")
    print("=" * 40)
    
    # Load the simple test level
    simple_level_path = os.path.join('../src', 'levels', 'Test', 'simple_test.txt')
    
    if not os.path.exists(simple_level_path):
        print(f"❌ File not found: {simple_level_path}")
        return False
    
    try:
        collection = LevelCollectionParser.parse_file(simple_level_path)
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"🎮 Testing: {level_title}")
            print(f"📏 Size: {level.width}x{level.height}")
            print(f"📦 Boxes: {len(level.boxes)}")
            print(f"🎯 Targets: {len(level.targets)}")
            
            # Show level layout
            print("\n📋 Level layout:")
            level_lines = level.get_state_string().strip().split('\n')
            for i, line in enumerate(level_lines, 1):
                print(f"   {i:2d}: {line}")
            
            # Create FESS solver with generous limits for simple level
            solver = FESSSearchEngine(level, max_states=10000, time_limit=30.0)
            
            def progress_callback(message):
                print(f"  🤖 {message}")
            
            print("\n🔍 Starting FESS analysis...")
            start_time = time.time()
            solution = solver.search(progress_callback)
            end_time = time.time()
            
            if solution:
                print(f"\n✅ SUCCESS!")
                print(f"   Solution: {solution}")
                print(f"   Moves: {len(solution)}")
                print(f"   States explored: {solver.states_explored}")
                print(f"   States generated: {solver.states_generated}")
                print(f"   Deadlocks detected: {solver.deadlocks_detected}")
                print(f"   Time taken: {end_time - start_time:.2f} seconds")
                return True
            else:
                print(f"\n❌ FAILED: No solution found")
                print(f"   States explored: {solver.states_explored}")
                print(f"   States generated: {solver.states_generated}")
                print(f"   Deadlocks detected: {solver.deadlocks_detected}")
                print(f"   Time taken: {end_time - start_time:.2f} seconds")
                
                return False
                
        else:
            print("❌ No levels found in collection")
            return False
            
    except Exception as e:
        print(f"❌ Error loading collection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_level()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 The enhanced FESS algorithm solved the simple level!")
    else:
        print("💡 The enhanced FESS algorithm still needs improvements.")