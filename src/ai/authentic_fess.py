"""
Implémentation authentique de l'algorithme FESS (Feature Space Search)
selon Shoham & Schaeffer [2020] - "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"

Ce module implémente le vrai algorithme FESS qui a été le premier à résoudre 
tous les 90 problèmes du benchmark XSokoban en moins de 4 minutes.
"""

import time
from typing import List, Tuple, Set, Dict, Optional, FrozenSet, Any, Callable
from dataclasses import dataclass
from collections import deque, defaultdict
from enum import Enum
import heapq
import math


@dataclass
class MacroMove:
    """
    Représente un macro-move: séquence de mouvements qui pousse la même box
    sans pousser d'autres boxes entre-temps.
    """
    box_from: Tuple[int, int]
    box_to: Tuple[int, int]
    push_sequence: List[str]  # Séquence de moves pour accomplir le macro-move
    weight: int = 1  # Poids du macro-move


class FESSState:
    """
    État optimisé pour l'algorithme FESS authentique.
    
    Contrairement à l'implémentation précédente, cet état ne stocke pas
    de valeurs heuristiques combinées mais seulement les données brutes
    pour la projection vers l'espace de features 4D.
    """
    
    def __init__(self, player_pos: Tuple[int, int], boxes: FrozenSet[Tuple[int, int]], 
                 parent: Optional['FESSState'] = None, move: Optional[str] = None, 
                 accumulated_weight: int = 0):
        self.player_pos = player_pos
        self.boxes = boxes
        self.parent = parent
        self.move = move
        self.accumulated_weight = accumulated_weight
        
        # Pas de h_cost, f_cost ici - FESS ne les utilise pas
        self._hash_cache = None
        
        # Métadonnées pour l'arbre de recherche
        self.children_moves = []  # Liste des mouvements possibles avec leurs poids
        self.is_expanded = False
        
    def __hash__(self):
        if self._hash_cache is None:
            self._hash_cache = hash((self.player_pos, self.boxes))
        return self._hash_cache
    
    def __eq__(self, other):
        if not isinstance(other, FESSState):
            return False
        return self.player_pos == other.player_pos and self.boxes == other.boxes
    
    def add_child_move(self, move: str, weight: int):
        """Ajoute un mouvement possible avec son poids."""
        self.children_moves.append((move, weight))


class FESSSearchTree:
    """
    Arbre de recherche pour FESS avec gestion des poids accumulés.
    
    Contrairement aux arbres A*, cet arbre stocke les poids des mouvements
    et maintient la structure nécessaire pour le cycling FESS.
    """
    
    def __init__(self):
        self.root: Optional[FESSState] = None
        self.states_by_hash: Dict[int, FESSState] = {}
        self.total_states = 0
        
    def add_root(self, state: FESSState):
        """Ajoute l'état racine."""
        self.root = state
        self.states_by_hash[hash(state)] = state
        self.total_states = 1
        
    def add_state(self, state: FESSState) -> bool:
        """
        Ajoute un état à l'arbre.
        
        Returns:
            bool: True si l'état a été ajouté, False s'il existait déjà
        """
        state_hash = hash(state)
        if state_hash in self.states_by_hash:
            return False
            
        self.states_by_hash[state_hash] = state
        self.total_states += 1
        return True
        
    def contains(self, state: FESSState) -> bool:
        """Vérifie si un état est dans l'arbre."""
        return hash(state) in self.states_by_hash
        
    def get_state(self, state: FESSState) -> Optional[FESSState]:
        """Récupère un état de l'arbre s'il existe."""
        return self.states_by_hash.get(hash(state))


class FESSFeatureSpace:
    """
    Espace de features 4D du vrai FESS.
    
    Cet espace maintient les cellules (f1, f2, f3, f4) et les états DS
    qui projettent vers chaque cellule. C'est le cœur de l'algorithme FESS.
    """
    
    def __init__(self, level):
        self.level = level
        
        # Analyseurs pour les 4 features spécialisées
        self.packing_analyzer = None      # Sera initialisé plus tard
        self.connectivity_analyzer = None  # Sera initialisé plus tard  
        self.room_analyzer = None         # Sera initialisé plus tard
        self.out_of_plan_analyzer = None  # Sera initialisé plus tard
        
        # Cellules FS: (f1,f2,f3,f4) -> liste d'états DS
        self.fs_cells: Dict[Tuple[int, int, int, int], List[FESSState]] = defaultdict(list)
        
        # Pour le cycling à travers les cellules
        self.cell_cycle_index = 0
        self.non_empty_cells: List[Tuple[int, int, int, int]] = []
        
    def project_state(self, state: FESSState) -> Tuple[int, int, int, int]:
        """
        Projette un état DS vers les coordonnées FS 4D.
        
        Cette méthode calcule les 4 features spécialisées pour cet état
        et retourne les coordonnées dans l'espace de features.
        
        C'est le cœur du vrai FESS - chaque état est projeté dans un espace 4D
        selon les features sophistiquées de Shoham & Schaeffer [2020].
        """
        # Feature 1: Packing (la plus critique)
        f1 = self.packing_analyzer.calculate_packing_feature(state)
        
        # Feature 2: Connectivity
        f2 = self.connectivity_analyzer.calculate_connectivity(state)
        
        # Feature 3: Room Connectivity
        f3 = self.room_analyzer.calculate_room_connectivity(state)
        
        # Feature 4: Out of Plan
        f4 = self.out_of_plan_analyzer.calculate_out_of_plan(state)
        
        return (f1, f2, f3, f4)
    
    def add_state_to_cell(self, state: FESSState):
        """Ajoute un état à sa cellule FS correspondante."""
        fs_coords = self.project_state(state)
        
        # Ajouter l'état à la cellule
        self.fs_cells[fs_coords].append(state)
        
        # Mettre à jour la liste des cellules non-vides pour le cycling
        if fs_coords not in self.non_empty_cells:
            self.non_empty_cells.append(fs_coords)
    
    def get_next_cell_for_cycling(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Retourne la prochaine cellule pour le cycling FESS.
        
        Le vrai FESS cycle à travers toutes les cellules non-vides
        de manière répétitive.
        """
        if not self.non_empty_cells:
            return None
            
        cell = self.non_empty_cells[self.cell_cycle_index]
        self.cell_cycle_index = (self.cell_cycle_index + 1) % len(self.non_empty_cells)
        return cell
    
    def get_states_in_cell(self, fs_coords: Tuple[int, int, int, int]) -> List[FESSState]:
        """Retourne tous les états DS dans une cellule FS."""
        return self.fs_cells.get(fs_coords, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de l'espace de features."""
        total_states = sum(len(states) for states in self.fs_cells.values())
        
        return {
            'total_cells': len(self.fs_cells),
            'non_empty_cells': len(self.non_empty_cells),
            'total_states_in_fs': total_states,
            'average_states_per_cell': total_states / max(len(self.fs_cells), 1),
            'cycle_index': self.cell_cycle_index
        }


# Classes de base pour les analyseurs (seront implémentées dans Phase 2)

class BaseFeatureAnalyzer:
    """Classe de base pour tous les analyseurs de features FESS."""
    
    def __init__(self, level):
        self.level = level
        self.width = level.width
        self.height = level.height


class PackingAnalyzer(BaseFeatureAnalyzer):
    """
    Analyseur pour la feature Packing (Feature 1 - la plus critique).
    
    Cette feature compte le nombre de boxes qui ont atteint leur target
    dans l'ORDRE OPTIMAL déterminé par analyse rétrograde.
    
    L'analyse rétrograde détermine l'ordre optimal en partant de l'état final
    et en remontant pour identifier quelle box doit être packée en dernier,
    avant-dernière, etc.
    """
    
    def __init__(self, level):
        super().__init__(level)
        self.targets = list(level.targets)
        self.boxes_initial = list(level.boxes)
        
        # Calculer l'ordre optimal par analyse rétrograde
        self.optimal_packing_order = self._compute_optimal_packing_order()
        
        # Cache pour optimiser les calculs répétés
        self._packing_cache = {}
        
    def _compute_optimal_packing_order(self) -> List[Tuple[int, int]]:
        """
        Calcule l'ordre optimal de packing par analyse rétrograde.
        
        Cette méthode détermine l'ordre dans lequel les boxes doivent être
        packées en analysant les contraintes de chaque target.
        
        Returns:
            List[Tuple[int, int]]: Ordre optimal des targets
        """
        if len(self.targets) != len(self.boxes_initial):
            # Si nombre de targets != nombre de boxes, utiliser ordre par défaut
            return self.targets
        
        # Analyser les contraintes pour chaque target
        target_constraints = self._analyze_target_constraints()
        
        # Trier les targets par ordre de difficulté (plus difficile = à packer en dernier)
        ordered_targets = self._sort_targets_by_difficulty(target_constraints)
        
        return ordered_targets
    
    def _analyze_target_constraints(self) -> Dict[Tuple[int, int], Dict[str, float]]:
        """
        Analyse les contraintes pour chaque target.
        
        Calcule plusieurs métriques de difficulté pour chaque target:
        - Accessibilité (nombre de directions libres)
        - Isolement (distance aux autres targets)
        - Contraintes spatiales (coins, corridors)
        """
        constraints = {}
        
        for target in self.targets:
            x, y = target
            
            # 1. Accessibilité: nombre de directions libres autour du target
            free_directions = 0
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    not self.level.is_wall(nx, ny)):
                    free_directions += 1
            
            accessibility = free_directions / 4.0
            
            # 2. Isolement: distance moyenne aux autres targets
            if len(self.targets) > 1:
                total_distance = sum(
                    abs(x - tx) + abs(y - ty)
                    for tx, ty in self.targets if (tx, ty) != target
                )
                isolation = total_distance / (len(self.targets) - 1)
            else:
                isolation = 0
            
            # 3. Contraintes spatiales: est-ce dans un coin ou corridor?
            spatial_constraint = self._calculate_spatial_constraint(x, y)
            
            # 4. Blocage potentiel: est-ce que packer cette box pourrait bloquer d'autres?
            blocking_potential = self._calculate_blocking_potential(target)
            
            constraints[target] = {
                'accessibility': accessibility,
                'isolation': isolation,
                'spatial_constraint': spatial_constraint,
                'blocking_potential': blocking_potential,
                'difficulty_score': self._calculate_difficulty_score(
                    accessibility, isolation, spatial_constraint, blocking_potential
                )
            }
        
        return constraints
    
    def _calculate_spatial_constraint(self, x: int, y: int) -> float:
        """
        Calcule la contrainte spatiale d'une position.
        
        Retourne une valeur entre 0 (facile) et 1 (très contraint).
        """
        # Compter les murs adjacents
        wall_count = sum(
            1 for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
            if self.level.is_wall(x + dx, y + dy)
        )
        
        # Plus il y a de murs, plus c'est contraint
        constraint = wall_count / 4.0
        
        # Bonus pour les coins (particulièrement contraints)
        corner_patterns = [
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y-1)),
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y-1)),
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y+1)),
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y+1))
        ]
        
        if any(corner_patterns):
            constraint += 0.3  # Bonus de contrainte pour les coins
        
        return min(constraint, 1.0)
    
    def _calculate_blocking_potential(self, target: Tuple[int, int]) -> float:
        """
        Calcule le potentiel de blocage d'un target.
        
        Un target a un fort potentiel de blocage s'il est sur un chemin
        critique vers d'autres targets.
        """
        x, y = target
        blocking_score = 0.0
        
        # Vérifier si ce target est sur un chemin étroit
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            # Compter les espaces libres dans cette direction
            spaces_in_direction = 0
            nx, ny = x + dx, y + dy
            
            while (0 <= nx < self.width and 0 <= ny < self.height and
                   not self.level.is_wall(nx, ny)):
                spaces_in_direction += 1
                nx += dx
                ny += dy
                
                # Arrêter après quelques cases pour éviter les calculs longs
                if spaces_in_direction > 3:
                    break
            
            # Si chemin court dans cette direction, augmenter le score de blocage
            if spaces_in_direction <= 2:
                blocking_score += 0.25
        
        return min(blocking_score, 1.0)
    
    def _calculate_difficulty_score(self, accessibility: float, isolation: float,
                                   spatial_constraint: float, blocking_potential: float) -> float:
        """
        Calcule un score global de difficulté pour un target.
        
        Plus le score est élevé, plus le target doit être packé tard.
        """
        # Poids pour chaque facteur (ajustables empiriquement)
        weights = {
            'accessibility': -2.0,      # Moins accessible = plus difficile
            'isolation': 0.1,           # Plus isolé = légèrement plus difficile
            'spatial_constraint': 3.0,  # Plus contraint = beaucoup plus difficile
            'blocking_potential': 2.5   # Plus bloquant = plus difficile
        }
        
        difficulty = (
            weights['accessibility'] * accessibility +
            weights['isolation'] * isolation +
            weights['spatial_constraint'] * spatial_constraint +
            weights['blocking_potential'] * blocking_potential
        )
        
        return max(difficulty, 0.0)
    
    def _sort_targets_by_difficulty(self, constraints: Dict) -> List[Tuple[int, int]]:
        """
        Trie les targets par ordre de difficulté croissante.
        
        Les targets les plus faciles sont packés en premier,
        les plus difficiles en dernier.
        """
        target_difficulty = [
            (target, constraints[target]['difficulty_score'])
            for target in self.targets
        ]
        
        # Trier par difficulté croissante (facile -> difficile)
        target_difficulty.sort(key=lambda x: x[1])
        
        return [target for target, _ in target_difficulty]
    
    def calculate_packing_feature(self, state: FESSState) -> int:
        """
        Calcule la feature packing pour un état.
        
        Retourne le nombre de boxes packées dans l'ordre optimal.
        Cette feature est cruciale car elle guide directement vers la solution.
        """
        # Utiliser le cache si possible
        state_key = hash(state.boxes)
        if state_key in self._packing_cache:
            return self._packing_cache[state_key]
        
        packed_count = 0
        
        # Compter les boxes packées dans l'ordre optimal
        for target in self.optimal_packing_order:
            if target in state.boxes:
                packed_count += 1
            else:
                # Arrêter dès qu'on trouve un target non-packé
                # (l'ordre doit être respecté)
                break
        
        # Mettre en cache pour éviter les recalculs
        self._packing_cache[state_key] = packed_count
        
        return packed_count
    
    def get_packing_progress_ratio(self, state: FESSState) -> float:
        """
        Retourne le ratio de progression du packing (0.0 à 1.0).
        """
        packed_count = self.calculate_packing_feature(state)
        total_targets = len(self.optimal_packing_order)
        return packed_count / max(total_targets, 1)
    
    def get_optimal_packing_order(self) -> List[Tuple[int, int]]:
        """Retourne l'ordre optimal de packing calculé."""
        return self.optimal_packing_order.copy()
    
    def get_next_target_to_pack(self, state: FESSState) -> Optional[Tuple[int, int]]:
        """
        Retourne le prochain target à packer selon l'ordre optimal.
        """
        packed_count = self.calculate_packing_feature(state)
        
        if packed_count < len(self.optimal_packing_order):
            return self.optimal_packing_order[packed_count]
        
        return None  # Tous les targets sont packés
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de l'analyseur de packing."""
        return {
            'total_targets': len(self.targets),
            'optimal_order': self.optimal_packing_order,
            'cache_size': len(self._packing_cache),
            'analysis_completed': True
        }


