"""
Test script for custom skin import functionality.

This script demonstrates and tests the custom skin import system.
"""

import pygame
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.skins_menu import SkinsMenu
from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
from src.core.constants import TITLE

def test_skins_menu():
    """Test the enhanced skins menu with import functionality."""
    pygame.init()
    
    # Create screen
    screen_width, screen_height = 1000, 800
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption(f"{TITLE} - Enhanced Skins Menu Test")
    
    # Create enhanced skin manager
    skin_manager = EnhancedSkinManager()
    
    # Create skins menu with import functionality
    skins_menu = SkinsMenu(screen, screen_width, screen_height, skin_manager)
    
    print("Enhanced Skins Menu Test")
    print("=======================")
    print("Features available:")
    print("• Skin selection from available skins")
    print("• Tile size selection (8x8, 16x16, 32x32, 64x64, 128x128)")
    print("• Live preview of selected skin and tile size")
    print("• Import custom skins from PNG files")
    print("• Refresh skins list after import")
    print("• Background image support")
    print("• Directional player sprites support")
    print()
    print("Instructions:")
    print("1. Select a skin from the left panel")
    print("2. Select a tile size from the middle panel") 
    print("3. View the preview in the right panel")
    print("4. Click 'Import Skin' to add custom PNG sprites")
    print("5. Click 'Refresh' to update the skins list")
    print("6. Click 'Apply' to save changes")
    print("7. Press ESC or click 'Back' to exit")
    print()
    print(f"Available skins: {skin_manager.get_available_skins()}")
    print(f"Available tile sizes: {skin_manager.get_available_tile_sizes()}")
    print(f"Current skin: {skin_manager.get_current_skin_name()}")
    print(f"Current tile size: {skin_manager.get_current_tile_size()}")
    print(f"Skins directory: {skin_manager.skins_dir}")
    
    # Start the menu
    skins_menu.start()
    
    pygame.quit()

def create_sample_sprites():
    """Create sample sprites for testing import functionality."""
    import pygame
    from PIL import Image
    
    # Create sample directory
    sample_dir = "sample_sprites"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Sample sprite size
    sprite_size = 64
    
    # Colors for sample sprites
    colors = {
        'wall': (80, 80, 80),
        'floor': (200, 200, 200),
        'player': (0, 150, 255),
        'box': (150, 75, 0),
        'target': (255, 100, 100),
        'player_on_target': (100, 255, 100),
        'box_on_target': (0, 200, 0)
    }
    
    # Create sample sprites
    sprites_created = []
    
    for sprite_name, color in colors.items():
        # Create a simple colored square
        img = Image.new('RGBA', (sprite_size, sprite_size), color + (255,))
        
        # Add some simple decoration
        if sprite_name == 'player':
            # Add eyes
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            eye_size = sprite_size // 8
            eye_y = sprite_size // 3
            draw.ellipse([sprite_size//3 - eye_size, eye_y, sprite_size//3 + eye_size, eye_y + eye_size*2], fill=(255, 255, 255, 255))
            draw.ellipse([2*sprite_size//3 - eye_size, eye_y, 2*sprite_size//3 + eye_size, eye_y + eye_size*2], fill=(255, 255, 255, 255))
        elif sprite_name == 'target':
            # Add concentric circles
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            center = sprite_size // 2
            draw.ellipse([center - sprite_size//4, center - sprite_size//4, center + sprite_size//4, center + sprite_size//4], outline=(255, 255, 255, 255), width=3)
        
        # Save sprite
        sprite_path = os.path.join(sample_dir, f"{sprite_name}.png")
        img.save(sprite_path)
        sprites_created.append(sprite_path)
    
    print(f"\nSample sprites created in '{sample_dir}' directory:")
    for sprite_path in sprites_created:
        print(f"  • {sprite_path}")
    print("\nYou can use these sprites to test the import functionality!")
    
    return sample_dir

if __name__ == "__main__":
    print("Sokoban Enhanced Skins System Test")
    print("==================================")
    
    choice = input("\nWhat would you like to do?\n1. Test skins menu\n2. Create sample sprites\n3. Both\nChoice (1-3): ").strip()
    
    if choice in ['2', '3']:
        print("\nCreating sample sprites...")
        create_sample_sprites()
    
    if choice in ['1', '3']:
        print("\nStarting skins menu test...")
        test_skins_menu()
    
    print("\nTest completed!")