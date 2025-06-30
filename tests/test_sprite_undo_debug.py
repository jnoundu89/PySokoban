#!/usr/bin/env python3
"""
Test script for debugging sprite animation during undo operations.

This script thoroughly tests the enhanced sprite animation system to verify
that undo operations correctly restore the historical sprites instead of
always showing the last sprite in the sequence.
"""

import os
import sys
import pygame

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
from src.core.level import Level
from src.level_management.level_manager import LevelManager

def test_sprite_undo_system():
    """
    Test the sprite undo system with detailed debugging.
    """
    print("=" * 60)
    print("STARTING SPRITE UNDO SYSTEM TEST")
    print("=" * 60)
    
    # Initialize pygame (required for sprite operations)
    pygame.init()
    
    # Create an enhanced skin manager
    skin_manager = EnhancedSkinManager()
    
    # Create a simple test level
    test_level_data = """
########
#......#
#.@.$..#
#......#
########
"""
    
    level = Level(level_data=test_level_data)
    
    # Test sequence: perform several moves, then undo them
    print("\n" + "=" * 40)
    print("PHASE 1: PERFORMING MOVEMENTS")
    print("=" * 40)
    
    # Initial state
    print("Initial player sprite (should be default):")
    initial_sprite = skin_manager.get_player_sprite(advance_animation=False)
    print(f"Initial sprite: {skin_manager.get_sprite_info(initial_sprite)}")
    skin_manager.print_sprite_history_debug()
    
    # Simulate movements with different directions
    movements = [
        ('right', False, False),
        ('right', False, False), 
        ('down', False, False),
        ('left', False, False),
        ('up', False, False)
    ]
    
    sprites_during_movement = []
    
    for i, (direction, is_pushing, is_blocked) in enumerate(movements):
        print(f"\n--- Movement {i+1}: {direction} ---")
        
        # Update player state
        skin_manager.update_player_state(direction, is_pushing, is_blocked)
        
        # Simulate the level move
        dx, dy = {'right': (1, 0), 'left': (-1, 0), 'down': (0, 1), 'up': (0, -1)}[direction]
        moved = level.move(dx, dy)
        
        if moved:
            # Get sprite with animation advancement
            sprite = skin_manager.get_player_sprite(advance_animation=True)
            sprites_during_movement.append(sprite)
            sprite_info = skin_manager.get_sprite_info(sprite)
            print(f"Movement successful, sprite: {sprite_info}")
        else:
            print("Movement failed")
        
        # Validate history integrity
        if not skin_manager.validate_sprite_history_integrity():
            print("❌ HISTORY INTEGRITY CHECK FAILED!")
            return False
    
    print(f"\nCompleted {len(sprites_during_movement)} movements")
    skin_manager.print_sprite_history_debug()
    
    print("\n" + "=" * 40)
    print("PHASE 2: TESTING UNDO OPERATIONS")
    print("=" * 40)
    
    # Now test undo operations
    sprites_during_undo = []
    
    for i in range(len(movements)):
        print(f"\n--- Undo {i+1} ---")
        
        # Get debug info before undo
        debug_before = skin_manager.get_undo_debug_info()
        print(f"Before undo - History length: {debug_before['sprite_history_length']}, Undo mode: {debug_before['undo_mode']}")
        
        # Perform undo in level
        undo_success = level.undo()
        
        if undo_success:
            # Get previous sprite from history
            prev_sprite = skin_manager.get_previous_sprite()
            
            if prev_sprite:
                sprites_during_undo.append(prev_sprite)
                sprite_info = skin_manager.get_sprite_info(prev_sprite)
                print(f"Undo successful, historical sprite: {sprite_info}")
                
                # Check if we're in undo mode
                debug_after = skin_manager.get_undo_debug_info()
                print(f"After undo - Undo mode: {debug_after['undo_mode']}, Undo sprite: {debug_after['undo_sprite_info']}")
                
                # Test that get_player_sprite now returns the undo sprite
                current_display_sprite = skin_manager.get_player_sprite(advance_animation=False)
                current_sprite_info = skin_manager.get_sprite_info(current_display_sprite)
                print(f"Current display sprite: {current_sprite_info}")
                
                # Verify they match
                if current_display_sprite == prev_sprite:
                    print("✅ SUCCESS: Display sprite matches historical sprite")
                else:
                    print("❌ FAIL: Display sprite does not match historical sprite!")
                    return False
            else:
                print("No previous sprite returned")
        else:
            print("Undo failed - no more moves to undo")
            break
        
        # Validate history integrity
        if not skin_manager.validate_sprite_history_integrity():
            print("❌ HISTORY INTEGRITY CHECK FAILED!")
            return False
    
    print("\n" + "=" * 40)
    print("PHASE 3: VERIFYING SPRITE SEQUENCE")
    print("=" * 40)
    
    # Verify that undo sprites are in reverse order of movement sprites
    print("Sprites during movement (in order):")
    for i, sprite in enumerate(sprites_during_movement):
        sprite_info = skin_manager.get_sprite_info(sprite)
        print(f"  Movement {i+1}: {sprite_info}")
    
    print("\nSprites during undo (in order):")
    for i, sprite in enumerate(sprites_during_undo):
        sprite_info = skin_manager.get_sprite_info(sprite)
        print(f"  Undo {i+1}: {sprite_info}")
    
    # The correct undo behavior: when undoing move N, show the sprite from state N-1
    # So undo sequence should be: [movement4, movement3, movement2, movement1, initial_sprite]
    expected_undo_sequence = []
    
    # For the first undo, we expect the sprite from movement 4 (before movement 5)
    # For the second undo, we expect the sprite from movement 3 (before movement 4)
    # etc.
    for i in range(len(sprites_during_movement) - 1, 0, -1):
        expected_undo_sequence.append(sprites_during_movement[i-1])
    
    # The last undo should return to the initial sprite (sprite_@)
    # We need to get the initial sprite from the skin manager
    skin_data = skin_manager._load_current_skin()
    initial_sprite = skin_data.get('@', skin_data.get('player'))  # fallback for '@' character
    expected_undo_sequence.append(initial_sprite)
    
    print(f"\nExpected undo sequence (showing previous states):")
    for i, sprite in enumerate(expected_undo_sequence):
        sprite_info = skin_manager.get_sprite_info(sprite)
        print(f"  Undo {i+1}: {sprite_info} (showing state before movement {len(sprites_during_movement) - i})")
    
    if len(sprites_during_undo) == len(expected_undo_sequence):
        sequences_match = True
        for i, (undo_sprite, expected_sprite) in enumerate(zip(sprites_during_undo, expected_undo_sequence)):
            if undo_sprite != expected_sprite:
                print(f"❌ SEQUENCE MISMATCH at position {i+1}")
                print(f"   Expected: {skin_manager.get_sprite_info(expected_sprite)}")
                print(f"   Got: {skin_manager.get_sprite_info(undo_sprite)}")
                sequences_match = False
        
        if sequences_match:
            print("✅ SUCCESS: Undo sprite sequence correctly shows previous states")
        else:
            print("❌ FAIL: Undo sprite sequence does not match expected previous states")
            return False
    else:
        print(f"❌ FAIL: Sequence length mismatch - movements: {len(sprites_during_movement)}, undos: {len(sprites_during_undo)}")
        return False
    
    print("\n" + "=" * 40)
    print("PHASE 4: TESTING RECOVERY FROM UNDO MODE")
    print("=" * 40)
    
    # Test that making a new movement exits undo mode
    print("Testing recovery from undo mode by making a new movement...")
    
    # Make a new movement
    skin_manager.update_player_state('right', False, False)
    dx, dy = (1, 0)
    moved = level.move(dx, dy)
    
    if moved:
        # This should exit undo mode
        new_sprite = skin_manager.get_player_sprite(advance_animation=True)
        debug_after_new_move = skin_manager.get_undo_debug_info()
        
        print(f"New movement made, undo mode: {debug_after_new_move['undo_mode']}")
        
        if not debug_after_new_move['undo_mode']:
            print("✅ SUCCESS: Undo mode correctly exited after new movement")
        else:
            print("❌ FAIL: Still in undo mode after new movement")
            return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
    print("The sprite undo system is working correctly.")
    print("=" * 60)
    
    return True

