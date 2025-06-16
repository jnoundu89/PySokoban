"""
FESS Packing Plan System
========================

Implémentation du système de packing plan selon les documents de recherche.

"Early on, human Sokoban players learn that it is not enough to bring boxes to 
targets. Boxes must also be packed in a specific order."

"A useful technique for finding the packing order and the parking squares is to 
solve the level backwards: Start with the final position and pull boxes away 
from the targets."

"Sink assumption: There is a room near the target area that can hold an infinite 
number of boxes. This room is called the sink room."

Référence: "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
"""

from typing import Dict, List, Set, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

from src.core.level import Level
from src.core.sokoban_state import SokobanState


@dataclass
class SinkRoom:
    """Représente une sink room pour le packing plan."""
    id: int
    squares: Set[Tuple[int, int]]
    capacity_score: float
    proximity_to_targets: float
    accessibility_score: float
    
    @property
    def total_score(self) -> float:
        """Score total de qualité de la sink room."""
        return self.capacity_score + self.proximity_to_targets + self.accessibility_score


@dataclass
class Basin:
    """Représente un basin pour une target donnée."""
    target_position: Tuple[int, int]
    reachable_squares: Set[Tuple[int, int]]
    size: int
    
    def __post_init__(self):
        self.size = len(self.reachable_squares)
    
    def contains_box(self, box_position: Tuple[int, int]) -> bool:
        """Vérifie si une boîte est dans ce basin."""
        return box_position in self.reachable_squares


@dataclass
class PackingStep:
    """Représente une étape dans le packing plan."""
    step_number: int
    target_position: Tuple[int, int]
    preferred_source: Optional[Tuple[int, int]]  # Position recommandée pour la boîte
    parking_squares: List[Tuple[int, int]]       # Positions de parking intermédiaires
    reason: str                                  # Explication de cette étape


class PackingPlan:
    """
    Plan de packing complet pour un niveau.
    
    Détermine l'ordre optimal de packing des boîtes et identifie
    les positions de parking nécessaires.
    """
    
    def __init__(self):
        self.steps: List[PackingStep] = []
        self.sink_room: Optional[SinkRoom] = None
        self.basins: Dict[Tuple[int, int], Basin] = {}
        self.parking_squares: Set[Tuple[int, int]] = set()
        self.is_valid = False
    
    def add_step(self, step: PackingStep):
        """Ajoute une étape au plan."""
        self.steps.append(step)
        if step.parking_squares:
            self.parking_squares.update(step.parking_squares)
    
    def get_packing_order(self) -> List[Tuple[int, int]]:
        """Retourne l'ordre de packing des targets."""
        return [step.target_position for step in self.steps]
    
    def is_box_in_plan(self, box_position: Tuple[int, int]) -> bool:
        """Vérifie si une boîte est dans le plan (sink room ou déjà packée)."""
        if self.sink_room and box_position in self.sink_room.squares:
            return True
        
        # Vérifie si dans un basin
        for basin in self.basins.values():
            if basin.contains_box(box_position):
                return True
        
        return False
    
    def count_out_of_plan_boxes(self, state: SokobanState) -> int:
        """Compte les boîtes out-of-plan selon la définition du document."""
        oop_count = 0
        
        for box_pos in state.box_positions:
            if not self.is_box_in_plan(box_pos):
                # Vérifie si la boîte n'est pas déjà sur une target
                is_on_target = any(box_pos == step.target_position for step in self.steps)
                if not is_on_target:
                    oop_count += 1
        
        return oop_count


