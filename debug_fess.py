import os
import time
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess import FESSSearchEngine, DeadlockDetector

def debug_fess_step_by_step():
    """Debug FESS step by step to identify issues."""
    print("🐛 Debugging FESS Step by Step")
    print("=" * 40)
    
    # Load a simple test level first
    simple_level_path = os.path.join('src', 'levels', 'Test', 'simple_test.txt')
    
    if not os.path.exists(simple_level_path):
        print(f"❌ Simple test file not found: {simple_level_path}")
        return False
    
    try:
        collection = LevelCollectionParser.parse_file(simple_level_path)
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"🎮 Testing simple level: {level_title}")
            print(f"📏 Size: {level.width}x{level.height}")
            print(f"📦 Boxes: {len(level.boxes)}")
            print(f"🎯 Targets: {len(level.targets)}")
            
            # Test deadlock detector
            print("\n🔍 Testing deadlock detector...")
            deadlock_detector = DeadlockDetector(level)
            print(f"  Deadlock squares found: {len(deadlock_detector.deadlock_squares)}")
            
            # Create FESS solver with short timeout
            print("\n🔍 Creating FESS solver...")
            solver = FESSSearchEngine(level, max_states=1000, time_limit=10.0)
            
            print(f"  Feature space initialized: {solver.feature_space is not None}")
            print(f"  Macro generator initialized: {solver.macro_generator is not None}")
            print(f"  Deadlock detector initialized: {solver.deadlock_detector is not None}")
            
            # Test initial state creation
            print("\n🔍 Testing initial state creation...")
            initial_state = solver._create_initial_state()
            print(f"  Initial player pos: {initial_state.player_pos}")
            print(f"  Initial boxes count: {len(initial_state.boxes)}")
            
            # Test feature analyzers
            print("\n🔍 Testing feature analyzers...")
            try:
                packed = solver.feature_space.packing_analyzer.calculate_packing_feature(initial_state)
                print(f"  Packing feature: {packed}")
                
                connectivity = solver.feature_space.connectivity_analyzer.calculate_connectivity(initial_state)
                print(f"  Connectivity feature: {connectivity}")
                
                oop = solver.feature_space.out_of_plan_analyzer.calculate_out_of_plan(initial_state)
                print(f"  Out-of-plan feature: {oop}")
                
                room_conn = solver.feature_space.room_analyzer.calculate_room_connectivity(initial_state)
                print(f"  Room connectivity feature: {room_conn}")
                
            except Exception as e:
                print(f"  ❌ Error in feature analyzers: {e}")
                return False
            
            # Test move generation
            print("\n🔍 Testing move generation...")
            try:
                solver._assign_move_weights(initial_state)
                print(f"  Moves generated: {len(initial_state.children_moves)}")
                if initial_state.children_moves:
                    print(f"  First few moves: {initial_state.children_moves[:3]}")
            except Exception as e:
                print(f"  ❌ Error in move generation: {e}")
                return False
            
            # Try a short search
            print("\n🔍 Testing short search...")
            def progress_callback(message):
                print(f"    {message}")
            
            start_time = time.time()
            solution = solver.search(progress_callback)
            end_time = time.time()
            
            print(f"\n📊 Results:")
            print(f"  Time taken: {end_time - start_time:.2f}s")
            print(f"  States explored: {solver.states_explored}")
            print(f"  States generated: {solver.states_generated}")
            print(f"  Deadlocks detected: {solver.deadlocks_detected}")
            print(f"  Solution found: {solution is not None}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_fess_step_by_step()