"""
FESS Enhanced Features System
============================

Implémentation des 4 features FESS optimisées selon les documents de recherche :
1. Packing Feature - Boîtes packées selon le packing plan
2. Connectivity Feature - Régions déconnectées optimisé
3. Room Connectivity Feature - Passages rooms obstrués  
4. Out-of-Plan Feature - Boîtes interfèrent avec le plan

Référence: "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
"""

from typing import Dict, List, Tuple, Set, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import deque

from src.core.level import Level
from src.core.sokoban_state import SokobanState


class FESSFeatureType(Enum):
    """Types de features FESS selon le document de recherche."""
    PACKING = "packing"
    CONNECTIVITY = "connectivity" 
    ROOM_CONNECTIVITY = "room_connectivity"
    OUT_OF_PLAN = "out_of_plan"


@dataclass
class FESSFeatureVector:
    """Vecteur de features FESS 4D."""
    packing: int
    connectivity: int
    room_connectivity: int
    out_of_plan: int
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Convertit en tuple pour utilisation comme clé de cellule."""
        return (self.packing, self.connectivity, self.room_connectivity, self.out_of_plan)
    
    def __str__(self) -> str:
        return f"({self.packing},{self.connectivity},{self.room_connectivity},{self.out_of_plan})"


class ConnectedRegion:
    """Représente une région connectée sur le plateau."""
    
    def __init__(self, squares: Set[Tuple[int, int]]):
        self.squares = squares
        self.size = len(squares)
        
    def contains_player(self, player_pos: Tuple[int, int]) -> bool:
        """Vérifie si le joueur est dans cette région."""
        return player_pos in self.squares
    
    def is_accessible_from(self, start_pos: Tuple[int, int], 
                          walls: Set[Tuple[int, int]], 
                          boxes: Set[Tuple[int, int]]) -> bool:
        """Vérifie si la région est accessible depuis une position."""
        if start_pos in self.squares:
            return True
        
        # BFS pour vérifier la connectivité
        visited = {start_pos}
        queue = deque([start_pos])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) in visited:
                    continue
                if (nx, ny) in walls or (nx, ny) in boxes:
                    continue
                if (nx, ny) in self.squares:
                    return True
                    
                visited.add((nx, ny))
                queue.append((nx, ny))
        
        return False


class FESSEnhancedFeatures:
    """
    Système de features FESS amélioré conforme aux documents de recherche.
    
    Implémente les 4 features clés avec optimisations pour performance :
    - Packing Feature avec support du packing plan
    - Connectivity Feature optimisé  
    - Room Connectivity Feature (nouveau)
    - Out-of-Plan Feature (nouveau)
    """
    
    def __init__(self, level: Level):
        self.level = level
        self.width = level.width
        self.height = level.height
        
        # Caches pour optimisation
        self._walls_cache = None
        self._targets_cache = None
        self._connectivity_cache = {}
        self._room_graph_cache = None
        
        # Configuration features
        self.packing_plan_order = None  # Sera défini par le packing plan
        self.sink_room_basin = None     # Sera défini par l'analyse basin
        
        # Pré-calculs
        self._precompute_static_data()
    
    def _precompute_static_data(self):
        """Pré-calcule les données statiques du niveau."""
        # Cache des murs
        self._walls_cache = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.level.get_cell(x, y) == '#':
                    self._walls_cache.add((x, y))
        
        # Cache des targets
        self._targets_cache = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.level.get_cell(x, y) in ['.', '*', '+']:
                    self._targets_cache.add((x, y))
    
    def compute_feature_vector(self, state: SokobanState) -> FESSFeatureVector:
        """
        Calcule le vecteur de features FESS 4D pour un état.
        
        Args:
            state: État Sokoban à analyser
            
        Returns:
            Vecteur de features FESS
        """
        packing = self._compute_packing_feature(state)
        connectivity = self._compute_connectivity_feature(state)
        room_connectivity = self._compute_room_connectivity_feature(state)
        out_of_plan = self._compute_out_of_plan_feature(state)
        
        return FESSFeatureVector(
            packing=packing,
            connectivity=connectivity,
            room_connectivity=room_connectivity,
            out_of_plan=out_of_plan
        )
    
    def _compute_packing_feature(self, state: SokobanState) -> int:
        """
        Calcule la Packing Feature selon le document de recherche.
        
        "This feature counts the number of boxes that have reached a target.
        However, for many Sokoban problems the order that the boxes are moved
        to their destination squares can be critical. A pre-search is done using
        retrograde analysis to determine a plausible ordering."
        
        Returns:
            Nombre de boîtes packées selon l'ordre optimal
        """
        if self.packing_plan_order is None:
            # Fallback : simple comptage des boîtes sur targets
            packed_count = 0
            for box_pos in state.box_positions:
                if box_pos in self._targets_cache:
                    packed_count += 1
            return packed_count
        
        # Utilise l'ordre du packing plan pour un comptage précis
        packed_count = 0
        for target_pos in self.packing_plan_order:
            if target_pos in state.box_positions:
                packed_count += 1
            else:
                # L'ordre est critique : si une boîte manque, on s'arrête
                break
        
        return packed_count
    
    def _compute_connectivity_feature(self, state: SokobanState) -> int:
        """
        Calcule la Connectivity Feature optimisée.
        
        "Usually, the boxes divide the board into closed regions. The player can
        move around freely within a region, but cannot move to another region
        without first pushing boxes. A connectivity of one means that the player
        can move anywhere on the board."
        
        Returns:
            Nombre de régions déconnectées
        """
        # Utilise le cache si possible
        boxes_tuple = tuple(sorted(state.box_positions))
        if boxes_tuple in self._connectivity_cache:
            return self._connectivity_cache[boxes_tuple]
        
        # Calcule les régions connectées
        regions = self._find_connected_regions(state)
        connectivity = len(regions)
        
        # Met en cache le résultat
        self._connectivity_cache[boxes_tuple] = connectivity
        
        return connectivity
    
    def _find_connected_regions(self, state: SokobanState) -> List[ConnectedRegion]:
        """Trouve toutes les régions connectées sur le plateau."""
        visited = set()
        regions = []
        
        # Obstacles : murs + boîtes
        obstacles = self._walls_cache | set(state.box_positions)
        
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in visited and (x, y) not in obstacles:
                    # Nouvelle région trouvée
                    region_squares = self._flood_fill_region((x, y), obstacles, visited)
                    if region_squares:
                        regions.append(ConnectedRegion(region_squares))
        
        return regions
    
    def _flood_fill_region(self, start: Tuple[int, int], 
                          obstacles: Set[Tuple[int, int]], 
                          global_visited: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Effectue un flood fill pour trouver une région connectée."""
        if start in obstacles or start in global_visited:
            return set()
        
        region = set()
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in region or (x, y) in obstacles:
                continue
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
                
            region.add((x, y))
            global_visited.add((x, y))
            
            # Ajoute les voisins
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in region:
                    queue.append((nx, ny))
        
        return region
    
    def _compute_room_connectivity_feature(self, state: SokobanState) -> int:
        """
        Calcule la Room Connectivity Feature (nouveau dans FESS).
        
        "Room connectivity is related to the connectivity idea. Sokoban levels
        are often composed of rooms linked by tunnels. The room connectivity
        feature counts how many room links are obstructed by boxes."
        
        Returns:
            Nombre de passages entre rooms obstrués
        """
        if self._room_graph_cache is None:
            # Analyse des rooms sera implémentée dans fess_room_analysis.py
            # Pour l'instant, retourne 0 (sera mis à jour plus tard)
            return 0
        
        # TODO: Implémenter l'analyse complète des passages rooms
        # Pour l'instant, approximation basée sur la connectivity
        base_connectivity = self._compute_connectivity_feature(state)
        return max(0, base_connectivity - 1)
    
    def _compute_out_of_plan_feature(self, state: SokobanState) -> int:
        """
        Calcule la Out-of-Plan Feature (nouveau dans FESS).
        
        "As packing proceeds, some areas of the board may become blocked.
        The out-of-plan feature counts the number of boxes in soon-to-be-blocked
        areas. This number should be minimized."
        
        Returns:
            Nombre de boîtes "out of plan"
        """
        if self.sink_room_basin is None:
            # Sans analyse basin, approximation simple
            return self._count_problematic_boxes(state)
        
        # Compte les boîtes hors du basin et non packées
        oop_count = 0
        for box_pos in state.box_positions:
            if (box_pos not in self.sink_room_basin and 
                box_pos not in self._targets_cache):
                oop_count += 1
        
        return oop_count
    
    def _count_problematic_boxes(self, state: SokobanState) -> int:
        """Approximation simple des boîtes problématiques."""
        problematic = 0
        
        for box_pos in state.box_positions:
            if box_pos in self._targets_cache:
                continue  # Boîte déjà packée
            
            # Vérifie si la boîte peut encore atteindre des targets
            reachable_targets = self._count_reachable_targets(box_pos, state)
            if reachable_targets == 0:
                problematic += 1
        
        return problematic
    
    def _count_reachable_targets(self, box_pos: Tuple[int, int], 
                                state: SokobanState) -> int:
        """Compte les targets atteignables depuis une position de boîte."""
        reachable = 0
        obstacles = self._walls_cache | set(state.box_positions) - {box_pos}
        
        for target_pos in self._targets_cache:
            if target_pos in state.box_positions:
                continue  # Target déjà occupée
            
            if self._is_path_clear(box_pos, target_pos, obstacles):
                reachable += 1
        
        return reachable
    
    def _is_path_clear(self, start: Tuple[int, int], 
                      end: Tuple[int, int], 
                      obstacles: Set[Tuple[int, int]]) -> bool:
        """Vérifie s'il existe un chemin libre entre deux positions."""
        if start == end:
            return True
        
        visited = {start}
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) == end:
                    return True
                
                if ((nx, ny) in visited or (nx, ny) in obstacles or
                    nx < 0 or nx >= self.width or ny < 0 or ny >= self.height):
                    continue
                
                visited.add((nx, ny))
                queue.append((nx, ny))
        
        return False
    
    def set_packing_plan(self, packing_order: List[Tuple[int, int]]):
        """Définit l'ordre de packing déterminé par l'analyse rétrograde."""
        self.packing_plan_order = packing_order
    
    def set_sink_room_basin(self, basin_squares: Set[Tuple[int, int]]):
        """Définit le basin du sink room pour la feature Out-of-Plan."""
        self.sink_room_basin = basin_squares
    
    def get_feature_progression_direction(self, 
                                        current: FESSFeatureVector, 
                                        goal: FESSFeatureVector) -> Dict[FESSFeatureType, int]:
        """
        Détermine la direction de progression nécessaire pour chaque feature.
        
        Returns:
            Dict indiquant si chaque feature doit augmenter (+1), diminuer (-1) ou rester (0)
        """
        return {
            FESSFeatureType.PACKING: 1 if current.packing < goal.packing else 0,
            FESSFeatureType.CONNECTIVITY: -1 if current.connectivity > goal.connectivity else 0,
            FESSFeatureType.ROOM_CONNECTIVITY: -1 if current.room_connectivity > goal.room_connectivity else 0,
            FESSFeatureType.OUT_OF_PLAN: -1 if current.out_of_plan > goal.out_of_plan else 0
        }
    
    def compute_feature_distance(self, 
                               current: FESSFeatureVector, 
                               goal: FESSFeatureVector) -> float:
        """
        Calcule une distance dans l'espace des features.
        
        Utilisé pour l'ordering lexicographique selon le document :
        1. OOP (priorité absolue)
        2. Packed boxes
        3. Connectivity
        4. Room connectivity
        """
        # Ordre lexicographique prioritaire
        if current.out_of_plan != goal.out_of_plan:
            return abs(current.out_of_plan - goal.out_of_plan) * 1000
        if current.packing != goal.packing:
            return abs(current.packing - goal.packing) * 100
        if current.connectivity != goal.connectivity:
            return abs(current.connectivity - goal.connectivity) * 10
        return abs(current.room_connectivity - goal.room_connectivity)
    
    def is_progress_towards_goal(self, 
                               old_features: FESSFeatureVector,
                               new_features: FESSFeatureVector,
                               goal_features: FESSFeatureVector) -> bool:
        """Vérifie si les nouvelles features représentent un progrès vers le but."""
        old_distance = self.compute_feature_distance(old_features, goal_features)
        new_distance = self.compute_feature_distance(new_features, goal_features)
        return new_distance < old_distance


def create_goal_features(num_boxes: int) -> FESSFeatureVector:
    """
    Crée le vecteur de features pour l'état but.
    
    État but: toutes les boîtes packées, connectivité minimale, pas de OOP.
    """
    return FESSFeatureVector(
        packing=num_boxes,      # Toutes les boîtes packées
        connectivity=1,         # Connectivité minimale
        room_connectivity=0,    # Aucun passage obstrué
        out_of_plan=0          # Aucune boîte out-of-plan
    )


# Fonctions utilitaires pour l'interface avec l'algorithme FESS
def features_to_cell_key(features: FESSFeatureVector) -> Tuple[int, int, int, int]:
    """Convertit un vecteur de features en clé de cellule Feature Space."""
    return features.to_tuple()


def cell_key_to_features(cell_key: Tuple[int, int, int, int]) -> FESSFeatureVector:
    """Convertit une clé de cellule en vecteur de features."""
    return FESSFeatureVector(*cell_key)