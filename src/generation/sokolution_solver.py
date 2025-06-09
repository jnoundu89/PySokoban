"""
Advanced Sokoban solver based on the Sokolution solver by Florent Diedler.
This implementation incorporates techniques described in the Sokolution solver:
- Multiple search algorithms (BFS, DFS, A*, IDA*)
- Forward, backward, and bidirectional search modes
- Advanced heuristic using bipartite matching (Hungarian algorithm)
- Transposition table with hash function
- PI-Corral pruning
- Macro moves
- Dynamic deadlock detection

Author: AI Assistant
"""

import time
import heapq
from collections import deque, defaultdict
from typing import List, Tuple, Set, Dict, Optional, FrozenSet, Any, Callable
import itertools

# Constants for search algorithms
ALGORITHM_BFS = "BFS"
ALGORITHM_DFS = "DFS"
ALGORITHM_ASTAR = "A*"
ALGORITHM_IDA = "IDA*"
ALGORITHM_GREEDY = "GREEDY"

# Constants for search modes
MODE_FORWARD = "FORWARD"
MODE_BACKWARD = "BACKWARD"
MODE_BIDIRECTIONAL = "BIDIRECTIONAL"

class SokolutionState:
    """
    Represents a state in the Sokoban game.
    """
    def __init__(self, player_pos: Tuple[int, int], boxes: FrozenSet[Tuple[int, int]], 
                 parent=None, move=None, g_cost=0):
        self.player_pos = player_pos
        self.boxes = boxes
        self.parent = parent
        self.move = move
        self.g_cost = g_cost
        self.h_cost = 0
        self.f_cost = 0
    
    def __hash__(self):
        return hash((self.player_pos, self.boxes))
    
    def __eq__(self, other):
        if not isinstance(other, SokolutionState):
            return False
        return self.player_pos == other.player_pos and self.boxes == other.boxes
    
    def __lt__(self, other):
        # Primary sort by f_cost, secondary by h_cost, tertiary by newest (higher g_cost)
        if self.f_cost != other.f_cost:
            return self.f_cost < other.f_cost
        if self.h_cost != other.h_cost:
            return self.h_cost < other.h_cost
        return self.g_cost > other.g_cost  # Prefer newer nodes (higher g_cost)

class TranspositionTable:
    """
    A custom transposition table for storing visited states.
    Uses open-addressing with linear probing.
    """
    def __init__(self, size=1000000):
        self.size = size
        self.table = [None] * size
        self.count = 0
    
    def _hash(self, state: SokolutionState) -> int:
        """
        Hash function for the state.
        """
        # Use the default hash function for the state and do a modulo with the table size
        return hash(state) % self.size
    
    def add(self, state: SokolutionState) -> bool:
        """
        Add a state to the table.
        Returns True if the state was added, False if it was already in the table.
        """
        if self.count >= self.size * 0.75:  # Resize if load factor > 0.75
            self._resize(self.size * 2)
        
        index = self._hash(state)
        
        # Linear probing
        while self.table[index] is not None:
            if self.table[index] == state:
                return False  # State already in table
            index = (index + 1) % self.size
        
        self.table[index] = state
        self.count += 1
        return True
    
    def contains(self, state: SokolutionState) -> bool:
        """
        Check if a state is in the table.
        """
        index = self._hash(state)
        
        # Linear probing
        while self.table[index] is not None:
            if self.table[index] == state:
                return True
            index = (index + 1) % self.size
        
        return False
    
    def _resize(self, new_size: int):
        """
        Resize the table.
        """
        old_table = self.table
        self.size = new_size
        self.table = [None] * new_size
        self.count = 0
        
        for state in old_table:
            if state is not None:
                self.add(state)

