"""
Game module for the Sokoban game.

This module contains the core game logic for the Sokoban game.
"""

import sys
import time
from abc import ABC, abstractmethod
from src.core.constants import KEY_BINDINGS, QWERTY, AZERTY, DEFAULT_KEYBOARD
from src.renderers import AbstractRenderer


class Game(ABC):
    """
    Main class for the Sokoban game.

    This class is responsible for initializing the game components,
    handling user input, and managing the game loop.
    """

    def __init__(self, level_manager, renderer: AbstractRenderer, keyboard_layout=DEFAULT_KEYBOARD):
        """
        Initialize the Sokoban game.

        Args:
            level_manager: The level manager instance.
            renderer: The renderer instance.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           Defaults to DEFAULT_KEYBOARD.
        """
        self.level_manager = level_manager
        self.renderer = renderer
        self.running = False
        self.keyboard_layout = keyboard_layout

        # Check if keyboard layout is valid
        if self.keyboard_layout not in [QWERTY, AZERTY]:
            print(f"Invalid keyboard layout '{keyboard_layout}'. Using default ({DEFAULT_KEYBOARD}).")
            self.keyboard_layout = DEFAULT_KEYBOARD

        # Check if levels were loaded successfully
        if not self.level_manager.level_files:
            print(f"No level files found in '{level_manager.levels_dir}' directory.")
            print("Please create level files with .txt extension in this directory.")
            sys.exit(1)

    def start(self, skip_welcome=False):
        """
        Start the game.

        Args:
            skip_welcome (bool, optional): Whether to skip the welcome screen.
                                          Defaults to False.
        """
        self.running = True

        if not skip_welcome:
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
            elif key == 'menu':
                # Return to menu
                self.running = False
                return
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

    @abstractmethod
    def _get_input(self):
        """
        Get user input.

        Returns:
            str: The action corresponding to the key pressed.
        """
        ...

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
