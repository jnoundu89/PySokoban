#!/usr/bin/env python3
"""
Game launcher that properly sets up the Python path and levels directory.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run the main game
if __name__ == "__main__":
    from gui_main import GUIGame
    from core.constants import DEFAULT_KEYBOARD
    
    # Set the correct levels directory
    levels_dir = os.path.join('src', 'levels')
    
    # Create and start the game with correct levels path
    game = GUIGame(levels_dir, DEFAULT_KEYBOARD)
    game.start()