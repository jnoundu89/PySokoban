"""
Sokoban State module
====================

Représentation d'un état du jeu Sokoban pour les algorithmes FESS.
Compatible avec le système de notation et les macro moves.
"""

from typing import Set, Tuple, List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class SokobanState:
    """
    Représentation immutable d'un état Sokoban.
    
    Utilisée par les algorithmes FESS pour représenter les états
    du jeu de manière efficace et hashable.
    """
    
    player_position: Tuple[int, int]
    box_positions: frozenset  # Utilisé frozenset pour l'immutabilité et le hashing
    
    def __post_init__(self):
        """Validation post-initialisation."""
        if not isinstance(self.player_position, tuple) or len(self.player_position) != 2:
            raise ValueError("player_position must be a tuple of two integers")
        
        if not isinstance(self.box_positions, (set, frozenset)):
            # Convertit en frozenset si ce n'est pas déjà le cas
            object.__setattr__(self, 'box_positions', frozenset(self.box_positions))
    
    @classmethod
    def from_level(cls, level):
        """
        Crée un SokobanState depuis un objet Level.
        
        Args:
            level: Instance de Level avec player_pos et boxes
            
        Returns:
            SokobanState correspondant
        """
        return cls(
            player_position=level.player_pos,
            box_positions=frozenset(level.boxes)
        )
    
    def with_player_move(self, new_player_position: Tuple[int, int]) -> 'SokobanState':
        """
        Crée un nouvel état avec une nouvelle position du joueur.
        
        Args:
            new_player_position: Nouvelle position du joueur
            
        Returns:
            Nouvel état Sokoban
        """
        return SokobanState(
            player_position=new_player_position,
            box_positions=self.box_positions
        )
    
    def with_box_move(self, 
                     old_box_position: Tuple[int, int], 
                     new_box_position: Tuple[int, int]) -> 'SokobanState':
        """
        Crée un nouvel état avec une boîte déplacée.
        
        Args:
            old_box_position: Ancienne position de la boîte
            new_box_position: Nouvelle position de la boîte
            
        Returns:
            Nouvel état Sokoban
        """
        if old_box_position not in self.box_positions:
            raise ValueError(f"No box at position {old_box_position}")
        
        new_boxes = set(self.box_positions)
        new_boxes.remove(old_box_position)
        new_boxes.add(new_box_position)
        
        return SokobanState(
            player_position=self.player_position,
            box_positions=frozenset(new_boxes)
        )
    
    def with_player_and_box_move(self, 
                                new_player_position: Tuple[int, int],
                                old_box_position: Tuple[int, int], 
                                new_box_position: Tuple[int, int]) -> 'SokobanState':
        """
        Crée un nouvel état avec joueur et boîte déplacés (push move).
        
        Args:
            new_player_position: Nouvelle position du joueur
            old_box_position: Ancienne position de la boîte
            new_box_position: Nouvelle position de la boîte
            
        Returns:
            Nouvel état Sokoban
        """
        if old_box_position not in self.box_positions:
            raise ValueError(f"No box at position {old_box_position}")
        
        new_boxes = set(self.box_positions)
        new_boxes.remove(old_box_position)
        new_boxes.add(new_box_position)
        
        return SokobanState(
            player_position=new_player_position,
            box_positions=frozenset(new_boxes)
        )
    
    def get_box_at(self, position: Tuple[int, int]) -> bool:
        """
        Vérifie s'il y a une boîte à une position donnée.
        
        Args:
            position: Position à vérifier
            
        Returns:
            True s'il y a une boîte, False sinon
        """
        return position in self.box_positions
    
    def get_all_positions(self) -> Set[Tuple[int, int]]:
        """
        Retourne toutes les positions occupées (joueur + boîtes).
        
        Returns:
            Set de toutes les positions occupées
        """
        return {self.player_position} | set(self.box_positions)
    
    def is_equivalent_to(self, other: 'SokobanState') -> bool:
        """
        Vérifie si deux états sont équivalents.
        
        Args:
            other: Autre état à comparer
            
        Returns:
            True si les états sont équivalents
        """
        return (self.player_position == other.player_position and 
                self.box_positions == other.box_positions)
    
    def __str__(self) -> str:
        """Représentation string de l'état."""
        return f"SokobanState(player={self.player_position}, boxes={sorted(self.box_positions)})"
    
    def __repr__(self) -> str:
        """Représentation détaillée de l'état."""
        return self.__str__()
    
    def __hash__(self) -> int:
        """Hash de l'état pour utilisation en clé de dictionnaire."""
        return hash((self.player_position, self.box_positions))
    
    def __eq__(self, other) -> bool:
        """Égalité entre états."""
        if not isinstance(other, SokobanState):
            return False
        return (self.player_position == other.player_position and 
                self.box_positions == other.box_positions)


def create_state(player_pos: Tuple[int, int], 
                box_positions: List[Tuple[int, int]]) -> SokobanState:
    """
    Factory function pour créer un SokobanState.
    
    Args:
        player_pos: Position du joueur
        box_positions: Liste des positions des boîtes
        
    Returns:
        Nouvel état Sokoban
    """
    return SokobanState(
        player_position=player_pos,
        box_positions=frozenset(box_positions)
    )


def states_equal(state1: SokobanState, state2: SokobanState) -> bool:
    """
    Vérifie si deux états sont égaux.
    
    Args:
        state1: Premier état
        state2: Deuxième état
        
    Returns:
        True si les états sont égaux
    """
    return state1 == state2


def copy_state(state: SokobanState) -> SokobanState:
    """
    Copie un état (retourne le même objet car immutable).
    
    Args:
        state: État à copier
        
    Returns:
        Copie de l'état (même objet car immutable)
    """
    return state  # Pas besoin de copier car immutable


class StateManager:
    """
    Gestionnaire d'états pour optimiser les performances.
    
    Utilise un cache pour éviter de recréer des états identiques.
    """
    
    def __init__(self):
        self._state_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_or_create_state(self, 
                           player_pos: Tuple[int, int], 
                           box_positions: List[Tuple[int, int]]) -> SokobanState:
        """
        Récupère ou crée un état avec cache.
        
        Args:
            player_pos: Position du joueur
            box_positions: Positions des boîtes
            
        Returns:
            État Sokoban (depuis le cache si possible)
        """
        box_frozenset = frozenset(box_positions)
        key = (player_pos, box_frozenset)
        
        if key in self._state_cache:
            self._cache_hits += 1
            return self._state_cache[key]
        
        state = SokobanState(player_pos, box_frozenset)
        self._state_cache[key] = state
        self._cache_misses += 1
        
        return state
    
    def get_cache_stats(self) -> dict:
        """Retourne les statistiques du cache."""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0
        
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'total': total,
            'hit_rate': hit_rate,
            'cache_size': len(self._state_cache)
        }
    
    def clear_cache(self):
        """Vide le cache."""
        self._state_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0