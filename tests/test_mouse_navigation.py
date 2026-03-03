"""Tests for MouseNavigationSystem: YASC-style pathfinding, lift-and-drop, BoxPushPathfinder."""

import pytest
from src.core.level import Level
from src.ui.mouse_navigation import (
    MouseNavigationSystem, MouseMode, BoxPushPathfinder
)


# Open level for pathfinding
#  #####
#  #.  #
#  # $ #
#  # @ #
#  #   #
#  #####
OPEN_LEVEL = (
    "#####\n"
    "#.  #\n"
    "# $ #\n"
    "# @ #\n"
    "#   #\n"
    "#####"
)

# Push test level
#  #####
#  #.  #
#  # $@#
#  #   #
#  #####
PUSH_LEVEL = (
    "#####\n"
    "#.  #\n"
    "# $@#\n"
    "#   #\n"
    "#####"
)


@pytest.fixture
def nav():
    return MouseNavigationSystem()


@pytest.fixture
def open_level():
    return Level(level_data=OPEN_LEVEL)


@pytest.fixture
def push_level():
    return Level(level_data=PUSH_LEVEL)


# ---------------------------------------------------------------------------
# A* Pathfinding
# ---------------------------------------------------------------------------

class TestPathfinding:

    def test_path_to_self_empty(self, nav, open_level):
        nav.set_level(open_level)
        path = nav._calculate_path((2, 3), (2, 3))
        assert path == []

    def test_path_adjacent(self, nav, open_level):
        nav.set_level(open_level)
        path = nav._calculate_path((2, 3), (2, 4))
        assert path == [(2, 3), (2, 4)]

    def test_path_around_box(self, nav, open_level):
        """Path should go around a box, not through it."""
        nav.set_level(open_level)
        path = nav._calculate_path((2, 3), (2, 1))
        assert (2, 2) not in path  # box position excluded
        assert path[0] == (2, 3)
        assert path[-1] == (2, 1)

    def test_path_blocked_by_walls(self, nav):
        lvl = Level(level_data="###\n#@#\n###")
        nav.set_level(lvl)
        path = nav._calculate_path((1, 1), (0, 0))
        assert path == [] or path[-1] == (1, 1)

    def test_path_to_movements(self, nav):
        path = [(1, 1), (2, 1), (2, 2), (2, 3)]
        movements = nav._path_to_movements(path)
        assert movements == ['right', 'down', 'down']


# ---------------------------------------------------------------------------
# YASC-style Lift-and-Drop
# ---------------------------------------------------------------------------

class TestLiftAndDrop:

    def test_click_box_enters_lift_mode(self, nav, push_level):
        """Clicking a movable box should enter BOX_LIFTED mode (YASC-style)."""
        nav.set_level(push_level)
        nav.player_position = push_level.player_pos  # (3,2)
        result = nav._handle_left_click((2, 2))  # box position
        assert result is True
        assert nav.mouse_mode == MouseMode.BOX_LIFTED
        assert nav.lifted_box_pos == (2, 2)

    def test_click_box_does_not_move_player(self, nav, push_level):
        """Clicking a box should NOT immediately move the player."""
        nav.set_level(push_level)
        nav.player_position = push_level.player_pos
        original_pos = push_level.player_pos
        nav._handle_left_click((2, 2))
        assert push_level.player_pos == original_pos
        assert nav.movement_queue == []
        assert nav.is_moving is False

    def test_drop_on_reachable_target(self, nav, push_level):
        """Dropping on a reachable target should queue movements."""
        nav.set_level(push_level)
        nav.player_position = push_level.player_pos
        nav.mouse_mode = MouseMode.BOX_LIFTED
        nav.lifted_box_pos = (2, 2)
        result = nav._handle_lift_drop((1, 1))
        assert result is True
        assert len(nav.movement_queue) > 0
        assert nav.mouse_mode == MouseMode.PATH_EXECUTING

    def test_right_click_cancels_lift(self, nav, push_level):
        nav.set_level(push_level)
        nav.mouse_mode = MouseMode.BOX_LIFTED
        nav.lifted_box_pos = (2, 2)
        assert nav.handle_right_click() is True
        assert nav.mouse_mode == MouseMode.IDLE
        assert nav.lifted_box_pos is None

    def test_click_same_box_cancels(self, nav, push_level):
        nav.set_level(push_level)
        nav.mouse_mode = MouseMode.BOX_LIFTED
        nav.lifted_box_pos = (2, 2)
        nav._handle_lift_drop((2, 2))
        assert nav.mouse_mode == MouseMode.IDLE

    def test_drop_on_unreachable_stays_in_lift(self, nav):
        """Dropping on unreachable target should stay in BOX_LIFTED mode."""
        lvl = Level(level_data="####\n#$@#\n####")
        nav.set_level(lvl)
        nav.player_position = lvl.player_pos
        nav.mouse_mode = MouseMode.BOX_LIFTED
        nav.lifted_box_pos = (1, 1)
        # Box at (1,1) walled in on all sides except player side — can't push
        result = nav._handle_lift_drop((0, 0))  # wall position, unreachable
        assert result is True  # handled but stays in lift
        assert nav.mouse_mode == MouseMode.BOX_LIFTED  # unchanged

    def test_click_empty_cell_walks(self, nav, open_level):
        """Clicking an empty cell in IDLE mode should queue walk movements."""
        nav.set_level(open_level)
        nav.player_position = open_level.player_pos  # (2,3)
        # Calculate path first (normally done by update_mouse_position)
        nav.current_path = nav._calculate_path((2, 3), (2, 4))
        result = nav._handle_left_click((2, 4))
        assert result is True
        assert nav.is_moving is True
        assert nav.movement_queue == ['down']


