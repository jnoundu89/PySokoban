"""
Version simplifiée et fonctionnelle de l'algorithme FESS.
Focus sur la résolution effective du niveau Original 1.
"""

from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass
import time
from collections import deque

@dataclass
class SimpleMacroMove:
    """Macro move simplifié - série de poussées d'une même boîte."""
    box_start: Tuple[int, int]
    box_end: Tuple[int, int]
    pushes: int = 1
    weight: float = 1.0
    
    def __str__(self):
        return f"{self.box_start}→{self.box_end} ({self.pushes}p)"

@dataclass
class SimpleFeatures:
    """Features simplifiées."""
    boxes_on_targets: int = 0
    connectivity: int = 0
    
    def to_tuple(self):
        return (self.boxes_on_targets, self.connectivity)
    
    def __hash__(self):
        return hash(self.to_tuple())
    
    def __eq__(self, other):
        return isinstance(other, SimpleFeatures) and self.to_tuple() == other.to_tuple()

class SimpleState:
    """État Sokoban simplifié."""
    
    def __init__(self, level):
        self.width = level.width
        self.height = level.height
        self.walls = set()
        self.targets = set(level.targets)
        self.boxes = set(level.boxes)
        self.player_pos = level.player_pos
        
        # Extract walls
        for y in range(level.height):
            for x in range(level.width):
                if level.is_wall(x, y):
                    self.walls.add((x, y))
    
    def copy(self):
        new_state = SimpleState.__new__(SimpleState)
        new_state.width = self.width
        new_state.height = self.height
        new_state.walls = self.walls.copy()
        new_state.targets = self.targets.copy()
        new_state.boxes = self.boxes.copy()
        new_state.player_pos = self.player_pos
        return new_state
    
    def is_valid(self, pos):
        x, y = pos
        return (0 <= x < self.width and 0 <= y < self.height and 
                pos not in self.walls)
    
    def is_solved(self):
        return self.boxes == self.targets
    
    def get_reachable(self, start):
        """Positions accessibles au joueur."""
        reachable = set()
        queue = deque([start])
        visited = {start}
        
        while queue:
            pos = queue.popleft()
            reachable.add(pos)
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (pos[0] + dx, pos[1] + dy)
                if (new_pos not in visited and 
                    self.is_valid(new_pos) and 
                    new_pos not in self.boxes):
                    visited.add(new_pos)
                    queue.append(new_pos)
        
        return reachable
    
    def calculate_features(self):
        """Calcul des features simplifiées."""
        boxes_on_targets = len(self.boxes & self.targets)
        
        # Connectivity simple : nombre de régions libres
        free_positions = set()
        for x in range(self.width):
            for y in range(self.height):
                pos = (x, y)
                if self.is_valid(pos) and pos not in self.boxes:
                    free_positions.add(pos)
        
        # Compter les composantes connexes
        visited = set()
        connectivity = 0
        
        for pos in free_positions:
            if pos not in visited:
                connectivity += 1
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
        
        return SimpleFeatures(boxes_on_targets, connectivity)

class SimpleFESSGenerator:
    """Générateur de macro moves simplifié mais efficace."""
    
    def __init__(self, state: SimpleState):
        self.state = state
    
    def generate_moves(self) -> List[SimpleMacroMove]:
        """Génère tous les macro moves possibles."""
        moves = []
        reachable = self.state.get_reachable(self.state.player_pos)
        
        # Pour chaque boîte
        for box_pos in self.state.boxes:
            # Positions adjacentes où le joueur peut se placer pour pousser
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                push_from = (box_pos[0] - dx, box_pos[1] - dy)
                push_to = (box_pos[0] + dx, box_pos[1] + dy)
                
                # Le joueur peut-il atteindre la position de poussée ?
                if push_from not in reachable:
                    continue
                
                # La destination est-elle valide ?
                if not self.state.is_valid(push_to) or push_to in self.state.boxes:
                    continue
                
                # Move simple (1 poussée)
                move = SimpleMacroMove(box_pos, push_to, 1, 1.0)
                
                # Priorité aux moves vers les cibles
                if push_to in self.state.targets:
                    move.weight = 0.0  # Priorité maximale
                
                moves.append(move)
                
                # Essayer des séquences de 2-3 poussées dans la même direction
                for extra_pushes in range(1, 3):
                    extended_to = (push_to[0] + dx * extra_pushes, 
                                 push_to[1] + dy * extra_pushes)
                    
                    if (self.state.is_valid(extended_to) and 
                        extended_to not in self.state.boxes):
                        
                        extended_move = SimpleMacroMove(
                            box_pos, extended_to, 1 + extra_pushes, 1.0
                        )
                        
                        # Priorité aux moves vers les cibles
                        if extended_to in self.state.targets:
                            extended_move.weight = 0.0
                        
                        moves.append(extended_move)
        
        return moves

