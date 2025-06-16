import os
import time
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess import FESSSearchEngine

def test_fess_original_first_level():
    """Test the first level from Original.txt using the improved FESS algorithm."""
    print("🎯 Testing First Level from Original.txt with Improved FESS")
    print("=" * 50)
    
    # Load the Original.txt collection
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ File not found: {original_path}")
        return False
    
    try:
        # Parse the collection
        collection = LevelCollectionParser.parse_file(original_path)
        print(f"📁 Collection: {collection.title}")
        print(f"📊 Total levels: {collection.get_level_count()}")
        
        # Get the first level
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"🎮 Testing: {level_title}")
            print(f"📏 Size: {level.width}x{level.height}")
            print(f"📦 Boxes: {len(level.boxes)}")
            print(f"🎯 Targets: {len(level.targets)}")
            
            # Create FESS solver with improved algorithm
            solver = FESSSearchEngine(level, max_states=1000000, time_limit=120.0)
            
            def progress_callback(message):
                print(f"  🤖 {message}")
            
            print("\n🔍 Starting FESS analysis...")
            start_time = time.time()
            solution = solver.search(progress_callback)
            end_time = time.time()
            
            if solution:
                print(f"\n✅ SUCCESS!")
                print(f"   Solution: {len(solution)} moves")
                print(f"   States explored: {solver.states_explored}")
                print(f"   Time taken: {end_time - start_time:.2f} seconds")
                return True
            else:
                print(f"\n❌ FAILED: No solution found")
                print(f"   States explored: {solver.states_explored}")
                print(f"   Time limit: {solver.time_limit}s")
                print(f"   State limit: {solver.max_states}")
                
                # Show the level layout for reference
                print(f"\n📋 Level layout:")
                level_lines = level.get_state_string().strip().split('\n')
                for i, line in enumerate(level_lines, 1):
                    print(f"   {i:2d}: {line}")
                
                return False
                
        else:
            print("❌ No levels found in collection")
            return False
            
    except Exception as e:
        print(f"❌ Error loading collection: {e}")
        return False

if __name__ == "__main__":
    success = test_fess_original_first_level()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 The first Original.txt level CAN be solved by our improved FESS algorithm!")
    else:
        print("💡 The first Original.txt level is still too complex for our improved FESS algorithm.")