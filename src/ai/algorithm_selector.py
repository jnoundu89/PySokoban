"""
Sélecteur d'algorithme automatique pour le système IA Sokoban.

Ce module implémente la logique de sélection automatique d'algorithme
basée sur la complexité du niveau, inspirée des techniques Sokolution.
"""

from enum import Enum
from typing import Dict, Any
import math


class Algorithm(Enum):
    """Énumération des algorithmes disponibles."""
    FESS = "FESS"  # Feature Space Search - Algorithme par défaut
    BFS = "BFS"
    ASTAR = "A*"
    IDA_STAR = "IDA*"
    GREEDY = "GREEDY"
    BIDIRECTIONAL_GREEDY = "BIDIRECTIONAL_GREEDY"


class ComplexityAnalyzer:
    """Analyseur de complexité pour les niveaux Sokoban."""
    
    def __init__(self):
        self.complexity_factors = {
            'base_size_weight': 0.5,
            'box_penalty': 15,
            'target_penalty': 10,
            'large_level_multiplier': 1.5,
            'very_complex_multiplier': 1.2
        }
    
    def calculate_complexity_score(self, level) -> float:
        """
        Calcule le score de complexité d'un niveau.
        
        Args:
            level: Instance de Level à analyser
            
        Returns:
            float: Score de complexité du niveau
        """
        # Calcul de base : taille du niveau
        base_score = level.width * level.height * self.complexity_factors['base_size_weight']
        
        # Pénalités pour les boxes et targets
        box_penalty = len(level.boxes) * self.complexity_factors['box_penalty']
        target_penalty = len(level.targets) * self.complexity_factors['target_penalty']
        
        complexity_score = base_score + box_penalty + target_penalty
        
        # Multiplicateurs pour les niveaux complexes
        if self._is_large_level_with_many_boxes(level):
            complexity_score *= self.complexity_factors['large_level_multiplier']
            
        if self._is_very_complex_level(level):
            complexity_score *= self.complexity_factors['very_complex_multiplier']
            
        # Facteurs additionnels de complexité
        complexity_score += self._calculate_spatial_complexity(level)
        complexity_score += self._calculate_connectivity_complexity(level)
        
        return complexity_score
    
    def _is_large_level_with_many_boxes(self, level) -> bool:
        """Vérifie si le niveau est grand avec beaucoup de boxes."""
        return len(level.boxes) > 5 and (level.width * level.height) > 150
    
    def _is_very_complex_level(self, level) -> bool:
        """Vérifie si le niveau est très complexe."""
        return len(level.boxes) > 8 and (level.width * level.height) > 200
    
    def _calculate_spatial_complexity(self, level) -> float:
        """Calcule la complexité spatiale du niveau."""
        # Analyse de la distribution des boxes et targets
        box_dispersion = self._calculate_dispersion(level.boxes, level.width, level.height)
        target_dispersion = self._calculate_dispersion(level.targets, level.width, level.height)
        
        # Plus la dispersion est élevée, plus c'est complexe
        spatial_complexity = (box_dispersion + target_dispersion) * 5
        
        return spatial_complexity
    
    def _calculate_connectivity_complexity(self, level) -> float:
        """Calcule la complexité de connectivité du niveau."""
        # Analyse du nombre de corridors et d'espaces ouverts
        free_spaces = self._count_free_spaces(level)
        corridors = self._estimate_corridors(level)
        
        # Plus il y a de corridors par rapport aux espaces libres, plus c'est complexe
        if free_spaces > 0:
            corridor_ratio = corridors / free_spaces
            return corridor_ratio * 20
        
        return 0
    
    def _calculate_dispersion(self, positions, width, height) -> float:
        """Calcule la dispersion d'un ensemble de positions."""
        if len(positions) < 2:
            return 0
        
        # Calcul du centre de masse
        center_x = sum(pos[0] for pos in positions) / len(positions)
        center_y = sum(pos[1] for pos in positions) / len(positions)
        
        # Calcul de la variance par rapport au centre
        variance = sum((pos[0] - center_x)**2 + (pos[1] - center_y)**2 for pos in positions)
        variance /= len(positions)
        
        # Normalisation par la taille du niveau
        max_distance_squared = (width**2 + height**2) / 4
        return math.sqrt(variance / max_distance_squared) if max_distance_squared > 0 else 0
    
    def _count_free_spaces(self, level) -> int:
        """Compte le nombre d'espaces libres dans le niveau."""
        free_count = 0
        for y in range(level.height):
            for x in range(level.width):
                if not level.is_wall(x, y):
                    free_count += 1
        return free_count
    
    def _estimate_corridors(self, level) -> int:
        """Estime le nombre de corridors dans le niveau."""
        corridor_count = 0
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                if not level.is_wall(x, y):
                    # Vérifie si c'est un corridor (2 murs opposés)
                    if ((level.is_wall(x-1, y) and level.is_wall(x+1, y)) or
                        (level.is_wall(x, y-1) and level.is_wall(x, y+1))):
                        corridor_count += 1
        return corridor_count


