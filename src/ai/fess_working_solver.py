"""
Version fonctionnelle de l'algorithme FESS avec vraie recherche.
Utilise une approche breadth-first avec heuristique pour trouver une solution.
"""

from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass
import time
from collections import deque
import heapq

@dataclass
class Move:
    """Un move simple : pousser une boîte d'une position à l'adjacente."""
    box_from: Tuple[int, int]
    box_to: Tuple[int, int]
    player_from: Tuple[int, int]
    player_to: Tuple[int, int]
    
    def __str__(self):
        return f"Push {self.box_from}→{self.box_to}"

@dataclass
class State:
    """État du jeu."""
    boxes: Set[Tuple[int, int]]
    player: Tuple[int, int]
    
    def __hash__(self):
        return hash((tuple(sorted(self.boxes)), self.player))
    
    def __eq__(self, other):
        return isinstance(other, State) and hash(self) == hash(other)

class SokobanSolver:
    """Solveur Sokoban avec vraie recherche."""
    
    def __init__(self, level):
        self.width = level.width
        self.height = level.height
        self.walls = set()
        self.targets = set(level.targets)
        self.initial_boxes = set(level.boxes)
        self.initial_player = level.player_pos
        
        # Extract walls
        for y in range(level.height):
            for x in range(level.width):
                if level.is_wall(x, y):
                    self.walls.add((x, y))
    
    def is_valid(self, pos):
        """Position valide ?"""
        x, y = pos
        return (0 <= x < self.width and 0 <= y < self.height and 
                pos not in self.walls)
    
    def get_reachable(self, player_pos, boxes):
        """Positions accessibles au joueur."""
        reachable = set()
        queue = deque([player_pos])
        visited = {player_pos}
        
        while queue:
            pos = queue.popleft()
            reachable.add(pos)
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (pos[0] + dx, pos[1] + dy)
                if (new_pos not in visited and 
                    self.is_valid(new_pos) and 
                    new_pos not in boxes):
                    visited.add(new_pos)
                    queue.append(new_pos)
        
        return reachable
    
    def get_possible_moves(self, state):
        """Tous les moves possibles depuis cet état."""
        moves = []
        reachable = self.get_reachable(state.player, state.boxes)
        
        for box in state.boxes:
            # Pour chaque direction
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                # Position où aller pour pousser
                push_from = (box[0] - dx, box[1] - dy)
                # Destination de la boîte
                box_to = (box[0] + dx, box[1] + dy)
                
                # Le joueur peut-il atteindre la position de poussée ?
                if push_from not in reachable:
                    continue
                
                # La destination est-elle valide ?
                if not self.is_valid(box_to) or box_to in state.boxes:
                    continue
                
                # Créer le move
                move = Move(box, box_to, state.player, box)
                moves.append(move)
        
        return moves
    
    def apply_move(self, state, move):
        """Applique un move."""
        new_boxes = state.boxes.copy()
        new_boxes.remove(move.box_from)
        new_boxes.add(move.box_to)
        
        # Le joueur finit où était la boîte
        new_player = move.box_from
        
        return State(new_boxes, new_player)
    
    def is_solved(self, state):
        """État résolu ?"""
        return state.boxes == self.targets
    
    def heuristic(self, state):
        """Heuristique : distance des boîtes aux cibles."""
        total_distance = 0
        
        # Distance minimum de chaque boîte à une cible
        for box in state.boxes:
            if box not in self.targets:
                min_dist = min(abs(box[0] - target[0]) + abs(box[1] - target[1]) 
                             for target in self.targets)
                total_distance += min_dist
        
        # Bonus : boîtes déjà sur cibles
        boxes_on_targets = len(state.boxes & self.targets)
        total_distance -= boxes_on_targets * 10
        
        return total_distance
    
    def is_deadlock(self, state):
        """Détection de deadlocks basique."""
        for box in state.boxes:
            if box not in self.targets:
                x, y = box
                # Boîte coincée dans un coin
                walls_around = 0
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    if (x + dx, y + dy) in self.walls:
                        walls_around += 1
                
                if walls_around >= 2:
                    return True
        return False
    
    def solve_bfs(self, max_time=60):
        """Résolution par BFS avec heuristique."""
        start_time = time.time()
        
        initial_state = State(self.initial_boxes, self.initial_player)
        
        # Queue prioritaire : (priorité, état, chemin)
        queue = [(self.heuristic(initial_state), initial_state, [])]
        visited = set()
        nodes_expanded = 0
        
        print(f"🔍 Démarrage BFS avec heuristique...")
        print(f"   État initial: {len(self.initial_boxes)} boîtes")
        print(f"   Heuristique initiale: {self.heuristic(initial_state)}")
        
        while queue and time.time() - start_time < max_time:
            priority, current_state, path = heapq.heappop(queue)
            
            # Déjà visité ?
            if current_state in visited:
                continue
            visited.add(current_state)
            
            nodes_expanded += 1
            
            # Solution trouvée ?
            if self.is_solved(current_state):
                elapsed = time.time() - start_time
                print(f"✅ Solution trouvée!")
                print(f"   Moves: {len(path)}")
                print(f"   Nœuds expansés: {nodes_expanded}")
                print(f"   Temps: {elapsed:.2f}s")
                return True, path, nodes_expanded, elapsed
            
            # Deadlock ?
            if self.is_deadlock(current_state):
                continue
            
            # Générer les moves successeurs
            moves = self.get_possible_moves(current_state)
            
            for move in moves:
                new_state = self.apply_move(current_state, move)
                
                if new_state not in visited:
                    new_path = path + [move]
                    new_priority = len(new_path) + self.heuristic(new_state)
                    heapq.heappush(queue, (new_priority, new_state, new_path))
            
            # Progress
            if nodes_expanded % 100 == 0:
                boxes_on_targets = len(current_state.boxes & self.targets)
                print(f"   Nœuds: {nodes_expanded}, Boîtes sur cibles: {boxes_on_targets}/6")
        
        elapsed = time.time() - start_time
        print(f"❌ Pas de solution trouvée")
        print(f"   Nœuds expansés: {nodes_expanded}")
        print(f"   Temps: {elapsed:.2f}s")
        return False, [], nodes_expanded, elapsed
    
    def solve_limited_depth(self, max_depth=50, max_time=30):
        """Résolution par DFS avec profondeur limitée."""
        start_time = time.time()
        
        initial_state = State(self.initial_boxes, self.initial_player)
        
        def dfs(state, path, depth):
            nonlocal start_time
            
            if time.time() - start_time > max_time:
                return False, []
            
            if depth > max_depth:
                return False, []
            
            if self.is_solved(state):
                return True, path
            
            if self.is_deadlock(state):
                return False, []
            
            # Trier les moves par heuristique
            moves = self.get_possible_moves(state)
            moves.sort(key=lambda m: self.heuristic(self.apply_move(state, m)))
            
            for move in moves:
                new_state = self.apply_move(state, move)
                
                success, solution = dfs(new_state, path + [move], depth + 1)
                if success:
                    return True, solution
            
            return False, []
        
        print(f"🔍 Démarrage DFS profondeur limitée (max: {max_depth})...")
        success, solution = dfs(initial_state, [], 0)
        
        elapsed = time.time() - start_time
        if success:
            print(f"✅ Solution trouvée!")
            print(f"   Moves: {len(solution)}")
            print(f"   Temps: {elapsed:.2f}s")
        else:
            print(f"❌ Pas de solution trouvée")
            print(f"   Temps: {elapsed:.2f}s")
        
        return success, solution, 0, elapsed