class BackwardSearchEngine:
    """
    Moteur de recherche rétrograde pour générer le packing plan.
    
    "The general strategy for computing the packing order involves two rules:
    1. If a box can be pulled to the sink room, remove the box from the board.
    2. Otherwise, pull a box as far away from the targets as possible."
    """
    
    def __init__(self, level: Level):
        self.level = level
        self.width = level.width
        self.height = level.height
        self.walls = self._extract_walls()
        self.targets = self._extract_targets()
        
        self.logger = logging.getLogger(__name__)
    
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
                if self.level.is_target(x, y):
                    targets.add((x, y))
        return targets
    
    def compute_distance_scores(self, state: SokobanState) -> Dict[Tuple[int, int], float]:
        """
        Calcule les distance-scores pour tous les carrés.
        
        "First, we compute for each square its distance from its nearest target 
        square. Then the distance-score for a position is simply the sum of these 
        distances for all squares occupied by boxes."
        """
        distance_map = {}
        
        # Calcule la distance de chaque carré à la target la plus proche
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.walls:
                    min_distance = float('inf')
                    for target in self.targets:
                        distance = abs(x - target[0]) + abs(y - target[1])
                        min_distance = min(min_distance, distance)
                    distance_map[(x, y)] = min_distance
        
        return distance_map
    
    def pull_box_to_farthest_position(self, 
                                    box_pos: Tuple[int, int], 
                                    state: SokobanState,
                                    distance_map: Dict[Tuple[int, int], float]) -> Optional[Tuple[int, int]]:
        """
        Tire une boîte vers la position la plus éloignée des targets.
        
        Implémente la règle 2 : "pull a box as far away from the targets as possible."
        """
        # Trouve toutes les positions atteignables pour cette boîte
        reachable_positions = self._find_pullable_positions(box_pos, state)
        
        if not reachable_positions:
            return None
        
        # Sélectionne la position avec le distance-score maximum
        best_position = max(reachable_positions, 
                          key=lambda pos: distance_map.get(pos, 0))
        
        return best_position
    
    def _find_pullable_positions(self, 
                               box_pos: Tuple[int, int], 
                               state: SokobanState) -> Set[Tuple[int, int]]:
        """Trouve toutes les positions où une boîte peut être tirée."""
        pullable = set()
        obstacles = self.walls | state.box_positions
        
        # BFS pour trouver toutes les positions atteignables
        visited = set()
        queue = deque([box_pos])
        
        while queue:
            current_pos = queue.popleft()
            
            if current_pos in visited:
                continue
            visited.add(current_pos)
            pullable.add(current_pos)
            
            # Vérifie les 4 directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_x, new_y = current_pos[0] + dx, current_pos[1] + dy
                new_pos = (new_x, new_y)
                
                # Vérifie si la nouvelle position est valide
                if (0 <= new_x < self.width and 0 <= new_y < self.height and
                    new_pos not in obstacles and new_pos not in visited):
                    
                    # Vérifie si le mouvement de pull est possible
                    # (le joueur doit pouvoir se placer de l'autre côté)
                    player_x = current_pos[0] - dx
                    player_y = current_pos[1] - dy
                    player_pos = (player_x, player_y)
                    
                    if (0 <= player_x < self.width and 0 <= player_y < self.height and
                        player_pos not in obstacles):
                        queue.append(new_pos)
        
        return pullable