class SimpleFESS:
    """Version simplifiée de l'algorithme FESS qui fonctionne."""
    
    def __init__(self, level, max_time=60.0):
        self.initial_state = SimpleState(level)
        self.max_time = max_time
        self.start_time = 0
        self.nodes_expanded = 0
        
    def solve(self):
        """Résout le niveau avec l'algorithme FESS simplifié."""
        self.start_time = time.time()
        
        # État initial
        current_state = self.initial_state
        solution_moves = []
        visited_states = set()
        
        print(f"🎯 Démarrage résolution FESS simplifiée...")
        print(f"   État initial: {len(current_state.boxes)} boîtes")
        
        # Boucle principale
        iteration = 0
        while time.time() - self.start_time < self.max_time:
            iteration += 1
            
            # Vérifier si résolu
            if current_state.is_solved():
                print(f"✅ Solution trouvée en {iteration} itérations!")
                return True, solution_moves, self._get_stats()
            
            # État visité ?
            state_hash = self._hash_state(current_state)
            if state_hash in visited_states:
                print(f"❌ État déjà visité, recherche terminée")
                break
            visited_states.add(state_hash)
            
            # Générer les moves
            generator = SimpleFESSGenerator(current_state)
            moves = generator.generate_moves()
            
            if not moves:
                print(f"❌ Aucun move possible")
                break
            
            # Trier par poids (priorité aux moves vers cibles)
            moves.sort(key=lambda m: m.weight)
            
            # Essayer le meilleur move
            best_move = moves[0]
            new_state = self._apply_move(current_state, best_move)
            
            if new_state is None:
                print(f"❌ Move invalide: {best_move}")
                break
            
            # Éviter les deadlocks simples
            if self._is_simple_deadlock(new_state):
                # Essayer le move suivant
                if len(moves) > 1:
                    best_move = moves[1]
                    new_state = self._apply_move(current_state, best_move)
                    if new_state is None or self._is_simple_deadlock(new_state):
                        break
                else:
                    break
            
            # Appliquer le move
            current_state = new_state
            solution_moves.append(best_move)
            self.nodes_expanded += 1
            
            # Progress
            features = current_state.calculate_features()
            if iteration % 10 == 0:
                print(f"   Iteration {iteration}: {features.boxes_on_targets}/6 boîtes sur cibles")
            
            # Limite de sécurité
            if len(solution_moves) > 100:
                print(f"⚠️  Solution trop longue (>100 moves)")
                break
        
        print(f"❌ Pas de solution trouvée")
        return False, solution_moves, self._get_stats()
    
    def _apply_move(self, state, move):
        """Applique un macro move."""
        if move.box_start not in state.boxes:
            return None
        
        new_state = state.copy()
        new_state.boxes.remove(move.box_start)
        new_state.boxes.add(move.box_end)
        
        # Position joueur approximative
        new_state.player_pos = move.box_start
        
        return new_state
    
    def _is_simple_deadlock(self, state):
        """Détection de deadlocks simples."""
        for box in state.boxes:
            if box not in state.targets:
                x, y = box
                # Boîte dans un coin = deadlock
                walls_adjacent = 0
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    if (x + dx, y + dy) in state.walls:
                        walls_adjacent += 1
                
                if walls_adjacent >= 2:
                    return True
        return False
    
    def _hash_state(self, state):
        """Hash de l'état pour éviter les cycles."""
        return (tuple(sorted(state.boxes)), state.player_pos)
    
    def _get_stats(self):
        """Statistiques."""
        return {
            'nodes_expanded': self.nodes_expanded,
            'time_elapsed': time.time() - self.start_time
        }

def test_simple_fess():
    """Test de la version simplifiée."""
    print("🧪 Test FESS Simplifié - Original Level 1")
    print("=" * 50)
    
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    
    from src.level_management.level_collection_parser import LevelCollectionParser
    
    # Charger le niveau
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    print(f"📋 Niveau: {level_title}")
    
    # Créer et tester l'algorithme
    fess = SimpleFESS(level, max_time=30.0)
    success, moves, stats = fess.solve()
    
    print(f"\n📊 Résultats:")
    print(f"   Solution: {'✅ TROUVÉE' if success else '❌ NON TROUVÉE'}")
    print(f"   Moves: {len(moves)}")
    print(f"   Nœuds: {stats['nodes_expanded']}")
    print(f"   Temps: {stats['time_elapsed']:.2f}s")
    
    if success:
        print(f"\n📝 Solution:")
        for i, move in enumerate(moves):
            print(f"   {i+1}. {move}")
        
        total_pushes = sum(move.pushes for move in moves)
        print(f"\n   Total poussées: {total_pushes}")
    
    return success

if __name__ == "__main__":
    test_simple_fess()