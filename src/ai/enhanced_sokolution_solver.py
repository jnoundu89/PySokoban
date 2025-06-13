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
import numpy as np


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


class FeatureExtractor:
    """
    Extracteur de features pour l'algorithme FESS (Feature Space Search).
    
    Basé sur Shoham and Schaeffer [2020], cet extracteur calcule des features
    sophistiquées pour guider la recherche dans l'espace des états Sokoban.
    """
    
    def __init__(self, level):
        self.level = level
        self.width = level.width
        self.height = level.height
        self.targets = set(level.targets)
        
        # Précalculs pour optimiser l'extraction de features
        self._precompute_topology_features()
        
    def _precompute_topology_features(self):
        """Précalcule les features topologiques statiques du niveau."""
        self.wall_density = self._calculate_wall_density()
        self.corridor_map = self._calculate_corridor_map()
        self.deadlock_zones = self._calculate_deadlock_zones()
        self.target_connectivity = self._calculate_target_connectivity()
        
    def _calculate_wall_density(self) -> float:
        """Calcule la densité de murs dans le niveau."""
        total_cells = self.width * self.height
        wall_count = sum(1 for y in range(self.height) for x in range(self.width)
                        if self.level.is_wall(x, y))
        return wall_count / total_cells if total_cells > 0 else 0
        
    def _calculate_corridor_map(self) -> Dict[Tuple[int, int], bool]:
        """Identifie les cellules qui sont dans des corridors."""
        corridor_map = {}
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y):
                    corridor_map[(x, y)] = self._is_corridor_cell(x, y)
        return corridor_map
        
    def _is_corridor_cell(self, x: int, y: int) -> bool:
        """Vérifie si une cellule fait partie d'un corridor."""
        if self.level.is_wall(x, y):
            return False
            
        # Compter les murs adjacents
        adjacent_walls = sum(1 for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]
                           if self.level.is_wall(x + dx, y + dy))
        
        # Un corridor a typiquement 2 murs adjacents
        return adjacent_walls >= 2
        
    def _calculate_deadlock_zones(self) -> Set[Tuple[int, int]]:
        """Identifie les zones de deadlock potentielles."""
        deadlock_zones = set()
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y) and (x, y) not in self.targets:
                    if self._is_potential_deadlock_zone(x, y):
                        deadlock_zones.add((x, y))
        return deadlock_zones
        
    def _is_potential_deadlock_zone(self, x: int, y: int) -> bool:
        """Vérifie si une position est une zone de deadlock potentielle."""
        # Coins sans target
        corner_patterns = [
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y-1)),
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y-1)),
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y+1)),
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y+1))
        ]
        return any(corner_patterns)
        
    def _calculate_target_connectivity(self) -> Dict[Tuple[int, int], int]:
        """Calcule la connectivité de chaque target."""
        connectivity = {}
        for target in self.targets:
            x, y = target
            # Compter les directions libres depuis cette target
            free_directions = sum(1 for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]
                                if not self.level.is_wall(x + dx, y + dy))
            connectivity[target] = free_directions
        return connectivity
        
    def extract_features(self, state: 'SokolutionState') -> np.ndarray:
        """
        Extrait un vecteur de features complet de l'état.
        
        Returns:
            np.ndarray: Vecteur de features normalisé
        """
        features = []
        
        # 1. Features de base
        features.extend(self._extract_basic_features(state))
        
        # 2. Features géométriques
        features.extend(self._extract_geometric_features(state))
        
        # 3. Features topologiques
        features.extend(self._extract_topological_features(state))
        
        # 4. Features de progès
        features.extend(self._extract_progress_features(state))
        
        # 5. Features de connectivité
        features.extend(self._extract_connectivity_features(state))
        
        return np.array(features, dtype=np.float32)
        
    def _extract_basic_features(self, state: 'SokolutionState') -> List[float]:
        """Features de base : positions et comptages."""
        features = []
        
        # Position du joueur normalisée
        px, py = state.player_pos
        features.extend([px / self.width, py / self.height])
        
        # Nombre de boxes sur targets
        boxes_on_targets = len([box for box in state.boxes if box in self.targets])
        features.append(boxes_on_targets / max(len(self.targets), 1))
        
        # Nombre de boxes pas sur targets
        boxes_off_targets = len(state.boxes) - boxes_on_targets
        features.append(boxes_off_targets / max(len(state.boxes), 1))
        
        return features
        
    def _extract_geometric_features(self, state: 'SokolutionState') -> List[float]:
        """Features géométriques : distances et dispersions."""
        features = []
        boxes = list(state.boxes)
        
        if not boxes:
            return [0.0] * 6  # Padding si pas de boxes
            
        # Centre de masse des boxes
        center_x = sum(box[0] for box in boxes) / len(boxes)
        center_y = sum(box[1] for box in boxes) / len(boxes)
        features.extend([center_x / self.width, center_y / self.height])
        
        # Dispersion des boxes
        if len(boxes) > 1:
            variance_x = sum((box[0] - center_x) ** 2 for box in boxes) / len(boxes)
            variance_y = sum((box[1] - center_y) ** 2 for box in boxes) / len(boxes)
            dispersion = (variance_x + variance_y) / (self.width * self.height)
        else:
            dispersion = 0
        features.append(dispersion)
        
        # Distance moyenne joueur-boxes
        if boxes:
            avg_distance = sum(abs(px - box[0]) + abs(py - box[1])
                              for box in boxes for px, py in [state.player_pos]) / len(boxes)
            max_distance = max(self.width + self.height, 1)
            features.append(avg_distance / max_distance)
        else:
            features.append(0.0)
        
        # Distance minimale aux targets pour boxes non placées
        unplaced_boxes = [box for box in boxes if box not in self.targets]
        if unplaced_boxes and self.targets:
            min_distances = []
            for box in unplaced_boxes:
                min_dist = min(abs(box[0] - target[0]) + abs(box[1] - target[1])
                              for target in self.targets)
                min_distances.append(min_dist)
            avg_min_distance = sum(min_distances) / max(len(min_distances), 1)
            features.append(avg_min_distance / max(max_distance, 1))
        else:
            features.append(0.0)
        
        # Compacité (ratio périmètre/aire)
        compactness = self._calculate_box_compactness(boxes)
        features.append(compactness)
        
        return features
        
    def _extract_topological_features(self, state: 'SokolutionState') -> List[float]:
        """Features topologiques : structure et contraintes."""
        features = []
        
        # Boxes dans des corridors
        boxes_in_corridors = sum(1 for box in state.boxes
                               if self.corridor_map.get(box, False))
        corridor_ratio = boxes_in_corridors / len(state.boxes) if state.boxes else 0
        features.append(corridor_ratio)
        
        # Boxes dans des zones de deadlock
        boxes_in_deadlock_zones = sum(1 for box in state.boxes
                                    if box in self.deadlock_zones)
        deadlock_ratio = boxes_in_deadlock_zones / len(state.boxes) if state.boxes else 0
        features.append(deadlock_ratio)
        
        # Densité locale autour du joueur
        px, py = state.player_pos
        local_density = self._calculate_local_density(px, py, state.boxes)
        features.append(local_density)
        
        return features
        
    def _extract_progress_features(self, state: 'SokolutionState') -> List[float]:
        """Features de progrès : évaluation de l'avancement."""
        features = []
        
        # Progression globale (boxes sur targets)
        progress = len([box for box in state.boxes if box in self.targets]) / max(len(self.targets), 1)
        features.append(progress)
        
        # Potentiel d'amélioration
        unplaced_boxes = [box for box in state.boxes if box not in self.targets]
        improvement_potential = self._calculate_improvement_potential(unplaced_boxes)
        features.append(improvement_potential)
        
        return features
        
    def _extract_connectivity_features(self, state: 'SokolutionState') -> List[float]:
        """Features de connectivité : accessibilité et mobilité."""
        features = []
        
        # Accessibilité du joueur
        player_connectivity = self._calculate_player_connectivity(state)
        features.append(player_connectivity)
        
        # Mobilité moyenne des boxes
        box_mobility = self._calculate_average_box_mobility(state)
        features.append(box_mobility)
        
        return features
        
    def _calculate_box_compactness(self, boxes: List[Tuple[int, int]]) -> float:
        """Calcule la compacité d'un groupe de boxes."""
        if len(boxes) <= 1:
            return 1.0
            
        # Calculer l'enveloppe convexe simplifiée (bounding box)
        min_x = min(box[0] for box in boxes)
        max_x = max(box[0] for box in boxes)
        min_y = min(box[1] for box in boxes)
        max_y = max(box[1] for box in boxes)
        
        area = (max_x - min_x + 1) * (max_y - min_y + 1)
        return len(boxes) / area if area > 0 else 0
        
    def _calculate_local_density(self, x: int, y: int, boxes: FrozenSet[Tuple[int, int]]) -> float:
        """Calcule la densité locale autour d'une position."""
        radius = 2
        local_count = 0
        total_count = 0
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    total_count += 1
                    if (nx, ny) in boxes:
                        local_count += 1
        
        return local_count / total_count if total_count > 0 else 0
        
    def _calculate_improvement_potential(self, unplaced_boxes: List[Tuple[int, int]]) -> float:
        """Calcule le potentiel d'amélioration pour les boxes non placées."""
        if not unplaced_boxes or not self.targets:
            return 0.0
            
        # Basé sur la facilité d'accès aux targets
        total_potential = 0
        for box in unplaced_boxes:
            # Trouver la target la plus proche
            min_distance = min(abs(box[0] - target[0]) + abs(box[1] - target[1])
                             for target in self.targets)
            # Potentiel inversement proportionnel à la distance
            potential = 1.0 / (1.0 + min_distance)
            total_potential += potential
            
        return total_potential / max(len(unplaced_boxes), 1)
        
    def _calculate_player_connectivity(self, state: 'SokolutionState') -> float:
        """Calcule la connectivité du joueur."""
        px, py = state.player_pos
        reachable_count = 0
        total_count = 0
        
        # BFS simple pour compter les positions accessibles
        visited = set()
        queue = deque([(px, py)])
        visited.add((px, py))
        
        while queue and len(visited) < 100:  # Limiter pour la performance
            x, y = queue.popleft()
            reachable_count += 1
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    not self.level.is_wall(nx, ny) and (nx, ny) not in state.boxes and
                    (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        # Compter le total d'espaces libres
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y):
                    total_count += 1
        
        return reachable_count / total_count if total_count > 0 else 0
        
    def _calculate_average_box_mobility(self, state: 'SokolutionState') -> float:
        """Calcule la mobilité moyenne des boxes."""
        if not state.boxes:
            return 0.0
            
        total_mobility = 0
        for box in state.boxes:
            mobility = self._calculate_box_mobility(box, state.boxes)
            total_mobility += mobility
            
        return total_mobility / max(len(state.boxes), 1)
        
    def _calculate_box_mobility(self, box: Tuple[int, int], boxes: FrozenSet[Tuple[int, int]]) -> float:
        """Calcule la mobilité d'une box individuelle."""
        x, y = box
        free_directions = 0
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            # Vérifier si la box peut potentiellement bouger dans cette direction
            if (0 <= nx < self.width and 0 <= ny < self.height and
                not self.level.is_wall(nx, ny) and (nx, ny) not in boxes):
                free_directions += 1
                
        return free_directions / 4.0  # Normaliser par le nombre max de directions


