"""
Level Selector module for the Sokoban game.

This module provides a level selection interface organized by categories/folders.
"""

import os
import pygame
from constants import TITLE, CELL_SIZE
from level_collection_parser import LevelCollection, is_level_collection_file

class LevelItem:
    """Represents a single level, either a file or part of a collection."""

    def __init__(self, path, display_name, collection_index=None, collection=None):
        """
        Initialize a level item.

        Args:
            path (str): Path to the level file or collection file
            display_name (str): Display name for the level
            collection_index (int, optional): Index in the collection if this is a collection level
            collection (LevelCollection, optional): Reference to the collection if this is a collection level
        """
        self.path = path
        self.display_name = display_name
        self.collection_index = collection_index
        self.collection = collection

    def is_collection_level(self):
        """Check if this level is part of a collection."""
        return self.collection_index is not None and self.collection is not None

    def get_level_data(self):
        """Get the level data as a string."""
        if self.is_collection_level():
            return self.collection.get_level(self.collection_index)
        return None  # For file-based levels, the path is used directly


class LevelCategory:
    """Represents a category of levels."""

    def __init__(self, name, display_name, levels):
        """
        Initialize a level category.

        Args:
            name (str): Internal name of the category
            display_name (str): Display name for the category
            levels (list): List of level items in this category
        """
        self.name = name
        self.display_name = display_name
        self.levels = levels

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
                if self.action:
                    self.action()
                return True
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
            'level_button_hover': (180, 130, 100)
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

        # Load level categories
        self.categories = self._load_level_categories()

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
                level_files = [
                    os.path.join(subdir_path, f) for f in os.listdir(subdir_path)
                    if f.endswith('.txt') and os.path.isfile(os.path.join(subdir_path, f))
                ]

                if level_files:
                    # Create display name based on folder name
                    display_name = subdir.replace('_', ' ').replace('-', ' ').title()
                    if subdir.lower() == 'classic':
                        display_name = 'Niveaux Classiques'
                    elif subdir.lower() == 'generated':
                        display_name = 'Niveaux Générés'
                    elif subdir.lower() == 'advanced generated':
                        display_name = 'Niveaux IA Avancés'
                    elif subdir.lower() == 'test':
                        display_name = 'Niveaux de Test'
                    elif subdir.lower() == 'original':
                        display_name = 'Niveaux Originaux'

                    # Process level files
                    level_items = []

                    for file_path in sorted(level_files):
                        # Check if this is a level collection file
                        if is_level_collection_file(file_path):
                            try:
                                # Parse the collection
                                collection = LevelCollection(file_path)

                                # Add each level from the collection as a separate item
                                for i in range(collection.get_level_count()):
                                    level_title = collection.get_level_title(i)
                                    level_display_name = f"{os.path.splitext(os.path.basename(file_path))[0]} - {level_title}"

                                    level_items.append(LevelItem(
                                        file_path,
                                        level_display_name,
                                        collection_index=i,
                                        collection=collection
                                    ))
                            except Exception as e:
                                print(f"Error parsing level collection {file_path}: {e}")
                                # Add the file as a regular level if parsing fails
                                filename = os.path.splitext(os.path.basename(file_path))[0]
                                display_name = filename.replace('_', ' ').title()
                                level_items.append(LevelItem(file_path, display_name))
                        else:
                            # Regular level file
                            filename = os.path.splitext(os.path.basename(file_path))[0]
                            display_name = filename.replace('_', ' ').title()
                            level_items.append(LevelItem(file_path, display_name))

                    if level_items:
                        categories.append(LevelCategory(
                            subdir.lower().replace(' ', '_'),
                            display_name,
                            level_items
                        ))
        else:
            # Fallback to old method if no subdirectories
            all_level_files = [
                os.path.join(self.levels_dir, f) for f in os.listdir(self.levels_dir)
                if f.endswith('.txt') and os.path.isfile(os.path.join(self.levels_dir, f))
            ]

            # Categorize levels based on filename patterns
            classic_levels = []
            generated_levels = []
            advanced_generated_levels = []

            for file_path in all_level_files:
                filename = os.path.basename(file_path)
                level_item = None

                # Check if this is a level collection file
                if is_level_collection_file(file_path):
                    try:
                        # Parse the collection
                        collection = LevelCollection(file_path)

                        # Add each level from the collection as a separate item
                        for i in range(collection.get_level_count()):
                            level_title = collection.get_level_title(i)
                            level_display_name = f"{os.path.splitext(filename)[0]} - {level_title}"

                            level_item = LevelItem(
                                file_path,
                                level_display_name,
                                collection_index=i,
                                collection=collection
                            )

                            # Categorize based on filename
                            if filename.startswith('advanced_generated'):
                                advanced_generated_levels.append(level_item)
                            elif filename.startswith('generated'):
                                generated_levels.append(level_item)
                            else:
                                classic_levels.append(level_item)
                    except Exception as e:
                        print(f"Error parsing level collection {file_path}: {e}")
                        # Add the file as a regular level if parsing fails
                        level_item = LevelItem(file_path, os.path.splitext(filename)[0].replace('_', ' ').title())

                        # Categorize based on filename
                        if filename.startswith('advanced_generated'):
                            advanced_generated_levels.append(level_item)
                        elif filename.startswith('generated'):
                            generated_levels.append(level_item)
                        else:
                            classic_levels.append(level_item)
                else:
                    # Regular level file
                    level_item = LevelItem(file_path, os.path.splitext(filename)[0].replace('_', ' ').title())

                    # Categorize based on filename
                    if filename.startswith('advanced_generated'):
                        advanced_generated_levels.append(level_item)
                    elif filename.startswith('generated'):
                        generated_levels.append(level_item)
                    else:
                        classic_levels.append(level_item)

            # Create categories
            if classic_levels:
                categories.append(LevelCategory('classic', 'Niveaux Classiques', classic_levels))
            if generated_levels:
                categories.append(LevelCategory('generated', 'Niveaux Générés', generated_levels))
            if advanced_generated_levels:
                categories.append(LevelCategory('advanced', 'Niveaux IA Avancés', advanced_generated_levels))

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

        button_width = 300
        button_height = 60
        button_spacing = 20

        total_height = len(self.categories) * button_height + (len(self.categories) - 1) * button_spacing
        start_y = (self.screen_height - total_height) // 2
        if start_y < 200:
            start_y = 200

        button_x = (self.screen_width - button_width) // 2

        for i, category in enumerate(self.categories):
            y = start_y + i * (button_height + button_spacing)
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

        button_width = 400
        button_height = 50
        button_spacing = 15

        # Calculate grid layout
        buttons_per_row = max(1, (self.screen_width - 100) // (button_width + 20))
        rows_needed = (len(self.selected_category.levels) + buttons_per_row - 1) // buttons_per_row

        total_height = rows_needed * button_height + (rows_needed - 1) * button_spacing
        start_y = (self.screen_height - total_height) // 2
        if start_y < 200:
            start_y = 200

        start_x = (self.screen_width - (buttons_per_row * button_width + (buttons_per_row - 1) * 20)) // 2

        for i, level_item in enumerate(self.selected_category.levels):
            row = i // buttons_per_row
            col = i % buttons_per_row

            x = start_x + col * (button_width + 20)
            y = start_y + row * (button_height + button_spacing)

            button = Button(
                level_item.display_name,
                x, y, button_width, button_height,
                action=lambda item=level_item: self._select_level(item),
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
        self._create_level_buttons()

    def _select_level(self, level_item):
        """
        Select a level and exit the selector.

        Args:
            level_item (LevelItem): The level item to select.
        """
        # For collection levels, we need to create a temporary file with the level data
        if level_item.is_collection_level():
            # Get the level data from the collection
            level_data = level_item.get_level_data()

            # Create a directory for temporary levels if it doesn't exist
            temp_dir = os.path.join(self.levels_dir, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Create a temporary file with the level data
            # Use the collection name and level title to create a unique filename
            collection_name = os.path.splitext(os.path.basename(level_item.path))[0]
            level_title = level_item.collection.get_level_title(level_item.collection_index)
            temp_filename = f"{collection_name}_{level_title}.txt"
            temp_path = os.path.join(temp_dir, temp_filename)

            # Write the level data to the temporary file
            with open(temp_path, 'w') as f:
                f.write(level_data)

            # Set the selected level to the temporary file path
            self.selected_level = temp_path
        else:
            # For regular level files, just use the path
            self.selected_level = level_item.path

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

    def start(self):
        """Start the level selector."""
        self.running = True
        self.selected_level = None
        self.current_view = 'categories'
        self.selected_category = None
        self.level_buttons = []

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
                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size
                    self._create_buttons()

                # Handle button events
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

        # Update and draw level buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.level_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)

        # Draw back button
        self.back_button.update(mouse_pos)
        self.back_button.draw(self.screen)

        pygame.display.flip()
