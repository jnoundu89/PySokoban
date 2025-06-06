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

        # Menu state
        self.running = False
        self.selected_skin_index = 0
        self.selected_tile_size_index = 0

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

        self.skin_manager.set_skin(selected_skin)
        self.skin_manager.set_tile_size(selected_tile_size)

        # Save settings (in a real implementation, this would save to a config file)
        print(f"Applied skin: {selected_skin}, tile size: {selected_tile_size}")

    def _go_back(self):
        """Go back to the previous menu."""
        self.running = False

    def start(self):
        """Start the skins menu."""
        self.running = True
        self._update_preview()

        clock = pygame.time.Clock()

        while self.running:
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
        self._draw_buttons()

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
