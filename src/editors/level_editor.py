#!/usr/bin/env python3
"""
Level Editor for the Sokoban game.

This module provides functionality for creating and editing Sokoban levels.
It allows users to design new levels or modify existing ones.
"""

import os
import sys
import keyboard
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET
from src.core.constants import KEY_BINDINGS, QWERTY, AZERTY, DEFAULT_KEYBOARD
from src.core.level import Level
from src.level_management.level_manager import LevelManager
from src.renderers.terminal_renderer import TerminalRenderer


class LevelEditor:
    """
    Class for creating and editing Sokoban levels.

    This class provides functionality for designing new levels or
    modifying existing ones through a terminal interface.
    """

    def __init__(self, levels_dir='levels', keyboard_layout=DEFAULT_KEYBOARD):
        """
        Initialize the level editor.

        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           Defaults to DEFAULT_KEYBOARD.
        """
        self.levels_dir = levels_dir
        self.renderer = TerminalRenderer()
        self.level_manager = LevelManager(levels_dir)
        self.keyboard_layout = keyboard_layout

        # Check if keyboard layout is valid
        if self.keyboard_layout not in [QWERTY, AZERTY]:
            print(f"Invalid keyboard layout '{keyboard_layout}'. Using default ({DEFAULT_KEYBOARD}).")
            self.keyboard_layout = DEFAULT_KEYBOARD

        # Check if levels directory exists, create it if not
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)

        # Current level being edited (either new or existing)
        self.current_level = None

        # Editor state
        self.cursor_pos = (0, 0)
        self.current_element = WALL
        self.running = False
        self.unsaved_changes = False

    def start(self):
        """
        Start the level editor.
        """
        self.running = True
        self._show_welcome_screen()
        self._main_loop()

    def _show_welcome_screen(self):
        """
        Show the welcome screen with options to create a new level or edit an existing one.
        """
        self.renderer.clear_screen()
        print("=== Sokoban Level Editor ===\n")
        print("1. Create new level")
        print("2. Edit existing level")
        print("3. Generate random level")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == '1':
            self._create_new_level()
        elif choice == '2':
            self._select_level_to_edit()
        elif choice == '3':
            self._generate_random_level()
        else:
            self.running = False

    def _create_new_level(self):
        """
        Create a new level from scratch.
        """
        self.renderer.clear_screen()
        print("=== Create New Level ===\n")

        # Get level dimensions
        try:
            width = int(input("Enter level width (5-20): "))
            height = int(input("Enter level height (5-20): "))

            # Validate dimensions
            if width < 5 or width > 20 or height < 5 or height > 20:
                print("Invalid dimensions. Width and height must be between 5 and 20.")
                input("Press Enter to continue...")
                self._show_welcome_screen()
                return
        except ValueError:
            print("Invalid input. Please enter numbers only.")
            input("Press Enter to continue...")
            self._show_welcome_screen()
            return

        # Create an empty level with walls around the perimeter
        level_data = []
        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    row.append(WALL)
                else:
                    row.append(FLOOR)
            level_data.append(''.join(row))

        level_string = '\n'.join(level_data)
        self.current_level = Level(level_data=level_string)
        self.cursor_pos = (1, 1)
        self.unsaved_changes = True

        # Show help before starting
        self._show_editor_help()

    def _select_level_to_edit(self):
        """
        Select an existing level to edit.
        """
        self.renderer.clear_screen()
        print("=== Edit Existing Level ===\n")

        # List available levels
        level_files = self.level_manager.level_files
        if not level_files:
            print("No levels found in the levels directory.")
            input("Press Enter to continue...")
            self._show_welcome_screen()
            return

        print("Available levels:")
        for i, level_file in enumerate(level_files):
            print(f"{i+1}. {os.path.basename(level_file)}")

        print(f"{len(level_files)+1}. Back to main menu")

        # Get user choice
        try:
            choice = int(input(f"\nEnter your choice (1-{len(level_files)+1}): "))

            if choice < 1 or choice > len(level_files) + 1:
                print("Invalid choice.")
                input("Press Enter to continue...")
                self._select_level_to_edit()
                return

            if choice == len(level_files) + 1:
                self._show_welcome_screen()
                return

            # Load the selected level
            level_file = level_files[choice - 1]
            self.current_level = Level(level_file=level_file)
            self.cursor_pos = (1, 1)
            self.unsaved_changes = False

            # Show help before starting
            self._show_editor_help()
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("Press Enter to continue...")
            self._select_level_to_edit()
            return

    def _show_editor_help(self):
        """
        Show editor help/instructions.
        """
        self.renderer.clear_screen()
        print("=== Level Editor Controls ===\n")
        print("Arrow keys: Move cursor")
        print("Space: Place current element")
        print("Tab: Cycle through elements")

        # Show keyboard-specific controls
        if self.keyboard_layout == QWERTY:
            print("S: Save level")
            print("H: Show this help")
        else:  # AZERTY
            print("S: Save level")
            print("H: Show this help")

        print("ESC: Exit editor")
        print("\nAvailable elements:")
        print(f"Wall: {WALL}")
        print(f"Floor: {FLOOR}")
        print(f"Player: {PLAYER}")
        print(f"Box: {BOX}")
        print(f"Target: {TARGET}")
        print(f"Player on target: {PLAYER_ON_TARGET}")
        print(f"Box on target: {BOX_ON_TARGET}")

        # Display keyboard layout information
        print(f"\nCurrent keyboard layout: {self.keyboard_layout.upper()}")

        input("\nPress Enter to start editing...")

    def _main_loop(self):
        """
        Main editor loop.
        """
        while self.running and self.current_level:
            # Render the current level
            self._render_editor()

            # Get user input
            key = self._get_input()

            # Process input
            self._process_input(key)

    def _render_editor(self):
        """
        Render the level editor interface.
        """
        self.renderer.clear_screen()

        # Render the level
        level_lines = self.current_level.get_state_string().split('\n')

        for y, line in enumerate(level_lines):
            # Convert the line to a list for easier modification
            chars = list(line)

            # Add cursor indicator
            if y == self.cursor_pos[1]:
                cursor_x = self.cursor_pos[0]
                if cursor_x < len(chars):
                    # Highlight the cursor position
                    char_at_cursor = chars[cursor_x]
                    chars[cursor_x] = f"\033[7m{char_at_cursor}\033[0m"  # Invert colors

            print(''.join(chars))

        # Display editor information
        print("\n=== Editor Info ===")
        print(f"Cursor: ({self.cursor_pos[0]}, {self.cursor_pos[1]})")
        print(f"Current element: {self.current_element}")
        print("Unsaved changes: Yes" if self.unsaved_changes else "Unsaved changes: No")
        print(f"Keyboard layout: {self.keyboard_layout.upper()}")

        # Display controls reminder
        print("\nControls: Arrow keys=Move, Space=Place, Tab=Cycle elements, S=Save, H=Help, ESC=Exit")

    def _get_input(self):
        """
        Get user input.

        Returns:
            str: The key pressed.
        """
        try:
            # Wait for a key press
            event = keyboard.read_event(suppress=True)

            # Only process key down events
            if event.event_type == keyboard.KEY_DOWN:
                # Check if the key is in the current keyboard layout's bindings
                action = KEY_BINDINGS[self.keyboard_layout].get(event.name)

                # For movement keys, we'll still use the original key names
                if action in ['up', 'down', 'left', 'right']:
                    return action

                # For other keys, pass through the original key name
                return event.name
        except Exception as e:
            print(f"Input error: {e}")

        return None

    def _process_input(self, key):
        """
        Process user input.

        Args:
            key (str): The key pressed.
        """
        if key is None:
            return

        # Movement
        if key == 'up' and self.cursor_pos[1] > 0:
            self.cursor_pos = (self.cursor_pos[0], self.cursor_pos[1] - 1)
        elif key == 'down' and self.cursor_pos[1] < self.current_level.height - 1:
            self.cursor_pos = (self.cursor_pos[0], self.cursor_pos[1] + 1)
        elif key == 'left' and self.cursor_pos[0] > 0:
            self.cursor_pos = (self.cursor_pos[0] - 1, self.cursor_pos[1])
        elif key == 'right' and self.cursor_pos[0] < self.current_level.width - 1:
            self.cursor_pos = (self.cursor_pos[0] + 1, self.cursor_pos[1])

        # Place element
        elif key == 'space':
            self._place_element()

        # Cycle through elements
        elif key == 'tab':
            self._cycle_element()

        # Save level - works with both 's' for QWERTY and 's' for AZERTY (same key)
        elif key == 's':
            self._save_level()

        # Show help - works with both 'h' for QWERTY and 'h' for AZERTY (same key)
        elif key == 'h':
            self._show_editor_help()

        # Exit editor
        elif key == 'esc':
            if self.unsaved_changes:
                self._confirm_exit()
            else:
                self.running = False
                self._show_welcome_screen()

    def _place_element(self):
        """
        Place the current element at the cursor position.
        """
        x, y = self.cursor_pos

        # Update the level data based on the current element
        original_char = self.current_level.get_display_char(x, y)

        # Get current player position
        player_x, player_y = self.current_level.player_pos

        # If placing a player, remove any existing player
        if self.current_element in [PLAYER, PLAYER_ON_TARGET]:
            # Remove the old player
            old_x, old_y = self.current_level.player_pos
            old_is_target = (old_x, old_y) in self.current_level.targets

            # Update the player position
            self.current_level.player_pos = (x, y)

            # Check if we're replacing a target
            if self.current_element == PLAYER_ON_TARGET or (x, y) in self.current_level.targets:
                if (x, y) not in self.current_level.targets:
                    self.current_level.targets.append((x, y))
            else:
                # Remove from targets if it was there
                if (x, y) in self.current_level.targets:
                    self.current_level.targets.remove((x, y))

        # If placing a box, add to boxes list
        elif self.current_element in [BOX, BOX_ON_TARGET]:
            if (x, y) not in self.current_level.boxes:
                self.current_level.boxes.append((x, y))

            # Check if we're replacing a target
            if self.current_element == BOX_ON_TARGET or (x, y) in self.current_level.targets:
                if (x, y) not in self.current_level.targets:
                    self.current_level.targets.append((x, y))
            else:
                # Remove from targets if it was there
                if (x, y) in self.current_level.targets:
                    self.current_level.targets.remove((x, y))

        # If placing a target, add to targets list
        elif self.current_element == TARGET:
            if (x, y) not in self.current_level.targets:
                self.current_level.targets.append((x, y))

            # Remove from boxes if it was there
            if (x, y) in self.current_level.boxes:
                self.current_level.boxes.remove((x, y))

        # If placing a wall or floor, update the map data
        elif self.current_element in [WALL, FLOOR]:
            self.current_level.map_data[y][x] = self.current_element

            # Remove from targets, boxes, and player position if needed
            if (x, y) in self.current_level.targets:
                self.current_level.targets.remove((x, y))

            if (x, y) in self.current_level.boxes:
                self.current_level.boxes.remove((x, y))

            if (x, y) == self.current_level.player_pos:
                # Reset player position (not ideal, but prevents crashes)
                for ny in range(self.current_level.height):
                    for nx in range(self.current_level.width):
                        if self.current_level.get_cell(nx, ny) == FLOOR and (nx, ny) != (x, y):
                            self.current_level.player_pos = (nx, ny)
                            break

        self.unsaved_changes = True

    def _cycle_element(self):
        """
        Cycle through the available elements.
        """
        elements = [WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET]
        current_index = elements.index(self.current_element)
        next_index = (current_index + 1) % len(elements)
        self.current_element = elements[next_index]

    def _save_level(self):
        """
        Save the current level to a file.
        """
        self.renderer.clear_screen()
        print("=== Save Level ===\n")

        # Get filename
        filename = input("Enter filename (without extension): ")

        if not filename:
            print("Invalid filename.")
            input("Press Enter to continue...")
            return

        # Add .txt extension if not provided
        if not filename.endswith('.txt'):
            filename += '.txt'

        # Create full path
        level_path = os.path.join(self.levels_dir, filename)

        # Check if file exists
        if os.path.exists(level_path):
            overwrite = input(f"File '{filename}' already exists. Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                print("Save cancelled.")
                input("Press Enter to continue...")
                return

        # Save the level
        level_string = self.current_level.get_state_string()

        try:
            with open(level_path, 'w') as file:
                file.write(level_string)

            print(f"Level saved to '{filename}'.")
            self.unsaved_changes = False
        except Exception as e:
            print(f"Error saving level: {e}")

        input("Press Enter to continue...")

    def _generate_random_level(self):
        """
        Generate a random level using the procedural generator.
        """
        self.renderer.clear_screen()
        print("=== Generate Random Level ===\n")

        # Get generation parameters
        try:
            min_width = int(input("Enter minimum width (5-20, default 7): ") or "7")
            max_width = int(input("Enter maximum width (5-20, default 15): ") or "15")
            min_height = int(input("Enter minimum height (5-20, default 7): ") or "7")
            max_height = int(input("Enter maximum height (5-20, default 15): ") or "15")
            min_boxes = int(input("Enter minimum boxes (1-10, default 1): ") or "1")
            max_boxes = int(input("Enter maximum boxes (1-10, default 5): ") or "5")
            wall_density = float(input("Enter wall density (0.0-0.5, default 0.2): ") or "0.2")

            # Validate parameters
            if (min_width < 5 or min_width > 20 or max_width < 5 or max_width > 20 or
                min_height < 5 or min_height > 20 or max_height < 5 or max_height > 20 or
                min_boxes < 1 or min_boxes > 10 or max_boxes < 1 or max_boxes > 10 or
                wall_density < 0.0 or wall_density > 0.5):
                print("Invalid parameters. Using defaults.")
                min_width, max_width = 7, 15
                min_height, max_height = 7, 15
                min_boxes, max_boxes = 1, 5
                wall_density = 0.2
        except ValueError:
            print("Invalid input. Using defaults.")
            min_width, max_width = 7, 15
            min_height, max_height = 7, 15
            min_boxes, max_boxes = 1, 5
            wall_density = 0.2

        print("\nGenerating random level... This may take a moment.")

        # Generate the level
        params = {
            'min_width': min_width,
            'max_width': max_width,
            'min_height': min_height,
            'max_height': max_height,
            'min_boxes': min_boxes,
            'max_boxes': max_boxes,
            'wall_density': wall_density
        }

        if self.level_manager.generate_random_level(params):
            self.current_level = self.level_manager.current_level
            self.unsaved_changes = True
            print("\nRandom level generated successfully!")

            # Show the level
            self.renderer.clear_screen()
            self.renderer.render_level(self.current_level, None)

            # Ask if user wants to save the level
            save = input("\nDo you want to save this level? (y/n): ")
            if save.lower() == 'y':
                self._save_level()

            # Show help before starting editing
            self._show_editor_help()
        else:
            print("\nFailed to generate a random level.")
            input("Press Enter to continue...")
            self._show_welcome_screen()

    def _confirm_exit(self):
        """
        Confirm exit if there are unsaved changes.
        """
        self.renderer.clear_screen()
        print("You have unsaved changes. Exit anyway? (y/n): ")

        while True:
            try:
                event = keyboard.read_event(suppress=True)

                if event.event_type == keyboard.KEY_DOWN:
                    if event.name.lower() == 'y':
                        self.running = False
                        self._show_welcome_screen()
                        break
                    elif event.name.lower() == 'n':
                        break
            except Exception:
                pass


def main():
    """
    Main function to run the Sokoban level editor.
    """
    # Parse command line arguments
    levels_dir = 'levels'

    # Get default keyboard layout from config
    from src.core.config_manager import get_config_manager
    config_manager = get_config_manager()
    keyboard_layout = config_manager.get('game', 'keyboard_layout', 'qwerty')

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

    # Create and start the level editor
    editor = LevelEditor(levels_dir, keyboard_layout)
    editor.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nEditor terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
