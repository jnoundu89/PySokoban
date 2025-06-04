"""
Sokoban Level Solver module.

This module provides functionality to solve Sokoban levels and determine if they are solvable.
It implements a complete breadth-first search algorithm that guarantees to find a solution
if one exists.
"""

import copy
from collections import deque
from level import Level


class SokobanSolver:
    """
    Class for solving Sokoban levels.
    
    This class implements a breadth-first search algorithm to find solutions
    for Sokoban levels. It can determine if a level is solvable and provide
    the solution path.
    """
    
    def __init__(self, max_states=1000000):
        """
        Initialize the solver.
        
        Args:
            max_states (int, optional): Maximum number of states to explore before giving up.
                                       Defaults to 1,000,000.
        """
        self.max_states = max_states
        self.visited_states = set()
        self.solution = None
        self.states_explored = 0
    
    def is_solvable(self, level):
        """
        Check if the level is solvable.
        
        Args:
            level (Level): The level to check.
            
        Returns:
            bool: True if the level is solvable, False otherwise.
        """
        self.solution = self._solve(level)
        return self.solution is not None
    
    def get_solution(self):
        """
        Get the solution for the last solved level.
        
        Returns:
            list: List of moves in the solution, or None if no solution was found.
        """
        return self.solution
    
    def _solve(self, level):
        """
        Find a solution for the level using breadth-first search.
        
        Args:
            level (Level): The level to solve.
            
        Returns:
            list: List of moves in the solution, or None if no solution was found.
        """
        # Reset state
        self.visited_states = set()
        self.states_explored = 0
        
        # Create a queue for BFS
        queue = deque()
        
        # Create initial state
        initial_state = self._get_state(level)
        initial_hash = self._get_state_hash(initial_state)
        
        # Add initial state to queue and visited set
        queue.append((initial_state, []))  # (state, moves)
        self.visited_states.add(initial_hash)
        
        # BFS loop
        while queue and self.states_explored < self.max_states:
            # Get the next state and moves from the queue
            state, moves = queue.popleft()
            self.states_explored += 1
            
            # Check if this state is a solution
            if self._is_solved(state):
                return moves
            
            # Try all possible moves
            for direction, (dx, dy) in [('up', (0, -1)), ('down', (0, 1)), 
                                       ('left', (-1, 0)), ('right', (1, 0))]:
                # Create a new level from the current state
                new_level = self._create_level_from_state(state)
                
                # Try to move in the given direction
                if new_level.move(dx, dy):
                    # Get the new state
                    new_state = self._get_state(new_level)
                    new_hash = self._get_state_hash(new_state)
                    
                    # If this state hasn't been visited before
                    if new_hash not in self.visited_states:
                        # Check for deadlocks
                        if not self._is_deadlock(new_level, new_state):
                            # Add to queue and visited set
                            new_moves = moves + [direction]
                            queue.append((new_state, new_moves))
                            self.visited_states.add(new_hash)
        
        # If we get here, no solution was found
        return None
    
    def _get_state(self, level):
        """
        Get the current state of the level.
        
        Args:
            level (Level): The level to get the state from.
            
        Returns:
            dict: A dictionary representing the current state.
        """
        return {
            'player_pos': level.player_pos,
            'boxes': frozenset(level.boxes),
            'map_data': tuple(tuple(row) for row in level.map_data)
        }
    
    def _get_state_hash(self, state):
        """
        Create a hash of the current level state for tracking visited states.
        
        Args:
            state (dict): The state to hash.
            
        Returns:
            tuple: A hashable representation of the state.
        """
        return (state['player_pos'], state['boxes'])
    
    def _create_level_from_state(self, state):
        """
        Create a new Level object from a state.
        
        Args:
            state (dict): The state to create a level from.
            
        Returns:
            Level: A new Level object with the given state.
        """
        # Create a string representation of the level
        map_data = list(list(row) for row in state['map_data'])
        level_string = '\n'.join(''.join(row) for row in map_data)
        
        # Create a new level
        level = Level(level_data=level_string)
        
        # Set the player position and boxes
        level.player_pos = state['player_pos']
        level.boxes = list(state['boxes'])
        
        return level
    
    def _is_solved(self, state):
        """
        Check if the state represents a solved level.
        
        Args:
            state (dict): The state to check.
            
        Returns:
            bool: True if the level is solved, False otherwise.
        """
        # A level is solved if all boxes are on targets
        # We need to extract targets from the map data
        targets = set()
        for y, row in enumerate(state['map_data']):
            for x, cell in enumerate(row):
                if cell == '.':  # TARGET
                    targets.add((x, y))
        
        # Check if all boxes are on targets
        return all(box in targets for box in state['boxes'])
    
    def _is_deadlock(self, level, state):
        """
        Check if the level is in a deadlock state.
        
        Args:
            level (Level): The level to check.
            state (dict): The current state.
            
        Returns:
            bool: True if the level is in a deadlock state, False otherwise.
        """
        # Simple deadlock detection: check for boxes in corners
        for box_x, box_y in state['boxes']:
            # Skip boxes that are already on targets
            if level.is_target(box_x, box_y):
                continue
            
            # Check if box is in a corner
            if ((level.is_wall(box_x - 1, box_y) and level.is_wall(box_x, box_y - 1)) or
                (level.is_wall(box_x + 1, box_y) and level.is_wall(box_x, box_y - 1)) or
                (level.is_wall(box_x - 1, box_y) and level.is_wall(box_x, box_y + 1)) or
                (level.is_wall(box_x + 1, box_y) and level.is_wall(box_x, box_y + 1))):
                return True
        
        # No deadlock detected
        return False


def test_solver():
    """
    Test the solver with a simple level.
    """
    # Create a simple level
    level_string = """
    #####
    #   #
    # $ #
    # . #
    # @ #
    #####
    """
    level = Level(level_data=level_string)
    
    # Create a solver
    solver = SokobanSolver()
    
    # Check if the level is solvable
    is_solvable = solver.is_solvable(level)
    
    # Print the result
    print(f"Level is solvable: {is_solvable}")
    if is_solvable:
        print(f"Solution: {solver.get_solution()}")
        print(f"States explored: {solver.states_explored}")


if __name__ == "__main__":
    test_solver()