class SinkRoomAnalyzer:
    """
    Analyseur pour identifier la meilleure sink room.
    
    "We choose the sink room to be the room associated with the basin that 
    contains the largest number of boxes in the initial position."
    """
    
    def __init__(self, level: Level):
        self.level = level
        self.width = level.width
        self.height = level.height
        self.walls = self._extract_walls()
        self.targets = self._extract_targets()
        
        self.logger = logging.getLogger(__name__)
    
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
                if self.level.is_target(x, y):
                    targets.add((x, y))
        return targets
    
    def find_best_sink_room(self, initial_state: SokobanState) -> Optional[SinkRoom]:
        """
        Trouve la meilleure sink room selon les critères du document.
        
        Returns:
            SinkRoom optimale ou None si aucune n'est trouvée
        """
        # Calcule les basins pour chaque target
        basins = self._compute_all_basins()
        
        if not basins:
            return None
        
        # Évalue chaque basin comme candidat sink room
        best_sink = None
        best_score = -1
        
        for target_pos, basin in basins.items():
            # Compte les boîtes initiales dans ce basin
            boxes_in_basin = sum(1 for box_pos in initial_state.box_positions 
                               if basin.contains_box(box_pos))
            
            # Calcule les scores
            capacity_score = len(basin.reachable_squares) / 100.0  # Normalise
            proximity_score = self._compute_proximity_to_targets(basin)
            accessibility_score = self._compute_accessibility_score(basin)
            
            # Score total pondéré par le nombre de boîtes initiales
            total_score = (capacity_score + proximity_score + accessibility_score) * (1 + boxes_in_basin)
            
            if total_score > best_score:
                best_score = total_score
                best_sink = SinkRoom(
                    id=len(basins),
                    squares=basin.reachable_squares,
                    capacity_score=capacity_score,
                    proximity_to_targets=proximity_score,
                    accessibility_score=accessibility_score
                )
        
        return best_sink
    
    def _compute_all_basins(self) -> Dict[Tuple[int, int], Basin]:
        """
        Calcule tous les basins pour les targets.
        
        "A basin is the set of squares from which a box can reach a given target 
        square, when the board is in the final position."
        """
        basins = {}
        
        # Pour chaque target, calcule son basin
        for target_pos in self.targets:
            reachable_squares = self._compute_basin_for_target(target_pos)
            
            basin = Basin(
                target_position=target_pos,
                reachable_squares=reachable_squares,
                size=0  # Sera calculé automatiquement
            )
            
            basins[target_pos] = basin
        
        return basins
    
    def _compute_basin_for_target(self, target_pos: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """
        Calcule le basin pour une target donnée.
        
        Utilise BFS pour trouver toutes les positions d'où une boîte peut
        atteindre cette target dans la position finale.
        """
        reachable = set()
        visited = set()
        queue = deque([target_pos])
        
        # Simule la position finale (toutes les autres targets occupées par des boîtes)
        final_obstacles = self.walls | (self.targets - {target_pos})
        
        while queue:
            current_pos = queue.popleft()
            
            if current_pos in visited:
                continue
            
            visited.add(current_pos)
            reachable.add(current_pos)
            
            # Explore les voisins
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_x, new_y = current_pos[0] + dx, current_pos[1] + dy
                new_pos = (new_x, new_y)
                
                if (0 <= new_x < self.width and 0 <= new_y < self.height and
                    new_pos not in final_obstacles and new_pos not in visited):
                    queue.append(new_pos)
        
        return reachable
    
    def _compute_proximity_to_targets(self, basin: Basin) -> float:
        """Calcule la proximité du basin aux targets."""
        if not basin.reachable_squares:
            return 0.0
        
        # Distance moyenne aux targets
        total_distance = 0
        count = 0
        
        for square in basin.reachable_squares:
            for target in self.targets:
                distance = abs(square[0] - target[0]) + abs(square[1] - target[1])
                total_distance += distance
                count += 1
        
        if count == 0:
            return 0.0
        
        avg_distance = total_distance / count
        return max(0, 10 - avg_distance)  # Plus proche = meilleur score
    
    def _compute_accessibility_score(self, basin: Basin) -> float:
        """Calcule le score d'accessibilité du basin."""
        # Pour l'instant, approximation simple basée sur la taille
        return min(5.0, len(basin.reachable_squares) / 20.0)


class FESSPackingPlanGenerator:
    """
    Générateur principal de packing plan pour FESS.
    
    Coordonne l'analyse des sink rooms, la recherche rétrograde et
    la génération du plan de packing optimal.
    """
    
    def __init__(self, level: Level):
        self.level = level
        self.sink_analyzer = SinkRoomAnalyzer(level)
        self.backward_engine = BackwardSearchEngine(level)
        
        self.logger = logging.getLogger(__name__)
    
    def generate_packing_plan(self, initial_state: SokobanState) -> PackingPlan:
        """
        Génère un plan de packing complet pour le niveau.
        
        Args:
            initial_state: État initial du niveau
            
        Returns:
            PackingPlan complet
        """
        plan = PackingPlan()
        
        try:
            # 1. Trouve la meilleure sink room
            sink_room = self.sink_analyzer.find_best_sink_room(initial_state)
            if sink_room:
                plan.sink_room = sink_room
                self.logger.debug(f"Sink room found with {len(sink_room.squares)} squares")
            
            # 2. Calcule les basins
            basins = self.sink_analyzer._compute_all_basins()
            plan.basins = basins
            self.logger.debug(f"Computed {len(basins)} basins")
            
            # 3. Génère l'ordre de packing via recherche rétrograde
            packing_steps = self._generate_packing_steps(basins, sink_room, initial_state)
            
            for step in packing_steps:
                plan.add_step(step)
            
            plan.is_valid = len(plan.steps) > 0
            
            if plan.is_valid:
                self.logger.info(f"Packing plan generated with {len(plan.steps)} steps")
            else:
                self.logger.warning("Failed to generate valid packing plan")
            
        except Exception as e:
            self.logger.error(f"Error generating packing plan: {e}")
            plan.is_valid = False
        
        return plan
    
    def _generate_packing_steps(self, 
                              basins: Dict[Tuple[int, int], Basin],
                              sink_room: Optional[SinkRoom],
                              initial_state: SokobanState) -> List[PackingStep]:
        """Génère les étapes de packing via analyse rétrograde."""
        steps = []
        
        # Pour l'instant, génère un ordre simple basé sur la proximité
        # Une implémentation complète inclurait la recherche rétrograde
        
        targets = list(basins.keys())
        targets.sort(key=lambda t: (t[0], t[1]))  # Ordre lexicographique simple
        
        for i, target_pos in enumerate(targets):
            step = PackingStep(
                step_number=i + 1,
                target_position=target_pos,
                preferred_source=None,  # Sera déterminé par l'algorithm FESS
                parking_squares=[],     # Sera déterminé par l'algorithm FESS
                reason=f"Pack target at {target_pos}"
            )
            steps.append(step)
        
        return steps


def create_packing_plan_generator(level: Level) -> FESSPackingPlanGenerator:
    """Factory function pour créer un générateur de packing plan."""
    return FESSPackingPlanGenerator(level)


def analyze_packing_requirements(level: Level, 
                                initial_state: SokobanState) -> Dict[str, any]:
    """
    Analyse les exigences de packing pour un niveau.
    
    Returns:
        Dictionnaire avec les informations d'analyse
    """
    generator = create_packing_plan_generator(level)
    plan = generator.generate_packing_plan(initial_state)
    
    return {
        'has_valid_plan': plan.is_valid,
        'num_targets': len(generator.sink_analyzer.targets),
        'sink_room_size': len(plan.sink_room.squares) if plan.sink_room else 0,
        'num_basins': len(plan.basins),
        'packing_steps': len(plan.steps),
        'parking_squares': len(plan.parking_squares),
        'oop_boxes': plan.count_out_of_plan_boxes(initial_state)
    }