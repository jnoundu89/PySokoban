"""
FESS Room Analysis System
=========================

Implémentation de l'analyse des rooms selon les documents de recherche.

"Sokoban levels are usually composed of rooms connected by corridors or tunnels.
For a human player it is obvious what a room is: a spacious place in which boxes
can be stored and the player can move around freely. Defining it formally, however,
proved slightly tricky. In the end, we settled for this definition: 
A room is a connected area of 2x3 squares."

"Room connectivity is related to the connectivity idea. The room connectivity
feature counts how many room links are obstructed by boxes."

Référence: "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
"""

from typing import Dict, List, Set, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from collections import defaultdict, deque
import numpy as np

from src.core.level import Level
from src.core.sokoban_state import SokobanState


@dataclass
class Room:
    """Représente une room dans le niveau Sokoban."""
    id: int
    squares: Set[Tuple[int, int]]
    center: Tuple[int, int]
    area: int
    
    def __post_init__(self):
        self.area = len(self.squares)
        if not self.center:
            # Calcule le centre géométrique
            if self.squares:
                x_coords = [x for x, y in self.squares]
                y_coords = [y for x, y in self.squares]
                self.center = (sum(x_coords) // len(x_coords), 
                              sum(y_coords) // len(y_coords))
    
    def contains_position(self, pos: Tuple[int, int]) -> bool:
        """Vérifie si une position est dans cette room."""
        return pos in self.squares
    
    def get_boundary_squares(self) -> Set[Tuple[int, int]]:
        """Retourne les carrés à la frontière de la room."""
        boundary = set()
        for x, y in self.squares:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in self.squares:
                    boundary.add((x, y))
                    break
        return boundary


@dataclass
class RoomConnection:
    """Représente une connexion entre deux rooms."""
    room1_id: int
    room2_id: int
    passage_squares: List[Tuple[int, int]]
    is_tunnel: bool  # True si c'est un tunnel étroit, False si passage large
    
    def get_connection_key(self) -> Tuple[int, int]:
        """Retourne une clé unique pour cette connexion."""
        return tuple(sorted([self.room1_id, self.room2_id]))
    
    def is_obstructed_by_boxes(self, box_positions: Set[Tuple[int, int]]) -> bool:
        """Vérifie si cette connexion est obstruée par des boîtes."""
        for passage_square in self.passage_squares:
            if passage_square in box_positions:
                return True
        return False


class RoomGraph:
    """Graphe représentant les connexions entre rooms."""
    
    def __init__(self):
        self.rooms: Dict[int, Room] = {}
        self.connections: List[RoomConnection] = []
        self.adjacency_matrix: Optional[np.ndarray] = None
        self._connection_map: Dict[Tuple[int, int], RoomConnection] = {}
    
    def add_room(self, room: Room):
        """Ajoute une room au graphe."""
        self.rooms[room.id] = room
    
    def add_connection(self, connection: RoomConnection):
        """Ajoute une connexion entre rooms."""
        self.connections.append(connection)
        self._connection_map[connection.get_connection_key()] = connection
    
    def build_adjacency_matrix(self):
        """Construit la matrice d'adjacence des rooms."""
        num_rooms = len(self.rooms)
        if num_rooms == 0:
            return
        
        self.adjacency_matrix = np.zeros((num_rooms, num_rooms), dtype=int)
        
        for connection in self.connections:
            r1, r2 = connection.room1_id, connection.room2_id
            self.adjacency_matrix[r1][r2] = 1
            self.adjacency_matrix[r2][r1] = 1
    
    def get_obstructed_connections(self, box_positions: Set[Tuple[int, int]]) -> List[RoomConnection]:
        """Retourne les connexions obstruées par les boîtes."""
        obstructed = []
        for connection in self.connections:
            if connection.is_obstructed_by_boxes(box_positions):
                obstructed.append(connection)
        return obstructed
    
    def count_obstructed_connections(self, box_positions: Set[Tuple[int, int]]) -> int:
        """Compte le nombre de connexions obstruées (room connectivity feature)."""
        return len(self.get_obstructed_connections(box_positions))


class HotspotAnalyzer:
    """
    Analyseur de hotspots selon le document de recherche.
    
    "A box is defined as a hotspot if turning it into a wall reduces the number
    of reachable targets for any of the other boxes."
    """
    
    def __init__(self, level: Level):
        self.level = level
        self.width = level.width
        self.height = level.height
        
        # Cache des murs et targets
        self.walls = self._extract_walls()
        self.targets = self._extract_targets()
        
        # Table de hotspots pré-calculée
        self.hotspot_table: Dict[Tuple[Tuple[int, int], Tuple[int, int]], bool] = {}
        self._precompute_hotspot_table()
    
    def _extract_walls(self) -> Set[Tuple[int, int]]:
        """Extrait les positions des murs."""
        walls = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.level.get_cell(x, y) == '#':
                    walls.add((x, y))
        return walls
    
    def _extract_targets(self) -> Set[Tuple[int, int]]:
        """Extrait les positions des targets."""
        targets = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.level.get_cell(x, y) in ['.', '*', '+']:
                    targets.add((x, y))
        return targets
    
    def _precompute_hotspot_table(self):
        """
        Pré-calcule la table des hotspots pour toutes les paires de positions.
        
        "At the level preprocessing stage, we check all pairs of X,Y squares
        for being in a hotspot relation."
        """
        all_squares = []
        for y in range(self.height):
            for x in range(self.width):
                if self.level.get_cell(x, y) != '#':  # Pas un mur
                    all_squares.append((x, y))
        
        for x_square in all_squares:
            for y_square in all_squares:
                if x_square != y_square:
                    is_hotspot = self._is_hotspot_pair(x_square, y_square)
                    self.hotspot_table[(x_square, y_square)] = is_hotspot
    
    def _is_hotspot_pair(self, x_square: Tuple[int, int], y_square: Tuple[int, int]) -> bool:
        """
        Vérifie si y_square est un hotspot pour x_square.
        
        "First, a box is placed on square X, and we count the number of reachable
        targets from this square. Then another box is added on square Y and we count
        again. If the number has changed, then square Y is a hotspot square for square X."
        """
        # Compte les targets atteignables depuis X sans Y
        targets_without_y = self._count_reachable_targets(x_square, {y_square})
        
        # Compte les targets atteignables depuis X avec Y (comme mur)
        targets_with_y = self._count_reachable_targets(x_square, {y_square} | self.walls)
        
        # Y est un hotspot pour X si le nombre de targets atteignables change
        return targets_without_y != targets_with_y
    
    def _count_reachable_targets(self, start: Tuple[int, int], 
                                obstacles: Set[Tuple[int, int]]) -> int:
        """Compte les targets atteignables depuis une position."""
        reachable_count = 0
        
        for target in self.targets:
            if self._is_reachable(start, target, obstacles):
                reachable_count += 1
        
        return reachable_count
    
    def _is_reachable(self, start: Tuple[int, int], 
                     target: Tuple[int, int], 
                     obstacles: Set[Tuple[int, int]]) -> bool:
        """Vérifie si une target est atteignable depuis une position."""
        if start == target:
            return True
        
        visited = {start}
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) == target:
                    return True
                
                if ((nx, ny) in visited or (nx, ny) in obstacles or
                    nx < 0 or nx >= self.width or ny < 0 or ny >= self.height):
                    continue
                
                visited.add((nx, ny))
                queue.append((nx, ny))
        
        return False
    
    def count_hotspots_in_state(self, state: SokobanState) -> int:
        """
        Compte le nombre de hotspots dans un état donné.
        
        "During the search phase, we examine all pairs of boxes. Using the table,
        we can tell if a box on square Y is a hotspot for a box on square X."
        """
        hotspot_count = 0
        box_positions = list(state.box_positions)
        
        for i, box_x in enumerate(box_positions):
            for j, box_y in enumerate(box_positions):
                if i != j:  # Différentes boîtes
                    if self.hotspot_table.get((box_x, box_y), False):
                        hotspot_count += 1
        
        # Chaque hotspot est compté une seule fois
        return hotspot_count // 2 if hotspot_count > 0 else 0
    
    def find_most_disruptive_hotspot(self, state: SokobanState) -> Optional[Tuple[int, int]]:
        """
        Trouve le hotspot qui bloque le plus grand nombre de boîtes.
        
        Utilisé par l'Opener Advisor selon le document :
        "First, it finds the hotspot that blocks the largest number of boxes."
        """
        box_positions = list(state.box_positions)
        hotspot_impact = defaultdict(int)
        
        for box_x in box_positions:
            for box_y in box_positions:
                if box_x != box_y:
                    if self.hotspot_table.get((box_x, box_y), False):
                        hotspot_impact[box_y] += 1  # box_y bloque box_x
        
        if not hotspot_impact:
            return None
        
        # Retourne le hotspot avec le plus grand impact
        return max(hotspot_impact.items(), key=lambda x: x[1])[0]