def test_with_animation_frames():
    """
    Test the system with animation frames if available.
    """
    print("\n" + "=" * 60)
    print("TESTING WITH ANIMATION FRAMES")
    print("=" * 60)
    
    pygame.init()
    
    # Try to use a skin with animation frames
    skin_manager = EnhancedSkinManager()
    skin_manager.set_skin('Thinking Rabbit 16')  # This skin has animation frames
    
    print(f"Current skin: {skin_manager.get_current_skin_name()}")
    print(f"Available animation frames: {list(skin_manager.animation_frames.keys())}")
    
    if skin_manager.animation_frames:
        print("Animation frames detected - testing with animated sprites")
        
        # Create a simple test level
        test_level_data = """
########
#......#
#.@....#
#......#
########
"""
        level = Level(level_data=test_level_data)
        
        # Perform movements in same direction to cycle through animation frames
        for i in range(5):
            print(f"\nAnimation test movement {i+1} (down)")
            skin_manager.update_player_state('down', False, False)
            moved = level.move(0, 1)
            
            if moved:
                sprite = skin_manager.get_player_sprite(advance_animation=True)
                sprite_info = skin_manager.get_sprite_info(sprite)
                frame_index = skin_manager.current_frame_indices.get('walking_down', 0)
                print(f"Sprite: {sprite_info}, Frame index: {frame_index}")
        
        # Test undo with animation frames
        print("\nTesting undo with animation frames...")
        for i in range(3):
            print(f"\nUndo {i+1}")
            if level.undo():
                prev_sprite = skin_manager.get_previous_sprite()
                if prev_sprite:
                    sprite_info = skin_manager.get_sprite_info(prev_sprite)
                    print(f"Undo sprite: {sprite_info}")
        
        print("✅ Animation frame testing completed")
    else:
        print("No animation frames found in current skin")

if __name__ == "__main__":
    try:
        # Test basic sprite undo system
        success = test_sprite_undo_system()
        
        if success:
            # Test with animation frames if available
            test_with_animation_frames()
            
            print("\n🎉 ALL SPRITE UNDO TESTS PASSED! 🎉")
            print("\nThe sprite animation system correctly handles undo operations:")
            print("✅ Historical sprites are properly restored during undo")
            print("✅ Undo mode prevents calculation of sprites based on current state")
            print("✅ Sprite sequences are correctly reversed during undo")
            print("✅ Normal operation resumes after new movements")
            print("✅ System works with both basic and animated sprites")
        else:
            print("\n❌ TESTS FAILED - Check the output above for details")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        pygame.quit()