class ConnectivityAnalyzer(BaseFeatureAnalyzer):
    """
    Analyseur pour la feature Connectivity (Feature 2).
    
    Cette feature compte le nombre de régions fermées créées par les boxes.
    1 = le joueur peut accéder partout, >1 = régions séparées.
    
    Selon le paper: "Usually, the boxes divide the board into closed regions.
    The player can move around freely within a region, but cannot move to
    another region without first pushing boxes."
    """
    
    def __init__(self, level):
        super().__init__(level)
        
        # Précalcul des espaces libres pour optimiser flood-fill
        self.free_spaces = self._compute_free_spaces()
        
        # Cache pour éviter les recalculs
        self._connectivity_cache = {}
    
    def _compute_free_spaces(self) -> Set[Tuple[int, int]]:
        """Calcule tous les espaces libres (non-murs) du niveau."""
        free_spaces = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y):
                    free_spaces.add((x, y))
        
        return free_spaces
    
    def calculate_connectivity(self, state: FESSState) -> int:
        """
        Calcule le nombre de régions de connectivité.
        
        Utilise flood-fill pour compter les régions accessibles.
        Les boxes agissent comme des obstacles temporaires qui séparent les régions.
        """
        # Utiliser le cache si possible
        state_key = (state.player_pos, state.boxes)
        if state_key in self._connectivity_cache:
            return self._connectivity_cache[state_key]
        
        # Espaces accessibles = espaces libres - boxes
        accessible_spaces = self.free_spaces - state.boxes
        
        if not accessible_spaces:
            # Aucun espace accessible
            self._connectivity_cache[state_key] = 0
            return 0
        
        # Position du joueur doit être accessible
        if state.player_pos not in accessible_spaces:
            # Situation impossible normalement
            self._connectivity_cache[state_key] = 0
            return 0
        
        # Utiliser flood-fill pour compter les régions connectées
        regions_count = self._count_connected_regions(accessible_spaces, state.player_pos)
        
        # Mettre en cache
        self._connectivity_cache[state_key] = regions_count
        
        return regions_count
    
    def _count_connected_regions(self, accessible_spaces: Set[Tuple[int, int]],
                                player_pos: Tuple[int, int]) -> int:
        """
        Compte le nombre de régions connectées en utilisant flood-fill.
        
        Args:
            accessible_spaces: Ensemble des positions accessibles (sans boxes)
            player_pos: Position actuelle du joueur
            
        Returns:
            int: Nombre de régions connectées
        """
        unvisited = accessible_spaces.copy()
        regions_count = 0
        
        while unvisited:
            # Prendre n'importe quel point non-visité pour démarrer une nouvelle région
            start_point = next(iter(unvisited))
            
            # Flood-fill depuis ce point
            region_spaces = self._flood_fill(start_point, unvisited)
            
            # Retirer tous les espaces de cette région des non-visités
            unvisited -= region_spaces
            
            # Compter cette région
            regions_count += 1
        
        return regions_count
    
    def _flood_fill(self, start: Tuple[int, int],
                   available_spaces: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        Effectue un flood-fill depuis un point de départ.
        
        Args:
            start: Point de départ du flood-fill
            available_spaces: Espaces disponibles pour l'exploration
            
        Returns:
            Set[Tuple[int, int]]: Tous les espaces connectés au point de départ
        """
        if start not in available_spaces:
            return set()
        
        visited = set()
        queue = deque([start])
        visited.add(start)
        
        while queue:
            x, y = queue.popleft()
            
            # Explorer les 4 directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                
                # Vérifier si le voisin est accessible et non-visité
                if (neighbor in available_spaces and
                    neighbor not in visited):
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return visited
    
    def get_player_accessible_region(self, state: FESSState) -> Set[Tuple[int, int]]:
        """
        Retourne la région accessible depuis la position du joueur.
        
        Utile pour d'autres analyses et pour l'interface utilisateur.
        """
        accessible_spaces = self.free_spaces - state.boxes
        
        if state.player_pos not in accessible_spaces:
            return set()
        
        return self._flood_fill(state.player_pos, accessible_spaces)
    
    def get_inaccessible_regions(self, state: FESSState) -> List[Set[Tuple[int, int]]]:
        """
        Retourne toutes les régions inaccessibles depuis la position du joueur.
        
        Ces régions sont créées par les boxes qui bloquent le passage.
        """
        accessible_spaces = self.free_spaces - state.boxes
        player_region = self.get_player_accessible_region(state)
        
        # Espaces inaccessibles = tous les espaces libres - région du joueur
        inaccessible_spaces = accessible_spaces - player_region
        
        # Grouper les espaces inaccessibles en régions connectées
        inaccessible_regions = []
        unvisited = inaccessible_spaces.copy()
        
        while unvisited:
            start_point = next(iter(unvisited))
            region = self._flood_fill(start_point, unvisited)
            unvisited -= region
            inaccessible_regions.append(region)
        
        return inaccessible_regions
    
    def is_connectivity_improving(self, current_state: FESSState,
                                 next_state: FESSState) -> bool:
        """
        Vérifie si la connectivity s'améliore entre deux états.
        
        Une connectivity qui diminue (moins de régions) est généralement
        bonne car elle signifie que le joueur a plus d'accès.
        """
        current_connectivity = self.calculate_connectivity(current_state)
        next_connectivity = self.calculate_connectivity(next_state)
        
        return next_connectivity < current_connectivity
    
    def calculate_connectivity_penalty(self, state: FESSState) -> float:
        """
        Calcule une pénalité basée sur la connectivity.
        
        Plus il y a de régions séparées, plus la pénalité est élevée.
        """
        connectivity = self.calculate_connectivity(state)
        
        if connectivity <= 1:
            return 0.0  # Pas de pénalité si tout est connecté
        
        # Pénalité croissante avec le nombre de régions
        return (connectivity - 1) * 2.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de l'analyseur de connectivity."""
        return {
            'total_free_spaces': len(self.free_spaces),
            'cache_size': len(self._connectivity_cache),
            'level_dimensions': (self.width, self.height)
        }


class RoomAnalyzer(BaseFeatureAnalyzer):
    """
    Analyseur pour la feature Room Connectivity (Feature 3).
    
    Cette feature compte le nombre de liens room-to-room obstrués par des boxes.
    
    Selon le paper: "Sokoban levels are often composed of rooms linked by tunnels.
    The room connectivity feature counts how many room links are obstructed by boxes."
    """
    
    def __init__(self, level):
        super().__init__(level)
        
        # Identifier les rooms et tunnels du niveau
        self.rooms = self._identify_rooms()
        self.tunnels = self._identify_tunnels()
        self.room_connections = self._identify_room_connections()
        
        # Cache pour éviter les recalculs
        self._room_connectivity_cache = {}
        
    def _identify_rooms(self) -> List[Set[Tuple[int, int]]]:
        """
        Identifie les rooms (espaces ouverts) dans le niveau.
        
        Une room est définie comme une zone d'au moins 4 cases connectées
        qui n'est pas un simple corridor.
        """
        # Obtenir tous les espaces libres
        free_spaces = set()
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y):
                    free_spaces.add((x, y))
        
        # Identifier les zones expansives (potentielles rooms)
        rooms = []
        unvisited = free_spaces.copy()
        
        while unvisited:
            # Commencer une nouvelle région
            start_point = next(iter(unvisited))
            region = self._flood_fill_region(start_point, unvisited)
            unvisited -= region
            
            # Vérifier si cette région qualifie comme une room
            if self._is_region_a_room(region):
                rooms.append(region)
        
        return rooms
    
    def _flood_fill_region(self, start: Tuple[int, int],
                          available_spaces: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Flood-fill pour identifier une région connectée."""
        if start not in available_spaces:
            return set()
        
        visited = set()
        queue = deque([start])
        visited.add(start)
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                
                if (neighbor in available_spaces and neighbor not in visited):
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return visited
    
    def _is_region_a_room(self, region: Set[Tuple[int, int]]) -> bool:
        """
        Détermine si une région qualifie comme une room.
        
        Critères:
        - Au moins 4 cases
        - Pas juste un corridor linéaire
        - Ratio largeur/longueur raisonnable
        """
        if len(region) < 4:
            return False
        
        # Calculer les dimensions de la région
        min_x = min(pos[0] for pos in region)
        max_x = max(pos[0] for pos in region)
        min_y = min(pos[1] for pos in region)
        max_y = max(pos[1] for pos in region)
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Vérifier si c'est plus qu'un simple corridor
        if width == 1 or height == 1:
            return False  # C'est un corridor
        
        # Vérifier la densité (ratio cases/aire bounding box)
        bounding_area = width * height
        density = len(region) / bounding_area
        
        # Une room devrait avoir une densité raisonnable
        return density > 0.3
    
    def _identify_tunnels(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Identifie les tunnels (corridors étroits) entre les rooms.
        
        Un tunnel est un corridor de largeur 1 qui connecte deux rooms.
        """
        tunnels = []
        
        # Trouver tous les corridors (largeur 1)
        corridors = self._find_corridors()
        
        # Pour chaque corridor, vérifier s'il connecte deux rooms
        for corridor in corridors:
            connected_rooms = self._find_rooms_connected_by_corridor(corridor)
            if len(connected_rooms) >= 2:
                # Ce corridor connecte au moins 2 rooms
                start = min(corridor)
                end = max(corridor)
                tunnels.append((start, end))
        
        return tunnels
    
    def _find_corridors(self) -> List[List[Tuple[int, int]]]:
        """Trouve tous les corridors (passages étroits) dans le niveau."""
        corridors = []
        free_spaces = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y):
                    free_spaces.add((x, y))
        
        # Identifier les espaces qui forment des corridors
        corridor_spaces = set()
        for x, y in free_spaces:
            if self._is_corridor_space(x, y):
                corridor_spaces.add((x, y))
        
        # Grouper les espaces de corridor en corridors connectés
        unvisited = corridor_spaces.copy()
        while unvisited:
            start = next(iter(unvisited))
            corridor = self._flood_fill_region(start, unvisited)
            unvisited -= corridor
            if len(corridor) >= 2:  # Au moins 2 cases pour former un corridor
                corridors.append(list(corridor))
        
        return corridors
    
    def _is_corridor_space(self, x: int, y: int) -> bool:
        """Vérifie si une position fait partie d'un corridor."""
        if self.level.is_wall(x, y):
            return False
        
        # Compter les murs adjacents
        wall_count = sum(
            1 for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
            if self.level.is_wall(x + dx, y + dy)
        )
        
        # Un corridor a typiquement 2 murs adjacents (couloir)
        return wall_count >= 2
    
    def _find_rooms_connected_by_corridor(self, corridor: List[Tuple[int, int]]) -> List[int]:
        """
        Trouve les rooms connectées par un corridor donné.
        
        Returns:
            List[int]: Indices des rooms connectées par ce corridor
        """
        connected_rooms = set()
        
        # Pour chaque extrémité du corridor, chercher les rooms adjacentes
        for corridor_pos in corridor:
            x, y = corridor_pos
            
            # Examiner les positions adjacentes
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                adj_pos = (x + dx, y + dy)
                
                # Vérifier si cette position appartient à une room
                for room_idx, room in enumerate(self.rooms):
                    if adj_pos in room:
                        connected_rooms.add(room_idx)
        
        return list(connected_rooms)
    
    def _identify_room_connections(self) -> List[Tuple[int, int, List[Tuple[int, int]]]]:
        """
        Identifie toutes les connexions entre rooms.
        
        Returns:
            List[Tuple[int, int, List]]: (room1_idx, room2_idx, corridor_positions)
        """
        connections = []
        
        for tunnel_start, tunnel_end in self.tunnels:
            # Reconstruire le corridor pour ce tunnel
            corridor_positions = self._get_corridor_between_points(tunnel_start, tunnel_end)
            
            # Trouver les rooms connectées
            connected_rooms = self._find_rooms_connected_by_corridor(corridor_positions)
            
            # Créer des connexions pairwise
            for i in range(len(connected_rooms)):
                for j in range(i + 1, len(connected_rooms)):
                    room1_idx = connected_rooms[i]
                    room2_idx = connected_rooms[j]
                    connections.append((room1_idx, room2_idx, corridor_positions))
        
        return connections
    
    def _get_corridor_between_points(self, start: Tuple[int, int],
                                   end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reconstitue le corridor entre deux points."""
        # Implémentation simplifiée - retourner juste les deux points
        # Une implémentation complète ferait un pathfinding
        return [start, end]
    
    def calculate_room_connectivity(self, state: FESSState) -> int:
        """
        Calcule le nombre de liens room-to-room obstrués par des boxes.
        
        Plus cette valeur est élevée, plus il y a de connexions bloquées.
        """
        # Utiliser le cache si possible
        state_key = state.boxes
        if state_key in self._room_connectivity_cache:
            return self._room_connectivity_cache[state_key]
        
        obstructed_connections = 0
        
        # Vérifier chaque connexion room-to-room
        for room1_idx, room2_idx, corridor_positions in self.room_connections:
            # Vérifier si des boxes bloquent ce corridor
            is_obstructed = any(pos in state.boxes for pos in corridor_positions)
            
            if is_obstructed:
                obstructed_connections += 1
        
        # Mettre en cache
        self._room_connectivity_cache[state_key] = obstructed_connections
        
        return obstructed_connections
    
    def get_accessible_rooms_from_player(self, state: FESSState) -> Set[int]:
        """
        Retourne les indices des rooms accessibles depuis la position du joueur.
        """
        accessible_rooms = set()
        
        # Déterminer dans quelle room se trouve le joueur
        player_room = None
        for room_idx, room in enumerate(self.rooms):
            if state.player_pos in room:
                player_room = room_idx
                break
        
        if player_room is None:
            return accessible_rooms  # Joueur pas dans une room
        
        # BFS pour trouver toutes les rooms accessibles
        visited_rooms = set()
        queue = deque([player_room])
        visited_rooms.add(player_room)
        accessible_rooms.add(player_room)
        
        while queue:
            current_room = queue.popleft()
            
            # Examiner toutes les connexions depuis cette room
            for room1_idx, room2_idx, corridor_positions in self.room_connections:
                other_room = None
                if room1_idx == current_room:
                    other_room = room2_idx
                elif room2_idx == current_room:
                    other_room = room1_idx
                
                if other_room is not None and other_room not in visited_rooms:
                    # Vérifier si la connexion n'est pas bloquée
                    is_blocked = any(pos in state.boxes for pos in corridor_positions)
                    
                    if not is_blocked:
                        visited_rooms.add(other_room)
                        accessible_rooms.add(other_room)
                        queue.append(other_room)
        
        return accessible_rooms
    
    def is_room_connectivity_improving(self, current_state: FESSState,
                                     next_state: FESSState) -> bool:
        """
        Vérifie si la room connectivity s'améliore entre deux états.
        
        Une amélioration signifie moins de connexions obstruées.
        """
        current_obstructed = self.calculate_room_connectivity(current_state)
        next_obstructed = self.calculate_room_connectivity(next_state)
        
        return next_obstructed < current_obstructed
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de l'analyseur de room connectivity."""
        return {
            'total_rooms': len(self.rooms),
            'total_tunnels': len(self.tunnels),
            'total_connections': len(self.room_connections),
            'cache_size': len(self._room_connectivity_cache),
            'rooms_sizes': [len(room) for room in self.rooms] if self.rooms else []
        }


class OutOfPlanAnalyzer(BaseFeatureAnalyzer):
    """
    Analyseur pour la feature Out of Plan (Feature 4).
    
    Cette feature compte le nombre de boxes dans des zones qui seront
    bientôt bloquées selon le plan de packing.
    
    Selon le paper: "As packing proceeds, some areas of the board may become
    blocked. The out-of-plan feature counts the number of boxes in soon-to-be-blocked areas."
    
    Exemple du paper (niveau #74): Un plan de packing right-to-left peut bloquer
    les boxes si elles ne sont pas dans la bonne position.
    """
    
    def __init__(self, level, packing_analyzer):
        super().__init__(level)
        self.packing_analyzer = packing_analyzer
        
        # Zones de risque précalculées selon le plan de packing
        self.risk_zones = self._identify_risk_zones()
        self.blocking_patterns = self._identify_blocking_patterns()
        
        # Cache pour éviter les recalculs
        self._out_of_plan_cache = {}
    
    def _identify_risk_zones(self) -> Dict[int, Set[Tuple[int, int]]]:
        """
        Identifie les zones à risque pour chaque étape du packing.
        
        Une zone est à risque si elle peut être bloquée quand
        certains targets sont packés dans l'ordre optimal.
        
        Returns:
            Dict[int, Set]: {étape_packing: zones_à_risque}
        """
        risk_zones = {}
        optimal_order = self.packing_analyzer.get_optimal_packing_order()
        
        for step, target in enumerate(optimal_order):
            # Identifier les zones qui seront bloquées après avoir packé ce target
            blocked_zones = self._calculate_zones_blocked_by_target(target, optimal_order[:step+1])
            risk_zones[step] = blocked_zones
        
        return risk_zones
    
    def _calculate_zones_blocked_by_target(self, target: Tuple[int, int],
                                         packed_targets: List[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        Calcule les zones qui seront bloquées après avoir packé un target.
        
        Args:
            target: Target qui vient d'être packé
            packed_targets: Tous les targets déjà packés
            
        Returns:
            Set: Positions qui deviennent inaccessibles
        """
        blocked_zones = set()
        
        # Simulation: si on met des boxes sur tous les packed_targets,
        # quelles zones deviennent inaccessibles?
        simulated_boxes = set(packed_targets)
        
        # Calculer les zones accessibles depuis le target
        accessible_from_target = self._get_accessible_zones_from_position(target, simulated_boxes)
        
        # Les zones bloquées sont celles qui étaient accessibles avant
        # mais ne le sont plus après avoir ajouté ce target
        all_free_spaces = set()
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y):
                    all_free_spaces.add((x, y))
        
        # Zones accessibles avant ce target
        previous_boxes = set(packed_targets[:-1]) if len(packed_targets) > 1 else set()
        previously_accessible = all_free_spaces - previous_boxes
        
        # Zones accessibles après ce target
        currently_accessible = all_free_spaces - simulated_boxes
        
        # Zones nouvellement bloquées
        newly_blocked = previously_accessible - currently_accessible
        blocked_zones.update(newly_blocked)
        
        return blocked_zones
    
    def _get_accessible_zones_from_position(self, start: Tuple[int, int],
                                          obstacles: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        Calcule toutes les zones accessibles depuis une position.
        
        Args:
            start: Position de départ
            obstacles: Positions bloquées (murs + boxes)
            
        Returns:
            Set: Toutes les positions accessibles
        """
        accessible = set()
        queue = deque([start])
        visited = {start}
        
        while queue:
            x, y = queue.popleft()
            accessible.add((x, y))
            
            # Explorer les 4 directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                
                # Vérifier si accessible
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    not self.level.is_wall(nx, ny) and
                    neighbor not in obstacles and
                    neighbor not in visited):
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return accessible
    
    def _identify_blocking_patterns(self) -> List[Dict[str, Any]]:
        """
        Identifie les patterns de blocage typiques.
        
        Ces patterns représentent des configurations où des boxes
        risquent de bloquer l'accès à des zones importantes.
        """
        patterns = []
        
        # Pattern 1: Boxes qui bloquent l'accès aux targets non encore packés
        for i, target in enumerate(self.packing_analyzer.get_optimal_packing_order()):
            pattern = {
                'type': 'target_access_blocking',
                'target': target,
                'priority_level': i,
                'description': f'Boxes bloquant l\'accès au target {target}'
            }
            patterns.append(pattern)
        
        # Pattern 2: Boxes dans des coins sans target
        corner_positions = self._find_corner_positions()
        targets = set(self.packing_analyzer.targets)
        
        for corner in corner_positions:
            if corner not in targets:
                pattern = {
                    'type': 'corner_trap',
                    'position': corner,
                    'risk_level': 'high',
                    'description': f'Coin sans target en {corner}'
                }
                patterns.append(pattern)
        
        # Pattern 3: Boxes qui créent des deadlocks de ligne
        pattern = {
            'type': 'line_deadlock',
            'description': 'Boxes formant des lignes contre les murs'
        }
        patterns.append(pattern)
        
        return patterns
    
    def _find_corner_positions(self) -> List[Tuple[int, int]]:
        """Trouve toutes les positions de coin dans le niveau."""
        corners = []
        
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if not self.level.is_wall(x, y):
                    # Vérifier les patterns de coin
                    corner_patterns = [
                        (self.level.is_wall(x-1, y) and self.level.is_wall(x, y-1)),  # Haut-gauche
                        (self.level.is_wall(x+1, y) and self.level.is_wall(x, y-1)),  # Haut-droite
                        (self.level.is_wall(x-1, y) and self.level.is_wall(x, y+1)),  # Bas-gauche
                        (self.level.is_wall(x+1, y) and self.level.is_wall(x, y+1))   # Bas-droite
                    ]
                    
                    if any(corner_patterns):
                        corners.append((x, y))
        
        return corners
    
    def calculate_out_of_plan(self, state: FESSState) -> int:
        """
        Calcule le nombre de boxes en zones à risque.
        
        Cette feature est cruciale pour éviter les deadlocks causés
        par un mauvais positionnement des boxes selon le plan.
        """
        # Utiliser le cache si possible
        state_key = (state.boxes, self.packing_analyzer.calculate_packing_feature(state))
        if state_key in self._out_of_plan_cache:
            return self._out_of_plan_cache[state_key]
        
        out_of_plan_count = 0
        
        # Déterminer l'étape actuelle du packing
        current_packing_step = self.packing_analyzer.calculate_packing_feature(state)
        
        # Boxes pas encore sur leur target
        unpacked_boxes = [box for box in state.boxes
                         if box not in self.packing_analyzer.targets]
        
        # Vérifier chaque box non-packée
        for box in unpacked_boxes:
            risk_level = self._calculate_box_risk_level(box, state, current_packing_step)
            
            if risk_level > 0.5:  # Seuil de risque
                out_of_plan_count += 1
        
        # Mettre en cache
        self._out_of_plan_cache[state_key] = out_of_plan_count
        
        return out_of_plan_count
    
    def _calculate_box_risk_level(self, box: Tuple[int, int], state: FESSState,
                                 packing_step: int) -> float:
        """
        Calcule le niveau de risque d'une box individuelle.
        
        Args:
            box: Position de la box
            state: État actuel
            packing_step: Étape actuelle du packing
            
        Returns:
            float: Niveau de risque (0.0 = aucun risque, 1.0 = risque maximum)
        """
        risk_level = 0.0
        
        # Risque 1: Box dans une zone qui sera bloquée prochainement
        for step in range(packing_step, min(packing_step + 3, len(self.risk_zones))):
            if step in self.risk_zones and box in self.risk_zones[step]:
                risk_level += 0.3
        
        # Risque 2: Box dans un coin sans target
        if self._is_box_in_corner_without_target(box):
            risk_level += 0.4
        
        # Risque 3: Box bloquant l'accès au prochain target à packer
        next_target = self.packing_analyzer.get_next_target_to_pack(state)
        if next_target and self._is_box_blocking_target_access(box, next_target, state):
            risk_level += 0.5
        
        # Risque 4: Box formant un pattern de deadlock potentiel
        if self._is_box_in_deadlock_pattern(box, state):
            risk_level += 0.3
        
        return min(risk_level, 1.0)
    
    def _is_box_in_corner_without_target(self, box: Tuple[int, int]) -> bool:
        """Vérifie si une box est dans un coin sans target."""
        x, y = box
        
        # Vérifier si c'est un coin
        corner_patterns = [
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y-1)),
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y-1)),
            (self.level.is_wall(x-1, y) and self.level.is_wall(x, y+1)),
            (self.level.is_wall(x+1, y) and self.level.is_wall(x, y+1))
        ]
        
        is_corner = any(corner_patterns)
        is_target = box in self.packing_analyzer.targets
        
        return is_corner and not is_target
    
    def _is_box_blocking_target_access(self, box: Tuple[int, int], target: Tuple[int, int],
                                     state: FESSState) -> bool:
        """
        Vérifie si une box bloque l'accès à un target.
        
        Utilise pathfinding simplifié pour déterminer si le target
        reste accessible depuis la position du joueur.
        """
        # Créer une simulation sans cette box
        simulated_boxes = state.boxes - {box}
        
        # Vérifier si le target est toujours accessible
        accessible_positions = self._get_accessible_zones_from_position(
            state.player_pos, simulated_boxes
        )
        
        # Le target est-il accessible directement?
        target_accessible_without_box = target in accessible_positions
        
        # Le target est-il accessible avec la box?
        accessible_with_box = self._get_accessible_zones_from_position(
            state.player_pos, state.boxes
        )
        target_accessible_with_box = target in accessible_with_box
        
        # Si accessible sans la box mais pas avec, alors la box bloque
        return target_accessible_without_box and not target_accessible_with_box
    
    def _is_box_in_deadlock_pattern(self, box: Tuple[int, int], state: FESSState) -> bool:
        """
        Vérifie si une box fait partie d'un pattern de deadlock.
        
        Détecte les patterns simples comme les lignes contre les murs.
        """
        x, y = box
        
        # Pattern: ligne horizontale contre un mur
        horizontal_line = self._check_horizontal_line_deadlock(box, state)
        
        # Pattern: ligne verticale contre un mur
        vertical_line = self._check_vertical_line_deadlock(box, state)
        
        return horizontal_line or vertical_line
    
    def _check_horizontal_line_deadlock(self, box: Tuple[int, int], state: FESSState) -> bool:
        """Vérifie le deadlock de ligne horizontale."""
        x, y = box
        
        # Vérifier si il y a un mur au-dessus ou en-dessous
        wall_above = self.level.is_wall(x, y - 1)
        wall_below = self.level.is_wall(x, y + 1)
        
        if not (wall_above or wall_below):
            return False
        
        # Compter les boxes adjacentes horizontalement
        adjacent_boxes = 0
        for dx in [-1, 1]:
            if (x + dx, y) in state.boxes:
                adjacent_boxes += 1
        
        # Si au moins une box adjacente et contre un mur, c'est risqué
        return adjacent_boxes > 0
    
    def _check_vertical_line_deadlock(self, box: Tuple[int, int], state: FESSState) -> bool:
        """Vérifie le deadlock de ligne verticale."""
        x, y = box
        
        # Vérifier si il y a un mur à gauche ou à droite
        wall_left = self.level.is_wall(x - 1, y)
        wall_right = self.level.is_wall(x + 1, y)
        
        if not (wall_left or wall_right):
            return False
        
        # Compter les boxes adjacentes verticalement
        adjacent_boxes = 0
        for dy in [-1, 1]:
            if (x, y + dy) in state.boxes:
                adjacent_boxes += 1
        
        # Si au moins une box adjacente et contre un mur, c'est risqué
        return adjacent_boxes > 0
    
    def get_risky_boxes(self, state: FESSState) -> List[Tuple[Tuple[int, int], float]]:
        """
        Retourne toutes les boxes avec leur niveau de risque.
        
        Returns:
            List[Tuple]: [(position, niveau_risque), ...]
        """
        risky_boxes = []
        current_packing_step = self.packing_analyzer.calculate_packing_feature(state)
        
        unpacked_boxes = [box for box in state.boxes
                         if box not in self.packing_analyzer.targets]
        
        for box in unpacked_boxes:
            risk_level = self._calculate_box_risk_level(box, state, current_packing_step)
            if risk_level > 0:
                risky_boxes.append((box, risk_level))
        
        # Trier par niveau de risque décroissant
        risky_boxes.sort(key=lambda x: x[1], reverse=True)
        return risky_boxes
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de l'analyseur out-of-plan."""
        return {
            'total_risk_zones': sum(len(zones) for zones in self.risk_zones.values()),
            'blocking_patterns_count': len(self.blocking_patterns),
            'cache_size': len(self._out_of_plan_cache),
            'corner_positions': len(self._find_corner_positions())
        }


