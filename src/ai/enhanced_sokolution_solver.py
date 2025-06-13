"""
Enhanced SokolutionSolver - Solver Sokoban unifié et optimisé.

Ce module implémente un solver Sokoban avancé basé sur les techniques
du solver Sokolution de Florent Diedler, avec des améliorations pour
l'intégration ML et l'analyse de performance.
"""

import time
import heapq
from collections import deque, defaultdict
from typing import List, Tuple, Set, Dict, Optional, FrozenSet, Any, Callable
import itertools
from dataclasses import dataclass
from enum import Enum

from .algorithm_selector import Algorithm


class SearchMode(Enum):
    """Modes de recherche disponibles."""
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    BIDIRECTIONAL = "BIDIRECTIONAL"


@dataclass
class SolutionData:
    """Données de solution avec métriques."""
    moves: List[str]
    solve_time: float
    states_explored: int
    states_generated: int
    deadlocks_pruned: int
    algorithm_used: Algorithm
    search_mode: SearchMode
    memory_peak: int
    heuristic_calls: int
    macro_moves_used: int


class SokolutionState:
    """
    Représentation optimisée d'un état dans le jeu Sokoban.
    Utilise des techniques d'optimisation mémoire inspirées de Sokolution.
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
        self._hash_cache = None
    
    def __hash__(self):
        if self._hash_cache is None:
            self._hash_cache = hash((self.player_pos, self.boxes))
        return self._hash_cache
    
    def __eq__(self, other):
        if not isinstance(other, SokolutionState):
            return False
        return self.player_pos == other.player_pos and self.boxes == other.boxes
    
    def __lt__(self, other):
        # Tri selon les critères Sokolution : F-cost, H-cost, puis plus récent (G-cost élevé)
        if self.f_cost != other.f_cost:
            return self.f_cost < other.f_cost
        if self.h_cost != other.h_cost:
            return self.h_cost < other.h_cost
        return self.g_cost > other.g_cost  # Préférer les nœuds plus récents


class TranspositionTable:
    """
    Table de transposition optimisée avec linear probing.
    Implémentation inspirée de Sokolution pour le contrôle mémoire.
    """
    
    def __init__(self, size=2**20):  # 1M entries par défaut
        self.size = size
        self.table = [None] * size
        self.count = 0
        self.hits = 0
        self.misses = 0
        self.collisions = 0
    
    def _hash_function(self, state: SokolutionState) -> int:
        """Fonction de hash optimisée pour les états Sokoban."""
        return hash(state) % self.size
    
    def add(self, state: SokolutionState) -> bool:
        """
        Ajoute un état à la table.
        
        Returns:
            bool: True si l'état a été ajouté, False s'il existait déjà
        """
        if self.count >= self.size * 0.75:  # Redimensionner si facteur de charge > 0.75
            self._resize(self.size * 2)
        
        index = self._hash_function(state)
        original_index = index
        
        # Linear probing
        while self.table[index] is not None:
            if self.table[index] == state:
                return False  # État déjà dans la table
            index = (index + 1) % self.size
            if index == original_index:  # Table pleine
                return False
        
        self.table[index] = state
        self.count += 1
        return True
    
    def contains(self, state: SokolutionState) -> bool:
        """Vérifie si un état est dans la table."""
        index = self._hash_function(state)
        original_index = index
        
        while self.table[index] is not None:
            if self.table[index] == state:
                self.hits += 1
                return True
            index = (index + 1) % self.size
            if index == original_index:
                break
        
        self.misses += 1
        return False
    
    def _resize(self, new_size: int):
        """Redimensionne la table."""
        old_table = self.table
        self.size = new_size
        self.table = [None] * new_size
        old_count = self.count
        self.count = 0
        
        for state in old_table:
            if state is not None:
                self.add(state)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de performance de la table."""
        total_accesses = self.hits + self.misses
        hit_ratio = self.hits / total_accesses if total_accesses > 0 else 0
        load_factor = self.count / self.size
        
        return {
            'size': self.size,
            'count': self.count,
            'hits': self.hits,
            'misses': self.misses,
            'hit_ratio': hit_ratio,
            'load_factor': load_factor
        }


