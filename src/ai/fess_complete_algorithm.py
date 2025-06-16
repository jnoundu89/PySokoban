"""
FESS Complete Algorithm
=======================

Implémentation complète de l'algorithme FESS selon le document de recherche.

"Initialize:
Set feature space to empty (FS)
Set the start state as the root of the search tree (DS)
Assign a weight of zero to the root state (DS)
Add feature values to the root state (DS)
Project root state onto a cell in feature space (FS)
Assign weights to all moves from the root state (DS+FS)

Search:
while no solution has been found
Pick the next cell in feature space (FS)
Find all search-tree states that project onto this cell (DS)
Identify all un-expanded moves from these states (DS)
Choose move with least accumulated weight (DS)
Add the resulting state to the search tree (DS)
Added state's weight = parent's weight + move weight (DS)
Add feature values to the added state (DS)
Project added state onto a cell in feature space (FS)
Assign weights to all moves from the added state (DS+FS)"

Référence: "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
"""

from typing import Dict, List, Set, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from collections import defaultdict, deque
import time
import logging

from src.core.level import Level
from src.core.sokoban_state import SokobanState
from src.ai.fess_enhanced_features import FESSEnhancedFeatures, FESSFeatureVector, create_goal_features
from src.ai.fess_weight_system import FESSWeightSystem, FESSMoveSelector, WeightedMove
from src.ai.fess_room_analysis import FESSRoomAnalyzer
from src.ai.fess_advisors import FESSAdvisorSystem
from src.ai.fess_packing_plan import FESSPackingPlanGenerator, PackingPlan
from src.ai.fess_deadlock_detection import FESSDeadlockDetector
from src.ai.fess_notation import FESSLevelAnalyzer, MacroMove


@dataclass
class FESSNode:
    """Nœud dans l'arbre de recherche FESS."""
    state: SokobanState
    features: FESSFeatureVector
    parent: Optional['FESSNode']
    move_from_parent: Optional[MacroMove]
    accumulated_weight: int
    depth: int
    children: List['FESSNode']
    is_expanded: bool = False
    is_deadlock: bool = False
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class FESSCell:
    """Cellule dans l'espace des features."""
    features: FESSFeatureVector
    nodes: List[FESSNode]
    is_visited: bool = False
    visit_count: int = 0
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
    
    def add_node(self, node: FESSNode):
        """Ajoute un nœud à cette cellule."""
        self.nodes.append(node)
    
    def get_unexpanded_moves(self) -> List[Tuple[FESSNode, MacroMove]]:
        """Retourne tous les moves non-expandus depuis cette cellule."""
        unexpanded = []
        
        for node in self.nodes:
            if not node.is_deadlock:
                # Génère les moves possibles pour ce nœud
                # (sera fait par l'algorithme principal)
                pass
        
        return unexpanded


@dataclass
class FESSSearchStatistics:
    """Statistiques de la recherche FESS."""
    nodes_expanded: int = 0
    total_nodes: int = 0
    feature_space_cells: int = 0
    deadlocks_detected: int = 0
    advisor_moves_used: int = 0
    difficult_moves_used: int = 0
    search_time: float = 0.0
    solution_length: int = 0
    max_depth_reached: int = 0


