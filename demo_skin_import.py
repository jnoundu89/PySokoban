"""
Demonstration script for custom skin import functionality.

This script creates sample sprites and demonstrates the import process.
"""

import os
import sys
import pygame
from PIL import Image, ImageDraw

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
from src.ui.skins.custom_skin_importer import CustomSkinImporter

def create_demo_skin(name="demo_skin", tile_size=64):
    """
    Create a complete demo skin with all required and optional sprites.
    
    Args:
        name (str): Name of the demo skin
        tile_size (int): Size of the sprites
    """
    print(f"Creating demo skin '{name}' with {tile_size}x{tile_size} sprites...")
    
    # Create demo directory
    demo_dir = f"demo_{name}"
    os.makedirs(demo_dir, exist_ok=True)
    
    # Color palette for the demo skin
    colors = {
        'wall': (60, 60, 60),
        'floor': (240, 230, 200),
        'player': (50, 150, 255),
        'box': (180, 120, 60),
        'target': (255, 80, 80),
        'player_on_target': (100, 255, 100),
        'box_on_target': (100, 200, 100)
    }
    
    # Required sprites
    required_sprites = {
        'wall': 'wall.png',
        'floor': 'floor.png', 
        'player': 'player.png',
        'box': 'box.png',
        'target': 'target.png',
        'player_on_target': 'player_on_target.png',
        'box_on_target': 'box_on_target.png'
    }
    
    # Optional directional sprites
    directional_sprites = {
        'player_up': 'player_up.png',
        'player_down': 'player_down.png',
        'player_left': 'player_left.png',
        'player_right': 'player_right.png',
        'player_push_up': 'player_push_up.png',
        'player_push_down': 'player_push_down.png',
        'player_push_left': 'player_push_left.png',
        'player_push_right': 'player_push_right.png',
        'player_blocked': 'player_blocked.png'
    }
    
    created_files = []
    
    # Create required sprites
    for sprite_name, filename in required_sprites.items():
        img = create_sprite_image(sprite_name, colors, tile_size)
        filepath = os.path.join(demo_dir, filename)
        img.save(filepath)
        created_files.append(filepath)
        print(f"  ✓ Created {filename}")
    
    # Create directional sprites
    for sprite_name, filename in directional_sprites.items():
        img = create_directional_sprite_image(sprite_name, colors, tile_size)
        filepath = os.path.join(demo_dir, filename)
        img.save(filepath)
        created_files.append(filepath)
        print(f"  ✓ Created {filename}")
    
    # Create background
    bg_img = create_background_image(tile_size * 8)
    bg_filepath = os.path.join(demo_dir, 'background.png')
    bg_img.save(bg_filepath)
    created_files.append(bg_filepath)
    print(f"  ✓ Created background.png")
    
    print(f"\nDemo skin created in '{demo_dir}' directory with {len(created_files)} files!")
    return demo_dir, created_files

