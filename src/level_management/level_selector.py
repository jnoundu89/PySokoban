"""
Level Selector module for the Sokoban game.

This module provides a level selection interface organized by categories/folders.
"""

import os
import pygame
from src.core.constants import TITLE, CELL_SIZE, WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET
from src.core.level import Level
from src.level_management.level_collection_parser import LevelCollectionParser
from src.ui.level_preview import LevelPreview
from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager

class LevelCategory:
    """Represents a category of levels."""

    def __init__(self, name, display_name, levels, is_collection=False, collection_file=None):
        """
        Initialize a level category.

        Args:
            name (str): Internal name of the category
            display_name (str): Display name for the category
            levels (list): List of level file paths or level info tuples
            is_collection (bool): Whether this category represents a collection
            collection_file (str): Path to the collection file if is_collection is True
        """
        self.name = name
        self.display_name = display_name
        self.levels = levels
        self.is_collection = is_collection
        self.collection_file = collection_file

class LevelInfo:
    """Represents information about a single level."""

    def __init__(self, title, collection_file, level_index, is_from_collection=False):
        """
        Initialize level information.

        Args:
            title (str): Title of the level
            collection_file (str): Path to the collection file or level file
            level_index (int): Index of the level in the collection (or -1 for single files)
            is_from_collection (bool): Whether this level is from a collection
        """
        self.title = title
        self.collection_file = collection_file
        self.level_index = level_index
        self.is_from_collection = is_from_collection

    def __eq__(self, other):
        """
        Compare two LevelInfo objects for equality.

        Args:
            other: Another LevelInfo object to compare with

        Returns:
            bool: True if the objects represent the same level, False otherwise
        """
        if not isinstance(other, LevelInfo):
            return False
        return (self.title == other.title and 
                self.collection_file == other.collection_file and 
                self.level_index == other.level_index and 
                self.is_from_collection == other.is_from_collection)

    def __ne__(self, other):
        """
        Compare two LevelInfo objects for inequality.

        Args:
            other: Another LevelInfo object to compare with

        Returns:
            bool: True if the objects represent different levels, False otherwise
        """
        return not self.__eq__(other)

