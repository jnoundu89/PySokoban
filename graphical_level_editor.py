"""
Graphical Level Editor for the Sokoban game.

This module provides a GUI-based level editor with drag-and-drop functionality
for creating and editing Sokoban levels.
"""

import os
import sys
import pygame
from constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE, TITLE
from level import Level
from level_manager import LevelManager
from skin_manager import SkinManager
from procedural_generator import ProceduralGenerator

class GraphicalLevelEditor:
    """
    Class for creating and editing Sokoban levels with a graphical interface.
    
    This class provides a GUI-based level editor with drag-and-drop functionality
    for designing new levels or modifying existing ones.
    """
    
    def __init__(self, levels_dir='levels', screen=None):
        """
        Initialize the graphical level editor.
        
        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
            screen (pygame.Surface, optional): Existing pygame surface to use.
                                             If None, a new window will be created.
        """
        # Only initialize pygame if not already initialized
        if not pygame.get_init():
            pygame.init()
        
        # Initialize window
        self.screen_width = 1024
        self.screen_height = 768
        
        # Use existing screen if provided, otherwise create a new one
        if screen is not None:
            self.screen = screen
            self.screen_width, self.screen_height = self.screen.get_size()
            self.using_shared_screen = True
            print("Using existing screen for level editor")
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
            pygame.display.set_caption(f"{TITLE} - Level Editor")
            self.using_shared_screen = False
            print("Created new screen for level editor")
        
        # Initialize managers
        self.levels_dir = levels_dir
        self.level_manager = LevelManager(levels_dir)
        self.skin_manager = SkinManager()
        
        # Check if levels directory exists, create it if not
        if not os.path.exists(levels_dir):
            os.makedirs(levels_dir)
            
        # Editor state
        self.current_level = None
        self.current_element = WALL
        self.grid_size = CELL_SIZE
        self.grid_offset_x = 20
        self.grid_offset_y = 100
        self.grid_width = 20
        self.grid_height = 15
        self.unsaved_changes = False
        self.show_help = False
        self.show_grid = True
        self.show_metrics = False
        self.test_mode = False
        self.player_pos_in_test = None
        self.running = False
        
        # Element palette
        self.palette = [
            {'char': WALL, 'name': 'Wall'},
            {'char': FLOOR, 'name': 'Floor'},
            {'char': PLAYER, 'name': 'Player'},
            {'char': BOX, 'name': 'Box'},
            {'char': TARGET, 'name': 'Target'}
        ]
        self.palette_rect = pygame.Rect(20, 20, self.screen_width - 40, 60)
        
        # Buttons
        self.buttons = []
        self._create_buttons()
        
        # Colors
        self.colors = {
            'background': (240, 240, 240),
            'grid': (200, 200, 200),
            'text': (50, 50, 50),
            'button': (100, 100, 200),
            'button_hover': (130, 130, 255),
            'button_text': (255, 255, 255),
            'selected': (255, 255, 0),
            'palette': (220, 220, 220)
        }
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Create a new empty level by default
        self._create_new_level(self.grid_width, self.grid_height)
        
    def _create_buttons(self):
        """Create buttons for the editor interface."""
        button_width = 100
        button_height = 30
        button_spacing = 10
        button_y = self.screen_height - 50
        
        # Create buttons
        self.buttons = [
            {'rect': pygame.Rect(20, button_y, button_width, button_height),
             'text': 'New', 'action': self._show_new_level_dialog},
            {'rect': pygame.Rect(20 + (button_width + button_spacing), button_y, button_width, button_height),
             'text': 'Open', 'action': self._show_open_level_dialog},
            {'rect': pygame.Rect(20 + (button_width + button_spacing) * 2, button_y, button_width, button_height),
             'text': 'Save', 'action': self._show_save_level_dialog},
            {'rect': pygame.Rect(20 + (button_width + button_spacing) * 3, button_y, button_width, button_height),
             'text': 'Test', 'action': self._toggle_test_mode},
            {'rect': pygame.Rect(20 + (button_width + button_spacing) * 4, button_y, button_width, button_height),
             'text': 'Validate', 'action': self._validate_level},
            {'rect': pygame.Rect(20 + (button_width + button_spacing) * 5, button_y, button_width, button_height),
             'text': 'Help', 'action': self._toggle_help},
            {'rect': pygame.Rect(20 + (button_width + button_spacing) * 6, button_y, button_width, button_height),
              'text': 'Generate', 'action': self._show_generate_dialog},
            {'rect': pygame.Rect(20 + (button_width + button_spacing) * 7, button_y, button_width, button_height),
              'text': 'Metrics', 'action': self._toggle_metrics},
            {'rect': pygame.Rect(20 + (button_width + button_spacing) * 8, button_y, button_width, button_height),
              'text': 'Exit', 'action': self._exit_editor}
        ]
        
    def _create_new_level(self, width, height):
        """
        Create a new empty level.
        
        Args:
            width (int): Width of the level in cells.
            height (int): Height of the level in cells.
        """
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
        self.unsaved_changes = True
        
    def _show_new_level_dialog(self):
        """Show dialog to create a new level."""
        # For simplicity, we'll just create a new level with default dimensions
        # In a real implementation, you would show a dialog to input dimensions
        self._create_new_level(self.grid_width, self.grid_height)
        
    def _show_open_level_dialog(self):
        """Show dialog to open an existing level."""
        # For simplicity, we'll just show a list of available levels
        # In a real implementation, you would show a proper file dialog
        
        # Get list of level files
        level_files = self.level_manager.level_files
        if not level_files:
            return  # No levels to open
            
        # Create a simple dialog
        dialog_width = 400
        dialog_height = 500
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Create buttons for each level
        level_buttons = []
        button_height = 30
        button_spacing = 5
        
        for i, level_file in enumerate(level_files):
            level_name = os.path.basename(level_file)
            button_rect = pygame.Rect(dialog_x + 20, dialog_y + 60 + i * (button_height + button_spacing),
                                     dialog_width - 40, button_height)
            level_buttons.append({
                'rect': button_rect,
                'text': level_name,
                'action': lambda lf=level_file: self._open_level(lf)
            })
            
        # Add cancel button
        cancel_rect = pygame.Rect(dialog_x + dialog_width - 120, dialog_y + dialog_height - 50,
                                 100, 30)
        
        # Dialog loop
        dialog_running = True
        while dialog_running and self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    dialog_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        dialog_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if cancel button was clicked
                    if cancel_rect.collidepoint(mouse_pos):
                        dialog_running = False
                        
                    # Check if a level button was clicked
                    for button in level_buttons:
                        if button['rect'].collidepoint(mouse_pos):
                            button['action']()
                            dialog_running = False
                            break
            
            # Draw dialog
            self._draw_editor()  # Draw editor in background
            
            # Draw dialog box
            pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)
            
            # Draw title
            title_surface = self.title_font.render("Open Level", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)
            
            # Draw level buttons
            for button in level_buttons:
                pygame.draw.rect(self.screen, (200, 200, 200), button['rect'])
                pygame.draw.rect(self.screen, (0, 0, 0), button['rect'], 1)
                
                text_surface = self.text_font.render(button['text'], True, (0, 0, 0))
                text_rect = text_surface.get_rect(midleft=(button['rect'].left + 10, button['rect'].centery))
                self.screen.blit(text_surface, text_rect)
                
            # Draw cancel button
            pygame.draw.rect(self.screen, (200, 100, 100), cancel_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), cancel_rect, 1)
            
            cancel_text = self.text_font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            self.screen.blit(cancel_text, cancel_text_rect)
            
            pygame.display.flip()
            
    def _open_level(self, level_file):
        """
        Open an existing level.
        
        Args:
            level_file (str): Path to the level file.
        """
        try:
            self.current_level = Level(level_file=level_file)
            self.unsaved_changes = False
        except Exception as e:
            print(f"Error opening level: {e}")
            
    def _show_save_level_dialog(self):
        """Show dialog to save the current level."""
        # Create a simple dialog
        dialog_width = 400
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Create text input field
        input_rect = pygame.Rect(dialog_x + 20, dialog_y + 80, dialog_width - 40, 30)
        input_text = "level"
        input_active = True
        
        # Create buttons
        save_rect = pygame.Rect(dialog_x + dialog_width - 220, dialog_y + dialog_height - 50,
                               100, 30)
        cancel_rect = pygame.Rect(dialog_x + dialog_width - 110, dialog_y + dialog_height - 50,
                                 100, 30)
        
        # Dialog loop
        dialog_running = True
        while dialog_running and self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    dialog_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        dialog_running = False
                    elif event.key == pygame.K_RETURN:
                        self._save_level(input_text)
                        dialog_running = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        # Add character to input text if it's a valid filename character
                        if event.unicode.isalnum() or event.unicode in "-_":
                            input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if save button was clicked
                    if save_rect.collidepoint(mouse_pos):
                        self._save_level(input_text)
                        dialog_running = False
                        
                    # Check if cancel button was clicked
                    if cancel_rect.collidepoint(mouse_pos):
                        dialog_running = False
                        
                    # Check if input field was clicked
                    input_active = input_rect.collidepoint(mouse_pos)
            
            # Draw dialog
            self._draw_editor()  # Draw editor in background
            
            # Draw dialog box
            pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)
            
            # Draw title
            title_surface = self.title_font.render("Save Level", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)
            
            # Draw input field label
            label_surface = self.text_font.render("Level name:", True, (0, 0, 0))
            label_rect = label_surface.get_rect(midleft=(dialog_x + 20, dialog_y + 65))
            self.screen.blit(label_surface, label_rect)
            
            # Draw input field
            pygame.draw.rect(self.screen, (255, 255, 255), input_rect)
            pygame.draw.rect(self.screen, (0, 0, 0) if input_active else (100, 100, 100), input_rect, 2)
            
            input_surface = self.text_font.render(input_text, True, (0, 0, 0))
            input_text_rect = input_surface.get_rect(midleft=(input_rect.left + 5, input_rect.centery))
            self.screen.blit(input_surface, input_text_rect)
            
            # Draw save button
            pygame.draw.rect(self.screen, (100, 200, 100), save_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), save_rect, 1)
            
            save_text = self.text_font.render("Save", True, (255, 255, 255))
            save_text_rect = save_text.get_rect(center=save_rect.center)
            self.screen.blit(save_text, save_text_rect)
            
            # Draw cancel button
            pygame.draw.rect(self.screen, (200, 100, 100), cancel_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), cancel_rect, 1)
            
            cancel_text = self.text_font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            self.screen.blit(cancel_text, cancel_text_rect)
            
            pygame.display.flip()
            
    def _save_level(self, filename):
        """
        Save the current level to a file.
        
        Args:
            filename (str): Name of the file to save to (without extension).
        """
        if not filename:
            return
            
        # Add .txt extension if not provided
        if not filename.endswith('.txt'):
            filename += '.txt'
            
        # Create full path
        level_path = os.path.join(self.levels_dir, filename)
        
        # Save the level
        level_string = self.current_level.get_state_string()
        
        try:
            with open(level_path, 'w') as file:
                file.write(level_string)
                
            self.unsaved_changes = False
            
            # Reload level files in level manager
            self.level_manager._load_level_files()
        except Exception as e:
            print(f"Error saving level: {e}")
            
    def _toggle_test_mode(self):
        """Toggle test mode to play the current level."""
        if self._validate_level(show_dialog=False):
            self.test_mode = not self.test_mode
            
            if self.test_mode:
                # Save player position for testing
                self.player_pos_in_test = self.current_level.player_pos
            else:
                # Restore player position after testing
                self.current_level.player_pos = self.player_pos_in_test
                
    def _validate_level(self, show_dialog=True):
        """
        Validate the current level.
        
        Args:
            show_dialog (bool): Whether to show a dialog with validation results.
            
        Returns:
            bool: True if the level is valid, False otherwise.
        """
        # Check if level has a player
        has_player = self.current_level.player_pos != (0, 0)
        
        # Check if level has at least one box and target
        has_boxes = len(self.current_level.boxes) > 0
        has_targets = len(self.current_level.targets) > 0
        
        # Check if number of boxes matches number of targets
        boxes_match_targets = len(self.current_level.boxes) == len(self.current_level.targets)
        
        # Check if level is valid
        is_valid = has_player and has_boxes and has_targets and boxes_match_targets
        
        if show_dialog:
            # Create a simple dialog
            dialog_width = 400
            dialog_height = 250
            dialog_x = (self.screen_width - dialog_width) // 2
            dialog_y = (self.screen_height - dialog_height) // 2
            
            dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
            
            # Create OK button
            ok_rect = pygame.Rect(dialog_x + (dialog_width - 100) // 2, dialog_y + dialog_height - 50,
                                 100, 30)
            
            # Dialog loop
            dialog_running = True
            while dialog_running and self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        dialog_running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                            dialog_running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # Check if OK button was clicked
                        if ok_rect.collidepoint(mouse_pos):
                            dialog_running = False
                
                # Draw dialog
                self._draw_editor()  # Draw editor in background
                
                # Draw dialog box
                pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)
                
                # Draw title
                title_text = "Level Validation"
                title_surface = self.title_font.render(title_text, True, (0, 0, 0))
                title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
                self.screen.blit(title_surface, title_rect)
                
                # Draw validation results
                results = [
                    f"Player: {'Yes' if has_player else 'No'}",
                    f"Boxes: {'Yes' if has_boxes else 'No'}",
                    f"Targets: {'Yes' if has_targets else 'No'}",
                    f"Boxes match targets: {'Yes' if boxes_match_targets else 'No'}",
                    "",
                    f"Level is {'valid' if is_valid else 'invalid'}"
                ]
                
                for i, result in enumerate(results):
                    color = (0, 128, 0) if "Yes" in result or "valid" in result else (200, 0, 0)
                    if result == "":
                        continue
                        
                    result_surface = self.text_font.render(result, True, color)
                    result_rect = result_surface.get_rect(midleft=(dialog_x + 30, dialog_y + 80 + i * 25))
                    self.screen.blit(result_surface, result_rect)
                
                # Draw OK button
                pygame.draw.rect(self.screen, (100, 100, 200), ok_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), ok_rect, 1)
                
                ok_text = self.text_font.render("OK", True, (255, 255, 255))
                ok_text_rect = ok_text.get_rect(center=ok_rect.center)
                self.screen.blit(ok_text, ok_text_rect)
                
                pygame.display.flip()
                
        return is_valid
        
    def _toggle_help(self):
        """Toggle help screen."""
        self.show_help = not self.show_help
    
    def _toggle_metrics(self):
        """Toggle display of level metrics."""
        self.show_metrics = not self.show_metrics
        
    def _show_generate_dialog(self):
        """Show dialog to configure and generate a random level."""
        # Create a dialog
        dialog_width = 500
        dialog_height = 400
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Default parameters
        params = {
            'min_width': 7,
            'max_width': 15,
            'min_height': 7,
            'max_height': 15,
            'min_boxes': 1,
            'max_boxes': 5,
            'wall_density': 0.2
        }
        
        # Input fields
        input_fields = [
            {'name': 'min_width', 'label': 'Min Width:', 'value': str(params['min_width']), 'rect': None, 'active': False},
            {'name': 'max_width', 'label': 'Max Width:', 'value': str(params['max_width']), 'rect': None, 'active': False},
            {'name': 'min_height', 'label': 'Min Height:', 'value': str(params['min_height']), 'rect': None, 'active': False},
            {'name': 'max_height', 'label': 'Max Height:', 'value': str(params['max_height']), 'rect': None, 'active': False},
            {'name': 'min_boxes', 'label': 'Min Boxes:', 'value': str(params['min_boxes']), 'rect': None, 'active': False},
            {'name': 'max_boxes', 'label': 'Max Boxes:', 'value': str(params['max_boxes']), 'rect': None, 'active': False},
            {'name': 'wall_density', 'label': 'Wall Density:', 'value': str(params['wall_density']), 'rect': None, 'active': False}
        ]
        
        # Create input field rectangles
        field_width = 100
        field_height = 30
        field_spacing = 40
        
        for i, field in enumerate(input_fields):
            field['rect'] = pygame.Rect(
                dialog_x + dialog_width - field_width - 30,
                dialog_y + 80 + i * field_spacing,
                field_width,
                field_height
            )
        
        # Create buttons
        generate_rect = pygame.Rect(dialog_x + dialog_width // 2 - 110, dialog_y + dialog_height - 50, 100, 30)
        cancel_rect = pygame.Rect(dialog_x + dialog_width // 2 + 10, dialog_y + dialog_height - 50, 100, 30)
        
        # Status message
        status_message = ""
        generating = False
        
        # Dialog loop
        dialog_running = True
        while dialog_running and self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    dialog_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        dialog_running = False
                    elif event.key == pygame.K_RETURN:
                        if not generating:
                            generating = True
                            status_message = "Generating level... Please wait."
                    elif event.key == pygame.K_BACKSPACE:
                        # Delete last character in active field
                        for field in input_fields:
                            if field['active']:
                                field['value'] = field['value'][:-1]
                                break
                    else:
                        # Add character to active field if it's valid
                        for field in input_fields:
                            if field['active']:
                                if field['name'] == 'wall_density':
                                    # Allow numbers and decimal point
                                    if event.unicode.isdigit() or event.unicode == '.':
                                        field['value'] += event.unicode
                                else:
                                    # Allow only numbers
                                    if event.unicode.isdigit():
                                        field['value'] += event.unicode
                                break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if generate button was clicked
                    if generate_rect.collidepoint(mouse_pos) and not generating:
                        generating = True
                        status_message = "Generating level... Please wait."
                    
                    # Check if cancel button was clicked
                    elif cancel_rect.collidepoint(mouse_pos):
                        dialog_running = False
                    
                    # Check if an input field was clicked
                    else:
                        for field in input_fields:
                            field['active'] = field['rect'].collidepoint(mouse_pos)
            
            # Draw dialog
            self._draw_editor()  # Draw editor in background
            
            # Draw dialog box
            pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)
            
            # Draw title
            title_surface = self.title_font.render("Generate Random Level", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)
            
            # Draw input fields and labels
            for field in input_fields:
                # Draw label
                label_surface = self.text_font.render(field['label'], True, (0, 0, 0))
                label_rect = label_surface.get_rect(midright=(field['rect'].left - 10, field['rect'].centery))
                self.screen.blit(label_surface, label_rect)
                
                # Draw input field
                pygame.draw.rect(self.screen, (255, 255, 255), field['rect'])
                pygame.draw.rect(self.screen, (0, 0, 0) if field['active'] else (100, 100, 100), field['rect'], 2)
                
                # Draw input text
                text_surface = self.text_font.render(field['value'], True, (0, 0, 0))
                text_rect = text_surface.get_rect(midleft=(field['rect'].left + 5, field['rect'].centery))
                self.screen.blit(text_surface, text_rect)
            
            # Draw generate button
            button_color = (100, 200, 100) if not generating else (150, 150, 150)
            pygame.draw.rect(self.screen, button_color, generate_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), generate_rect, 1)
            
            generate_text = self.text_font.render("Generate", True, (255, 255, 255))
            generate_text_rect = generate_text.get_rect(center=generate_rect.center)
            self.screen.blit(generate_text, generate_text_rect)
            
            # Draw cancel button
            pygame.draw.rect(self.screen, (200, 100, 100), cancel_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), cancel_rect, 1)
            
            cancel_text = self.text_font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            self.screen.blit(cancel_text, cancel_text_rect)
            
            # Draw status message if generating
            if status_message:
                status_surface = self.text_font.render(status_message, True, (200, 0, 0) if "Failed" in status_message else (0, 100, 0))
                status_rect = status_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + dialog_height - 100))
                self.screen.blit(status_surface, status_rect)
            
            pygame.display.flip()
            
            # If we're generating, do it now
            if generating:
                try:
                    # Parse parameters
                    for field in input_fields:
                        if field['name'] == 'wall_density':
                            params[field['name']] = float(field['value'] or params[field['name']])
                        else:
                            params[field['name']] = int(field['value'] or params[field['name']])
                    
                    # Generate level
                    if self.level_manager.generate_random_level(params):
                        self.current_level = self.level_manager.current_level
                        self.unsaved_changes = True
                        dialog_running = False
                    else:
                        status_message = "Failed to generate level. Try different parameters."
                        generating = False
                except ValueError:
                    status_message = "Invalid parameters. Please check your inputs."
                    generating = False
                except Exception as e:
                    status_message = f"Error: {str(e)}"
                    generating = False
    
    def _exit_editor(self):
        """Exit the editor."""
        print("Exit editor method called")
        if self.unsaved_changes:
            # Show confirmation dialog
            dialog_width = 400
            dialog_height = 150
            dialog_x = (self.screen_width - dialog_width) // 2
            dialog_y = (self.screen_height - dialog_height) // 2
            
            dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
            
            # Create buttons
            yes_rect = pygame.Rect(dialog_x + dialog_width // 2 - 110, dialog_y + dialog_height - 50,
                                   100, 30)
            no_rect = pygame.Rect(dialog_x + dialog_width // 2 + 10, dialog_y + dialog_height - 50,
                                  100, 30)
            
            # Dialog loop
            dialog_running = True
            while dialog_running and self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        dialog_running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            dialog_running = False
                        elif event.key == pygame.K_y:
                            self.running = False
                            dialog_running = False
                        elif event.key == pygame.K_n:
                            dialog_running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # Check if yes button was clicked
                        if yes_rect.collidepoint(mouse_pos):
                            self.running = False
                            dialog_running = False
                            
                        # Check if no button was clicked
                        if no_rect.collidepoint(mouse_pos):
                            dialog_running = False
                
                # Draw dialog
                self._draw_editor()  # Draw editor in background
                
                # Draw dialog box
                pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)
                
                # Draw title
                title_surface = self.title_font.render("Unsaved Changes", True, (0, 0, 0))
                title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
                self.screen.blit(title_surface, title_rect)
                
                # Draw message
                message_surface = self.text_font.render("Do you want to exit without saving?", True, (0, 0, 0))
                message_rect = message_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 70))
                self.screen.blit(message_surface, message_rect)
                
                # Draw yes button
                pygame.draw.rect(self.screen, (200, 100, 100), yes_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), yes_rect, 1)
                
                yes_text = self.text_font.render("Yes", True, (255, 255, 255))
                yes_text_rect = yes_text.get_rect(center=yes_rect.center)
                self.screen.blit(yes_text, yes_text_rect)
                
                # Draw no button
                pygame.draw.rect(self.screen, (100, 200, 100), no_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), no_rect, 1)
                
                no_text = self.text_font.render("No", True, (255, 255, 255))
                no_text_rect = no_text.get_rect(center=no_rect.center)
                self.screen.blit(no_text, no_text_rect)
                
                pygame.display.flip()
        else:
            # No unsaved changes, just exit
            self.running = False
                
    def _handle_grid_click(self, mouse_pos, mouse_button):
        """
        Handle clicks on the grid.
        
        Args:
            mouse_pos (tuple): (x, y) position of the mouse.
            mouse_button (int): Mouse button that was clicked.
        """
        # Convert mouse position to grid coordinates
        grid_x = (mouse_pos[0] - self.grid_offset_x) // self.grid_size
        grid_y = (mouse_pos[1] - self.grid_offset_y) // self.grid_size
        
        # Check if click is within grid bounds
        if (0 <= grid_x < self.current_level.width and
            0 <= grid_y < self.current_level.height):
            
            # In test mode, handle player movement
            if self.test_mode:
                if mouse_button == 1:  # Left click
                    # Get player position
                    player_x, player_y = self.current_level.player_pos
                    
                    # Calculate direction to move
                    dx = grid_x - player_x
                    dy = grid_y - player_y
                    
                    # Only allow adjacent moves
                    if abs(dx) + abs(dy) == 1:
                        self.current_level.move(dx, dy)
                        
                return
            
            # In edit mode, place the current element
            if mouse_button == 1:  # Left click
                self._place_element(grid_x, grid_y)
            elif mouse_button == 3:  # Right click
                # Clear the cell (set to floor)
                self._clear_element(grid_x, grid_y)
                
    def _place_element(self, x, y):
        """
        Place the current element at the specified grid coordinates.
        
        Args:
            x (int): X coordinate on the grid.
            y (int): Y coordinate on the grid.
        """
        if self.current_element == PLAYER:
            # Remove existing player
            self.current_level.player_pos = (x, y)
        elif self.current_element == BOX:
            # Add box if not already there
            if (x, y) not in self.current_level.boxes:
                self.current_level.boxes.append((x, y))
        elif self.current_element == TARGET:
            # Add target if not already there
            if (x, y) not in self.current_level.targets:
                self.current_level.targets.append((x, y))
        elif self.current_element == WALL:
            # Set cell to wall
            self.current_level.map_data[y][x] = WALL
            
            # Remove any objects at this position
            if (x, y) == self.current_level.player_pos:
                self.current_level.player_pos = (0, 0)
            if (x, y) in self.current_level.boxes:
                self.current_level.boxes.remove((x, y))
            if (x, y) in self.current_level.targets:
                self.current_level.targets.remove((x, y))
        elif self.current_element == FLOOR:
            # Set cell to floor
            self.current_level.map_data[y][x] = FLOOR
            
        self.unsaved_changes = True
        
    def _clear_element(self, x, y):
        """
        Clear the element at the specified grid coordinates.
        
        Args:
            x (int): X coordinate on the grid.
            y (int): Y coordinate on the grid.
        """
        # Remove any objects at this position
        if (x, y) == self.current_level.player_pos:
            self.current_level.player_pos = (0, 0)
        if (x, y) in self.current_level.boxes:
            self.current_level.boxes.remove((x, y))
        if (x, y) in self.current_level.targets:
            self.current_level.targets.remove((x, y))
            
        # Set cell to floor
        self.current_level.map_data[y][x] = FLOOR
        
        self.unsaved_changes = True
        
    def _handle_palette_click(self, mouse_pos):
        """
        Handle clicks on the element palette.
        
        Args:
            mouse_pos (tuple): (x, y) position of the mouse.
        """
        # Calculate which element was clicked
        element_width = self.palette_rect.width // len(self.palette)
        element_index = (mouse_pos[0] - self.palette_rect.left) // element_width
        
        if 0 <= element_index < len(self.palette):
            self.current_element = self.palette[element_index]['char']
            
    def _draw_editor(self):
        """Draw the editor interface."""
        # Clear the screen
        self.screen.fill(self.colors['background'])
        
        # Draw the element palette
        pygame.draw.rect(self.screen, self.colors['palette'], self.palette_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), self.palette_rect, 1)
        
        # Draw each element in the palette
        element_width = self.palette_rect.width // len(self.palette)
        for i, element in enumerate(self.palette):
            # Calculate element position
            element_x = self.palette_rect.left + i * element_width
            element_y = self.palette_rect.top
            element_rect = pygame.Rect(element_x, element_y, element_width, self.palette_rect.height)
            
            # Draw element background
            if element['char'] == self.current_element:
                pygame.draw.rect(self.screen, self.colors['selected'], element_rect)
            
            # Draw element border
            pygame.draw.rect(self.screen, (0, 0, 0), element_rect, 1)
            
            # Draw element icon
            skin = self.skin_manager.get_skin()
            if element['char'] in skin:
                icon = skin[element['char']]
                icon_rect = icon.get_rect(center=(element_x + element_width // 2, element_y + self.palette_rect.height // 2))
                self.screen.blit(icon, icon_rect)
            
            # Draw element name
            name_surface = self.small_font.render(element['name'], True, (0, 0, 0))
            name_rect = name_surface.get_rect(center=(element_x + element_width // 2, element_y + self.palette_rect.height - 10))
            self.screen.blit(name_surface, name_rect)
        
        # Draw the grid
        grid_width_pixels = self.current_level.width * self.grid_size
        grid_height_pixels = self.current_level.height * self.grid_size
        grid_rect = pygame.Rect(self.grid_offset_x, self.grid_offset_y, grid_width_pixels, grid_height_pixels)
        
        # Draw grid background
        pygame.draw.rect(self.screen, (255, 255, 255), grid_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), grid_rect, 1)
        
        # Draw grid lines
        if self.show_grid:
            for x in range(self.current_level.width + 1):
                pygame.draw.line(self.screen, self.colors['grid'],
                                (self.grid_offset_x + x * self.grid_size, self.grid_offset_y),
                                (self.grid_offset_x + x * self.grid_size, self.grid_offset_y + grid_height_pixels))
            for y in range(self.current_level.height + 1):
                pygame.draw.line(self.screen, self.colors['grid'],
                                (self.grid_offset_x, self.grid_offset_y + y * self.grid_size),
                                (self.grid_offset_x + grid_width_pixels, self.grid_offset_y + y * self.grid_size))
        
        # Draw level elements
        skin = self.skin_manager.get_skin()
        for y in range(self.current_level.height):
            for x in range(self.current_level.width):
                # Calculate cell position
                cell_x = self.grid_offset_x + x * self.grid_size
                cell_y = self.grid_offset_y + y * self.grid_size
                
                # Get cell character
                char = self.current_level.get_display_char(x, y)
                
                # Draw cell
                if char in skin:
                    self.screen.blit(skin[char], (cell_x, cell_y))
        
        # Draw buttons
        for button in self.buttons:
            # Draw button background
            if button['rect'].collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, self.colors['button_hover'], button['rect'], 0, 5)
            else:
                pygame.draw.rect(self.screen, self.colors['button'], button['rect'], 0, 5)
            
            # Draw button border
            pygame.draw.rect(self.screen, (0, 0, 0), button['rect'], 1, 5)
            
            # Draw button text
            text_surface = self.text_font.render(button['text'], True, self.colors['button_text'])
            text_rect = text_surface.get_rect(center=button['rect'].center)
            self.screen.blit(text_surface, text_rect)
        
        # Draw status bar
        status_rect = pygame.Rect(20, self.screen_height - 80, self.screen_width - 40, 20)
        status_text = f"Mode: {'Test' if self.test_mode else 'Edit'} | " \
                     f"Element: {next((e['name'] for e in self.palette if e['char'] == self.current_element), 'None')} | " \
                     f"Unsaved Changes: {'Yes' if self.unsaved_changes else 'No'}"
        status_surface = self.small_font.render(status_text, True, (0, 0, 0))
        self.screen.blit(status_surface, status_rect)
        
        # Draw help screen if enabled
        if self.show_help:
            self._draw_help_screen()
        
        # Draw metrics if enabled
        if self.show_metrics and hasattr(self.level_manager, 'current_level_metrics') and self.level_manager.current_level_metrics:
            self._draw_metrics_screen()
            
        # Update the display
        pygame.display.flip()
        
    def _draw_help_screen(self):
        """Draw the help screen overlay."""
        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Create help content area
        help_width = 600
        help_height = 400
        help_x = (self.screen_width - help_width) // 2
        help_y = (self.screen_height - help_height) // 2
        
        help_rect = pygame.Rect(help_x, help_y, help_width, help_height)
        pygame.draw.rect(self.screen, (240, 240, 240), help_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), help_rect, 2)
        
        # Draw title
        title_surface = self.title_font.render("Level Editor Help", True, (0, 0, 0))
        title_rect = title_surface.get_rect(center=(help_x + help_width // 2, help_y + 30))
        self.screen.blit(title_surface, title_rect)
        
        # Draw help text
        help_lines = [
            "Left Click: Place selected element",
            "Right Click: Clear cell (set to floor)",
            "Click on palette: Select element",
            "",
            "Buttons:",
            "New: Create a new empty level",
            "Open: Open an existing level",
            "Save: Save the current level",
            "Test: Test the current level",
            "Validate: Check if the level is valid",
            "Help: Show this help screen",
            "Exit: Exit the editor",
            "",
            "Press any key to close this help screen"
        ]
        
        for i, line in enumerate(help_lines):
            if line == "":
                continue
                
            line_surface = self.text_font.render(line, True, (0, 0, 0))
            line_rect = line_surface.get_rect(midleft=(help_x + 30, help_y + 80 + i * 25))
            self.screen.blit(line_surface, line_rect)
    
    def _draw_metrics_screen(self):
        """Draw the metrics screen overlay."""
        # Create a semi-transparent overlay for the right side of the screen
        metrics_width = 300
        metrics_height = self.screen_height - 200
        metrics_x = self.screen_width - metrics_width - 20
        metrics_y = 100
        
        metrics_rect = pygame.Rect(metrics_x, metrics_y, metrics_width, metrics_height)
        
        # Draw semi-transparent background
        overlay = pygame.Surface((metrics_width, metrics_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        self.screen.blit(overlay, (metrics_x, metrics_y))
        
        # Draw border
        pygame.draw.rect(self.screen, (200, 200, 200), metrics_rect, 2)
        
        # Draw title
        title_surface = self.title_font.render("Level Metrics", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(metrics_x + metrics_width // 2, metrics_y + 30))
        self.screen.blit(title_surface, title_rect)
        
        # Get metrics
        metrics = self.level_manager.current_level_metrics
        
        # Draw metrics
        y_offset = 80
        line_height = 25
        
        # Basic metrics
        self._draw_metric_line("Level Size", f"{metrics['size']['width']}x{metrics['size']['height']}", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("Playable Area", f"{metrics['size']['playable_area']} tiles", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("Box Count", f"{metrics['box_count']}", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("Solution Length", f"{metrics['solution_length']} moves", metrics_x, metrics_y + y_offset)
        y_offset += line_height * 1.5
        
        # Difficulty metrics
        difficulty_score = metrics['difficulty']['overall_score']
        difficulty_color = (0, 255, 0) if difficulty_score < 30 else (255, 255, 0) if difficulty_score < 70 else (255, 100, 100)
        self._draw_metric_line("Difficulty", f"{difficulty_score:.1f}/100", metrics_x, metrics_y + y_offset, difficulty_color)
        y_offset += line_height * 1.5
        
        # Efficiency metrics
        self._draw_metric_line("Space Efficiency", f"{metrics['space_efficiency']:.2f}", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("Box Density", f"{metrics['box_density']:.2f}", metrics_x, metrics_y + y_offset)
        y_offset += line_height * 1.5
        
        # Pattern metrics
        patterns = metrics['patterns']
        self._draw_metric_line("Patterns", "", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("  Corners", f"{patterns['corners']}", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("  Corridors", f"{patterns['corridors']}", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("  Rooms", f"{patterns['rooms']}", metrics_x, metrics_y + y_offset)
        y_offset += line_height
        
        self._draw_metric_line("  Dead Ends", f"{patterns['dead_ends']}", metrics_x, metrics_y + y_offset)
    
    def _draw_metric_line(self, label, value, base_x, y, value_color=(255, 255, 255)):
        """Draw a metric line with label and value."""
        label_surface = self.text_font.render(label + ":", True, (200, 200, 200))
        label_rect = label_surface.get_rect(topleft=(base_x + 20, y))
        self.screen.blit(label_surface, label_rect)
        
        value_surface = self.text_font.render(value, True, value_color)
        value_rect = value_surface.get_rect(topright=(base_x + 280, y))
        self.screen.blit(value_surface, value_rect)
            
    def start(self):
        """Start the level editor."""
        try:
            print("Level editor start method called")
            self.running = True
            clock = pygame.time.Clock()
            
            # Store the current display caption to restore it later
            original_caption = pygame.display.get_caption()[0]
            pygame.display.set_caption(f"{TITLE} - Level Editor")
            
            while self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("Quit event received in editor")
                        self._exit_editor()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.show_help:
                                self.show_help = False
                            elif self.test_mode:
                                self._toggle_test_mode()
                            else:
                                self._exit_editor()
                        elif event.key == pygame.K_h:
                            self._toggle_help()
                        elif event.key == pygame.K_g:
                            self.show_grid = not self.show_grid
                        elif event.key == pygame.K_m:
                            self._toggle_metrics()
                        elif event.key == pygame.K_t:
                            self._toggle_test_mode()
                        elif self.test_mode:
                            # Handle keyboard movement in test mode
                            dx, dy = 0, 0
                            if event.key == pygame.K_UP:
                                dy = -1
                            elif event.key == pygame.K_DOWN:
                                dy = 1
                            elif event.key == pygame.K_LEFT:
                                dx = -1
                            elif event.key == pygame.K_RIGHT:
                                dx = 1
                                
                            if dx != 0 or dy != 0:
                                self.current_level.move(dx, dy)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # Check if a button was clicked
                        for button in self.buttons:
                            if button['rect'].collidepoint(mouse_pos):
                                button['action']()
                                break
                        else:
                            # Check if palette was clicked
                            if self.palette_rect.collidepoint(mouse_pos):
                                self._handle_palette_click(mouse_pos)
                            # Check if grid was clicked
                            elif (self.grid_offset_x <= mouse_pos[0] <= self.grid_offset_x + self.current_level.width * self.grid_size and
                                  self.grid_offset_y <= mouse_pos[1] <= self.grid_offset_y + self.current_level.height * self.grid_size):
                                self._handle_grid_click(mouse_pos, event.button)
                    elif event.type == pygame.VIDEORESIZE:
                        # Update window size
                        self.screen_width, self.screen_height = event.size
                        
                        # Only create a new screen if we're not using a shared screen
                        if not hasattr(self, 'using_shared_screen') or not self.using_shared_screen:
                            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                        
                        # Update palette rect
                        self.palette_rect = pygame.Rect(20, 20, self.screen_width - 40, 60)
                        
                        # Recreate buttons
                        self._create_buttons()
                
                # Draw the editor
                self._draw_editor()
                
                # Cap the frame rate
                clock.tick(60)
            
            # Restore original caption when exiting
            pygame.display.set_caption(original_caption)
            print("Level editor exited normally")
            
            # Only quit pygame if we're not using a shared screen
            if not self.using_shared_screen:
                pygame.quit()
                print("Pygame quit called (standalone mode)")
            else:
                print("Pygame quit skipped (shared screen mode)")
            
        except Exception as e:
            print(f"Error in level editor start method: {e}")
            import traceback
            traceback.print_exc()


# Main function to run the level editor standalone
def main():
    """Main function to run the level editor."""
    editor = GraphicalLevelEditor()
    editor.start()


if __name__ == "__main__":
    main()