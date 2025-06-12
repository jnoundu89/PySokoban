#!/usr/bin/env python3
"""
Sokoban Game - GUI Version

A Python implementation of the classic Sokoban puzzle game with a graphical user interface.
This is the main module that starts the GUI version of the game.
"""

import os
import sys
import pygame
from src.core.constants import KEY_BINDINGS, QWERTY, AZERTY, DEFAULT_KEYBOARD, TITLE
from src.core.level import Level
from src.level_management.level_manager import LevelManager
from src.renderers.gui_renderer import GUIRenderer
from src.core.game import Game
from src.core.auto_solver import AutoSolver
from src.core.config_manager import get_config_manager


class GUIGame(Game):
    """
    GUI version of the Sokoban game.

    This class extends the base Game class with GUI-specific functionality.
    """

    def __init__(self, levels_dir='levels', keyboard_layout=None, skin_manager=None):
        """
        Initialize the GUI version of the Sokoban game.

        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           If None, loads from config file.
            skin_manager (EnhancedSkinManager, optional): Existing skin manager to use.
                                                         If None, creates a new one.
        """
        # Load config manager first to get keyboard layout
        from src.core.config_manager import get_config_manager
        self.config_manager = get_config_manager()

        # If keyboard_layout is not provided, load it from config
        if keyboard_layout is None:
            keyboard_layout = self.config_manager.get('game', 'keyboard_layout', DEFAULT_KEYBOARD)

        level_manager = LevelManager(levels_dir)
        renderer = GUIRenderer(window_title=TITLE)
        super().__init__(level_manager, renderer, keyboard_layout)

        # Enhanced skin manager for directional sprites
        if skin_manager:
            self.skin_manager = skin_manager
        else:
            from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
            self.skin_manager = EnhancedSkinManager()
        self.show_help = False
        self.show_grid = False  # Grid toggle functionality

        # Zoom and scroll for better level viewing
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        self.scroll_x = 0
        self.scroll_y = 0

        # Continuous movement support
        self.keys_pressed = set()
        self.last_move_time = 0
        self.move_delay = self.config_manager.get('game', 'movement_cooldown')  # milliseconds between moves when holding key
        self.initial_move_delay = 300  # milliseconds before starting continuous movement

        # Auto solver for solving levels
        self.auto_solver = None

        # Load custom keybindings from config
        self.custom_keybindings = self.config_manager.get_keybindings()

        # Create a reverse mapping for continuous movement
        self.custom_movement_keys = {}
        self._update_movement_keys()

    def start(self):
        """
        Start the game.
        """
        self.running = True
        self.renderer.render_welcome_screen(self.custom_keybindings)

        # Reset sprite history at the start of the game
        self.skin_manager.reset_sprite_history()

        # Wait for a key press to start
        waiting_for_start = True
        while waiting_for_start:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit_game()
                    return
                elif event.type == pygame.KEYDOWN:
                    waiting_for_start = False

        self.game_loop()

    def game_loop(self):
        """
        Main game loop.
        """
        clock = pygame.time.Clock()

        # Reload keybindings and movement cooldown at the start of each game loop
        self.custom_keybindings = self.config_manager.get_keybindings()
        self.move_delay = self.config_manager.get('game', 'movement_cooldown', 200)
        self._update_movement_keys()

        while self.running:
            current_time = pygame.time.get_ticks()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit_game()
                elif event.type == pygame.KEYDOWN:
                    # Check for F11 key for fullscreen toggle
                    if event.key == pygame.K_F11:
                        # Find the parent EnhancedSokoban instance
                        for frame in sys._current_frames().values():
                            try:
                                if 'self' in frame.f_locals and hasattr(frame.f_locals['self'], 'toggle_fullscreen'):
                                    frame.f_locals['self'].toggle_fullscreen()
                                    break
                            except:
                                continue
                    else:
                        # Add key to pressed keys set
                        self.keys_pressed.add(event.key)
                        self._handle_key_event(event)
                        self.last_move_time = current_time
                elif event.type == pygame.KEYUP:
                    # Remove key from pressed keys set
                    self.keys_pressed.discard(event.key)
                elif event.type == pygame.MOUSEWHEEL:
                    # Handle zoom with mouse wheel
                    if event.y > 0:  # Scroll up - zoom in
                        self.zoom_level = min(self.max_zoom, self.zoom_level * 1.1)
                    else:  # Scroll down - zoom out
                        self.zoom_level = max(self.min_zoom, self.zoom_level / 1.1)
                elif event.type == pygame.VIDEORESIZE:
                    # Update renderer with new screen size
                    self.renderer.window_size = (event.w, event.h)
                    self.renderer.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

                    # Save new dimensions to config
                    config_manager = get_config_manager()
                    config_manager.set_display_config(width=event.w, height=event.h)

            # Handle continuous movement
            if self.keys_pressed and current_time - self.last_move_time > self.move_delay:
                self._handle_continuous_movement()
                self.last_move_time = current_time

            # Render the current state
            if self.show_help:
                self.renderer.render_help(self.custom_keybindings)
            else:
                self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                         self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager, 
                                         show_completion_message=True)

            # Cap the frame rate
            clock.tick(60)

    def _handle_key_event(self, event):
        """
        Handle keyboard events.

        Args:
            event: Pygame key event.
        """
        # If help screen is showing, any key dismisses it
        if self.show_help:
            self.show_help = False
            return

        # Get the key name
        key_name = pygame.key.name(event.key)

        # Check for Escape key to return to level selector
        if key_name == 'escape':
            self._return_to_level_selector()
            return

        # First check arrow keys (which work regardless of keyboard layout)
        if key_name == 'up':
            self._handle_movement('up')
        elif key_name == 'down':
            self._handle_movement('down')
        elif key_name == 'left':
            self._handle_movement('left')
        elif key_name == 'right':
            self._handle_movement('right')
        # Check for WASD/ZQSD keys directly
        elif (self.keyboard_layout == QWERTY and key_name == 'w') or (self.keyboard_layout == AZERTY and key_name == 'z'):
            self._handle_movement('up')
        elif (self.keyboard_layout == QWERTY and key_name == 'a') or (self.keyboard_layout == AZERTY and key_name == 'q'):
            self._handle_movement('left')
        elif key_name == 's':  # Same in both layouts
            self._handle_movement('down')
        elif key_name == 'd':  # Same in both layouts
            self._handle_movement('right')
        else:
            # Check if this key matches any custom keybinding
            action = None

            # Look for the key in custom keybindings
            for action_name, bound_key in self.custom_keybindings.items():
                if key_name == bound_key:
                    action = action_name
                    break

            # If not found in custom keybindings, check if this key is used for a different action
            # in the custom keybindings before falling back to default layout
            if action is None:
                # Create a reverse mapping of keys to actions from custom keybindings
                custom_keys = {v: k for k, v in self.custom_keybindings.items()}

                # Check if this key is bound to an action in the default layout
                default_action = KEY_BINDINGS[self.keyboard_layout].get(key_name)

                # Only use the default action if it's not rebound to a different key
                if default_action and default_action not in custom_keys:
                    action = default_action

            if action:
                if action == 'up':
                    self._handle_movement('up')
                elif action == 'down':
                    self._handle_movement('down')
                elif action == 'left':
                    self._handle_movement('left')
                elif action == 'right':
                    self._handle_movement('right')
                elif action == 'reset':
                    self.level_manager.reset_current_level()
                    # Reset sprite history for the reset level
                    self.skin_manager.reset_sprite_history()
                elif action == 'quit':
                    self._quit_game()
                elif action == 'next':
                    # Go to next level regardless of completion status
                    self._next_level()
                elif action == 'previous':
                    # Go to previous level
                    self._prev_level()
                elif action == 'undo':
                    # Get the previous sprite before undoing the move
                    if self.level_manager.current_level.undo():
                        # Get previous sprite from history
                        self.skin_manager.get_previous_sprite()
                elif action == 'help':
                    self.show_help = True
                elif action == 'grid':
                    self.show_grid = not self.show_grid
                elif action == 'solve':
                    self._solve_current_level()

    def _update_movement_keys(self):
        """
        Update the movement keys mapping based on custom keybindings.
        """
        # Start with the default arrow keys
        self.custom_movement_keys = {
            pygame.K_UP: 'up',
            pygame.K_DOWN: 'down',
            pygame.K_LEFT: 'left',
            pygame.K_RIGHT: 'right'
        }

        # Add layout-specific keys (WASD for QWERTY, ZQSD for AZERTY)
        if self.keyboard_layout == QWERTY:
            self.custom_movement_keys[pygame.K_w] = 'up'
            self.custom_movement_keys[pygame.K_a] = 'left'
            self.custom_movement_keys[pygame.K_s] = 'down'
            self.custom_movement_keys[pygame.K_d] = 'right'
        elif self.keyboard_layout == AZERTY:
            self.custom_movement_keys[pygame.K_z] = 'up'
            self.custom_movement_keys[pygame.K_q] = 'left'
            self.custom_movement_keys[pygame.K_s] = 'down'
            self.custom_movement_keys[pygame.K_d] = 'right'

        # Add custom keybindings for movement (these override the defaults)
        for action, key_name in self.custom_keybindings.items():
            if action in ['up', 'down', 'left', 'right']:
                # Convert key name to pygame key constant
                key_constant = getattr(pygame, f'K_{key_name.upper()}', None)
                if key_constant:
                    self.custom_movement_keys[key_constant] = action

    def _handle_continuous_movement(self):
        """
        Handle continuous movement when keys are held down.
        """
        if self.show_help:
            return

        # Use the custom movement keys mapping
        for key in self.keys_pressed:
            if key in self.custom_movement_keys:
                self._handle_movement(self.custom_movement_keys[key])
                break  # Only handle one movement at a time

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

        # Check if move would push a box
        player_x, player_y = self.level_manager.current_level.player_pos
        new_x, new_y = player_x + dx, player_y + dy
        is_pushing = (new_x, new_y) in self.level_manager.current_level.boxes

        # Check if move is blocked using the existing can_move method
        is_blocked = not self.level_manager.current_level.can_move(dx, dy)
        if is_pushing:
            # Check if box can be pushed
            box_new_x, box_new_y = new_x + dx, new_y + dy
            # Check if the box destination is valid (not a wall and not another box)
            is_blocked = (self.level_manager.current_level.is_wall(box_new_x, box_new_y) or
                         self.level_manager.current_level.is_box(box_new_x, box_new_y))

        # Update player state in skin manager
        self.skin_manager.update_player_state(direction, is_pushing, is_blocked)

        # Try to move the player
        moved = self.level_manager.current_level.move(dx, dy)

        # If the player moved, advance the animation
        if moved:
            # Get the player sprite with advance_animation=True to move to the next frame
            self.skin_manager.get_player_sprite(advance_animation=True)

        # Check if level is completed after the move
        if moved and self.level_manager.current_level_completed():
            # Render the completed level without showing completion message
            self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                     self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager,
                                     show_completion_message=False)
            pygame.display.flip()

            # Wait for a moment
            pygame.time.wait(1000)

            # Show level completion screen with option to proceed to next level
            self._show_level_completion_screen()

    def _get_input(self):
        """
        Get user input.

        This method is not used in the GUI version, as input is handled by pygame events.
        """
        pass

    def _next_level(self):
        """
        Go to the next level, prioritizing collection navigation.
        """
        # First try to go to next level in current collection
        if self.level_manager.has_next_level_in_collection():
            self.level_manager.next_level_in_collection()
            # Reset sprite history for the new level
            self.skin_manager.reset_sprite_history()
        # If no more levels in collection, try next level file
        elif self.level_manager.has_next_level():
            self.level_manager.next_level()
            # Reset sprite history for the new level
            self.skin_manager.reset_sprite_history()
        else:
            # No more levels, return to selector
            self._return_to_level_selector()

    def _prev_level(self):
        """
        Go to the previous level, prioritizing collection navigation.
        """
        # First try to go to previous level in current collection
        if self.level_manager.has_prev_level_in_collection():
            self.level_manager.prev_level_in_collection()
            # Reset sprite history for the new level
            self.skin_manager.reset_sprite_history()
        # If no more levels in collection, try previous level file
        elif self.level_manager.has_prev_level():
            self.level_manager.prev_level()
            # Reset sprite history for the new level
            self.skin_manager.reset_sprite_history()

    def _return_to_level_selector(self):
        """
        Return to the level selector.
        """
        self.running = False

    def _show_level_completion_screen(self):
        """
        Show level completion screen with option to proceed to next level.
        If there's no next level in the collection, show options to replay current level or return to level selector.
        Shows a preview of the next level in the collection if available.
        """
        # Check if there's a next level in the collection
        has_next_level = self.level_manager.has_next_level_in_collection()

        # Clear the keys_pressed set to prevent automatic movement
        self.keys_pressed.clear()

        # Get the collection file
        collection_file = self.level_manager.level_files[self.level_manager.current_level_index]

        # Create a LevelInfo object
        from src.level_management.level_selector import LevelInfo

        if has_next_level:
            # Get information about the next level
            next_level_index = self.level_manager.current_collection_index + 1

            # Get the next level's title
            try:
                next_level_title, _ = self.level_manager.current_collection.get_level(next_level_index)
            except:
                next_level_title = "Next Level"

            # Create a LevelInfo object for the next level
            level_info = LevelInfo(
                title=next_level_title,
                collection_file=collection_file,
                level_index=next_level_index,
                is_from_collection=True
            )
        else:
            # If there's no next level, create a LevelInfo object for the current level
            # This will allow the player to replay the current level or return to level selection
            current_level_index = self.level_manager.current_collection_index

            try:
                current_level_title, _ = self.level_manager.current_collection.get_level(current_level_index)
            except:
                current_level_title = "Current Level"

            level_info = LevelInfo(
                title=current_level_title + " (Completed)",
                collection_file=collection_file,
                level_index=current_level_index,
                is_from_collection=True
            )

        # Create a level preview
        from src.ui.level_preview import LevelPreview
        level_preview = LevelPreview(
            self.renderer.screen,
            self.renderer.screen.get_width(),
            self.renderer.screen.get_height()
        )

        # Show the level preview and get the user's choice
        action = level_preview.show_level_preview(level_info)

        # Handle the user's choice
        if action == 'play':
            if has_next_level:
                # Proceed to the next level
                self.level_manager.next_level_in_collection()
            else:
                # Replay the current level
                self.level_manager.reset_current_level()
                # Reset sprite history for the reset level
                self.skin_manager.reset_sprite_history()
        else:
            # Return to level selection
            self._return_to_level_selector()

    def _solve_current_level(self):
        """
        Solve the current level automatically and animate the solution.
        """
        if not self.level_manager.current_level:
            return

        # Don't solve if already solving
        if self.auto_solver and self.auto_solver.is_solving:
            return

        # Create auto solver for current level
        self.auto_solver = AutoSolver(
            self.level_manager.current_level,
            self.renderer,
            self.skin_manager
        )

        # Show solving message
        def progress_callback(message):
            # Render current level with overlay (without completion message)
            self.renderer.render_level(
                self.level_manager.current_level,
                self.level_manager,
                self.show_grid,
                self.zoom_level,
                self.scroll_x,
                self.scroll_y,
                self.skin_manager,
                show_completion_message=False
            )

            # Add solving overlay
            self._render_solving_overlay(message)
            pygame.display.flip()

        # Try to solve the level
        success = self.auto_solver.solve_level(progress_callback)

        if success:
            # Execute the solution live - AI takes control
            self.auto_solver.execute_solution_live(
                move_delay=400,  # 400ms between moves for smoother experience
                show_grid=self.show_grid,
                zoom_level=self.zoom_level,
                scroll_x=self.scroll_x,
                scroll_y=self.scroll_y,
                level_manager=self.level_manager
            )
        else:
            # Show "no solution" message with more details (without completion message)
            self.renderer.render_level(
                self.level_manager.current_level,
                self.level_manager,
                self.show_grid,
                self.zoom_level,
                self.scroll_x,
                self.scroll_y,
                self.skin_manager,
                show_completion_message=False
            )

            # Create detailed message
            level_size = self.level_manager.current_level.width * self.level_manager.current_level.height
            box_count = len(self.level_manager.current_level.boxes)

            if level_size > 100 or box_count > 8:
                message = f"Level too complex for AI! ({box_count} boxes, {level_size} cells)\nTry a simpler level. Press any key to continue..."
            else:
                message = "AI couldn't find solution in time limit.\nLevel might be unsolvable. Press any key to continue..."

            self._render_solving_overlay(message)
            pygame.display.flip()

            # Wait for user input
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                        waiting = False

    def _render_solving_overlay(self, text):
        """
        Render an overlay with solving progress text.

        Args:
            text (str): Text to display.
        """
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.renderer.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.renderer.screen.blit(overlay, (0, 0))

        # Render text
        font = pygame.font.Font(None, 36)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.renderer.screen.get_width() // 2,
                                                 self.renderer.screen.get_height() // 2))
        self.renderer.screen.blit(text_surface, text_rect)

        # Add instruction text
        instruction_font = pygame.font.Font(None, 24)
        instruction_text = "Press S to solve level | Press ESC to cancel"
        instruction_surface = instruction_font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(self.renderer.screen.get_width() // 2,
                                                              text_rect.bottom + 30))
        self.renderer.screen.blit(instruction_surface, instruction_rect)

    def _quit_game(self):
        """
        Quit the game.
        """
        self.running = False
        self.renderer.cleanup()
        sys.exit(0)


def main():
    """
    Main function to run the GUI version of the Sokoban game.
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
    game = GUIGame(levels_dir, keyboard_layout)
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
