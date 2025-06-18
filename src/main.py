#!/usr/bin/env python3
"""
PySokoban - Main Entry Point

A Python implementation of the classic Sokoban puzzle game.
This is the main module that serves as the entry point for all versions of the game.
"""

import argparse
import os
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

        self.levels_dir = levels_dir
        self.keyboard_layout = keyboard_layout
        self.level_manager = LevelManager(levels_dir)
        self.renderer = TerminalRenderer()
        self.game = Game(self.level_manager, self.renderer, keyboard_layout)
        self.game._get_input = self._get_input
        self.running = True
        self.current_state = 'menu'  # 'menu', 'playing', 'category_select', 'level_select'
        self.selected_category = None
        self.categories = []
        self._load_categories()

    def _load_categories(self):
        """Load level categories from the levels directory."""
        self.categories = []

        # Check for subdirectories first
        if os.path.exists(self.levels_dir):
            subdirs = [
                d for d in os.listdir(self.levels_dir)
                if os.path.isdir(os.path.join(self.levels_dir, d))
            ]

            if subdirs:
                # Use subdirectories as categories
                for subdir in sorted(subdirs):
                    subdir_path = os.path.join(self.levels_dir, subdir)
                    files_in_subdir = [
                        os.path.join(subdir_path, f) for f in os.listdir(subdir_path)
                        if f.endswith('.txt') and os.path.isfile(os.path.join(subdir_path, f))
                    ]

                    if files_in_subdir:
                        # Create display name based on folder name
                        display_name = subdir.replace('_', ' ').replace('-', ' ').title()
                        self.categories.append({
                            'name': subdir,
                            'display_name': display_name,
                            'levels': files_in_subdir
                        })

            # If no subdirectories, use all level files
            if not self.categories:
                all_files = [
                    os.path.join(self.levels_dir, f) for f in os.listdir(self.levels_dir)
                    if f.endswith('.txt') and os.path.isfile(os.path.join(self.levels_dir, f))
                ]

                if all_files:
                    self.categories.append({
                        'name': 'all',
                        'display_name': 'All Levels',
                        'levels': all_files
                    })

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

                    # Handle numeric inputs for menu selection
                    if event.name.isdigit():
                        return event.name

                    # Handle 'm' key for menu
                    if event.name == 'm':
                        return 'menu'
            except Exception as e:
                print(f"Input error: {e}")
                return None

    def _display_main_menu(self):
        """Display the main menu."""
        self.renderer.clear_screen()
        self.renderer.render_welcome_screen()
        print("\nMENU PRINCIPAL")
        print("==============")
        print("1. Jouer")
        print("2. Sélectionner un niveau")
        print("3. Aide")
        print("4. Quitter")
        print("\nEntrez votre choix (1-4): ")

    def _display_category_menu(self):
        """Display the category selection menu."""
        self.renderer.clear_screen()
        print("SÉLECTION DE CATÉGORIE")
        print("=====================")

        if not self.categories:
            print("Aucune catégorie trouvée.")
            print("\nAppuyez sur une touche pour revenir au menu principal...")
            return

        for i, category in enumerate(self.categories):
            print(f"{i+1}. {category['display_name']} ({len(category['levels'])} niveaux)")

        print("\n0. Retour au menu principal")
        print("\nEntrez votre choix (0-{}): ".format(len(self.categories)))

    def _display_level_menu(self):
        """Display the level selection menu."""
        self.renderer.clear_screen()
        print(f"SÉLECTION DE NIVEAU - {self.selected_category['display_name']}")
        print("=" * (24 + len(self.selected_category['display_name'])))

        levels = self.selected_category['levels']
        if not levels:
            print("Aucun niveau trouvé dans cette catégorie.")
            print("\nAppuyez sur une touche pour revenir à la sélection de catégorie...")
            return

        for i, level_path in enumerate(levels):
            level_name = os.path.splitext(os.path.basename(level_path))[0]
            level_name = level_name.replace('_', ' ').title()
            print(f"{i+1}. {level_name}")

        print("\n0. Retour à la sélection de catégorie")
        print("\nEntrez votre choix (0-{}): ".format(len(levels)))

    def _handle_main_menu(self):
        """Handle user input in the main menu."""
        action = self._get_input()

        if action == '1':  # Play
            # Start the game with the first level
            if self.level_manager.level_files:
                self.level_manager.load_level(0)
                self.current_state = 'playing'
            else:
                self.renderer.clear_screen()
                print("Aucun niveau trouvé. Veuillez vérifier le répertoire des niveaux.")
                print("\nAppuyez sur une touche pour continuer...")
                self._get_input()

        elif action == '2':  # Select level
            self.current_state = 'category_select'

        elif action == '3':  # Help
            self.renderer.clear_screen()
            self.renderer.render_help()
            print("\nAppuyez sur une touche pour revenir au menu principal...")
            self._get_input()

        elif action == '4' or action == 'quit':  # Quit
            self.running = False

    def _handle_category_menu(self):
        """Handle user input in the category selection menu."""
        action = self._get_input()

        if action == '0' or action == 'quit':
            self.current_state = 'menu'
            return

        try:
            category_index = int(action) - 1
            if 0 <= category_index < len(self.categories):
                self.selected_category = self.categories[category_index]
                self.current_state = 'level_select'
            else:
                print("Choix invalide. Veuillez réessayer.")
                import time
                time.sleep(1)
        except ValueError:
            pass

    def _handle_level_menu(self):
        """Handle user input in the level selection menu."""
        action = self._get_input()

        if action == '0' or action == 'quit':
            self.current_state = 'category_select'
            return

        try:
            level_index = int(action) - 1
            if 0 <= level_index < len(self.selected_category['levels']):
                level_path = self.selected_category['levels'][level_index]

                # Find the index of this level in the level manager's list
                if level_path in self.level_manager.level_files:
                    level_manager_index = self.level_manager.level_files.index(level_path)
                    self.level_manager.load_level(level_manager_index)
                else:
                    # If not found, try to load it directly
                    from src.core.level import Level
                    self.level_manager.current_level = Level(level_file=level_path)
                    self.level_manager.current_level_index = -1  # Custom level

                self.current_state = 'playing'
            else:
                print("Choix invalide. Veuillez réessayer.")
                import time
                time.sleep(1)
        except ValueError:
            pass

    def _handle_playing(self):
        """Handle the game playing state."""
        # Start the game, skipping the welcome screen when coming from the menu
        self.game.start(skip_welcome=True)

        # After the game ends, return to the main menu
        self.current_state = 'menu'

    def start(self):
        """Start the terminal version of the game."""
        while self.running:
            if self.current_state == 'menu':
                self._display_main_menu()
                self._handle_main_menu()
            elif self.current_state == 'category_select':
                self._display_category_menu()
                self._handle_category_menu()
            elif self.current_state == 'level_select':
                self._display_level_menu()
                self._handle_level_menu()
            elif self.current_state == 'playing':
                self._handle_playing()


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
