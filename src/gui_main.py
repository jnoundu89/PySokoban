#!/usr/bin/env python3
"""
Sokoban Game - GUI Version

A Python implementation of the classic Sokoban puzzle game with a graphical user interface.
This is the main module that starts the GUI version of the game.
"""

import os
import sys
import pygame
from typing import Optional, Dict, Any
from src.core.constants import KEY_BINDINGS, QWERTY, AZERTY, DEFAULT_KEYBOARD, TITLE, CELL_SIZE
from src.core.level import Level
from src.level_management.level_manager import LevelManager
from src.renderers.gui_renderer import GUIRenderer
from src.core.game import Game
from src.core.auto_solver import AutoSolver
from src.core.config_manager import get_config_manager
from src.ai.visual_ai_solver import VisualAISolver
from src.ai.algorithm_selector import Algorithm
from src.core.deadlock_detector import DeadlockDetector
from src.ui.mouse_navigation import MouseNavigationSystem


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

        # Initialize deadlock detector
        self.deadlock_detector = None
        self.deadlock_notification_shown = False

        # Load deadlock display setting from config
        self.show_deadlocks = self.config_manager.get('game', 'show_deadlocks', True)

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

        # Auto solver for solving levels (legacy)
        self.auto_solver = None

        # New unified AI system
        self.visual_ai_solver = VisualAISolver(self.renderer, self.skin_manager)

        # Advanced mouse navigation system
        self.mouse_navigation = MouseNavigationSystem()

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

        # Reload keybindings and game settings at the start of each game loop
        self.custom_keybindings = self.config_manager.get_keybindings()
        self.move_delay = self.config_manager.get('game', 'movement_cooldown', 200)
        self.show_deadlocks = self.config_manager.get('game', 'show_deadlocks', True)
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
                        # Check if AI system handles this event first
                        ai_handled = self.visual_ai_solver.handle_events([event])

                        if not ai_handled:
                            # Add key to pressed keys set
                            self.keys_pressed.add(event.key)
                            self._handle_key_event(event)
                            self.last_move_time = current_time
                elif event.type == pygame.KEYUP:
                    # Remove key from pressed keys set
                    self.keys_pressed.discard(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Handle mouse clicks for navigation
                    self._handle_mouse_click(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    # Handle mouse button release for drag-drop
                    self._handle_mouse_release(event)
                elif event.type == pygame.MOUSEMOTION:
                    # Handle mouse movement for drag-drop and path updates
                    self._handle_mouse_motion(event)
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
                    config_manager.set_display_config(event.w, event.h)

            # Handle continuous movement
            if self.keys_pressed and current_time - self.last_move_time > self.move_delay:
                self._handle_continuous_movement()
                self.last_move_time = current_time

            # Update mouse navigation system
            self._update_mouse_navigation(current_time)

            # Render the current state
            if self.show_help:
                self.renderer.render_help(self.custom_keybindings)
            else:
                # Get current mouse position for interactive highlighting
                mouse_pos = pygame.mouse.get_pos()
                self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                         self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager,
                                         show_completion_message=True, mouse_pos=mouse_pos)

                # Render mouse navigation overlay
                self._render_mouse_navigation()

                # Update the display to show all rendered content
                pygame.display.flip()

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

                # Check if this key is already used in any custom keybinding
                if key_name not in self.custom_keybindings.values():
                    # Check if this key is bound to an action in the default layout
                    default_action = KEY_BINDINGS[self.keyboard_layout].get(key_name)

                    # Special case for 'a' key in AZERTY mode which is mapped to 'quit' by default
                    if self.keyboard_layout == AZERTY and key_name == 'a' and default_action == 'quit':
                        # Check if 'quit' is already remapped to a different key
                        if 'quit' in self.custom_keybindings:
                            # 'quit' is remapped, so don't use the default action for 'a'
                            default_action = None

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
                    # Reset deadlock detector for the reset level
                    self.deadlock_detector = None
                    self.deadlock_notification_shown = False
                    # Clear mouse navigation
                    self.mouse_navigation.clear_navigation()
                elif action == 'quit':
                    self._quit_game()
                elif action == 'next':
                    # Go to next level regardless of completion status
                    self._next_level()
                elif action == 'previous':
                    # Go to previous level
                    self._prev_level()
                elif action == 'undo':
                    # Undo the move in the game state
                    if self.level_manager.current_level.undo():
                        # Get previous sprite from history
                        # This will pop the current sprite and return the previous one
                        # When undoing multiple moves, this will return each previous sprite in reverse order
                        prev_sprite = self.skin_manager.get_previous_sprite()
                        prev_sprite_info = self.skin_manager.get_sprite_info(prev_sprite) if prev_sprite else "None"
                        print(f"UNDO: Restored to sprite: {prev_sprite_info}")
                    else:
                        print("UNDO: No moves to undo")
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
            player_sprite = self.skin_manager.get_player_sprite(advance_animation=True)
            sprite_info = self.skin_manager.get_sprite_info(player_sprite)
            print(f"MOVEMENT_COMPLETE: Advanced animation to sprite: {sprite_info}")
            print(f"MOVEMENT_DEBUG: Move #{self.skin_manager.move_counter - 1}, Direction: {direction}, State: {self.skin_manager.current_player_state}")

            # Check for deadlocks after the move
            if self.deadlock_detector is None:
                self.deadlock_detector = DeadlockDetector(self.level_manager.current_level)

            if self.deadlock_detector.is_deadlock() and not self.deadlock_notification_shown:
                # Only show deadlock notification if the setting is enabled
                if self.show_deadlocks:
                    # Render the current level state
                    mouse_pos = pygame.mouse.get_pos()
                    self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                             self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager,
                                             show_completion_message=False, mouse_pos=mouse_pos)
                    pygame.display.flip()

                    # Show deadlock notification
                    self._show_deadlock_notification()

                # Set the flag to indicate that the notification has been shown
                self.deadlock_notification_shown = True

        # Check if level is completed after the move
        if moved and self.level_manager.current_level_completed():
            # Render the completed level without showing completion message
            mouse_pos = pygame.mouse.get_pos()
            self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                     self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager,
                                     show_completion_message=False, mouse_pos=mouse_pos)
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
            # Reset deadlock detector for the new level
            self.deadlock_detector = None
            self.deadlock_notification_shown = False
            # Clear mouse navigation for new level
            self.mouse_navigation.clear_navigation()
        # If no more levels in collection, try next level file
        elif self.level_manager.has_next_level():
            self.level_manager.next_level()
            # Reset sprite history for the new level
            self.skin_manager.reset_sprite_history()
            # Reset deadlock detector for the new level
            self.deadlock_detector = None
            self.deadlock_notification_shown = False
            # Clear mouse navigation for new level
            self.mouse_navigation.clear_navigation()
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
            # Reset deadlock detector for the new level
            self.deadlock_detector = None
            self.deadlock_notification_shown = False
            # Clear mouse navigation for new level
            self.mouse_navigation.clear_navigation()
        # If no more levels in collection, try previous level file
        elif self.level_manager.has_prev_level():
            self.level_manager.prev_level()
            # Reset sprite history for the new level
            self.skin_manager.reset_sprite_history()
            # Reset deadlock detector for the new level
            self.deadlock_detector = None
            self.deadlock_notification_shown = False
            # Clear mouse navigation for new level
            self.mouse_navigation.clear_navigation()

    def _return_to_level_selector(self):
        """
        Return to the level selector.
        """
        self.running = False

    def _show_in_game_popup(self, title, message, timeout=3000):
        """
        Show a popup message directly on the game screen.

        Args:
            title (str): Title of the popup
            message (str): Message to display
            timeout (int, optional): Time in milliseconds before the popup disappears. 
                                    If None, waits for user input. Defaults to 3000.
        """
        # Clear the keys_pressed set to prevent automatic movement
        self.keys_pressed.clear()

        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.renderer.screen.get_width(), self.renderer.screen.get_height()))
        overlay.set_alpha(180)  # Semi-transparent
        overlay.fill((0, 0, 0))  # Black background
        self.renderer.screen.blit(overlay, (0, 0))

        # Create fonts
        title_font = pygame.font.Font(None, 36)
        message_font = pygame.font.Font(None, 24)
        instruction_font = pygame.font.Font(None, 20)

        # Create text surfaces
        title_surface = title_font.render(title, True, (255, 255, 255))  # White text
        message_surface = message_font.render(message, True, (255, 255, 255))  # White text
        instruction_surface = instruction_font.render("Appuyez sur une touche pour continuer", True, (200, 200, 200))  # Light gray text

        # Position text
        title_rect = title_surface.get_rect(center=(self.renderer.screen.get_width() // 2, 100))
        message_rect = message_surface.get_rect(center=(self.renderer.screen.get_width() // 2, 150))
        instruction_rect = instruction_surface.get_rect(center=(self.renderer.screen.get_width() // 2, 200))

        # Draw text
        self.renderer.screen.blit(title_surface, title_rect)
        self.renderer.screen.blit(message_surface, message_rect)
        self.renderer.screen.blit(instruction_surface, instruction_rect)

        # Update display
        pygame.display.flip()

        # Wait for timeout or user input
        start_time = pygame.time.get_ticks()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit_game()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False

            # Check if timeout has elapsed
            if timeout is not None and pygame.time.get_ticks() - start_time > timeout:
                waiting = False

            # Small delay to prevent CPU hogging
            pygame.time.wait(10)

    def _show_deadlock_notification(self):
        """
        Show a notification when a deadlock is detected.

        This method displays a popup informing the player that the last move has resulted in a deadlock,
        making the level unsolvable. The notification is purely informative and doesn't force any action.
        """
        # Show the deadlock notification using the in-game popup
        self._show_in_game_popup(
            "Deadlock Détecté!",
            "Le dernier coup rend le niveau infinissable."
        )

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
                # Reset deadlock detector for the reset level
                self.deadlock_detector = None
                self.deadlock_notification_shown = False
        else:
            # Return to level selection
            self._return_to_level_selector()

    def _solve_current_level(self):
        """
        Solve the current level using the new unified AI system with enhanced features.
        """
        if not self.level_manager.current_level:
            return

        # Don't solve if already solving
        if self.visual_ai_solver.is_busy():
            return

        # Show algorithm selection menu
        selected_algorithm = self._show_algorithm_selection_menu()
        if selected_algorithm is None:
            return  # User cancelled

        # Show initial solving message
        self._render_enhanced_solving_overlay("🤖 Analyzing level and preparing AI solver...")
        pygame.display.flip()

        # Enhanced progress callback for detailed analysis tracking
        def enhanced_analysis_callback(message):
            print(f"🧠 LEVEL_ANALYSIS: {message}")

        print("🚀 SOLVE_START: Début de l'analyse et résolution du niveau")

        try:
            # Use the new unified AI system to solve WITHOUT animation during solving
            result = self.visual_ai_solver.solve_level_visual(
                level=self.level_manager.current_level,
                algorithm=selected_algorithm,
                animate_immediately=False,  # Don't animate during solving
                progress_callback=enhanced_analysis_callback  # Enhanced callback for better tracking
            )

            if result['success']:
                # Now animate the solution after it's found
                self._animate_solution_after_solving(result['solve_result'])

                # Show completion statistics
                solve_info = self.visual_ai_solver.get_last_solve_info()
                if solve_info:
                    self._show_ai_completion_stats(solve_info)
            else:
                # Show enhanced failure message with AI insights
                self._show_ai_failure_message(selected_algorithm)

        except Exception as e:
            # Handle any errors gracefully
            error_message = f"AI Error: {str(e)}\nPress any key to continue..."
            self._render_enhanced_solving_overlay(error_message)
            pygame.display.flip()

            # Wait for user input
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                        waiting = False

    def _show_algorithm_selection_menu(self) -> Optional[Algorithm]:
        """
        Show algorithm selection menu and return selected algorithm using game's UI standards.

        Returns:
            Algorithm or None: Selected algorithm, None if auto-selection or cancelled
        """
        # Get recommendation for current level
        recommendation = self.visual_ai_solver.get_algorithm_recommendation(self.level_manager.current_level)

        # Create algorithm selection screen with game's color scheme
        screen = self.renderer.screen

        # Use consistent colors with the game's theme
        background_color = (240, 240, 240)  # Light gray like menu system
        text_color = (50, 50, 50)  # Dark gray for readability
        title_color = (70, 70, 150)  # Blue for title
        selected_color = (100, 150, 200)  # Blue for selection
        recommendation_color = (100, 180, 100)  # Green for recommendation

        # Responsive font sizing based on screen size
        base_dimension = min(screen.get_width(), screen.get_height())
        title_size = min(max(28, base_dimension // 20), 48)
        text_size = min(max(20, base_dimension // 30), 32)
        small_size = min(max(16, base_dimension // 40), 24)

        title_font = pygame.font.Font(None, title_size)
        text_font = pygame.font.Font(None, text_size)
        small_font = pygame.font.Font(None, small_size)

        # Algorithm options (None = auto-selection)
        algorithms = [None] + list(Algorithm)
        algorithm_names = ["🤖 Auto-Select (Recommended)"] + [f"🔧 {alg.value}" for alg in Algorithm]
        selected_index = 0

        # Button dimensions
        button_width = min(max(300, screen.get_width() // 3), 500)
        button_height = min(max(40, screen.get_height() // 20), 60)

        clock = pygame.time.Clock()

        while True:
            # Clear screen with game's background color
            screen.fill(background_color)

            # Title with shadow effect (like in menu system)
            title_text = "🧠 AI Algorithm Selection"

            # Draw shadow
            shadow_color = (50, 50, 100)
            shadow_offset = 2
            title_shadow = title_font.render(title_text, True, shadow_color)
            shadow_rect = title_shadow.get_rect(center=(screen.get_width() // 2 + shadow_offset, 80 + shadow_offset))
            screen.blit(title_shadow, shadow_rect)

            # Draw main title
            title_surface = title_font.render(title_text, True, title_color)
            title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 80))
            screen.blit(title_surface, title_rect)

            # Level analysis section
            y_pos = 140
            analysis_title = text_font.render("Level Analysis", True, title_color)
            analysis_rect = analysis_title.get_rect(center=(screen.get_width() // 2, y_pos))
            screen.blit(analysis_title, analysis_rect)

            y_pos += 35
            complexity_text = f"Complexity: {recommendation['complexity_category']} (Score: {recommendation['complexity_score']:.1f})"
            complexity_surface = small_font.render(complexity_text, True, text_color)
            complexity_rect = complexity_surface.get_rect(center=(screen.get_width() // 2, y_pos))
            screen.blit(complexity_surface, complexity_rect)

            # Recommended algorithm
            if recommendation:
                y_pos += 25
                rec_text = f"Recommended: {recommendation['recommended_algorithm'].value}"
                rec_surface = small_font.render(rec_text, True, recommendation_color)
                rec_rect = rec_surface.get_rect(center=(screen.get_width() // 2, y_pos))
                screen.blit(rec_surface, rec_rect)

            # Algorithm selection section
            y_pos += 60
            selection_title = text_font.render("Select Algorithm", True, title_color)
            selection_rect = selection_title.get_rect(center=(screen.get_width() // 2, y_pos))
            screen.blit(selection_title, selection_rect)

            # Algorithm options with button-like appearance
            y_start = y_pos + 50
            button_x = (screen.get_width() - button_width) // 2

            for i, name in enumerate(algorithm_names):
                button_y = y_start + i * (button_height + 10)

                # Button background
                if i == selected_index:
                    button_color = selected_color
                    text_display_color = (255, 255, 255)
                else:
                    button_color = (200, 200, 200)
                    text_display_color = text_color

                # Draw button with rounded corners
                pygame.draw.rect(screen, button_color,
                               (button_x, button_y, button_width, button_height), 0, 10)
                pygame.draw.rect(screen, (100, 100, 100),
                               (button_x, button_y, button_width, button_height), 2, 10)

                # Button text
                option_surface = small_font.render(name, True, text_display_color)
                option_rect = option_surface.get_rect(center=(button_x + button_width // 2, button_y + button_height // 2))
                screen.blit(option_surface, option_rect)

            # Instructions section
            instructions_y = screen.get_height() - 120
            instruction_title = text_font.render("Controls", True, title_color)
            instruction_title_rect = instruction_title.get_rect(center=(screen.get_width() // 2, instructions_y))
            screen.blit(instruction_title, instruction_title_rect)

            instructions = [
                "↑↓ Navigate | ENTER Select | ESC Cancel",
                "B - Run Algorithm Benchmark"
            ]

            for i, instruction in enumerate(instructions):
                inst_surface = small_font.render(instruction, True, text_color)
                inst_rect = inst_surface.get_rect(center=(screen.get_width() // 2, instructions_y + 30 + i * 20))
                screen.blit(inst_surface, inst_rect)

            pygame.display.flip()
            clock.tick(60)

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(algorithms)
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(algorithms)
                    elif event.key == pygame.K_RETURN:
                        return algorithms[selected_index]
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_b:
                        # Run benchmark
                        self._run_algorithm_benchmark()
                        return None

    def _run_algorithm_benchmark(self):
        """Run algorithm benchmark and show results."""
        def benchmark_progress(message):
            self.renderer.screen.fill((30, 30, 50))
            font = pygame.font.Font(None, 32)
            text = font.render("🔬 Running Algorithm Benchmark...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.renderer.screen.get_width() // 2, 200))
            self.renderer.screen.blit(text, text_rect)

            small_font = pygame.font.Font(None, 24)
            status = small_font.render(message, True, (200, 200, 200))
            status_rect = status.get_rect(center=(self.renderer.screen.get_width() // 2, 250))
            self.renderer.screen.blit(status, status_rect)

            pygame.display.flip()

        # Run benchmark
        benchmark_results = self.visual_ai_solver.benchmark_algorithms(
            self.level_manager.current_level,
            progress_callback=benchmark_progress
        )

        # Show results
        self._show_benchmark_results(benchmark_results)

    def _show_benchmark_results(self, results: Dict[str, Any]):
        """Show benchmark results screen."""
        screen = self.renderer.screen
        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 20)

        waiting = True
        while waiting:
            screen.fill((30, 30, 50))

            # Title
            title = font.render("🏆 Algorithm Benchmark Results", True, (255, 255, 255))
            title_rect = title.get_rect(center=(screen.get_width() // 2, 50))
            screen.blit(title, title_rect)

            # Level info
            level_info = results.get('level_info', {})
            info_text = f"Level: {level_info.get('width', 0)}x{level_info.get('height', 0)}, {level_info.get('boxes_count', 0)} boxes"
            info_surface = small_font.render(info_text, True, (200, 200, 200))
            info_rect = info_surface.get_rect(center=(screen.get_width() // 2, 80))
            screen.blit(info_surface, info_rect)

            # Results
            y_pos = 120
            algorithm_results = results.get('algorithm_results', {})

            for algorithm, result in algorithm_results.items():
                if result.get('success'):
                    moves = result.get('moves_count', 0)
                    time = result.get('solve_time', 0)
                    states = result.get('states_explored', 0)

                    # Color code based on performance
                    color = (100, 255, 100) if algorithm == results.get('best_algorithm') else (255, 255, 255)
                    if algorithm == results.get('fastest_algorithm'):
                        color = (100, 200, 255)

                    text = f"{algorithm}: {moves} moves, {time:.2f}s, {states:,} states"
                    surface = small_font.render(text, True, color)
                    rect = surface.get_rect(center=(screen.get_width() // 2, y_pos))
                    screen.blit(surface, rect)
                else:
                    text = f"{algorithm}: FAILED - {result.get('error', 'Unknown error')}"
                    surface = small_font.render(text, True, (255, 100, 100))
                    rect = surface.get_rect(center=(screen.get_width() // 2, y_pos))
                    screen.blit(surface, rect)

                y_pos += 25

            # Best algorithm highlight
            if results.get('best_algorithm'):
                y_pos += 20
                best_text = f"🏆 Best Solution: {results['best_algorithm']}"
                best_surface = small_font.render(best_text, True, (255, 215, 0))
                best_rect = best_surface.get_rect(center=(screen.get_width() // 2, y_pos))
                screen.blit(best_surface, best_rect)

            if results.get('fastest_algorithm'):
                y_pos += 25
                fastest_text = f"⚡ Fastest: {results['fastest_algorithm']}"
                fastest_surface = small_font.render(fastest_text, True, (100, 200, 255))
                fastest_rect = fastest_surface.get_rect(center=(screen.get_width() // 2, y_pos))
                screen.blit(fastest_surface, fastest_rect)

            # Instructions
            instruction = "Press any key to continue..."
            inst_surface = small_font.render(instruction, True, (150, 150, 150))
            inst_rect = inst_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50))
            screen.blit(inst_surface, inst_rect)

            pygame.display.flip()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False

    def _render_enhanced_solving_overlay(self, text):
        """
        Render an enhanced overlay with AI solving progress text.

        Args:
            text (str): Text to display.
        """
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.renderer.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.renderer.screen.blit(overlay, (0, 0))

        # Main text
        font = pygame.font.Font(None, 32)

        # Split text by lines for multi-line support
        lines = text.split('\n')
        y_offset = self.renderer.screen.get_height() // 2 - (len(lines) * 20)

        for line in lines:
            text_surface = font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(self.renderer.screen.get_width() // 2, y_offset))
            self.renderer.screen.blit(text_surface, text_rect)
            y_offset += 40

        # Add AI indicator
        ai_font = pygame.font.Font(None, 24)
        ai_text = "🤖 Enhanced AI System Active"
        ai_surface = ai_font.render(ai_text, True, (100, 255, 100))
        ai_rect = ai_surface.get_rect(center=(self.renderer.screen.get_width() // 2, y_offset + 20))
        self.renderer.screen.blit(ai_surface, ai_rect)

        # Control instructions
        instruction_font = pygame.font.Font(None, 20)
        instructions = [
            "SPACE: Pause/Resume | ESC: Stop | +/-: Speed | F1: Debug | F2: Metrics"
        ]

        for i, instruction in enumerate(instructions):
            instruction_surface = instruction_font.render(instruction, True, (180, 180, 180))
            instruction_rect = instruction_surface.get_rect(center=(self.renderer.screen.get_width() // 2, y_offset + 60 + i * 25))
            self.renderer.screen.blit(instruction_surface, instruction_rect)

    def _show_ai_completion_stats(self, solve_info: Dict[str, Any]):
        """Show AI completion statistics."""
        screen = self.renderer.screen
        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 22)

        # Create stats display
        waiting = True
        while waiting:
            screen.fill((20, 50, 20))  # Dark green background

            # Title
            title = font.render("🎉 AI Solution Complete!", True, (100, 255, 100))
            title_rect = title.get_rect(center=(screen.get_width() // 2, 60))
            screen.blit(title, title_rect)

            # Statistics
            stats_lines = [
                f"Algorithm Used: {solve_info.get('algorithm_used', 'Unknown')}",
                f"Moves: {solve_info.get('moves_count', 0)}",
                f"Solve Time: {solve_info.get('solve_time', 0):.2f} seconds",
                f"States Explored: {solve_info.get('states_explored', 0):,}",
                f"States Generated: {solve_info.get('states_generated', 0):,}",
                f"Deadlocks Avoided: {solve_info.get('deadlocks_pruned', 0)}",
                f"Memory Used: {solve_info.get('memory_peak', 0):,} states",
                f"Heuristic Calls: {solve_info.get('heuristic_calls', 0):,}"
            ]

            y_pos = 120
            for line in stats_lines:
                surface = small_font.render(line, True, (255, 255, 255))
                rect = surface.get_rect(center=(screen.get_width() // 2, y_pos))
                screen.blit(surface, rect)
                y_pos += 30

            # Performance analysis
            if solve_info.get('states_explored', 0) > 0 and solve_info.get('solve_time', 0) > 0:
                efficiency = solve_info['states_explored'] / max(solve_info.get('states_generated', 1), 1)
                speed = solve_info['states_explored'] / solve_info['solve_time']

                y_pos += 20
                perf_lines = [
                    f"Search Efficiency: {efficiency:.1%}",
                    f"Search Speed: {speed:,.0f} states/sec"
                ]

                for line in perf_lines:
                    surface = small_font.render(line, True, (200, 255, 200))
                    rect = surface.get_rect(center=(screen.get_width() // 2, y_pos))
                    screen.blit(surface, rect)
                    y_pos += 25

            # Instructions
            instruction = "Press any key to continue..."
            inst_surface = small_font.render(instruction, True, (150, 255, 150))
            inst_rect = inst_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50))
            screen.blit(inst_surface, inst_rect)

            pygame.display.flip()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False

    def _show_ai_failure_message(self, algorithm: Optional[Algorithm]):
        """Show enhanced AI failure message with insights."""
        screen = self.renderer.screen
        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 22)

        # Get level complexity analysis
        recommendation = self.visual_ai_solver.get_algorithm_recommendation(self.level_manager.current_level)

        waiting = True
        while waiting:
            screen.fill((50, 20, 20))  # Dark red background

            # Title
            title = font.render("🤔 AI Analysis Complete", True, (255, 100, 100))
            title_rect = title.get_rect(center=(screen.get_width() // 2, 60))
            screen.blit(title, title_rect)

            # Level analysis
            level = self.level_manager.current_level
            analysis_lines = [
                f"Level Size: {level.width}x{level.height} ({level.width * level.height} cells)",
                f"Boxes: {len(level.boxes)} | Targets: {len(level.targets)}",
                f"Complexity: {recommendation['complexity_category']} (Score: {recommendation['complexity_score']:.1f})",
                f"Algorithm Used: {algorithm.value if algorithm else 'Auto-Selected'}"
            ]

            y_pos = 120
            for line in analysis_lines:
                surface = small_font.render(line, True, (255, 255, 255))
                rect = surface.get_rect(center=(screen.get_width() // 2, y_pos))
                screen.blit(surface, rect)
                y_pos += 25

            # Determine failure reason and suggestions
            complexity_score = recommendation['complexity_score']
            box_count = len(level.boxes)
            level_size = level.width * level.height

            y_pos += 20
            if complexity_score > 300:
                reason = "Level complexity exceeds AI capabilities"
                suggestions = [
                    "• Try a simpler level first",
                    "• This level may require advanced human strategies",
                    "• Consider using manual solving techniques"
                ]
            elif level_size > 200:
                reason = "Level size may cause memory limitations"
                suggestions = [
                    "• Large levels require significant computation",
                    "• Try smaller levels for better AI performance",
                    "• AI works best on focused puzzle areas"
                ]
            elif box_count > 10:
                reason = "High number of boxes increases search complexity"
                suggestions = [
                    "• Many boxes create exponential search space",
                    "• AI performs better with fewer moving pieces",
                    "• Consider levels with 3-8 boxes for optimal results"
                ]
            else:
                reason = "Level may be unsolvable or require unique strategy"
                suggestions = [
                    "• Some levels have no solution",
                    "• AI may need more time for complex patterns",
                    "• Try different algorithm selections"
                ]

            # Display reason
            reason_surface = small_font.render(f"Analysis: {reason}", True, (255, 200, 100))
            reason_rect = reason_surface.get_rect(center=(screen.get_width() // 2, y_pos))
            screen.blit(reason_surface, reason_rect)
            y_pos += 40

            # Display suggestions
            suggestion_title = small_font.render("Suggestions:", True, (200, 200, 255))
            suggestion_rect = suggestion_title.get_rect(center=(screen.get_width() // 2, y_pos))
            screen.blit(suggestion_title, suggestion_rect)
            y_pos += 25

            for suggestion in suggestions:
                surface = small_font.render(suggestion, True, (180, 180, 180))
                rect = surface.get_rect(center=(screen.get_width() // 2, y_pos))
                screen.blit(surface, rect)
                y_pos += 22

            # Instructions
            instruction = "Press any key to continue..."
            inst_surface = small_font.render(instruction, True, (255, 150, 150))
            inst_rect = inst_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50))
            screen.blit(inst_surface, inst_rect)

            pygame.display.flip()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False

    def _render_solving_overlay(self, text):
        """
        Render a basic overlay with solving progress text (legacy method).

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

    def _animate_solution_after_solving(self, solve_result):
        """
        Animate the solution after it has been found.

        Args:
            solve_result: The SolveResult containing the solution
        """
        if not solve_result.success or not solve_result.solution_data:
            return

        moves = solve_result.solution_data.moves
        if not moves:
            return

        # Reset level to initial state
        self.level_manager.current_level.reset()

        # Show animation start message
        total_moves = len(moves)
        self._render_enhanced_solving_overlay(f"🎬 Animating solution: {total_moves} moves")
        pygame.display.flip()
        pygame.time.wait(1000)  # Give user time to read

        # Animate each move
        for i, move in enumerate(moves):
            # Check for user input to skip animation
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Skip to end
                        self._execute_remaining_moves(moves[i:])
                        return
                    elif event.key == pygame.K_ESCAPE:
                        return
                elif event.type == pygame.QUIT:
                    return

            # Execute the move
            success = self._execute_ai_move(move)

            # Render current state
            mouse_pos = pygame.mouse.get_pos()
            self.renderer.render_level(
                self.level_manager.current_level,
                self.level_manager,
                self.show_grid,
                self.zoom_level,
                self.scroll_x,
                self.scroll_y,
                self.skin_manager,
                show_completion_message=False,
                mouse_pos=mouse_pos
            )

            # Show progress overlay
            progress = (i + 1) / total_moves * 100
            overlay_text = f"🤖 AI Solution: Move {i+1}/{total_moves} ({progress:.1f}%)\n"
            overlay_text += f"Direction: {move} -> {'✅' if success else '❌'}\n"
            overlay_text += "SPACE: Skip animation | ESC: Stop"

            self._render_enhanced_solving_overlay(overlay_text)
            pygame.display.flip()

            # Animation delay
            pygame.time.wait(300)  # 300ms per move

            # Check if level is completed
            if self.level_manager.current_level.is_completed():
                break

    def _execute_ai_move(self, move: str) -> bool:
        """Execute a move from the AI solution."""
        direction_map = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0)
        }

        if move in direction_map:
            dx, dy = direction_map[move]
            return self.level_manager.current_level.move(dx, dy)

        return False

    def _execute_remaining_moves(self, remaining_moves):
        """Execute all remaining moves instantly."""
        for move in remaining_moves:
            self._execute_ai_move(move)
            if self.level_manager.current_level.is_completed():
                break

        # Render final state
        mouse_pos = pygame.mouse.get_pos()
        self.renderer.render_level(
            self.level_manager.current_level,
            self.level_manager,
            self.show_grid,
            self.zoom_level,
            self.scroll_x,
            self.scroll_y,
            self.skin_manager,
            show_completion_message=False,
            mouse_pos=mouse_pos
        )
        pygame.display.flip()

    def _handle_mouse_click(self, event):
        """
        Handle mouse click events for navigation.

        Args:
            event: Pygame mouse button down event.
        """
        if not self.level_manager.current_level or self.show_help:
            return

        # Update mouse navigation system with current level
        self.mouse_navigation.set_level(self.level_manager.current_level)

        # Calculate map area parameters
        map_area_x, map_area_y, cell_size = self._get_map_area_params()

        # Handle left click for navigation
        if event.button == 1:  # Left click
            # Check if starting a drag operation
            if self.mouse_navigation.handle_mouse_drag_start(
                event.pos, map_area_x, map_area_y, cell_size,
                self.scroll_x, self.scroll_y
            ):
                return  # Drag started, don't process as navigation click

            # Handle navigation click
            self.mouse_navigation.handle_mouse_click(
                event.pos, event.button, map_area_x, map_area_y, cell_size,
                self.scroll_x, self.scroll_y
            )

    def _handle_mouse_release(self, event):
        """
        Handle mouse button release events.

        Args:
            event: Pygame mouse button up event.
        """
        if event.button == 1:  # Left click release
            self.mouse_navigation.handle_mouse_drag_end()

    def _handle_mouse_motion(self, event):
        """
        Handle mouse motion events for drag operations.

        Args:
            event: Pygame mouse motion event.
        """
        if not self.level_manager.current_level or self.show_help:
            return

        # Calculate map area parameters
        map_area_x, map_area_y, cell_size = self._get_map_area_params()

        # Handle drag motion
        self.mouse_navigation.handle_mouse_drag(
            event.pos, map_area_x, map_area_y, cell_size,
            self.scroll_x, self.scroll_y
        )

    def _update_mouse_navigation(self, current_time):
        """
        Update the mouse navigation system.

        Args:
            current_time: Current time in milliseconds.
        """
        if not self.level_manager.current_level or self.show_help:
            return

        # Update mouse navigation with current level
        self.mouse_navigation.set_level(self.level_manager.current_level)

        # Update movement speed from configuration
        self.mouse_navigation.update_movement_speed()

        # Get current mouse position and update navigation
        mouse_pos = pygame.mouse.get_pos()
        map_area_x, map_area_y, cell_size = self._get_map_area_params()

        self.mouse_navigation.update_mouse_position(
            mouse_pos, map_area_x, map_area_y, cell_size,
            self.scroll_x, self.scroll_y
        )

        # Update automatic movement
        if self.mouse_navigation.update_movement(current_time):
            # A movement was executed, get the direction and update sprite animation
            direction = self.mouse_navigation.last_movement_direction
            if direction:
                # Update player state in skin manager for proper animation
                player_x, player_y = self.level_manager.current_level.player_pos
                new_x, new_y = player_x, player_y

                # Calculate new position based on direction
                if direction == 'up':
                    new_y -= 1
                elif direction == 'down':
                    new_y += 1
                elif direction == 'left':
                    new_x -= 1
                elif direction == 'right':
                    new_x += 1

                # Check if move would push a box
                is_pushing = (new_x, new_y) in self.level_manager.current_level.boxes
                is_blocked = False  # Movement already succeeded

                # Update player state in skin manager
                self.skin_manager.update_player_state(direction, is_pushing, is_blocked)

                # Advance animation
                player_sprite = self.skin_manager.get_player_sprite(advance_animation=True)
                sprite_info = self.skin_manager.get_sprite_info(player_sprite)
                print(f"MOUSE_NAVIGATION: Advanced animation to sprite: {sprite_info}")

            # Check for level completion
            if self.level_manager.current_level.is_completed():
                # Clear navigation when level is completed
                self.mouse_navigation.clear_navigation()

                # Show level completion screen
                mouse_pos = pygame.mouse.get_pos()
                self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                         self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager,
                                         show_completion_message=False, mouse_pos=mouse_pos)
                pygame.display.flip()
                pygame.time.wait(1000)
                self._show_level_completion_screen()

    def _render_mouse_navigation(self):
        """Render the mouse navigation overlay."""
        if not self.level_manager.current_level or self.show_help:
            return

        # Calculate map area parameters
        map_area_x, map_area_y, cell_size = self._get_map_area_params()

        # Render navigation guideline and highlights
        self.mouse_navigation.render_navigation(
            self.renderer.screen, map_area_x, map_area_y, cell_size,
            self.scroll_x, self.scroll_y
        )

    def _get_map_area_params(self):
        """
        Calculate map area parameters for mouse navigation.

        Returns:
            Tuple of (map_area_x, map_area_y, cell_size_scaled).
        """
        level = self.level_manager.current_level
        current_screen_width, current_screen_height = self.renderer.screen.get_size()

        # Calculate base window size needed for the level
        base_cell_size = CELL_SIZE * self.zoom_level
        base_window_width = level.width * base_cell_size
        base_window_height = level.height * base_cell_size + 100  # Extra space for stats

        # Check if we're in a resized window (including fullscreen)
        if current_screen_width > base_window_width or current_screen_height > base_window_height:
            # We're in a larger window, calculate scaling
            width_scale = current_screen_width / base_window_width
            height_scale = current_screen_height / base_window_height
            scale_factor = min(width_scale, height_scale, self.zoom_level) * 0.9  # Use 90% of available space

            # Calculate centered position with scroll offset
            offset_x = (current_screen_width - (base_window_width * scale_factor / self.zoom_level)) // 2 + self.scroll_x
            offset_y = (current_screen_height - (base_window_height * scale_factor / self.zoom_level)) // 2 + self.scroll_y
        else:
            # We're in a normal window, use zoom level directly
            if base_window_width <= current_screen_width and base_window_height <= current_screen_height:
                scale_factor = self.zoom_level
                offset_x = (current_screen_width - base_window_width) // 2 + self.scroll_x
                offset_y = (current_screen_height - base_window_height) // 2 + self.scroll_y
            else:
                # Need to fit in window
                width_scale = current_screen_width / base_window_width
                height_scale = (current_screen_height - 100) / (base_window_height - 100)
                scale_factor = min(width_scale, height_scale) * 0.9
                offset_x = (current_screen_width - (level.width * CELL_SIZE * scale_factor)) // 2 + self.scroll_x
                offset_y = (current_screen_height - (level.height * CELL_SIZE * scale_factor + 100)) // 2 + self.scroll_y

        cell_size_scaled = int(CELL_SIZE * scale_factor)

        return int(offset_x), int(offset_y), cell_size_scaled

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
