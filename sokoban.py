#!/usr/bin/env python3
"""
Sokoban Game

A Python implementation of the classic Sokoban puzzle game.
This is the main module that starts the game and handles user input.
"""

import os
import sys
import keyboard
import time
from constants import KEY_BINDINGS, QWERTY, AZERTY, DEFAULT_KEYBOARD
from level import Level
from level_manager import LevelManager
from terminal_renderer import TerminalRenderer


class SokobanGame:
    """
    Main class for the Sokoban game.
    
    This class is responsible for initializing the game components,
    handling user input, and managing the game loop.
    """
    
    def __init__(self, levels_dir='levels', keyboard_layout=DEFAULT_KEYBOARD):
        """
        Initialize the Sokoban game.
        
        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           Defaults to DEFAULT_KEYBOARD.
        """
        self.level_manager = LevelManager(levels_dir)
        self.renderer = TerminalRenderer()
        self.running = False
        self.keyboard_layout = keyboard_layout
        
        # Check if keyboard layout is valid
        if self.keyboard_layout not in [QWERTY, AZERTY]:
            print(f"Invalid keyboard layout '{keyboard_layout}'. Using default ({DEFAULT_KEYBOARD}).")
            self.keyboard_layout = DEFAULT_KEYBOARD
        
        # Check if levels were loaded successfully
        if not self.level_manager.level_files:
            print(f"No level files found in '{levels_dir}' directory.")
            print("Please create level files with .txt extension in this directory.")
            sys.exit(1)
    
    def start(self):
        """
        Start the game.
        """
        self.running = True
        self.renderer.render_welcome_screen()
        input("Press Enter to start...")
        
        self.game_loop()
    
    def game_loop(self):
        """
        Main game loop.
        """
        while self.running:
            # Render the current level
            self.renderer.render_level(self.level_manager.current_level, self.level_manager)
            
            # Get user input
            key = self._get_input()
            
            # Process input
            if key == 'quit':
                self._quit_game()
            elif key == 'reset':
                self.level_manager.reset_current_level()
            elif key == 'next':
                if self.level_manager.current_level_completed():
                    self._next_level()
                else:
                    print("\nComplete this level first!")
                    time.sleep(1)
            elif key == 'previous':
                self._prev_level()
            elif key == 'undo':
                self.level_manager.current_level.undo()
            elif key == 'help':
                self.renderer.render_help()
                input("\nPress Enter to continue...")
            elif key in ['up', 'down', 'left', 'right']:
                self._handle_movement(key)
            
            # Check if level is completed
            if self.level_manager.current_level_completed():
                self.renderer.render_level(self.level_manager.current_level, self.level_manager)
                time.sleep(1)
                
                # If there's a next level, wait for user input
                if self.level_manager.has_next_level():
                    input("\nPress Enter for the next level...")
                    self._next_level()
                else:
                    # Game completed!
                    self.renderer.render_game_over_screen(completed_all=True)
                    input()
                    self._quit_game()
    
    def _get_input(self):
        """
        Get user input.
        
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
    
    def _handle_movement(self, direction):
        """
        Handle player movement.
        
        Args:
            direction (str): Direction to move ('up', 'down', 'left', 'right').
        """
        dx, dy = 0, 0
        
        if direction == 'up':
            dy = -1
        elif direction == 'down':
            dy = 1
        elif direction == 'left':
            dx = -1
        elif direction == 'right':
            dx = 1
        
        self.level_manager.current_level.move(dx, dy)
    
    def _next_level(self):
        """
        Load the next level.
        """
        if not self.level_manager.next_level():
            print("No more levels!")
            time.sleep(1)
            self.renderer.render_game_over_screen(completed_all=True)
            input()
            self._quit_game()
    
    def _prev_level(self):
        """
        Load the previous level.
        """
        if not self.level_manager.prev_level():
            print("Already at the first level!")
            time.sleep(1)
    
    def _quit_game(self):
        """
        Quit the game.
        """
        self.running = False
        self.renderer.clear_screen()
        print("Thanks for playing Sokoban!")
        sys.exit(0)


def main():
    """
    Main function to run the Sokoban game.
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
    game = SokobanGame(levels_dir, keyboard_layout)
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