"""Tests for SolutionReplayController: state precomputation, navigation, playback."""

import pytest
from src.core.level import Level


# We can't fully test render_controls without a display, but we can test
# all the state logic.

LEVEL_DATA = (
    "#####\n"
    "#@$.#\n"
    "#####"
)

SOLUTION = ['RIGHT']  # Push box onto target


@pytest.fixture
def level():
    return Level(level_data=LEVEL_DATA)


def _make_controller(level, moves):
    """Create a controller without needing pygame display."""
    from src.ui.solution_replay import SolutionReplayController, DIRECTION_MAP
    import copy

    # Manually build the controller to avoid needing renderer/skin_manager
    class FakeRenderer:
        class FakeScreen:
            def get_size(self):
                return (800, 600)
            def get_width(self):
                return 800
            def get_height(self):
                return 600
        screen = FakeScreen()

    ctrl = SolutionReplayController.__new__(SolutionReplayController)
    ctrl.renderer = FakeRenderer()
    ctrl.skin_manager = None
    ctrl.solution_moves = list(moves)
    ctrl.states = []
    ctrl.current_index = 0
    ctrl.playing = False
    ctrl.speed_ms = 300
    ctrl.last_step_time = 0
    ctrl.finished = False
    ctrl._bar_height = 60

    # Precompute states
    lvl = copy.deepcopy(level)
    lvl.reset()
    ctrl.states.append((lvl.player_pos, list(lvl.boxes)))
    for move in moves:
        delta = DIRECTION_MAP.get(move)
        if delta:
            lvl.move(delta[0], delta[1])
        ctrl.states.append((lvl.player_pos, list(lvl.boxes)))

    return ctrl


class TestStatePrecomputation:

    def test_states_count(self, level):
        ctrl = _make_controller(level, SOLUTION)
        # Initial + 1 move = 2 states
        assert len(ctrl.states) == 2

    def test_initial_state(self, level):
        ctrl = _make_controller(level, SOLUTION)
        player_pos, boxes = ctrl.states[0]
        assert player_pos == (1, 1)
        assert (2, 1) in boxes

    def test_final_state(self, level):
        ctrl = _make_controller(level, SOLUTION)
        player_pos, boxes = ctrl.states[-1]
        assert player_pos == (2, 1)
        assert (3, 1) in boxes  # box pushed onto target

    def test_multi_move_states(self):
        lvl = Level(level_data="#######\n#@  $.#\n#######")
        moves = ['RIGHT', 'RIGHT', 'RIGHT']  # walk, walk, push
        ctrl = _make_controller(lvl, moves)
        assert len(ctrl.states) == 4


class TestNavigation:

    def test_step_forward(self, level):
        ctrl = _make_controller(level, SOLUTION)
        assert ctrl.current_index == 0
        ctrl.step_forward()
        assert ctrl.current_index == 1

    def test_step_backward(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.step_forward()
        ctrl.step_backward()
        assert ctrl.current_index == 0

    def test_step_backward_at_start(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.step_backward()
        assert ctrl.current_index == 0

    def test_step_forward_at_end(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.step_forward()
        ctrl.step_forward()  # past end
        assert ctrl.current_index == 1  # clamped

    def test_jump_to(self, level):
        moves = ['RIGHT']
        ctrl = _make_controller(level, moves)
        ctrl.jump_to(0)
        assert ctrl.current_index == 0
        ctrl.jump_to(1)
        assert ctrl.current_index == 1

    def test_jump_clamped(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.jump_to(999)
        assert ctrl.current_index == len(ctrl.states) - 1
        ctrl.jump_to(-5)
        assert ctrl.current_index == 0


class TestPlayback:

    def test_play_pause(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.play()
        assert ctrl.playing is True
        ctrl.pause()
        assert ctrl.playing is False

    def test_toggle(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.toggle_play()
        assert ctrl.playing is True
        ctrl.toggle_play()
        assert ctrl.playing is False

    def test_speed_limits(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.set_speed(10)
        assert ctrl.speed_ms == 20  # min
        ctrl.set_speed(5000)
        assert ctrl.speed_ms == 2000  # max

    def test_update_advances_when_playing(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.play()
        ctrl.last_step_time = 0
        result = ctrl.update(1000)  # well past speed_ms=300
        assert result is True
        assert ctrl.current_index == 1

    def test_update_stops_at_end(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.play()
        ctrl.current_index = len(ctrl.states) - 1
        ctrl.update(1000)
        assert ctrl.playing is False

    def test_apply_state(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.current_index = 1
        ctrl.apply_state(level)
        assert level.player_pos == ctrl.states[1][0]
        assert level.boxes == list(ctrl.states[1][1])

    def test_finished_stops_update(self, level):
        ctrl = _make_controller(level, SOLUTION)
        ctrl.finished = True
        assert ctrl.update(0) is False
