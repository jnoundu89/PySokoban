import os
import time
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess import FESSSearchEngine

def debug_fess_limits():
    """Debug why FESS _within_limits() returns False immediately."""
    print("🐛 Debugging FESS _within_limits() Method")
    print("=" * 40)
    
    # Load a simple test level
    simple_level_path = os.path.join('src', 'levels', 'Test', 'simple_test.txt')
    
    try:
        collection = LevelCollectionParser.parse_file(simple_level_path)
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"🎮 Testing: {level_title}")
            
            # Create FESS solver
            solver = FESSSearchEngine(level, max_states=100, time_limit=30.0)
            
            print(f"Solver initialized:")
            print(f"  max_states: {solver.max_states}")
            print(f"  time_limit: {solver.time_limit}")
            print(f"  states_explored: {solver.states_explored}")
            print(f"  start_time: {solver.start_time}")
            
            # Initialize solver properly
            solver.start_time = time.time()
            print(f"  start_time after setting: {solver.start_time}")
            
            # Test _within_limits before and after
            print(f"\nTesting _within_limits():")
            
            current_time = time.time()
            time_check = current_time - solver.start_time <= solver.time_limit
            states_check = solver.states_explored <= solver.max_states
            
            print(f"  Current time: {current_time}")
            print(f"  Elapsed time: {current_time - solver.start_time}")
            print(f"  Time limit: {solver.time_limit}")
            print(f"  Time check (elapsed <= limit): {time_check}")
            print(f"  States explored: {solver.states_explored}")
            print(f"  States limit: {solver.max_states}")
            print(f"  States check (explored <= limit): {states_check}")
            print(f"  Overall _within_limits(): {solver._within_limits()}")
            
            # Try a manual loop with explicit checks
            print(f"\nTrying manual loop with explicit checks:")
            
            initial_state = solver._create_initial_state()
            initial_state.accumulated_weight = 0
            solver.search_tree.add_root(initial_state)
            solver.feature_space.add_state_to_cell(initial_state)
            solver._assign_move_weights(initial_state)
            
            iteration = 0
            max_iterations = 10
            
            while iteration < max_iterations:
                iteration += 1
                print(f"\n--- Iteration {iteration} ---")
                
                # Explicit limit checks
                current_time = time.time()
                elapsed = current_time - solver.start_time
                time_ok = elapsed <= solver.time_limit
                states_ok = solver.states_explored <= solver.max_states
                
                print(f"  Elapsed: {elapsed:.2f}s, Time OK: {time_ok}")
                print(f"  States: {solver.states_explored}, States OK: {states_ok}")
                print(f"  _within_limits(): {solver._within_limits()}")
                
                if not solver._within_limits():
                    print("  _within_limits() returned False - breaking")
                    break
                
                # Try to get next cell
                current_fs_cell = solver.feature_space.get_next_cell_for_cycling()
                print(f"  Next FS cell: {current_fs_cell}")
                
                if current_fs_cell is None:
                    print("  No FS cell - breaking")
                    break
                
                # Get states in cell
                states_in_cell = solver.feature_space.get_states_in_cell(current_fs_cell)
                print(f"  States in cell: {len(states_in_cell)}")
                
                # Try to get a move
                best_move_info = solver._find_least_weight_unexpanded_move(states_in_cell)
                print(f"  Best move info: {best_move_info}")
                
                if best_move_info is None:
                    print("  No move available - continuing")
                    continue
                
                parent_state, move, weight = best_move_info
                print(f"  Selected move: {move}")
                
                # Apply the move
                new_state = solver._apply_move(parent_state, move, weight)
                
                if new_state is None:
                    print("  Move failed - continuing")
                    continue
                
                print(f"  Move succeeded")
                
                # Check deadlock
                if solver.deadlock_detector.is_deadlock(new_state):
                    print("  Deadlock detected - continuing")
                    solver.deadlocks_detected += 1
                    continue
                
                # Add state
                new_state.accumulated_weight = parent_state.accumulated_weight + weight
                
                if not solver.search_tree.add_state(new_state):
                    print("  State already exists - continuing")
                    continue
                
                solver.states_generated += 1
                solver.states_explored += 1
                
                print(f"  New state added - explored: {solver.states_explored}")
                
                # Add to feature space and assign weights
                solver.feature_space.add_state_to_cell(new_state)
                solver._assign_move_weights(new_state)
                
                # Check for goal
                if solver._is_goal_state(new_state):
                    print("  🎯 GOAL STATE FOUND!")
                    return True
            
            print(f"\n📊 Final stats:")
            print(f"  Iterations: {iteration}")
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
    debug_fess_limits()