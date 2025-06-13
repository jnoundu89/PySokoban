"""
Collecteur de métriques ML pour l'analyse des performances de résolution Sokoban.

Ce module implémente la collection complète de métriques pour l'apprentissage
automatique et l'analyse de performance selon le plan de refactoring.
"""

import math
import time
from typing import Dict, List, Tuple, Any, Set, Optional
from collections import Counter, defaultdict
import numpy as np
from dataclasses import dataclass


@dataclass
class MovementPattern:
    """Pattern de mouvement détecté."""
    sequence: List[str]
    frequency: int
    positions: List[Tuple[int, int]]
    is_loop: bool
    efficiency_score: float


@dataclass
class SpatialDistribution:
    """Distribution spatiale des éléments du niveau."""
    box_clustering_coefficient: float
    target_dispersion_index: float
    connectivity_score: float
    geometric_complexity: float
    symmetry_score: float


class MLMetricsCollector:
    """
    Collecteur de métriques ML pour l'analyse avancée des performances Sokoban.
    
    Collecte des métriques dans plusieurs catégories :
    - Métriques de performance de base
    - Analyse algorithmique avancée
    - Structure et complexité du niveau
    - Patterns de mouvement et efficacité
    - Corrélations et apprentissage
    """
    
    def __init__(self):
        self.collected_metrics_history = []
        self.movement_pattern_library = {}
        self.level_complexity_cache = {}
    
    def collect_solving_metrics(self, level, solution_data, solver_stats) -> Dict[str, Any]:
        """
        Collecte complète de toutes les métriques pour une résolution.
        
        Args:
            level: Instance du niveau résolu
            solution_data: Données de solution du solver
            solver_stats: Statistiques détaillées du solver
            
        Returns:
            Dict: Métriques complètes organisées par catégorie
        """
        # Métriques de base
        basic_metrics = self._collect_basic_metrics(solution_data, solver_stats)
        
        # Métriques algorithmiques avancées
        algorithm_metrics = self._collect_algorithm_metrics(solution_data, solver_stats)
        
        # Analyse de la structure du niveau
        level_structure = self._analyze_level_structure(level)
        
        # Analyse des patterns de mouvement
        movement_analysis = self._analyze_movement_patterns(solution_data.moves, level)
        
        # Distribution spatiale
        spatial_analysis = self._analyze_spatial_distribution(level)
        
        # Corrélations structure-performance
        correlation_analysis = self._analyze_structure_performance_correlation(
            level, solution_data, level_structure
        )
        
        # Métriques de qualité de solution
        solution_quality = self._analyze_solution_quality(solution_data, level)
        
        # Compilation des métriques complètes
        complete_metrics = {
            'timestamp': time.time(),
            'basic_metrics': basic_metrics,
            'algorithm_metrics': algorithm_metrics,
            'level_structure': level_structure,
            'movement_analysis': movement_analysis,
            'spatial_analysis': spatial_analysis,
            'correlation_analysis': correlation_analysis,
            'solution_quality': solution_quality,
            'ml_features': self._extract_ml_features(
                basic_metrics, algorithm_metrics, level_structure, 
                movement_analysis, spatial_analysis
            )
        }
        
        # Ajouter à l'historique
        self.collected_metrics_history.append(complete_metrics)
        
        return complete_metrics
    
    def _collect_basic_metrics(self, solution_data, solver_stats) -> Dict[str, Any]:
        """Collecte les métriques de performance de base."""
        return {
            'moves_count': len(solution_data.moves),
            'solve_time': solution_data.solve_time,
            'states_explored': solution_data.states_explored,
            'states_generated': solution_data.states_generated,
            'deadlocks_pruned': solution_data.deadlocks_pruned,
            'algorithm_used': solution_data.algorithm_used.value,
            'search_mode': solution_data.search_mode.value,
            'memory_peak': solution_data.memory_peak,
            'heuristic_calls': solution_data.heuristic_calls,
            'macro_moves_used': solution_data.macro_moves_used,
            
            # Métriques dérivées
            'states_per_second': solution_data.states_explored / max(solution_data.solve_time, 0.001),
            'moves_per_second': len(solution_data.moves) / max(solution_data.solve_time, 0.001),
            'pruning_efficiency': solution_data.deadlocks_pruned / max(solution_data.states_generated, 1),
            'exploration_efficiency': solution_data.states_explored / max(solution_data.states_generated, 1),
            'heuristic_frequency': solution_data.heuristic_calls / max(solution_data.states_explored, 1)
        }
    
    def _collect_algorithm_metrics(self, solution_data, solver_stats) -> Dict[str, Any]:
        """Collecte les métriques spécifiques à l'algorithme."""
        search_stats = solver_stats.get('search_statistics', {})
        deadlock_stats = solver_stats.get('deadlock_detection', {})
        table_stats = solver_stats.get('transposition_table', {})
        
        return {
            'algorithm_selection_accuracy': self._calculate_algorithm_accuracy(solution_data),
            'heuristic_effectiveness': self._calculate_heuristic_effectiveness(solution_data, search_stats),
            'deadlock_detection_rate': deadlock_stats.get('total_deadlocks_detected', 0) / max(search_stats.get('states_generated', 1), 1),
            'macro_move_utilization': solution_data.macro_moves_used / max(len(solution_data.moves), 1),
            'search_tree_efficiency': self._calculate_search_tree_efficiency(search_stats),
            'cache_performance': table_stats.get('hit_ratio', 0.0),
            'memory_efficiency': table_stats.get('load_factor', 0.0),
            
            # Métriques de convergence
            'convergence_rate': self._estimate_convergence_rate(search_stats),
            'branching_factor': search_stats.get('states_generated', 0) / max(search_stats.get('states_explored', 1), 1),
            'pruning_effectiveness': deadlock_stats.get('total_deadlocks_detected', 0) / max(search_stats.get('states_generated', 1), 1)
        }
    
    def _analyze_level_structure(self, level) -> Dict[str, Any]:
        """Analyse approfondie de la structure du niveau."""
        # Utiliser le cache si disponible
        level_key = self._generate_level_key(level)
        if level_key in self.level_complexity_cache:
            return self.level_complexity_cache[level_key]
        
        structure_analysis = {
            'basic_properties': {
                'width': level.width,
                'height': level.height,
                'total_area': level.width * level.height,
                'boxes_count': len(level.boxes),
                'targets_count': len(level.targets),
                'wall_density': self._calculate_wall_density(level)
            },
            
            'geometric_complexity': self._calculate_geometric_complexity(level),
            'connectivity_analysis': self._analyze_connectivity(level),
            'bottleneck_analysis': self._identify_bottlenecks(level),
            'corridor_analysis': self._analyze_corridors(level),
            'space_distribution': self._analyze_space_distribution(level),
            'topological_features': self._extract_topological_features(level)
        }
        
        # Mettre en cache
        self.level_complexity_cache[level_key] = structure_analysis
        return structure_analysis
    
    def _analyze_movement_patterns(self, moves: List[str], level) -> Dict[str, Any]:
        """Analyse détaillée des patterns de mouvement."""
        return {
            'direction_frequency': self._analyze_direction_frequency(moves),
            'sequence_patterns': self._find_movement_sequences(moves),
            'backtrack_analysis': self._analyze_backtracks(moves),
            'push_pull_analysis': self._analyze_push_pull_ratio(moves, level),
            'movement_entropy': self._calculate_movement_entropy(moves),
            'efficiency_metrics': self._calculate_movement_efficiency(moves, level),
            'pattern_complexity': self._calculate_pattern_complexity(moves),
            'spatial_movement_distribution': self._analyze_spatial_movement_distribution(moves, level)
        }
    
    def _analyze_spatial_distribution(self, level) -> Dict[str, Any]:
        """Analyse de la distribution spatiale des éléments."""
        return {
            'box_clustering': self._measure_box_clustering(level.boxes, level),
            'target_dispersion': self._measure_target_dispersion(level.targets, level),
            'box_target_correlation': self._calculate_box_target_spatial_correlation(level),
            'free_space_analysis': self._analyze_free_space_distribution(level),
            'geometric_features': self._extract_geometric_features(level),
            'symmetry_analysis': self._analyze_level_symmetries(level),
            'accessibility_map': self._create_accessibility_map(level)
        }
    
    def _analyze_structure_performance_correlation(self, level, solution_data, level_structure) -> Dict[str, Any]:
        """Analyse des corrélations entre structure du niveau et performance."""
        return {
            'complexity_solve_time_correlation': self._correlate_complexity_with_time(level_structure, solution_data),
            'structure_algorithm_effectiveness': self._correlate_structure_with_algorithm(level_structure, solution_data),
            'geometric_difficulty_correlation': self._correlate_geometry_with_difficulty(level_structure, solution_data),
            'spatial_efficiency_correlation': self._correlate_spatial_features_with_efficiency(level_structure, solution_data),
            'pattern_predictability': self._analyze_pattern_predictability(level, solution_data)
        }
    
    def _analyze_solution_quality(self, solution_data, level) -> Dict[str, Any]:
        """Analyse de la qualité de la solution."""
        return {
            'optimality_estimate': self._estimate_solution_optimality(solution_data, level),
            'solution_elegance': self._calculate_solution_elegance(solution_data),
            'redundancy_analysis': self._analyze_move_redundancy(solution_data.moves),
            'efficiency_score': self._calculate_overall_efficiency_score(solution_data, level),
            'comparative_metrics': self._calculate_comparative_metrics(solution_data, level)
        }
    
    # Implémentations détaillées des méthodes d'analyse
    
    def _calculate_wall_density(self, level) -> float:
        """Calcule la densité de murs dans le niveau."""
        total_cells = level.width * level.height
        wall_count = sum(1 for y in range(level.height) for x in range(level.width) if level.is_wall(x, y))
        return wall_count / total_cells
    
    def _calculate_geometric_complexity(self, level) -> Dict[str, float]:
        """Calcule la complexité géométrique du niveau."""
        # Analyse des contours et des formes
        perimeter = self._calculate_level_perimeter(level)
        area = self._calculate_free_area(level)
        compactness = (4 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
        
        # Analyse de la rugosité des bords
        edge_roughness = self._calculate_edge_roughness(level)
        
        # Analyse de la fragmentation
        fragmentation_index = self._calculate_fragmentation_index(level)
        
        return {
            'compactness': compactness,
            'edge_roughness': edge_roughness,
            'fragmentation_index': fragmentation_index,
            'aspect_ratio': level.width / level.height,
            'area_efficiency': area / (level.width * level.height)
        }
    
    def _analyze_connectivity(self, level) -> Dict[str, Any]:
        """Analyse la connectivité du niveau."""
        # Créer un graphe de connectivité
        connectivity_graph = self._build_connectivity_graph(level)
        
        # Calculer les métriques de connectivité
        components = self._find_connected_components(connectivity_graph)
        articulation_points = self._find_articulation_points(connectivity_graph)
        bridges = self._find_bridges(connectivity_graph)
        
        return {
            'connected_components': len(components),
            'largest_component_size': max(len(comp) for comp in components) if components else 0,
            'articulation_points_count': len(articulation_points),
            'bridges_count': len(bridges),
            'connectivity_density': len(connectivity_graph) / max(self._calculate_free_area(level), 1),
            'clustering_coefficient': self._calculate_clustering_coefficient(connectivity_graph)
        }
    
    def _analyze_direction_frequency(self, moves: List[str]) -> Dict[str, float]:
        """Analyse la fréquence des directions de mouvement."""
        if not moves:
            return {'UP': 0, 'DOWN': 0, 'LEFT': 0, 'RIGHT': 0}
        
        direction_counts = Counter(moves)
        total_moves = len(moves)
        
        return {
            'UP': direction_counts.get('UP', 0) / total_moves,
            'DOWN': direction_counts.get('DOWN', 0) / total_moves,
            'LEFT': direction_counts.get('LEFT', 0) / total_moves,
            'RIGHT': direction_counts.get('RIGHT', 0) / total_moves
        }
    
    def _find_movement_sequences(self, moves: List[str]) -> Dict[str, Any]:
        """Trouve les séquences récurrentes de mouvements."""
        sequences = {}
        
        # Chercher des patterns de longueur 2 à 5
        for length in range(2, min(6, len(moves) + 1)):
            pattern_counts = defaultdict(int)
            
            for i in range(len(moves) - length + 1):
                pattern = tuple(moves[i:i + length])
                pattern_counts[pattern] += 1
            
            # Garder seulement les patterns qui apparaissent plus d'une fois
            frequent_patterns = {k: v for k, v in pattern_counts.items() if v > 1}
            
            if frequent_patterns:
                sequences[f'length_{length}'] = dict(frequent_patterns)
        
        # Statistiques des séquences
        total_patterns = sum(len(patterns) for patterns in sequences.values())
        max_frequency = max(
            max(freq for freq in patterns.values()) if patterns else 0
            for patterns in sequences.values()
        ) if sequences else 0
        
        return {
            'sequences_by_length': sequences,
            'total_unique_patterns': total_patterns,
            'max_pattern_frequency': max_frequency,
            'pattern_diversity': len(sequences)
        }
    
    def _analyze_backtracks(self, moves: List[str]) -> Dict[str, Any]:
        """Analyse les retours en arrière dans les mouvements."""
        opposite_moves = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
        
        immediate_backtracks = 0
        delayed_backtracks = []
        
        for i in range(len(moves) - 1):
            if moves[i + 1] == opposite_moves.get(moves[i]):
                immediate_backtracks += 1
        
        # Chercher les backtracks retardés (retour à une position précédente)
        for i in range(len(moves)):
            for j in range(i + 2, min(i + 10, len(moves))):  # Chercher dans une fenêtre de 10 mouvements
                if moves[j] == opposite_moves.get(moves[i]):
                    delayed_backtracks.append(j - i)
        
        backtrack_ratio = immediate_backtracks / max(len(moves) - 1, 1)
        avg_backtrack_delay = sum(delayed_backtracks) / len(delayed_backtracks) if delayed_backtracks else 0
        
        return {
            'immediate_backtracks': immediate_backtracks,
            'delayed_backtracks_count': len(delayed_backtracks),
            'backtrack_ratio': backtrack_ratio,
            'average_backtrack_delay': avg_backtrack_delay,
            'backtrack_efficiency': 1.0 - backtrack_ratio  # Plus c'est haut, mieux c'est
        }
    
    def _calculate_movement_entropy(self, moves: List[str]) -> float:
        """Calcule l'entropie des mouvements pour mesurer la prévisibilité."""
        if not moves:
            return 0.0
        
        # Calculer les probabilités de chaque direction
        direction_counts = Counter(moves)
        total_moves = len(moves)
        probabilities = [count / total_moves for count in direction_counts.values()]
        
        # Calculer l'entropie de Shannon
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
        
        # Normaliser par l'entropie maximale (log2(4) pour 4 directions)
        max_entropy = math.log2(4)
        normalized_entropy = entropy / max_entropy
        
        return normalized_entropy
    
    def _measure_box_clustering(self, boxes: List[Tuple[int, int]], level) -> Dict[str, float]:
        """Mesure le clustering des boxes."""
        if len(boxes) < 2:
            return {'clustering_coefficient': 0.0, 'average_distance': 0.0, 'cluster_count': len(boxes)}
        
        # Calculer les distances entre toutes les paires de boxes
        distances = []
        for i, box1 in enumerate(boxes):
            for box2 in boxes[i + 1:]:
                dist = abs(box1[0] - box2[0]) + abs(box1[1] - box2[1])  # Distance Manhattan
                distances.append(dist)
        
        avg_distance = sum(distances) / len(distances)
        
        # Calculer le coefficient de clustering
        # Une box est considérée comme "connectée" à une autre si la distance <= 2
        connections = sum(1 for dist in distances if dist <= 2)
        max_connections = len(distances)
        clustering_coefficient = connections / max_connections if max_connections > 0 else 0
        
        # Estimer le nombre de clusters
        cluster_count = self._estimate_cluster_count(boxes)
        
        return {
            'clustering_coefficient': clustering_coefficient,
            'average_distance': avg_distance,
            'cluster_count': cluster_count,
            'max_distance': max(distances) if distances else 0,
            'min_distance': min(distances) if distances else 0
        }
    
    def _estimate_cluster_count(self, positions: List[Tuple[int, int]]) -> int:
        """Estime le nombre de clusters dans un ensemble de positions."""
        if not positions:
            return 0
        
        visited = set()
        clusters = 0
        
        def dfs(pos, cluster_positions):
            if pos in visited:
                return
            visited.add(pos)
            cluster_positions.append(pos)
            
            # Chercher les positions adjacentes (distance Manhattan <= 2)
            for other_pos in positions:
                if other_pos not in visited:
                    dist = abs(pos[0] - other_pos[0]) + abs(pos[1] - other_pos[1])
                    if dist <= 2:
                        dfs(other_pos, cluster_positions)
        
        for pos in positions:
            if pos not in visited:
                cluster_positions = []
                dfs(pos, cluster_positions)
                if cluster_positions:
                    clusters += 1
        
        return clusters
    
    def _extract_ml_features(self, basic_metrics, algorithm_metrics, level_structure, 
                           movement_analysis, spatial_analysis) -> Dict[str, float]:
        """Extrait un vecteur de features pour l'apprentissage automatique."""
        features = {}
        
        # Features de performance normalisées
        features.update({
            'log_solve_time': math.log1p(basic_metrics['solve_time']),
            'log_states_explored': math.log1p(basic_metrics['states_explored']),
            'moves_count_normalized': basic_metrics['moves_count'] / max(level_structure['basic_properties']['total_area'], 1),
            'exploration_efficiency': algorithm_metrics['search_tree_efficiency'],
            'pruning_efficiency': basic_metrics['pruning_efficiency']
        })
        
        # Features de structure du niveau
        features.update({
            'level_area': level_structure['basic_properties']['total_area'],
            'box_density': level_structure['basic_properties']['boxes_count'] / level_structure['basic_properties']['total_area'],
            'wall_density': level_structure['basic_properties']['wall_density'],
            'aspect_ratio': level_structure['geometric_complexity']['aspect_ratio'],
            'compactness': level_structure['geometric_complexity']['compactness'],
            'connectivity_density': level_structure['connectivity_analysis']['connectivity_density']
        })
        
        # Features de mouvement
        features.update({
            'movement_entropy': movement_analysis['movement_entropy'],
            'backtrack_efficiency': movement_analysis['backtrack_analysis']['backtrack_efficiency'],
            'pattern_complexity': movement_analysis.get('pattern_complexity', 0),
            'direction_balance': self._calculate_direction_balance(movement_analysis['direction_frequency'])
        })
        
        # Features spatiales
        features.update({
            'box_clustering': spatial_analysis['box_clustering']['clustering_coefficient'],
            'target_dispersion': spatial_analysis['target_dispersion'].get('dispersion_index', 0),
            'spatial_correlation': spatial_analysis.get('box_target_correlation', {}).get('correlation_coefficient', 0)
        })
        
        return features
    
    def _calculate_direction_balance(self, direction_freq: Dict[str, float]) -> float:
        """Calcule l'équilibre dans l'utilisation des directions."""
        frequencies = list(direction_freq.values())
        if not frequencies:
            return 0.0
        
        # Calculer l'écart type des fréquences (plus c'est bas, plus c'est équilibré)
        mean_freq = sum(frequencies) / len(frequencies)
        variance = sum((f - mean_freq) ** 2 for f in frequencies) / len(frequencies)
        std_dev = math.sqrt(variance)
        
        # Normaliser : équilibré parfait = 1, déséquilibré = 0
        max_std = 0.5  # Maximum théorique quand une direction = 1, autres = 0
        balance = 1.0 - (std_dev / max_std)
        
        return max(0.0, balance)
    
    # Méthodes utilitaires supplémentaires
    
    def _generate_level_key(self, level) -> str:
        """Génère une clé unique pour un niveau (pour le cache)."""
        # Utiliser une représentation simplifiée du niveau
        walls_str = ''.join('1' if level.is_wall(x, y) else '0' 
                           for y in range(level.height) 
                           for x in range(level.width))
        boxes_str = ''.join(f"{x},{y};" for x, y in sorted(level.boxes))
        targets_str = ''.join(f"{x},{y};" for x, y in sorted(level.targets))
        
        return f"{level.width}x{level.height}_{hash(walls_str + boxes_str + targets_str)}"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtient un résumé des métriques collectées."""
        if not self.collected_metrics_history:
            return {'message': 'Aucune métrique collectée'}
        
        # Calculer des moyennes et statistiques
        successful_metrics = [m for m in self.collected_metrics_history 
                             if m['basic_metrics']['moves_count'] > 0]
        
        if not successful_metrics:
            return {'message': 'Aucune résolution réussie'}
        
        avg_solve_time = sum(m['basic_metrics']['solve_time'] for m in successful_metrics) / len(successful_metrics)
        avg_moves = sum(m['basic_metrics']['moves_count'] for m in successful_metrics) / len(successful_metrics)
        avg_states = sum(m['basic_metrics']['states_explored'] for m in successful_metrics) / len(successful_metrics)
        
        return {
            'total_collections': len(self.collected_metrics_history),
            'successful_solves': len(successful_metrics),
            'averages': {
                'solve_time': avg_solve_time,
                'moves_count': avg_moves,
                'states_explored': avg_states
            },
            'algorithms_used': list(set(m['basic_metrics']['algorithm_used'] for m in successful_metrics)),
            'patterns_learned': len(self.movement_pattern_library)
        }
    
    def export_training_data(self, filepath: str):
        """Exporte les données pour l'entraînement ML."""
        training_data = []
        
        for metrics in self.collected_metrics_history:
            if 'ml_features' in metrics:
                training_data.append({
                    'features': metrics['ml_features'],
                    'labels': {
                        'solve_time': metrics['basic_metrics']['solve_time'],
                        'moves_count': metrics['basic_metrics']['moves_count'],
                        'success': metrics['basic_metrics']['moves_count'] > 0,
                        'algorithm_used': metrics['basic_metrics']['algorithm_used']
                    }
                })
        
        import json
        with open(filepath, 'w') as f:
            json.dump(training_data, f, indent=2)