"""Tests for EnhancedSkinManager: initialization, skin loading, sprite state."""

import os
import pytest

# pygame is required for skin manager
pygame = pytest.importorskip("pygame")

from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Initialize pygame display for sprite loading."""
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def skin_manager():
    return EnhancedSkinManager()


class TestInitialization:

    def test_creates_instance(self, skin_manager):
        assert skin_manager is not None

    def test_has_available_skins(self, skin_manager):
        skins = skin_manager.get_available_skins()
        assert isinstance(skins, list)
        assert len(skins) > 0

    def test_has_available_tile_sizes(self, skin_manager):
        sizes = skin_manager.get_available_tile_sizes()
        assert isinstance(sizes, list)
        assert len(sizes) > 0

    def test_current_skin_set(self, skin_manager):
        assert skin_manager.current_skin is not None


class TestPlayerSprite:

    def test_get_player_sprite(self, skin_manager):
        sprite = skin_manager.get_player_sprite()
        assert sprite is not None

    def test_update_player_state(self, skin_manager):
        skin_manager.update_player_state('right', False, False)
        sprite = skin_manager.get_player_sprite()
        assert sprite is not None

    def test_push_state(self, skin_manager):
        skin_manager.update_player_state('down', True, False)
        sprite = skin_manager.get_player_sprite()
        assert sprite is not None

    def test_blocked_state(self, skin_manager):
        skin_manager.update_player_state('left', False, True)
        sprite = skin_manager.get_player_sprite()
        assert sprite is not None


class TestSpriteHistory:

    def test_reset_sprite_history(self, skin_manager):
        skin_manager.update_player_state('right', False, False)
        skin_manager.get_player_sprite(advance_animation=True)
        skin_manager.reset_sprite_history()
        # Should not raise

    def test_get_previous_sprite(self, skin_manager):
        skin_manager.update_player_state('right', False, False)
        skin_manager.get_player_sprite(advance_animation=True)
        skin_manager.update_player_state('left', False, False)
        skin_manager.get_player_sprite(advance_animation=True)
        prev = skin_manager.get_previous_sprite()
        assert prev is not None


class TestTileSize:

    def test_get_available_tile_sizes_returns_ints(self, skin_manager):
        sizes = skin_manager.get_available_tile_sizes()
        assert all(isinstance(s, int) for s in sizes)

    def test_current_skin_has_name(self, skin_manager):
        assert isinstance(skin_manager.current_skin, str)
        assert len(skin_manager.current_skin) > 0
