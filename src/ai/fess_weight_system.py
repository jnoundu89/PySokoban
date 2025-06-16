"""
FESS Weight System
==================

Implémentation du système de poids optimisé selon les documents de recherche.

"Moves chosen by the advisors are assigned a weight of 0, and all other moves 
are assigned a weight of 1. Consequently, variations composed solely of advisor 
moves are explored before other move sequences."

"We made the following experiment to test this hypothesis. The weight of advisor 
moves was set to zero, and the weight of difficult moves was set to one, so the 
weight simply counted the difficult moves. We expected the results to be identical 
to the results with the 1:100 ratio. The results were, however, even better!"

Référence: "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
"""

from typing import Dict, List, Optional, Set, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging

from src.core.sokoban_state import SokobanState
from src.ai.fess_notation import MacroMove


class MoveType(Enum):
    """Types de moves dans le système FESS."""
    ADVISOR = "advisor"      # Move recommandé par un advisor (poids 0)
    DIFFICULT = "difficult"  # Move non-advisor (poids 1)


@dataclass
class WeightedMove:
    """Représente un move avec son poids et sa source."""
    macro_move: MacroMove
    weight: int
    move_type: MoveType
    advisor_source: Optional[str] = None  # Nom de l'advisor qui a recommandé le move
    reasoning: Optional[str] = None       # Explication du poids assigné
    
    def __str__(self) -> str:
        source_info = f" (by {self.advisor_source})" if self.advisor_source else ""
        return f"{self.macro_move}{source_info} [weight={self.weight}]"