class FESSRoomAnalyzer:
    """
    Analyseur de rooms principal pour le système FESS.
    
    Intègre tous les aspects de l'analyse des rooms :
    - Détection des rooms (zones 2x3)
    - Construction du graphe de connectivité
    - Analyse des hotspots
    - Calcul de la mobilité
    """
    
    def __init__(self, level: Level):
        self.level = level
        self.width = level.width
        self.height = level.height
        
        # Composants d'analyse
        self.hotspot_analyzer = HotspotAnalyzer(level)
        self.room_graph = RoomGraph()
        
        # Cache
        self._free_squares_cache = None
        
        # Analyse initiale
        self._analyze_level()
    
    def _analyze_level(self):
        """Effectue l'analyse complète du niveau."""
        self._detect_rooms()
        self._detect_room_connections()
        self.room_graph.build_adjacency_matrix()
    
    def _get_free_squares(self) -> Set[Tuple[int, int]]:
        """Retourne les carrés libres (pas des murs)."""
        if self._free_squares_cache is None:
            free_squares = set()
            for y in range(self.height):
                for x in range(self.width):
                    if self.level.get_cell(x, y) != '#':
                        free_squares.add((x, y))
            self._free_squares_cache = free_squares
        return self._free_squares_cache
    
    def _detect_rooms(self):
        """
        Détecte les rooms selon la définition du document.
        
        "A room is a connected area of 2x3 squares."
        """
        free_squares = self._get_free_squares()
        room_candidates = self._find_room_candidates(free_squares)
        
        room_id = 0
        for candidate_squares in room_candidates:
            if len(candidate_squares) >= 6:  # Au moins 2x3 = 6 carrés
                room = Room(
                    id=room_id,
                    squares=candidate_squares,
                    center=(0, 0),  # Sera calculé automatiquement
                    area=0  # Sera calculé automatiquement dans __post_init__
                )
                self.room_graph.add_room(room)
                room_id += 1
    
    def _find_room_candidates(self, free_squares: Set[Tuple[int, int]]) -> List[Set[Tuple[int, int]]]:
        """Trouve les candidats de rooms par flood fill."""
        visited = set()
        room_candidates = []
        
        for square in free_squares:
            if square not in visited:
                # Nouvelle zone connexe
                room_squares = self._flood_fill_room(square, free_squares, visited)
                if len(room_squares) >= 6:  # Assez grande pour être une room
                    room_candidates.append(room_squares)
        
        return room_candidates
    
    def _flood_fill_room(self, start: Tuple[int, int], 
                        free_squares: Set[Tuple[int, int]], 
                        global_visited: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Effectue un flood fill pour trouver une zone connexe."""
        if start in global_visited or start not in free_squares:
            return set()
        
        room_squares = set()
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in room_squares or (x, y) not in free_squares:
                continue
            
            room_squares.add((x, y))
            global_visited.add((x, y))
            
            # Ajoute les voisins
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in room_squares and (nx, ny) in free_squares:
                    queue.append((nx, ny))
        
        return room_squares
    
    def _detect_room_connections(self):
        """Détecte les connexions entre rooms."""
        rooms = list(self.room_graph.rooms.values())
        
        for i, room1 in enumerate(rooms):
            for j, room2 in enumerate(rooms[i+1:], i+1):
                connection = self._find_connection_between_rooms(room1, room2)
                if connection:
                    self.room_graph.add_connection(connection)
    
    def _find_connection_between_rooms(self, room1: Room, room2: Room) -> Optional[RoomConnection]:
        """Trouve une connexion directe entre deux rooms."""
        # Trouve les carrés de passage entre les rooms
        passage_squares = []
        
        for square1 in room1.get_boundary_squares():
            for square2 in room2.get_boundary_squares():
                # Vérifie si les carrés sont adjacents
                x1, y1 = square1
                x2, y2 = square2
                
                if abs(x1 - x2) + abs(y1 - y2) == 1:  # Adjacents
                    # Trouve le(s) carré(s) de passage
                    path = self._find_passage_path(square1, square2)
                    if path:
                        passage_squares.extend(path)
        
        if passage_squares:
            # Supprime les doublons
            unique_passages = list(set(passage_squares))
            
            return RoomConnection(
                room1_id=room1.id,
                room2_id=room2.id,
                passage_squares=unique_passages,
                is_tunnel=len(unique_passages) <= 2  # Tunnel si ≤ 2 carrés
            )
        
        return None
    
    def _find_passage_path(self, start: Tuple[int, int], 
                          end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Trouve le chemin de passage entre deux points."""
        # Implémentation simple : si adjacents, le passage est entre eux
        x1, y1 = start
        x2, y2 = end
        
        if abs(x1 - x2) + abs(y1 - y2) == 1:
            return [start, end]  # Passage direct
        
        # Pour les passages plus complexes, utilise BFS (implémentation future)
        return []
    
    def compute_room_connectivity_feature(self, state: SokobanState) -> int:
        """
        Calcule la Room Connectivity Feature.
        
        "The room connectivity feature counts how many room links are obstructed by boxes."
        """
        return self.room_graph.count_obstructed_connections(set(state.box_positions))
    
    def compute_hotspots_feature(self, state: SokobanState) -> int:
        """Calcule le nombre de hotspots dans l'état."""
        return self.hotspot_analyzer.count_hotspots_in_state(state)
    
    def compute_mobility_feature(self, state: SokobanState) -> int:
        """
        Calcule la Mobility Feature.
        
        "Mobility refers to the number of possible moves in a position. However,
        such a feature is too expensive to compute, so we approximate it by the
        number of box sides the player can reach."
        """
        player_pos = state.player_position
        reachable_box_sides = 0
        
        # Trouve toutes les positions accessibles au joueur
        reachable_positions = self._find_reachable_positions(
            player_pos, set(state.box_positions) | self.hotspot_analyzer.walls
        )
        
        # Compte les côtés de boîtes accessibles
        for box_pos in state.box_positions:
            bx, by = box_pos
            
            # Vérifie chaque côté de la boîte
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                side_pos = (bx + dx, by + dy)
                if side_pos in reachable_positions:
                    reachable_box_sides += 1
        
        return reachable_box_sides
    
    def _find_reachable_positions(self, start: Tuple[int, int], 
                                 obstacles: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Trouve toutes les positions atteignables depuis un point de départ."""
        reachable = set()
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in reachable or (x, y) in obstacles:
                continue
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            
            reachable.add((x, y))
            
            # Ajoute les voisins
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in reachable:
                    queue.append((nx, ny))
        
        return reachable
    
    def get_room_containing_position(self, pos: Tuple[int, int]) -> Optional[Room]:
        """Trouve la room contenant une position donnée."""
        for room in self.room_graph.rooms.values():
            if room.contains_position(pos):
                return room
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """Retourne les statistiques de l'analyse des rooms."""
        return {
            'num_rooms': len(self.room_graph.rooms),
            'num_connections': len(self.room_graph.connections),
            'total_room_area': sum(room.area for room in self.room_graph.rooms.values()),
            'hotspot_pairs_precomputed': len(self.hotspot_analyzer.hotspot_table)
        }


def create_room_analyzer(level: Level) -> FESSRoomAnalyzer:
    """Factory function pour créer un analyseur de rooms FESS."""
    return FESSRoomAnalyzer(level)