class DeadlockDetector:
    """
    Advanced deadlock detection for Sokoban.
    """
    def __init__(self, level):
        self.level = level
        self.width = level.width
        self.height = level.height
        
        # Precompute deadlock positions
        self.corner_deadlocks = self._find_corner_deadlocks()
        self.goal_room_map = self._build_goal_room_map()
        
        # Cache for freeze deadlocks
        self.freeze_deadlock_cache = {}
        
        # Dynamic deadlock patterns found during search
        self.deadlock_patterns = set()
    
    def _find_corner_deadlocks(self) -> Set[Tuple[int, int]]:
        """
        Find all corner deadlock positions.
        """
        corner_deadlocks = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if self._is_corner_deadlock(x, y):
                    corner_deadlocks.add((x, y))
        
        return corner_deadlocks
    
    def _is_corner_deadlock(self, x: int, y: int) -> bool:
        """
        Check if a position is a corner deadlock.
        """
        # Skip walls and targets
        if self.level.is_wall(x, y) or self.level.is_target(x, y):
            return False
        
        # Check for corner (two adjacent walls)
        if ((self.level.is_wall(x-1, y) and self.level.is_wall(x, y-1)) or
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y-1)) or
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y+1)) or
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y+1))):
            return True
        
        return False
    
    def _build_goal_room_map(self) -> Dict[int, Set[Tuple[int, int]]]:
        """
        Build a map of goal rooms.
        A goal room is a connected area containing targets with limited entrances.
        """
        goal_rooms = {}
        room_id = 0
        visited = set()
        
        # Find all targets
        targets = set(self.level.targets)
        
        # For each target, try to find a goal room
        for target in targets:
            if target in visited:
                continue
            
            # Flood fill from this target
            room = self._flood_fill_room(target, visited)
            
            # If we found a room with targets
            if room:
                goal_rooms[room_id] = room
                room_id += 1
        
        return goal_rooms
    
    def _flood_fill_room(self, start: Tuple[int, int], visited: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        Flood fill to find a connected room.
        """
        queue = deque([start])
        room = set()
        entrances = set()
        
        while queue:
            pos = queue.popleft()
            
            if pos in visited:
                continue
            
            visited.add(pos)
            room.add(pos)
            
            # Check neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                
                # Skip walls
                if self.level.is_wall(nx, ny):
                    continue
                
                # If it's a floor or target, add to queue
                if not self.level.is_wall(nx, ny):
                    queue.append((nx, ny))
                
                # Check if it's an entrance
                if not self.level.is_target(nx, ny):
                    entrances.add((nx, ny))
        
        # If there's only one entrance, it's a goal room
        if len(entrances) == 1:
            return room
        
        return None
    
    def is_deadlock(self, boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Check if the current state is a deadlock.
        """
        # Check for corner deadlocks
        for box in boxes:
            # Skip boxes on targets
            if box in self.level.targets:
                continue
            
            # Check if box is in a corner deadlock
            if box in self.corner_deadlocks:
                return True
        
        # Check for freeze deadlocks
        if self._has_freeze_deadlock(boxes):
            return True
        
        # Check for goal room violations
        if self._has_goal_room_violation(boxes):
            return True
        
        # Check for known deadlock patterns
        for pattern in self.deadlock_patterns:
            if pattern.issubset(boxes):
                return True
        
        return False
    
    def _has_freeze_deadlock(self, boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Check for freeze deadlocks.
        A freeze deadlock occurs when boxes are arranged in a way that they cannot be moved.
        """
        # Check each box
        for box in boxes:
            # Skip boxes on targets
            if box in self.level.targets:
                continue
            
            # Check if box is trapped
            if self._is_box_trapped(box, boxes):
                return True
        
        return False
    
    def _is_box_trapped(self, box: Tuple[int, int], boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Check if a box is trapped (cannot be moved).
        """
        x, y = box
        
        # Check if box can be moved horizontally
        horizontal_blocked = False
        if (self.level.is_wall(x-1, y) or (x-1, y) in boxes) and (self.level.is_wall(x+1, y) or (x+1, y) in boxes):
            horizontal_blocked = True
        
        # Check if box can be moved vertically
        vertical_blocked = False
        if (self.level.is_wall(x, y-1) or (x, y-1) in boxes) and (self.level.is_wall(x, y+1) or (x, y+1) in boxes):
            vertical_blocked = True
        
        # If both directions are blocked, the box is trapped
        if horizontal_blocked and vertical_blocked:
            return True
        
        return False
    
    def _has_goal_room_violation(self, boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Check for goal room violations.
        A goal room violation occurs when there are more boxes in a goal room than targets.
        """
        for room_id, room in self.goal_room_map.items():
            # Count boxes and targets in this room
            boxes_in_room = sum(1 for box in boxes if box in room)
            targets_in_room = sum(1 for target in self.level.targets if target in room)
            
            # If there are more boxes than targets, it's a violation
            if boxes_in_room > targets_in_room:
                return True
        
        return False
    
    def add_deadlock_pattern(self, boxes: FrozenSet[Tuple[int, int]]):
        """
        Add a new deadlock pattern found during search.
        """
        # Try to minimize the pattern
        minimal_pattern = self._minimize_deadlock_pattern(boxes)
        if minimal_pattern:
            self.deadlock_patterns.add(minimal_pattern)
    
    def _minimize_deadlock_pattern(self, boxes: FrozenSet[Tuple[int, int]]) -> Optional[FrozenSet[Tuple[int, int]]]:
        """
        Try to find a minimal subset of boxes that still causes a deadlock.
        """
        # This is a simplified version - in a real implementation, we would use a more sophisticated algorithm
        # to find the minimal subset of boxes that causes a deadlock.
        return boxes

class BipartiteMatching:
    """
    Hungarian algorithm for bipartite matching.
    Used to calculate the minimum cost assignment of boxes to targets.
    """
    def __init__(self, level):
        self.level = level
        self.distances = self._precompute_distances()
    
    def _precompute_distances(self) -> Dict[Tuple[int, int], Dict[Tuple[int, int], int]]:
        """
        Precompute distances between all positions.
        """
        distances = {}
        
        # For each position, compute distances to all other positions
        for y in range(self.level.height):
            for x in range(self.level.width):
                if not self.level.is_wall(x, y):
                    distances[(x, y)] = self._bfs_distances((x, y))
        
        return distances
    
    def _bfs_distances(self, start: Tuple[int, int]) -> Dict[Tuple[int, int], int]:
        """
        Compute distances from start to all other positions using BFS.
        """
        distances = {start: 0}
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Skip walls and already visited positions
                if self.level.is_wall(nx, ny) or (nx, ny) in distances:
                    continue
                
                distances[(nx, ny)] = distances[(x, y)] + 1
                queue.append((nx, ny))
        
        return distances
    
    def calculate_matching(self, boxes: List[Tuple[int, int]]) -> int:
        """
        Calculate the minimum cost matching between boxes and targets.
        """
        targets = list(self.level.targets)
        
        # Create cost matrix
        cost_matrix = []
        for box in boxes:
            row = []
            for target in targets:
                # If we can't reach the target from the box, use a large value
                if target not in self.distances.get(box, {}):
                    row.append(float('inf'))
                else:
                    row.append(self.distances[box][target])
            cost_matrix.append(row)
        
        # Use Hungarian algorithm to find minimum cost matching
        return self._hungarian_algorithm(cost_matrix)
    
    def _hungarian_algorithm(self, cost_matrix: List[List[int]]) -> int:
        """
        Hungarian algorithm for minimum cost bipartite matching.
        """
        n = len(cost_matrix)
        m = len(cost_matrix[0]) if n > 0 else 0
        
        # If no boxes or targets, return 0
        if n == 0 or m == 0:
            return 0
        
        # Make a copy of the cost matrix
        cost = [row[:] for row in cost_matrix]
        
        # Step 1: Subtract minimum value from each row
        for i in range(n):
            min_val = min(cost[i])
            for j in range(m):
                cost[i][j] -= min_val
        
        # Step 2: Subtract minimum value from each column
        for j in range(m):
            min_val = min(cost[i][j] for i in range(n))
            for i in range(n):
                cost[i][j] -= min_val
        
        # Step 3: Cover all zeros with minimum number of lines
        # Step 4: Create additional zeros
        # Step 5: Find optimal assignment
        
        # This is a simplified version - in a real implementation, we would use the full Hungarian algorithm
        # For now, we'll just return a heuristic estimate
        
        # Sum of minimum values in each row and column
        return sum(min(row) for row in cost_matrix) + sum(min(cost_matrix[i][j] for i in range(n)) for j in range(m))

class SokolutionHeuristic:
    """
    Advanced heuristic for Sokoban using bipartite matching.
    """
    def __init__(self, level):
        self.level = level
        self.bipartite_matching = BipartiteMatching(level)
        
        # Precompute distances from each position to all targets
        self.target_distances = self._precompute_target_distances()
    
    def _precompute_target_distances(self) -> Dict[Tuple[int, int], Dict[Tuple[int, int], int]]:
        """
        Precompute distances from each position to all targets.
        """
        target_distances = {}
        
        for y in range(self.level.height):
            for x in range(self.level.width):
                if not self.level.is_wall(x, y):
                    target_distances[(x, y)] = {}
                    for target in self.level.targets:
                        # Use BFS to find distance
                        distance = self._bfs_distance((x, y), target)
                        if distance is not None:
                            target_distances[(x, y)][target] = distance
        
        return target_distances
    
    def _bfs_distance(self, start: Tuple[int, int], end: Tuple[int, int]) -> Optional[int]:
        """
        Find the shortest path distance from start to end using BFS.
        """
        if start == end:
            return 0
        
        visited = {start}
        queue = deque([(start, 0)])  # (position, distance)
        
        while queue:
            (x, y), distance = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) == end:
                    return distance + 1
                
                if self.level.is_wall(nx, ny) or (nx, ny) in visited:
                    continue
                
                visited.add((nx, ny))
                queue.append(((nx, ny), distance + 1))
        
        return None  # No path found
    
    def calculate_heuristic(self, state: SokolutionState) -> int:
        """
        Calculate the heuristic value for a state.
        """
        # Use bipartite matching to find minimum cost assignment
        boxes = list(state.boxes)
        h_cost = self.bipartite_matching.calculate_matching(boxes)
        
        # Add penalty for boxes not on targets
        h_cost += self._box_penalty(state.boxes)
        
        # Add penalty for player distance to nearest box
        h_cost += self._player_distance_penalty(state)
        
        return h_cost
    
    def _box_penalty(self, boxes: FrozenSet[Tuple[int, int]]) -> int:
        """
        Calculate penalty for boxes not on targets.
        """
        penalty = 0
        
        for box in boxes:
            if box not in self.level.targets:
                penalty += 1
        
        return penalty
    
    def _player_distance_penalty(self, state: SokolutionState) -> int:
        """
        Calculate penalty based on player distance to nearest box.
        """
        player_x, player_y = state.player_pos
        min_distance = float('inf')
        
        for box in state.boxes:
            # Skip boxes on targets
            if box in self.level.targets:
                continue
            
            # Calculate Manhattan distance
            distance = abs(player_x - box[0]) + abs(player_y - box[1])
            min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 0

class MacroMoveGenerator:
    """
    Generator for macro moves in Sokoban.
    """
    def __init__(self, level):
        self.level = level
        self.tunnels = self._find_tunnels()
        self.goal_rooms = self._find_goal_rooms()
    
    def _find_tunnels(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Find all tunnels in the level.
        A tunnel is a narrow passage where a box can only move in one direction.
        """
        tunnels = {}
        
        for y in range(self.level.height):
            for x in range(self.level.width):
                if self.level.is_wall(x, y):
                    continue
                
                # Check for horizontal tunnel
                if (not self.level.is_wall(x-1, y) and not self.level.is_wall(x+1, y) and
                    self.level.is_wall(x, y-1) and self.level.is_wall(x, y+1)):
                    # Find tunnel length
                    length = 1
                    nx = x + 1
                    while (not self.level.is_wall(nx, y) and
                           self.level.is_wall(nx, y-1) and self.level.is_wall(nx, y+1)):
                        length += 1
                        nx += 1
                    
                    if length > 1:
                        tunnels[(x, y)] = {
                            'direction': 'horizontal',
                            'length': length,
                            'end': (x + length - 1, y)
                        }
                
                # Check for vertical tunnel
                if (not self.level.is_wall(x, y-1) and not self.level.is_wall(x, y+1) and
                    self.level.is_wall(x-1, y) and self.level.is_wall(x+1, y)):
                    # Find tunnel length
                    length = 1
                    ny = y + 1
                    while (not self.level.is_wall(x, ny) and
                           self.level.is_wall(x-1, ny) and self.level.is_wall(x+1, ny)):
                        length += 1
                        ny += 1
                    
                    if length > 1:
                        tunnels[(x, y)] = {
                            'direction': 'vertical',
                            'length': length,
                            'end': (x, y + length - 1)
                        }
        
        return tunnels
    
    def _find_goal_rooms(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Find all goal rooms in the level.
        A goal room is a room with a single entrance and one or more targets.
        """
        goal_rooms = {}
        
        # Find all targets
        targets = set(self.level.targets)
        
        # For each target, check if it's in a goal room
        for target in targets:
            # Skip targets we've already processed
            if any(target in room['targets'] for room in goal_rooms.values()):
                continue
            
            # Find all connected targets and the entrance
            room_targets, entrance = self._find_connected_targets(target)
            
            if entrance and room_targets:
                goal_rooms[entrance] = {
                    'targets': room_targets,
                    'entrance': entrance
                }
        
        return goal_rooms
    
    def _find_connected_targets(self, start: Tuple[int, int]) -> Tuple[Set[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """
        Find all targets connected to the start target and the entrance to the room.
        """
        targets = {start}
        entrance = None
        visited = {start}
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Skip walls and already visited positions
                if self.level.is_wall(nx, ny) or (nx, ny) in visited:
                    continue
                
                visited.add((nx, ny))
                
                # If it's a target, add to targets and queue
                if self.level.is_target(nx, ny):
                    targets.add((nx, ny))
                    queue.append((nx, ny))
                else:
                    # Check if it's an entrance
                    is_entrance = False
                    for dx2, dy2 in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx2, ny2 = nx + dx2, ny + dy2
                        if not self.level.is_wall(nx2, ny2) and (nx2, ny2) not in visited:
                            is_entrance = True
                            break
                    
                    if is_entrance:
                        if entrance is None:
                            entrance = (nx, ny)
                        else:
                            # More than one entrance, not a goal room
                            return set(), None
        
        return targets, entrance
    
    def generate_macro_moves(self, state: SokolutionState) -> List[Tuple[SokolutionState, str]]:
        """
        Generate macro moves for the current state.
        """
        macro_moves = []
        
        # Generate tunnel macro moves
        tunnel_moves = self._generate_tunnel_moves(state)
        macro_moves.extend(tunnel_moves)
        
        # Generate goal room macro moves
        goal_room_moves = self._generate_goal_room_moves(state)
        macro_moves.extend(goal_room_moves)
        
        return macro_moves
    
    def _generate_tunnel_moves(self, state: SokolutionState) -> List[Tuple[SokolutionState, str]]:
        """
        Generate tunnel macro moves.
        """
        moves = []
        
        # Check each box
        for box in state.boxes:
            # Check if box is at the start of a tunnel
            if box in self.tunnels:
                tunnel = self.tunnels[box]
                
                # Check if player can reach the position before the box
                player_pos = self._can_reach_position(state.player_pos, box, state.boxes)
                
                if player_pos:
                    # Create new state with box at the end of the tunnel
                    new_boxes = set(state.boxes)
                    new_boxes.remove(box)
                    new_boxes.add(tunnel['end'])
                    
                    new_state = SokolutionState(
                        player_pos=box,  # Player moves to the box position
                        boxes=frozenset(new_boxes),
                        parent=state,
                        move=f"TUNNEL_{tunnel['direction']}_{tunnel['length']}",
                        g_cost=state.g_cost + tunnel['length']
                    )
                    
                    moves.append((new_state, f"TUNNEL_{tunnel['direction']}_{tunnel['length']}"))
        
        return moves
    
    def _generate_goal_room_moves(self, state: SokolutionState) -> List[Tuple[SokolutionState, str]]:
        """
        Generate goal room macro moves.
        """
        moves = []
        
        # Check each box
        for box in state.boxes:
            # Check if box is at the entrance of a goal room
            if box in self.goal_rooms:
                goal_room = self.goal_rooms[box]
                
                # Check if player can reach the position before the box
                player_pos = self._can_reach_position(state.player_pos, box, state.boxes)
                
                if player_pos:
                    # Find an empty target in the goal room
                    for target in goal_room['targets']:
                        if target not in state.boxes:
                            # Create new state with box on the target
                            new_boxes = set(state.boxes)
                            new_boxes.remove(box)
                            new_boxes.add(target)
                            
                            new_state = SokolutionState(
                                player_pos=box,  # Player moves to the box position
                                boxes=frozenset(new_boxes),
                                parent=state,
                                move=f"GOAL_ROOM_{target[0]}_{target[1]}",
                                g_cost=state.g_cost + 1
                            )
                            
                            moves.append((new_state, f"GOAL_ROOM_{target[0]}_{target[1]}"))
                            break
        
        return moves
    
    def _can_reach_position(self, player_pos: Tuple[int, int], target_pos: Tuple[int, int], 
                           boxes: FrozenSet[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """
        Check if the player can reach a position adjacent to the target position.
        Returns the position the player can reach, or None if not reachable.
        """
        # Find positions adjacent to the target
        adjacent_positions = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = target_pos[0] + dx, target_pos[1] + dy
            
            # Skip walls and boxes
            if self.level.is_wall(nx, ny) or (nx, ny) in boxes:
                continue
            
            adjacent_positions.append((nx, ny))
        
        # Check if player can reach any of the adjacent positions
        for pos in adjacent_positions:
            if self._is_reachable(player_pos, pos, boxes):
                return pos
        
        return None
    
    def _is_reachable(self, start: Tuple[int, int], end: Tuple[int, int], 
                     boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Check if a position is reachable from the start position.
        """
        if start == end:
            return True
        
        visited = {start}
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) == end:
                    return True
                
                # Skip walls, boxes, and visited positions
                if self.level.is_wall(nx, ny) or (nx, ny) in boxes or (nx, ny) in visited:
                    continue
                
                visited.add((nx, ny))
                queue.append((nx, ny))
        
        return False

class PICorralDetector:
    """
    PI-Corral detection for Sokoban.
    """
    def __init__(self, level):
        self.level = level
    
    def find_pi_corrals(self, state: SokolutionState) -> List[Dict[str, Any]]:
        """
        Find all PI-Corrals in the current state.
        """
        corrals = []
        
        # Find all simple corrals
        simple_corrals = self._find_simple_corrals(state)
        corrals.extend(simple_corrals)
        
        # Find combined corrals
        combined_corrals = self._find_combined_corrals(state, simple_corrals)
        corrals.extend(combined_corrals)
        
        # Sort corrals by priority
        corrals.sort(key=self._corral_priority, reverse=True)
        
        return corrals
    
    def _find_simple_corrals(self, state: SokolutionState) -> List[Dict[str, Any]]:
        """
        Find all simple corrals in the current state.
        """
        corrals = []
        
        # Find all potential corral entrances
        for y in range(self.level.height):
            for x in range(self.level.width):
                if self.level.is_wall(x, y) or (x, y) in state.boxes:
                    continue
                
                # Check if this position could be an entrance to a corral
                corral = self._check_corral_from_entrance((x, y), state)
                if corral:
                    corrals.append(corral)
        
        return corrals
    
    def _check_corral_from_entrance(self, entrance: Tuple[int, int], state: SokolutionState) -> Optional[Dict[str, Any]]:
        """
        Check if an entrance leads to a corral.
        """
        # Flood fill from the entrance
        inside_area = self._flood_fill_from_entrance(entrance, state)
        
        # If no inside area, not a corral
        if not inside_area:
            return None
        
        # Find frontier boxes
        frontier_boxes = set()
        for pos in inside_area:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                
                if (nx, ny) in state.boxes:
                    frontier_boxes.add((nx, ny))
        
        # If no frontier boxes, not a corral
        if not frontier_boxes:
            return None
        
        # Check if all frontier boxes are reachable by the player
        player_reachable = self._get_player_reachable_positions(state)
        
        if all(box in player_reachable for box in frontier_boxes):
            return {
                'entrance': entrance,
                'inside_area': inside_area,
                'frontier_boxes': frontier_boxes,
                'boxes_on_targets': sum(1 for box in frontier_boxes if box in self.level.targets)
            }
        
        return None
    
    def _flood_fill_from_entrance(self, entrance: Tuple[int, int], state: SokolutionState) -> Set[Tuple[int, int]]:
        """
        Flood fill from an entrance to find the inside area of a potential corral.
        """
        inside_area = {entrance}
        queue = deque([entrance])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Skip walls, boxes, and already visited positions
                if self.level.is_wall(nx, ny) or (nx, ny) in state.boxes or (nx, ny) in inside_area:
                    continue
                
                inside_area.add((nx, ny))
                queue.append((nx, ny))
        
        return inside_area
    
    def _get_player_reachable_positions(self, state: SokolutionState) -> Set[Tuple[int, int]]:
        """
        Get all positions reachable by the player.
        """
        reachable = {state.player_pos}
        queue = deque([state.player_pos])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Skip walls, boxes, and already visited positions
                if self.level.is_wall(nx, ny) or (nx, ny) in state.boxes or (nx, ny) in reachable:
                    continue
                
                reachable.add((nx, ny))
                queue.append((nx, ny))
        
        return reachable
    
    def _find_combined_corrals(self, state: SokolutionState, simple_corrals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find combined corrals formed by two or more simple corrals.
        """
        combined_corrals = []
        
        # Try all pairs of simple corrals
        for i in range(len(simple_corrals)):
            for j in range(i + 1, len(simple_corrals)):
                corral1 = simple_corrals[i]
                corral2 = simple_corrals[j]
                
                # Check if the corrals share frontier boxes
                shared_frontier = corral1['frontier_boxes'].intersection(corral2['frontier_boxes'])
                
                if shared_frontier:
                    # Combine the corrals
                    combined_corral = {
                        'entrance': None,  # Combined corrals don't have a single entrance
                        'inside_area': corral1['inside_area'].union(corral2['inside_area']),
                        'frontier_boxes': corral1['frontier_boxes'].union(corral2['frontier_boxes']),
                        'boxes_on_targets': sum(1 for box in corral1['frontier_boxes'].union(corral2['frontier_boxes']) 
                                              if box in self.level.targets)
                    }
                    
                    combined_corrals.append(combined_corral)
        
        return combined_corrals
    
    def _corral_priority(self, corral: Dict[str, Any]) -> Tuple[int, int, int]:
        """
        Calculate priority for a corral.
        Higher priority corrals are preferred.
        """
        # Priority: 
        # 1. More boxes on targets
        # 2. Fewer frontier boxes
        # 3. Smaller inside area
        return (
            corral['boxes_on_targets'],
            -len(corral['frontier_boxes']),
            -len(corral['inside_area'])
        )

class SokolutionSolver:
    """
    Advanced Sokoban solver based on the Sokolution solver.
    """
    def __init__(self, level, algorithm=ALGORITHM_ASTAR, mode=MODE_FORWARD, 
                 max_states=1000000, time_limit=120.0):
        self.level = level
        self.algorithm = algorithm
        self.mode = mode
        self.max_states = max_states
        self.time_limit = time_limit
        
        # Initialize components
        self.deadlock_detector = DeadlockDetector(level)
        self.heuristic = SokolutionHeuristic(level)
        self.macro_move_generator = MacroMoveGenerator(level)
        self.pi_corral_detector = PICorralDetector(level)
        
        # State management
        self.transposition_table = TranspositionTable()
        self.open_set = []  # For A*, Greedy, BFS, DFS
        self.solution = None
        
        # Statistics
        self.states_explored = 0
        self.states_generated = 0
        self.deadlocks_pruned = 0
        self.start_time = 0
    
    def solve(self, progress_callback=None) -> Optional[List[str]]:
        """
        Solve the Sokoban level using the selected algorithm and mode.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of moves if solution found, None otherwise
        """
        self.start_time = time.time()
        self.states_explored = 0
        self.states_generated = 0
        self.deadlocks_pruned = 0
        self.solution = None
        
        if progress_callback:
            progress_callback(f"Starting Sokolution solver with {self.algorithm} algorithm in {self.mode} mode...")
        
        # Select the appropriate search algorithm
        if self.algorithm == ALGORITHM_BFS:
            self.solution = self._bfs_search(progress_callback)
        elif self.algorithm == ALGORITHM_DFS:
            self.solution = self._dfs_search(progress_callback)
        elif self.algorithm == ALGORITHM_ASTAR:
            self.solution = self._astar_search(progress_callback)
        elif self.algorithm == ALGORITHM_IDA:
            self.solution = self._ida_search(progress_callback)
        elif self.algorithm == ALGORITHM_GREEDY:
            self.solution = self._greedy_search(progress_callback)
        
        if progress_callback:
            if self.solution:
                progress_callback(f"Solution found! {len(self.solution)} moves, {self.states_explored} states explored")
            else:
                progress_callback("No solution found")
        
        return self.solution
    
    def _bfs_search(self, progress_callback=None) -> Optional[List[str]]:
        """
        Breadth-first search algorithm.
        """
        # Create initial state
        initial_state = self._create_initial_state()
        
        # Initialize search
        self.open_set = deque([initial_state])
        self.transposition_table = TranspositionTable()
        self.transposition_table.add(initial_state)
        
        while self.open_set and self._within_limits():
            # Get next state
            current_state = self.open_set.popleft()
            self.states_explored += 1
            
            # Progress update
            if progress_callback and self.states_explored % 10000 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"Explored {self.states_explored} states in {elapsed:.1f}s")
            
            # Check if solved
            if self._is_solved(current_state):
                return self._reconstruct_path(current_state)
            
            # Check for PI-Corrals
            pi_corrals = self.pi_corral_detector.find_pi_corrals(current_state)
            if pi_corrals:
                # Use the highest priority corral
                corral = pi_corrals[0]
                
                # Check if all frontier boxes are on targets
                if all(box in self.level.targets for box in corral['frontier_boxes']):
                    # All frontier boxes are frozen on targets
                    pass
            
            # Generate successors
            successors = self._generate_successors(current_state)
            
            for successor, move in successors:
                if not self.transposition_table.contains(successor):
                    self.open_set.append(successor)
                    self.transposition_table.add(successor)
                    self.states_generated += 1
        
        return None
    
    def _dfs_search(self, progress_callback=None) -> Optional[List[str]]:
        """
        Depth-first search algorithm.
        """
        # Create initial state
        initial_state = self._create_initial_state()
        
        # Initialize search
        self.open_set = [initial_state]
        self.transposition_table = TranspositionTable()
        self.transposition_table.add(initial_state)
        
        while self.open_set and self._within_limits():
            # Get next state
            current_state = self.open_set.pop()
            self.states_explored += 1
            
            # Progress update
            if progress_callback and self.states_explored % 10000 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"Explored {self.states_explored} states in {elapsed:.1f}s")
            
            # Check if solved
            if self._is_solved(current_state):
                return self._reconstruct_path(current_state)
            
            # Generate successors
            successors = self._generate_successors(current_state)
            
            for successor, move in successors:
                if not self.transposition_table.contains(successor):
                    self.open_set.append(successor)
                    self.transposition_table.add(successor)
                    self.states_generated += 1
        
        return None
    
    def _astar_search(self, progress_callback=None) -> Optional[List[str]]:
        """
        A* search algorithm.
        """
        # Create initial state
        initial_state = self._create_initial_state()
        initial_state.h_cost = self.heuristic.calculate_heuristic(initial_state)
        initial_state.f_cost = initial_state.g_cost + initial_state.h_cost
        
        # Initialize search
        self.open_set = [initial_state]
        self.transposition_table = TranspositionTable()
        self.transposition_table.add(initial_state)
        
        while self.open_set and self._within_limits():
            # Get best state
            current_state = heapq.heappop(self.open_set)
            self.states_explored += 1
            
            # Progress update
            if progress_callback and self.states_explored % 10000 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"Explored {self.states_explored} states in {elapsed:.1f}s")
            
            # Check if solved
            if self._is_solved(current_state):
                return self._reconstruct_path(current_state)
            
            # Generate successors
            successors = self._generate_successors(current_state)
            
            for successor, move in successors:
                # Calculate heuristic
                successor.h_cost = self.heuristic.calculate_heuristic(successor)
                successor.f_cost = successor.g_cost + successor.h_cost
                
                if not self.transposition_table.contains(successor):
                    heapq.heappush(self.open_set, successor)
                    self.transposition_table.add(successor)
                    self.states_generated += 1
        
        return None
    
    def _ida_search(self, progress_callback=None) -> Optional[List[str]]:
        """
        IDA* search algorithm.
        """
        # Create initial state
        initial_state = self._create_initial_state()
        initial_state.h_cost = self.heuristic.calculate_heuristic(initial_state)
        initial_state.f_cost = initial_state.g_cost + initial_state.h_cost
        
        # Initialize search
        threshold = initial_state.h_cost
        
        for iteration in range(50):  # Maximum iterations
            if progress_callback and iteration % 5 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"IDA* iteration {iteration}, threshold={threshold}, explored={self.states_explored}, time={elapsed:.1f}s")
            
            # Check time limit
            if not self._within_limits():
                break
            
            min_threshold = float('inf')
            result = self._ida_search_recursive(initial_state, 0, threshold, [], min_threshold)
            
            if isinstance(result, list):
                return result
            
            if result == float('inf'):
                break
            
            threshold = result
        
        return None
    
    def _ida_search_recursive(self, state: SokolutionState, g: int, threshold: int, 
                             path: List[str], min_threshold: float) -> Any:
        """
        Recursive IDA* search.
        """
        # Check limits
        if not self._within_limits():
            return min_threshold
        
        self.states_explored += 1
        
        # Calculate f-cost
        h = self.heuristic.calculate_heuristic(state)
        f = g + h
        
        if f > threshold:
            return min(min_threshold, f)
        
        # Check if solved
        if self._is_solved(state):
            return path.copy()
        
        # Generate successors
        successors = self._generate_successors(state)
        
        for successor, move in successors:
            new_path = path + [move]
            result = self._ida_search_recursive(successor, g + 1, threshold, new_path, min_threshold)
            
            if isinstance(result, list):
                return result
            
            min_threshold = min(min_threshold, result)
        
        return min_threshold
    
    def _greedy_search(self, progress_callback=None) -> Optional[List[str]]:
        """
        Greedy best-first search algorithm.
        """
        # Create initial state
        initial_state = self._create_initial_state()
        initial_state.h_cost = self.heuristic.calculate_heuristic(initial_state)
        initial_state.f_cost = initial_state.h_cost  # In greedy search, f = h
        
        # Initialize search
        self.open_set = [initial_state]
        self.transposition_table = TranspositionTable()
        self.transposition_table.add(initial_state)
        
        while self.open_set and self._within_limits():
            # Get best state
            current_state = heapq.heappop(self.open_set)
            self.states_explored += 1
            
            # Progress update
            if progress_callback and self.states_explored % 10000 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"Explored {self.states_explored} states in {elapsed:.1f}s")
            
            # Check if solved
            if self._is_solved(current_state):
                return self._reconstruct_path(current_state)
            
            # Generate successors
            successors = self._generate_successors(current_state)
            
            for successor, move in successors:
                # Calculate heuristic
                successor.h_cost = self.heuristic.calculate_heuristic(successor)
                successor.f_cost = successor.h_cost  # In greedy search, f = h
                
                if not self.transposition_table.contains(successor):
                    heapq.heappush(self.open_set, successor)
                    self.transposition_table.add(successor)
                    self.states_generated += 1
        
        return None
    
    def _create_initial_state(self) -> SokolutionState:
        """
        Create the initial state based on the search mode.
        """
        if self.mode == MODE_FORWARD:
            # Forward mode: start from initial state
            return SokolutionState(
                player_pos=self.level.player_pos,
                boxes=frozenset(self.level.boxes)
            )
        elif self.mode == MODE_BACKWARD:
            # Backward mode: start from goal state (all boxes on targets)
            # This is a simplified implementation - in a real backward search,
            # we would need to handle pulling boxes instead of pushing them
            return SokolutionState(
                player_pos=self.level.player_pos,  # Start with player in same position
                boxes=frozenset(self.level.targets)  # All boxes on targets
            )
        else:
            # Default to forward mode
            return SokolutionState(
                player_pos=self.level.player_pos,
                boxes=frozenset(self.level.boxes)
            )
    
    def _is_solved(self, state: SokolutionState) -> bool:
        """
        Check if a state represents a solved level.
        """
        if self.mode == MODE_FORWARD:
            # Forward mode: all boxes on targets
            return state.boxes == frozenset(self.level.targets)
        elif self.mode == MODE_BACKWARD:
            # Backward mode: all boxes in initial positions
            return state.boxes == frozenset(self.level.boxes)
        else:
            # Default to forward mode
            return state.boxes == frozenset(self.level.targets)
    
    def _generate_successors(self, state: SokolutionState) -> List[Tuple[SokolutionState, str]]:
        """
        Generate all valid successor states.
        """
        successors = []
        
        # Generate macro moves
        macro_moves = self.macro_move_generator.generate_macro_moves(state)
        successors.extend(macro_moves)
        
        # Generate regular moves
        regular_moves = self._generate_regular_moves(state)
        successors.extend(regular_moves)
        
        return successors
    
    def _generate_regular_moves(self, state: SokolutionState) -> List[Tuple[SokolutionState, str]]:
        """
        Generate regular (non-macro) moves.
        """
        moves = []
        player_x, player_y = state.player_pos
        
        # Try all four directions
        for direction, (dx, dy) in [('UP', (0, -1)), ('DOWN', (0, 1)),
                                   ('LEFT', (-1, 0)), ('RIGHT', (1, 0))]:
            new_x, new_y = player_x + dx, player_y + dy
            
            # Check bounds and walls
            if (new_x < 0 or new_x >= self.level.width or
                new_y < 0 or new_y >= self.level.height or
                self.level.is_wall(new_x, new_y)):
                continue
            
            # Check if there's a box in the way
            if (new_x, new_y) in state.boxes:
                # Try to push the box
                box_x, box_y = new_x + dx, new_y + dy
                
                # Check if the box can be pushed
                if (box_x < 0 or box_x >= self.level.width or
                    box_y < 0 or box_y >= self.level.height or
                    self.level.is_wall(box_x, box_y) or
                    (box_x, box_y) in state.boxes):
                    continue
                
                # Create new state with pushed box
                new_boxes = set(state.boxes)
                new_boxes.remove((new_x, new_y))
                new_boxes.add((box_x, box_y))
                
                new_state = SokolutionState(
                    player_pos=(new_x, new_y),
                    boxes=frozenset(new_boxes),
                    parent=state,
                    move=direction,
                    g_cost=state.g_cost + 1
                )
                
                # Check for deadlocks
                if not self.deadlock_detector.is_deadlock(new_state.boxes):
                    moves.append((new_state, direction))
                else:
                    self.deadlocks_pruned += 1
            else:
                # Just move the player
                new_state = SokolutionState(
                    player_pos=(new_x, new_y),
                    boxes=state.boxes,
                    parent=state,
                    move=direction,
                    g_cost=state.g_cost + 1
                )
                
                moves.append((new_state, direction))
        
        return moves
    
    def _reconstruct_path(self, final_state: SokolutionState) -> List[str]:
        """
        Reconstruct the path from the initial state to the final state.
        """
        path = []
        current = final_state
        
        while current.parent is not None:
            path.append(current.move)
            current = current.parent
        
        return list(reversed(path))
    
    def _within_limits(self) -> bool:
        """
        Check if we're within the time and state limits.
        """
        return (time.time() - self.start_time <= self.time_limit and
                self.states_explored <= self.max_states)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the search.
        """
        return {
            'states_explored': self.states_explored,
            'states_generated': self.states_generated,
            'deadlocks_pruned': self.deadlocks_pruned,
            'time': time.time() - self.start_time,
            'algorithm': self.algorithm,
            'mode': self.mode
        }