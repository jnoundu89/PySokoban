"""
Solution Optimizer for Sokoban Game.

Takes an existing solution and reduces the number of moves/pushes by:
1. Eliminating redundant back-and-forth moves.
2. Re-routing player walks between pushes via shortest paths.
"""

import copy
from collections import deque


DIRECTION_MAP = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0),
}

OPPOSITE = {
    'UP': 'DOWN',
    'DOWN': 'UP',
    'LEFT': 'RIGHT',
    'RIGHT': 'LEFT',
}


class SolutionOptimizer:
    """Optimizes Sokoban solutions to reduce total moves."""

    def optimize(self, level, solution_moves):
        """
        Optimize a solution for the given level.

        Args:
            level: The Level object (will be deep-copied).
            solution_moves: List of move strings ('UP', 'DOWN', 'LEFT', 'RIGHT').

        Returns:
            list[str]: Optimized move list.
        """
        moves = list(solution_moves)
        moves = self.remove_redundant_moves(moves)
        moves = self.optimize_player_paths(level, moves)
        return moves

    def remove_redundant_moves(self, moves):
        """
        Remove consecutive opposite moves that cancel each other.
        Only removes pairs where neither move is a push.

        We do multiple passes until no more reductions are possible.
        """
        changed = True
        while changed:
            changed = False
            result = []
            i = 0
            while i < len(moves):
                if (i + 1 < len(moves) and
                        moves[i + 1] == OPPOSITE.get(moves[i])):
                    # Skip both moves (they cancel out)
                    i += 2
                    changed = True
                else:
                    result.append(moves[i])
                    i += 1
            moves = result
        return moves

    def optimize_player_paths(self, level, moves):
        """
        For each walk segment between pushes, recalculate the shortest path
        using BFS on the board state at that point.

        Args:
            level: The Level object (will be deep-copied).
            moves: List of move strings.

        Returns:
            list[str]: Optimized move list with shorter walk segments.
        """
        # First, identify push moves by simulating the solution
        lvl = copy.deepcopy(level)
        lvl.reset()

        # Classify each move as push or walk
        segments = []  # list of (is_push, [moves])
        current_segment = []
        current_is_push = False

        for move in moves:
            delta = DIRECTION_MAP.get(move)
            if not delta:
                continue

            px, py = lvl.player_pos
            nx, ny = px + delta[0], py + delta[1]
            is_push = (nx, ny) in lvl.boxes

            if current_segment and is_push != current_is_push:
                segments.append((current_is_push, current_segment))
                current_segment = []

            current_segment.append(move)
            current_is_push = is_push
            lvl.move(delta[0], delta[1])

        if current_segment:
            segments.append((current_is_push, current_segment))

        # Now re-simulate and optimize walk segments
        lvl2 = copy.deepcopy(level)
        lvl2.reset()

        optimized = []
        for is_push, seg_moves in segments:
            if is_push:
                # Push segments must be kept as-is (order matters)
                for m in seg_moves:
                    delta = DIRECTION_MAP[m]
                    lvl2.move(delta[0], delta[1])
                optimized.extend(seg_moves)
            else:
                # Walk segment: find where we end up and try BFS shortcut
                start_pos = lvl2.player_pos
                # Execute original moves to find the end position
                for m in seg_moves:
                    delta = DIRECTION_MAP[m]
                    lvl2.move(delta[0], delta[1])
                end_pos = lvl2.player_pos

                # BFS from start to end on the board (treating boxes as walls)
                shorter = self._bfs_path(lvl2, start_pos, end_pos)
                if shorter is not None and len(shorter) < len(seg_moves):
                    optimized.extend(shorter)
                else:
                    optimized.extend(seg_moves)

        return optimized

    def _bfs_path(self, level, start, goal):
        """
        BFS shortest path from start to goal, treating walls and boxes as obstacles.

        Returns:
            list[str] or None: List of direction strings, or None if unreachable.
        """
        if start == goal:
            return []

        queue = deque([(start, [])])
        visited = {start}

        dir_name = {(0, -1): 'UP', (0, 1): 'DOWN', (-1, 0): 'LEFT', (1, 0): 'RIGHT'}

        while queue:
            (x, y), path = queue.popleft()

            for (dx, dy), name in dir_name.items():
                nx, ny = x + dx, y + dy
                if (nx, ny) in visited:
                    continue
                if not (0 <= nx < level.width and 0 <= ny < level.height):
                    continue
                if level.is_wall(nx, ny) or level.is_box(nx, ny):
                    continue

                new_path = path + [name]
                if (nx, ny) == goal:
                    return new_path

                visited.add((nx, ny))
                queue.append(((nx, ny), new_path))

        return None

    def get_optimization_stats(self, original_moves, optimized_moves):
        """
        Get statistics about the optimization.

        Returns:
            dict: Stats including moves saved, pushes comparison, etc.
        """
        return {
            'original_moves': len(original_moves),
            'optimized_moves': len(optimized_moves),
            'moves_saved': len(original_moves) - len(optimized_moves),
            'reduction_percent': (
                (1 - len(optimized_moves) / max(len(original_moves), 1)) * 100
            ),
        }
