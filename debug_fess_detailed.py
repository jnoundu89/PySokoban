import os
import time
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess import FESSSearchEngine

def debug_fess_search_loop():
    """Debug the FESS search loop in detail."""
    print("🐛 Debugging FESS Search Loop")
    print("=" * 40)
    
    # Load a simple test level
    simple_level_path = os.path.join('src', 'levels', 'Test', 'simple_test.txt')
    
    try:
        collection = LevelCollectionParser.parse_file(simple_level_path)
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"🎮 Testing: {level_title}")
            
            # Show level layout
            print("\n📋 Level layout:")
            level_lines = level.get_state_string().strip().split('\n')
            for i, line in enumerate(level_lines, 1):
                print(f"   {i:2d}: {line}")
            
            # Create FESS solver with minimal limits for debugging
            solver = FESSSearchEngine(level, max_states=100, time_limit=30.0)
            
            # Manual search loop debugging
            print("\n🔍 Manual search loop debugging...")
            
            initial_state = solver._create_initial_state()
            initial_state.accumulated_weight = 0
            
            solver.search_tree.add_root(initial_state)
            solver.feature_space.add_state_to_cell(initial_state)
            solver._assign_move_weights(initial_state)
            
            print(f"Initial state moves: {len(initial_state.children_moves)}")
            for i, (move, weight) in enumerate(initial_state.children_moves):
                print(f"  {i+1}. {move}: weight={weight}")
            
            # Check feature space
            print(f"\nFeature space cells: {len(solver.feature_space.non_empty_cells)}")
            print(f"Feature space stats: {solver.feature_space.get_statistics()}")
            
            iteration = 0
            max_iterations = 20
            
            while iteration < max_iterations and solver._within_limits():
                iteration += 1
                print(f"\n--- Iteration {iteration} ---")
                
                # Pick the next cell
                current_fs_cell = solver.feature_space.get_next_cell_for_cycling()
                print(f"Selected FS cell: {current_fs_cell}")
                
                if current_fs_cell is None:
                    print("No FS cell available - breaking")
                    break
                
                # Find states in cell
                states_in_cell = solver.feature_space.get_states_in_cell(current_fs_cell)
                print(f"States in cell: {len(states_in_cell)}")
                
                # Find best move
                best_move_info = solver._find_least_weight_unexpanded_move(states_in_cell)
                
                if best_move_info is None:
                    print("No moves available - continuing")
                    continue
                
                parent_state, move, weight = best_move_info
                print(f"Selected move: {move} with weight {weight}")
                
                # Apply move
                new_state = solver._apply_move(parent_state, move, weight)
                
                if new_state is None:
                    print("Move application failed - continuing")
                    continue
                
                print(f"New state created - player: {new_state.player_pos}, boxes: {len(new_state.boxes)}")
                
                # Check deadlock
                if solver.deadlock_detector.is_deadlock(new_state):
                    print("State is deadlock - skipping")
                    solver.deadlocks_detected += 1
                    continue
                
                # Check if goal
                if solver._is_goal_state(new_state):
                    print("🎯 GOAL STATE FOUND!")
                    return True
                
                # Add to search tree
                new_state.accumulated_weight = parent_state.accumulated_weight + weight
                
                if not solver.search_tree.add_state(new_state):
                    print("State already exists - continuing")
                    continue
                
                solver.states_generated += 1
                solver.states_explored += 1
                
                # Add to feature space
                solver.feature_space.add_state_to_cell(new_state)
                
                # Assign weights
                solver._assign_move_weights(new_state)
                print(f"New state has {len(new_state.children_moves)} moves")
                
                # Check progress
                packed = solver.feature_space.packing_analyzer.calculate_packing_feature(new_state)
                print(f"Packing progress: {packed}/{len(level.targets)}")
                
            print(f"\n📊 Final stats after {iteration} iterations:")
            print(f"  States explored: {solver.states_explored}")
            print(f"  States generated: {solver.states_generated}")
            print(f"  Deadlocks detected: {solver.deadlocks_detected}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_fess_search_loop()