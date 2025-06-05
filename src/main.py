#!/usr/bin/env python3
"""
Sokoban Game - Terminal Version

A Python implementation of the classic Sokoban puzzle game.
This is the main module that starts the terminal version of the game.
"""

import os
import sys
import keyboard
import time
from src.core.constants import KEY_BINDINGS, QWERTY, AZERTY, DEFAULT_KEYBOARD
from src.core.level import Level
from src.level_management.level_manager import LevelManager
from src.renderers.terminal_renderer import TerminalRenderer
from src.core.game import Game


class TerminalGame(Game):
    """
    Terminal version of the Sokoban game.
    
    This class extends the base Game class with terminal-specific functionality.
    """
    
    def __init__(self, levels_dir='levels', keyboard_layout=DEFAULT_KEYBOARD):
        """
        Initialize the terminal version of the Sokoban game.
        
        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           Defaults to DEFAULT_KEYBOARD.
        """
        level_manager = LevelManager(levels_dir)
        renderer = TerminalRenderer()
        super().__init__(level_manager, renderer, keyboard_layout)
    
    def _get_input(self):
        """
        Get user input from the keyboard.
        
        Returns:
            str: The action corresponding to the key pressed.
        """
        while True:
            try:
                # Wait for a key press
                event = keyboard.read_event(suppress=True)
                
                # Only process key down events
                if event.event_type == keyboard.KEY_DOWN:
                    # Try to find the key in KEY_BINDINGS for the current keyboard layout
                    action = KEY_BINDINGS[self.keyboard_layout].get(event.name)
                    
                    if action:
                        return action
            except Exception as e:
                print(f"Input error: {e}")
                return None


def main():
    """
    Main function to run the terminal version of the Sokoban game.
    """
    # Parse command line arguments
    levels_dir = 'levels'
    keyboard_layout = DEFAULT_KEYBOARD
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--levels' or sys.argv[i] == '-l':
            if i + 1 < len(sys.argv):
                levels_dir = sys.argv[i + 1]
                i += 2
            else:
                print("Error: Missing argument for --levels")
                sys.exit(1)
        elif sys.argv[i] == '--keyboard' or sys.argv[i] == '-k':
            if i + 1 < len(sys.argv):
                keyboard_layout = sys.argv[i + 1].lower()
                i += 2
            else:
                print("Error: Missing argument for --keyboard")
                sys.exit(1)
        else:
            # For backwards compatibility, treat first argument as levels_dir
            if i == 1:
                levels_dir = sys.argv[i]
            i += 1
    
    # Create and start the game
    game = TerminalGame(levels_dir, keyboard_layout)
    game.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)