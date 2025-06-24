#!/usr/bin/env python3
"""
PySokoban - Main Entry Point

A Python implementation of the classic Sokoban puzzle game.
This is the main module that serves as the entry point for all versions of the game.
"""

import argparse
import os
import sys

# Add the parent directory to sys.path to allow imports to work in both
# development and when packaged as an executable
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.core.config_manager import get_config_manager
from src.terminal_game import TerminalGame


def run_terminal_game(levels_dir='levels', keyboard_layout=None):
    """Run the terminal version of the Sokoban game."""
    # Use keyboard layout from config if not specified
    if keyboard_layout is None:
        config_manager = get_config_manager()
        keyboard_layout = config_manager.get('game', 'keyboard_layout', 'qwerty')

    game = TerminalGame(levels_dir, keyboard_layout)
    game.start()


def run_gui_game(levels_dir='levels', keyboard_layout=None):
    """Run the GUI version of the Sokoban game."""
    # Use keyboard layout from config if not specified
    if keyboard_layout is None:
        config_manager = get_config_manager()
        keyboard_layout = config_manager.get('game', 'keyboard_layout', 'qwerty')

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
    # Get default keyboard layout from config
    config_manager = get_config_manager()
    default_keyboard = config_manager.get('game', 'keyboard_layout', 'qwerty')

    parser.add_argument('--keyboard', '-k', choices=['qwerty', 'azerty'], default=default_keyboard,
                        help=f'Keyboard layout to use (default: {default_keyboard})')

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
