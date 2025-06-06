#!/usr/bin/env python3
"""
Enhanced Sokoban Game

This module provides an enhanced version of the Sokoban game with additional features:
- Menu system (hub)
- Graphical level editor
- Skin/sprite system
- Level validation
- Live testing of levels
"""

import os
import sys
import pygame
from src.core.constants import TITLE, CELL_SIZE
from src.core.level import Level
from src.level_management.level_manager import LevelManager
from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
from src.ui.menu_system import MenuSystem
from src.editors.enhanced_level_editor import EnhancedLevelEditor
from src.gui_main import GUIGame

# Import for window maximization on Windows
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes


class EnhancedSokoban:
    """
    Enhanced Sokoban game with additional features.
    
    This class integrates all the enhanced features into a single game:
    - Menu system (hub)
    - Graphical level editor
    - Skin/sprite system
    - Level validation
    - Live testing of levels
    """
    
    def __init__(self, levels_dir='levels'):
        """
        Initialize the enhanced Sokoban game.
        
        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
        """
        pygame.init()
        
        # Initialize window - start maximized
        self.fullscreen = False
        # Create initial window
        self.screen_width = 1024
        self.screen_height = 768
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        
        # Maximize the window using OS-specific method
        self._maximize_window()
        
        # Get actual screen size after maximizing
        self.screen_width, self.screen_height = self.screen.get_size()
        
        # Initialize managers
        self.levels_dir = levels_dir
        self.level_manager = LevelManager(levels_dir)
        self.skin_manager = EnhancedSkinManager()
        
        # Check if levels directory exists, create it if not
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)
            
        # Game state
        self.running = False
        self.current_state = 'menu'  # 'menu', 'playing', 'editor'
        
        # Create components
        self.menu_system = MenuSystem(self.screen, self.screen_width, self.screen_height, levels_dir, self.skin_manager)
        self.game = GUIGame(levels_dir, skin_manager=self.skin_manager)
        self.editor = EnhancedLevelEditor(levels_dir, screen=self.screen)
        
        # Set up fullscreen toggle key handler
        self.key_handlers = {
            pygame.K_F11: self.toggle_fullscreen,
            pygame.K_ESCAPE: self.exit_fullscreen_if_active
        }
        
        # Set up menu actions
        self._setup_menu_actions()
        
        # Update all components with the maximized screen size
        self._update_components_screen_size()
        
    def start(self):
        """Start the enhanced Sokoban game."""
        self.running = True
        print("EnhancedSokoban start method called")
        
        while self.running:
            print(f"Current state: {self.current_state}")
            if self.current_state == 'menu':
                print("Running menu")
                self._run_menu()
            elif self.current_state == 'playing':
                print("Running game")
                self._run_game()
            elif self.current_state == 'editor':
                print("Running editor")
                self._run_editor()
            else:
                print(f"Unknown state: {self.current_state}")
                self.running = False
                
        print("EnhancedSokoban main loop exited")
        pygame.quit()
        
    def _run_menu(self):
        """Run the menu system."""
        print("_run_menu method called")
        self.menu_system.running = True
        print(f"Menu system running set to True: {self.menu_system.running}")
        
        clock = pygame.time.Clock()
        loop_count = 0
        
        while self.menu_system.running and self.running:
            loop_count += 1
            if loop_count == 1:
                print(f"Entering menu loop, running: {self.menu_system.running}")
            
            # Handle events
            events = pygame.event.get()
            if loop_count <= 5:  # Debug first few loops
                print(f"Loop {loop_count}: Got {len(events)} events")
            
            for event in events:
                if event.type == pygame.QUIT:
                    print("QUIT event received")
                    self.menu_system.running = False
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                    self._update_components_screen_size()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_ESCAPE and self.fullscreen:
                        self.exit_fullscreen_if_active()
                    elif event.key == pygame.K_ESCAPE and self.menu_system.current_state != 'main':
                        self.menu_system._change_state('main')
                
                # Handle button events
                active_buttons = []
                if self.menu_system.current_state == 'main':
                    active_buttons = self.menu_system.main_menu_buttons
                elif self.menu_system.current_state == 'play':
                    active_buttons = self.menu_system.play_menu_buttons
                elif self.menu_system.current_state == 'editor':
                    active_buttons = self.menu_system.editor_menu_buttons
                elif self.menu_system.current_state == 'settings':
                    active_buttons = self.menu_system.settings_menu_buttons
                elif self.menu_system.current_state == 'skins':
                    active_buttons = self.menu_system.skins_menu_buttons
                elif self.menu_system.current_state == 'credits':
                    active_buttons = self.menu_system.credits_menu_buttons
                
                for button in active_buttons:
                    button.handle_event(event)
            
            # Update current state
            try:
                self.menu_system.states[self.menu_system.current_state]()
            except Exception as e:
                print(f"Error in menu state update: {e}")
                break
            
            # Cap the frame rate
            clock.tick(60)
            
            # Check if running status changed
            if loop_count <= 5:
                print(f"End of loop {loop_count}, running: {self.menu_system.running}")
        
        print(f"Menu system loop completed after {loop_count} iterations")
        print(f"Final menu_system.running: {self.menu_system.running}")
        print(f"Final self.running: {self.running}")
        
        # Check if we're transitioning to another state or exiting the game
        if not self.menu_system.running and self.current_state == 'menu':
            # Check if a level was selected for playing
            if self.menu_system.current_state == 'start_game' and (self.menu_system.selected_level_info or self.menu_system.selected_level_path):
                if self.menu_system.selected_level_info:
                    print(f"Starting game with selected level: {self.menu_system.selected_level_info['title']}")
                else:
                    print(f"Starting game with selected level: {self.menu_system.selected_level_path}")
                self.current_state = 'playing'
                # Reset menu state for next time
                self.menu_system.current_state = 'main'
            else:
                print("Menu system running is False and still in menu state, exiting game")
                self.running = False
        else:
            print(f"Transitioning to state: {self.current_state}")
            
    def _run_game(self):
        """Run the game."""
        # If a specific level was selected, load it
        if self.menu_system.selected_level_info:
            level_info = self.menu_system.selected_level_info
            
            if level_info['type'] == 'collection_level':
                # Load a specific level from a collection
                try:
                    from src.level_management.level_collection_parser import LevelCollectionParser
                    collection = LevelCollectionParser.parse_file(level_info['collection_file'])
                    level_title, level = collection.get_level(level_info['level_index'])
                    
                    # Set metadata
                    level.title = level_title
                    level.description = collection.description
                    level.author = collection.author
                    
                    # Set as current level
                    self.game.level_manager.current_level = level
                    self.game.level_manager.current_level_index = -1  # Custom level
                    
                    print(f"Loaded collection level: {level_info['title']}")
                except Exception as e:
                    print(f"Failed to load collection level: {e}")
                    # Fall back to first level
                    self.game.level_manager.load_level(0)
            
            elif level_info['type'] == 'single_level':
                # Load a single level file
                try:
                    from src.core.level import Level
                    self.game.level_manager.current_level = Level(level_file=level_info['file_path'])
                    self.game.level_manager.current_level_index = -1  # Custom level
                    print(f"Loaded single level: {level_info['title']}")
                except Exception as e:
                    print(f"Failed to load single level: {e}")
                    # Fall back to first level
                    self.game.level_manager.load_level(0)
            
            # Clear the selected level info
            self.menu_system.selected_level_info = None
        
        # Legacy support for old selected_level_path
        elif self.menu_system.selected_level_path:
            # Load the specific level (legacy)
            level_index = -1
            if self.menu_system.selected_level_path in self.game.level_manager.level_files:
                level_index = self.game.level_manager.level_files.index(self.menu_system.selected_level_path)
            
            if level_index >= 0:
                self.game.level_manager.load_level(level_index)
            else:
                # If level not found in the list, try to load it directly
                try:
                    from src.core.level import Level
                    self.game.level_manager.current_level = Level(level_file=self.menu_system.selected_level_path)
                    self.game.level_manager.current_level_index = -1  # Indicate it's a custom level
                except Exception as e:
                    print(f"Failed to load selected level: {e}")
                    # Fall back to first level
                    self.game.level_manager.load_level(0)
            
            # Clear the selected level path
            self.menu_system.selected_level_path = None
        
        self.game.running = True
        self.game.game_loop()
        
        # When game is closed, return to level selector (play menu)
        self.current_state = 'menu'
        self.menu_system.current_state = 'play'
        
    def _run_editor(self):
        """Run the level editor."""
        try:
            print("Starting level editor...")
            self.editor.running = True
            print("Editor running flag set to True")
            self.editor.start()
            print("Editor start method completed")
            
            # When editor is closed, return to menu
            self.current_state = 'menu'
        except Exception as e:
            print(f"Error in level editor: {e}")
            import traceback
            traceback.print_exc()
            # Return to menu on error
            self.current_state = 'menu'
        
    def _start_game(self):
        """Start the game."""
        self.current_state = 'playing'
        self.menu_system.running = False
        
    def _show_level_selector(self):
        """Show the level selector."""
        self.menu_system._change_state('play')
        
    def _start_editor(self):
        """Start the level editor."""
        print("_start_editor method called")
        try:
            self.current_state = 'editor'
            print("Current state set to 'editor'")
            self.menu_system.running = False
            print("Menu system running set to False")
        except Exception as e:
            print(f"Error in _start_editor: {e}")
            import traceback
            traceback.print_exc()
        
    def _show_settings(self):
        """Show the settings menu."""
        # For now, just change the menu state
        self.menu_system._change_state('settings')
        
    def _show_skins(self):
        """Show the skins menu."""
        # For now, just change the menu state
        self.menu_system._change_state('skins')
        
    def _show_credits(self):
        """Show the credits menu."""
        # For now, just change the menu state
        self.menu_system._change_state('credits')
        
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            # Store current window size before going fullscreen
            self.windowed_size = (self.screen_width, self.screen_height)
            # Switch to fullscreen mode
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.screen_width, self.screen_height = self.screen.get_size()
        else:
            # Return to windowed mode with previous size
            self.screen_width, self.screen_height = self.windowed_size
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        
        # Update components with new screen size
        self._update_components_screen_size()
        
    def exit_fullscreen_if_active(self):
        """Exit fullscreen mode if currently active."""
        if self.fullscreen:
            self.toggle_fullscreen()
    
    def _update_components_screen_size(self):
        """Update all components with the new screen size."""
        # Update menu system
        self.menu_system.screen_width = self.screen_width
        self.menu_system.screen_height = self.screen_height
        self.menu_system.screen = self.screen
        if hasattr(self.menu_system, '_recreate_all_buttons'): # Check if method exists from previous step
            self.menu_system._recreate_all_buttons()
            # Re-setup menu actions after recreating buttons
            self._setup_menu_actions()
        else: # Fallback if the method name was different or apply_diff failed more severely
            self.menu_system._create_main_menu_buttons() # Attempt old method
            self._setup_menu_actions()
        
        # Update editor
        self.editor.screen = self.screen
        self.editor.screen_width = self.screen_width
        self.editor.screen_height = self.screen_height
        
        # Update game renderer if needed
        if hasattr(self.game, 'renderer'):
            self.game.renderer.window_size = (self.screen_width, self.screen_height)
            self.game.renderer.screen = self.screen
    
    def _setup_menu_actions(self):
        """Set up the actions for menu buttons."""
        if len(self.menu_system.main_menu_buttons) >= 6:
            self.menu_system.main_menu_buttons[0].action = self._show_level_selector  # Play Game
            self.menu_system.main_menu_buttons[1].action = self._start_editor  # Level Editor
            self.menu_system.main_menu_buttons[2].action = self._show_settings  # Settings
            self.menu_system.main_menu_buttons[3].action = self._show_skins  # Skins
            self.menu_system.main_menu_buttons[4].action = self._show_credits  # Credits
            self.menu_system.main_menu_buttons[5].action = self._exit_game  # Exit
    
    def _maximize_window(self):
        """Maximize the pygame window by setting it to screen size."""
        try:
            # Get screen dimensions
            info = pygame.display.Info()
            screen_w, screen_h = info.current_w, info.current_h
            
            # Set window to nearly full screen size (leave space for taskbar)
            self.screen_width = screen_w - 10
            self.screen_height = screen_h - 80  # Leave space for taskbar
            
            # Create the maximized window
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
            
            # Try to position window at top-left if on Windows
            if sys.platform == "win32":
                try:
                    import os
                    os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
                except:
                    pass
                    
        except Exception as e:
            print(f"Could not maximize window: {e}")
            # Fallback to default large window size
            self.screen_width = 1200
            self.screen_height = 800
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
    
    def _exit_game(self):
        """Exit the game."""
        self.running = False
        self.menu_system.running = False


def main():
    """Main function to run the enhanced Sokoban game."""
    game = EnhancedSokoban()
    game.start()


if __name__ == "__main__":
    main()