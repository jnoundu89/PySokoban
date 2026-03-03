"""Tests for level collection parsing and LevelManager."""

import os
import pytest
from src.core.level import Level
from src.level_management.level_collection_parser import LevelCollectionParser
from src.level_management.level_manager import LevelManager


LEVELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'levels')
ORIGINAL_DIR = os.path.join(LEVELS_DIR, 'Original & Extra')
ORIGINAL_FILE = os.path.join(ORIGINAL_DIR, 'Original.txt')


def has_levels():
    return os.path.isdir(LEVELS_DIR) and os.path.isfile(ORIGINAL_FILE)


# ---------------------------------------------------------------------------
# Collection Parser
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not has_levels(), reason="Level files not found")
class TestLevelCollectionParser:

    def test_parse_original(self):
        collection = LevelCollectionParser.parse_file(ORIGINAL_FILE)
        assert collection is not None
        assert collection.get_level_count() > 0

    def test_level_count_original(self):
        collection = LevelCollectionParser.parse_file(ORIGINAL_FILE)
        assert collection.get_level_count() == 90

    def test_get_level_returns_tuple(self):
        collection = LevelCollectionParser.parse_file(ORIGINAL_FILE)
        title, level = collection.get_level(0)
        assert isinstance(title, str)
        assert isinstance(level, Level)

    def test_level_is_playable(self):
        collection = LevelCollectionParser.parse_file(ORIGINAL_FILE)
        _, level = collection.get_level(0)
        assert level.player_pos is not None
        assert len(level.boxes) > 0
        assert len(level.targets) > 0
        assert len(level.boxes) == len(level.targets)


# ---------------------------------------------------------------------------
# Level Manager
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not has_levels(), reason="Level files not found")
class TestLevelManager:

    def test_loads_levels(self):
        mgr = LevelManager(LEVELS_DIR)
        assert mgr.current_level is not None

    def test_navigation(self):
        mgr = LevelManager(LEVELS_DIR)
        if mgr.has_next_level_in_collection():
            mgr.next_level_in_collection()
            assert mgr.current_level is not None

    def test_reset(self):
        mgr = LevelManager(LEVELS_DIR)
        mgr.current_level.move(1, 0)
        mgr.reset_current_level()
        assert mgr.current_level.moves == 0


# ---------------------------------------------------------------------------
# Inline level parsing edge cases
# ---------------------------------------------------------------------------

class TestLevelEdgeCases:

    def test_player_on_target(self):
        lvl = Level(level_data="###\n#+$#\n# .#\n####")
        assert lvl.player_pos is not None
        assert lvl.player_pos in lvl.targets or any(
            t == lvl.player_pos for t in lvl.targets
        )

    def test_box_on_target(self):
        lvl = Level(level_data="###\n#@*#\n####")
        assert len(lvl.boxes) == 1
        assert len(lvl.targets) == 1
        assert lvl.boxes[0] in lvl.targets

    def test_empty_lines_stripped(self):
        lvl = Level(level_data="\n\n###\n#@.#\n# $#\n####\n\n")
        assert lvl.height == 4
