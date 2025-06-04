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
from constants import TITLE, CELL_SIZE
from level import Level
from level_manager import LevelManager
from skin_manager import SkinManager
from menu_system import MenuSystem
from graphical_level_editor import GraphicalLevelEditor
from sokoban_gui import SokobanGUIGame

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
        
        # Initialize window
        self.screen_width = 1024
        self.screen_height = 768
        self.fullscreen = False
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        
        # Initialize managers
        self.levels_dir = levels_dir
        self.level_manager = LevelManager(levels_dir)
        self.skin_manager = SkinManager()
        
        # Check if levels directory exists, create it if not
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)
            
        # Game state
        self.running = False
        self.current_state = 'menu'  # 'menu', 'playing', 'editor'
        
        # Create components
        self.menu_system = MenuSystem(self.screen_width, self.screen_height)
        self.game = SokobanGUIGame(levels_dir)
        self.editor = GraphicalLevelEditor(levels_dir, screen=self.screen)
        
        # Set up fullscreen toggle key handler
        self.key_handlers = {
            pygame.K_F11: self.toggle_fullscreen,
            pygame.K_ESCAPE: self.exit_fullscreen_if_active
        }
        
        # Set up menu actions
        self.menu_system.main_menu_buttons[0].action = self._start_game  # Play Game
        self.menu_system.main_menu_buttons[1].action = self._start_editor  # Level Editor
        self.menu_system.main_menu_buttons[2].action = self._show_settings  # Settings
        self.menu_system.main_menu_buttons[3].action = self._show_skins  # Skins
        self.menu_system.main_menu_buttons[4].action = self._show_credits  # Credits
        self.menu_system.main_menu_buttons[5].action = self._exit_game  # Exit
        
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
        print("Menu system running set to True")
        
        # Add F11 key handler to the menu system
        original_run_loop = self.menu_system._run_loop
        
        def patched_run_loop():
            clock = pygame.time.Clock()
            
            while self.menu_system.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.menu_system.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.screen_width, self.screen_height = event.size
                        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                        self.menu_system.screen_width = self.screen_width
                        self.menu_system.screen_height = self.screen_height
                        self.menu_system.screen = self.screen
                        self.menu_system._create_main_menu_buttons()
                    elif event.type == pygame.KEYDOWN:
                        # Check for F11 (fullscreen toggle) or ESC (exit fullscreen)
                        if event.key == pygame.K_F11:
                            self.toggle_fullscreen()
                        elif event.key == pygame.K_ESCAPE and self.fullscreen:
                            self.exit_fullscreen_if_active()
                        elif event.key == pygame.K_ESCAPE and self.menu_system.current_state != 'main':
                            # Return to main menu on ESC if not already there
                            self.menu_system._change_state('main')
                    
                    # Handle button events based on current state
                    if self.menu_system.current_state == 'main':
                        for button in self.menu_system.main_menu_buttons:
                            button.handle_event(event)
                
                # Update current state
                self.menu_system.states[self.menu_system.current_state]()
                
                # Cap the frame rate
                clock.tick(60)
        
        # Replace the run loop method
        self.menu_system._run_loop = patched_run_loop
        
        # Run the menu system
        self.menu_system._run_loop()
        
        print("Menu system _run_loop completed")
        
        # Check if we're transitioning to another state or exiting the game
        if not self.menu_system.running and self.current_state == 'menu':
            # Only exit the game if we're still in the menu state
            # This means the menu was closed without transitioning to another state
            print("Menu system running is False and still in menu state, exiting game")
            self.running = False
        else:
            print(f"Transitioning to state: {self.current_state}")
            
    def _run_game(self):
        """Run the game."""
        self.game.running = True
        self.game.game_loop()
        
        # When game is closed, return to menu
        self.current_state = 'menu'
        
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
        self.menu_system._create_main_menu_buttons()
        
        # Update editor
        self.editor.screen = self.screen
        self.editor.screen_width = self.screen_width
        self.editor.screen_height = self.screen_height
        
        # Update game renderer if needed
        if hasattr(self.game, 'renderer'):
            self.game.renderer.window_size = (self.screen_width, self.screen_height)
            self.game.renderer.screen = self.screen
    
    def _exit_game(self):
        """Exit the game."""
        self.running = False
        self.menu_system.running = False


# Main function to run the enhanced Sokoban game
def main():
    """Main function to run the enhanced Sokoban game."""
    game = EnhancedSokoban()
    game.start()


if __name__ == "__main__":
    main()