class FESSCompleteAlgorithm:
    """
    Algorithme FESS complet selon le document de recherche.
    
    Intègre tous les composants FESS :
    - Feature Space 4D avec enhanced features
    - Weight System 0:1 avec 7 advisors
    - Packing Plan et analyse des deadlocks
    - Sélection cyclique des cellules
    - Macro moves comme unité de base
    """
    
    def __init__(self, level: Level):
        self.level = level
        self.logger = logging.getLogger(__name__)
        
        # Composants FESS
        self.features = FESSEnhancedFeatures(level)
        self.room_analyzer = FESSRoomAnalyzer(level)
        self.advisor_system = FESSAdvisorSystem(self.features, self.room_analyzer)
        self.weight_system = FESSWeightSystem()
        self.move_selector = FESSMoveSelector(self.weight_system)
        self.packing_plan_generator = FESSPackingPlanGenerator(level)
        self.deadlock_detector = FESSDeadlockDetector(level)
        self.macro_move_analyzer = FESSLevelAnalyzer(level)
        
        # Structures de données FESS
        self.feature_space: Dict[Tuple[int, int, int, int], FESSCell] = {}
        self.search_tree_root: Optional[FESSNode] = None
        self.current_cell_cycle = []
        self.current_cell_index = 0
        self.packing_plan: Optional[PackingPlan] = None
        
        # Configuration
        self.max_search_time = 300.0  # 5 minutes par défaut
        self.max_nodes = 100000       # Limite de nœuds
        self.cycle_strategy = "round_robin"  # Stratégie de sélection des cellules
        
        # Statistiques
        self.stats = FESSSearchStatistics()
    
    def solve(self, initial_state: SokobanState, 
              max_time: Optional[float] = None,
              max_nodes: Optional[int] = None) -> Optional[List[MacroMove]]:
        """
        Résout le niveau en utilisant l'algorithme FESS complet.
        
        Args:
            initial_state: État initial du niveau
            max_time: Temps maximum de recherche (secondes)
            max_nodes: Nombre maximum de nœuds
            
        Returns:
            Liste des macro moves solution ou None si pas trouvé
        """
        start_time = time.time()
        
        if max_time is not None:
            self.max_search_time = max_time
        if max_nodes is not None:
            self.max_nodes = max_nodes
        
        self.logger.info(f"Starting FESS search with max_time={self.max_search_time}s, max_nodes={self.max_nodes}")
        
        try:
            # Initialize selon le pseudocode
            self._initialize(initial_state)
            
            # Search selon le pseudocode
            solution = self._search(start_time)
            
            self.stats.search_time = time.time() - start_time
            self._log_final_statistics()
            
            return solution
            
        except Exception as e:
            self.logger.error(f"FESS search failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _initialize(self, initial_state: SokobanState):
        """
        Initialize selon le pseudocode Figure 2.
        
        "Set feature space to empty (FS)
        Set the start state as the root of the search tree (DS)
        Assign a weight of zero to the root state (DS)
        Add feature values to the root state (DS)
        Project root state onto a cell in feature space (FS)
        Assign weights to all moves from the root state (DS+FS)"
        """
        self.logger.debug("Initializing FESS algorithm")
        
        # Generate packing plan
        self.packing_plan = self.packing_plan_generator.generate_packing_plan(initial_state)
        if self.packing_plan.is_valid:
            # Intègre le packing plan dans les features
            self.features.set_packing_plan(self.packing_plan.get_packing_order())
            if self.packing_plan.sink_room:
                self.features.set_sink_room_basin(self.packing_plan.sink_room.squares)
        
        # Set feature space to empty (FS)
        self.feature_space.clear()
        
        # Set the start state as the root of the search tree (DS)
        initial_features = self.features.compute_feature_vector(initial_state)
        
        self.search_tree_root = FESSNode(
            state=initial_state,
            features=initial_features,
            parent=None,
            move_from_parent=None,
            accumulated_weight=0,  # Assign a weight of zero to the root state
            depth=0,
            children=[]
        )
        
        # Project root state onto a cell in feature space (FS)
        cell_key = initial_features.to_tuple()
        if cell_key not in self.feature_space:
            self.feature_space[cell_key] = FESSCell(
                features=initial_features,
                nodes=[]
            )
        
        self.feature_space[cell_key].add_node(self.search_tree_root)
        
        # Initialize cell cycle for "going cyclically over all non-empty cells"
        self.current_cell_cycle = [cell_key]
        self.current_cell_index = 0
        
        # Update statistics
        self.stats.total_nodes = 1
        self.stats.feature_space_cells = 1
        
        self.logger.debug(f"Initialized with features: {initial_features}")
    
    def _search(self, start_time: float) -> Optional[List[MacroMove]]:
        """
        Search selon le pseudocode Figure 2.
        
        "while no solution has been found
        Pick the next cell in feature space (FS)
        Find all search-tree states that project onto this cell (DS)
        Identify all un-expanded moves from these states (DS)
        Choose move with least accumulated weight (DS)
        Add the resulting state to the search tree (DS)
        Added state's weight = parent's weight + move weight (DS)
        Add feature values to the added state (DS)
        Project added state onto a cell in feature space (FS)
        Assign weights to all moves from the added state (DS+FS)"
        """
        goal_features = create_goal_features(len(self.search_tree_root.state.box_positions))
        self.logger.debug(f"Goal features: {goal_features}")
        
        iteration = 0
        while True:
            iteration += 1
            
            # Check termination conditions
            if time.time() - start_time > self.max_search_time:
                self.logger.warning("Search timeout reached")
                break
            
            if self.stats.total_nodes >= self.max_nodes:
                self.logger.warning("Node limit reached")
                break
            
            if not self.feature_space:
                self.logger.warning("Feature space is empty")
                break
            
            # Pick the next cell in feature space (FS)
            current_cell = self._pick_next_cell()
            if current_cell is None:
                self.logger.warning("No more cells to explore")
                break
            
            # Find all search-tree states that project onto this cell (DS)
            # Identify all un-expanded moves from these states (DS)
            node_move_pairs = self._get_unexpanded_moves_from_cell(current_cell)
            
            if not node_move_pairs:
                # No unexpanded moves in this cell, continue to next
                continue
            
            # Choose move with least accumulated weight (DS)
            selected_node, selected_weighted_move = self._choose_minimum_weight_move(node_move_pairs)
            
            if selected_weighted_move is None:
                continue
            
            # Add the resulting state to the search tree (DS)
            new_node = self._expand_node(selected_node, selected_weighted_move)
            
            if new_node is None:
                continue  # Expansion failed (deadlock, invalid move, etc.)
            
            # Check for solution
            if self._is_solution(new_node, goal_features):
                self.logger.info(f"Solution found at iteration {iteration}!")
                return self._extract_solution_path(new_node)
            
            # Log progress periodically
            if iteration % 100 == 0:
                self._log_search_progress(iteration, current_cell.features)
        
        self.logger.info(f"Search completed after {iteration} iterations without solution")
        return None
    
    def _pick_next_cell(self) -> Optional[FESSCell]:
        """
        Pick the next cell in feature space (FS).
        
        "FESS works by going cyclically over all non-empty cells in the FS."
        """
        if not self.current_cell_cycle:
            # Rebuild cycle with all non-empty cells
            self.current_cell_cycle = list(self.feature_space.keys())
            self.current_cell_index = 0
        
        if not self.current_cell_cycle:
            return None
        
        # Cyclically select next cell
        cell_key = self.current_cell_cycle[self.current_cell_index]
        self.current_cell_index = (self.current_cell_index + 1) % len(self.current_cell_cycle)
        
        cell = self.feature_space.get(cell_key)
        if cell:
            cell.visit_count += 1
            cell.is_visited = True
        
        return cell
    
    def _get_unexpanded_moves_from_cell(self, cell: FESSCell) -> List[Tuple[FESSNode, WeightedMove]]:
        """
        Find all search-tree states that project onto this cell (DS)
        Identify all un-expanded moves from these states (DS)
        """
        node_move_pairs = []
        
        for node in cell.nodes:
            if node.is_deadlock:
                continue
            
            # Generate macro moves for this node
            macro_moves = self.macro_move_analyzer.generate_macro_moves(node.state)
            
            if not macro_moves:
                continue
            
            # Consult advisors
            advisor_recommendations = self.advisor_system.consult_advisors(node.state, macro_moves)
            
            # Assign weights
            weighted_moves = self.weight_system.assign_weights_to_moves(
                node.state, macro_moves, advisor_recommendations
            )
            
            # Filter out already expanded moves
            for weighted_move in weighted_moves:
                if not self._is_move_already_expanded(node, weighted_move.macro_move):
                    node_move_pairs.append((node, weighted_move))
        
        return node_move_pairs
    
    def _choose_minimum_weight_move(self, 
                                   node_move_pairs: List[Tuple[FESSNode, WeightedMove]]) -> Tuple[Optional[FESSNode], Optional[WeightedMove]]:
        """
        Choose move with least accumulated weight (DS).
        
        "Added state's weight = parent's weight + move weight (DS)"
        """
        if not node_move_pairs:
            return None, None
        
        # Calculate accumulated weights
        candidates = []
        for node, weighted_move in node_move_pairs:
            accumulated_weight = node.accumulated_weight + weighted_move.weight
            candidates.append((accumulated_weight, node, weighted_move))
        
        # Sort by accumulated weight (minimum first)
        candidates.sort(key=lambda x: x[0])
        
        # Select minimum weight move with tie-breaking
        min_weight = candidates[0][0]
        min_candidates = [c for c in candidates if c[0] == min_weight]
        
        if len(min_candidates) == 1:
            _, selected_node, selected_move = min_candidates[0]
        else:
            # Tie-breaking using feature-based comparison
            _, selected_node, selected_move = self._break_ties(min_candidates)
        
        return selected_node, selected_move
    
    def _break_ties(self, candidates: List[Tuple[int, FESSNode, WeightedMove]]) -> Tuple[int, FESSNode, WeightedMove]:
        """Break ties using lexicographic ordering according to the document."""
        goal_features = create_goal_features(len(self.search_tree_root.state.box_positions))
        
        # Trie par progression vers le but selon l'ordre lexicographique FESS
        def calculate_progress_score(candidate):
            accumulated_weight, node, weighted_move = candidate
            
            # Simule le nouvel état pour évaluer le progrès
            try:
                new_state = weighted_move.macro_move.apply_to_state(node.state)
                new_features = self.features.compute_feature_vector(new_state)
                
                # Score basé sur la progression vers le but (ordre lexicographique)
                # 1. OOP (priorité absolue - doit diminuer)
                oop_progress = max(0, node.features.out_of_plan - new_features.out_of_plan) * 1000
                
                # 2. Packing (doit augmenter)
                packing_progress = max(0, new_features.packing - node.features.packing) * 100
                
                # 3. Connectivity (doit diminuer)
                connectivity_progress = max(0, node.features.connectivity - new_features.connectivity) * 10
                
                # 4. Room connectivity (doit diminuer)
                room_connectivity_progress = max(0, node.features.room_connectivity - new_features.room_connectivity)
                
                # Score total de progression
                total_progress = oop_progress + packing_progress + connectivity_progress + room_connectivity_progress
                
                # Bonus pour les advisor moves
                advisor_bonus = 5 if weighted_move.weight == 0 else 0
                
                return total_progress + advisor_bonus
                
            except Exception:
                return 0  # En cas d'erreur, score minimal
        
        # Trie par score de progression (descendant)
        candidates_with_scores = [(calculate_progress_score(c), c) for c in candidates]
        candidates_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Retourne le candidat avec le meilleur score
        return candidates_with_scores[0][1]
    
    def _expand_node(self, parent_node: FESSNode, weighted_move: WeightedMove) -> Optional[FESSNode]:
        """
        Add the resulting state to the search tree (DS)
        Added state's weight = parent's weight + move weight (DS)
        Add feature values to the added state (DS)
        Project added state onto a cell in feature space (FS)
        """
        try:
            # Apply the macro move
            new_state = weighted_move.macro_move.apply_to_state(parent_node.state)
            
            # Check for deadlock
            if self.deadlock_detector.is_deadlocked(new_state):
                self.stats.deadlocks_detected += 1
                return None
            
            # Add feature values to the added state (DS)
            new_features = self.features.compute_feature_vector(new_state)
            
            # Added state's weight = parent's weight + move weight (DS)
            new_accumulated_weight = parent_node.accumulated_weight + weighted_move.weight
            
            # Create new node
            new_node = FESSNode(
                state=new_state,
                features=new_features,
                parent=parent_node,
                move_from_parent=weighted_move.macro_move,
                accumulated_weight=new_accumulated_weight,
                depth=parent_node.depth + 1,
                children=[]
            )
            
            # Add to parent's children
            parent_node.children.append(new_node)
            
            # Project added state onto a cell in feature space (FS)
            cell_key = new_features.to_tuple()
            if cell_key not in self.feature_space:
                self.feature_space[cell_key] = FESSCell(
                    features=new_features,
                    nodes=[]
                )
                self.stats.feature_space_cells += 1
                
                # Add to cycle for future exploration
                self.current_cell_cycle.append(cell_key)
            
            self.feature_space[cell_key].add_node(new_node)
            
            # Update statistics
            self.stats.nodes_expanded += 1
            self.stats.total_nodes += 1
            self.stats.max_depth_reached = max(self.stats.max_depth_reached, new_node.depth)
            
            if weighted_move.weight == 0:
                self.stats.advisor_moves_used += 1
            else:
                self.stats.difficult_moves_used += 1
            
            return new_node
            
        except Exception as e:
            self.logger.debug(f"Failed to expand node: {e}")
            return None
    
    def _is_move_already_expanded(self, node: FESSNode, macro_move: MacroMove) -> bool:
        """Vérifie si un move a déjà été expandu depuis ce nœud."""
        for child in node.children:
            if child.move_from_parent == macro_move:
                return True
        return False
    
    def _is_solution(self, node: FESSNode, goal_features: FESSFeatureVector) -> bool:
        """Vérifie si un nœud représente une solution."""
        # Vérifie d'abord la condition FESS
        if node.features == goal_features:
            return True
        
        # Vérifie aussi directement si toutes les boîtes sont sur des targets
        return self._is_sokoban_solved(node.state)
    
    def _is_sokoban_solved(self, state: SokobanState) -> bool:
        """Vérifie si l'état Sokoban est résolu (toutes boîtes sur targets)."""
        for box_pos in state.box_positions:
            if not self.level.is_target(box_pos[0], box_pos[1]):
                return False
        return True
    
    def _extract_solution_path(self, solution_node: FESSNode) -> List[MacroMove]:
        """Extrait le chemin de solution depuis la racine."""
        path = []
        current = solution_node
        
        while current.parent is not None:
            if current.move_from_parent:
                path.append(current.move_from_parent)
            current = current.parent
        
        path.reverse()
        self.stats.solution_length = len(path)
        
        return path
    
    def _log_search_progress(self, iteration: int, current_features: FESSFeatureVector):
        """Log le progrès de la recherche."""
        self.logger.debug(f"Iteration {iteration}: "
                         f"Features={current_features}, "
                         f"Nodes={self.stats.total_nodes}, "
                         f"Cells={self.stats.feature_space_cells}")
    
    def _log_final_statistics(self):
        """Log les statistiques finales."""
        self.logger.info("FESS Search Statistics:")
        self.logger.info(f"  Nodes expanded: {self.stats.nodes_expanded}")
        self.logger.info(f"  Total nodes: {self.stats.total_nodes}")
        self.logger.info(f"  Feature space cells: {self.stats.feature_space_cells}")
        self.logger.info(f"  Deadlocks detected: {self.stats.deadlocks_detected}")
        self.logger.info(f"  Advisor moves used: {self.stats.advisor_moves_used}")
        self.logger.info(f"  Difficult moves used: {self.stats.difficult_moves_used}")
        self.logger.info(f"  Search time: {self.stats.search_time:.2f}s")
        self.logger.info(f"  Max depth reached: {self.stats.max_depth_reached}")
        
        if self.stats.solution_length > 0:
            self.logger.info(f"  Solution length: {self.stats.solution_length} macro moves")
    
    def get_statistics(self) -> FESSSearchStatistics:
        """Retourne les statistiques de recherche."""
        return self.stats
    
    def reset_statistics(self):
        """Remet à zéro les statistiques."""
        self.stats = FESSSearchStatistics()


def create_fess_solver(level: Level) -> FESSCompleteAlgorithm:
    """Factory function pour créer un solveur FESS complet."""
    return FESSCompleteAlgorithm(level)


def solve_level_with_fess(level: Level, 
                         max_time: float = 60.0,
                         max_nodes: int = 50000) -> Optional[List[MacroMove]]:
    """
    Résout un niveau avec l'algorithme FESS complet.
    
    Args:
        level: Niveau à résoudre
        max_time: Temps maximum de recherche
        max_nodes: Nombre maximum de nœuds
        
    Returns:
        Solution en macro moves ou None
    """
    solver = create_fess_solver(level)
    initial_state = SokobanState.from_level(level)
    
    return solver.solve(initial_state, max_time, max_nodes)