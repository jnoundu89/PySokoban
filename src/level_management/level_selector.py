"""
Level Selector module for the Sokoban game.

This module provides a level selection interface organized by categories/folders.
"""

import os
import pygame
from src.core.constants import TITLE, CELL_SIZE
from src.level_management.level_collection_parser import LevelCollectionParser

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
        
        # Scroll management
        self.scroll_offset = 0
        self.max_visible_buttons = 10  # Maximum buttons visible at once
        
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
        
        button_width = 300
        button_height = 50
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
        self._create_level_buttons()
    
    def _select_level_info(self, level_info):
        """Select a level from level info and exit the selector."""
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
                    elif event.key == pygame.K_UP and self.current_view == 'levels':
                        self.scroll_offset = max(0, self.scroll_offset - 1)
                        self._create_level_buttons()
                    elif event.key == pygame.K_DOWN and self.current_view == 'levels':
                        self.scroll_offset += 1
                        self._create_level_buttons()
                    elif event.key == pygame.K_PAGEUP and self.current_view == 'levels':
                        self.scroll_offset = max(0, self.scroll_offset - 3)
                        self._create_level_buttons()
                    elif event.key == pygame.K_PAGEDOWN and self.current_view == 'levels':
                        self.scroll_offset += 3
                        self._create_level_buttons()
                elif event.type == pygame.MOUSEWHEEL and self.current_view == 'levels':
                    if event.y > 0:  # Scroll up
                        self.scroll_offset = max(0, self.scroll_offset - 1)
                    else:  # Scroll down
                        self.scroll_offset += 1
                    self._create_level_buttons()
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
        
        # Draw scroll indicators if needed
        if self.selected_category and len(self.selected_category.levels) > 0:
            button_width = 300
            button_height = 50
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
                help_text = "↑↓ ou molette pour naviguer, Page↑↓ pour navigation rapide"
                help_surface = pygame.font.Font(None, 20).render(help_text, True, self.colors['text'])
                help_rect = help_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 100))
                self.screen.blit(help_surface, help_rect)
        
        # Update and draw level buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.level_buttons:
            button.update(mouse_pos)
            button.draw(self.screen)
        
        # Draw back button
        self.back_button.update(mouse_pos)
        self.back_button.draw(self.screen)
        
        pygame.display.flip()