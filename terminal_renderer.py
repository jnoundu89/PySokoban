"""
Terminal renderer module for the Sokoban game.

This module provides functionality for rendering the game in a terminal environment.
"""

import os
import platform
from constants import DISPLAY_CHARS, COLORS


class TerminalRenderer:
    """
    Class for rendering the Sokoban game in a terminal.
    
    This class is responsible for rendering the game state, level information,
    and game statistics in a terminal environment.
    """
    
    def __init__(self, use_colors=True):
        """
        Initialize the terminal renderer.
        
        Args:
            use_colors (bool, optional): Whether to use colors in the terminal.
                                        Defaults to True.
        """
        self.use_colors = use_colors
        # Disable colors on Windows if not using a compatible terminal
        if platform.system() == 'Windows' and os.environ.get('TERM') is None:
            self.use_colors = False
    
    def clear_screen(self):
        """
        Clear the terminal screen.
        """
        # Check which command to use based on the operating system
        command = 'cls' if platform.system() == 'Windows' else 'clear'
        os.system(command)
    
    def render_level(self, level, level_manager=None):
        """
        Render the current level state in the terminal.
        
        Args:
            level: The Level object to render.
            level_manager: Optional LevelManager object for additional information.
        """
        self.clear_screen()
        
        # Print level information if level manager is provided
        if level_manager:
            level_info = f"Level {level_manager.get_current_level_number()} of {level_manager.get_level_count()}"
            print(level_info)
            print("=" * len(level_info))
        
        # Print the level
        for y in range(level.height):
            line = ""
            for x in range(level.width):
                char = level.get_display_char(x, y)
                display_char = DISPLAY_CHARS.get(char, char)
                
                if self.use_colors:
                    if char == '#':
                        line += f"{COLORS['wall']}{display_char}{COLORS['reset']}"
                    elif char == '@':
                        line += f"{COLORS['player']}{display_char}{COLORS['reset']}"
                    elif char == '+':
                        line += f"{COLORS['player_on_target']}{display_char}{COLORS['reset']}"
                    elif char == '$':
                        line += f"{COLORS['box']}{display_char}{COLORS['reset']}"
                    elif char == '*':
                        line += f"{COLORS['box_on_target']}{display_char}{COLORS['reset']}"
                    elif char == '.':
                        line += f"{COLORS['target']}{display_char}{COLORS['reset']}"
                    else:
                        line += display_char
                else:
                    line += display_char
            print(line)
        
        # Print game statistics
        stats = f"Moves: {level.moves}  Pushes: {level.pushes}"
        print("\n" + stats)
        
        # Print level completion message
        if level.is_completed():
            completion_msg = "Level completed!"
            if level_manager and level_manager.has_next_level():
                completion_msg += " Press 'n' for the next level."
            print("\n" + completion_msg)
    
    def render_help(self):
        """
        Render the help information in the terminal.
        """
        help_text = """
Controls:
  ↑, w         : Move up
  ↓, s         : Move down
  ←, a         : Move left
  →, d         : Move right
  r           : Reset level
  u           : Undo move
  n           : Next level
  p           : Previous level
  h           : Show this help
  q           : Quit game
        """
        print(help_text)
    
    def render_welcome_screen(self):
        """
        Render the welcome screen in the terminal.
        """
        self.clear_screen()
        
        welcome_text = """
██████╗  ██████╗ ██╗  ██╗ ██████╗ ██████╗  █████╗ ███╗   ██╗
██╔══██╗██╔═══██╗██║ ██╔╝██╔═══██╗██╔══██╗██╔══██╗████╗  ██║
██████╔╝██║   ██║█████╔╝ ██║   ██║██████╔╝███████║██╔██╗ ██║
██╔══██╗██║   ██║██╔═██╗ ██║   ██║██╔══██╗██╔══██║██║╚██╗██║
██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██████╔╝██║  ██║██║ ╚████║
╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝
                                                            
A puzzle game where you push boxes to their targets!

Press any key to start...
        """
        print(welcome_text)
    
    def render_game_over_screen(self, completed_all=False):
        """
        Render the game over screen in the terminal.
        
        Args:
            completed_all (bool, optional): Whether all levels were completed.
                                          Defaults to False.
        """
        self.clear_screen()
        
        if completed_all:
            game_over_text = """
 ██████╗ ██████╗ ███╗   ██╗ ██████╗ ██████╗  █████╗ ████████╗███████╗██╗
██╔════╝██╔═══██╗████╗  ██║██╔════╝ ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║
██║     ██║   ██║██╔██╗ ██║██║  ███╗██████╔╝███████║   ██║   ███████╗██║
██║     ██║   ██║██║╚██╗██║██║   ██║██╔══██╗██╔══██║   ██║   ╚════██║╚═╝
╚██████╗╚██████╔╝██║ ╚████║╚██████╔╝██║  ██║██║  ██║   ██║   ███████║██╗
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝
                                                                         
You have completed all levels! Well done!

Press any key to quit...
            """
        else:
            game_over_text = """
 ██████╗  █████╗ ███╗   ███╗███████╗     ██████╗ ██╗   ██╗███████╗██████╗ 
██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
                                                                           
Thanks for playing Sokoban!

Press any key to quit...
            """
        
        print(game_over_text)