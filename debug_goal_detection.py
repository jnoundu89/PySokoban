import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess import FESSSearchEngine, FESSState

def debug_goal_detection():
    """Debug goal state detection."""
    print("🐛 Debugging Goal State Detection")
    print("=" * 40)
    
    # Load the simple test level
    simple_level_path = os.path.join('src', 'levels', 'Test', 'simple_test.txt')
    
    try:
        collection = LevelCollectionParser.parse_file(simple_level_path)
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"🎮 Testing: {level_title}")
            
            # Show level details
            print(f"\nLevel details:")
            print(f"  Player position: {level.player_pos}")
            print(f"  Boxes: {list(level.boxes)}")
            print(f"  Targets: {list(level.targets)}")
            
            # Show level layout
            print("\n📋 Level layout:")
            level_lines = level.get_state_string().strip().split('\n')
            for i, line in enumerate(level_lines, 1):
                print(f"   {i:2d}: {line}")
            
            # Create solver
            solver = FESSSearchEngine(level, max_states=100, time_limit=30.0)
            
            # Test initial state
            initial_state = solver._create_initial_state()
            print(f"\nInitial state:")
            print(f"  Player pos: {initial_state.player_pos}")
            print(f"  Boxes: {list(initial_state.boxes)}")
            print(f"  Is goal: {solver._is_goal_state(initial_state)}")
            
            # Create winning state manually
            target_pos = list(level.targets)[0]  # Get the target position
            winning_boxes = frozenset([target_pos])  # Box on target
            winning_state = FESSState(
                player_pos=initial_state.player_pos,
                boxes=winning_boxes
            )
            
            print(f"\nWinning state (manual):")
            print(f"  Player pos: {winning_state.player_pos}")
            print(f"  Boxes: {list(winning_state.boxes)}")
            print(f"  Targets: {list(level.targets)}")
            print(f"  Is goal: {solver._is_goal_state(winning_state)}")
            print(f"  Boxes == Targets: {winning_state.boxes == frozenset(level.targets)}")
            
            # Test all possible UP moves to see what happens
            print(f"\nTesting UP move from initial state:")
            up_state = solver._apply_basic_move(initial_state, 'UP', 0)
            if up_state:
                print(f"  UP move succeeded:")
                print(f"    Player pos: {up_state.player_pos}")
                print(f"    Boxes: {list(up_state.boxes)}")
                print(f"    Is goal: {solver._is_goal_state(up_state)}")
                
                # Check what the packing analyzer says
                packed = solver.feature_space.packing_analyzer.calculate_packing_feature(up_state)
                print(f"    Packing feature: {packed}")
                
                # Let's see the level state after this move
                print(f"    Level state visualization:")
                # We would need to create a level state visualizer here
                
            else:
                print(f"  UP move failed")
            
            # Let's manually simulate the correct sequence
            print(f"\nManual simulation:")
            player_x, player_y = initial_state.player_pos
            box_pos = list(initial_state.boxes)[0]
            target_pos = list(level.targets)[0]
            
            print(f"  Initial: Player {initial_state.player_pos}, Box {box_pos}, Target {target_pos}")
            
            # If player moves UP, they should push the box up
            new_player_pos = (player_x, player_y - 1)
            new_box_pos = (box_pos[0], box_pos[1] - 1)
            
            print(f"  After UP: Player would be {new_player_pos}, Box would be {new_box_pos}")
            print(f"  Target is at: {target_pos}")
            print(f"  Box on target? {new_box_pos == target_pos}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_goal_detection()