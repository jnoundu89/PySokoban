"""Tests for SolutionOptimizer: redundant move removal and path optimization."""

import pytest
from src.core.level import Level
from src.ai.solution_optimizer import SolutionOptimizer


@pytest.fixture
def optimizer():
    return SolutionOptimizer()


class TestRemoveRedundantMoves:

    def test_cancel_opposite_pair(self, optimizer):
        moves = ['UP', 'DOWN']
        result = optimizer.remove_redundant_moves(moves)
        assert result == []

    def test_cancel_multiple_pairs(self, optimizer):
        moves = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        result = optimizer.remove_redundant_moves(moves)
        assert result == []

    def test_nested_cancellation(self, optimizer):
        # UP, LEFT, RIGHT, DOWN -> LEFT/RIGHT cancel -> UP, DOWN -> cancel
        moves = ['UP', 'LEFT', 'RIGHT', 'DOWN']
        result = optimizer.remove_redundant_moves(moves)
        assert result == []

    def test_no_redundancy(self, optimizer):
        moves = ['UP', 'UP', 'RIGHT', 'RIGHT']
        result = optimizer.remove_redundant_moves(moves)
        assert result == ['UP', 'UP', 'RIGHT', 'RIGHT']

    def test_partial_cancellation(self, optimizer):
        moves = ['UP', 'RIGHT', 'LEFT', 'UP']
        result = optimizer.remove_redundant_moves(moves)
        assert result == ['UP', 'UP']

    def test_empty_input(self, optimizer):
        assert optimizer.remove_redundant_moves([]) == []


class TestOptimizePlayerPaths:

    def test_shortens_walk(self, optimizer):
        # Level where a detour walk can be shortened
        #  #######
        #  #@   .#
        #  # $ $ #
        #  #     #
        #  #######
        lvl = Level(level_data="#######\n#@   .#\n# $ $ #\n#     #\n#######")
        # Suboptimal walk: right, down, down, right, up, up, right
        # Optimal: right, right, right, right (4 moves vs 7)
        moves = ['RIGHT', 'DOWN', 'DOWN', 'RIGHT', 'UP', 'UP', 'RIGHT', 'RIGHT']
        optimized = optimizer.optimize_player_paths(lvl, moves)
        assert len(optimized) <= len(moves)

    def test_preserves_pushes(self, optimizer):
        """Push sequences must not be altered."""
        lvl = Level(level_data="#####\n#@$.#\n#####")
        moves = ['RIGHT']  # single push
        optimized = optimizer.optimize_player_paths(lvl, moves)
        assert optimized == ['RIGHT']

    def test_stats(self, optimizer):
        original = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'UP']
        optimized = ['UP']
        stats = optimizer.get_optimization_stats(original, optimized)
        assert stats['original_moves'] == 5
        assert stats['optimized_moves'] == 1
        assert stats['moves_saved'] == 4
        assert stats['reduction_percent'] == pytest.approx(80.0)

    def test_full_optimize(self, optimizer):
        """Full optimize pipeline: redundancy removal + path shortening."""
        lvl = Level(level_data="#####\n#@ .#\n#   #\n#####")
        moves = ['RIGHT', 'LEFT', 'RIGHT', 'DOWN', 'UP', 'RIGHT']
        optimized = optimizer.optimize(lvl, moves)
        assert len(optimized) <= len(moves)