class Button:
    """A clickable button for the level selector."""

    def __init__(self, text, x, y, width, height, action=None, color=(100, 100, 200), hover_color=(130, 130, 255), text_color=(255, 255, 255)):
        """Initialize a button."""
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = self.color
        self.font = pygame.font.Font(None, 32)
        self.is_pressed = False  # Track if button is being pressed

    def draw(self, screen):
        """Draw the button on the screen."""
        pygame.draw.rect(screen, self.current_color, (self.x, self.y, self.width, self.height), 0, 10)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        """Check if the mouse is hovering over the button."""
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

    def update(self, mouse_pos):
        """Update the button's appearance based on mouse position."""
        if self.is_hovered(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

    def handle_event(self, event):
        """Handle mouse events for the button."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered(pygame.mouse.get_pos()):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.is_hovered(pygame.mouse.get_pos()):
                self.is_pressed = False
                if self.action:
                    self.action()
                return True
            self.is_pressed = False
        return False

class LevelSelector:
    """
    Level selector interface for choosing levels organized by categories.
    """

    def __init__(self, screen, screen_width, screen_height, levels_dir='levels'):
        """
        Initialize the level selector.

        Args:
            screen: Pygame surface to draw on
            screen_width (int): Width of the screen
            screen_height (int): Height of the screen
            levels_dir (str): Directory containing level files
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.levels_dir = levels_dir

        # Define colors
        self.colors = {
            'background': (240, 240, 240),
            'text': (50, 50, 50),
            'button': (100, 100, 200),
            'button_hover': (130, 130, 255),
            'button_text': (255, 255, 255),
            'title': (70, 70, 150),
            'category_button': (80, 150, 80),
            'category_button_hover': (100, 180, 100),
            'level_button': (150, 100, 80),
            'level_button_hover': (180, 130, 100),
            # Colors for hover preview
            'preview_bg': (255, 255, 255),
            'preview_border': (100, 100, 100),
            'wall': (80, 80, 80),
            'floor': (220, 220, 220),
            'player': (0, 100, 200),
            'box': (180, 120, 80),
            'target': (200, 50, 50),
            'player_on_target': (0, 150, 200),
            'box_on_target': (200, 150, 80)
        }

        # Load fonts
        self.title_font = pygame.font.Font(None, 64)
        self.subtitle_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 24)

        # State management
        self.current_view = 'categories'  # 'categories' or 'levels'
        self.selected_category = None
        self.running = False
        self.selected_level = None

        # Scroll management
        self.scroll_offset = 0
        self.category_scroll_offset = 0
        self.max_visible_buttons = 10  # Maximum buttons visible at once

        # Scrollbar information
        self.category_scrollbar = {'x': 0, 'y': 0, 'width': 0, 'height': 0, 'thumb_y': 0, 'thumb_height': 0}
        self.level_scrollbar = {'x': 0, 'y': 0, 'width': 0, 'height': 0, 'thumb_y': 0, 'thumb_height': 0}

        # Scrollbar interaction state
        self.scrollbar_active = False
        self.scrollbar_last_pos = None

        # Level preview
        self.level_preview = LevelPreview(screen, screen_width, screen_height)
        self.popup_open = False  # Flag to track if popup is open
        self.popup_close_time = 0  # Time when popup was closed
        self.click_protection_delay = 200  # ms to ignore clicks after popup closes

        # Initialize skin manager to use the configured skin
        self.skin_manager = EnhancedSkinManager()

        # Hover preview
        self.hovered_level_info = None
        self.hover_preview_level = None

        # Load level categories
        self.categories = self._load_level_categories()

        # No UI layout containers needed in the original implementation

        # Create buttons
        self.category_buttons = []
        self.level_buttons = []
        self.back_button = None
        self._create_buttons()

    def _load_level_categories(self):
        """Load and categorize levels from the levels directory."""
        categories = []

        if not os.path.exists(self.levels_dir):
            return categories

        # Check for subdirectories first
        subdirs = [
            d for d in os.listdir(self.levels_dir)
            if os.path.isdir(os.path.join(self.levels_dir, d))
        ]

        if subdirs:
            # Use subdirectories as categories
            for subdir in sorted(subdirs):
                subdir_path = os.path.join(self.levels_dir, subdir)
                files_in_subdir = [
                    os.path.join(subdir_path, f) for f in os.listdir(subdir_path)
                    if f.endswith('.txt') and os.path.isfile(os.path.join(subdir_path, f))
                ]

                if files_in_subdir:
                    files_in_subdir.sort()

                    # Create display name based on folder name
                    display_name = subdir.replace('_', ' ').replace('-', ' ').title()
                    if subdir.lower() == 'classic':
                        display_name = 'Niveaux Classiques'
                    elif subdir.lower() == 'original':
                        display_name = 'Niveaux Originaux'
                    elif subdir.lower() == 'generated':
                        display_name = 'Niveaux Générés'
                    elif subdir.lower() == 'advanced generated':
                        display_name = 'Niveaux IA Avancés'
                    elif subdir.lower() == 'test':
                        display_name = 'Niveaux de Test'

                    # Check if any file is a collection
                    level_infos = []
                    for file_path in files_in_subdir:
                        try:
                            # Try to parse as collection
                            collection = LevelCollectionParser.parse_file(file_path)
                            if collection.get_level_count() > 1:
                                # This is a collection, add each level as a separate entry
                                for i in range(collection.get_level_count()):
                                    level_title, _ = collection.get_level(i)
                                    display_title = level_title if level_title else f"Niveau {i+1}"
                                    level_infos.append(LevelInfo(display_title, file_path, i, True))
                            else:
                                # Single level file
                                filename = os.path.splitext(os.path.basename(file_path))[0]
                                display_title = filename.replace('_', ' ').title()
                                level_infos.append(LevelInfo(display_title, file_path, -1, False))
                        except:
                            # Not a collection, treat as single level
                            filename = os.path.splitext(os.path.basename(file_path))[0]
                            display_title = filename.replace('_', ' ').title()
                            level_infos.append(LevelInfo(display_title, file_path, -1, False))

                    if level_infos:
                        categories.append(LevelCategory(subdir.lower().replace(' ', '_'), display_name, level_infos))
        else:
            # Fallback to old method if no subdirectories
            all_files = [
                os.path.join(self.levels_dir, f) for f in os.listdir(self.levels_dir)
                if f.endswith('.txt') and os.path.isfile(os.path.join(self.levels_dir, f))
            ]

            # Categorize levels based on filename patterns
            classic_level_infos = []
            generated_level_infos = []
            advanced_generated_level_infos = []

            for file_path in all_files:
                filename = os.path.basename(file_path)

                # Try to parse as collection first
                try:
                    collection = LevelCollectionParser.parse_file(file_path)
                    if collection.get_level_count() > 1:
                        # This is a collection, add each level as a separate entry
                        level_infos = []
                        for i in range(collection.get_level_count()):
                            level_title, _ = collection.get_level(i)
                            display_title = level_title if level_title else f"Niveau {i+1}"
                            level_infos.append(LevelInfo(display_title, file_path, i, True))

                        # Categorize based on filename
                        if filename.startswith('advanced_generated'):
                            advanced_generated_level_infos.extend(level_infos)
                        elif filename.startswith('generated'):
                            generated_level_infos.extend(level_infos)
                        else:
                            classic_level_infos.extend(level_infos)
                        continue
                except:
                    pass

                # Single level file
                display_title = os.path.splitext(filename)[0].replace('_', ' ').title()
                level_info = LevelInfo(display_title, file_path, -1, False)

                if filename.startswith('advanced_generated'):
                    advanced_generated_level_infos.append(level_info)
                elif filename.startswith('generated'):
                    generated_level_infos.append(level_info)
                else:
                    classic_level_infos.append(level_info)

            # Create categories
            if classic_level_infos:
                categories.append(LevelCategory('classic', 'Niveaux Classiques', classic_level_infos))
            if generated_level_infos:
                categories.append(LevelCategory('generated', 'Niveaux Générés', generated_level_infos))
            if advanced_generated_level_infos:
                categories.append(LevelCategory('advanced', 'Niveaux IA Avancés', advanced_generated_level_infos))

        return categories

    def _create_buttons(self):
        """Create buttons for the current view."""
        self._create_category_buttons()
        self._create_back_button()

    def _create_category_buttons(self):
        """Create buttons for category selection."""
        self.category_buttons = []

        if not self.categories:
            return

        button_width = 600  # Doubled the width as requested
        button_height = 70  # Slightly increased the height as requested
        button_spacing = 20

        # Calculate visible area
        available_height = self.screen_height - 250  # Leave space for title and instructions
        max_visible_categories = max(1, available_height // (button_height + button_spacing))

        # Calculate scroll bounds
        total_categories = len(self.categories)
        max_scroll_offset = max(0, total_categories - max_visible_categories)
        self.category_scroll_offset = max(0, min(self.category_scroll_offset, max_scroll_offset))

        # Calculate start position
        start_y = 220
        button_x = (self.screen_width - button_width) // 2

        # Only create buttons for visible categories
        start_category = self.category_scroll_offset
        end_category = min(start_category + max_visible_categories, total_categories)

        for i in range(start_category, end_category):
            category = self.categories[i]

            # Calculate position relative to visible area
            visible_index = i - start_category
            y = start_y + visible_index * (button_height + button_spacing)

            button = Button(
                f"{category.display_name} ({len(category.levels)})",
                button_x, y, button_width, button_height,
                action=lambda cat=category: self._select_category(cat),
                color=self.colors['category_button'],
                hover_color=self.colors['category_button_hover']
            )
            self.category_buttons.append(button)

    def _create_level_buttons(self):
        """Create buttons for level selection within a category."""
        self.level_buttons = []

        if not self.selected_category:
            return

        button_width = 600  # Doubled the width as requested
        button_height = 60  # Slightly increased the height as requested
        button_spacing = 15

        # Calculate grid layout
        buttons_per_row = max(1, (self.screen_width - 100) // (button_width + 20))

        # Calculate visible area
        available_height = self.screen_height - 250  # Leave space for title and instructions
        max_visible_rows = max(1, available_height // (button_height + button_spacing))

        # Calculate scroll bounds
        total_levels = len(self.selected_category.levels)
        total_rows = (total_levels + buttons_per_row - 1) // buttons_per_row
        max_scroll_offset = max(0, total_rows - max_visible_rows)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll_offset))

        start_y = 220
        start_x = (self.screen_width - (buttons_per_row * button_width + (buttons_per_row - 1) * 20)) // 2

        # Only create buttons for visible levels
        start_level = self.scroll_offset * buttons_per_row
        end_level = min(start_level + max_visible_rows * buttons_per_row, total_levels)

        for i in range(start_level, end_level):
            level_info = self.selected_category.levels[i]

            # Calculate position relative to visible area
            visible_index = i - start_level
            row = visible_index // buttons_per_row
            col = visible_index % buttons_per_row

            x = start_x + col * (button_width + 20)
            y = start_y + row * (button_height + button_spacing)

            button = Button(
                level_info.title,
                x, y, button_width, button_height,
                action=lambda info=level_info: self._select_level_info(info),
                color=self.colors['level_button'],
                hover_color=self.colors['level_button_hover']
            )
            self.level_buttons.append(button)

    def _create_back_button(self):
        """Create the back button."""
        self.back_button = Button(
            "Retour", 20, self.screen_height - 60, 100, 40,
            action=self._go_back,
            color=(200, 100, 100),
            hover_color=(255, 130, 130)
        )

    def _select_category(self, category):
        """Select a category and show its levels."""
        self.selected_category = category
        self.current_view = 'levels'
        self.scroll_offset = 0  # Reset scroll position
        self._create_level_buttons()

    def _select_level_info(self, level_info):
        """Show level preview and handle the user's choice."""
        # Set popup flag to disable level button handling
        self.popup_open = True

        # Show the level preview popup
        action = self.level_preview.show_level_preview(level_info)

        # Clear any remaining events from the pygame queue to prevent
        # click events from leaking to level buttons
        pygame.event.clear()

        # Reset popup flag and record close time
        self.popup_open = False
        self.popup_close_time = pygame.time.get_ticks()

        if action == 'play':
            # User wants to play the level
            if level_info.is_from_collection:
                # Store collection info for the game to use
                self.selected_level = {
                    'type': 'collection_level',
                    'collection_file': level_info.collection_file,
                    'level_index': level_info.level_index,
                    'title': level_info.title
                }
            else:
                # Single level file
                self.selected_level = {
                    'type': 'single_level',
                    'file_path': level_info.collection_file,
                    'title': level_info.title
                }
            self.running = False
        # If action is 'back', we just continue in the level selection

    def _select_level(self, level_path):
        """Select a level and exit the selector (legacy method)."""
        self.selected_level = {
            'type': 'single_level',
            'file_path': level_path,
            'title': os.path.splitext(os.path.basename(level_path))[0]
        }
        self.running = False

    def _go_back(self):
        """Go back to the previous view or exit."""
        if self.current_view == 'levels':
            self.current_view = 'categories'
            self.selected_category = None
            self.level_buttons = []
        else:
            # Exit to main menu
            self.running = False

    def _handle_scrollbar_click(self, pos, event_type):
        """
        Handle interactions with the scrollbar.

        Args:
            pos: (x, y) tuple of mouse position
            event_type: Type of event (MOUSEBUTTONDOWN, MOUSEBUTTONUP, or MOUSEMOTION)

        Returns:
            bool: True if the interaction was with a scrollbar and handled, False otherwise
        """
        # Determine which scrollbar to check based on current view
        scrollbar = self.category_scrollbar if self.current_view == 'categories' else self.level_scrollbar

        # Handle mouse down event - start scrollbar interaction
        if event_type == pygame.MOUSEBUTTONDOWN:
            # Check if click is within scrollbar bounds
            if (scrollbar['x'] <= pos[0] <= scrollbar['x'] + scrollbar['width'] and
                scrollbar['y'] <= pos[1] <= scrollbar['y'] + scrollbar['height']):

                self.scrollbar_active = True
                self.scrollbar_last_pos = pos

                # Process the initial click position
                self._process_scrollbar_position(pos)
                return True

        # Handle mouse up event - end scrollbar interaction
        elif event_type == pygame.MOUSEBUTTONUP:
            if self.scrollbar_active:
                self.scrollbar_active = False
                self.scrollbar_last_pos = None
                return True

        # Handle mouse motion event - continue scrolling if active
        elif event_type == pygame.MOUSEMOTION and self.scrollbar_active:
            # Process the current mouse position
            self._process_scrollbar_position(pos)
            return True

        return False

    def _process_scrollbar_position(self, pos):
        """
        Process the scrollbar position and update scroll offset.

        Args:
            pos: (x, y) tuple of mouse position
        """
        # Determine which scrollbar to use based on current view
        scrollbar = self.category_scrollbar if self.current_view == 'categories' else self.level_scrollbar

        # Check if position is within scrollbar bounds
        if (scrollbar['x'] <= pos[0] <= scrollbar['x'] + scrollbar['width'] and
            scrollbar['y'] <= pos[1] <= scrollbar['y'] + scrollbar['height']):

            # Calculate the relative position in the scrollbar
            # This allows for direct positioning based on where the user clicked
            if scrollbar['height'] > 0:  # Prevent division by zero
                relative_pos = (pos[1] - scrollbar['y']) / scrollbar['height']
                new_scroll = int(relative_pos * scrollbar['max_scroll'])

                # Update the appropriate scroll offset
                if self.current_view == 'categories':
                    self.category_scroll_offset = max(0, min(new_scroll, scrollbar['max_scroll']))
                    self._create_category_buttons()
                else:
                    self.scroll_offset = max(0, min(new_scroll, scrollbar['max_scroll']))
                    self._create_level_buttons()

    def _render_hover_preview(self, level_info):
        """
        Render a preview of the level when hovering over its button.

        Args:
            level_info: LevelInfo object containing level information
        """
        # Always load the level when this method is called to ensure fresh data
        try:
            if level_info.is_from_collection:
                collection = LevelCollectionParser.parse_file(level_info.collection_file)
                _, level = collection.get_level(level_info.level_index)
            else:
                level = Level(level_file=level_info.collection_file)
            self.hover_preview_level = level
            # Update the hovered_level_info to the current level_info
            self.hovered_level_info = level_info
        except Exception as e:
            print(f"Error loading level for hover preview: {e}")
            return

        # Get mouse position for positioning the preview
        mouse_pos = pygame.mouse.get_pos()

        # Define preview dimensions - responsive to screen size
        preview_width = min(250, max(150, int(self.screen_width * 0.15)))
        preview_height = min(250, max(150, int(self.screen_height * 0.25)))

        # Position the preview near the mouse cursor but ensure it stays on screen
        preview_x = min(mouse_pos[0] + 20, self.screen_width - preview_width - 10)
        preview_y = min(mouse_pos[1] + 20, self.screen_height - preview_height - 10)

        # Draw preview background with rounded corners
        pygame.draw.rect(self.screen, self.colors['preview_bg'], 
                        (preview_x, preview_y, preview_width, preview_height), 0, 10)
        pygame.draw.rect(self.screen, self.colors['preview_border'], 
                        (preview_x, preview_y, preview_width, preview_height), 2, 10)

        # Draw level title
        title_text = f"Niveau: {level_info.title}"
        title_surface = self.text_font.render(title_text, True, self.colors['text'])
        title_rect = title_surface.get_rect(center=(preview_x + preview_width // 2, preview_y + 15))
        self.screen.blit(title_surface, title_rect)

        # Calculate cell size to fit the level in the preview area
        level = self.hover_preview_level
        max_cell_width = (preview_width - 20) // max(1, level.width)
        max_cell_height = (preview_height - 40) // max(1, level.height)
        cell_size = min(max_cell_width, max_cell_height, 20)  # Max 20px per cell

        # Calculate actual preview dimensions
        actual_width = level.width * cell_size
        actual_height = level.height * cell_size

        # Center the preview
        level_preview_x = preview_x + (preview_width - actual_width) // 2
        level_preview_y = preview_y + 30 + (preview_height - 40 - actual_height) // 2

        # Draw level cells
        for y in range(level.height):
            for x in range(level.width):
                cell_x = level_preview_x + x * cell_size
                cell_y = level_preview_y + y * cell_size

                # Get the display character for this position
                display_char = level.get_display_char(x, y)

                # Get the skin from the skin manager
                skin = self.skin_manager.get_skin()

                # Draw the cell using the skin
                if display_char in skin:
                    # Scale the sprite to the cell size
                    scaled_sprite = pygame.transform.scale(skin[display_char], (cell_size, cell_size))
                    self.screen.blit(scaled_sprite, (cell_x, cell_y))
                else:
                    # Fallback to a colored rectangle if sprite not found
                    pygame.draw.rect(self.screen, (220, 220, 220), (cell_x, cell_y, cell_size, cell_size))

                # Draw grid lines for better visibility (only if cells are large enough)
                if cell_size > 4:
                    pygame.draw.rect(self.screen, (180, 180, 180), 
                                   (cell_x, cell_y, cell_size, cell_size), 1)

    def start(self):
        """Start the level selector."""
        self.running = True
        self.selected_level = None
        self.current_view = 'categories'
        self.selected_category = None
        self.level_buttons = []
        self.scroll_offset = 0
        self.category_scroll_offset = 0

        # Recreate buttons to ensure they're up to date
        self._create_buttons()

        clock = pygame.time.Clock()

        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_back()
                    elif event.key == pygame.K_UP:
                        if self.current_view == 'levels':
                            self.scroll_offset = max(0, self.scroll_offset - 1)
                            self._create_level_buttons()
                        elif self.current_view == 'categories':
                            self.category_scroll_offset = max(0, self.category_scroll_offset - 1)
                            self._create_category_buttons()
                    elif event.key == pygame.K_DOWN:
                        if self.current_view == 'levels':
                            self.scroll_offset += 1
                            self._create_level_buttons()
                        elif self.current_view == 'categories':
                            self.category_scroll_offset += 1
                            self._create_category_buttons()
                    elif event.key == pygame.K_PAGEUP:
                        if self.current_view == 'levels':
                            self.scroll_offset = max(0, self.scroll_offset - 3)
                            self._create_level_buttons()
                        elif self.current_view == 'categories':
                            self.category_scroll_offset = max(0, self.category_scroll_offset - 3)
                            self._create_category_buttons()
                    elif event.key == pygame.K_PAGEDOWN:
                        if self.current_view == 'levels':
                            self.scroll_offset += 3
                            self._create_level_buttons()
                        elif self.current_view == 'categories':
                            self.category_scroll_offset += 3
                            self._create_category_buttons()
                elif event.type == pygame.MOUSEWHEEL:
                    if self.current_view == 'levels':
                        if event.y > 0:  # Scroll up
                            self.scroll_offset = max(0, self.scroll_offset - 1)
                        else:  # Scroll down
                            self.scroll_offset += 1
                        self._create_level_buttons()
                    elif self.current_view == 'categories':
                        if event.y > 0:  # Scroll up
                            self.category_scroll_offset = max(0, self.category_scroll_offset - 1)
                        else:  # Scroll down
                            self.category_scroll_offset += 1
                        self._create_category_buttons()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size
                    self._create_buttons()

                # Handle button events only if popup is not open and protection delay has passed
                current_time = pygame.time.get_ticks()
                protection_active = (current_time - self.popup_close_time) < self.click_protection_delay

                if not self.popup_open and not protection_active:
                    # Handle scrollbar interactions first
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # If interaction was with scrollbar, don't process button clicks
                        if self._handle_scrollbar_click(event.pos, pygame.MOUSEBUTTONDOWN):
                            continue
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        # Handle mouse up on scrollbar
                        if self._handle_scrollbar_click(event.pos, pygame.MOUSEBUTTONUP):
                            continue
                    elif event.type == pygame.MOUSEMOTION:
                        # Handle mouse motion for scrollbar dragging
                        if self._handle_scrollbar_click(event.pos, pygame.MOUSEMOTION):
                            continue

                    # Handle button clicks
                    active_buttons = []
                    if self.current_view == 'categories':
                        active_buttons = self.category_buttons
                    elif self.current_view == 'levels':
                        active_buttons = self.level_buttons

                    active_buttons.append(self.back_button)

                    for button in active_buttons:
                        button.handle_event(event)

            # Render the current view
            if self.current_view == 'categories':
                self._render_categories()
            elif self.current_view == 'levels':
                self._render_levels()

            clock.tick(60)

        return self.selected_level

    def _render_categories(self):
        """Render the category selection view."""
        self.screen.fill(self.colors['background'])

        # Draw title
        title_surface = self.title_font.render("SOKOBAN", True, self.colors['title'])
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 80))
        self.screen.blit(title_surface, title_rect)

        # Draw subtitle
        subtitle_surface = self.subtitle_font.render("Sélection de Niveau", True, self.colors['text'])
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width // 2, 130))
        self.screen.blit(subtitle_surface, subtitle_rect)

        # Draw instruction
        instruction_text = "Choisissez une catégorie de niveaux"
        instruction_surface = self.text_font.render(instruction_text, True, self.colors['text'])
        instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, 170))
        self.screen.blit(instruction_surface, instruction_rect)

        # Draw scroll indicators if needed
        if self.categories:
            button_height = 60
            button_spacing = 20
            available_height = self.screen_height - 250
            max_visible_categories = max(1, available_height // (button_height + button_spacing))
            total_categories = len(self.categories)

            if total_categories > max_visible_categories:
                # Show scroll indicators
                scroll_text = f"Page {self.category_scroll_offset + 1} / {total_categories - max_visible_categories + 1}"
                scroll_surface = self.text_font.render(scroll_text, True, self.colors['text'])
                scroll_rect = scroll_surface.get_rect(center=(self.screen_width // 2, 200))
                self.screen.blit(scroll_surface, scroll_rect)

                # Show navigation help
                help_text = "Up/Down keys or mouse wheel to navigate, Page Up/Down for fast navigation"
                help_surface = pygame.font.Font(None, 20).render(help_text, True, self.colors['text'])
                help_rect = help_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
                self.screen.blit(help_surface, help_rect)

                # Draw scrollbar
                button_width = 600  # Using the updated button width
                button_x = (self.screen_width - button_width) // 2
                scrollbar_x = button_x + button_width + 40  # Increased spacing to move scrollbar more to the right
                scrollbar_y = 220  # Same starting y as buttons

                # Calculate the height based on the number of visible buttons
                if self.category_buttons:
                    last_button = self.category_buttons[-1]
                    # Ensure the scrollbar stops at the same level as the last visible button
                    scrollbar_height = (last_button.y + last_button.height) - scrollbar_y
                    # Limit the scrollbar height to prevent it from extending beyond the window
                    max_allowed_height = self.screen_height - scrollbar_y - 20  # 20px margin from bottom
                    scrollbar_height = min(scrollbar_height, max_allowed_height)
                else:
                    scrollbar_height = available_height

                scrollbar_width = 20  # Increased width for easier selection

                # Calculate thumb size and position
                thumb_height = max(30, scrollbar_height * max_visible_categories / total_categories)
                max_scroll = total_categories - max_visible_categories
                thumb_pos = scrollbar_y + (scrollbar_height - thumb_height) * (self.category_scroll_offset / max_scroll) if max_scroll > 0 else scrollbar_y

                # Store scrollbar information for event handling
                self.category_scrollbar = {
                    'x': scrollbar_x,
                    'y': scrollbar_y,
                    'width': scrollbar_width,
                    'height': scrollbar_height,
                    'thumb_y': thumb_pos,
                    'thumb_height': thumb_height,
                    'max_scroll': max_scroll,
                    'visible_items': max_visible_categories
                }

                # Draw scrollbar track
                pygame.draw.rect(self.screen, (200, 200, 200), 
                                (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height), 0, 5)

                # Draw scrollbar thumb
                pygame.draw.rect(self.screen, (150, 150, 150), 
                                (scrollbar_x, thumb_pos, scrollbar_width, thumb_height), 0, 5)

        # Update and draw category buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.category_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)

        # Draw back button
        self.back_button.update(mouse_pos)
        self.back_button.draw(self.screen)

        pygame.display.flip()

    def _render_levels(self):
        """Render the level selection view."""
        self.screen.fill(self.colors['background'])

        # Draw title
        title_surface = self.title_font.render("SOKOBAN", True, self.colors['title'])
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 80))
        self.screen.blit(title_surface, title_rect)

        # Draw category name
        if self.selected_category:
            category_surface = self.subtitle_font.render(self.selected_category.display_name, True, self.colors['text'])
            category_rect = category_surface.get_rect(center=(self.screen_width // 2, 130))
            self.screen.blit(category_surface, category_rect)

        # Draw instruction
        instruction_text = "Choisissez un niveau"
        instruction_surface = self.text_font.render(instruction_text, True, self.colors['text'])
        instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, 170))
        self.screen.blit(instruction_surface, instruction_rect)

        # Draw scroll indicators if needed
        if self.selected_category and len(self.selected_category.levels) > 0:
            button_width = 600  # Using the updated button width
            button_height = 60  # Using the updated button height
            button_spacing = 15
            buttons_per_row = max(1, (self.screen_width - 100) // (button_width + 20))
            available_height = self.screen_height - 250
            max_visible_rows = max(1, available_height // (button_height + button_spacing))
            total_rows = (len(self.selected_category.levels) + buttons_per_row - 1) // buttons_per_row

            if total_rows > max_visible_rows:
                # Show scroll indicators
                scroll_text = f"Page {self.scroll_offset + 1} / {total_rows - max_visible_rows + 1}"
                scroll_surface = self.text_font.render(scroll_text, True, self.colors['text'])
                scroll_rect = scroll_surface.get_rect(center=(self.screen_width // 2, 200))
                self.screen.blit(scroll_surface, scroll_rect)

                # Show navigation help
                help_text = "Up/Down keys or mouse wheel to navigate, Page Up/Down for fast navigation"
                help_surface = pygame.font.Font(None, 20).render(help_text, True, self.colors['text'])
                help_rect = help_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
                self.screen.blit(help_surface, help_rect)

                # Draw scrollbar
                # Calculate the rightmost edge of the buttons
                start_x = (self.screen_width - (buttons_per_row * button_width + (buttons_per_row - 1) * 20)) // 2
                rightmost_button_edge = start_x + (buttons_per_row * button_width) + ((buttons_per_row - 1) * 20)

                scrollbar_x = rightmost_button_edge + 40  # Increased spacing to move scrollbar more to the right
                scrollbar_y = 220  # Same starting y as buttons

                # Calculate the height based on the number of visible buttons
                if self.level_buttons:
                    last_button = self.level_buttons[-1]
                    # Ensure the scrollbar stops at the same level as the last visible button
                    scrollbar_height = (last_button.y + last_button.height) - scrollbar_y
                    # Limit the scrollbar height to prevent it from extending beyond the window
                    max_allowed_height = self.screen_height - scrollbar_y - 20  # 20px margin from bottom
                    scrollbar_height = min(scrollbar_height, max_allowed_height)
                else:
                    scrollbar_height = available_height

                scrollbar_width = 20  # Increased width for easier selection

                # Calculate thumb size and position
                thumb_height = max(30, scrollbar_height * max_visible_rows / total_rows)
                max_scroll = total_rows - max_visible_rows
                thumb_pos = scrollbar_y + (scrollbar_height - thumb_height) * (self.scroll_offset / max_scroll) if max_scroll > 0 else scrollbar_y

                # Store scrollbar information for event handling
                self.level_scrollbar = {
                    'x': scrollbar_x,
                    'y': scrollbar_y,
                    'width': scrollbar_width,
                    'height': scrollbar_height,
                    'thumb_y': thumb_pos,
                    'thumb_height': thumb_height,
                    'max_scroll': max_scroll,
                    'visible_items': max_visible_rows
                }

                # Draw scrollbar track
                pygame.draw.rect(self.screen, (200, 200, 200), 
                                (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height), 0, 5)

                # Draw scrollbar thumb
                pygame.draw.rect(self.screen, (150, 150, 150), 
                                (scrollbar_x, thumb_pos, scrollbar_width, thumb_height), 0, 5)

        # Reset hover state
        self.hovered_level_info = None

        # Update and draw level buttons
        mouse_pos = pygame.mouse.get_pos()
        for i, button in enumerate(self.level_buttons):
            button.update(mouse_pos)
            button.draw(self.screen)

            # Check if this button is being hovered
            if button.is_hovered(mouse_pos):
                # Get the level info for this button
                start_level = self.scroll_offset * max(1, (self.screen_width - 100) // (button_width + 20))
                level_index = start_level + i
                if level_index < len(self.selected_category.levels):
                    self.hovered_level_info = self.selected_category.levels[level_index]

        # Draw back button
        self.back_button.update(mouse_pos)
        self.back_button.draw(self.screen)

        # If a level is being hovered, show its preview
        if self.hovered_level_info:
            self._render_hover_preview(self.hovered_level_info)

        pygame.display.flip()