class FESSHeuristic:
    """
    Heuristique FESS utilisant les features extraites pour estimer la distance au goal.
    """
    
    def __init__(self, level):
        self.level = level
        self.feature_extractor = FeatureExtractor(level)
        
        # Poids appris/configurés pour les différentes features
        self.feature_weights = self._initialize_feature_weights()
        
    def _initialize_feature_weights(self) -> np.ndarray:
        """
        Initialise les poids des features.
        
        Dans une implémentation complète, ces poids seraient appris par ML.
        Ici, on utilise des poids heuristiques basés sur l'expérience.
        """
        # Nombre total de features estimé
        num_features = 15  # À ajuster selon le nombre réel de features
        
        # Poids heuristiques (à affiner empiriquement)
        weights = np.array([
            # Basic features (4)
            0.1, 0.1,  # position joueur
            -10.0,     # boxes sur targets (négatif car on veut maximiser)
            2.0,       # boxes pas sur targets
            
            # Geometric features (6)
            0.5, 0.5,  # centre de masse
            1.0,       # dispersion
            1.5,       # distance joueur-boxes
            3.0,       # distance boxes-targets
            0.8,       # compacité
            
            # Topological features (3)
            2.0,       # boxes dans corridors
            5.0,       # boxes dans zones deadlock
            1.0,       # densité locale
            
            # Progress features (2)
            -8.0,      # progression (négatif car on veut maximiser)
            -2.0,      # potentiel d'amélioration
            
            # Connectivity features (2)
            -1.0,      # connectivité joueur
            -1.5       # mobilité boxes
        ], dtype=np.float32)
        
        return weights[:num_features] if len(weights) > num_features else weights
        
    def calculate_heuristic(self, state: 'SokolutionState') -> float:
        """Calcule la valeur heuristique basée sur les features."""
        features = self.feature_extractor.extract_features(state)
        
        # Assurer que les dimensions correspondent
        min_len = min(len(features), len(self.feature_weights))
        features_trimmed = features[:min_len]
        weights_trimmed = self.feature_weights[:min_len]
        
        # Produit scalaire pour obtenir la valeur heuristique
        heuristic_value = np.dot(features_trimmed, weights_trimmed)
        
        # S'assurer que la valeur est positive et raisonnable
        return max(0.0, float(heuristic_value))


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
            level_complexity = len(self.level.boxes) * self.level.width * self.level.height
            progress_callback(f"🔍 Démarrage solver {algorithm.value} (mode {mode.value}) - Complexité: {level_complexity}")
        
        # Sélection de l'algorithme de recherche
        if algorithm == Algorithm.FESS:
            solution_moves = self._fess_search(progress_callback)
        elif algorithm == Algorithm.BFS:
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
    
    def _fess_search(self, progress_callback: Optional[Callable] = None) -> Optional[List[str]]:
        """
        Implémentation du vrai algorithme FESS (Feature Space Search).
        
        Basé sur Shoham and Schaeffer [2020] - implémentation authentique
        qui utilise l'espace de features 4D et les advisors domain-spécifiques.
        """
        if progress_callback:
            progress_callback("🔬 Initialisation du vrai FESS (Shoham & Schaeffer 2020)")
        
        # Utiliser le vrai moteur de recherche FESS
        from .authentic_fess import FESSSearchEngine
        
        fess_engine = FESSSearchEngine(
            level=self.level,
            max_states=self.max_states,
            time_limit=self.time_limit
        )
        
        # Lancer la recherche authentique FESS
        solution_moves = fess_engine.search(progress_callback)
        
        # Mettre à jour nos métriques avec celles du moteur FESS
        fess_stats = fess_engine.get_statistics()
        self.states_explored = fess_stats['search_statistics']['states_explored']
        self.states_generated = fess_stats['search_statistics']['states_generated']
        
        return solution_moves
    
    def _adapt_fess_parameters(self, current_state: SokolutionState,
                              last_best_h: float, stagnation_counter: int) -> float:
        """
        Adapte dynamiquement les paramètres FESS basé sur le progrès.
        
        Cette fonction ajuste les poids et stratégies selon la performance
        de la recherche actuelle.
        """
        base_factor = 1.0
        
        # Si on stagne, augmenter l'exploration
        if stagnation_counter > 500:
            base_factor *= 1.2  # Augmenter l'exploration
        elif stagnation_counter > 1000:
            base_factor *= 1.5  # Exploration plus agressive
        
        # Si on progresse bien, rester concentré
        if current_state.h_cost < last_best_h:
            base_factor *= 0.9  # Rester plus concentré
        
        # Adaptation basée sur la profondeur
        depth_factor = 1.0 + (current_state.g_cost * 0.001)
        
        return base_factor * depth_factor
    
    def _apply_fess_bonuses(self, state: SokolutionState, feature_extractor: FeatureExtractor):
        """
        Applique des bonus/malus spécifiques FESS basés sur les features.
        """
        # Bonus pour les configurations prometteuses
        boxes_on_targets = len([box for box in state.boxes if box in self.level.targets])
        total_boxes = len(state.boxes)
        
        if total_boxes > 0:
            progress_ratio = boxes_on_targets / total_boxes
            
            # Bonus significatif si beaucoup de progrès
            if progress_ratio > 0.8:
                state.f_cost *= 0.5  # Forte priorité
            elif progress_ratio > 0.6:
                state.f_cost *= 0.8  # Priorité modérée
        
        # Malus pour les positions dangereuses (deadlocks potentiels)
        dangerous_boxes = sum(1 for box in state.boxes
                            if box in feature_extractor.deadlock_zones)
        if dangerous_boxes > 0:
            danger_ratio = dangerous_boxes / total_boxes
            state.f_cost *= (1.0 + danger_ratio * 2.0)  # Pénaliser les configurations dangereuses
        
        # Bonus pour la mobilité du joueur
        player_connectivity = feature_extractor._calculate_player_connectivity(state)
        if player_connectivity > 0.7:
            state.f_cost *= 0.95  # Léger bonus pour bonne connectivité
    
    # Les autres implémentations d'algorithmes suivent...
    
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