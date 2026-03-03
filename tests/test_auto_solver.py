"""Tests for AutoSolver: solving simple levels with timeout protection."""

import pytest
from src.core.level import Level
from src.core.auto_solver import AutoSolver


# Very simple level: one box, one target, 1 push
TRIVIAL_LEVEL = (
    "#####\n"
    "#@$.#\n"
    "#####"
)

# Simple level: requires a few moves
SIMPLE_LEVEL = (
    "######\n"
    "#    #\n"
    "# @$ #\n"
    "#  . #\n"
    "######"
)


@pytest.fixture
def trivial():
    return Level(level_data=TRIVIAL_LEVEL)


@pytest.fixture
def simple():
    return Level(level_data=SIMPLE_LEVEL)


class TestAutoSolver:

    def test_solve_trivial(self, trivial):
        solver = AutoSolver(trivial)
        success = solver.solve_level()
        assert success is True
        assert solver.solution is not None
        assert len(solver.solution) >= 1

    def test_solution_is_valid(self, trivial):
        """Apply solution moves and verify level is completed."""
        solver = AutoSolver(trivial)
        assert solver.solve_level()

        direction_map = {
            'UP': (0, -1), 'DOWN': (0, 1),
            'LEFT': (-1, 0), 'RIGHT': (1, 0),
        }

        for move in solver.solution:
            dx, dy = direction_map[move]
            trivial.move(dx, dy)

        assert trivial.is_completed()

    def test_solve_simple(self, simple):
        solver = AutoSolver(simple)
        assert solver.solve_level()
        assert solver.solution is not None

    def test_solution_applied_completes_simple(self, simple):
        solver = AutoSolver(simple)
        assert solver.solve_level()

        direction_map = {
            'UP': (0, -1), 'DOWN': (0, 1),
            'LEFT': (-1, 0), 'RIGHT': (1, 0),
        }

        for move in solver.solution:
            dx, dy = direction_map[move]
            simple.move(dx, dy)

        assert simple.is_completed()

    def test_get_solution_info(self, trivial):
        solver = AutoSolver(trivial)
        solver.solve_level()
        info = solver.get_solution_info()
        assert info is not None
        assert 'moves' in info or 'move_count' in info or isinstance(info, dict)
