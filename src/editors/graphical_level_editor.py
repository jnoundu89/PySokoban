import os
import sys
import pygame
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE, TITLE
from src.core.level import Level
from src.level_management.level_manager import LevelManager
from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
from src.generation.procedural_generator import ProceduralGenerator


class GraphicalLevelEditor:
    """
    A graphical level editor for Sokoban levels.
    """

    def __init__(self, levels_dir='levels', screen=None):
        """
        Initialize the level editor.

        Args:
            levels_dir (str): Directory containing level files
            screen (pygame.Surface): Existing screen to use, or None to create a new one
        """
        # Initialize pygame if not already initialized
        if not pygame.get_init():
            pygame.init()

        # Set up display
        if screen is None:
            self.screen_width = 1024
            self.screen_height = 768
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            pygame.display.set_caption(f"{TITLE} - Level Editor")
        else:
            self.screen = screen
            self.screen_width, self.screen_height = self.screen.get_size()

        # Set up clock
        self.clock = pygame.time.Clock()

        # Set up fonts
        self.title_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 24)

        # Set up level manager
        self.level_manager = LevelManager(levels_dir)

        # Set up skin manager
        self.skin_manager = EnhancedSkinManager()

        # Load configuration
        from src.core.config_manager import get_config_manager
        self.config_manager = get_config_manager()

        # Set up current level
        self.current_level = None

        # Set up editor state
        self.running = False
        self.unsaved_changes = False
        self.selected_element = WALL
        self.show_help = False
        self.show_metrics = False

        # Set up grid
        self.cell_size = CELL_SIZE
        self.grid_offset_x = 100
        self.grid_offset_y = 50

        # Set up palette
        self.palette_elements = [WALL, FLOOR, PLAYER, BOX, TARGET]
        self.palette_rects = []

        for i, element in enumerate(self.palette_elements):
            self.palette_rects.append(pygame.Rect(20, 20 + i * 60, 40, 40))

        # Set up buttons
        self._create_buttons()

    def _create_buttons(self):
        """Create editor buttons."""
        self.buttons = []

        # New button
        new_rect = pygame.Rect(self.screen_width - 100, 20, 80, 30)
        self.buttons.append({
            'text': 'New',
            'rect': new_rect,
            'action': self._show_new_level_dialog
        })

        # Open button
        open_rect = pygame.Rect(self.screen_width - 100, 60, 80, 30)
        self.buttons.append({
            'text': 'Open',
            'rect': open_rect,
            'action': self._show_open_level_dialog
        })

        # Save button
        save_rect = pygame.Rect(self.screen_width - 100, 100, 80, 30)
        self.buttons.append({
            'text': 'Save',
            'rect': save_rect,
            'action': self._show_save_level_dialog
        })

        # Test button
        test_rect = pygame.Rect(self.screen_width - 100, 140, 80, 30)
        self.buttons.append({
            'text': 'Test',
            'rect': test_rect,
            'action': self._toggle_test_mode
        })

        # Generate button
        generate_rect = pygame.Rect(self.screen_width - 100, 180, 80, 30)
        self.buttons.append({
            'text': 'Generate',
            'rect': generate_rect,
            'action': self._show_generate_dialog
        })

    def _create_new_level(self, width, height):
        """
        Create a new level with the given dimensions.

        Args:
            width (int): Width of the new level
            height (int): Height of the new level
        """
        # Create a new level
        level_data = []

        # Add top wall
        level_data.append('#' * width)

        # Add middle rows
        for _ in range(height - 2):
            level_data.append('#' + ' ' * (width - 2) + '#')

        # Add bottom wall
        level_data.append('#' * width)

        # Create level
        self.current_level = Level(level_data='\n'.join(level_data))

        # Mark as having unsaved changes
        self.unsaved_changes = True

    def _show_new_level_dialog(self):
        """Show dialog to create a new level."""
        self._create_new_level(10, 10)

    def _show_open_level_dialog(self):
        """Show dialog to open an existing level."""
        # Create a dialog
        dialog_width = 600
        dialog_height = 500
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2

        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

        # Get list of level files
        level_files = self.level_manager.get_level_files()

        # Create level buttons
        level_buttons = []
        button_height = 30
        button_spacing = 10

        for i, level_file in enumerate(level_files):
            level_name = os.path.basename(level_file)
            level_rect = pygame.Rect(
                dialog_x + 50,
                dialog_y + 80 + i * (button_height + button_spacing),
                dialog_width - 100,
                button_height
            )

            level_buttons.append({
                'text': level_name,
                'rect': level_rect,
                'file': level_file
            })

        # Create cancel button
        cancel_rect = pygame.Rect(dialog_x + dialog_width // 2 - 50, dialog_y + dialog_height - 50, 100, 30)

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

                    # Check if a level button was clicked
                    for button in level_buttons:
                        if button['rect'].collidepoint(mouse_pos):
                            self._open_level(button['file'])
                            dialog_running = False
                            break

                    # Check if cancel button was clicked
                    if cancel_rect.collidepoint(mouse_pos):
                        dialog_running = False

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
            level_file (str): Path to the level file
        """
        try:
            # Load level
            self.current_level = Level(level_file=level_file)

            # Reset unsaved changes flag
            self.unsaved_changes = False
        except Exception as e:
            print(f"Error loading level: {e}")

    def _show_save_level_dialog(self):
        """Show dialog to save the current level."""
        # Create a dialog
        dialog_width = 500
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2

        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

        # Create input field
        input_rect = pygame.Rect(dialog_x + 50, dialog_y + 100, dialog_width - 100, 30)
        input_text = ""
        input_active = True

        # Create buttons
        save_rect = pygame.Rect(dialog_x + dialog_width // 2 - 110, dialog_y + dialog_height - 50, 100, 30)
        cancel_rect = pygame.Rect(dialog_x + dialog_width // 2 + 10, dialog_y + dialog_height - 50, 100, 30)

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
                        if input_text:
                            self._save_level(input_text)
                            dialog_running = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        # Add character to input text if it's valid for a filename
                        if event.unicode.isalnum() or event.unicode in "-_. ":
                            input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    # Check if input field was clicked
                    input_active = input_rect.collidepoint(mouse_pos)

                    # Check if save button was clicked
                    if save_rect.collidepoint(mouse_pos) and input_text:
                        self._save_level(input_text)
                        dialog_running = False

                    # Check if cancel button was clicked
                    elif cancel_rect.collidepoint(mouse_pos):
                        dialog_running = False

            # Draw dialog
            self._draw_editor()  # Draw editor in background

            # Draw dialog box
            pygame.draw.rect(self.screen, (240, 240, 240), dialog_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 2)

            # Draw title
            title_surface = self.title_font.render("Save Level", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
            self.screen.blit(title_surface, title_rect)

            # Draw input label
            label_surface = self.text_font.render("Filename:", True, (0, 0, 0))
            label_rect = label_surface.get_rect(midright=(input_rect.left - 10, input_rect.centery))
            self.screen.blit(label_surface, label_rect)

            # Draw input field
            pygame.draw.rect(self.screen, (255, 255, 255), input_rect)
            pygame.draw.rect(self.screen, (0, 0, 0) if input_active else (100, 100, 100), input_rect, 2)

            # Draw input text
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
            filename (str): Name of the file to save to
        """
        try:
            # Ensure filename has .txt extension
            if not filename.endswith('.txt'):
                filename += '.txt'

            # Get level directory
            level_dir = self.level_manager.levels_dir

            # Create directory if it doesn't exist
            os.makedirs(level_dir, exist_ok=True)

            # Full path to save file
            save_path = os.path.join(level_dir, filename)

            # Save level
            with open(save_path, 'w') as f:
                # Write level data
                for y in range(self.current_level.height):
                    for x in range(self.current_level.width):
                        cell = self.current_level.get_cell(x, y)

                        if cell == WALL:
                            f.write('#')
                        elif cell == FLOOR:
                            f.write(' ')
                        elif cell == PLAYER:
                            f.write('@')
                        elif cell == BOX:
                            f.write('$')
                        elif cell == TARGET:
                            f.write('.')
                        elif cell == PLAYER_ON_TARGET:
                            f.write('+')
                        elif cell == BOX_ON_TARGET:
                            f.write('*')

                    f.write('\n')

            # Reset unsaved changes flag
            self.unsaved_changes = False

            print(f"Level saved to {save_path}")
        except Exception as e:
            print(f"Error saving level: {e}")

    def _toggle_test_mode(self):
        """Toggle test mode to validate the level."""
        # Validate level
        is_valid, message = self._validate_level()

        if is_valid:
            print("Level is valid!")
        else:
            print(f"Level validation failed: {message}")

    def _validate_level(self, show_dialog=True):
        """
        Validate the current level.

        Args:
            show_dialog (bool): Whether to show a dialog with the validation result

        Returns:
            tuple: (is_valid, message)
        """
        # Check if level exists
        if self.current_level is None:
            return False, "No level to validate"

        # Check if level has a player
        has_player = False
        for y in range(self.current_level.height):
            for x in range(self.current_level.width):
                cell = self.current_level.get_cell(x, y)
                if cell == PLAYER or cell == PLAYER_ON_TARGET:
                    has_player = True
                    break
            if has_player:
                break

        if not has_player:
            if show_dialog:
                # Create a dialog
                dialog_width = 400
                dialog_height = 150
                dialog_x = (self.screen_width - dialog_width) // 2
                dialog_y = (self.screen_height - dialog_height) // 2

                dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

                # Create OK button
                ok_rect = pygame.Rect(dialog_x + dialog_width // 2 - 50, dialog_y + dialog_height - 50, 100, 30)

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
                    title_surface = self.title_font.render("Validation Error", True, (200, 0, 0))
                    title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
                    self.screen.blit(title_surface, title_rect)

                    # Draw message
                    message_surface = self.text_font.render("Level must have a player!", True, (0, 0, 0))
                    message_rect = message_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 70))
                    self.screen.blit(message_surface, message_rect)

                    # Draw OK button
                    pygame.draw.rect(self.screen, (100, 100, 200), ok_rect)
                    pygame.draw.rect(self.screen, (0, 0, 0), ok_rect, 1)

                    ok_text = self.text_font.render("OK", True, (255, 255, 255))
                    ok_text_rect = ok_text.get_rect(center=ok_rect.center)
                    self.screen.blit(ok_text, ok_text_rect)

                    pygame.display.flip()

            return False, "Level must have a player"

        # Check if level has boxes and targets
        box_count = 0
        target_count = 0

        for y in range(self.current_level.height):
            for x in range(self.current_level.width):
                cell = self.current_level.get_cell(x, y)
                if cell == BOX or cell == BOX_ON_TARGET:
                    box_count += 1
                if cell == TARGET or cell == PLAYER_ON_TARGET or cell == BOX_ON_TARGET:
                    target_count += 1

        if box_count == 0 or target_count == 0:
            if show_dialog:
                # Create a dialog
                dialog_width = 400
                dialog_height = 150
                dialog_x = (self.screen_width - dialog_width) // 2
                dialog_y = (self.screen_height - dialog_height) // 2

                dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

                # Create OK button
                ok_rect = pygame.Rect(dialog_x + dialog_width // 2 - 50, dialog_y + dialog_height - 50, 100, 30)

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
                    title_surface = self.title_font.render("Validation Error", True, (200, 0, 0))
                    title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
                    self.screen.blit(title_surface, title_rect)

                    # Draw message
                    message_surface = self.text_font.render("Level must have boxes and targets!", True, (0, 0, 0))
                    message_rect = message_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 70))
                    self.screen.blit(message_surface, message_rect)

                    # Draw OK button
                    pygame.draw.rect(self.screen, (100, 100, 200), ok_rect)
                    pygame.draw.rect(self.screen, (0, 0, 0), ok_rect, 1)

                    ok_text = self.text_font.render("OK", True, (255, 255, 255))
                    ok_text_rect = ok_text.get_rect(center=ok_rect.center)
                    self.screen.blit(ok_text, ok_text_rect)

                    pygame.display.flip()

            return False, "Level must have boxes and targets"

        # Check if box count matches target count
        if box_count != target_count:
            if show_dialog:
                # Create a dialog
                dialog_width = 400
                dialog_height = 150
                dialog_x = (self.screen_width - dialog_width) // 2
                dialog_y = (self.screen_height - dialog_height) // 2

                dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

                # Create OK button
                ok_rect = pygame.Rect(dialog_x + dialog_width // 2 - 50, dialog_y + dialog_height - 50, 100, 30)

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
                    title_surface = self.title_font.render("Validation Error", True, (200, 0, 0))
                    title_rect = title_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
                    self.screen.blit(title_surface, title_rect)

                    # Draw message
                    message = f"Box count ({box_count}) must match target count ({target_count})!"
                    message_surface = self.text_font.render(message, True, (0, 0, 0))
                    message_rect = message_surface.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 70))
                    self.screen.blit(message_surface, message_rect)

                    # Draw OK button
                    pygame.draw.rect(self.screen, (100, 100, 200), ok_rect)
                    pygame.draw.rect(self.screen, (0, 0, 0), ok_rect, 1)

                    ok_text = self.text_font.render("OK", True, (255, 255, 255))
                    ok_text_rect = ok_text.get_rect(center=ok_rect.center)
                    self.screen.blit(ok_text, ok_text_rect)

                    pygame.display.flip()

            return False, f"Box count ({box_count}) must match target count ({target_count})"

        # Level is valid
        is_valid = True

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
                        elif no_rect.collidepoint(mouse_pos):
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
                pygame.draw.rect(self.screen, (100, 200, 100), yes_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), yes_rect, 1)

                yes_text = self.text_font.render("Yes", True, (255, 255, 255))
                yes_text_rect = yes_text.get_rect(center=yes_rect.center)
                self.screen.blit(yes_text, yes_text_rect)

                # Draw no button
                pygame.draw.rect(self.screen, (200, 100, 100), no_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), no_rect, 1)

                no_text = self.text_font.render("No", True, (255, 255, 255))
                no_text_rect = no_text.get_rect(center=no_rect.center)
                self.screen.blit(no_text, no_text_rect)

                pygame.display.flip()
        else:
            self.running = False

    def _handle_grid_click(self, mouse_pos, mouse_button):
        """Handle click on the grid."""
        # Calculate grid coordinates
        grid_x = (mouse_pos[0] - self.grid_offset_x) // self.cell_size
        grid_y = (mouse_pos[1] - self.grid_offset_y) // self.cell_size

        # Check if click is within grid bounds
        if 0 <= grid_x < self.current_level.width and 0 <= grid_y < self.current_level.height:
            # Left click: place selected element
            if mouse_button == 1:
                self._place_element(grid_x, grid_y)
            # Right click: clear element
            elif mouse_button == 3:
                self._clear_element(grid_x, grid_y)

            # Mark level as having unsaved changes
            self.unsaved_changes = True

    def _place_element(self, x, y):
        """Place the currently selected element at the given grid coordinates."""
        # Get current cell content
        current_cell = self.current_level.get_cell(x, y)

        # Handle different element types
        if self.selected_element == WALL:
            # Place wall
            self.current_level.set_cell(x, y, WALL)

        elif self.selected_element == FLOOR:
            # Place floor
            self.current_level.set_cell(x, y, FLOOR)

        elif self.selected_element == PLAYER:
            # Remove existing player if any
            for i in range(self.current_level.width):
                for j in range(self.current_level.height):
                    if self.current_level.get_cell(i, j) == PLAYER or self.current_level.get_cell(i, j) == PLAYER_ON_TARGET:
                        if self.current_level.get_cell(i, j) == PLAYER_ON_TARGET:
                            self.current_level.set_cell(i, j, TARGET)
                        else:
                            self.current_level.set_cell(i, j, FLOOR)

            # Place player
            if current_cell == TARGET:
                self.current_level.set_cell(x, y, PLAYER_ON_TARGET)
            else:
                self.current_level.set_cell(x, y, PLAYER)

        elif self.selected_element == BOX:
            # Place box
            if current_cell == TARGET:
                self.current_level.set_cell(x, y, BOX_ON_TARGET)
            else:
                self.current_level.set_cell(x, y, BOX)

        elif self.selected_element == TARGET:
            # Place target
            if current_cell == PLAYER:
                self.current_level.set_cell(x, y, PLAYER_ON_TARGET)
            elif current_cell == BOX:
                self.current_level.set_cell(x, y, BOX_ON_TARGET)
            else:
                self.current_level.set_cell(x, y, TARGET)

    def _clear_element(self, x, y):
        """Clear the element at the given grid coordinates."""
        current_cell = self.current_level.get_cell(x, y)

        # Handle different cell types
        if current_cell == PLAYER_ON_TARGET:
            self.current_level.set_cell(x, y, TARGET)
        elif current_cell == BOX_ON_TARGET:
            self.current_level.set_cell(x, y, TARGET)
        else:
            self.current_level.set_cell(x, y, FLOOR)

    def _handle_palette_click(self, mouse_pos):
        """Handle click on the palette."""
        # Calculate which palette element was clicked
        for i, rect in enumerate(self.palette_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_element = self.palette_elements[i]
                break

    def _draw_editor(self):
        """Draw the editor interface."""
        # Fill background
        self.screen.fill((50, 50, 50))

        # Draw grid
        grid_width = self.current_level.width * self.cell_size
        grid_height = self.current_level.height * self.cell_size

        # Draw grid background
        grid_rect = pygame.Rect(self.grid_offset_x, self.grid_offset_y, grid_width, grid_height)
        pygame.draw.rect(self.screen, (30, 30, 30), grid_rect)

        # Draw cells
        for y in range(self.current_level.height):
            for x in range(self.current_level.width):
                cell_x = self.grid_offset_x + x * self.cell_size
                cell_y = self.grid_offset_y + y * self.cell_size

                # Get cell content
                cell = self.current_level.get_cell(x, y)

                # Get the skin
                skin = self.skin_manager.get_skin()

                # Draw cell
                if cell == WALL:
                    self.screen.blit(skin[WALL], (cell_x, cell_y))
                elif cell == FLOOR:
                    self.screen.blit(skin[FLOOR], (cell_x, cell_y))
                elif cell == PLAYER:
                    self.screen.blit(skin[FLOOR], (cell_x, cell_y))
                    self.screen.blit(skin[PLAYER], (cell_x, cell_y))
                elif cell == BOX:
                    self.screen.blit(skin[FLOOR], (cell_x, cell_y))
                    self.screen.blit(skin[BOX], (cell_x, cell_y))
                elif cell == TARGET:
                    self.screen.blit(skin[FLOOR], (cell_x, cell_y))
                    self.screen.blit(skin[TARGET], (cell_x, cell_y))
                elif cell == PLAYER_ON_TARGET:
                    self.screen.blit(skin[FLOOR], (cell_x, cell_y))
                    self.screen.blit(skin[TARGET], (cell_x, cell_y))
                    self.screen.blit(skin[PLAYER], (cell_x, cell_y))
                elif cell == BOX_ON_TARGET:
                    self.screen.blit(skin[FLOOR], (cell_x, cell_y))
                    self.screen.blit(skin[TARGET], (cell_x, cell_y))
                    self.screen.blit(skin[BOX], (cell_x, cell_y))

        # Draw grid lines using color from config
        grid_color_list = self.config_manager.get('game', 'grid_color', [255, 255, 255])
        grid_color = tuple(grid_color_list)

        for x in range(self.current_level.width + 1):
            pygame.draw.line(self.screen, grid_color,
                            (self.grid_offset_x + x * self.cell_size, self.grid_offset_y),
                            (self.grid_offset_x + x * self.cell_size, self.grid_offset_y + grid_height))

        for y in range(self.current_level.height + 1):
            pygame.draw.line(self.screen, grid_color,
                            (self.grid_offset_x, self.grid_offset_y + y * self.cell_size),
                            (self.grid_offset_x + grid_width, self.grid_offset_y + y * self.cell_size))

        # Draw palette
        palette_rect = pygame.Rect(10, 10, 60, 300)
        pygame.draw.rect(self.screen, (70, 70, 70), palette_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), palette_rect, 2)

        # Draw palette elements
        for i, element in enumerate(self.palette_elements):
            rect = self.palette_rects[i]

            # Highlight selected element
            if element == self.selected_element:
                pygame.draw.rect(self.screen, (150, 150, 150), rect)

            # Get the skin
            skin = self.skin_manager.get_skin()

            # Draw element
            if element == WALL:
                self.screen.blit(skin[WALL], rect)
            elif element == FLOOR:
                self.screen.blit(skin[FLOOR], rect)
            elif element == PLAYER:
                self.screen.blit(skin[FLOOR], rect)
                self.screen.blit(skin[PLAYER], rect)
            elif element == BOX:
                self.screen.blit(skin[FLOOR], rect)
                self.screen.blit(skin[BOX], rect)
            elif element == TARGET:
                self.screen.blit(skin[FLOOR], rect)
                self.screen.blit(skin[TARGET], rect)

        # Draw buttons
        for button in self.buttons:
            pygame.draw.rect(self.screen, (70, 70, 70), button['rect'])
            pygame.draw.rect(self.screen, (100, 100, 100), button['rect'], 2)

            text_surface = self.text_font.render(button['text'], True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=button['rect'].center)
            self.screen.blit(text_surface, text_rect)

        # Draw help screen if enabled
        if self.show_help:
            self._draw_help_screen()

        # Draw metrics screen if enabled
        if self.show_metrics:
            self._draw_metrics_screen()

    def _draw_help_screen(self):
        """Draw the help screen overlay."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Draw help content
        help_width = 600
        help_height = 500
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
        help_text = [
            "Left-click: Place selected element",
            "Right-click: Clear element (replace with floor)",
            "N: Create new level",
            "O: Open existing level",
            "S: Save level",
            "T: Test level (validate)",
            "G: Generate random level",
            "H: Toggle help screen",
            "M: Toggle metrics display",
            "Esc: Exit editor"
        ]

        for i, line in enumerate(help_text):
            text_surface = self.text_font.render(line, True, (0, 0, 0))
            text_rect = text_surface.get_rect(midleft=(help_x + 50, help_y + 100 + i * 30))
            self.screen.blit(text_surface, text_rect)

        # Draw close button
        close_rect = pygame.Rect(help_x + help_width // 2 - 50, help_y + help_height - 50, 100, 30)
        pygame.draw.rect(self.screen, (200, 100, 100), close_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), close_rect, 1)

        close_text = self.text_font.render("Close", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        self.screen.blit(close_text, close_text_rect)

    def _draw_metrics_screen(self):
        """Draw the metrics screen overlay."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Draw metrics content
        metrics_width = 600
        metrics_height = 500
        metrics_x = (self.screen_width - metrics_width) // 2
        metrics_y = (self.screen_height - metrics_height) // 2

        metrics_rect = pygame.Rect(metrics_x, metrics_y, metrics_width, metrics_height)
        pygame.draw.rect(self.screen, (240, 240, 240), metrics_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), metrics_rect, 2)

        # Draw title
        title_surface = self.title_font.render("Level Metrics", True, (0, 0, 0))
        title_rect = title_surface.get_rect(center=(metrics_x + metrics_width // 2, metrics_y + 30))
        self.screen.blit(title_surface, title_rect)

        # Validate level and get metrics
        is_valid, message = self._validate_level(show_dialog=False)

        if is_valid:
            # Basic metrics
            self._draw_metric_line("Level size:", f"{self.current_level.width}x{self.current_level.height}", 
                                  metrics_x + 50, metrics_y + 80)

            # Count elements
            wall_count = 0
            box_count = 0
            target_count = 0

            for y in range(self.current_level.height):
                for x in range(self.current_level.width):
                    cell = self.current_level.get_cell(x, y)
                    if cell == WALL:
                        wall_count += 1
                    elif cell == BOX or cell == BOX_ON_TARGET:
                        box_count += 1
                    elif cell == TARGET or cell == PLAYER_ON_TARGET or cell == BOX_ON_TARGET:
                        target_count += 1

            self._draw_metric_line("Wall count:", str(wall_count), metrics_x + 50, metrics_y + 110)
            self._draw_metric_line("Box count:", str(box_count), metrics_x + 50, metrics_y + 140)
            self._draw_metric_line("Target count:", str(target_count), metrics_x + 50, metrics_y + 170)

            # Check if boxes and targets match
            if box_count == target_count:
                self._draw_metric_line("Boxes and targets:", "Match ✓", metrics_x + 50, metrics_y + 200, (0, 150, 0))
            else:
                self._draw_metric_line("Boxes and targets:", "Don't match ✗", metrics_x + 50, metrics_y + 200, (150, 0, 0))

            # Calculate playable area
            playable_area = self.current_level.width * self.current_level.height - wall_count
            self._draw_metric_line("Playable area:", f"{playable_area} tiles", metrics_x + 50, metrics_y + 230)

            # Calculate box density
            if playable_area > 0:
                box_density = box_count / playable_area
                self._draw_metric_line("Box density:", f"{box_density:.2f}", metrics_x + 50, metrics_y + 260)

            # Solvability status
            self._draw_metric_line("Solvability:", "Unknown (not tested)", metrics_x + 50, metrics_y + 290, (100, 100, 100))
        else:
            # Display validation error
            error_surface = self.text_font.render(message, True, (150, 0, 0))
            error_rect = error_surface.get_rect(center=(metrics_x + metrics_width // 2, metrics_y + 150))
            self.screen.blit(error_surface, error_rect)

        # Draw close button
        close_rect = pygame.Rect(metrics_x + metrics_width // 2 - 50, metrics_y + metrics_height - 50, 100, 30)
        pygame.draw.rect(self.screen, (200, 100, 100), close_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), close_rect, 1)

        close_text = self.text_font.render("Close", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        self.screen.blit(close_text, close_text_rect)

    def _draw_metric_line(self, label, value, base_x, y, value_color=(255, 255, 255)):
        """Draw a metric line with label and value."""
        label_surface = self.text_font.render(label, True, (0, 0, 0))
        label_rect = label_surface.get_rect(midleft=(base_x, y))
        self.screen.blit(label_surface, label_rect)

        value_surface = self.text_font.render(value, True, value_color)
        value_rect = value_surface.get_rect(midleft=(base_x + 200, y))
        self.screen.blit(value_surface, value_rect)

    def start(self):
        """Start the level editor."""
        self.running = True

        # Create a new level if none exists
        if self.current_level is None:
            self._create_new_level(10, 10)

        # Main loop
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._exit_editor()
                    elif event.key == pygame.K_n:
                        self._show_new_level_dialog()
                    elif event.key == pygame.K_o:
                        self._show_open_level_dialog()
                    elif event.key == pygame.K_s:
                        self._show_save_level_dialog()
                    elif event.key == pygame.K_t:
                        self._toggle_test_mode()
                    elif event.key == pygame.K_g:
                        self._show_generate_dialog()
                    elif event.key == pygame.K_h:
                        self._toggle_help()
                    elif event.key == pygame.K_m:
                        self._toggle_metrics()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    # Check if a button was clicked
                    for button in self.buttons:
                        if button['rect'].collidepoint(mouse_pos):
                            button['action']()
                            break
                    else:
                        # Check if palette was clicked
                        for rect in self.palette_rects:
                            if rect.collidepoint(mouse_pos):
                                self._handle_palette_click(mouse_pos)
                                break
                        else:
                            # Check if grid was clicked
                            grid_rect = pygame.Rect(
                                self.grid_offset_x, self.grid_offset_y,
                                self.current_level.width * self.cell_size,
                                self.current_level.height * self.cell_size
                            )

                            if grid_rect.collidepoint(mouse_pos):
                                self._handle_grid_click(mouse_pos, event.button)

            # Draw editor
            self._draw_editor()

            # Update display
            pygame.display.flip()

            # Cap the frame rate
            self.clock.tick(60)


def main():
    """Main function to run the level editor."""
    editor = GraphicalLevelEditor()
    editor.start()


if __name__ == "__main__":
    main()
