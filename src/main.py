#!/usr/bin/env python3
"""
PySokoban - Main Entry Point

A Python implementation of the classic Sokoban puzzle game.
This is the main module that serves as the entry point for all versions of the game.
"""

import argparse
import sys

from src.core.constants import DEFAULT_KEYBOARD


class TerminalGame:
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
        from src.level_management.level_manager import LevelManager
        from src.renderers.terminal_renderer import TerminalRenderer
        from src.core.game import Game

        level_manager = LevelManager(levels_dir)
        renderer = TerminalRenderer()
        self.game = Game(level_manager, renderer, keyboard_layout)
        self.game._get_input = self._get_input

    def _get_input(self):
        """
        Get user input from the keyboard.

        Returns:
            str: The action corresponding to the key pressed.
        """
        import keyboard
        from src.core.constants import KEY_BINDINGS

        while True:
            try:
                # Wait for a key press
                event = keyboard.read_event(suppress=True)

                # Only process key down events
                if event.event_type == keyboard.KEY_DOWN:
                    # Try to find the key in KEY_BINDINGS for the current keyboard layout
                    action = KEY_BINDINGS[self.game.keyboard_layout].get(event.name)

                    if action:
                        return action
            except Exception as e:
                print(f"Input error: {e}")
                return None

    def start(self):
        """Start the terminal version of the game."""
        self.game.start()


def run_terminal_game(levels_dir='levels', keyboard_layout=DEFAULT_KEYBOARD):
    """Run the terminal version of the Sokoban game."""
    game = TerminalGame(levels_dir, keyboard_layout)
    game.start()


def run_gui_game(levels_dir='levels', keyboard_layout=DEFAULT_KEYBOARD):
    """Run the GUI version of the Sokoban game."""
    from src.gui_main import GUIGame
    game = GUIGame(levels_dir, keyboard_layout)
    game.start()


def run_enhanced_game(levels_dir='levels'):
    """Run the enhanced version of the Sokoban game with menu, editor, etc."""
    from src.enhanced_main import EnhancedSokoban
    game = EnhancedSokoban(levels_dir)
    game.start()


def run_level_editor(levels_dir='levels'):
    """Run the level editor."""
    from src.editor_main import main as editor_main
    editor_main()


def main():
    """
    Main function to run the appropriate version of the Sokoban game.
    """
    parser = argparse.ArgumentParser(
        description='PySokoban - A Python implementation of the classic Sokoban puzzle game.')
    parser.add_argument('--mode', '-m', choices=['terminal', 'gui', 'enhanced', 'editor'], default='enhanced',
                        help='Game mode to run (default: enhanced)')
    parser.add_argument('--levels', '-l', default='levels',
                        help='Directory containing level files (default: levels)')
    parser.add_argument('--keyboard', '-k', choices=['qwerty', 'azerty'], default=DEFAULT_KEYBOARD,
                        help=f'Keyboard layout to use (default: {DEFAULT_KEYBOARD})')

    args = parser.parse_args()

    # Run the appropriate version of the game
    if args.mode == 'terminal':
        run_terminal_game(args.levels, args.keyboard)
    elif args.mode == 'gui':
        run_gui_game(args.levels, args.keyboard)
    elif args.mode == 'editor':
        run_level_editor(args.levels)
    else:  # enhanced is the default
        run_enhanced_game(args.levels)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