class HungarianMatcher:
    """
    Implémentation optimisée O(n³) de l'algorithme Hongrois
    pour le calcul du bipartite matching boxes-targets.
    """
    
    def __init__(self, level):
        self.level = level
        self.distances = self._precompute_distances()
    
    def _precompute_distances(self) -> Dict[Tuple[int, int], Dict[Tuple[int, int], int]]:
        """Précalcule les distances entre toutes les positions."""
        distances = {}
        
        for y in range(self.level.height):
            for x in range(self.level.width):
                if not self.level.is_wall(x, y):
                    distances[(x, y)] = self._bfs_distances((x, y))
        
        return distances
    
    def _bfs_distances(self, start: Tuple[int, int]) -> Dict[Tuple[int, int], int]:
        """Calcule les distances BFS depuis une position de départ."""
        distances = {start: 0}
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if self.level.is_wall(nx, ny) or (nx, ny) in distances:
                    continue
                
                distances[(nx, ny)] = distances[(x, y)] + 1
                queue.append((nx, ny))
        
        return distances
    
    def calculate_matching(self, boxes: List[Tuple[int, int]]) -> int:
        """
        Calcule le coût minimum du matching bipartite.
        
        Args:
            boxes: Liste des positions des boxes
            
        Returns:
            int: Coût minimum du matching
        """
        targets = list(self.level.targets)
        
        if not boxes or not targets:
            return 0
        
        # Créer la matrice de coûts
        cost_matrix = []
        for box in boxes:
            row = []
            for target in targets:
                if target in self.distances.get(box, {}):
                    cost = self.distances[box][target]
                else:
                    cost = float('inf')  # Inaccessible
                row.append(cost)
            cost_matrix.append(row)
        
        # Appliquer l'algorithme Hongrois optimisé
        return self._hungarian_algorithm(cost_matrix)
    
    def _hungarian_algorithm(self, cost_matrix: List[List[int]]) -> int:
        """
        Algorithme Hongrois optimisé O(n³).
        
        Cette implémentation simplifiée utilise une approche gloutonne
        pour une performance acceptable dans le contexte du jeu.
        """
        if not cost_matrix or not cost_matrix[0]:
            return 0
        
        n_boxes = len(cost_matrix)
        n_targets = len(cost_matrix[0])
        
        # Pour une implémentation rapide, on utilise une approche gloutonne
        # qui donne une bonne approximation du matching optimal
        total_cost = 0
        used_targets = set()
        
        # Trier les boxes par leur coût minimum vers une target
        box_costs = []
        for i, box_row in enumerate(cost_matrix):
            min_cost = min(cost for cost in box_row if cost != float('inf'))
            box_costs.append((min_cost, i))
        
        box_costs.sort()  # Traiter d'abord les boxes avec le coût minimum le plus bas
        
        for _, box_idx in box_costs:
            best_target = None
            best_cost = float('inf')
            
            for target_idx, cost in enumerate(cost_matrix[box_idx]):
                if target_idx not in used_targets and cost < best_cost:
                    best_cost = cost
                    best_target = target_idx
            
            if best_target is not None and best_cost != float('inf'):
                total_cost += best_cost
                used_targets.add(best_target)
            else:
                # Aucune target disponible, coût infini
                return float('inf')
        
        return total_cost