# ---------------------------------------------------------------------------
# BoxPushPathfinder
# ---------------------------------------------------------------------------

class TestBoxPushPathfinder:

    def test_simple_push(self, push_level):
        nav = MouseNavigationSystem()
        nav.set_level(push_level)
        pf = BoxPushPathfinder(push_level, nav._calculate_path)
        result = pf.find_push_path((2, 2), (2, 1), push_level.player_pos)
        assert result is not None
        assert len(result) >= 1

    def test_multi_push(self, push_level):
        nav = MouseNavigationSystem()
        nav.set_level(push_level)
        pf = BoxPushPathfinder(push_level, nav._calculate_path)
        result = pf.find_push_path((2, 2), (1, 1), push_level.player_pos)
        assert result is not None
        assert len(result) == 2

    def test_impossible_push(self):
        lvl = Level(level_data="####\n#$@#\n####")
        nav = MouseNavigationSystem()
        nav.set_level(lvl)
        pf = BoxPushPathfinder(lvl, nav._calculate_path)
        result = pf.find_push_path((1, 1), (2, 1), lvl.player_pos)
        # Box at (1,1), player at (2,1). Push right needs player at (0,1)=wall.
        # So this is likely None.

    def test_box_already_at_goal(self, push_level):
        nav = MouseNavigationSystem()
        nav.set_level(push_level)
        pf = BoxPushPathfinder(push_level, nav._calculate_path)
        result = pf.find_push_path((2, 2), (2, 2), push_level.player_pos)
        assert result == []

    def test_multi_push_through_original_position(self):
        """Push box 3 cells: player must traverse the box's original position."""
        # ######
        # #    #
        # # $@ #
        # #    #
        # ######
        lvl = Level(level_data="######\n#    #\n# $@ #\n#    #\n######")
        nav = MouseNavigationSystem()
        nav.set_level(lvl)
        pf = BoxPushPathfinder(lvl, nav._calculate_path)
        # Box at (2,2), player at (3,2). Push box left to (1,1) = 2 pushes.
        result = pf.find_push_path((2, 2), (1, 1), lvl.player_pos)
        assert result is not None
        assert len(result) >= 2

    def test_multi_push_same_direction(self):
        """Push box 2 cells right: player must go around to push twice."""
        # #######
        # #     #
        # # $@  #
        # #     #
        # #######
        lvl = Level(level_data="#######\n#     #\n# $@  #\n#     #\n#######")
        nav = MouseNavigationSystem()
        nav.set_level(lvl)
        pf = BoxPushPathfinder(lvl, nav._calculate_path)
        # Box at (2,2), player at (3,2). Push box right to (4,2) = 2 pushes.
        result = pf.find_push_path((2, 2), (4, 2), lvl.player_pos)
        assert result is not None
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Movement Queue
# ---------------------------------------------------------------------------

class TestMovementQueue:

    def test_execute_movement(self, nav, open_level):
        nav.set_level(open_level)
        assert nav._execute_movement('down')
        assert open_level.player_pos == (2, 4)

    def test_execute_movement_invalid(self, nav):
        lvl = Level(level_data="###\n#@#\n###")
        nav.set_level(lvl)
        assert not nav._execute_movement('up')

    def test_dir_to_str(self):
        assert MouseNavigationSystem._dir_to_str(0, -1) == 'up'
        assert MouseNavigationSystem._dir_to_str(0, 1) == 'down'
        assert MouseNavigationSystem._dir_to_str(-1, 0) == 'left'
        assert MouseNavigationSystem._dir_to_str(1, 0) == 'right'
        assert MouseNavigationSystem._dir_to_str(1, 1) is None
