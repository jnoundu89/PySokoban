"""
FESS Advisors System
====================

Implémentation des 7 advisors selon les documents de recherche.

"To address the problem of the large branching factor, we introduce the concept
of advisors. Advisors are domain-specific heuristics that aim to pick promising
moves. The advisors are implemented using the FESS weighting mechanism: moves
that are recommended by advisors are assigned a small weight, and all other
moves are assigned a large weight."

"Our solver uses seven advisors. Four of them are directly related to improving
features (packed-boxes, connectivity, room-connectivity, and out-of-plan),
suggesting ways to advance along a specific axis in the feature space."

Référence: "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
"""

from typing import Dict, List, Set, Tuple, Optional, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from collections import defaultdict

from src.core.level import Level
from src.core.sokoban_state import SokobanState
from src.ai.fess_notation import MacroMove
from src.ai.fess_enhanced_features import FESSEnhancedFeatures, FESSFeatureVector
from src.ai.fess_room_analysis import FESSRoomAnalyzer


class FESSAdvisor(ABC):
    """
    Classe abstraite pour tous les advisors FESS.
    
    Chaque advisor peut suggérer au maximum un move par position.
    """
    
    def __init__(self, name: str, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        self.name = name
        self.features = features
        self.room_analyzer = room_analyzer
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Statistiques
        self.stats = {
            'suggestions_made': 0,
            'suggestions_applied': 0,
            'moves_evaluated': 0
        }
    
    @abstractmethod
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """
        Suggère le meilleur move selon la stratégie de cet advisor.
        
        Args:
            state: État Sokoban actuel
            available_moves: Liste des macro moves possibles
            
        Returns:
            Move recommandé ou None si aucun move n'est approprié
        """
        pass
    
    def get_priority(self) -> int:
        """Retourne la priorité de cet advisor (plus bas = plus prioritaire)."""
        return 100  # Priorité par défaut
    
    def reset_stats(self):
        """Remet à zéro les statistiques."""
        self.stats = {
            'suggestions_made': 0,
            'suggestions_applied': 0,
            'moves_evaluated': 0
        }
    
    def log_stats(self):
        """Affiche les statistiques de cet advisor."""
        self.logger.info(f"{self.name} Stats: "
                        f"Suggested={self.stats['suggestions_made']}, "
                        f"Applied={self.stats['suggestions_applied']}, "
                        f"Evaluated={self.stats['moves_evaluated']}")


class PackingAdvisor(FESSAdvisor):
    """
    Packing Advisor - Maximise le nombre de boîtes packées.
    
    "This advisor considers only moves that increase the number of packed boxes,
    and rejects all other moves. If several packing moves are available, it
    chooses the best one."
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        super().__init__("Packing", features, room_analyzer)
    
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """Suggère un move qui augmente le nombre de boîtes packées."""
        current_features = self.features.compute_feature_vector(state)
        current_packing = current_features.packing
        
        packing_moves = []
        
        for move in available_moves:
            self.stats['moves_evaluated'] += 1
            
            # Simule le move
            try:
                new_state = move.apply_to_state(state)
                new_features = self.features.compute_feature_vector(new_state)
                
                # Vérifie si le move améliore le packing
                if new_features.packing > current_packing:
                    packing_moves.append((move, new_features.packing))
            
            except Exception as e:
                self.logger.debug(f"Move simulation failed: {move}, error: {e}")
                continue
        
        if not packing_moves:
            return None
        
        # Sélectionne le move avec le meilleur packing
        best_move = max(packing_moves, key=lambda x: x[1])[0]
        
        self.stats['suggestions_made'] += 1
        self.logger.debug(f"Suggested packing move: {best_move}")
        
        return best_move
    
    def get_priority(self) -> int:
        """Priorité élevée pour le packing."""
        return 20


class ConnectivityAdvisor(FESSAdvisor):
    """
    Connectivity Advisor - Améliore la connectivité.
    
    "Very similarly to the packing advisor, this advisor considers only moves
    that improve connectivity."
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        super().__init__("Connectivity", features, room_analyzer)
    
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """Suggère un move qui améliore la connectivité."""
        current_features = self.features.compute_feature_vector(state)
        current_connectivity = current_features.connectivity
        
        connectivity_moves = []
        
        for move in available_moves:
            self.stats['moves_evaluated'] += 1
            
            try:
                new_state = move.apply_to_state(state)
                new_features = self.features.compute_feature_vector(new_state)
                
                # Vérifie si le move améliore la connectivité (diminue le nombre de régions)
                if new_features.connectivity < current_connectivity:
                    connectivity_moves.append((move, new_features.connectivity))
            
            except Exception as e:
                self.logger.debug(f"Move simulation failed: {move}, error: {e}")
                continue
        
        if not connectivity_moves:
            return None
        
        # Sélectionne le move avec la meilleure connectivité
        best_move = min(connectivity_moves, key=lambda x: x[1])[0]
        
        self.stats['suggestions_made'] += 1
        self.logger.debug(f"Suggested connectivity move: {best_move}")
        
        return best_move
    
    def get_priority(self) -> int:
        """Priorité pour la connectivité."""
        return 30


class RoomConnectivityAdvisor(FESSAdvisor):
    """
    Room-Connectivity Advisor - Améliore la connectivité entre rooms.
    
    "This advisor considers only moves that improve room connectivity."
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        super().__init__("RoomConnectivity", features, room_analyzer)
    
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """Suggère un move qui améliore la connectivité entre rooms."""
        current_room_connectivity = self.room_analyzer.compute_room_connectivity_feature(state)
        
        room_connectivity_moves = []
        
        for move in available_moves:
            self.stats['moves_evaluated'] += 1
            
            try:
                new_state = move.apply_to_state(state)
                new_room_connectivity = self.room_analyzer.compute_room_connectivity_feature(new_state)
                
                # Vérifie si le move améliore la room connectivity (diminue les obstructions)
                if new_room_connectivity < current_room_connectivity:
                    room_connectivity_moves.append((move, new_room_connectivity))
            
            except Exception as e:
                self.logger.debug(f"Move simulation failed: {move}, error: {e}")
                continue
        
        if not room_connectivity_moves:
            return None
        
        # Sélectionne le move avec la meilleure room connectivity
        best_move = min(room_connectivity_moves, key=lambda x: x[1])[0]
        
        self.stats['suggestions_made'] += 1
        self.logger.debug(f"Suggested room connectivity move: {best_move}")
        
        return best_move
    
    def get_priority(self) -> int:
        """Priorité pour la room connectivity."""
        return 40


class HotspotsAdvisor(FESSAdvisor):
    """
    Hotspots Advisor - Réduit le nombre de hotspots.
    
    "This advisor considers only moves that reduce hotspots."
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        super().__init__("Hotspots", features, room_analyzer)
    
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """Suggère un move qui réduit le nombre de hotspots."""
        current_hotspots = self.room_analyzer.compute_hotspots_feature(state)
        
        hotspot_moves = []
        
        for move in available_moves:
            self.stats['moves_evaluated'] += 1
            
            try:
                new_state = move.apply_to_state(state)
                new_hotspots = self.room_analyzer.compute_hotspots_feature(new_state)
                
                # Vérifie si le move réduit les hotspots
                if new_hotspots < current_hotspots:
                    hotspot_moves.append((move, new_hotspots))
            
            except Exception as e:
                self.logger.debug(f"Move simulation failed: {move}, error: {e}")
                continue
        
        if not hotspot_moves:
            return None
        
        # Sélectionne le move qui réduit le plus les hotspots
        best_move = min(hotspot_moves, key=lambda x: x[1])[0]
        
        self.stats['suggestions_made'] += 1
        self.logger.debug(f"Suggested hotspot reduction move: {best_move}")
        
        return best_move
    
    def get_priority(self) -> int:
        """Priorité pour les hotspots."""
        return 50


class ExplorerAdvisor(FESSAdvisor):
    """
    Explorer Advisor - Ouvre l'accès à de nouvelles zones.
    
    "This advisor opens a path to a free square which enables a new push.
    Most of the time, this advisor agrees with the connectivity advisor.
    However, sometimes it finds other moves."
    
    "The explorer advisor was designed for forcefully breaking into closed rooms."
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        super().__init__("Explorer", features, room_analyzer)
    
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """Suggère un move qui ouvre l'accès à de nouvelles zones."""
        current_mobility = self.room_analyzer.compute_mobility_feature(state)
        
        explorer_moves = []
        
        for move in available_moves:
            self.stats['moves_evaluated'] += 1
            
            try:
                new_state = move.apply_to_state(state)
                new_mobility = self.room_analyzer.compute_mobility_feature(new_state)
                
                # Vérifie si le move améliore la mobilité (accès à de nouvelles zones)
                if new_mobility > current_mobility:
                    # Vérifie aussi que ça n'empire pas trop la connectivité
                    current_features = self.features.compute_feature_vector(state)
                    new_features = self.features.compute_feature_vector(new_state)
                    
                    connectivity_penalty = new_features.connectivity - current_features.connectivity
                    if connectivity_penalty <= 1:  # Accepte une légère dégradation
                        explorer_moves.append((move, new_mobility))
            
            except Exception as e:
                self.logger.debug(f"Move simulation failed: {move}, error: {e}")
                continue
        
        if not explorer_moves:
            return None
        
        # Sélectionne le move avec la meilleure mobilité
        best_move = max(explorer_moves, key=lambda x: x[1])[0]
        
        self.stats['suggestions_made'] += 1
        self.logger.debug(f"Suggested explorer move: {best_move}")
        
        return best_move
    
    def get_priority(self) -> int:
        """Priorité pour l'exploration."""
        return 60


class OpenerAdvisor(FESSAdvisor):
    """
    Opener Advisor - Libère les hotspots critiques.
    
    "This is probably the most interesting advisor. First, it finds the hotspot
    that blocks the largest number of boxes. Clearly, this box should be pushed
    away. It is, however, often blocked by other boxes. In such cases, the opener
    advisor tries to open up by pushing nearby boxes away from the hotspot.
    Only moves that do not worsen the connectivity are considered."
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        super().__init__("Opener", features, room_analyzer)
    
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """Suggère un move qui libère les hotspots critiques."""
        # Trouve le hotspot le plus disruptif
        most_disruptive_hotspot = self.room_analyzer.hotspot_analyzer.find_most_disruptive_hotspot(state)
        
        if most_disruptive_hotspot is None:
            return None
        
        current_features = self.features.compute_feature_vector(state)
        current_connectivity = current_features.connectivity
        
        opener_moves = []
        
        for move in available_moves:
            self.stats['moves_evaluated'] += 1
            
            try:
                new_state = move.apply_to_state(state)
                new_features = self.features.compute_feature_vector(new_state)
                
                # Vérifie que la connectivité ne s'empire pas
                if new_features.connectivity <= current_connectivity:
                    # Vérifie si le move aide à libérer le hotspot
                    if self._helps_free_hotspot(move, most_disruptive_hotspot, state):
                        opener_moves.append(move)
            
            except Exception as e:
                self.logger.debug(f"Move simulation failed: {move}, error: {e}")
                continue
        
        if not opener_moves:
            return None
        
        # Sélectionne le move qui libère le mieux le hotspot
        best_move = self._select_best_opener_move(opener_moves, most_disruptive_hotspot, state)
        
        self.stats['suggestions_made'] += 1
        self.logger.debug(f"Suggested opener move: {best_move} for hotspot at {most_disruptive_hotspot}")
        
        return best_move
    
    def _helps_free_hotspot(self, move: MacroMove, 
                           hotspot_pos: Tuple[int, int], 
                           state: SokobanState) -> bool:
        """Vérifie si un move aide à libérer un hotspot."""
        # Si le move déplace directement le hotspot
        if move.start_pos == hotspot_pos:
            return True
        
        # Si le move libère de l'espace autour du hotspot
        hx, hy = hotspot_pos
        hotspot_neighbors = {(hx+dx, hy+dy) for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]}
        
        # Vérifie si le move libère un voisin du hotspot
        if move.start_pos in hotspot_neighbors:
            return True
        
        return False
    
    def _select_best_opener_move(self, moves: List[MacroMove], 
                                hotspot_pos: Tuple[int, int], 
                                state: SokobanState) -> MacroMove:
        """Sélectionne le meilleur move pour libérer un hotspot."""
        # Priorité : moves qui déplacent directement le hotspot
        direct_moves = [m for m in moves if m.start_pos == hotspot_pos]
        if direct_moves:
            return direct_moves[0]
        
        # Sinon, moves qui libèrent de l'espace autour
        hx, hy = hotspot_pos
        for move in moves:
            mx, my = move.start_pos
            distance = abs(mx - hx) + abs(my - hy)
            if distance <= 2:  # Proximité raisonnable
                return move
        
        # Fallback
        return moves[0]
    
    def get_priority(self) -> int:
        """Priorité pour l'opener."""
        return 10  # Très haute priorité


class OOPAdvisor(FESSAdvisor):
    """
    Out-of-Plan (OOP) Advisor - Gère les boîtes qui interfèrent avec le packing plan.
    
    "OOP ('out of plan') boxes interfere with the packing plan. They can be dealt
    with by pushing them into a basin area."
    
    "The OOP advisor is very similar in design to the opener advisor. First, it
    finds the OOP box closest to the basin. If this box can be pushed into the
    basin, the advisor chooses this move. Otherwise, it tries to make room for
    the OOP box by pushing nearby boxes into the basin."
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        super().__init__("OOP", features, room_analyzer)
    
    def suggest_move(self, state: SokobanState, 
                    available_moves: List[MacroMove]) -> Optional[MacroMove]:
        """Suggère un move qui gère les boîtes Out-of-Plan."""
        current_features = self.features.compute_feature_vector(state)
        current_oop = current_features.out_of_plan
        
        if current_oop == 0:
            return None  # Pas de boîtes OOP
        
        current_connectivity = current_features.connectivity
        oop_moves = []
        
        for move in available_moves:
            self.stats['moves_evaluated'] += 1
            
            try:
                new_state = move.apply_to_state(state)
                new_features = self.features.compute_feature_vector(new_state)
                
                # Vérifie si le move réduit les boîtes OOP
                if new_features.out_of_plan < current_oop:
                    # Vérifie que la connectivité ne s'empire pas
                    if new_features.connectivity <= current_connectivity:
                        oop_reduction = current_oop - new_features.out_of_plan
                        oop_moves.append((move, oop_reduction))
            
            except Exception as e:
                self.logger.debug(f"Move simulation failed: {move}, error: {e}")
                continue
        
        if not oop_moves:
            return None
        
        # Sélectionne le move qui réduit le plus les boîtes OOP
        best_move = max(oop_moves, key=lambda x: x[1])[0]
        
        self.stats['suggestions_made'] += 1
        self.logger.debug(f"Suggested OOP move: {best_move}")
        
        return best_move
    
    def get_priority(self) -> int:
        """Priorité absolue pour OOP selon le document."""
        return 0  # Priorité absolue


class FESSAdvisorSystem:
    """
    Système complet des 7 advisors FESS.
    
    Coordonne tous les advisors et gère leurs recommandations selon
    la stratégie définie dans les documents de recherche.
    """
    
    def __init__(self, features: FESSEnhancedFeatures, room_analyzer: FESSRoomAnalyzer):
        self.features = features
        self.room_analyzer = room_analyzer
        self.logger = logging.getLogger(__name__)
        
        # Crée les 7 advisors
        self.advisors = [
            OOPAdvisor(features, room_analyzer),           # Priorité 0
            OpenerAdvisor(features, room_analyzer),        # Priorité 10
            PackingAdvisor(features, room_analyzer),       # Priorité 20
            ConnectivityAdvisor(features, room_analyzer),  # Priorité 30
            RoomConnectivityAdvisor(features, room_analyzer), # Priorité 40
            HotspotsAdvisor(features, room_analyzer),      # Priorité 50
            ExplorerAdvisor(features, room_analyzer)       # Priorité 60
        ]
        
        # Trie par priorité
        self.advisors.sort(key=lambda a: a.get_priority())
        
        # Statistiques globales
        self.total_consultations = 0
        self.total_recommendations = 0
    
    def consult_advisors(self, state: SokobanState, 
                        available_moves: List[MacroMove]) -> Dict[str, Optional[MacroMove]]:
        """
        Consulte tous les advisors pour obtenir leurs recommandations.
        
        "In our implementation, each advisor is allowed to suggest at most one move."
        
        Args:
            state: État Sokoban actuel
            available_moves: Liste des macro moves possibles
            
        Returns:
            Dict {advisor_name: recommended_move}
        """
        self.total_consultations += 1
        recommendations = {}
        
        for advisor in self.advisors:
            try:
                suggested_move = advisor.suggest_move(state, available_moves)
                recommendations[advisor.name] = suggested_move
                
                if suggested_move is not None:
                    self.total_recommendations += 1
                    self.logger.debug(f"{advisor.name} recommends: {suggested_move}")
                else:
                    self.logger.debug(f"{advisor.name} has no recommendation")
            
            except Exception as e:
                self.logger.error(f"Error in {advisor.name}: {e}")
                recommendations[advisor.name] = None
        
        return recommendations
    
    def get_advisor_statistics(self) -> Dict[str, Dict[str, int]]:
        """Retourne les statistiques de tous les advisors."""
        return {advisor.name: advisor.stats for advisor in self.advisors}
    
    def reset_all_stats(self):
        """Remet à zéro toutes les statistiques."""
        for advisor in self.advisors:
            advisor.reset_stats()
        self.total_consultations = 0
        self.total_recommendations = 0
    
    def log_global_stats(self):
        """Affiche les statistiques globales du système d'advisors."""
        recommendation_rate = (self.total_recommendations / max(1, self.total_consultations * len(self.advisors)))
        
        self.logger.info(f"Advisor System Stats: "
                        f"Consultations={self.total_consultations}, "
                        f"Recommendations={self.total_recommendations}, "
                        f"Rate={recommendation_rate:.2%}")
        
        for advisor in self.advisors:
            advisor.log_stats()
    
    def get_recommended_moves_set(self, recommendations: Dict[str, Optional[MacroMove]]) -> Set[MacroMove]:
        """Extrait l'ensemble des moves recommandés par les advisors."""
        recommended_moves = set()
        for move in recommendations.values():
            if move is not None:
                recommended_moves.add(move)
        return recommended_moves


def create_advisor_system(features: FESSEnhancedFeatures, 
                         room_analyzer: FESSRoomAnalyzer) -> FESSAdvisorSystem:
    """Factory function pour créer un système d'advisors FESS complet."""
    return FESSAdvisorSystem(features, room_analyzer)