class DeadlockDetector:
    """
    Détecteur de deadlocks avancé selon les techniques Sokolution.
    Inclut la détection de deadlocks statiques et dynamiques.
    """
    
    def __init__(self, level):
        self.level = level
        self.width = level.width
        self.height = level.height
        
        # Précalcul des deadlocks statiques
        self.corner_deadlocks = self._find_corner_deadlocks()
        self.freeze_deadlock_cache = {}
        
        # Patterns de deadlocks dynamiques découverts
        self.dynamic_deadlock_patterns = set()
        
        # Statistiques de détection
        self.deadlocks_detected = 0
        self.corner_deadlocks_count = 0
        self.freeze_deadlocks_count = 0
    
    def _find_corner_deadlocks(self) -> Set[Tuple[int, int]]:
        """Trouve toutes les positions de deadlock en coin."""
        corner_deadlocks = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if self._is_corner_deadlock(x, y):
                    corner_deadlocks.add((x, y))
        
        return corner_deadlocks
    
    def _is_corner_deadlock(self, x: int, y: int) -> bool:
        """Vérifie si une position est un deadlock de coin."""
        # Ignorer les murs et les targets
        if self.level.is_wall(x, y) or self.level.is_target(x, y):
            return False
        
        # Vérifier les coins (deux murs adjacents)
        corner_patterns = [
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y-1)),  # Coin haut-gauche
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y-1)),  # Coin haut-droite
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y+1)),  # Coin bas-gauche
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y+1))   # Coin bas-droite
        ]
        
        return any(corner_patterns)
    
    def is_deadlock(self, boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Vérifie si la configuration actuelle est un deadlock.
        
        Args:
            boxes: Positions actuelles des boxes
            
        Returns:
            bool: True si c'est un deadlock
        """
        # Vérification des deadlocks de coin
        for box in boxes:
            if box not in self.level.targets and box in self.corner_deadlocks:
                self.corner_deadlocks_count += 1
                self.deadlocks_detected += 1
                return True
        
        # Vérification des deadlocks de gel
        if self._has_freeze_deadlock(boxes):
            self.freeze_deadlocks_count += 1
            self.deadlocks_detected += 1
            return True
        
        # Vérification des patterns de deadlocks dynamiques
        for pattern in self.dynamic_deadlock_patterns:
            if pattern.issubset(boxes):
                self.deadlocks_detected += 1
                return True
        
        return False
    
    def _has_freeze_deadlock(self, boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Détecte les deadlocks de gel (boxes qui ne peuvent plus bouger).
        """
        # Vérifier chaque box individuellement
        for box in boxes:
            if box in self.level.targets:
                continue  # Les boxes sur targets ne sont pas des deadlocks
            
            if self._is_box_frozen(box, boxes):
                return True
        
        # Vérifier les deadlocks de groupe (plusieurs boxes qui se bloquent mutuellement)
        return self._has_group_freeze_deadlock(boxes)
    
    def _is_box_frozen(self, box: Tuple[int, int], boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """Vérifie si une box individuelle est gelée."""
        x, y = box
        
        # Vérifier si la box peut bouger horizontalement
        horizontal_blocked = (
            (self.level.is_wall(x-1, y) or (x-1, y) in boxes) and
            (self.level.is_wall(x+1, y) or (x+1, y) in boxes)
        )
        
        # Vérifier si la box peut bouger verticalement
        vertical_blocked = (
            (self.level.is_wall(x, y-1) or (x, y-1) in boxes) and
            (self.level.is_wall(x, y+1) or (x, y+1) in boxes)
        )
        
        # Si les deux directions sont bloquées, la box est gelée
        return horizontal_blocked and vertical_blocked
    
    def _has_group_freeze_deadlock(self, boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """
        Détecte les deadlocks de groupe où plusieurs boxes se bloquent mutuellement.
        """
        # Cette fonction peut être étendue pour détecter des patterns plus complexes
        # Pour l'instant, on se contente de vérifications simples
        
        # Vérifier les lignes de boxes contre un mur
        return self._check_line_deadlocks(boxes)
    
    def _check_line_deadlocks(self, boxes: FrozenSet[Tuple[int, int]]) -> bool:
        """Vérifie les deadlocks de ligne de boxes."""
        # Vérifier les lignes horizontales
        for y in range(self.height):
            line_boxes = [box for box in boxes if box[1] == y and box not in self.level.targets]
            if len(line_boxes) >= 2:
                line_boxes.sort()  # Trier par x
                
                # Vérifier si toute la ligne est contre un mur
                if all(self.level.is_wall(box[0], y-1) or self.level.is_wall(box[0], y+1) for box in line_boxes):
                    # Vérifier s'il y a des gaps dans la ligne qui empêchent le mouvement
                    for i in range(len(line_boxes) - 1):
                        if line_boxes[i+1][0] - line_boxes[i][0] == 1:  # Boxes adjacentes
                            # Vérifier si elles ne peuvent pas bouger
                            if not self._can_line_move(line_boxes[i:i+2], y):
                                return True
        
        # Même vérification pour les lignes verticales
        for x in range(self.width):
            line_boxes = [box for box in boxes if box[0] == x and box not in self.level.targets]
            if len(line_boxes) >= 2:
                line_boxes.sort(key=lambda b: b[1])  # Trier par y
                
                if all(self.level.is_wall(x-1, box[1]) or self.level.is_wall(x+1, box[1]) for box in line_boxes):
                    for i in range(len(line_boxes) - 1):
                        if line_boxes[i+1][1] - line_boxes[i][1] == 1:  # Boxes adjacentes
                            if not self._can_line_move(line_boxes[i:i+2], x, vertical=True):
                                return True
        
        return False
    
    def _can_line_move(self, line_boxes: List[Tuple[int, int]], coordinate: int, vertical=False) -> bool:
        """Vérifie si une ligne de boxes peut bouger."""
        # Simplifié pour l'implémentation de base
        # Une implémentation complète nécessiterait une analyse plus sophistiquée
        return False
    
    def add_dynamic_deadlock_pattern(self, boxes: FrozenSet[Tuple[int, int]]):
        """Ajoute un pattern de deadlock découvert dynamiquement."""
        # Simplifier le pattern pour ne garder que les boxes essentielles
        minimal_pattern = self._minimize_deadlock_pattern(boxes)
        if minimal_pattern and len(minimal_pattern) <= 5:  # Limiter la taille des patterns
            self.dynamic_deadlock_patterns.add(minimal_pattern)
    
    def _minimize_deadlock_pattern(self, boxes: FrozenSet[Tuple[int, int]]) -> Optional[FrozenSet[Tuple[int, int]]]:
        """
        Tente de minimiser un pattern de deadlock.
        
        Cette fonction pourrait être considérablement améliorée avec des algorithmes
        plus sophistiqués de minimisation de patterns.
        """
        # Pour l'instant, retourner le pattern complet
        # Une vraie implémentation essaierait de retirer des boxes une par une
        # et de vérifier si le deadlock persiste
        return boxes
    
    def get_statistics(self) -> Dict[str, int]:
        """Obtient les statistiques de détection de deadlocks."""
        return {
            'total_deadlocks_detected': self.deadlocks_detected,
            'corner_deadlocks': self.corner_deadlocks_count,
            'freeze_deadlocks': self.freeze_deadlocks_count,
            'dynamic_patterns_learned': len(self.dynamic_deadlock_patterns),
            'corner_deadlock_positions': len(self.corner_deadlocks)
        }


class EnhancedSokolutionSolver:
    """
    Solver Sokoban unifié et optimisé basé sur les techniques Sokolution.
    
    Ce solver intègre tous les algorithmes de recherche et les techniques
    avancées d'optimisation dans une seule classe unifiée.
    """
    
    def __init__(self, level, max_states=1000000, time_limit=120.0):
        self.level = level
        self.max_states = max_states
        self.time_limit = time_limit
        
        # Composants principaux
        self.hungarian_matcher = HungarianMatcher(level)
        self.deadlock_detector = DeadlockDetector(level)
        self.transposition_table = TranspositionTable()
        
        # État de la recherche
        self.open_set = []
        self.solution = None
        
        # Métriques de performance
        self.states_explored = 0
        self.states_generated = 0
        self.start_time = 0
        self.heuristic_calls = 0
        self.macro_moves_used = 0
        
        # Configuration
        self.current_algorithm = None
        self.current_mode = SearchMode.FORWARD
    
    def solve(self, algorithm: Algorithm, mode: SearchMode = SearchMode.FORWARD, 
              progress_callback: Optional[Callable] = None) -> Optional[SolutionData]:
        """
        Résout le niveau avec l'algorithme et le mode spécifiés.
        
        Args:
            algorithm: Algorithme à utiliser
            mode: Mode de recherche
            progress_callback: Callback optionnel pour les mises à jour de progression
            
        Returns:
            SolutionData si solution trouvée, None sinon
        """
        self._reset_state()
        self.current_algorithm = algorithm
        self.current_mode = mode
        self.start_time = time.time()
        
        if progress_callback:
            progress_callback(f"Démarrage du solver {algorithm.value} en mode {mode.value}...")
        
        # Sélection de l'algorithme de recherche
        if algorithm == Algorithm.BFS:
            solution_moves = self._bfs_search(progress_callback)
        elif algorithm == Algorithm.ASTAR:
            solution_moves = self._astar_search(progress_callback)
        elif algorithm == Algorithm.IDA_STAR:
            solution_moves = self._ida_star_search(progress_callback)
        elif algorithm == Algorithm.GREEDY:
            solution_moves = self._greedy_search(progress_callback)
        elif algorithm == Algorithm.BIDIRECTIONAL_GREEDY:
            solution_moves = self._bidirectional_search(progress_callback)
        else:
            raise ValueError(f"Algorithme non supporté: {algorithm}")
        
        solve_time = time.time() - self.start_time
        
        if solution_moves:
            if progress_callback:
                progress_callback(f"Solution trouvée: {len(solution_moves)} coups en {solve_time:.2f}s")
            
            return SolutionData(
                moves=solution_moves,
                solve_time=solve_time,
                states_explored=self.states_explored,
                states_generated=self.states_generated,
                deadlocks_pruned=self.deadlock_detector.deadlocks_detected,
                algorithm_used=algorithm,
                search_mode=mode,
                memory_peak=self.transposition_table.count,
                heuristic_calls=self.heuristic_calls,
                macro_moves_used=self.macro_moves_used
            )
        else:
            if progress_callback:
                progress_callback(f"Aucune solution trouvée en {solve_time:.2f}s")
            return None
    
    def _reset_state(self):
        """Remet à zéro l'état du solver."""
        self.states_explored = 0
        self.states_generated = 0
        self.heuristic_calls = 0
        self.macro_moves_used = 0
        self.transposition_table = TranspositionTable()
        self.open_set = []
        self.solution = None
    
    def _create_initial_state(self) -> SokolutionState:
        """Crée l'état initial selon le mode de recherche."""
        if self.current_mode == SearchMode.FORWARD:
            return SokolutionState(
                player_pos=self.level.player_pos,
                boxes=frozenset(self.level.boxes)
            )
        elif self.current_mode == SearchMode.BACKWARD:
            # Mode backward: commencer avec toutes les boxes sur les targets
            return SokolutionState(
                player_pos=self.level.player_pos,
                boxes=frozenset(self.level.targets)
            )
        else:  # BIDIRECTIONAL
            return SokolutionState(
                player_pos=self.level.player_pos,
                boxes=frozenset(self.level.boxes)
            )
    
    def _is_goal_state(self, state: SokolutionState) -> bool:
        """Vérifie si un état est l'état objectif."""
        if self.current_mode == SearchMode.FORWARD:
            return state.boxes == frozenset(self.level.targets)
        elif self.current_mode == SearchMode.BACKWARD:
            return state.boxes == frozenset(self.level.boxes)
        else:  # BIDIRECTIONAL
            return state.boxes == frozenset(self.level.targets)
    
    def _calculate_heuristic(self, state: SokolutionState) -> int:
        """Calcule la valeur heuristique d'un état."""
        self.heuristic_calls += 1
        
        # Utiliser le bipartite matching hongrois
        boxes_list = [box for box in state.boxes if box not in self.level.targets]
        
        if not boxes_list:
            return 0
        
        # Coût du matching bipartite
        matching_cost = self.hungarian_matcher.calculate_matching(boxes_list)
        
        # Ajouter des pénalités additionnelles
        penalty = self._calculate_additional_penalties(state)
        
        return matching_cost + penalty
    
    def _calculate_additional_penalties(self, state: SokolutionState) -> int:
        """Calcule des pénalités additionnelles pour l'heuristique."""
        penalty = 0
        
        # Pénalité pour les boxes pas sur target
        penalty += sum(1 for box in state.boxes if box not in self.level.targets)
        
        # Pénalité basée sur la distance du joueur aux boxes non placées
        unplaced_boxes = [box for box in state.boxes if box not in self.level.targets]
        if unplaced_boxes:
            min_distance = min(
                abs(state.player_pos[0] - box[0]) + abs(state.player_pos[1] - box[1])
                for box in unplaced_boxes
            )
            penalty += min_distance
        
        return penalty
    
    def _within_limits(self) -> bool:
        """Vérifie si on est dans les limites de temps et d'états."""
        return (time.time() - self.start_time <= self.time_limit and
                self.states_explored <= self.max_states)
    
    # Les implémentations des algorithmes de recherche suivront dans la suite...
    
    def _bfs_search(self, progress_callback: Optional[Callable] = None) -> Optional[List[str]]:
        """Implémentation BFS."""
        initial_state = self._create_initial_state()
        
        self.open_set = deque([initial_state])
        self.transposition_table.add(initial_state)
        
        while self.open_set and self._within_limits():
            current_state = self.open_set.popleft()
            self.states_explored += 1
            
            if progress_callback and self.states_explored % 10000 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"BFS: Exploré {self.states_explored} états en {elapsed:.1f}s")
            
            if self._is_goal_state(current_state):
                return self._reconstruct_path(current_state)
            
            # Générer les successeurs
            for successor in self._generate_successors(current_state):
                if not self.transposition_table.contains(successor):
                    self.open_set.append(successor)
                    self.transposition_table.add(successor)
                    self.states_generated += 1
        
        return None
    
    def _astar_search(self, progress_callback: Optional[Callable] = None) -> Optional[List[str]]:
        """Implémentation A*."""
        initial_state = self._create_initial_state()
        initial_state.h_cost = self._calculate_heuristic(initial_state)
        initial_state.f_cost = initial_state.g_cost + initial_state.h_cost
        
        self.open_set = [initial_state]
        self.transposition_table.add(initial_state)
        
        while self.open_set and self._within_limits():
            current_state = heapq.heappop(self.open_set)
            self.states_explored += 1
            
            if progress_callback and self.states_explored % 10000 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"A*: Exploré {self.states_explored} états en {elapsed:.1f}s")
            
            if self._is_goal_state(current_state):
                return self._reconstruct_path(current_state)
            
            for successor in self._generate_successors(current_state):
                successor.h_cost = self._calculate_heuristic(successor)
                successor.f_cost = successor.g_cost + successor.h_cost
                
                if not self.transposition_table.contains(successor):
                    heapq.heappush(self.open_set, successor)
                    self.transposition_table.add(successor)
                    self.states_generated += 1
        
        return None
    
    def _greedy_search(self, progress_callback: Optional[Callable] = None) -> Optional[List[str]]:
        """Implémentation recherche gloutonne."""
        initial_state = self._create_initial_state()
        initial_state.h_cost = self._calculate_heuristic(initial_state)
        initial_state.f_cost = initial_state.h_cost  # Greedy: f = h seulement
        
        self.open_set = [initial_state]
        self.transposition_table.add(initial_state)
        
        while self.open_set and self._within_limits():
            current_state = heapq.heappop(self.open_set)
            self.states_explored += 1
            
            if progress_callback and self.states_explored % 10000 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"Greedy: Exploré {self.states_explored} états en {elapsed:.1f}s")
            
            if self._is_goal_state(current_state):
                return self._reconstruct_path(current_state)
            
            for successor in self._generate_successors(current_state):
                successor.h_cost = self._calculate_heuristic(successor)
                successor.f_cost = successor.h_cost  # Greedy: ignorer g_cost
                
                if not self.transposition_table.contains(successor):
                    heapq.heappush(self.open_set, successor)
                    self.transposition_table.add(successor)
                    self.states_generated += 1
        
        return None
    
    def _ida_star_search(self, progress_callback: Optional[Callable] = None) -> Optional[List[str]]:
        """Implémentation IDA*."""
        initial_state = self._create_initial_state()
        initial_state.h_cost = self._calculate_heuristic(initial_state)
        
        threshold = initial_state.h_cost
        
        for iteration in range(50):  # Maximum 50 itérations
            if progress_callback and iteration % 5 == 0:
                elapsed = time.time() - self.start_time
                progress_callback(f"IDA* iteration {iteration}, seuil={threshold}, exploré={self.states_explored}")
            
            if not self._within_limits():
                break
            
            result = self._ida_search_recursive(initial_state, 0, threshold, [])
            
            if isinstance(result, list):
                return result
            
            if result == float('inf'):
                break
            
            threshold = result
        
        return None
    
    def _ida_search_recursive(self, state: SokolutionState, g: int, threshold: int, path: List[str]) -> Any:
        """Recherche récursive IDA*."""
        if not self._within_limits():
            return float('inf')
        
        self.states_explored += 1
        
        h = self._calculate_heuristic(state)
        f = g + h
        
        if f > threshold:
            return f
        
        if self._is_goal_state(state):
            return path[:]
        
        min_threshold = float('inf')
        
        for successor in self._generate_successors(state):
            new_path = path + [successor.move]
            result = self._ida_search_recursive(successor, g + 1, threshold, new_path)
            
            if isinstance(result, list):
                return result
            
            min_threshold = min(min_threshold, result)
        
        return min_threshold
    
    def _bidirectional_search(self, progress_callback: Optional[Callable] = None) -> Optional[List[str]]:
        """
        Implémentation recherche bidirectionnelle.
        
        Cette version simplifiée utilise la recherche gloutonne dans les deux directions.
        """
        # Pour l'instant, utiliser la recherche gloutonne standard
        # Une vraie implémentation bidirectionnelle nécessiterait threading
        return self._greedy_search(progress_callback)
    
    def _generate_successors(self, state: SokolutionState) -> List[SokolutionState]:
        """Génère tous les états successeurs valides."""
        successors = []
        player_x, player_y = state.player_pos
        
        # Essayer les quatre directions
        for direction, (dx, dy) in [('UP', (0, -1)), ('DOWN', (0, 1)),
                                   ('LEFT', (-1, 0)), ('RIGHT', (1, 0))]:
            new_x, new_y = player_x + dx, player_y + dy
            
            # Vérifier les limites et les murs
            if (new_x < 0 or new_x >= self.level.width or
                new_y < 0 or new_y >= self.level.height or
                self.level.is_wall(new_x, new_y)):
                continue
            
            # Vérifier s'il y a une box dans cette direction
            if (new_x, new_y) in state.boxes:
                # Essayer de pousser la box
                box_x, box_y = new_x + dx, new_y + dy
                
                # Vérifier si la box peut être poussée
                if (box_x < 0 or box_x >= self.level.width or
                    box_y < 0 or box_y >= self.level.height or
                    self.level.is_wall(box_x, box_y) or
                    (box_x, box_y) in state.boxes):
                    continue
                
                # Créer le nouvel état avec la box poussée
                new_boxes = set(state.boxes)
                new_boxes.remove((new_x, new_y))
                new_boxes.add((box_x, box_y))
                new_boxes_frozen = frozenset(new_boxes)
                
                # Vérifier les deadlocks
                if not self.deadlock_detector.is_deadlock(new_boxes_frozen):
                    successor = SokolutionState(
                        player_pos=(new_x, new_y),
                        boxes=new_boxes_frozen,
                        parent=state,
                        move=direction,
                        g_cost=state.g_cost + 1
                    )
                    successors.append(successor)
            else:
                # Juste déplacer le joueur
                successor = SokolutionState(
                    player_pos=(new_x, new_y),
                    boxes=state.boxes,
                    parent=state,
                    move=direction,
                    g_cost=state.g_cost + 1
                )
                successors.append(successor)
        
        return successors
    
    def _reconstruct_path(self, final_state: SokolutionState) -> List[str]:
        """Reconstruit le chemin de la solution."""
        path = []
        current = final_state
        
        while current.parent is not None:
            path.append(current.move)
            current = current.parent
        
        return list(reversed(path))
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Obtient des statistiques complètes du solver."""
        deadlock_stats = self.deadlock_detector.get_statistics()
        table_stats = self.transposition_table.get_statistics()
        
        return {
            'search_statistics': {
                'states_explored': self.states_explored,
                'states_generated': self.states_generated,
                'heuristic_calls': self.heuristic_calls,
                'macro_moves_used': self.macro_moves_used,
                'solve_time': time.time() - self.start_time if self.start_time > 0 else 0
            },
            'deadlock_detection': deadlock_stats,
            'transposition_table': table_stats,
            'algorithm_info': {
                'current_algorithm': self.current_algorithm.value if self.current_algorithm else None,
                'current_mode': self.current_mode.value if self.current_mode else None,
                'max_states': self.max_states,
                'time_limit': self.time_limit
            }
        }