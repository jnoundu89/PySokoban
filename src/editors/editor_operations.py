"""
Editor Operations delegate for the Enhanced Level Editor.

This module handles all level manipulation operations for the level editor,
including placing/clearing elements, creating/opening/saving levels,
validation, solving, generation, and test mode toggling.
"""

import os
import pygame
from ..core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE
from ..core.level import Level
from ..core.auto_solver import AutoSolver


class EditorOperations:
    """
    Handles all level manipulation operations for the EnhancedLevelEditor.

    Uses a back-reference to the editor instance to access shared state
    (current_level, map_width, map_height, sliders, level_manager, etc.).
    """

    def __init__(self, editor):
        """
        Initialize the operations handler with a back-reference to the editor.

        Args:
            editor: The EnhancedLevelEditor instance.
        """
        self.editor = editor

    def place_element(self, x, y):
        """Place the current element at the specified grid coordinates."""
        if self.editor.current_element == PLAYER:
            # Remove existing player
            self.editor.current_level.player_pos = (x, y)
        elif self.editor.current_element == BOX:
            # Add box if not already there
            if (x, y) not in self.editor.current_level.boxes:
                self.editor.current_level.boxes.append((x, y))
        elif self.editor.current_element == TARGET:
            # Add target if not already there
            if (x, y) not in self.editor.current_level.targets:
                self.editor.current_level.targets.append((x, y))
        elif self.editor.current_element == WALL:
            # Set cell to wall
            self.editor.current_level.map_data[y][x] = WALL

            # Remove any objects at this position
            if (x, y) == self.editor.current_level.player_pos:
                self.editor.current_level.player_pos = (0, 0)
            if (x, y) in self.editor.current_level.boxes:
                self.editor.current_level.boxes.remove((x, y))
            if (x, y) in self.editor.current_level.targets:
                self.editor.current_level.targets.remove((x, y))
        elif self.editor.current_element == FLOOR:
            # Set cell to floor
            self.editor.current_level.map_data[y][x] = FLOOR

        self.editor.unsaved_changes = True

    def place_floor(self, x, y):
        """Place floor at the specified coordinates, removing any existing elements."""
        # Remove any objects at this position
        if (x, y) == self.editor.current_level.player_pos:
            # Find a safe position for the player (first floor tile)
            for py in range(self.editor.current_level.height):
                for px in range(self.editor.current_level.width):
                    if (self.editor.current_level.map_data[py][px] == FLOOR and
                        (px, py) not in self.editor.current_level.boxes and
                        (px, py) not in self.editor.current_level.targets):
                        self.editor.current_level.player_pos = (px, py)
                        break
                else:
                    continue
                break
            else:
                # If no safe position found, place at (1,1)
                self.editor.current_level.player_pos = (1, 1)

        if (x, y) in self.editor.current_level.boxes:
            self.editor.current_level.boxes.remove((x, y))
        if (x, y) in self.editor.current_level.targets:
            self.editor.current_level.targets.remove((x, y))

        # Always set cell to floor
        self.editor.current_level.map_data[y][x] = FLOOR

        self.editor.unsaved_changes = True

    def clear_element(self, x, y):
        """Clear the element at the specified grid coordinates and set to floor."""
        # This method now just calls place_floor for consistency
        self.place_floor(x, y)

    def create_new_level(self, width, height):
        """Create a new empty level."""
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
        self.editor.current_level = Level(level_data=level_string)
        self.editor.unsaved_changes = True
        self.editor._reset_view()  # Auto-fit the new level

    def show_open_dialog(self):
        """Show dialog to open an existing level using a Windows file dialog."""
        import tkinter as tk
        from tkinter import filedialog
        try:
            # Initialize tkinter
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Make sure the dialog appears in front of the pygame window
            root.attributes('-topmost', True)

            # Show the file open dialog
            file_path = filedialog.askopenfilename(
                title="Open Level",
                initialdir=self.editor.levels_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            # If a file was selected, open it
            if file_path:
                try:
                    self.editor.current_level = Level(level_file=file_path)
                    # Update the editor's internal dimensions to match the loaded level
                    self.editor.map_width = self.editor.current_level.width
                    self.editor.map_height = self.editor.current_level.height
                    # Update slider values to match the new dimensions
                    for slider in self.editor.sliders:
                        if slider['label'] == 'Width':
                            slider['value'] = self.editor.map_width
                        elif slider['label'] == 'Height':
                            slider['value'] = self.editor.map_height
                    self.editor.unsaved_changes = False
                    self.editor._reset_view()
                except Exception as e:
                    print(f"Error opening level: {e}")
        finally:
            # Clean up tkinter
            try:
                root.destroy()
            except:
                pass

    def show_save_dialog(self):
        """Show dialog to save the current level using a Windows file dialog."""
        if not self.editor.current_level:
            return

        # Check if the level is valid before allowing save
        if not self.validate_level(show_dialog=False):
            import tkinter as tk
            from tkinter import messagebox
            try:
                # Initialize tkinter
                root = tk.Tk()
                root.withdraw()  # Hide the main window

                # Make sure the dialog appears in front of the pygame window
                root.attributes('-topmost', True)

                # Show warning message
                messagebox.showwarning(
                    "Invalid Level",
                    "Cannot save an invalid level. Please ensure:\n\n"
                    "- The level has a player\n"
                    "- The level has at least one box\n"
                    "- The level has at least one target\n"
                    "- The number of boxes matches the number of targets"
                )
            finally:
                # Clean up tkinter
                try:
                    root.destroy()
                except:
                    pass
            return

        import tkinter as tk
        from tkinter import filedialog
        try:
            # Initialize tkinter
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Make sure the dialog appears in front of the pygame window
            root.attributes('-topmost', True)

            # Show the file save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Level",
                initialdir=self.editor.levels_dir,
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            # If a file was selected, save it
            if file_path:
                # Pass the full file path to save_level
                self.save_level(file_path)
        finally:
            # Clean up tkinter
            try:
                root.destroy()
            except:
                pass

    def save_level(self, file_path):
        """Save the current level to a file."""
        if not file_path:
            return

        # Add .txt extension if not provided
        if not file_path.endswith('.txt'):
            file_path += '.txt'

        # Save the level without FESS coordinate labels
        level_string = self.editor.current_level.get_state_string(show_fess_coordinates=False)

        try:
            with open(file_path, 'w') as file:
                file.write(level_string)

            self.editor.unsaved_changes = False

            # Reload level files in level manager
            self.editor.level_manager._load_level_files()
        except Exception as e:
            print(f"Error saving level: {e}")

    def validate_level(self, show_dialog=True):
        """Validate the current level."""
        if not self.editor.current_level:
            return False

        # Check if level has a player
        has_player = self.editor.current_level.player_pos != (0, 0)

        # Check if level has at least one box and target
        has_boxes = len(self.editor.current_level.boxes) > 0
        has_targets = len(self.editor.current_level.targets) > 0

        # Check if number of boxes matches number of targets
        boxes_match_targets = len(self.editor.current_level.boxes) == len(self.editor.current_level.targets)

        # Check if level is valid
        is_valid = has_player and has_boxes and has_targets and boxes_match_targets

        if show_dialog:
            # Simple validation message (in a full implementation, this would be a proper dialog)
            status = "Valid" if is_valid else "Invalid"
            print(f"Level validation: {status}")
            if not is_valid:
                print(f"Player: {has_player}, Boxes: {has_boxes}, Targets: {has_targets}, Match: {boxes_match_targets}")

        return is_valid

    def solve_level(self):
        """Solve the current level and let AI take control to solve it automatically."""
        if not self.editor.current_level:
            print("No level to solve")
            return

        if not self.validate_level(show_dialog=False):
            print("Level is not valid - cannot solve")
            return

        try:
            # Create a renderer for the editor context
            class _EditorSolveRenderer:
                def __init__(self, editor):
                    self.editor = editor
                    self.screen = editor.screen

                def render_level(self, level, level_manager, show_grid, zoom_level, scroll_x, scroll_y, skin_manager):
                    # Use the editor's drawing method
                    self.editor._draw_editor()

                def get_size(self):
                    return self.screen.get_size()

            # Create auto solver with editor renderer
            auto_solver = AutoSolver(self.editor.current_level, _EditorSolveRenderer(self.editor), self.editor.skin_manager)

            # Show solving message
            print("\n" + "="*60)
            print("AI TAKING CONTROL OF LEVEL")
            print("="*60)

            def progress_callback(message):
                print(f"AI: {message}")

            # Solve the level
            success = auto_solver.solve_level(progress_callback)

            if success:
                solution_info = auto_solver.get_solution_info()
                print(f"SUCCESS: Solution found!")
                print(f"Solution length: {solution_info['moves']} moves")
                print(f"AI will now take control and solve the level...")
                print("="*60)

                # Let AI take control and solve the level
                ai_success = auto_solver.execute_solution_live(
                    move_delay=600,  # Slightly slower for editor visibility
                    show_grid=self.editor.show_grid,
                    zoom_level=self.editor.zoom_level,
                    scroll_x=self.editor.scroll_x,
                    scroll_y=self.editor.scroll_y,
                    level_manager=None
                )

                if ai_success:
                    print("AI successfully solved the level!")
                    self.editor.unsaved_changes = True  # Mark as changed since level state changed
                else:
                    print("AI failed to execute the solution")

            else:
                print("FAILED: No solution found for this level")
                print("The level might be unsolvable or too complex")
                print("="*60)

        except Exception as e:
            print(f"ERROR: Exception during AI level solving: {e}")
            import traceback
            traceback.print_exc()
            print("="*60)

    def show_generate_dialog(self):
        """Show dialog to generate a random level."""
        # Simple implementation - generate with default parameters
        try:
            params = {
                'min_width': 8,
                'max_width': 12,
                'min_height': 8,
                'max_height': 12,
                'min_boxes': 2,
                'max_boxes': 4,
                'wall_density': 0.15,
                'timeout': 30.0  # Increased timeout for better chance of success
            }

            # Show a message to indicate generation is in progress
            print("\n" + "="*60)
            print("LEVEL GENERATION STARTED")
            print("="*60)
            print("Parameters:")
            print(f"  Size: {params['min_width']}x{params['min_height']} to {params['max_width']}x{params['max_height']}")
            print(f"  Boxes: {params['min_boxes']} to {params['max_boxes']}")
            print(f"  Wall density: {params['wall_density']}")
            print(f"  Timeout: {params['timeout']} seconds")
            print("-"*60)

            # Define a custom progress callback with more detailed information
            def enhanced_progress_callback(progress_info):
                status = progress_info.get('status', 'unknown')
                attempts = progress_info.get('attempts', 0)
                elapsed = progress_info.get('elapsed_time', 0)
                percent = progress_info.get('percent', 0)

                # Create a progress bar
                bar_length = 40
                filled_length = int(bar_length * percent / 100)
                bar = '\u2588' * filled_length + '\u2591' * (bar_length - filled_length)

                if status == 'generating':
                    width = progress_info.get('width', 0)
                    height = progress_info.get('height', 0)
                    boxes = progress_info.get('boxes', 0)
                    timeout = progress_info.get('timeout', 0)
                    remaining = max(0, timeout - elapsed)

                    print(f"\rGenerating level... [{bar}] {percent:.1f}% | Attempts: {attempts} | Time: {elapsed:.1f}s | Remaining: {remaining:.1f}s | Current: {width}x{height} with {boxes} boxes", end='')

                elif status == 'success':
                    solution_length = progress_info.get('solution_length', 0)
                    width = progress_info.get('width', 0)
                    height = progress_info.get('height', 0)
                    boxes = progress_info.get('boxes', 0)

                    print(f"\rGeneration complete! [{bar}] 100% | Attempts: {attempts} | Time: {elapsed:.1f}s | Size: {width}x{height} | Boxes: {boxes} | Solution: {solution_length} moves")
                    print("\nSUCCESS: Level generated successfully!")
                    print("="*60)

                elif status == 'timeout':
                    print(f"\rGeneration timed out! [{bar}] 100% | Attempts: {attempts} | Time: {elapsed:.1f}s | Could not find a solvable level")
                    print("\nWARNING: Could not generate a solvable level within the timeout period.")
                    print("Try again with different parameters or a longer timeout.")
                    print("="*60)

            # Generate the level with our enhanced progress callback
            if self.editor.level_manager.generate_random_level(params, enhanced_progress_callback):
                self.editor.current_level = self.editor.level_manager.current_level
                self.editor.unsaved_changes = True
                self.editor._reset_view()

                # Additional metrics display
                if self.editor.level_manager.current_level_metrics:
                    metrics = self.editor.level_manager.current_level_metrics
                    print("\nLevel Metrics:")
                    print(f"  Difficulty: {metrics['difficulty']['overall_score']:.1f}/100")
                    if 'space_efficiency' in metrics:
                        print(f"  Space efficiency: {metrics['space_efficiency']:.2f}")
                    if 'box_density' in metrics:
                        print(f"  Box density: {metrics['box_density']:.2f}")
                    if 'patterns' in metrics:
                        print("  Patterns:")
                        patterns = metrics['patterns']
                        if 'corners' in patterns:
                            print(f"    Corners: {patterns['corners']}")
                        if 'corridors' in patterns:
                            print(f"    Corridors: {patterns['corridors']}")
                        if 'rooms' in patterns:
                            print(f"    Rooms: {patterns['rooms']}")
                        if 'dead_ends' in patterns:
                            print(f"    Dead ends: {patterns['dead_ends']}")
                    print("="*60)
            else:
                print("\nERROR: Failed to generate a level. Please try again.")
                print("="*60)
        except Exception as e:
            print(f"\nERROR: Exception during level generation: {e}")
            import traceback
            traceback.print_exc()
            print("="*60)

    def toggle_test_mode(self):
        """Toggle test mode to play the current level."""
        if self.validate_level(show_dialog=False):
            self.editor.test_mode = not self.editor.test_mode

            if self.editor.test_mode:
                # Save complete initial state for testing
                self.editor.initial_level_state = {
                    'player_pos': self.editor.current_level.player_pos,
                    'boxes': self.editor.current_level.boxes.copy(),
                    'targets': self.editor.current_level.targets.copy(),
                    'map_data': [row[:] for row in self.editor.current_level.map_data]  # Deep copy
                }
            else:
                # Restore complete initial state after testing
                if self.editor.initial_level_state:
                    self.editor.current_level.player_pos = self.editor.initial_level_state['player_pos']
                    self.editor.current_level.boxes = self.editor.initial_level_state['boxes'].copy()
                    self.editor.current_level.targets = self.editor.initial_level_state['targets'].copy()
                    self.editor.current_level.map_data = [row[:] for row in self.editor.initial_level_state['map_data']]
