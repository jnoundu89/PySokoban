"""
Simple test to verify skins path is correct.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager

def test_skin_path():
    """Test that skin manager finds the correct path."""
    
    skin_manager = EnhancedSkinManager()
    
    print("Testing Enhanced Skin Manager Paths")
    print("====================================")
    print(f"Skins directory: {skin_manager.skins_dir}")
    print(f"Directory exists: {os.path.exists(skin_manager.skins_dir)}")
    
    if os.path.exists(skin_manager.skins_dir):
        print(f"Contents of skins directory:")
        for item in os.listdir(skin_manager.skins_dir):
            item_path = os.path.join(skin_manager.skins_dir, item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
                # List contents of skin folder
                for sprite in os.listdir(item_path):
                    print(f"      🖼️ {sprite}")
            else:
                print(f"  📄 {item}")
    
    print(f"\nAvailable skins: {skin_manager.get_available_skins()}")
    print(f"Available tile sizes: {skin_manager.get_available_tile_sizes()}")
    print(f"Current skin: {skin_manager.get_current_skin_name()}")
    print(f"Current tile size: {skin_manager.get_current_tile_size()}")
    
    # Test loading skin
    skin_data = skin_manager.get_skin()
    print(f"\nLoaded skin sprites: {list(skin_data.keys()) if skin_data else 'None'}")

if __name__ == "__main__":
    test_skin_path()