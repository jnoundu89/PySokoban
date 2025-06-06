"""
Skins Menu for the Sokoban game.

This module provides an interactive menu for managing skins and sprite settings:
- Skin selection
- Tile size selection
- Preview of skins
- Background selection
"""

import os
import pygame
from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
from src.ui.skins.custom_skin_importer import CustomSkinImporter
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, TITLE

class SkinsMenu:
    """
    Interactive menu for managing skins and sprite settings.
    """
    
    def __init__(self, screen, screen_width, screen_height, skin_manager=None):
        """
        Initialize the skins menu.
        
        Args:
            screen: Pygame surface to draw on.
            screen_width (int): Width of the screen.
            screen_height (int): Height of the screen.
            skin_manager: Optional existing skin manager.
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Initialize skin manager
        if skin_manager:
            self.skin_manager = skin_manager
        else:
            self.skin_manager = EnhancedSkinManager()
            
        # Initialize custom skin importer
        self.skin_importer = CustomSkinImporter(skins_directory=self.skin_manager.skins_dir, screen=screen)
            
        # Menu state
        self.running = False
        self.selected_skin_index = 0
        self.selected_tile_size_index = 0
        
        # Message display
        self.show_applied_message = False
        self.applied_message_time = 0
        self.message_duration = 2000  # 2 seconds
        
        # Get available options
        self.available_skins = self.skin_manager.get_available_skins()
        self.available_tile_sizes = self.skin_manager.get_available_tile_sizes()
        
        # Find current selections
        current_skin = self.skin_manager.get_current_skin_name()
        current_tile_size = self.skin_manager.get_current_tile_size()
        
        if current_skin in self.available_skins:
            self.selected_skin_index = self.available_skins.index(current_skin)
        if current_tile_size in self.available_tile_sizes:
            self.selected_tile_size_index = self.available_tile_sizes.index(current_tile_size)
            
        # UI elements
        self.buttons = []
        self.preview_rect = None
        self._create_ui_elements()
        
        # Colors
        self.colors = {
            'background': (240, 240, 240),
            'panel': (220, 220, 220),
            'text': (50, 50, 50),
            'button': (100, 100, 200),
            'button_hover': (130, 130, 255),
            'button_selected': (80, 80, 180),
            'button_text': (255, 255, 255),
            'border': (100, 100, 100),
            'preview_bg': (255, 255, 255)
        }
        
        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
    def _create_ui_elements(self):
        """Create UI elements."""
        self.buttons = []
        
        # Back button
        self.buttons.append({
            'rect': pygame.Rect(20, self.screen_height - 60, 100, 40),
            'text': 'Back',
            'action': self._go_back,
            'type': 'navigation'
        })
        
        # Import Skin button
        self.buttons.append({
            'rect': pygame.Rect(self.screen_width - 350, self.screen_height - 60, 120, 40),
            'text': 'Import Skin',
            'action': self._import_custom_skin,
            'type': 'navigation'
        })
        
        # Refresh button
        self.buttons.append({
            'rect': pygame.Rect(self.screen_width - 220, self.screen_height - 60, 80, 40),
            'text': 'Refresh',
            'action': self._refresh_skins,
            'type': 'navigation'
        })
        
        # Apply button
        self.buttons.append({
            'rect': pygame.Rect(self.screen_width - 120, self.screen_height - 60, 100, 40),
            'text': 'Apply',
            'action': self._apply_changes,
            'type': 'navigation'
        })
        
        # Skin selection buttons
        skin_panel_x = 50
        skin_panel_y = 120
        skin_button_width = 200
        skin_button_height = 40
        skin_spacing = 50
        
        for i, skin_name in enumerate(self.available_skins):
            button_y = skin_panel_y + i * skin_spacing
            self.buttons.append({
                'rect': pygame.Rect(skin_panel_x, button_y, skin_button_width, skin_button_height),
                'text': skin_name.title(),
                'action': lambda idx=i: self._select_skin(idx),
                'type': 'skin',
                'index': i
            })
            
        # Tile size selection buttons
        tile_panel_x = 300
        tile_panel_y = 120
        tile_button_width = 80
        tile_button_height = 40
        tile_spacing = 50
        
        for i, tile_size in enumerate(self.available_tile_sizes):
            button_y = tile_panel_y + i * tile_spacing
            self.buttons.append({
                'rect': pygame.Rect(tile_panel_x, button_y, tile_button_width, tile_button_height),
                'text': f'{tile_size}x{tile_size}',
                'action': lambda idx=i: self._select_tile_size(idx),
                'type': 'tile_size',
                'index': i
            })
            
        # Preview area
        preview_x = 450
        preview_y = 120
        preview_width = min(400, self.screen_width - preview_x - 50)
        preview_height = min(300, self.screen_height - preview_y - 100)
        self.preview_rect = pygame.Rect(preview_x, preview_y, preview_width, preview_height)
        
    def _select_skin(self, index):
        """Select a skin."""
        self.selected_skin_index = index
        self._update_preview()
        
    def _select_tile_size(self, index):
        """Select a tile size."""
        self.selected_tile_size_index = index
        self._update_preview()
        
    def _update_preview(self):
        """Update the preview with current selections."""
        # Apply temporary changes for preview
        selected_skin = self.available_skins[self.selected_skin_index]
        selected_tile_size = self.available_tile_sizes[self.selected_tile_size_index]
        
        # Create temporary skin manager for preview
        temp_skin_manager = EnhancedSkinManager()
        temp_skin_manager.set_skin(selected_skin)
        temp_skin_manager.set_tile_size(selected_tile_size)
        
        # Store for preview rendering
        self.preview_skin_manager = temp_skin_manager
        
    def _apply_changes(self):
        """Apply the selected changes."""
        selected_skin = self.available_skins[self.selected_skin_index]
        selected_tile_size = self.available_tile_sizes[self.selected_tile_size_index]
        
        # Apply changes to skin manager (this will save to config automatically)
        self.skin_manager.set_skin(selected_skin)
        self.skin_manager.set_tile_size(selected_tile_size)
        
        # Show confirmation message
        self.show_applied_message = True
        self.applied_message_time = pygame.time.get_ticks()
        
        print(f"✓ Skin appliqué: {selected_skin}, taille des tuiles: {selected_tile_size}x{selected_tile_size}")
        
    def _go_back(self):
        """Go back to the previous menu."""
        self.running = False
        
    def _import_custom_skin(self):
        """Import a custom skin from PNG files."""
        try:
            # Get current tile size
            current_tile_size = self.available_tile_sizes[self.selected_tile_size_index]
            
            # Import skin
            imported_skin_name = self.skin_importer.import_skin(current_tile_size)
            
            if imported_skin_name:
                # Refresh the available skins
                self._refresh_skins()
                
                # Select the newly imported skin
                if imported_skin_name in self.available_skins:
                    self.selected_skin_index = self.available_skins.index(imported_skin_name)
                    self._update_preview()
                    
        except Exception as e:
            print(f"Error importing custom skin: {e}")
            
    def _refresh_skins(self):
        """Refresh the list of available skins."""
        # Rediscover skins
        self.skin_manager._discover_skins()
        self.available_skins = self.skin_manager.get_available_skins()
        
        # Validate current selection
        if self.selected_skin_index >= len(self.available_skins):
            self.selected_skin_index = 0
            
        # Recreate UI elements to reflect new skins
        self._create_ui_elements()
        self._update_preview()
        
    def start(self):
        """Start the skins menu."""
        self.running = True
        self._update_preview()
        
        clock = pygame.time.Clock()
        
        while self.running:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN:
                        self._apply_changes()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_click(pygame.mouse.get_pos())
                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size
                    self._create_ui_elements()
            
            # Check if applied message should be hidden
            if self.show_applied_message and current_time - self.applied_message_time > self.message_duration:
                self.show_applied_message = False
                    
            # Draw the menu
            self._draw_menu()
            
            # Cap the frame rate
            clock.tick(60)
            
    def _handle_mouse_click(self, mouse_pos):
        """Handle mouse clicks."""
        for button in self.buttons:
            if button['rect'].collidepoint(mouse_pos):
                button['action']()
                break
                
    def _draw_menu(self):
        """Draw the skins menu."""
        # Clear screen
        self.screen.fill(self.colors['background'])
        
        # Draw title
        title_surface = self.title_font.render("Skins & Sprites", True, self.colors['text'])
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 50))
        self.screen.blit(title_surface, title_rect)
        
        # Draw sections
        self._draw_skin_selection()
        self._draw_tile_size_selection()
        self._draw_preview()
        self._draw_import_info()
        self._draw_buttons()
        
        # Draw applied message if shown
        if self.show_applied_message:
            self._draw_applied_message()
        
        # Update display
        pygame.display.flip()
        
    def _draw_skin_selection(self):
        """Draw the skin selection section."""
        # Section title
        title_surface = self.subtitle_font.render("Skins", True, self.colors['text'])
        self.screen.blit(title_surface, (50, 90))
        
        # Draw skin buttons
        for button in self.buttons:
            if button['type'] == 'skin':
                self._draw_skin_button(button)
                
    def _draw_tile_size_selection(self):
        """Draw the tile size selection section."""
        # Section title
        title_surface = self.subtitle_font.render("Tile Size", True, self.colors['text'])
        self.screen.blit(title_surface, (300, 90))
        
        # Draw tile size buttons
        for button in self.buttons:
            if button['type'] == 'tile_size':
                self._draw_tile_size_button(button)
                
    def _draw_skin_button(self, button):
        """Draw a skin selection button."""
        is_selected = button['index'] == self.selected_skin_index
        is_hovered = button['rect'].collidepoint(pygame.mouse.get_pos())
        
        # Button color
        if is_selected:
            color = self.colors['button_selected']
        elif is_hovered:
            color = self.colors['button_hover']
        else:
            color = self.colors['button']
            
        # Draw button
        pygame.draw.rect(self.screen, color, button['rect'], 0, 5)
        pygame.draw.rect(self.screen, self.colors['border'], button['rect'], 2, 5)
        
        # Draw text
        text_surface = self.text_font.render(button['text'], True, self.colors['button_text'])
        text_rect = text_surface.get_rect(center=button['rect'].center)
        self.screen.blit(text_surface, text_rect)
        
    def _draw_tile_size_button(self, button):
        """Draw a tile size selection button."""
        is_selected = button['index'] == self.selected_tile_size_index
        is_hovered = button['rect'].collidepoint(pygame.mouse.get_pos())
        
        # Button color
        if is_selected:
            color = self.colors['button_selected']
        elif is_hovered:
            color = self.colors['button_hover']
        else:
            color = self.colors['button']
            
        # Draw button
        pygame.draw.rect(self.screen, color, button['rect'], 0, 5)
        pygame.draw.rect(self.screen, self.colors['border'], button['rect'], 2, 5)
        
        # Draw text
        text_surface = self.text_font.render(button['text'], True, self.colors['button_text'])
        text_rect = text_surface.get_rect(center=button['rect'].center)
        self.screen.blit(text_surface, text_rect)
        
    def _draw_preview(self):
        """Draw the preview section."""
        # Section title
        title_surface = self.subtitle_font.render("Preview", True, self.colors['text'])
        self.screen.blit(title_surface, (self.preview_rect.x, self.preview_rect.y - 30))
        
        # Preview background
        pygame.draw.rect(self.screen, self.colors['preview_bg'], self.preview_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.preview_rect, 2)
        
        # Draw preview sprites
        if hasattr(self, 'preview_skin_manager'):
            self._draw_preview_sprites()
            
    def _draw_preview_sprites(self):
        """Draw preview sprites in the preview area."""
        skin_data = self.preview_skin_manager.get_skin()
        tile_size = self.preview_skin_manager.get_current_tile_size()
        
        # Calculate layout
        sprites_to_show = [WALL, FLOOR, PLAYER, BOX, TARGET]
        sprite_names = ['Wall', 'Floor', 'Player', 'Box', 'Target']
        
        # Calculate grid layout
        cols = 3
        rows = 2
        cell_width = self.preview_rect.width // cols
        cell_height = self.preview_rect.height // rows
        
        for i, (sprite_key, name) in enumerate(zip(sprites_to_show, sprite_names)):
            if sprite_key in skin_data:
                row = i // cols
                col = i % cols
                
                # Calculate position
                x = self.preview_rect.x + col * cell_width + cell_width // 2
                y = self.preview_rect.y + row * cell_height + cell_height // 2
                
                # Draw sprite (scaled to fit)
                sprite = skin_data[sprite_key]
                max_size = min(cell_width - 20, cell_height - 40)
                if tile_size > max_size:
                    scale_factor = max_size / tile_size
                    scaled_size = int(tile_size * scale_factor)
                    sprite = pygame.transform.scale(sprite, (scaled_size, scaled_size))
                
                sprite_rect = sprite.get_rect(center=(x, y - 10))
                self.screen.blit(sprite, sprite_rect)
                
                # Draw label
                label_surface = self.small_font.render(name, True, self.colors['text'])
                label_rect = label_surface.get_rect(center=(x, y + sprite_rect.height // 2 + 15))
                self.screen.blit(label_surface, label_rect)
                
        # Draw current settings info
        info_y = self.preview_rect.bottom + 10
        skin_name = self.available_skins[self.selected_skin_index]
        tile_size = self.available_tile_sizes[self.selected_tile_size_index]
        
        info_text = f"Skin: {skin_name.title()} | Tile Size: {tile_size}x{tile_size}"
        info_surface = self.text_font.render(info_text, True, self.colors['text'])
        info_rect = info_surface.get_rect(center=(self.preview_rect.centerx, info_y))
        self.screen.blit(info_surface, info_rect)
        
    def _draw_import_info(self):
        """Draw import information and instructions."""
        # Draw import instructions panel
        info_y = 450
        info_width = min(600, self.screen_width - 100)
        info_height = 120
        info_x = (self.screen_width - info_width) // 2
        
        # Panel background
        info_rect = pygame.Rect(info_x, info_y, info_width, info_height)
        pygame.draw.rect(self.screen, self.colors['panel'], info_rect, 0, 10)
        pygame.draw.rect(self.screen, self.colors['border'], info_rect, 2, 10)
        
        # Title
        title_surface = self.subtitle_font.render("Custom Skin Import", True, self.colors['text'])
        title_rect = title_surface.get_rect(center=(info_rect.centerx, info_y + 20))
        self.screen.blit(title_surface, title_rect)
        
        # Instructions
        instructions = [
            f"• Click 'Import Skin' to add custom sprites",
            f"• PNG files should be {self.available_tile_sizes[self.selected_tile_size_index]}x{self.available_tile_sizes[self.selected_tile_size_index]} pixels for current tile size",
            f"• Required: wall, floor, player, box, target sprites",
            f"• Optional: directional player sprites, background image"
        ]
        
        for i, instruction in enumerate(instructions):
            text_surface = self.small_font.render(instruction, True, self.colors['text'])
            text_y = info_y + 45 + i * 18
            self.screen.blit(text_surface, (info_x + 20, text_y))
        
    def _draw_buttons(self):
        """Draw navigation buttons."""
        for button in self.buttons:
            if button['type'] == 'navigation':
                is_hovered = button['rect'].collidepoint(pygame.mouse.get_pos())
                
                # Button color
                color = self.colors['button_hover'] if is_hovered else self.colors['button']
                
                # Draw button
                pygame.draw.rect(self.screen, color, button['rect'], 0, 5)
                pygame.draw.rect(self.screen, self.colors['border'], button['rect'], 2, 5)
                
                # Draw text
                text_surface = self.text_font.render(button['text'], True, self.colors['button_text'])
                text_rect = text_surface.get_rect(center=button['rect'].center)
                self.screen.blit(text_surface, text_rect)
    
    def _draw_applied_message(self):
        """Draw the applied settings confirmation message."""
        # Create message surface
        message_text = "✓ Paramètres appliqués et sauvegardés!"
        message_surface = self.subtitle_font.render(message_text, True, (0, 150, 0))
        
        # Create background for message
        message_width = message_surface.get_width() + 40
        message_height = message_surface.get_height() + 20
        message_x = (self.screen_width - message_width) // 2
        message_y = 20
        
        # Draw message background
        message_rect = pygame.Rect(message_x, message_y, message_width, message_height)
        pygame.draw.rect(self.screen, (240, 255, 240), message_rect, 0, 10)
        pygame.draw.rect(self.screen, (0, 150, 0), message_rect, 2, 10)
        
        # Draw message text
        text_rect = message_surface.get_rect(center=message_rect.center)
        self.screen.blit(message_surface, text_rect)


# Main function to run the skins menu standalone
def main():
    """Main function to run the skins menu."""
    pygame.init()
    screen = pygame.display.set_mode((900, 700), pygame.RESIZABLE)
    pygame.display.set_caption(f"{TITLE} - Skins Menu")
    
    menu = SkinsMenu(screen, 900, 700)
    menu.start()
    
    pygame.quit()


if __name__ == "__main__":
    main()