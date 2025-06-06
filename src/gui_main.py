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


class GUIGame(Game):
    """
    GUI version of the Sokoban game.
    
    This class extends the base Game class with GUI-specific functionality.
    """
    
    def __init__(self, levels_dir='levels', keyboard_layout=DEFAULT_KEYBOARD, skin_manager=None):
        """
        Initialize the GUI version of the Sokoban game.
        
        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            keyboard_layout (str, optional): Keyboard layout to use ('qwerty' or 'azerty').
                                           Defaults to DEFAULT_KEYBOARD.
            skin_manager (EnhancedSkinManager, optional): Existing skin manager to use.
                                                         If None, creates a new one.
        """
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
        self.move_delay = 150  # milliseconds between moves when holding key
        self.initial_move_delay = 300  # milliseconds before starting continuous movement
    
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
            
            # Handle continuous movement
            if self.keys_pressed and current_time - self.last_move_time > self.move_delay:
                self._handle_continuous_movement()
                self.last_move_time = current_time
            
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
        else:
            # Check against the current keyboard layout bindings
            action = KEY_BINDINGS[self.keyboard_layout].get(key_name)
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
                elif action == 'quit':
                    self._quit_game()
                elif action == 'next':
                    if self.level_manager.current_level_completed():
                        self._next_level()
                    else:
                        # If not completed, try to go to next level in collection
                        if self.level_manager.has_next_level_in_collection():
                            self.level_manager.next_level_in_collection()
                elif action == 'previous':
                    self._prev_level()
                elif action == 'undo':
                    self.level_manager.current_level.undo()
                elif action == 'help':
                    self.show_help = True
                elif action == 'grid':
                    self.show_grid = not self.show_grid
    
    def _handle_continuous_movement(self):
        """
        Handle continuous movement when keys are held down.
        """
        if self.show_help:
            return
        
        # Check for movement keys
        movement_keys = {
            pygame.K_UP: 'up',
            pygame.K_DOWN: 'down',
            pygame.K_LEFT: 'left',
            pygame.K_RIGHT: 'right',
            pygame.K_w: 'up',
            pygame.K_s: 'down',
            pygame.K_a: 'left',
            pygame.K_d: 'right'
        }
        
        for key in self.keys_pressed:
            if key in movement_keys:
                self._handle_movement(movement_keys[key])
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
        # If no more levels in collection, try next level file
        elif self.level_manager.has_next_level():
            self.level_manager.next_level()
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
        # If no more levels in collection, try previous level file
        elif self.level_manager.has_prev_level():
            self.level_manager.prev_level()
    
    def _return_to_level_selector(self):
        """
        Return to the level selector.
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