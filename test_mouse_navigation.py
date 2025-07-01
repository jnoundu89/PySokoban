#!/usr/bin/env python3
"""
Test script for the advanced mouse navigation system in Sokoban.

This script demonstrates the new mouse navigation features:
- Dynamic white guideline from player to cursor
- Intelligent pathfinding with optimal route calculation
- Left-click navigation along calculated path
- Automatic obstacle handling
- Drag-and-drop box manipulation system
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui_main import GUIGame


def main():
    """
    Run the Sokoban game with advanced mouse navigation.
    """
    print("🎮 Starting Sokoban with Advanced Mouse Navigation System")
    print("=" * 60)
    print()
    print("🖱️  MOUSE NAVIGATION FEATURES:")
    print("   • Dynamic white guideline from player to cursor")
    print("   • Intelligent pathfinding with optimal route calculation")
    print("   • Left-click navigation along calculated path")
    print("   • Automatic obstacle handling (stops before unmovable boxes)")
    print("   • Drag-and-drop box manipulation system")
    print()
    print("🎯 HOW TO USE:")
    print("   1. Move your mouse around the level to see the white guideline")
    print("   2. Left-click anywhere to make the player navigate there automatically")
    print("   3. Click and drag boxes adjacent to the player to move them")
    print("   4. The system respects all game rules and collision detection")
    print()
    print("⌨️  KEYBOARD CONTROLS (still available):")
    print("   • Arrow keys or WASD: Manual movement")
    print("   • R: Reset level")
    print("   • U: Undo move")
    print("   • N: Next level")
    print("   • P: Previous level")
    print("   • S: AI solver")
    print("   • H: Help")
    print("   • G: Toggle grid")
    print("   • Q: Quit")
    print("   • F11: Toggle fullscreen")
    print()
    print("🚀 Starting game...")
    print("=" * 60)
    
    try:
        # Create and start the game with mouse navigation
        game = GUIGame('src/levels')
        game.start()
    except KeyboardInterrupt:
        print("\n🛑 Game terminated by user.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()