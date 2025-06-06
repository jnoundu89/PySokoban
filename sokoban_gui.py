#!/usr/bin/env python3
"""
Sokoban Game (GUI Version)

A Python implementation of the classic Sokoban puzzle game with a graphical user interface.
This is the main module that starts the game with a GUI and handles user input.
"""

import os
import sys
import pygame
from src.core.constants import KEY_BINDINGS, QWERTY, AZERTY, DEFAULT_KEYBOARD
from src.core.level import Level
from src.level_management.level_manager import LevelManager
from src.renderers.gui_renderer import GUIRenderer


class SokobanGUIGame:
    """
    Main class for the Sokoban game with GUI.
    
    This class is responsible for initializing the game components,
    handling user input, and managing the game loop.
    """
    
    def __init__(self, levels_dir='levels', keyboard_layout=DEFAULT_KEYBOARD):
        """
        Initialize the Sokoban GUI game.
        
        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           Defaults to DEFAULT_KEYBOARD.
        """
        self.level_manager = LevelManager(levels_dir)
        self.renderer = GUIRenderer()
        
        # Enhanced skin manager for directional sprites
        from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
        self.skin_manager = EnhancedSkinManager()
        self.running = False
        self.show_help = False
        self.show_grid = False  # Grid toggle functionality
        self.keyboard_layout = keyboard_layout
        
        # Load config manager for movement cooldown
        from src.core.config_manager import get_config_manager
        self.config_manager = get_config_manager()
        
        # Movement cooldown system
        self.movement_cooldown = self.config_manager.get('game', 'movement_cooldown', 200)
        self.last_movement_time = 0
        self.held_keys = set()  # Track which keys are currently held down
        
        # Zoom and scroll for better level viewing
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        self.scroll_x = 0
        self.scroll_y = 0
        
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
                        # Add key to held keys set
                        self.held_keys.add(event.key)
                        self._handle_key_event(event)
                elif event.type == pygame.KEYUP:
                    # Remove key from held keys set
                    self.held_keys.discard(event.key)
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
            
            # Handle held keys with cooldown (for continuous movement)
            if current_time - self.last_movement_time >= self.movement_cooldown:
                self._handle_held_keys(current_time)
            
            # Render the current state
            if self.show_help:
                self.renderer.render_help()
            else:
                self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                         self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager)
            
            # Cap the frame rate
            clock.tick(60)
    
    def _handle_key_event(self, event):
        """
        Handle keyboard events (immediate response for first press).
        
        Args:
            event: Pygame key event.
        """
        # If help screen is showing, any key dismisses it
        if self.show_help:
            self.show_help = False
            return
        
        # Refresh movement cooldown from config in case it was changed
        self.movement_cooldown = self.config_manager.get('game', 'movement_cooldown', 200)
        
        # Get the key name
        key_name = pygame.key.name(event.key)
        
        # Check for Escape key to return to level selector
        if key_name == 'escape':
            self._return_to_level_selector()
            return
        
        # First check arrow keys (which work regardless of keyboard layout)
        if key_name == 'up':
            self._handle_movement('up', immediate=True)
        elif key_name == 'down':
            self._handle_movement('down', immediate=True)
        elif key_name == 'left':
            self._handle_movement('left', immediate=True)
        elif key_name == 'right':
            self._handle_movement('right', immediate=True)
        else:
            # Check against the current keyboard layout bindings
            action = KEY_BINDINGS[self.keyboard_layout].get(key_name)
            if action:
                if action == 'up':
                    self._handle_movement('up', immediate=True)
                elif action == 'down':
                    self._handle_movement('down', immediate=True)
                elif action == 'left':
                    self._handle_movement('left', immediate=True)
                elif action == 'right':
                    self._handle_movement('right', immediate=True)
                elif action == 'reset':
                    self.level_manager.reset_current_level()
                elif action == 'quit':
                    self._quit_game()
                elif action == 'next' and self.level_manager.current_level_completed():
                    self._return_to_level_selector()
                elif action == 'previous':
                    self._prev_level()
                elif action == 'undo':
                    self.level_manager.current_level.undo()
                elif action == 'help':
                    self.show_help = True
                elif action == 'grid':
                    self.show_grid = not self.show_grid
    
    def _handle_held_keys(self, current_time):
        """
        Handle keys that are being held down (with cooldown for continuous movement).
        
        Args:
            current_time: Current time in milliseconds.
        """
        if not self.held_keys:
            return
            
        # Check for movement keys in held keys
        movement_keys = []
        
        # Check arrow keys
        if pygame.K_UP in self.held_keys:
            movement_keys.append('up')
        if pygame.K_DOWN in self.held_keys:
            movement_keys.append('down')
        if pygame.K_LEFT in self.held_keys:
            movement_keys.append('left')
        if pygame.K_RIGHT in self.held_keys:
            movement_keys.append('right')
        
        # Check keyboard layout specific keys
        for key in self.held_keys:
            key_name = pygame.key.name(key)
            action = KEY_BINDINGS[self.keyboard_layout].get(key_name)
            if action in ['up', 'down', 'left', 'right'] and action not in movement_keys:
                movement_keys.append(action)
        
        # If we have movement keys held, execute the first one found
        if movement_keys:
            self._handle_movement(movement_keys[0], immediate=False)
    
    def _handle_movement(self, direction, immediate=False):
        """
        Handle player movement with cooldown control.
        
        Args:
            direction (str): Direction to move ('up', 'down', 'left', 'right').
            immediate (bool): Whether this is an immediate response (first key press) or continuous movement.
        """
        current_time = pygame.time.get_ticks()
        
        # For immediate movements (first key press), allow without cooldown check
        # For continuous movements, check cooldown
        if not immediate and current_time - self.last_movement_time < self.movement_cooldown:
            return
        
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
        
        # Update last movement time only if the move was successful
        if moved:
            self.last_movement_time = current_time
        
        # Check if level is completed after the move
        if moved and self.level_manager.current_level_completed():
            # Render the completed level
            self.renderer.render_level(self.level_manager.current_level, self.level_manager,
                                     self.show_grid, self.zoom_level, self.scroll_x, self.scroll_y, self.skin_manager)
            pygame.display.flip()
            
            # Wait for a moment
            pygame.time.wait(1000)
            
            # Level completed - return to level selector
            self._return_to_level_selector()
    
    def _next_level(self):
        """
        Load the next level.
        """
        if not self.level_manager.next_level():
            # No more levels - return to level selector
            self._return_to_level_selector()
    
    def _prev_level(self):
        """
        Load the previous level.
        """
        if not self.level_manager.prev_level():
            # Already at the first level
            pass
    
    def _return_to_level_selector(self):
        """
        Return to the level selector.
        """
        self.running = False
    
    def _return_to_menu(self):
        """
        Return to the main menu.
        """
        self.running = False
    
    def _quit_game(self):
        """
        Quit the game.
        """
        self.running = False
        self.renderer.cleanup()
        sys.exit(0)


def main():
    """
    Main function to run the Sokoban GUI game.
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
    game = SokobanGUIGame(levels_dir, keyboard_layout)
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