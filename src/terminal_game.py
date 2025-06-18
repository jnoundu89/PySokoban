"""
Terminal Game module for the Sokoban game.

This module provides the terminal-based version of the Sokoban game.
"""

import os
import keyboard
from src.level_management.level_manager import LevelManager
from src.renderers.terminal_renderer import TerminalRenderer
from src.core.game import Game
from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.constants import KEY_BINDINGS
from src.core.config_manager import get_config_manager


class TerminalGame:
    """
    Terminal version of the Sokoban game.

    This class extends the base Game class with terminal-specific functionality.
    """

    def __init__(self, levels_dir='levels', keyboard_layout=None):
        """
        Initialize the terminal version of the Sokoban game.

        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           If None, uses the value from config.
        """
        # Get configuration
        self.config_manager = get_config_manager()
        
        # Use keyboard layout from config if not specified
        if keyboard_layout is None:
            keyboard_layout = self.config_manager.get('game', 'keyboard_layout', 'qwerty')
        
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
        # Initialize pagination state
        self.category_page = 0
        self.level_page = 0
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

                        # Count total levels including parsed levels from text files
                        total_levels = 0
                        parsed_levels = 0

                        for file_path in files_in_subdir:
                            try:
                                # Try to parse as a collection
                                collection = LevelCollectionParser.parse_file(file_path)
                                level_count = collection.get_level_count()
                                if level_count > 1:
                                    total_levels += level_count
                                    parsed_levels += level_count
                                else:
                                    total_levels += 1
                            except Exception:
                                # If parsing fails, count as a single level
                                total_levels += 1

                        self.categories.append({
                            'name': subdir,
                            'display_name': display_name,
                            'levels': files_in_subdir,
                            'total_levels': total_levels,
                            'parsed_levels': parsed_levels
                        })

            # If no subdirectories, use all level files
            if not self.categories:
                all_files = [
                    os.path.join(self.levels_dir, f) for f in os.listdir(self.levels_dir)
                    if f.endswith('.txt') and os.path.isfile(os.path.join(self.levels_dir, f))
                ]

                if all_files:
                    # Count total levels including parsed levels from text files
                    total_levels = 0
                    parsed_levels = 0

                    for file_path in all_files:
                        try:
                            # Try to parse as a collection
                            collection = LevelCollectionParser.parse_file(file_path)
                            level_count = collection.get_level_count()
                            if level_count > 1:
                                total_levels += level_count
                                parsed_levels += level_count
                            else:
                                total_levels += 1
                        except Exception:
                            # If parsing fails, count as a single level
                            total_levels += 1

                    self.categories.append({
                        'name': 'all',
                        'display_name': 'All Levels',
                        'levels': all_files,
                        'total_levels': total_levels,
                        'parsed_levels': parsed_levels
                    })

    def _get_input(self):
        """
        Get user input from the keyboard.

        Returns:
            str: The action corresponding to the key pressed.
        """
        # Get custom keybindings from config
        keybindings = self.config_manager.get_keybindings()

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

                    # Check custom keybindings from config
                    for action_name, key in keybindings.items():
                        if event.name == key:
                            return action_name

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
        print("SÉLECTION DE COLLECTION")
        print("=====================")

        if not self.categories:
            print("Aucune collection trouvée.")
            print("\nAppuyez sur une touche pour revenir au menu principal...")
            return

        # Pagination for categories
        if not hasattr(self, 'category_page'):
            self.category_page = 0

        items_per_page = 9
        start_idx = self.category_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(self.categories))
        total_pages = (len(self.categories) + items_per_page - 1) // items_per_page

        # Display page information
        if total_pages > 1:
            print(f"Page {self.category_page + 1}/{total_pages}")
            print()

        # Display categories for current page
        for i in range(start_idx, end_idx):
            category = self.categories[i]
            display_num = i - start_idx + 1

            # Display total levels and parsed levels if available
            if 'total_levels' in category:
                if category['parsed_levels'] > 0:
                    print(f"{display_num}. {category['display_name']} ({category['total_levels']} niveaux, dont {category['parsed_levels']} niveaux parsés)")
                else:
                    print(f"{display_num}. {category['display_name']} ({category['total_levels']} niveaux)")
            else:
                print(f"{display_num}. {category['display_name']} ({len(category['levels'])} niveaux)")

        print()
        # Navigation options
        if total_pages > 1:
            if self.category_page > 0:
                print("P. Page précédente")
            if self.category_page < total_pages - 1:
                print("N. Page suivante")

        print("0. Retour au menu principal")
        print("\nEntrez votre choix: ")

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

        # Pagination for levels
        if not hasattr(self, 'level_page'):
            self.level_page = 0

        items_per_page = 9
        start_idx = self.level_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(levels))
        total_pages = (len(levels) + items_per_page - 1) // items_per_page

        # Display page information
        if total_pages > 1:
            print(f"Page {self.level_page + 1}/{total_pages}")
            print()

        # Display levels for current page
        for i in range(start_idx, end_idx):
            level_path = levels[i]
            level_name = os.path.splitext(os.path.basename(level_path))[0]
            level_name = level_name.replace('_', ' ').title()
            display_num = i - start_idx + 1
            print(f"{display_num}. {level_name}")

        print()
        # Navigation options
        if total_pages > 1:
            if self.level_page > 0:
                print("P. Page précédente")
            if self.level_page < total_pages - 1:
                print("N. Page suivante")

        print("0. Retour à la sélection de catégorie")
        print("\nEntrez votre choix: ")

    def _handle_main_menu(self):
        """Handle user input in the main menu."""
        action = self._get_input()

        # Reset pagination state when entering the main menu
        if hasattr(self, 'category_page'):
            self.category_page = 0
        if hasattr(self, 'level_page'):
            self.level_page = 0

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

        # Handle pagination
        if action.lower() == 'p' and hasattr(self, 'category_page') and self.category_page > 0:
            self.category_page -= 1
            return
        elif action.lower() == 'n' and hasattr(self, 'category_page'):
            items_per_page = 9
            total_pages = (len(self.categories) + items_per_page - 1) // items_per_page
            if self.category_page < total_pages - 1:
                self.category_page += 1
            return

        try:
            # Calculate the actual index based on the current page
            items_per_page = 9
            start_idx = self.category_page * items_per_page if hasattr(self, 'category_page') else 0

            display_index = int(action) - 1
            category_index = start_idx + display_index

            if 0 <= display_index < items_per_page and category_index < len(self.categories):
                self.selected_category = self.categories[category_index]
                self.current_state = 'level_select'
                # Reset level pagination when changing categories
                if hasattr(self, 'level_page'):
                    self.level_page = 0
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

        # Handle pagination
        if action.lower() == 'p' and hasattr(self, 'level_page') and self.level_page > 0:
            self.level_page -= 1
            return
        elif action.lower() == 'n' and hasattr(self, 'level_page'):
            items_per_page = 9
            levels = self.selected_category['levels']
            total_pages = (len(levels) + items_per_page - 1) // items_per_page
            if self.level_page < total_pages - 1:
                self.level_page += 1
            return

        try:
            # Calculate the actual index based on the current page
            items_per_page = 9
            start_idx = self.level_page * items_per_page if hasattr(self, 'level_page') else 0

            display_index = int(action) - 1
            level_index = start_idx + display_index

            if 0 <= display_index < items_per_page and level_index < len(self.selected_category['levels']):
                level_path = self.selected_category['levels'][level_index]

                # Show level preview instead of immediately starting the game
                self._display_level_preview(level_path, level_index)
            else:
                print("Choix invalide. Veuillez réessayer.")
                import time
                time.sleep(1)
        except ValueError:
            pass

    def _display_level_preview(self, level_path, level_index):
        """
        Display a preview of the selected level and options to play or go back.
        If the level is a collection, ask for a level number first.

        Args:
            level_path (str): Path to the level file
            level_index (int): Index of the level in the category
        """
        from src.core.level import Level

        # Check if this is a collection file with multiple levels
        try:
            collection = LevelCollectionParser.parse_file(level_path)
            level_count = collection.get_level_count()

            if level_count > 1:
                # This is a collection with multiple levels
                self._handle_collection_preview(level_path, collection)
                return
        except Exception:
            # Not a collection or error parsing, treat as a single level
            pass

        # Handle single level file
        self.renderer.clear_screen()

        try:
            level = Level(level_file=level_path)

            # Display level information
            level_name = os.path.splitext(os.path.basename(level_path))[0]
            level_name = level_name.replace('_', ' ').title()

            print(f"APERÇU DU NIVEAU - {level_name}")
            print("=" * (18 + len(level_name)))
            print()

            # Display level metadata if available
            if level.title:
                print(f"Titre: {level.title}")
            if level.author:
                print(f"Auteur: {level.author}")
            if level.description:
                print(f"Description: {level.description}")

            print()
            print(f"Dimensions: {level.width}x{level.height}")
            print(f"Boîtes: {len(level.boxes)}")
            print(f"Cibles: {len(level.targets)}")
            print()

            # Display the level preview
            print("Aperçu du niveau:")
            print()

            # Get the level representation with coordinates
            level_str = level.get_state_string(show_fess_coordinates=True)
            print(level_str)

            print()
            print("Options:")
            print("1. Jouer à ce niveau")
            print("0. Retour à la liste des niveaux")
            print()
            print("Entrez votre choix: ")

            # Handle user input
            while True:
                # Use the new method for multi-digit input
                action = self._get_numeric_input()

                if action == '1':
                    # Load the level in the level manager
                    if level_path in self.level_manager.level_files:
                        level_manager_index = self.level_manager.level_files.index(level_path)
                        self.level_manager.load_level(level_manager_index)
                    else:
                        # If not found, use the level we already loaded
                        self.level_manager.current_level = level
                        self.level_manager.current_level_index = -1  # Custom level

                    self.current_state = 'playing'
                    return
                elif action == '0' or action == 'quit':
                    # Return to level selection
                    return
        except Exception as e:
            print(f"Erreur lors du chargement du niveau: {e}")
            print("\nAppuyez sur une touche pour revenir à la liste des niveaux...")
            self._get_input()

    def _get_numeric_input(self):
        """
        Get a numeric input from the user, allowing for multi-digit numbers.

        Returns:
            str: The complete numeric input as a string
        """
        # Display a cursor to indicate input mode
        print("> ", end="", flush=True)

        input_buffer = ""
        while True:
            event = keyboard.read_event(suppress=True)

            # Only process key down events
            if event.event_type == keyboard.KEY_DOWN:
                # Handle Enter key to confirm input
                if event.name == 'enter':
                    print()  # Move to next line after input
                    return input_buffer

                # Handle backspace to delete last character
                elif event.name == 'backspace' and input_buffer:
                    input_buffer = input_buffer[:-1]
                    # Clear the current line and redisplay
                    print("\r> " + input_buffer + " ", end="\r", flush=True)
                    print("> " + input_buffer, end="", flush=True)

                # Handle escape key to cancel
                elif event.name == 'esc':
                    print()  # Move to next line
                    return '0'  # Return '0' to indicate cancellation

                # Handle numeric inputs
                elif event.name.isdigit():
                    input_buffer += event.name
                    print(event.name, end="", flush=True)

                # Handle 'q' as quit
                elif event.name == 'q':
                    print()  # Move to next line
                    return 'quit'

    def _handle_collection_preview(self, level_path, collection):
        """
        Handle preview and selection of a level from a collection.

        Args:
            level_path (str): Path to the collection file
            collection: The parsed LevelCollection object
        """
        self.renderer.clear_screen()

        # Display collection information
        collection_name = os.path.splitext(os.path.basename(level_path))[0]
        collection_name = collection_name.replace('_', ' ').title()

        print(f"COLLECTION - {collection_name}")
        print("=" * (12 + len(collection_name)))
        print()

        # Display collection metadata
        if collection.title:
            print(f"Titre: {collection.title}")
        if collection.author:
            print(f"Auteur: {collection.author}")
        if collection.description:
            print(f"Description: {collection.description}")

        print()
        print(f"Cette collection contient {collection.get_level_count()} niveaux.")
        print("Veuillez saisir le numéro du niveau que vous souhaitez jouer (1-{0}):".format(collection.get_level_count()))
        print("0. Retour à la liste des niveaux")
        print()

        while True:
            # Use the new method for multi-digit input
            action = self._get_numeric_input()

            if action == '0' or action == 'quit':
                return

            try:
                level_num = int(action)
                if 1 <= level_num <= collection.get_level_count():
                    # Valid level number, show preview
                    self._display_collection_level_preview(level_path, collection, level_num - 1)
                    return
                else:
                    print(f"Numéro de niveau invalide. Veuillez saisir un nombre entre 1 et {collection.get_level_count()}.")
            except ValueError:
                print("Veuillez saisir un nombre valide.")

    def _display_collection_level_preview(self, level_path, collection, level_index):
        """
        Display a preview of a specific level from a collection.

        Args:
            level_path (str): Path to the collection file
            collection: The parsed LevelCollection object
            level_index (int): Index of the level in the collection (0-based)
        """
        self.renderer.clear_screen()

        try:
            # Get the level from the collection
            level_title, level = collection.get_level(level_index)

            # Set metadata from collection
            level.title = level_title
            level.description = collection.description
            level.author = collection.author

            print(f"APERÇU DU NIVEAU - {level_title}")
            print("=" * (18 + len(level_title)))
            print()

            # Display collection info
            collection_name = os.path.splitext(os.path.basename(level_path))[0]
            collection_name = collection_name.replace('_', ' ').title()
            print(f"Collection: {collection_name}")
            print(f"Niveau {level_index + 1} sur {collection.get_level_count()}")
            print()

            # Display level metadata
            if level.title:
                print(f"Titre: {level.title}")
            if level.author:
                print(f"Auteur: {level.author}")
            if level.description:
                print(f"Description: {level.description}")

            print()
            print(f"Dimensions: {level.width}x{level.height}")
            print(f"Boîtes: {len(level.boxes)}")
            print(f"Cibles: {len(level.targets)}")
            print()

            # Display the level preview
            print("Aperçu du niveau:")
            print()

            # Get the level representation with coordinates
            level_str = level.get_state_string(show_fess_coordinates=True)
            print(level_str)

            print()
            print("Options:")
            print("1. Jouer à ce niveau")
            print("0. Retour à la sélection de niveau")
            print()
            print("Entrez votre choix: ")

            # Handle user input
            while True:
                # Use the new method for multi-digit input
                action = self._get_numeric_input()

                if action == '1':
                    # Set up the level in the level manager
                    if level_path in self.level_manager.level_collections:
                        # Use the level manager's collection handling
                        self.level_manager.current_collection = collection
                        self.level_manager.current_collection_index = level_index
                        self.level_manager.current_level = level
                        self.level_manager.current_level_index = -1  # Custom level
                    else:
                        # Just set the level directly
                        self.level_manager.current_level = level
                        self.level_manager.current_level_index = -1  # Custom level

                    self.current_state = 'playing'
                    return
                elif action == '0' or action == 'quit':
                    # Return to collection level selection
                    self._handle_collection_preview(level_path, collection)
                    return
        except Exception as e:
            print(f"Erreur lors du chargement du niveau: {e}")
            print("\nAppuyez sur une touche pour revenir à la sélection de niveau...")
            self._get_input()
            return

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