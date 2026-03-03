"""Tests for ConfigManager: defaults, get/set, keybindings, persistence."""

import json
import os
import tempfile
import pytest
from src.core.config_manager import ConfigManager


@pytest.fixture
def config(tmp_path):
    """ConfigManager backed by a temporary file."""
    path = str(tmp_path / "test_config.json")
    return ConfigManager(config_file=path)


class TestDefaults:

    def test_default_keyboard(self, config):
        assert config.get('game', 'keyboard_layout') == 'qwerty'

    def test_default_keybindings(self, config):
        kb = config.get_keybindings()
        assert kb['undo'] == 'u'
        assert kb['redo'] == 'y'
        assert kb['snapshot_save'] == 'f5'
        assert kb['snapshot_load'] == 'f9'
        assert kb['reverse_mode'] == 'x'
        assert kb['optimize_solution'] == 'o'

    def test_default_mouse_tracking(self, config):
        assert config.get('game', 'mouse_pusher_tracking') is False

    def test_default_skin(self, config):
        assert config.get('skin', 'current_skin') == 'default'

    def test_default_display(self, config):
        assert config.get('display', 'window_width') == 900
        assert config.get('display', 'fullscreen') is False


class TestGetSet:

    def test_set_and_get(self, config):
        config.set('game', 'zoom_level', 2.5)
        assert config.get('game', 'zoom_level') == 2.5

    def test_get_missing_returns_default(self, config):
        assert config.get('game', 'nonexistent', 42) == 42

    def test_get_missing_section(self, config):
        assert config.get('nonexistent', 'key', 'fallback') == 'fallback'

    def test_set_creates_section(self, config):
        config.set('newsection', 'key', 'value')
        assert config.get('newsection', 'key') == 'value'


class TestKeybindings:

    def test_set_keybinding(self, config):
        config.set_keybinding('undo', 'z')
        assert config.get_keybindings()['undo'] == 'z'

    def test_reset_keybindings(self, config):
        config.set_keybinding('undo', 'z')
        config.reset_keybindings()
        assert config.get_keybindings()['undo'] == 'u'


class TestPersistence:

    def test_save_creates_file(self, config, tmp_path):
        # Config file path was set relative to project root, but we passed tmp_path
        # Let's check the actual config_file attribute
        config.save()
        assert os.path.exists(config.config_file)

    def test_reload_preserves_values(self, tmp_path):
        path = str(tmp_path / "test_config.json")
        c1 = ConfigManager(config_file=path)
        c1.set('game', 'zoom_level', 3.0)

        c2 = ConfigManager(config_file=path)
        assert c2.get('game', 'zoom_level') == 3.0

    def test_reset_to_defaults(self, config):
        config.set('game', 'zoom_level', 5.0)
        config.reset_to_defaults()
        assert config.get('game', 'zoom_level') == 1.0


class TestSpecializedSetters:

    def test_set_skin_config(self, config):
        config.set_skin_config('retro', 32)
        assert config.get('skin', 'current_skin') == 'retro'
        assert config.get('skin', 'tile_size') == 32

    def test_set_display_config(self, config):
        config.set_display_config(width=1920, height=1080, fullscreen=True)
        assert config.get('display', 'window_width') == 1920
        assert config.get('display', 'fullscreen') is True

    def test_set_game_config(self, config):
        config.set_game_config(movement_cooldown=100, show_deadlocks=False)
        assert config.get('game', 'movement_cooldown') == 100
        assert config.get('game', 'show_deadlocks') is False