class FESSWeightSystem:
    """
    Système de poids FESS optimisé selon les documents de recherche.
    
    Assignation des poids :
    - Advisor moves : poids = 0 (exploration prioritaire)
    - Difficult moves : poids = 1 (exploration secondaire)
    
    Cette stratégie permet de :
    1. Explorer d'abord les variations composées uniquement d'advisor moves
    2. Éviter l'explosion combinatoire en priorisant les moves prometteurs
    3. Maintenir la complétude en explorant toujours tous les moves
    """
    
    # Poids selon le document de recherche
    ADVISOR_WEIGHT = 0      # "weight of advisor moves was set to zero"
    DIFFICULT_WEIGHT = 1    # "weight of difficult moves was set to one"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Statistiques pour le debug
        self.stats = {
            'advisor_moves': 0,
            'difficult_moves': 0,
            'total_moves_weighted': 0
        }
    
    def assign_weights_to_moves(self, 
                               state: SokobanState,
                               macro_moves: List[MacroMove],
                               advisor_recommendations: Dict[str, Optional[MacroMove]]) -> List[WeightedMove]:
        """
        Assigne les poids aux macro moves selon les recommandations des advisors.
        
        Args:
            state: État Sokoban actuel
            macro_moves: Liste des macro moves possibles
            advisor_recommendations: Dict {advisor_name: recommended_move}
            
        Returns:
            Liste des moves avec leurs poids assignés
        """
        weighted_moves = []
        advisor_moves_set = set()
        
        # Collecte tous les moves recommandés par les advisors
        for advisor_name, recommended_move in advisor_recommendations.items():
            if recommended_move is not None:
                advisor_moves_set.add(recommended_move)
        
        # Assigne les poids
        for macro_move in macro_moves:
            if macro_move in advisor_moves_set:
                # Move recommandé par un advisor : poids 0
                advisor_source = self._find_recommending_advisor(macro_move, advisor_recommendations)
                weighted_move = WeightedMove(
                    macro_move=macro_move,
                    weight=self.ADVISOR_WEIGHT,
                    move_type=MoveType.ADVISOR,
                    advisor_source=advisor_source,
                    reasoning=f"Recommended by {advisor_source} advisor"
                )
                self.stats['advisor_moves'] += 1
            else:
                # Move difficile : poids 1
                weighted_move = WeightedMove(
                    macro_move=macro_move,
                    weight=self.DIFFICULT_WEIGHT,
                    move_type=MoveType.DIFFICULT,
                    reasoning="Non-advisor move (difficult)"
                )
                self.stats['difficult_moves'] += 1
            
            weighted_moves.append(weighted_move)
        
        self.stats['total_moves_weighted'] += len(weighted_moves)
        
        # Trie par poids (advisor moves en premier)
        weighted_moves.sort(key=lambda wm: (wm.weight, str(wm.macro_move)))
        
        self.logger.debug(f"Weighted {len(macro_moves)} moves: "
                         f"{len(advisor_moves_set)} advisor (weight 0), "
                         f"{len(macro_moves) - len(advisor_moves_set)} difficult (weight 1)")
        
        return weighted_moves
    
    def _find_recommending_advisor(self, 
                                  macro_move: MacroMove,
                                  advisor_recommendations: Dict[str, Optional[MacroMove]]) -> str:
        """Trouve quel advisor a recommandé un move donné."""
        for advisor_name, recommended_move in advisor_recommendations.items():
            if recommended_move == macro_move:
                return advisor_name
        return "unknown"
    
    def calculate_accumulated_weight(self, path_moves: List[WeightedMove]) -> int:
        """
        Calcule le poids accumulé d'un chemin de moves.
        
        "Added state's weight = parent's weight + move weight"
        
        Args:
            path_moves: Séquence de moves dans le chemin
            
        Returns:
            Poids total accumulé
        """
        return sum(move.weight for move in path_moves)
    
    def get_minimum_weight_move(self, weighted_moves: List[WeightedMove]) -> Optional[WeightedMove]:
        """
        Sélectionne le move avec le poids minimum.
        
        "Choose move with least accumulated weight"
        
        Args:
            weighted_moves: Liste des moves pondérés
            
        Returns:
            Move avec le poids minimum ou None si liste vide
        """
        if not weighted_moves:
            return None
        
        # Les moves sont déjà triés par poids, prend le premier
        return weighted_moves[0]
    
    def filter_moves_by_weight_threshold(self, 
                                       weighted_moves: List[WeightedMove],
                                       max_weight: int) -> List[WeightedMove]:
        """
        Filtre les moves selon un seuil de poids maximum.
        
        Utilisé pour implémenter la stratégie progressive :
        1. D'abord, essaie solutions avec 0 difficult moves (poids < 1)
        2. Puis, essaie solutions avec 1 difficult move (poids < 2)
        3. Et ainsi de suite...
        
        Args:
            weighted_moves: Liste des moves pondérés
            max_weight: Poids maximum accepté
            
        Returns:
            Moves filtrés selon le seuil
        """
        return [wm for wm in weighted_moves if wm.weight <= max_weight]
    
    def analyze_move_distribution(self, weighted_moves: List[WeightedMove]) -> Dict[str, int]:
        """
        Analyse la distribution des types de moves.
        
        Returns:
            Statistiques sur la distribution des moves
        """
        distribution = {
            'advisor_moves': 0,
            'difficult_moves': 0,
            'total_moves': len(weighted_moves)
        }
        
        for weighted_move in weighted_moves:
            if weighted_move.move_type == MoveType.ADVISOR:
                distribution['advisor_moves'] += 1
            else:
                distribution['difficult_moves'] += 1
        
        return distribution
    
    def get_advisor_efficiency_ratio(self) -> float:
        """
        Calcule le ratio d'efficacité des advisors.
        
        Returns:
            Ratio advisor_moves / total_moves
        """
        if self.stats['total_moves_weighted'] == 0:
            return 0.0
        
        return self.stats['advisor_moves'] / self.stats['total_moves_weighted']
    
    def reset_stats(self):
        """Remet à zéro les statistiques."""
        self.stats = {
            'advisor_moves': 0,
            'difficult_moves': 0,
            'total_moves_weighted': 0
        }
    
    def log_weighting_stats(self, level_name: str = ""):
        """Affiche les statistiques de pondération."""
        ratio = self.get_advisor_efficiency_ratio()
        self.logger.info(f"Weight System Stats {level_name}: "
                        f"Advisor={self.stats['advisor_moves']}, "
                        f"Difficult={self.stats['difficult_moves']}, "
                        f"Efficiency={ratio:.2%}")


