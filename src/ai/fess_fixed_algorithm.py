"""
Version corrigée de l'algorithme FESS pour résoudre les problèmes critiques identifiés.

Corrections principales :
1. Macro moves réalistes et faisables
2. Vérification correcte des chemins de poussée
3. Mise à jour correcte de la position du joueur
4. Détection basique de deadlocks
5. Génération optimisée de macro moves
"""

from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import heapq
import copy
import time
from collections import defaultdict, deque

from .fess_notation import FESSSolutionNotation, MacroMove, MacroMoveType

class FeatureType(Enum):
    """The four FESS features for Sokoban."""
    PACKING = "packing"
    CONNECTIVITY = "connectivity"
    ROOM_CONNECTIVITY = "room_connectivity"
    OUT_OF_PLAN = "out_of_plan"

@dataclass
class FeatureVector:
    """Represents a point in the 4-dimensional feature space."""
    packing: int = 0
    connectivity: int = 0
    room_connectivity: int = 0
    out_of_plan: int = 0
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Convert to tuple for hashing and comparison."""
        return (self.packing, self.connectivity, self.room_connectivity, self.out_of_plan)
    
    def __hash__(self):
        return hash(self.to_tuple())
    
    def __eq__(self, other):
        return isinstance(other, FeatureVector) and self.to_tuple() == other.to_tuple()

@dataclass
class MacroMoveAction:
    """Represents a feasible macro move with complete path information."""
    box_start: Tuple[int, int]
    box_end: Tuple[int, int]
    player_path: List[Tuple[int, int]] = field(default_factory=list)
    push_path: List[Tuple[int, int]] = field(default_factory=list)  # Path of box during push
    final_player_pos: Tuple[int, int] = None
    weight: float = 1.0
    pushes: int = 1
    
    def __post_init__(self):
        if self.final_player_pos is None:
            self.final_player_pos = self.box_start  # Default fallback
    
    def __str__(self):
        return f"Move box {self.box_start} → {self.box_end} (pushes: {self.pushes}, weight: {self.weight:.1f})"

@dataclass
class FESSNode:
    """Represents a node in the FESS search tree."""
    state: 'SokobanState'
    feature_vector: FeatureVector
    parent: Optional['FESSNode'] = None
    action: Optional[MacroMoveAction] = None
    accumulated_weight: float = 0.0
    depth: int = 0
    
    def __lt__(self, other):
        return self.accumulated_weight < other.accumulated_weight

class SokobanState:
    """Represents a Sokoban game state for FESS algorithm."""
    
    def __init__(self, level):
        """Initialize from a Sokoban level."""
        self.width = level.width
        self.height = level.height
        self.walls = set()
        self.targets = set(level.targets)
        self.boxes = set(level.boxes)
        self.player_pos = level.player_pos
        
        # Extract walls from level map
        for y in range(level.height):
            for x in range(level.width):
                if level.is_wall(x, y):
                    self.walls.add((x, y))
    
    def copy(self):
        """Create a deep copy of the state."""
        new_state = SokobanState.__new__(SokobanState)
        new_state.width = self.width
        new_state.height = self.height
        new_state.walls = self.walls.copy()
        new_state.targets = self.targets.copy()
        new_state.boxes = self.boxes.copy()
        new_state.player_pos = self.player_pos
        return new_state
    
    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is valid (not wall, within bounds)."""
        x, y = pos
        return (0 <= x < self.width and 0 <= y < self.height and 
                pos not in self.walls)
    
    def is_completed(self) -> bool:
        """Check if all boxes are on targets."""
        return self.boxes == self.targets
    
    def get_reachable_positions(self, start_pos: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """Get all positions reachable by the player from start_pos without pushing boxes."""
        reachable = set()
        queue = deque([start_pos])
        visited = {start_pos}
        
        while queue:
            pos = queue.popleft()
            reachable.add(pos)
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (pos[0] + dx, pos[1] + dy)
                if (new_pos not in visited and 
                    self.is_valid_position(new_pos) and 
                    new_pos not in self.boxes):
                    visited.add(new_pos)
                    queue.append(new_pos)
        
        return reachable
    
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Find shortest path from start to end using BFS."""
        if start == end:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            pos, path = queue.popleft()
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (pos[0] + dx, pos[1] + dy)
                
                if (new_pos not in visited and 
                    self.is_valid_position(new_pos) and 
                    new_pos not in self.boxes):
                    
                    new_path = path + [new_pos]
                    if new_pos == end:
                        return new_path
                    
                    visited.add(new_pos)
                    queue.append((new_pos, new_path))
        
        return []  # No path found
    
    def is_deadlock(self) -> bool:
        """Basic deadlock detection."""
        # Simple corner deadlock detection
        for box in self.boxes:
            if box not in self.targets:
                x, y = box
                # Check for corner deadlocks
                walls_adjacent = 0
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    adj_pos = (x + dx, y + dy)
                    if adj_pos in self.walls:
                        walls_adjacent += 1
                
                # Box in corner (2+ walls) and not on target = deadlock
                if walls_adjacent >= 2:
                    return True
        
        return False

class FESSFeatureCalculator:
    """Calculates the four FESS features for Sokoban states."""
    
    def __init__(self, initial_state: SokobanState):
        """Initialize with the initial state to set up analysis structures."""
        self.initial_state = initial_state
        self.target_order = self._calculate_target_order()
    
    def _calculate_target_order(self) -> List[Tuple[int, int]]:
        """
        Calculate optimal target order - simplified version.
        In practice, this would use retrograde analysis.
        """
        # For now, order targets from bottom-right to top-left
        targets = list(self.initial_state.targets)
        targets.sort(key=lambda t: (t[1], t[0]), reverse=True)
        return targets
    
    def calculate_features(self, state: SokobanState) -> FeatureVector:
        """Calculate all four FESS features for the given state."""
        return FeatureVector(
            packing=self._calculate_packing_feature(state),
            connectivity=self._calculate_connectivity_feature(state),
            room_connectivity=self._calculate_room_connectivity_feature(state),
            out_of_plan=self._calculate_out_of_plan_feature(state)
        )
    
    def _calculate_packing_feature(self, state: SokobanState) -> int:
        """Number of boxes on targets."""
        return len(state.boxes & state.targets)
    
    def _calculate_connectivity_feature(self, state: SokobanState) -> int:
        """Number of disconnected regions."""
        # Find all free positions
        free_positions = set()
        for x in range(state.width):
            for y in range(state.height):
                pos = (x, y)
                if state.is_valid_position(pos) and pos not in state.boxes:
                    free_positions.add(pos)
        
        # Count connected components
        visited = set()
        components = 0
        
        for pos in free_positions:
            if pos not in visited:
                components += 1
                # DFS to mark component
                stack = [pos]
                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        neighbor = (current[0] + dx, current[1] + dy)
                        if neighbor in free_positions and neighbor not in visited:
                            stack.append(neighbor)
        
        return components
    
    def _calculate_room_connectivity_feature(self, state: SokobanState) -> int:
        """Number of obstructed passages - simplified."""
        obstructed = 0
        for box in state.boxes:
            x, y = box
            # Check if box blocks a narrow passage
            if ((x-1, y) in state.walls and (x+1, y) in state.walls) or \
               ((x, y-1) in state.walls and (x, y+1) in state.walls):
                obstructed += 1
        return obstructed
    
    def _calculate_out_of_plan_feature(self, state: SokobanState) -> int:
        """Number of boxes with limited mobility."""
        out_of_plan = 0
        for box in state.boxes:
            if box not in state.targets:
                # Count escape routes
                escape_routes = 0
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    adj_pos = (box[0] + dx, box[1] + dy)
                    if state.is_valid_position(adj_pos) and adj_pos not in state.boxes:
                        escape_routes += 1
                
                if escape_routes <= 1:
                    out_of_plan += 1
        
        return out_of_plan

class FESSMacroMoveGenerator:
    """Generates feasible macro moves for FESS algorithm."""
    
    def __init__(self, state: SokobanState):
        self.state = state
    
    def generate_feasible_macro_moves(self) -> List[MacroMoveAction]:
        """Generate all feasible macro moves from current state."""
        moves = []
        reachable = self.state.get_reachable_positions(self.state.player_pos)
        
        for box_pos in self.state.boxes:
            # Find all adjacent positions to the box where player can stand
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                push_from = (box_pos[0] - dx, box_pos[1] - dy)
                push_to = (box_pos[0] + dx, box_pos[1] + dy)
                
                # Check if player can reach push position
                if push_from not in reachable:
                    continue
                
                # Check if push destination is valid
                if not self.state.is_valid_position(push_to) or push_to in self.state.boxes:
                    continue
                
                # Generate macro move for this single push
                player_path = self.state.find_path(self.state.player_pos, push_from)
                if player_path:
                    move = MacroMoveAction(
                        box_start=box_pos,
                        box_end=push_to,
                        player_path=player_path,
                        push_path=[box_pos, push_to],
                        final_player_pos=box_pos,  # Player ends up where box was
                        pushes=1,
                        weight=1.0
                    )
                    moves.append(move)
                
                # Also try multi-push sequences (limited to avoid explosion)
                self._generate_multi_push_sequences(box_pos, push_to, moves, max_pushes=3)
        
        return moves
    
    def _generate_multi_push_sequences(self, start_pos: Tuple[int, int], 
                                     first_push_to: Tuple[int, int], 
                                     moves: List[MacroMoveAction], 
                                     max_pushes: int = 3):
        """Generate multi-push macro moves (limited depth)."""
        if max_pushes <= 1:
            return
        
        # Create temporary state with box moved
        temp_state = self.state.copy()
        temp_state.boxes.remove(start_pos)
        temp_state.boxes.add(first_push_to)
        temp_state.player_pos = start_pos
        
        # Try continuing pushes from new position
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_push_to = (first_push_to[0] + dx, first_push_to[1] + dy)
            push_from = (first_push_to[0] - dx, first_push_to[1] - dy)
            
            if (temp_state.is_valid_position(next_push_to) and 
                next_push_to not in temp_state.boxes and
                push_from == start_pos):  # Player can push from original box position
                
                move = MacroMoveAction(
                    box_start=start_pos,
                    box_end=next_push_to,
                    push_path=[start_pos, first_push_to, next_push_to],
                    final_player_pos=first_push_to,
                    pushes=2,
                    weight=1.0
                )
                moves.append(move)

class FESSAdvisor:
    """Implements FESS advisors to recommend promising moves."""
    
    def __init__(self, feature_calculator: FESSFeatureCalculator):
        self.feature_calculator = feature_calculator
    
    def get_advisor_moves(self, state: SokobanState, current_features: FeatureVector) -> List[MacroMoveAction]:
        """Get moves recommended by all advisors."""
        generator = FESSMacroMoveGenerator(state)
        all_moves = generator.generate_feasible_macro_moves()
        
        advisor_moves = []
        
        # Packing advisor: moves that put boxes on targets
        for move in all_moves:
            if move.box_end in state.targets:
                move.weight = 0.0  # Highest priority
                advisor_moves.append(move)
        
        # Connectivity advisor: moves that improve connectivity
        for move in all_moves:
            if move not in advisor_moves:
                test_state = state.copy()
                test_state.boxes.remove(move.box_start)
                test_state.boxes.add(move.box_end)
                
                new_connectivity = self.feature_calculator._calculate_connectivity_feature(test_state)
                if new_connectivity < current_features.connectivity:
                    move.weight = 0.0
                    advisor_moves.append(move)
        
        return advisor_moves[:7]  # Limit as per paper

class FESSFixedAlgorithm:
    """
    Version corrigée de l'algorithme FESS qui génère des macro moves réalistes.
    """
    
    def __init__(self, level, max_time: float = 600.0):
        """Initialize FESS algorithm."""
        self.level = level
        self.initial_state = SokobanState(level)
        self.feature_calculator = FESSFeatureCalculator(self.initial_state)
        self.advisor = FESSAdvisor(self.feature_calculator)
        self.max_time = max_time
        
        # FESS data structures
        self.feature_space: Dict[FeatureVector, List[FESSNode]] = {}
        self.search_tree: Dict[Tuple, FESSNode] = {}
        self.unexpanded_moves: Dict[Tuple, List[MacroMoveAction]] = {}
        
        # Statistics
        self.nodes_expanded = 0
        self.start_time = 0.0
    
    def solve(self) -> Tuple[bool, List[MacroMoveAction], Dict[str, Any]]:
        """Solve using corrected FESS algorithm."""
        self.start_time = time.time()
        
        # Initialize
        self.feature_space = {}
        root_state = self.initial_state
        initial_features = self.feature_calculator.calculate_features(root_state)
        
        root_node = FESSNode(
            state=root_state,
            feature_vector=initial_features,
            accumulated_weight=0.0,
            depth=0
        )
        
        state_hash = self._state_to_hash(root_state)
        self.search_tree[state_hash] = root_node
        
        if initial_features not in self.feature_space:
            self.feature_space[initial_features] = []
        self.feature_space[initial_features].append(root_node)
        
        self._assign_weights_to_moves(root_node)
        
        # Search loop
        while time.time() - self.start_time < self.max_time:
            # Check for solution
            solution_node = self._check_for_solution()
            if solution_node:
                return self._extract_solution(solution_node)
            
            # Pick next cell
            current_cell = self._pick_next_feature_cell()
            if current_cell is None:
                break
            
            # Find states in cell
            states_in_cell = self.feature_space[current_cell]
            
            # Get unexpanded moves
            unexpanded_moves = []
            for node in states_in_cell:
                state_hash = self._state_to_hash(node.state)
                if state_hash in self.unexpanded_moves:
                    for move in self.unexpanded_moves[state_hash]:
                        unexpanded_moves.append((node, move))
            
            if not unexpanded_moves:
                continue
            
            # Choose best move
            best_node, best_move = min(unexpanded_moves,
                                     key=lambda x: x[0].accumulated_weight + x[1].weight)
            
            # Apply move
            new_state = self._apply_move(best_node.state, best_move)
            if new_state is None or new_state.is_deadlock():
                # Remove invalid move
                state_hash = self._state_to_hash(best_node.state)
                if state_hash in self.unexpanded_moves:
                    self.unexpanded_moves[state_hash].remove(best_move)
                continue
            
            # Add new state
            new_state_hash = self._state_to_hash(new_state)
            new_weight = best_node.accumulated_weight + best_move.weight
            
            if new_state_hash in self.search_tree:
                existing_node = self.search_tree[new_state_hash]
                if new_weight >= existing_node.accumulated_weight:
                    state_hash = self._state_to_hash(best_node.state)
                    if state_hash in self.unexpanded_moves:
                        self.unexpanded_moves[state_hash].remove(best_move)
                    continue
            
            # Create new node
            new_features = self.feature_calculator.calculate_features(new_state)
            new_node = FESSNode(
                state=new_state,
                feature_vector=new_features,
                parent=best_node,
                action=best_move,
                accumulated_weight=new_weight,
                depth=best_node.depth + 1
            )
            
            self.search_tree[new_state_hash] = new_node
            self.nodes_expanded += 1
            
            if new_features not in self.feature_space:
                self.feature_space[new_features] = []
            self.feature_space[new_features].append(new_node)
            
            self._assign_weights_to_moves(new_node)
            
            # Remove expanded move
            state_hash = self._state_to_hash(best_node.state)
            if state_hash in self.unexpanded_moves and best_move in self.unexpanded_moves[state_hash]:
                self.unexpanded_moves[state_hash].remove(best_move)
        
        return False, [], self._get_statistics()
    
    def _apply_move(self, state: SokobanState, move: MacroMoveAction) -> Optional[SokobanState]:
        """Apply a macro move with proper player position update."""
        if move.box_start not in state.boxes:
            return None
        
        if not state.is_valid_position(move.box_end) or move.box_end in state.boxes:
            return None
        
        new_state = state.copy()
        new_state.boxes.remove(move.box_start)
        new_state.boxes.add(move.box_end)
        new_state.player_pos = move.final_player_pos
        
        return new_state
    
    def _assign_weights_to_moves(self, node: FESSNode):
        """Assign weights to moves from the given state."""
        state_hash = self._state_to_hash(node.state)
        
        # Get advisor moves first
        advisor_moves = self.advisor.get_advisor_moves(node.state, node.feature_vector)
        
        # Generate all feasible moves
        generator = FESSMacroMoveGenerator(node.state)
        all_moves = generator.generate_feasible_macro_moves()
        
        # Remove duplicates and assign weights
        unique_moves = {}
        for move in advisor_moves + all_moves:
            key = (move.box_start, move.box_end)
            if key not in unique_moves or move.weight < unique_moves[key].weight:
                unique_moves[key] = move
        
        # Store for expansion
        self.unexpanded_moves[state_hash] = list(unique_moves.values())
    
    def _state_to_hash(self, state: SokobanState) -> Tuple:
        """Convert state to hashable representation."""
        return (tuple(sorted(state.boxes)), state.player_pos)
    
    def _check_for_solution(self) -> Optional[FESSNode]:
        """Check if any node represents a solution."""
        for node in self.search_tree.values():
            if node.state.is_completed():
                return node
        return None
    
    def _pick_next_feature_cell(self) -> Optional[FeatureVector]:
        """Pick next cell to explore."""
        if not self.feature_space:
            return None
        
        non_empty_cells = [cell for cell, nodes in self.feature_space.items() if nodes]
        if not non_empty_cells:
            return None
        
        return non_empty_cells[self.nodes_expanded % len(non_empty_cells)]
    
    def _extract_solution(self, goal_node: FESSNode) -> Tuple[bool, List[MacroMoveAction], Dict[str, Any]]:
        """Extract solution path."""
        solution_moves = []
        current = goal_node
        
        while current.parent is not None:
            if current.action:
                solution_moves.append(current.action)
            current = current.parent
        
        solution_moves.reverse()
        return True, solution_moves, self._get_statistics()
    
    def _get_statistics(self) -> Dict[str, Any]:
        """Get solving statistics."""
        return {
            'nodes_expanded': self.nodes_expanded,
            'time_elapsed': time.time() - self.start_time,
            'feature_space_size': len(self.feature_space)
        }