class AlgorithmSelector:
    """
    Sélectionneur automatique d'algorithme pour la résolution Sokoban.
    
    Choisit l'algorithme optimal basé sur la complexité du niveau
    selon les principes du solver Sokolution.
    """
    
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.algorithm_thresholds = {
            'simple': 50,      # BFS pour niveaux simples
            'medium': 150,     # A* pour niveaux moyens
            'complex': 300,    # IDA* pour niveaux complexes
            'expert': float('inf')  # Bidirectional Greedy pour niveaux experts
        }
        
        # Statistiques de sélection
        self.selection_stats = {
            Algorithm.FESS: 0,
            Algorithm.BFS: 0,
            Algorithm.ASTAR: 0,
            Algorithm.IDA_STAR: 0,
            Algorithm.GREEDY: 0,
            Algorithm.BIDIRECTIONAL_GREEDY: 0
        }
    
    def select_optimal_algorithm(self, level) -> Algorithm:
        """
        Sélectionne l'algorithme optimal pour un niveau donné.
        
        Args:
            level: Instance de Level à analyser
            
        Returns:
            Algorithm: Algorithme optimal sélectionné
        """
        complexity_score = self.complexity_analyzer.calculate_complexity_score(level)
        
        # FESS comme algorithme par défaut pour tous les niveaux
        # Il s'adapte automatiquement à la complexité via ses features
        selected_algorithm = Algorithm.FESS
        
        # Garder l'ancienne logique comme fallback si FESS échoue
        self.fallback_algorithm = self._select_fallback_algorithm(complexity_score)
        
        # Mise à jour des statistiques
        self.selection_stats[selected_algorithm] += 1
        
        return selected_algorithm
    
    def _select_fallback_algorithm(self, complexity_score: float) -> Algorithm:
        """Sélectionne un algorithme de fallback si FESS échoue."""
        if complexity_score < self.algorithm_thresholds['simple']:
            return Algorithm.BFS
        elif complexity_score < self.algorithm_thresholds['medium']:
            return Algorithm.ASTAR
        elif complexity_score < self.algorithm_thresholds['complex']:
            return Algorithm.IDA_STAR
        else:
            return Algorithm.BIDIRECTIONAL_GREEDY
    
    def get_fallback_algorithm(self, level) -> Algorithm:
        """Obtient l'algorithme de fallback pour un niveau."""
        complexity_score = self.complexity_analyzer.calculate_complexity_score(level)
        return self._select_fallback_algorithm(complexity_score)
    
    def get_algorithm_recommendation(self, level) -> Dict[str, Any]:
        """
        Obtient une recommandation détaillée d'algorithme.
        
        Args:
            level: Instance de Level à analyser
            
        Returns:
            Dict contenant les détails de la recommandation
        """
        complexity_score = self.complexity_analyzer.calculate_complexity_score(level)
        selected_algorithm = self.select_optimal_algorithm(level)
        
        return {
            'recommended_algorithm': selected_algorithm,
            'complexity_score': complexity_score,
            'complexity_category': self._get_complexity_category(complexity_score),
            'reasoning': self._get_selection_reasoning(complexity_score, selected_algorithm),
            'expected_performance': self._get_expected_performance(selected_algorithm),
            'alternative_algorithms': self._get_alternative_algorithms(complexity_score)
        }
    
    def _get_complexity_category(self, complexity_score: float) -> str:
        """Détermine la catégorie de complexité."""
        if complexity_score < self.algorithm_thresholds['simple']:
            return "Simple"
        elif complexity_score < self.algorithm_thresholds['medium']:
            return "Medium"
        elif complexity_score < self.algorithm_thresholds['complex']:
            return "Complex"
        else:
            return "Expert"
    
    def _get_selection_reasoning(self, complexity_score: float, algorithm: Algorithm) -> str:
        """Génère l'explication du choix d'algorithme."""
        category = self._get_complexity_category(complexity_score)
        
        reasoning_map = {
            Algorithm.FESS: f"Niveau {category.lower()} (score: {complexity_score:.1f}) - FESS (Feature Space Search) recommandé comme algorithme optimal adaptatif",
            Algorithm.BFS: f"Niveau {category.lower()} (score: {complexity_score:.1f}) - BFS optimal pour exploration exhaustive rapide",
            Algorithm.ASTAR: f"Niveau {category.lower()} (score: {complexity_score:.1f}) - A* optimal avec heuristique pour équilibrer rapidité et optimalité",
            Algorithm.IDA_STAR: f"Niveau {category.lower()} (score: {complexity_score:.1f}) - IDA* recommandé pour économiser la mémoire sur niveau complexe",
            Algorithm.BIDIRECTIONAL_GREEDY: f"Niveau {category.lower()} (score: {complexity_score:.1f}) - Recherche bidirectionnelle nécessaire pour niveau expert"
        }
        
        return reasoning_map.get(algorithm, f"Algorithme {algorithm.value} sélectionné pour score {complexity_score:.1f}")
    
    def _get_expected_performance(self, algorithm: Algorithm) -> Dict[str, str]:
        """Obtient les performances attendues pour un algorithme."""
        performance_map = {
            Algorithm.FESS: {
                'speed': 'Très rapide',
                'memory': 'Optimisée',
                'optimality': 'Quasi-optimal',
                'suitability': 'Tous niveaux'
            },
            Algorithm.BFS: {
                'speed': 'Rapide',
                'memory': 'Modérée',
                'optimality': 'Optimal',
                'suitability': 'Niveaux simples'
            },
            Algorithm.ASTAR: {
                'speed': 'Modérée',
                'memory': 'Élevée',
                'optimality': 'Optimal',
                'suitability': 'Niveaux moyens'
            },
            Algorithm.IDA_STAR: {
                'speed': 'Lente',
                'memory': 'Faible',
                'optimality': 'Optimal',
                'suitability': 'Niveaux complexes'
            },
            Algorithm.BIDIRECTIONAL_GREEDY: {
                'speed': 'Variable',
                'memory': 'Élevée',
                'optimality': 'Non-optimal',
                'suitability': 'Niveaux experts'
            }
        }
        
        return performance_map.get(algorithm, {
            'speed': 'Inconnue',
            'memory': 'Inconnue',
            'optimality': 'Inconnue',
            'suitability': 'Général'
        })
    
    def _get_alternative_algorithms(self, complexity_score: float) -> list:
        """Obtient les algorithmes alternatifs possibles."""
        alternatives = []
        
        # Toujours proposer BFS comme alternative rapide
        if complexity_score >= self.algorithm_thresholds['simple']:
            alternatives.append(Algorithm.BFS)
        
        # Proposer A* pour les niveaux pas trop complexes
        if complexity_score < self.algorithm_thresholds['complex']:
            alternatives.append(Algorithm.ASTAR)
        
        # Proposer Greedy pour une solution rapide non-optimale
        alternatives.append(Algorithm.GREEDY)
        
        return alternatives
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de sélection d'algorithmes."""
        total_selections = sum(self.selection_stats.values())
        
        if total_selections == 0:
            return {'total_selections': 0, 'algorithm_distribution': {}}
        
        distribution = {
            algorithm.value: count / total_selections * 100 
            for algorithm, count in self.selection_stats.items()
        }
        
        return {
            'total_selections': total_selections,
            'algorithm_distribution': distribution,
            'most_used_algorithm': max(self.selection_stats, key=self.selection_stats.get).value,
            'raw_counts': {algo.value: count for algo, count in self.selection_stats.items()}
        }
    
    def reset_statistics(self):
        """Remet à zéro les statistiques de sélection."""
        for algorithm in self.selection_stats:
            self.selection_stats[algorithm] = 0