def test_working_solver():
    """Test du solveur fonctionnel."""
    print("🎮 Test Solveur Sokoban Fonctionnel - Niveau Original 1")
    print("=" * 70)
    
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    from src.level_management.level_collection_parser import LevelCollectionParser
    
    # Charger le niveau
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ Fichier non trouvé: {original_path}")
        return False
    
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    print(f"📋 Niveau: {level_title}")
    print(f"   Taille: {level.width}x{level.height}")
    print(f"   Boîtes: {len(level.boxes)}")
    print(f"   Cibles: {len(level.targets)}")
    
    # Créer le solveur
    solver = SokobanSolver(level)
    
    # Test BFS
    print(f"\n🧪 Test 1: BFS avec heuristique (30s)")
    success1, solution1, nodes1, time1 = solver.solve_bfs(max_time=30)
    
    # Test DFS si BFS a échoué
    if not success1:
        print(f"\n🧪 Test 2: DFS profondeur limitée (30s)")
        success2, solution2, nodes2, time2 = solver.solve_limited_depth(max_depth=30, max_time=30)
    else:
        success2, solution2 = False, []
    
    # Résultats
    if success1 or success2:
        solution = solution1 if success1 else solution2
        print(f"\n🎉 SOLUTION TROUVÉE!")
        print(f"📝 Solution ({len(solution)} moves):")
        
        # Convertir en notation FESS
        from src.ai.fess_notation import FESSLevelAnalyzer
        analyzer = FESSLevelAnalyzer(level)
        notation_system = analyzer.notation
        
        for i, move in enumerate(solution[:10]):  # Afficher les 10 premiers
            start_notation = notation_system.coordinate_to_notation(move.box_from[0], move.box_from[1])
            end_notation = notation_system.coordinate_to_notation(move.box_to[0], move.box_to[1])
            print(f"   {i+1}. {start_notation} → {end_notation}")
        
        if len(solution) > 10:
            print(f"   ... ({len(solution) - 10} moves supplémentaires)")
        
        print(f"\n📊 Performance:")
        print(f"   • Nombre de moves: {len(solution)}")
        print(f"   • Algorithme: {'BFS' if success1 else 'DFS'}")
        print(f"   • Temps: {time1 if success1 else time2:.2f}s")
        
        return True
    else:
        print(f"\n❌ Aucune solution trouvée avec les deux algorithmes")
        print(f"\n🔧 Suggestions:")
        print("• Augmenter max_time")
        print("• Augmenter max_depth pour DFS")
        print("• Améliorer l'heuristique")
        print("• Optimiser la détection de deadlocks")
        
        return False

if __name__ == "__main__":
    test_working_solver()