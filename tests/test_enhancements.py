"""
Test script for the enhanced Sokoban game features.

This script tests all the new enhancements:
- Responsive menu system
- Enhanced level editor with paint mode
- Grid toggle functionality
- Zoom and scroll capabilities
- Enhanced skin system with directional sprites
- Tile size selection
"""

import pygame
import sys
import os

def test_responsive_menu():
    """Test the responsive menu system."""
    print("Testing responsive menu system...")
    
    try:
        from src.ui.menu_system import MenuSystem
        
        # Test different screen sizes
        test_sizes = [(800, 600), (1200, 800), (1920, 1080)]
        
        for width, height in test_sizes:
            print(f"  Testing menu at {width}x{height}")
            pygame.init()
            screen = pygame.display.set_mode((width, height))
            menu = MenuSystem(screen, width, height)
            
            # Check if buttons are properly sized and positioned
            for button in menu.main_menu_buttons:
                assert button.width > 0 and button.height > 0
                assert 0 <= button.x <= width
                assert 0 <= button.y <= height
                
            pygame.quit()
            
        print("  ✓ Responsive menu system working correctly")
        
    except Exception as e:
        print(f"  ✗ Error testing responsive menu: {e}")
        return False
        
    return True

def test_enhanced_level_editor():
    """Test the enhanced level editor."""
    print("Testing enhanced level editor...")
    
    try:
        from src.editors.enhanced_level_editor import EnhancedLevelEditor
        
        pygame.init()
        screen = pygame.display.set_mode((1200, 800))
        editor = EnhancedLevelEditor(screen=screen)
        
        # Test basic functionality
        assert editor.current_level is not None
        assert editor.zoom_level == 1.0
        assert editor.show_grid == True
        assert len(editor.palette) > 0
        assert len(editor.buttons) > 0
        assert len(editor.sliders) > 0
        
        # Test zoom functionality
        editor._zoom_in()
        assert editor.zoom_level > 1.0
        
        editor._zoom_out()
        editor._zoom_out()
        assert editor.zoom_level >= editor.min_zoom
        
        # Test grid toggle
        original_grid = editor.show_grid
        editor._toggle_grid()
        assert editor.show_grid != original_grid
        
        pygame.quit()
        print("  ✓ Enhanced level editor working correctly")
        
    except Exception as e:
        print(f"  ✗ Error testing enhanced level editor: {e}")
        return False
        
    return True

def test_enhanced_skin_system():
    """Test the enhanced skin system."""
    print("Testing enhanced skin system...")
    
    try:
        from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
        
        skin_manager = EnhancedSkinManager()
        
        # Test basic functionality
        assert skin_manager.get_current_tile_size() in skin_manager.get_available_tile_sizes()
        assert skin_manager.get_current_skin_name() in skin_manager.get_available_skins()
        
        # Test tile size changes
        original_size = skin_manager.get_current_tile_size()
        available_sizes = skin_manager.get_available_tile_sizes()
        
        if len(available_sizes) > 1:
            new_size = available_sizes[1] if available_sizes[0] == original_size else available_sizes[0]
            skin_manager.set_tile_size(new_size)
            assert skin_manager.get_current_tile_size() == new_size
        
        # Test player state updates
        skin_manager.update_player_state('up', False, False)
        assert skin_manager.current_player_state == 'walking_up'
        
        skin_manager.update_player_state('right', True, False)
        assert skin_manager.current_player_state == 'pushing_right'
        
        skin_manager.update_player_state('left', False, True)
        assert skin_manager.current_player_state == 'against_wall'
        
        # Test sprite retrieval
        skin_data = skin_manager.get_skin()
        assert len(skin_data) > 0
        
        player_sprite = skin_manager.get_player_sprite()
        assert player_sprite is not None
        
        print("  ✓ Enhanced skin system working correctly")
        
    except Exception as e:
        print(f"  ✗ Error testing enhanced skin system: {e}")
        return False
        
    return True

def test_skins_menu():
    """Test the skins menu."""
    print("Testing skins menu...")
    
    try:
        from src.ui.skins_menu import SkinsMenu
        from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager
        
        pygame.init()
        screen = pygame.display.set_mode((900, 700))
        skin_manager = EnhancedSkinManager()
        menu = SkinsMenu(screen, 900, 700, skin_manager)
        
        # Test basic functionality
        assert len(menu.available_skins) > 0
        assert len(menu.available_tile_sizes) > 0
        assert menu.selected_skin_index >= 0
        assert menu.selected_tile_size_index >= 0
        assert len(menu.buttons) > 0
        assert menu.preview_rect is not None
        
        # Test selection changes
        if len(menu.available_skins) > 1:
            original_index = menu.selected_skin_index
            menu._select_skin(1 if original_index == 0 else 0)
            assert menu.selected_skin_index != original_index
        
        if len(menu.available_tile_sizes) > 1:
            original_index = menu.selected_tile_size_index
            menu._select_tile_size(1 if original_index == 0 else 0)
            assert menu.selected_tile_size_index != original_index
        
        pygame.quit()
        print("  ✓ Skins menu working correctly")
        
    except Exception as e:
        print(f"  ✗ Error testing skins menu: {e}")
        return False
        
    return True

def test_game_integration():
    """Test the integration of all components."""
    print("Testing game integration...")
    
    try:
        from src.core.enhanced_sokoban import EnhancedSokoban
        
        # Test game initialization
        game = EnhancedSokoban()
        
        # Check that all components are properly initialized
        assert game.menu_system is not None
        assert game.game is not None
        assert game.editor is not None
        assert game.skin_manager is not None
        assert game.level_manager is not None
        
        # Check that the enhanced components are being used
        assert hasattr(game.editor, 'zoom_level')
        assert hasattr(game.editor, 'show_grid')
        assert hasattr(game.editor, 'paint_mode')
        
        assert hasattr(game.skin_manager, 'get_player_sprite')
        assert hasattr(game.skin_manager, 'update_player_state')
        assert hasattr(game.skin_manager, 'set_tile_size')
        
        print("  ✓ Game integration working correctly")
        
    except Exception as e:
        print(f"  ✗ Error testing game integration: {e}")
        return False
        
    return True

def main():
    """Run all tests."""
    print("Running enhanced Sokoban tests...\n")
    
    tests = [
        test_responsive_menu,
        test_enhanced_level_editor,
        test_enhanced_skin_system,
        test_skins_menu,
        test_game_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced Sokoban game is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)