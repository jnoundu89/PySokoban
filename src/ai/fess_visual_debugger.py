"""
FESS Visual Debugger

Ce module fournit une interface de debug visuel pour l'algorithme FESS,
permettant de suivre étape par étape la logique de résolution avec :
- Visualisation des 4 features FESS
- Affichage des macro moves
- Suivi de l'espace des caractéristiques
- Notation des coordonnées FESS
"""

import time
import copy
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

from .authentic_fess_algorithm import (
    FESSAlgorithm, SokobanState, FeatureVector, FESSNode, MacroMoveAction
)
from .fess_notation import FESSLevelAnalyzer, FESSSolutionNotation

@dataclass
class FESSDebugStep:
    """Représente une étape de debug FESS."""
    step_number: int
    action: str
    state: SokobanState
    features: FeatureVector
    current_cell: Optional[FeatureVector]
    macro_move: Optional[MacroMoveAction]
    accumulated_weight: float
    nodes_expanded: int
    feature_space_size: int
    advisor_recommendations: List[MacroMoveAction]
    
class FESSVisualDebugger:
    """
    Debugger visuel pour l'algorithme FESS.
    
    Fournit une interface pour suivre étape par étape l'exécution de FESS
    avec visualisation des features, macro moves, et logique de décision.
    """
    
    def __init__(self, level, max_time: float = 300.0):
        """
        Initialise le debugger visuel FESS.
        
        Args:
            level: Niveau Sokoban à débugger
            max_time: Temps maximum de résolution
        """
        self.level = level
        self.fess_algorithm = FESSAlgorithm(level, max_time)
        self.analyzer = FESSLevelAnalyzer(level)
        self.notation = self.analyzer.notation
        
        # Debug state
        self.debug_steps: List[FESSDebugStep] = []
        self.current_step = 0
        self.solution_found = False
        self.solution_steps: List[MacroMoveAction] = []
        
        # Visual settings
        self.show_coordinates = True
        self.show_features = True
        self.show_weights = True
        self.step_by_step = True
        
    def debug_solve(self, step_by_step: bool = True) -> Tuple[bool, List[MacroMoveAction], Dict]:
        """
        Résout le niveau avec debug visuel complet.
        
        Args:
            step_by_step: Si True, pause à chaque étape
            
        Returns:
            Tuple de (succès, moves, statistiques)
        """
        self.step_by_step = step_by_step
        self.debug_steps.clear()
        
        print("🔬 FESS Visual Debugger - Démarrage")
        print("=" * 60)
        
        # Affichage initial du niveau
        self._display_initial_state()
        
        # Wrap l'algorithme FESS pour capturer les étapes
        return self._debug_fess_algorithm()
    
    def _display_initial_state(self):
        """Affiche l'état initial du niveau avec analyse."""
        print(f"📋 Niveau Initial avec Système de Coordonnées FESS:")
        level_display = self.level.get_state_string(show_fess_coordinates=True)
        print(level_display)
        
        # Analyse des features initiales
        initial_state = SokobanState(self.level)
        initial_features = self.fess_algorithm.feature_calculator.calculate_features(initial_state)
        
        print(f"\n🧠 Analyse des Features FESS Initiales:")
        self._display_features(initial_features)
        
        # Positions clés avec coordonnées FESS
        print(f"\n📍 Positions Clés (Coordonnées FESS):")
        print(f"  • Joueur: {self._pos_to_fess(initial_state.player_pos)}")
        
        print(f"  • Boîtes:")
        for i, box_pos in enumerate(sorted(initial_state.boxes)):
            fess_coord = self._pos_to_fess(box_pos)
            print(f"    {i+1}. {fess_coord} {box_pos}")
        
        print(f"  • Cibles:")
        for i, target_pos in enumerate(sorted(initial_state.targets)):
            fess_coord = self._pos_to_fess(target_pos)
            print(f"    {i+1}. {fess_coord} {target_pos}")
        
        if self.step_by_step:
            input("\n⏸️  Appuyez sur Entrée pour continuer...")
    
    def _debug_fess_algorithm(self) -> Tuple[bool, List[MacroMoveAction], Dict]:
        """Version debug de l'algorithme FESS."""
        start_time = time.time()
        
        # Phase d'initialisation (selon Figure 2)
        print(f"\n🚀 Phase d'Initialisation FESS (Figure 2)")
        print("-" * 40)
        
        # Set feature space to empty (FS)
        self.fess_algorithm.feature_space = {}
        print("✅ Feature space initialisé (vide)")
        
        # Set the start state as the root of the search tree (DS)
        root_state = self.fess_algorithm.initial_state
        print("✅ État initial défini comme racine de l'arbre de recherche")
        
        # Add feature values to the root state (DS)
        initial_features = self.fess_algorithm.feature_calculator.calculate_features(root_state)
        print("✅ Valeurs des features ajoutées à l'état racine")
        
        # Assign a weight of zero to the root state (DS)
        root_node = self.fess_algorithm._create_root_node(root_state, initial_features)
        print("✅ Poids de zéro assigné à l'état racine")
        
        # Project root state onto a cell in feature space (FS)
        self.fess_algorithm._project_to_feature_space(root_node)
        print("✅ État racine projeté dans l'espace des features")
        
        # Assign weights to all moves from the root state (DS+FS)
        self.fess_algorithm._assign_weights_to_moves(root_node)
        print("✅ Poids assignés à tous les mouvements depuis l'état racine")
        
        # Recommandations des conseillers initiaux
        advisor_moves = self.fess_algorithm.advisor.get_advisor_moves(root_state, initial_features)
        print(f"\n🤖 Recommandations Initiales des Conseillers ({len(advisor_moves)} moves):")
        for i, move in enumerate(advisor_moves):
            start_fess = self._pos_to_fess(move.box_start)
            end_fess = self._pos_to_fess(move.box_end)
            print(f"  {i+1}. {start_fess} → {end_fess} (poids: {move.weight})")
        
        self._add_debug_step(
            "INITIALIZE",
            root_state,
            initial_features,
            None,
            None,
            0.0,
            0,
            1,
            advisor_moves
        )
        
        if self.step_by_step:
            input("\n⏸️  Appuyez sur Entrée pour commencer la recherche...")
        
        # Phase de recherche (selon Figure 2)
        print(f"\n🔍 Phase de Recherche FESS (Figure 2)")
        print("-" * 40)
        
        iteration = 0
        max_iterations = 100  # Limite pour le debug
        
        while (time.time() - start_time < self.fess_algorithm.max_time and 
               iteration < max_iterations):
            iteration += 1
            
            print(f"\n🔄 Itération {iteration}")
            print("─" * 30)
            
            # Check if solution found
            solution_node = self.fess_algorithm._check_for_solution()
            if solution_node:
                print("🎉 SOLUTION TROUVÉE!")
                return self._extract_debug_solution(solution_node)
            
            # Pick the next cell in feature space (FS)
            current_cell = self.fess_algorithm._pick_next_feature_cell()
            if current_cell is None:
                print("❌ Aucune cellule à explorer dans l'espace des features")
                break
            
            print(f"📍 Cellule sélectionnée: {self._features_to_string(current_cell)}")
            
            # Find all search-tree states that project onto this cell (DS)
            states_in_cell = self.fess_algorithm.feature_space[current_cell]
            print(f"🔍 États dans cette cellule: {len(states_in_cell)}")
            
            # Show current feature space
            self._display_feature_space_status()
            
            # Simulate one step of the algorithm
            step_result = self._simulate_fess_step(current_cell, iteration)
            
            if not step_result:
                print("⚠️  Aucun mouvement possible dans cette cellule")
                continue
            
            if self.step_by_step:
                input("\n⏸️  Appuyez sur Entrée pour continuer...")
        
        print("⏰ Temps écoulé ou limite d'itérations atteinte")
        return False, [], self._get_debug_statistics()
    
    def _simulate_fess_step(self, current_cell: FeatureVector, iteration: int) -> bool:
        """Simule une étape de l'algorithme FESS avec affichage debug."""
        
        # Get states in current cell
        states_in_cell = self.fess_algorithm.feature_space[current_cell]
        
        # Find unexpanded moves
        all_unexpanded = []
        for node in states_in_cell:
            state_hash = self.fess_algorithm._state_to_hash(node.state)
            if state_hash in self.fess_algorithm.unexpanded_moves:
                for move in self.fess_algorithm.unexpanded_moves[state_hash]:
                    all_unexpanded.append((node, move))
        
        if not all_unexpanded:
            return False
        
        # Choose move with least accumulated weight
        best_node, best_move = min(all_unexpanded, 
                                 key=lambda x: x[0].accumulated_weight + x[1].weight)
        
        print(f"🎯 Mouvement sélectionné:")
        start_fess = self._pos_to_fess(best_move.box_start)
        end_fess = self._pos_to_fess(best_move.box_end)
        print(f"  • Macro move: {start_fess} → {end_fess}")
        print(f"  • Poids accumulé: {best_node.accumulated_weight:.1f}")
        print(f"  • Poids du mouvement: {best_move.weight:.1f}")
        print(f"  • Poids total: {best_node.accumulated_weight + best_move.weight:.1f}")
        
        # Apply move
        new_state = self.fess_algorithm._apply_move(best_node.state, best_move)
        if new_state is None:
            print("❌ Mouvement invalide")
            return False
        
        # Calculate new features
        new_features = self.fess_algorithm.feature_calculator.calculate_features(new_state)
        new_weight = best_node.accumulated_weight + best_move.weight
        
        print(f"\n📊 Nouvelles Features après le mouvement:")
        self._display_features(new_features)
        
        # Show feature progression
        old_features = best_node.feature_vector
        self._display_feature_progression(old_features, new_features)
        
        # Add debug step
        advisor_moves = self.fess_algorithm.advisor.get_advisor_moves(new_state, new_features)
        
        self._add_debug_step(
            f"MOVE_{iteration}",
            new_state,
            new_features,
            current_cell,
            best_move,
            new_weight,
            self.fess_algorithm.nodes_expanded + 1,
            len(self.fess_algorithm.feature_space),
            advisor_moves
        )
        
        # Update algorithm state (simplified for debug)
        self.fess_algorithm.nodes_expanded += 1
        
        return True
    
    def _display_features(self, features: FeatureVector):
        """Affiche les features FESS de manière lisible."""
        print(f"  🎯 Packing: {features.packing} (boîtes correctement emballées)")
        print(f"  🔗 Connectivity: {features.connectivity} (régions déconnectées)")
        print(f"  🚪 Room Connectivity: {features.room_connectivity} (passages obstrués)")
        print(f"  ⚠️  Out-of-Plan: {features.out_of_plan} (boîtes problématiques)")
    
    def _display_feature_progression(self, old_features: FeatureVector, new_features: FeatureVector):
        """Affiche la progression des features."""
        print(f"\n📈 Progression des Features:")
        
        changes = []
        if new_features.packing != old_features.packing:
            diff = new_features.packing - old_features.packing
            symbol = "📈" if diff > 0 else "📉"
            changes.append(f"{symbol} Packing: {old_features.packing} → {new_features.packing} ({diff:+d})")
        
        if new_features.connectivity != old_features.connectivity:
            diff = new_features.connectivity - old_features.connectivity
            symbol = "📉" if diff < 0 else "📈"  # Moins de régions = mieux
            changes.append(f"{symbol} Connectivity: {old_features.connectivity} → {new_features.connectivity} ({diff:+d})")
        
        if new_features.room_connectivity != old_features.room_connectivity:
            diff = new_features.room_connectivity - old_features.room_connectivity
            symbol = "📉" if diff < 0 else "📈"  # Moins d'obstructions = mieux
            changes.append(f"{symbol} Room Connectivity: {old_features.room_connectivity} → {new_features.room_connectivity} ({diff:+d})")
        
        if new_features.out_of_plan != old_features.out_of_plan:
            diff = new_features.out_of_plan - old_features.out_of_plan
            symbol = "📉" if diff < 0 else "📈"  # Moins de problèmes = mieux
            changes.append(f"{symbol} Out-of-Plan: {old_features.out_of_plan} → {new_features.out_of_plan} ({diff:+d})")
        
        if changes:
            for change in changes:
                print(f"  {change}")
        else:
            print("  🔄 Aucun changement de features")
    
    def _display_feature_space_status(self):
        """Affiche le statut de l'espace des features."""
        print(f"\n🗺️  Espace des Features:")
        print(f"  • Cellules totales: {len(self.fess_algorithm.feature_space)}")
        print(f"  • États totaux: {sum(len(nodes) for nodes in self.fess_algorithm.feature_space.values())}")
        
        # Top 3 cellules avec le plus d'états
        sorted_cells = sorted(
            self.fess_algorithm.feature_space.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        print(f"  • Top cellules:")
        for i, (features, nodes) in enumerate(sorted_cells[:3]):
            features_str = self._features_to_string(features)
            print(f"    {i+1}. {features_str}: {len(nodes)} états")
    
    def _features_to_string(self, features: FeatureVector) -> str:
        """Convertit des features en string lisible."""
        return f"({features.packing},{features.connectivity},{features.room_connectivity},{features.out_of_plan})"
    
    def _pos_to_fess(self, pos: Tuple[int, int]) -> str:
        """Convertit une position en notation FESS."""
        return self.notation.coordinate_to_notation(pos[0], pos[1])
    
    def _add_debug_step(self, action: str, state: SokobanState, features: FeatureVector,
                       current_cell: Optional[FeatureVector], macro_move: Optional[MacroMoveAction],
                       weight: float, nodes_expanded: int, fs_size: int,
                       advisor_moves: List[MacroMoveAction]):
        """Ajoute une étape de debug."""
        step = FESSDebugStep(
            step_number=len(self.debug_steps) + 1,
            action=action,
            state=copy.deepcopy(state),
            features=features,
            current_cell=current_cell,
            macro_move=macro_move,
            accumulated_weight=weight,
            nodes_expanded=nodes_expanded,
            feature_space_size=fs_size,
            advisor_recommendations=advisor_moves
        )
        self.debug_steps.append(step)
    
    def _extract_debug_solution(self, goal_node) -> Tuple[bool, List[MacroMoveAction], Dict]:
        """Extrait la solution avec informations de debug."""
        solution_moves = []
        current = goal_node
        
        while current.parent is not None:
            solution_moves.append(current.action)
            current = current.parent
        
        solution_moves.reverse()
        
        print(f"\n🎉 SOLUTION TROUVÉE!")
        print(f"📊 Statistiques:")
        print(f"  • Macro moves: {len(solution_moves)}")
        print(f"  • Nœuds explorés: {self.fess_algorithm.nodes_expanded}")
        print(f"  • Taille espace features: {len(self.fess_algorithm.feature_space)}")
        
        print(f"\n📝 Solution en Notation FESS:")
        for i, move in enumerate(solution_moves):
            start_fess = self._pos_to_fess(move.box_start)
            end_fess = self._pos_to_fess(move.box_end)
            print(f"  {i+1}. ({start_fess}) → ({end_fess})")
        
        return True, solution_moves, self._get_debug_statistics()
    
    def _get_debug_statistics(self) -> Dict:
        """Retourne les statistiques de debug."""
        return {
            'debug_steps': len(self.debug_steps),
            'nodes_expanded': self.fess_algorithm.nodes_expanded,
            'feature_space_size': len(self.fess_algorithm.feature_space),
            'max_features': self._get_max_features()
        }
    
    def _get_max_features(self) -> Dict:
        """Calcule les valeurs maximales atteintes pour chaque feature."""
        if not self.debug_steps:
            return {}
        
        max_features = {
            'packing': max(step.features.packing for step in self.debug_steps),
            'connectivity': max(step.features.connectivity for step in self.debug_steps),
            'room_connectivity': max(step.features.room_connectivity for step in self.debug_steps),
            'out_of_plan': max(step.features.out_of_plan for step in self.debug_steps)
        }
        return max_features

# Extension de l'algorithme FESS pour le debug
class FESSNode:
    """Extension de FESSNode pour le debug."""
    pass

# Méthodes d'extension pour FESSAlgorithm
def _create_root_node(self, state: SokobanState, features: FeatureVector):
    """Crée le nœud racine avec debug."""
    from .authentic_fess_algorithm import FESSNode
    root_node = FESSNode(
        state=state,
        feature_vector=features,
        accumulated_weight=0.0,
        depth=0
    )
    
    state_hash = self._state_to_hash(state)
    self.search_tree[state_hash] = root_node
    
    return root_node

def _project_to_feature_space(self, node):
    """Projette un nœud dans l'espace des features avec debug."""
    if node.feature_vector not in self.feature_space:
        self.feature_space[node.feature_vector] = []
    self.feature_space[node.feature_vector].append(node)

# Ajouter les méthodes à FESSAlgorithm
FESSAlgorithm._create_root_node = _create_root_node
FESSAlgorithm._project_to_feature_space = _project_to_feature_space

def demo_visual_debugger():
    """Démonstration du debugger visuel FESS."""
    print("🔬 FESS Visual Debugger Demo")
    print("=" * 50)
    print("Ce debugger permet de suivre étape par étape l'algorithme FESS")
    print("avec visualisation des features et notation des coordonnées.")

if __name__ == "__main__":
    demo_visual_debugger()