def create_sprite_image(sprite_name, colors, size):
    """Create a sprite image for the given sprite type."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    margin = max(1, size // 16)
    center = size // 2
    
    if sprite_name == 'wall':
        # Draw brick pattern
        draw.rectangle([0, 0, size-1, size-1], fill=colors['wall'])
        # Add brick lines
        line_width = max(1, size // 32)
        for i in range(0, size, size // 4):
            draw.line([0, i, size, i], fill=(40, 40, 40), width=line_width)
        for i in range(0, size, size // 2):
            draw.line([i, 0, i, size], fill=(40, 40, 40), width=line_width)
    
    elif sprite_name == 'floor':
        # Simple floor
        draw.rectangle([0, 0, size-1, size-1], fill=colors['floor'])
        # Add subtle texture
        for i in range(0, size, size // 8):
            for j in range(0, size, size // 8):
                if (i + j) % (size // 4) == 0:
                    draw.point([i, j], fill=(220, 210, 180))
    
    elif sprite_name == 'player':
        # Floor background first
        draw.rectangle([0, 0, size-1, size-1], fill=colors['floor'])
        # Player circle
        radius = size // 3
        draw.ellipse([center-radius, center-radius, center+radius, center+radius], 
                    fill=colors['player'])
        # Eyes
        eye_size = max(1, size // 16)
        eye_offset = radius // 3
        draw.ellipse([center-eye_offset-eye_size, center-eye_offset-eye_size,
                     center-eye_offset+eye_size, center-eye_offset+eye_size], 
                    fill=(255, 255, 255))
        draw.ellipse([center+eye_offset-eye_size, center-eye_offset-eye_size,
                     center+eye_offset+eye_size, center-eye_offset+eye_size], 
                    fill=(255, 255, 255))
    
    elif sprite_name == 'box':
        # Floor background
        draw.rectangle([0, 0, size-1, size-1], fill=colors['floor'])
        # Box
        box_margin = size // 6
        draw.rectangle([box_margin, box_margin, size-box_margin-1, size-box_margin-1], 
                      fill=colors['box'], outline=(120, 80, 40), width=max(1, size//32))
        # Box highlight
        highlight_margin = box_margin + size // 16
        draw.line([highlight_margin, highlight_margin, size-highlight_margin, highlight_margin], 
                 fill=(220, 180, 120), width=max(1, size//64))
        draw.line([highlight_margin, highlight_margin, highlight_margin, size-highlight_margin], 
                 fill=(220, 180, 120), width=max(1, size//64))
    
    elif sprite_name == 'target':
        # Floor background
        draw.rectangle([0, 0, size-1, size-1], fill=colors['floor'])
        # Target circles
        outer_radius = size // 4
        inner_radius = size // 8
        draw.ellipse([center-outer_radius, center-outer_radius, center+outer_radius, center+outer_radius], 
                    fill=colors['target'])
        draw.ellipse([center-inner_radius, center-inner_radius, center+inner_radius, center+inner_radius], 
                    fill=colors['floor'])
    
    elif sprite_name == 'player_on_target':
        # Floor background
        draw.rectangle([0, 0, size-1, size-1], fill=colors['floor'])
        # Target first
        outer_radius = size // 4
        draw.ellipse([center-outer_radius, center-outer_radius, center+outer_radius, center+outer_radius], 
                    fill=colors['target'])
        # Player on top
        player_radius = size // 3
        draw.ellipse([center-player_radius, center-player_radius, center+player_radius, center+player_radius], 
                    fill=colors['player_on_target'])
    
    elif sprite_name == 'box_on_target':
        # Floor background
        draw.rectangle([0, 0, size-1, size-1], fill=colors['floor'])
        # Target first
        outer_radius = size // 4
        draw.ellipse([center-outer_radius, center-outer_radius, center+outer_radius, center+outer_radius], 
                    fill=colors['target'])
        # Box on top (green when on target)
        box_margin = size // 6
        draw.rectangle([box_margin, box_margin, size-box_margin-1, size-box_margin-1], 
                      fill=colors['box_on_target'], outline=(80, 160, 80), width=max(1, size//32))
    
    return img

def create_directional_sprite_image(sprite_name, colors, size):
    """Create a directional sprite image."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    
    # Floor background
    draw.rectangle([0, 0, size-1, size-1], fill=colors['floor'])
    
    # Base player color
    if 'push' in sprite_name:
        player_color = (colors['player'][0], colors['player'][1], min(255, colors['player'][2] + 50))
    elif 'blocked' in sprite_name:
        player_color = (min(255, colors['player'][0] + 50), colors['player'][1], colors['player'][2])
    else:
        player_color = colors['player']
    
    # Player circle
    radius = size // 3
    draw.ellipse([center-radius, center-radius, center+radius, center+radius], fill=player_color)
    
    # Direction indicator
    indicator_size = max(2, size // 8)
    
    if 'up' in sprite_name:
        # Arrow pointing up
        draw.polygon([
            (center, center - radius // 2),
            (center - indicator_size, center + indicator_size // 2),
            (center + indicator_size, center + indicator_size // 2)
        ], fill=(255, 255, 255))
    elif 'down' in sprite_name:
        # Arrow pointing down
        draw.polygon([
            (center, center + radius // 2),
            (center - indicator_size, center - indicator_size // 2),
            (center + indicator_size, center - indicator_size // 2)
        ], fill=(255, 255, 255))
    elif 'left' in sprite_name:
        # Arrow pointing left
        draw.polygon([
            (center - radius // 2, center),
            (center + indicator_size // 2, center - indicator_size),
            (center + indicator_size // 2, center + indicator_size)
        ], fill=(255, 255, 255))
    elif 'right' in sprite_name:
        # Arrow pointing right
        draw.polygon([
            (center + radius // 2, center),
            (center - indicator_size // 2, center - indicator_size),
            (center - indicator_size // 2, center + indicator_size)
        ], fill=(255, 255, 255))
    elif 'blocked' in sprite_name:
        # X mark
        line_width = max(2, size // 32)
        draw.line([center-indicator_size, center-indicator_size, center+indicator_size, center+indicator_size], 
                 fill=(255, 0, 0), width=line_width)
        draw.line([center-indicator_size, center+indicator_size, center+indicator_size, center-indicator_size], 
                 fill=(255, 0, 0), width=line_width)
    
    return img

def create_background_image(size):
    """Create a background image."""
    img = Image.new('RGBA', (size, size), (135, 206, 235, 255))  # Sky blue
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for y in range(size):
        alpha = int(255 * (1 - y / size))
        color = (255, 255, 255, alpha)
        draw.line([0, y, size, y], fill=color)
    
    return img

def test_programmatic_import():
    """Test programmatic skin import without GUI."""
    print("\nTesting Programmatic Skin Import")
    print("=================================")
    
    # Create demo skin files
    demo_dir, files = create_demo_skin("programmatic", 64)
    
    # Create skin manager and importer
    skin_manager = EnhancedSkinManager()
    importer = CustomSkinImporter(skin_manager.skins_dir)
    
    print(f"\nBefore import - Available skins: {skin_manager.get_available_skins()}")
    
    # Manually copy files to create a new skin (simulating import)
    new_skin_name = "demo_programmatic"
    new_skin_path = os.path.join(skin_manager.skins_dir, new_skin_name)
    
    print(f"Creating skin directory: {new_skin_path}")
    os.makedirs(new_skin_path, exist_ok=True)
    
    # Copy required files
    import shutil
    required_files = ['wall.png', 'floor.png', 'player.png', 'box.png', 'target.png', 
                     'player_on_target.png', 'box_on_target.png']
    
    for filename in required_files:
        src = os.path.join(demo_dir, filename)
        dst = os.path.join(new_skin_path, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  ✓ Copied {filename}")
    
    # Refresh skin manager
    skin_manager._discover_skins()
    
    print(f"\nAfter import - Available skins: {skin_manager.get_available_skins()}")
    
    # Test loading the new skin
    if new_skin_name in skin_manager.get_available_skins():
        skin_manager.set_skin(new_skin_name)
        skin_data = skin_manager.get_skin()
        print(f"Successfully loaded new skin with sprites: {list(skin_data.keys())}")
        return True
    else:
        print("Failed to load new skin")
        return False

def main():
    """Main demonstration function."""
    print("Sokoban Custom Skin Import Demonstration")
    print("========================================")
    
    # Test skin manager path
    skin_manager = EnhancedSkinManager()
    print(f"Skins directory: {skin_manager.skins_dir}")
    print(f"Directory exists: {os.path.exists(skin_manager.skins_dir)}")
    
    # Create demo sprites
    print("\n1. Creating Demo Sprites")
    print("------------------------")
    demo_dir, files = create_demo_skin("complete", 64)
    
    print(f"\nCreated {len(files)} sprite files:")
    for file in files:
        print(f"  • {os.path.basename(file)}")
    
    # Test programmatic import
    print("\n2. Testing Programmatic Import")
    print("------------------------------")
    success = test_programmatic_import()
    
    if success:
        print("\n✅ Demo completed successfully!")
        print(f"📁 Demo files created in: {demo_dir}")
        print("🎮 You can now use the GUI to import these sprites!")
        print("\nTo test the GUI import:")
        print("1. Run: python test_skin_import.py")
        print("2. Choose option 1 (Test skins menu)")
        print("3. Click 'Import Skin' in the GUI")
        print(f"4. Use the files from '{demo_dir}' directory")
    else:
        print("\n❌ Demo encountered issues")

if __name__ == "__main__":
    main()