class FESSMoveSelector:
    """
    Sélecteur de moves intégrant le système de poids et l'ordering lexicographique.
    
    Implémente la stratégie de sélection complète :
    1. Sélection par poids minimum (advisor moves prioritaires)
    2. En cas d'égalité, utilise l'ordering lexicographique des features
    3. Gestion des tie-breakers selon les priorités du document
    """
    
    def __init__(self, weight_system: FESSWeightSystem):
        self.weight_system = weight_system
        self.logger = logging.getLogger(__name__)
    
    def select_best_move(self, 
                        weighted_moves: List[WeightedMove],
                        feature_comparator: Optional[callable] = None) -> Optional[WeightedMove]:
        """
        Sélectionne le meilleur move selon les critères FESS.
        
        "Choose the move with the least weight. In case of equality, prioritize by other features"
        
        Args:
            weighted_moves: Moves pondérés disponibles
            feature_comparator: Fonction de comparaison des features pour tie-breaking
            
        Returns:
            Meilleur move sélectionné
        """
        if not weighted_moves:
            return None
        
        # Trouve le poids minimum
        min_weight = min(wm.weight for wm in weighted_moves)
        min_weight_moves = [wm for wm in weighted_moves if wm.weight == min_weight]
        
        if len(min_weight_moves) == 1:
            return min_weight_moves[0]
        
        # Tie-breaking nécessaire
        if feature_comparator:
            best_move = min(min_weight_moves, key=lambda wm: feature_comparator(wm.macro_move))
            self.logger.debug(f"Tie-breaking applied: selected {best_move}")
            return best_move
        
        # Fallback : prend le premier (ordre déterministe)
        return min_weight_moves[0]
    
    def get_moves_by_weight_class(self, weighted_moves: List[WeightedMove]) -> Dict[int, List[WeightedMove]]:
        """
        Groupe les moves par classe de poids.
        
        Returns:
            Dict {weight: [moves_with_that_weight]}
        """
        weight_classes = {}
        for weighted_move in weighted_moves:
            weight = weighted_move.weight
            if weight not in weight_classes:
                weight_classes[weight] = []
            weight_classes[weight].append(weighted_move)
        
        return weight_classes
    
    def explain_selection(self, 
                         selected_move: WeightedMove,
                         all_moves: List[WeightedMove]) -> str:
        """
        Génère une explication de la sélection du move.
        
        Utile pour le debug et la compréhension de l'algorithme.
        """
        min_weight = min(wm.weight for wm in all_moves)
        min_weight_count = sum(1 for wm in all_moves if wm.weight == min_weight)
        
        explanation = f"Selected: {selected_move}\n"
        explanation += f"Reason: Weight {selected_move.weight} (minimum among {len(all_moves)} moves)\n"
        
        if min_weight_count > 1:
            explanation += f"Tie-breaking: {min_weight_count} moves had minimum weight\n"
        
        if selected_move.advisor_source:
            explanation += f"Advisor: {selected_move.advisor_source}\n"
        
        return explanation


def create_weight_system() -> FESSWeightSystem:
    """Factory function pour créer un système de poids FESS standard."""
    return FESSWeightSystem()


def create_move_selector(weight_system: Optional[FESSWeightSystem] = None) -> FESSMoveSelector:
    """Factory function pour créer un sélecteur de moves FESS."""
    if weight_system is None:
        weight_system = create_weight_system()
    return FESSMoveSelector(weight_system)