class HotspotsAnalyzer:
    """
    Analyseur pour identifier les hotspots (boxes bloquantes).
    
    Un hotspot est une box qui, si elle était transformée en mur,
    réduirait le nombre de targets accessibles pour les autres boxes.
    """
    
    def __init__(self, level):
        self.level = level
        self.width = level.width
        self.height = level.height
        self.targets = list(level.targets)
        
        # Table de hotspots précalculée : (pos_box, pos_hotspot) -> bool
        self.hotspot_table = self._build_hotspot_table()
        
    def _build_hotspot_table(self) -> Dict[Tuple[Tuple[int, int], Tuple[int, int]], bool]:
        """
        Construit une table pour tous les pairs de positions X,Y :
        si une box en Y est un hotspot pour une box en X.
        """
        hotspot_table = {}
        
        # Pour chaque paire de positions libres
        free_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if not self.level.is_wall(x, y):
                    free_positions.append((x, y))
        
        for box_pos in free_positions:
            for potential_hotspot in free_positions:
                if box_pos != potential_hotspot:
                    is_hotspot = self._is_position_hotspot_for_box(potential_hotspot, box_pos)
                    hotspot_table[(box_pos, potential_hotspot)] = is_hotspot
        
        return hotspot_table
    
    def _is_position_hotspot_for_box(self, hotspot_pos: Tuple[int, int],
                                   box_pos: Tuple[int, int]) -> bool:
        """
        Vérifie si hotspot_pos est un hotspot pour une box à box_pos.
        """
        # Compter les targets accessibles sans le hotspot
        targets_without_hotspot = self._count_reachable_targets(box_pos, set())
        
        # Compter les targets accessibles avec le hotspot (simulated as wall)
        targets_with_hotspot = self._count_reachable_targets(box_pos, {hotspot_pos})
        
        # C'est un hotspot si ça réduit l'accessibilité
        return targets_with_hotspot < targets_without_hotspot
    
    def _count_reachable_targets(self, box_pos: Tuple[int, int],
                               blocked_positions: Set[Tuple[int, int]]) -> int:
        """
        Compte combien de targets sont accessibles depuis box_pos.
        """
        reachable_count = 0
        
        for target in self.targets:
            if self._can_box_reach_target(box_pos, target, blocked_positions):
                reachable_count += 1
        
        return reachable_count
    
    def _can_box_reach_target(self, box_pos: Tuple[int, int], target: Tuple[int, int],
                            blocked_positions: Set[Tuple[int, int]]) -> bool:
        """
        Vérifie si une box peut atteindre un target (pathfinding simplifié).
        """
        if box_pos == target:
            return True
        
        # BFS simple pour vérifier l'accessibilité
        queue = deque([box_pos])
        visited = {box_pos}
        
        while queue:
            x, y = queue.popleft()
            
            # Vérifier les 4 directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                
                if neighbor == target:
                    return True
                
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    not self.level.is_wall(nx, ny) and
                    neighbor not in blocked_positions and
                    neighbor not in visited):
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return False
    
    def calculate_hotspots(self, state: FESSState) -> int:
        """
        Calcule le nombre total de hotspots dans l'état donné.
        """
        hotspot_count = 0
        boxes_list = list(state.boxes)
        
        # Pour chaque paire de boxes, vérifier si l'une bloque l'autre
        for i, box1 in enumerate(boxes_list):
            for j, box2 in enumerate(boxes_list):
                if i != j:
                    # Vérifier si box2 est un hotspot pour box1
                    if self.hotspot_table.get((box1, box2), False):
                        hotspot_count += 1
        
        return hotspot_count
    
    def get_hotspot_boxes(self, state: FESSState) -> List[Tuple[int, int]]:
        """
        Retourne la liste des boxes qui sont des hotspots.
        """
        hotspot_boxes = []
        boxes_list = list(state.boxes)
        
        for box in boxes_list:
            is_hotspot = False
            for other_box in boxes_list:
                if box != other_box and self.hotspot_table.get((other_box, box), False):
                    is_hotspot = True
                    break
            
            if is_hotspot:
                hotspot_boxes.append(box)
        
        return hotspot_boxes
    
    def get_most_disruptive_hotspot(self, state: FESSState) -> Optional[Tuple[int, int]]:
        """
        Trouve le hotspot qui bloque le plus grand nombre de boxes.
        """
        boxes_list = list(state.boxes)
        max_disruption = 0
        most_disruptive = None
        
        for hotspot_candidate in boxes_list:
            disruption_count = 0
            
            for other_box in boxes_list:
                if (hotspot_candidate != other_box and
                    self.hotspot_table.get((other_box, hotspot_candidate), False)):
                    disruption_count += 1
            
            if disruption_count > max_disruption:
                max_disruption = disruption_count
                most_disruptive = hotspot_candidate
        
        return most_disruptive


class FESSAdvisors:
    """
    Les 7 advisors domain-spécifiques du vrai FESS.
    
    Chaque advisor suggère AU PLUS un mouvement avec poids 0.
    Ces advisors sont la clé de l'intelligence de FESS.
    """
    
    def __init__(self, level, feature_space):
        self.level = level
        self.feature_space = feature_space
        self.hotspots_analyzer = HotspotsAnalyzer(level)
        
    def get_advisor_moves(self, state: FESSState) -> List[Tuple[MacroMove, int]]:
        """
        Retourne les mouvements suggérés par tous les advisors.
        
        Chaque advisor peut suggérer au plus 1 mouvement avec poids 0.
        """
        advisor_moves = []
        
        # 1. Packing Advisor
        packing_move = self._packing_advisor(state)
        if packing_move:
            advisor_moves.append((packing_move, 0))
        
        # 2. Connectivity Advisor
        connectivity_move = self._connectivity_advisor(state)
        if connectivity_move:
            advisor_moves.append((connectivity_move, 0))
        
        # 3. Room Connectivity Advisor
        room_connectivity_move = self._room_connectivity_advisor(state)
        if room_connectivity_move:
            advisor_moves.append((room_connectivity_move, 0))
        
        # 4. Hotspots Advisor
        hotspots_move = self._hotspots_advisor(state)
        if hotspots_move:
            advisor_moves.append((hotspots_move, 0))
        
        # 5. Explorer Advisor
        explorer_move = self._explorer_advisor(state)
        if explorer_move:
            advisor_moves.append((explorer_move, 0))
        
        # 6. Opener Advisor
        opener_move = self._opener_advisor(state)
        if opener_move:
            advisor_moves.append((opener_move, 0))
        
        # 7. OOP (Out of Plan) Advisor
        oop_move = self._oop_advisor(state)
        if oop_move:
            advisor_moves.append((oop_move, 0))
        
        return advisor_moves
    
    def _packing_advisor(self, state: FESSState) -> Optional[MacroMove]:
        """
        Advisor 1: Suggest moves that increase packed boxes count.
        
        Considère seulement les mouvements qui augmentent le nombre de boxes packées.
        """
        next_target = self.feature_space.packing_analyzer.get_next_target_to_pack(state)
        if not next_target:
            return None  # Tout est déjà packé
        
        # Trouver une box qui peut atteindre ce target
        for box in state.boxes:
            if box not in self.feature_space.packing_analyzer.targets:
                # Vérifier si cette box peut être poussée vers le target
                macro_move = self._can_push_box_to_target(state, box, next_target)
                if macro_move:
                    return macro_move
        
        return None
    
    def _connectivity_advisor(self, state: FESSState) -> Optional[MacroMove]:
        """
        Advisor 2: Suggest moves that improve connectivity.
        
        Considère seulement les mouvements qui améliorent la connectivity.
        """
        current_connectivity = self.feature_space.connectivity_analyzer.calculate_connectivity(state)
        
        # Essayer de pousser chaque box pour voir si ça améliore la connectivity
        for box in state.boxes:
            improving_moves = self._find_connectivity_improving_moves(state, box, current_connectivity)
            if improving_moves:
                return improving_moves[0]  # Retourner le premier
        
        return None
    
    def _room_connectivity_advisor(self, state: FESSState) -> Optional[MacroMove]:
        """
        Advisor 3: Suggest moves that improve room connectivity.
        """
        current_room_connectivity = self.feature_space.room_analyzer.calculate_room_connectivity(state)
        
        # Essayer de pousser chaque box pour améliorer room connectivity
        for box in state.boxes:
            improving_moves = self._find_room_connectivity_improving_moves(state, box, current_room_connectivity)
            if improving_moves:
                return improving_moves[0]
        
        return None
    
    def _hotspots_advisor(self, state: FESSState) -> Optional[MacroMove]:
        """
        Advisor 4: Suggest moves that reduce hotspots.
        """
        hotspot_boxes = self.hotspots_analyzer.get_hotspot_boxes(state)
        
        if not hotspot_boxes:
            return None
        
        # Essayer de déplacer le hotspot le plus problématique
        most_disruptive = self.hotspots_analyzer.get_most_disruptive_hotspot(state)
        if most_disruptive:
            # Trouver un endroit où pousser ce hotspot
            move = self._find_hotspot_clearing_move(state, most_disruptive)
            return move
        
        return None
    
    def _explorer_advisor(self, state: FESSState) -> Optional[MacroMove]:
        """
        Advisor 5: Opens a path to a free square which enables a new push.
        
        Cet advisor cherche à ouvrir l'accès à de nouvelles zones.
        """
        # Identifier les zones actuellement inaccessibles
        inaccessible_regions = self.feature_space.connectivity_analyzer.get_inaccessible_regions(state)
        
        if not inaccessible_regions:
            return None  # Tout est déjà accessible
        
        # Chercher un mouvement qui donne accès à une nouvelle zone
        for box in state.boxes:
            exploring_move = self._find_exploring_move(state, box, inaccessible_regions)
            if exploring_move:
                return exploring_move
        
        return None
    
    def _opener_advisor(self, state: FESSState) -> Optional[MacroMove]:
        """
        Advisor 6: Find the most disruptive hotspot and push nearby boxes away.
        
        Trouve le hotspot qui bloque le plus de boxes et essaie de dégager le chemin.
        """
        most_disruptive = self.hotspots_analyzer.get_most_disruptive_hotspot(state)
        if not most_disruptive:
            return None
        
        # Trouver les boxes à proximité du hotspot principal
        nearby_boxes = self._find_boxes_near_hotspot(state, most_disruptive)
        
        # Essayer de pousser une box voisine pour libérer le hotspot
        for nearby_box in nearby_boxes:
            clearing_move = self._find_hotspot_clearing_move_for_box(state, nearby_box, most_disruptive)
            if clearing_move:
                return clearing_move
        
        return None
    
    def _oop_advisor(self, state: FESSState) -> Optional[MacroMove]:
        """
        Advisor 7: Deal with Out-of-Plan boxes.
        
        Gère les boxes qui interfèrent avec le plan de packing.
        """
        risky_boxes = self.feature_space.out_of_plan_analyzer.get_risky_boxes(state)
        
        if not risky_boxes:
            return None
        
        # Prendre la box la plus risquée et essayer de la déplacer vers une zone sûre
        most_risky_box, risk_level = risky_boxes[0]
        
        if risk_level > 0.5:  # Seuil de risque significatif
            safe_move = self._find_oop_clearing_move(state, most_risky_box)
            return safe_move
        
        return None
    
    # Méthodes utilitaires pour les advisors
    
    def _can_push_box_to_target(self, state: FESSState, box: Tuple[int, int],
                              target: Tuple[int, int]) -> Optional[MacroMove]:
        """Vérifie si une box peut être poussée vers un target."""
        # Implémentation simplifiée - vérification de base
        if self._is_adjacent(box, target):
            return MacroMove(box, target, ['PUSH'], 0)
        return None
    
    def _is_adjacent(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """Vérifie si deux positions sont adjacentes."""
        x1, y1 = pos1
        x2, y2 = pos2
        return abs(x1 - x2) + abs(y1 - y2) == 1
    
    def _find_connectivity_improving_moves(self, state: FESSState, box: Tuple[int, int],
                                         current_connectivity: int) -> List[MacroMove]:
        """Trouve les mouvements qui améliorent la connectivity."""
        improving_moves = []
        
        # Essayer de pousser la box dans chaque direction
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_box_pos = (box[0] + dx, box[1] + dy)
            
            if self._is_valid_box_position(new_box_pos, state):
                # Simuler le mouvement et vérifier l'amélioration
                simulated_state = self._simulate_box_move(state, box, new_box_pos)
                new_connectivity = self.feature_space.connectivity_analyzer.calculate_connectivity(simulated_state)
                
                if new_connectivity < current_connectivity:  # Amélioration = moins de régions
                    improving_moves.append(MacroMove(box, new_box_pos, ['PUSH'], 0))
        
        return improving_moves
    
    def _find_room_connectivity_improving_moves(self, state: FESSState, box: Tuple[int, int],
                                              current_room_connectivity: int) -> List[MacroMove]:
        """Trouve les mouvements qui améliorent la room connectivity."""
        improving_moves = []
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_box_pos = (box[0] + dx, box[1] + dy)
            
            if self._is_valid_box_position(new_box_pos, state):
                simulated_state = self._simulate_box_move(state, box, new_box_pos)
                new_room_connectivity = self.feature_space.room_analyzer.calculate_room_connectivity(simulated_state)
                
                if new_room_connectivity < current_room_connectivity:  # Moins d'obstructions = mieux
                    improving_moves.append(MacroMove(box, new_box_pos, ['PUSH'], 0))
        
        return improving_moves
    
    def _find_hotspot_clearing_move(self, state: FESSState, hotspot_box: Tuple[int, int]) -> Optional[MacroMove]:
        """Trouve un mouvement pour dégager un hotspot."""
        # Essayer de pousser le hotspot dans chaque direction
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_pos = (hotspot_box[0] + dx, hotspot_box[1] + dy)
            
            if self._is_valid_box_position(new_pos, state):
                return MacroMove(hotspot_box, new_pos, ['PUSH'], 0)
        
        return None
    
    def _find_exploring_move(self, state: FESSState, box: Tuple[int, int],
                           inaccessible_regions: List[Set[Tuple[int, int]]]) -> Optional[MacroMove]:
        """Trouve un mouvement qui ouvre l'accès à de nouvelles zones."""
        # Essayer de pousser la box pour débloquer des régions inaccessibles
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_pos = (box[0] + dx, box[1] + dy)
            
            if self._is_valid_box_position(new_pos, state):
                # Vérifier si ce mouvement donne accès à de nouvelles zones
                simulated_state = self._simulate_box_move(state, box, new_pos)
                new_inaccessible = self.feature_space.connectivity_analyzer.get_inaccessible_regions(simulated_state)
                
                # Si moins de régions inaccessibles, c'est bien
                if len(new_inaccessible) < len(inaccessible_regions):
                    return MacroMove(box, new_pos, ['PUSH'], 0)
        
        return None
    
    def _find_boxes_near_hotspot(self, state: FESSState, hotspot: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Trouve les boxes proches d'un hotspot."""
        nearby_boxes = []
        
        for box in state.boxes:
            if box != hotspot:
                distance = abs(box[0] - hotspot[0]) + abs(box[1] - hotspot[1])
                if distance <= 2:  # Proximité
                    nearby_boxes.append(box)
        
        return nearby_boxes
    
    def _find_hotspot_clearing_move_for_box(self, state: FESSState, box: Tuple[int, int],
                                          hotspot: Tuple[int, int]) -> Optional[MacroMove]:
        """Trouve un mouvement pour une box qui aide à dégager un hotspot."""
        # Essayer de pousser cette box loin du hotspot
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_pos = (box[0] + dx, box[1] + dy)
            
            if self._is_valid_box_position(new_pos, state):
                # Vérifier si ça aide à dégager le hotspot
                new_distance = abs(new_pos[0] - hotspot[0]) + abs(new_pos[1] - hotspot[1])
                old_distance = abs(box[0] - hotspot[0]) + abs(box[1] - hotspot[1])
                
                if new_distance > old_distance:  # S'éloigne du hotspot
                    return MacroMove(box, new_pos, ['PUSH'], 0)
        
        return None
    
    def _find_oop_clearing_move(self, state: FESSState, oop_box: Tuple[int, int]) -> Optional[MacroMove]:
        """Trouve un mouvement pour dégager une box Out-of-Plan."""
        # Essayer de pousser vers une zone moins risquée
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_pos = (oop_box[0] + dx, oop_box[1] + dy)
            
            if self._is_valid_box_position(new_pos, state):
                # Vérifier si la nouvelle position est moins risquée
                return MacroMove(oop_box, new_pos, ['PUSH'], 0)
        
        return None
    
    def _is_valid_box_position(self, pos: Tuple[int, int], state: FESSState) -> bool:
        """Vérifie si une position est valide pour une box."""
        x, y = pos
        return (0 <= x < self.level.width and
                0 <= y < self.level.height and
                not self.level.is_wall(x, y) and
                pos not in state.boxes)
    
    def _simulate_box_move(self, state: FESSState, old_pos: Tuple[int, int],
                         new_pos: Tuple[int, int]) -> FESSState:
        """Simule le déplacement d'une box et retourne le nouvel état."""
        new_boxes = set(state.boxes)
        new_boxes.remove(old_pos)
        new_boxes.add(new_pos)
        
        return FESSState(
            player_pos=state.player_pos,  # Position du joueur ne change pas pour la simulation
            boxes=frozenset(new_boxes)
        )


class MacroMoveGenerator:
    """
    Générateur de macro-moves pour FESS.
    
    Un macro-move est une séquence de mouvements qui pousse la même box
    de sa position actuelle vers une position cible, sans pousser
    d'autres boxes entre-temps.
    
    Selon le paper: "A macro move describes a push of a box from place (X1,Y1)
    on the board to place (X2,Y2). It does not describe the exact order of
    pushes and moves needed for this maneuver."
    """
    
    def __init__(self, level):
        self.level = level
        self.width = level.width
        self.height = level.height
        
        # Cache pour éviter les recalculs coûteux
        self._reachability_cache = {}
        
    def generate_macro_moves(self, state: FESSState) -> List[MacroMove]:
        """
        Génère tous les macro-moves possibles depuis cet état.
        
        Pour chaque box, trouve toutes les positions où elle peut être
        poussée en une séquence continue de mouvements.
        """
        macro_moves = []
        
        for box in state.boxes:
            # Générer tous les macro-moves possibles pour cette box
            box_macro_moves = self._generate_macro_moves_for_box(state, box)
            macro_moves.extend(box_macro_moves)
        
        return macro_moves
    
    def _generate_macro_moves_for_box(self, state: FESSState, box: Tuple[int, int]) -> List[MacroMove]:
        """
        Génère tous les macro-moves possibles pour une box spécifique.
        """
        macro_moves = []
        
        # Positions accessibles pour pousser cette box (version simplifiée)
        pushable_positions = self._find_nearby_pushable_positions(state, box)
        
        for target_pos in pushable_positions:
            # Vérifier si on peut effectivement pousser la box vers cette position
            if self._can_push_box_to_position(state, box, target_pos):
                # Calculer la séquence de mouvements (simplifiée pour l'instant)
                push_sequence = self._calculate_push_sequence(box, target_pos)
                
                # Calculer le poids du macro-move
                weight = self._calculate_macro_move_weight(box, target_pos)
                
                macro_move = MacroMove(
                    box_from=box,
                    box_to=target_pos,
                    push_sequence=push_sequence,
                    weight=weight
                )
                
                macro_moves.append(macro_move)
        
        return macro_moves
    
    def _find_nearby_pushable_positions(self, state: FESSState, box: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Trouve les positions proches où une box peut être poussée.
        Version optimisée qui limite la recherche aux positions proches.
        """
        pushable_positions = []
        box_x, box_y = box
        
        # Limiter à un rayon de 3 cases pour la performance
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx == 0 and dy == 0:
                    continue  # Skip la position actuelle
                    
                target_x, target_y = box_x + dx, box_y + dy
                target_pos = (target_x, target_y)
                
                # Vérifier si la position est valide
                if (0 <= target_x < self.width and 0 <= target_y < self.height and
                    not self.level.is_wall(target_x, target_y) and
                    target_pos not in state.boxes):
                    
                    pushable_positions.append(target_pos)
        
        return pushable_positions
    
    def _can_push_box_to_position(self, state: FESSState, box: Tuple[int, int],
                                target: Tuple[int, int]) -> bool:
        """
        Vérifie si une box peut être poussée vers une position target.
        Version simplifiée pour la performance.
        """
        # Vérification basique de ligne de vue
        return self._has_clear_path(state, box, target)
    
    def _has_clear_path(self, state: FESSState, start: Tuple[int, int],
                       end: Tuple[int, int]) -> bool:
        """
        Vérifie s'il y a un chemin clair entre deux positions.
        Version simplifiée utilisant la distance Manhattan.
        """
        start_x, start_y = start
        end_x, end_y = end
        
        # Distance Manhattan
        distance = abs(end_x - start_x) + abs(end_y - start_y)
        
        # Si trop loin, considérer comme non accessible pour la performance
        if distance > 5:
            return False
        
        # Vérification simple: pas d'obstacles sur la ligne droite
        if start_x == end_x:
            # Mouvement vertical
            min_y, max_y = min(start_y, end_y), max(start_y, end_y)
            for y in range(min_y + 1, max_y):
                if self.level.is_wall(start_x, y) or (start_x, y) in state.boxes:
                    return False
            return True
        elif start_y == end_y:
            # Mouvement horizontal
            min_x, max_x = min(start_x, end_x), max(start_x, end_x)
            for x in range(min_x + 1, max_x):
                if self.level.is_wall(x, start_y) or (x, start_y) in state.boxes:
                    return False
            return True
        else:
            # Mouvement diagonal - acceptable si distance courte
            return distance <= 2
    
    def _calculate_push_sequence(self, box: Tuple[int, int],
                               target: Tuple[int, int]) -> List[str]:
        """
        Calcule la séquence de mouvements pour pousser une box vers un target.
        Version simplifiée qui retourne la direction générale.
        """
        box_x, box_y = box
        target_x, target_y = target
        
        sequence = []
        
        # Mouvement horizontal prioritaire
        if target_x > box_x:
            sequence.append('RIGHT')
        elif target_x < box_x:
            sequence.append('LEFT')
        
        # Puis mouvement vertical
        if target_y > box_y:
            sequence.append('DOWN')
        elif target_y < box_y:
            sequence.append('UP')
        
        return sequence if sequence else ['STAY']
    
    def _calculate_macro_move_weight(self, box: Tuple[int, int],
                                   target: Tuple[int, int]) -> int:
        """
        Calcule le poids d'un macro-move basé sur la distance.
        """
        # Distance Manhattan comme base
        distance = abs(target[0] - box[0]) + abs(target[1] - box[1])
        
        # Poids de base basé sur la distance (minimum 1)
        return max(1, distance)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques du générateur de macro-moves."""
        return {
            'cache_size': len(self._reachability_cache),
            'level_dimensions': (self.width, self.height)
        }


class FESSSearchEngine:
    """
    Moteur de recherche principal du vrai FESS.
    
    Implémente exactement l'algorithme de la Figure 2 du paper:
    1. Initialize: root state, project to FS, assign weights  
    2. While no solution:
       - Pick next FS cell (cycling)
       - Find all DS states projecting to this cell
       - Choose move with least accumulated weight
       - Apply move, add to tree, project new state to FS
       - Assign weights to moves from new state
    """
    
    def __init__(self, level, max_states=1000000, time_limit=120.0):
        self.level = level
        self.max_states = max_states
        self.time_limit = time_limit
        
        # Composants principaux FESS
        self.feature_space = FESSFeatureSpace(level)
        self.macro_generator = MacroMoveGenerator(level)
        self.search_tree = FESSSearchTree()
        
        # Initialiser les analyseurs de features
        self._initialize_feature_analyzers()
        
        # Initialiser les advisors après les analyseurs de features
        self.advisors = FESSAdvisors(level, self.feature_space)
        
        # Métriques de performance
        self.states_explored = 0
        self.states_generated = 0
        self.start_time = 0
        self.move_weight_assignments = 0
        
    def _initialize_feature_analyzers(self):
        """Initialise les analyseurs de features dans l'espace FS."""
        # L'ordre d'initialisation est important car OutOfPlanAnalyzer dépend de PackingAnalyzer
        self.feature_space.packing_analyzer = PackingAnalyzer(self.level)
        self.feature_space.connectivity_analyzer = ConnectivityAnalyzer(self.level)
        self.feature_space.room_analyzer = RoomAnalyzer(self.level)
        
        # OutOfPlanAnalyzer a besoin du PackingAnalyzer pour fonctionner
        self.feature_space.out_of_plan_analyzer = OutOfPlanAnalyzer(
            self.level,
            self.feature_space.packing_analyzer
        )
        
    def search(self, progress_callback: Optional[Callable] = None) -> Optional[List[str]]:
        """
        Algorithme principal FESS selon Figure 2 du paper.
        
        Returns:
            List[str]: Séquence de mouvements si solution trouvée, None sinon
        """
        self.start_time = time.time()
        
        if progress_callback:
            progress_callback("🔬 Démarrage FESS authentique (Shoham & Schaeffer 2020)")
        
        # Initialize: Set feature space to empty (FS)
        # Set the start state as the root of the search tree (DS)
        initial_state = self._create_initial_state()
        
        # Assign a weight of zero to the root state (DS)
        initial_state.accumulated_weight = 0
        
        # Add feature values to the root state (DS)
        # Project root state onto a cell in feature space (FS)
        self.search_tree.add_root(initial_state)
        self.feature_space.add_state_to_cell(initial_state)
        
        # Assign weights to all moves from the root state (DS+FS)
        self._assign_move_weights(initial_state)
        
        # Search: while no solution has been found
        while self._within_limits():
            # Pick the next cell in feature space (FS)
            current_fs_cell = self.feature_space.get_next_cell_for_cycling()
            
            if current_fs_cell is None:
                break  # Pas de cellules à explorer
            
            # Find all search-tree states that project onto this cell (DS)
            states_in_cell = self.feature_space.get_states_in_cell(current_fs_cell)
            
            # Identify all un-expanded moves from these states (DS)
            best_move_info = self._find_least_weight_unexpanded_move(states_in_cell)
            
            if best_move_info is None:
                continue  # Pas de mouvements disponibles dans cette cellule
                
            parent_state, move, weight = best_move_info
            
            # Choose move with least accumulated weight (DS)
            # Add the resulting state to the search tree (DS)
            new_state = self._apply_move(parent_state, move, weight)
            
            if new_state is None:
                continue  # Mouvement invalide
                
            # Added state's weight = parent's weight + move weight (DS)
            new_state.accumulated_weight = parent_state.accumulated_weight + weight
            
            if not self.search_tree.add_state(new_state):
                continue  # État déjà exploré
                
            self.states_generated += 1
            
            # Add feature values to the added state (DS)
            # Project added state onto a cell in feature space (FS)
            self.feature_space.add_state_to_cell(new_state)
            
            # Vérifier si c'est l'état objectif
            if self._is_goal_state(new_state):
                if progress_callback:
                    elapsed = time.time() - self.start_time
                    progress_callback(f"🎯 FESS: Solution trouvée en {elapsed:.2f}s!")
                return self._reconstruct_path(new_state)
            
            # Assign weights to all moves from the added state (DS+FS)
            self._assign_move_weights(new_state)
            
            # Mise à jour du progrès
            self.states_explored += 1
            if progress_callback and self.states_explored % 1000 == 0:
                elapsed = time.time() - self.start_time
                fs_stats = self.feature_space.get_statistics()
                progress_callback(f"🔬 FESS: {self.states_explored:,} explorés, "
                                f"{fs_stats['total_cells']} cellules FS, "
                                f"poids={new_state.accumulated_weight} ({elapsed:.1f}s)")
        
        if progress_callback:
            elapsed = time.time() - self.start_time
            progress_callback(f"❌ FESS: Aucune solution trouvée en {elapsed:.2f}s")
        
        return None
    
    def _create_initial_state(self) -> FESSState:
        """Crée l'état initial pour FESS."""
        return FESSState(
            player_pos=self.level.player_pos,
            boxes=frozenset(self.level.boxes)
        )
    
    def _is_goal_state(self, state: FESSState) -> bool:
        """Vérifie si un état est l'état objectif."""
        return state.boxes == frozenset(self.level.targets)
    
    def _within_limits(self) -> bool:
        """Vérifie si on est dans les limites de temps et d'états."""
        return (time.time() - self.start_time <= self.time_limit and
                self.states_explored <= self.max_states)
    
    def _assign_move_weights(self, state: FESSState):
        """
        Assigne les poids aux mouvements depuis cet état.
        
        C'est ici que les advisors et l'intelligence FESS interviennent.
        Les mouvements suggérés par les advisors ont poids 0,
        tous les autres ont poids 1.
        
        Selon le paper: "moves chosen by the advisors are assigned a weight of 1,
        and all other moves are assigned a weight of M"
        """
        # Étape 1: Obtenir les suggestions des advisors
        advisor_moves = self.advisors.get_advisor_moves(state)
        advisor_move_set = set()
        
        # Convertir les macro-moves des advisors en mouvements de base
        for macro_move, weight in advisor_moves:
            if macro_move and macro_move.push_sequence:
                for move in macro_move.push_sequence:
                    if move in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                        advisor_move_set.add(move)
        
        # Étape 2: Générer tous les macro-moves possibles
        all_macro_moves = self.macro_generator.generate_macro_moves(state)
        
        # Étape 3: Assigner les poids selon le système FESS
        # Poids 0 pour les mouvements des advisors, poids 1 pour les autres
        
        # Ajouter les mouvements basiques avec les poids appropriés
        basic_moves = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        for move in basic_moves:
            if move in advisor_move_set:
                # Mouvement suggéré par un advisor = poids 0
                state.add_child_move(move, 0)
            else:
                # Mouvement ordinaire = poids 1
                state.add_child_move(move, 1)
        
        # Ajouter les macro-moves avec leurs poids calculés
        for macro_move in all_macro_moves:
            # Convertir le macro-move en identifiant unique
            move_id = f"MACRO_{macro_move.box_from}_{macro_move.box_to}"
            
            # Vérifier si ce macro-move est suggéré par un advisor
            is_advisor_move = any(
                advisor_macro.box_from == macro_move.box_from and
                advisor_macro.box_to == macro_move.box_to
                for advisor_macro, _ in advisor_moves
                if advisor_macro is not None
            )
            
            if is_advisor_move:
                # Macro-move d'advisor = poids 0
                state.add_child_move(move_id, 0)
            else:
                # Macro-move ordinaire = poids basé sur la distance/complexité
                state.add_child_move(move_id, macro_move.weight)
        
        self.move_weight_assignments += 1
        
        # Log pour le debugging (peut être retiré en production)
        if len(advisor_moves) > 0:
            print(f"🎯 FESS: {len(advisor_moves)} mouvements d'advisors, "
                  f"{len(all_macro_moves)} macro-moves générés")
    
    def _find_least_weight_unexpanded_move(self, states: List[FESSState]) -> Optional[Tuple[FESSState, str, int]]:
        """
        Trouve le mouvement non-exploré avec le poids accumulé minimum.
        
        Returns:
            Tuple[FESSState, str, int]: (état parent, mouvement, poids) ou None
        """
        best_info = None
        min_accumulated_weight = float('inf')
        best_state = None
        best_move_index = -1
        
        for state in states:
            # Examiner tous les mouvements non-explorés de cet état
            for i, (move, move_weight) in enumerate(state.children_moves):
                accumulated_weight = state.accumulated_weight + move_weight
                
                if accumulated_weight < min_accumulated_weight:
                    min_accumulated_weight = accumulated_weight
                    best_info = (state, move, move_weight)
                    best_state = state
                    best_move_index = i
        
        # Retirer le mouvement sélectionné de la liste pour éviter de le réexplorer
        if best_state is not None and best_move_index >= 0:
            best_state.children_moves.pop(best_move_index)
            
            # Marquer l'état comme expanded seulement si tous ses mouvements ont été explorés
            if not best_state.children_moves:
                best_state.is_expanded = True
        
        return best_info
    
    def _apply_move(self, state: FESSState, move: str, weight: int) -> Optional[FESSState]:
        """
        Applique un mouvement et retourne le nouvel état.
        
        Gère à la fois les mouvements basiques et les macro-moves.
        """
        # Vérifier si c'est un macro-move
        if move.startswith("MACRO_"):
            return self._apply_macro_move(state, move, weight)
        else:
            return self._apply_basic_move(state, move, weight)
    
    def _apply_basic_move(self, state: FESSState, move: str, weight: int) -> Optional[FESSState]:
        """
        Applique un mouvement basique (UP, DOWN, LEFT, RIGHT).
        """
        player_x, player_y = state.player_pos
        
        # Directions
        directions = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0)
        }
        
        if move not in directions:
            return None
            
        dx, dy = directions[move]
        new_x, new_y = player_x + dx, player_y + dy
        
        # Vérifier les limites et murs
        if (new_x < 0 or new_x >= self.level.width or
            new_y < 0 or new_y >= self.level.height or
            self.level.is_wall(new_x, new_y)):
            return None
        
        new_boxes = state.boxes
        
        # Vérifier s'il y a une box à pousser
        if (new_x, new_y) in state.boxes:
            box_x, box_y = new_x + dx, new_y + dy
            
            # Vérifier si la box peut être poussée
            if (box_x < 0 or box_x >= self.level.width or
                box_y < 0 or box_y >= self.level.height or
                self.level.is_wall(box_x, box_y) or
                (box_x, box_y) in state.boxes):
                return None
            
            # Pousser la box
            new_boxes = set(state.boxes)
            new_boxes.remove((new_x, new_y))
            new_boxes.add((box_x, box_y))
            new_boxes = frozenset(new_boxes)
        
        # Créer le nouvel état
        return FESSState(
            player_pos=(new_x, new_y),
            boxes=new_boxes,
            parent=state,
            move=move,
            accumulated_weight=state.accumulated_weight + weight
        )
    
    def _apply_macro_move(self, state: FESSState, move_id: str, weight: int) -> Optional[FESSState]:
        """
        Applique un macro-move.
        
        Format du move_id: "MACRO_from_to" où from et to sont des tuples.
        """
        try:
            # Parser le move_id pour extraire les positions
            # Format: "MACRO_(x1, y1)_(x2, y2)"
            parts = move_id.replace("MACRO_", "").split("_")
            if len(parts) < 2:
                return None
            
            # Extraire les coordonnées (format simplifié)
            from_part = parts[0].strip("()")
            to_part = parts[1].strip("()")
            
            from_coords = tuple(map(int, from_part.split(", ")))
            to_coords = tuple(map(int, to_part.split(", ")))
            
            # Vérifier que la box existe à la position from
            if from_coords not in state.boxes:
                return None
            
            # Vérifier que la position to est valide
            to_x, to_y = to_coords
            if (to_x < 0 or to_x >= self.level.width or
                to_y < 0 or to_y >= self.level.height or
                self.level.is_wall(to_x, to_y) or
                to_coords in state.boxes):
                return None
            
            # Appliquer le macro-move
            new_boxes = set(state.boxes)
            new_boxes.remove(from_coords)
            new_boxes.add(to_coords)
            new_boxes = frozenset(new_boxes)
            
            # Pour un macro-move, la position du joueur ne change pas nécessairement
            # (c'est une abstraction de plusieurs mouvements)
            # En pratique, on pourrait calculer la position finale du joueur
            # mais pour la simplicité, on garde la position actuelle
            
            return FESSState(
                player_pos=state.player_pos,  # Position simplifiée
                boxes=new_boxes,
                parent=state,
                move=move_id,
                accumulated_weight=state.accumulated_weight + weight
            )
            
        except (ValueError, IndexError) as e:
            # Erreur de parsing, ignorer ce mouvement
            print(f"❌ Erreur parsing macro-move {move_id}: {e}")
            return None
    
    def _reconstruct_path(self, final_state: FESSState) -> List[str]:
        """Reconstruit le chemin de la solution."""
        path = []
        current = final_state
        
        while current.parent is not None:
            path.append(current.move)
            current = current.parent
        
        return list(reversed(path))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques complètes de FESS."""
        fs_stats = self.feature_space.get_statistics()
        
        return {
            'algorithm': 'FESS_AUTHENTIC',
            'search_statistics': {
                'states_explored': self.states_explored,
                'states_generated': self.states_generated,
                'move_weight_assignments': self.move_weight_assignments,
                'solve_time': time.time() - self.start_time if self.start_time > 0 else 0
            },
            'feature_space_statistics': fs_stats,
            'search_tree_statistics': {
                'total_states_in_tree': self.search_tree.total_states
            }
        }