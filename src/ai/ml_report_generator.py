"""
Générateur de rapports ML pour l'analyse des performances Sokoban.

Ce module génère des rapports complets en plusieurs formats (JSON, HTML, CSV)
avec visualisations et analyses statistiques avancées.
"""

import json
import time
import math
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class MLReportGenerator:
    """
    Générateur de rapports ML complets pour l'analyse des performances Sokoban.
    
    Génère des rapports détaillés incluant :
    - Analyse de performance
    - Métriques ML structurées  
    - Recommandations d'optimisation
    - Visualisations de données
    - Export multi-format
    """
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.report_history = []
    
    def generate_comprehensive_report(self, level, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport ML complet pour une résolution.
        
        Args:
            level: Instance du niveau résolu
            solution_data: Données de solution
            metrics: Métriques collectées par MLMetricsCollector
            
        Returns:
            Dict: Rapport complet structuré
        """
        timestamp = datetime.now()
        
        # Structure du rapport principal
        report = {
            'metadata': self._generate_metadata(timestamp, level, solution_data),
            'executive_summary': self._generate_executive_summary(solution_data, metrics),
            'performance_analysis': self._analyze_performance(solution_data, metrics),
            'algorithm_analysis': self._analyze_algorithm_performance(solution_data, metrics),
            'level_analysis': self._analyze_level_characteristics(level, metrics),
            'movement_analysis': self._analyze_movement_patterns(solution_data, metrics),
            'spatial_analysis': self._analyze_spatial_distribution(metrics),
            'efficiency_analysis': self._analyze_efficiency_metrics(solution_data, metrics),
            'ml_features': self._structure_ml_features(metrics),
            'comparative_analysis': self._generate_comparative_analysis(metrics),
            'recommendations': self._generate_recommendations(solution_data, metrics),
            'visualizations': self._prepare_visualization_data(metrics),
            'raw_data': self._prepare_raw_data_export(solution_data, metrics)
        }
        
        # Sauvegarder dans l'historique
        self.report_history.append(report)
        
        # Exporter en différents formats
        report_id = self._generate_report_id(timestamp)
        self._export_json_report(report, report_id)
        self._export_html_report(report, report_id)
        self._export_csv_features(report['ml_features'], report_id)
        
        return report
    
    def _generate_metadata(self, timestamp: datetime, level, solution_data) -> Dict[str, Any]:
        """Génère les métadonnées du rapport."""
        return {
            'report_id': self._generate_report_id(timestamp),
            'generation_timestamp': timestamp.isoformat(),
            'generator_version': '2.0.0',
            'level_info': {
                'dimensions': f"{level.width}x{level.height}",
                'boxes_count': len(level.boxes),
                'targets_count': len(level.targets),
                'level_area': level.width * level.height
            },
            'solution_info': {
                'algorithm_used': solution_data.algorithm_used.value,
                'search_mode': solution_data.search_mode.value,
                'moves_count': len(solution_data.moves),
                'solve_time': solution_data.solve_time,
                'success': True
            }
        }
    
    def _generate_executive_summary(self, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le résumé exécutif du rapport."""
        basic_metrics = metrics.get('basic_metrics', {})
        algorithm_metrics = metrics.get('algorithm_metrics', {})
        
        # Calculer des scores de performance
        efficiency_score = self._calculate_efficiency_score(basic_metrics)
        algorithm_effectiveness = algorithm_metrics.get('heuristic_effectiveness', 0)
        
        # Déterminer les points forts et faibles
        strengths = []
        weaknesses = []
        
        if efficiency_score > 0.8:
            strengths.append("Excellente efficacité de résolution")
        elif efficiency_score < 0.4:
            weaknesses.append("Efficacité de résolution faible")
        
        if basic_metrics.get('pruning_efficiency', 0) > 0.6:
            strengths.append("Détection de deadlocks efficace")
        else:
            weaknesses.append("Détection de deadlocks à améliorer")
        
        if algorithm_effectiveness > 0.7:
            strengths.append("Heuristiques très efficaces")
        elif algorithm_effectiveness < 0.3:
            weaknesses.append("Heuristiques peu efficaces")
        
        return {
            'overall_performance_score': (efficiency_score + algorithm_effectiveness) / 2,
            'efficiency_score': efficiency_score,
            'algorithm_effectiveness': algorithm_effectiveness,
            'key_metrics': {
                'solve_time': basic_metrics.get('solve_time', 0),
                'moves_count': basic_metrics.get('moves_count', 0),
                'states_explored': basic_metrics.get('states_explored', 0),
                'algorithm_used': basic_metrics.get('algorithm_used', 'Unknown')
            },
            'strengths': strengths,
            'weaknesses': weaknesses,
            'performance_category': self._categorize_performance(efficiency_score)
        }
    
    def _analyze_performance(self, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse détaillée des performances."""
        basic_metrics = metrics.get('basic_metrics', {})
        
        return {
            'timing_analysis': {
                'solve_time': basic_metrics.get('solve_time', 0),
                'states_per_second': basic_metrics.get('states_per_second', 0),
                'moves_per_second': basic_metrics.get('moves_per_second', 0),
                'time_efficiency_rating': self._rate_time_efficiency(basic_metrics.get('solve_time', 0))
            },
            'search_efficiency': {
                'states_explored': basic_metrics.get('states_explored', 0),
                'states_generated': basic_metrics.get('states_generated', 0),
                'exploration_efficiency': basic_metrics.get('exploration_efficiency', 0),
                'pruning_efficiency': basic_metrics.get('pruning_efficiency', 0),
                'search_efficiency_rating': self._rate_search_efficiency(basic_metrics)
            },
            'memory_usage': {
                'memory_peak': basic_metrics.get('memory_peak', 0),
                'memory_efficiency_rating': self._rate_memory_efficiency(basic_metrics.get('memory_peak', 0))
            },
            'solution_quality': {
                'moves_count': basic_metrics.get('moves_count', 0),
                'macro_moves_used': basic_metrics.get('macro_moves_used', 0),
                'solution_compactness': self._calculate_solution_compactness(solution_data),
                'quality_rating': self._rate_solution_quality(solution_data)
            }
        }
    
    def _analyze_algorithm_performance(self, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse de la performance algorithmique."""
        algorithm_metrics = metrics.get('algorithm_metrics', {})
        basic_metrics = metrics.get('basic_metrics', {})
        
        return {
            'algorithm_selection': {
                'algorithm_used': basic_metrics.get('algorithm_used', 'Unknown'),
                'selection_appropriateness': self._evaluate_algorithm_appropriateness(solution_data, metrics),
                'alternative_suggestions': self._suggest_alternative_algorithms(metrics)
            },
            'heuristic_performance': {
                'heuristic_calls': basic_metrics.get('heuristic_calls', 0),
                'heuristic_frequency': basic_metrics.get('heuristic_frequency', 0),
                'heuristic_effectiveness': algorithm_metrics.get('heuristic_effectiveness', 0),
                'heuristic_rating': self._rate_heuristic_performance(algorithm_metrics)
            },
            'pruning_analysis': {
                'deadlocks_pruned': basic_metrics.get('deadlocks_pruned', 0),
                'pruning_efficiency': basic_metrics.get('pruning_efficiency', 0),
                'pruning_effectiveness': algorithm_metrics.get('pruning_effectiveness', 0),
                'pruning_rating': self._rate_pruning_performance(algorithm_metrics)
            },
            'convergence_analysis': {
                'convergence_rate': algorithm_metrics.get('convergence_rate', 0),
                'branching_factor': algorithm_metrics.get('branching_factor', 0),
                'search_tree_efficiency': algorithm_metrics.get('search_tree_efficiency', 0),
                'convergence_rating': self._rate_convergence_performance(algorithm_metrics)
            }
        }
    
    def _analyze_level_characteristics(self, level, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse des caractéristiques du niveau."""
        level_structure = metrics.get('level_structure', {})
        basic_props = level_structure.get('basic_properties', {})
        geometric = level_structure.get('geometric_complexity', {})
        connectivity = level_structure.get('connectivity_analysis', {})
        
        return {
            'structural_properties': {
                'dimensions': f"{basic_props.get('width', 0)}x{basic_props.get('height', 0)}",
                'total_area': basic_props.get('total_area', 0),
                'wall_density': basic_props.get('wall_density', 0),
                'boxes_density': basic_props.get('boxes_count', 0) / max(basic_props.get('total_area', 1), 1),
                'structural_complexity_rating': self._rate_structural_complexity(basic_props)
            },
            'geometric_analysis': {
                'compactness': geometric.get('compactness', 0),
                'aspect_ratio': geometric.get('aspect_ratio', 0),
                'edge_roughness': geometric.get('edge_roughness', 0),
                'fragmentation_index': geometric.get('fragmentation_index', 0),
                'geometric_complexity_rating': self._rate_geometric_complexity(geometric)
            },
            'connectivity_features': {
                'connected_components': connectivity.get('connected_components', 0),
                'articulation_points': connectivity.get('articulation_points_count', 0),
                'bridges_count': connectivity.get('bridges_count', 0),
                'connectivity_density': connectivity.get('connectivity_density', 0),
                'connectivity_rating': self._rate_connectivity_complexity(connectivity)
            },
            'difficulty_assessment': {
                'estimated_difficulty': self._estimate_level_difficulty(level_structure),
                'complexity_factors': self._identify_complexity_factors(level_structure),
                'difficulty_category': self._categorize_difficulty(level_structure)
            }
        }
    
    def _analyze_movement_patterns(self, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse des patterns de mouvement."""
        movement_analysis = metrics.get('movement_analysis', {})
        
        return {
            'movement_distribution': movement_analysis.get('direction_frequency', {}),
            'pattern_analysis': {
                'sequence_patterns': movement_analysis.get('sequence_patterns', {}),
                'pattern_complexity': movement_analysis.get('pattern_complexity', 0),
                'movement_entropy': movement_analysis.get('movement_entropy', 0),
                'pattern_efficiency_rating': self._rate_pattern_efficiency(movement_analysis)
            },
            'efficiency_metrics': {
                'backtrack_analysis': movement_analysis.get('backtrack_analysis', {}),
                'push_pull_analysis': movement_analysis.get('push_pull_analysis', {}),
                'movement_efficiency': movement_analysis.get('efficiency_metrics', {}),
                'movement_efficiency_rating': self._rate_movement_efficiency(movement_analysis)
            },
            'optimization_opportunities': self._identify_movement_optimizations(movement_analysis)
        }
    
    def _analyze_spatial_distribution(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse de la distribution spatiale."""
        spatial_analysis = metrics.get('spatial_analysis', {})
        
        return {
            'clustering_analysis': spatial_analysis.get('box_clustering', {}),
            'dispersion_analysis': spatial_analysis.get('target_dispersion', {}),
            'correlation_analysis': spatial_analysis.get('box_target_correlation', {}),
            'geometric_features': spatial_analysis.get('geometric_features', {}),
            'spatial_efficiency_rating': self._rate_spatial_efficiency(spatial_analysis),
            'spatial_optimization_suggestions': self._suggest_spatial_optimizations(spatial_analysis)
        }
    
    def _analyze_efficiency_metrics(self, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse des métriques d'efficacité."""
        basic_metrics = metrics.get('basic_metrics', {})
        solution_quality = metrics.get('solution_quality', {})
        
        # Calculer des métriques d'efficacité dérivées
        time_efficiency = 1.0 / (1.0 + basic_metrics.get('solve_time', 1))
        space_efficiency = basic_metrics.get('exploration_efficiency', 0)
        solution_efficiency = solution_quality.get('efficiency_score', 0)
        
        overall_efficiency = (time_efficiency + space_efficiency + solution_efficiency) / 3
        
        return {
            'time_efficiency': {
                'score': time_efficiency,
                'solve_time': basic_metrics.get('solve_time', 0),
                'states_per_second': basic_metrics.get('states_per_second', 0),
                'rating': self._rate_time_efficiency(basic_metrics.get('solve_time', 0))
            },
            'space_efficiency': {
                'score': space_efficiency,
                'exploration_efficiency': basic_metrics.get('exploration_efficiency', 0),
                'pruning_efficiency': basic_metrics.get('pruning_efficiency', 0),
                'rating': self._rate_space_efficiency(basic_metrics)
            },
            'solution_efficiency': {
                'score': solution_efficiency,
                'moves_count': basic_metrics.get('moves_count', 0),
                'optimality_estimate': solution_quality.get('optimality_estimate', 0),
                'rating': self._rate_solution_efficiency(solution_quality)
            },
            'overall_efficiency': {
                'score': overall_efficiency,
                'rating': self._rate_overall_efficiency(overall_efficiency),
                'improvement_potential': 1.0 - overall_efficiency
            }
        }
    
    def _structure_ml_features(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Structure les features ML pour export."""
        ml_features = metrics.get('ml_features', {})
        
        # Organiser les features par catégorie
        structured_features = {
            'performance_features': {
                k: v for k, v in ml_features.items() 
                if any(perf_key in k for perf_key in ['time', 'states', 'moves', 'efficiency'])
            },
            'structural_features': {
                k: v for k, v in ml_features.items()
                if any(struct_key in k for struct_key in ['area', 'density', 'ratio', 'compactness'])
            },
            'movement_features': {
                k: v for k, v in ml_features.items()
                if any(mov_key in k for mov_key in ['entropy', 'backtrack', 'pattern', 'direction'])
            },
            'spatial_features': {
                k: v for k, v in ml_features.items()
                if any(spat_key in k for spat_key in ['clustering', 'dispersion', 'correlation'])
            }
        }
        
        # Ajouter des métadonnées sur les features
        structured_features['feature_metadata'] = {
            'total_features': len(ml_features),
            'feature_categories': len(structured_features) - 1,  # -1 pour exclure metadata
            'feature_completeness': self._calculate_feature_completeness(ml_features),
            'feature_quality_score': self._assess_feature_quality(ml_features)
        }
        
        return structured_features
    
    def _generate_comparative_analysis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une analyse comparative avec l'historique."""
        if len(self.report_history) < 2:
            return {'message': 'Insufficient historical data for comparison'}
        
        # Comparer avec la moyenne historique
        current_performance = self._extract_performance_metrics(metrics)
        historical_average = self._calculate_historical_average()
        
        comparison = {}
        for key, current_value in current_performance.items():
            historical_value = historical_average.get(key, current_value)
            if historical_value != 0:
                improvement = (current_value - historical_value) / abs(historical_value) * 100
                comparison[key] = {
                    'current': current_value,
                    'historical_average': historical_value,
                    'improvement_percentage': improvement,
                    'trend': 'improved' if improvement > 5 else 'declined' if improvement < -5 else 'stable'
                }
        
        return {
            'performance_comparison': comparison,
            'overall_trend': self._determine_overall_trend(comparison),
            'ranking_percentile': self._calculate_performance_percentile(current_performance)
        }
    
    def _generate_recommendations(self, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des recommandations d'optimisation."""
        recommendations = {
            'algorithm_recommendations': [],
            'parameter_tuning': [],
            'level_design_insights': [],
            'performance_optimizations': []
        }
        
        basic_metrics = metrics.get('basic_metrics', {})
        algorithm_metrics = metrics.get('algorithm_metrics', {})
        
        # Recommandations algorithmiques
        if basic_metrics.get('solve_time', 0) > 10:
            recommendations['algorithm_recommendations'].append({
                'priority': 'high',
                'recommendation': 'Consider using a faster algorithm for this level complexity',
                'rationale': f"Solve time of {basic_metrics.get('solve_time', 0):.2f}s is above optimal threshold"
            })
        
        if basic_metrics.get('pruning_efficiency', 0) < 0.3:
            recommendations['algorithm_recommendations'].append({
                'priority': 'medium',
                'recommendation': 'Improve deadlock detection mechanisms',
                'rationale': f"Pruning efficiency of {basic_metrics.get('pruning_efficiency', 0):.2f} is below recommended threshold"
            })
        
        # Recommandations de paramétrage
        if algorithm_metrics.get('heuristic_effectiveness', 0) < 0.5:
            recommendations['parameter_tuning'].append({
                'priority': 'medium',
                'recommendation': 'Tune heuristic weights for better guidance',
                'rationale': f"Heuristic effectiveness of {algorithm_metrics.get('heuristic_effectiveness', 0):.2f} indicates room for improvement"
            })
        
        # Insights sur le design du niveau
        level_structure = metrics.get('level_structure', {})
        connectivity = level_structure.get('connectivity_analysis', {})
        
        if connectivity.get('connected_components', 1) > 1:
            recommendations['level_design_insights'].append({
                'priority': 'low',
                'insight': 'Level has multiple disconnected areas',
                'impact': 'May affect algorithm efficiency due to isolation'
            })
        
        # Optimisations de performance
        if basic_metrics.get('memory_peak', 0) > 100000:
            recommendations['performance_optimizations'].append({
                'priority': 'medium',
                'optimization': 'Consider memory optimization techniques',
                'benefit': 'Reduced memory usage may improve overall performance'
            })
        
        return recommendations
    
    def _prepare_visualization_data(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les données pour les visualisations."""
        return {
            'performance_radar': self._prepare_performance_radar_data(metrics),
            'algorithm_comparison': self._prepare_algorithm_comparison_data(metrics),
            'movement_heatmap': self._prepare_movement_heatmap_data(metrics),
            'efficiency_timeline': self._prepare_efficiency_timeline_data(metrics),
            'feature_importance': self._prepare_feature_importance_data(metrics)
        }
    
    def _prepare_raw_data_export(self, solution_data, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les données brutes pour export."""
        return {
            'solution_moves': solution_data.moves,
            'complete_metrics': metrics,
            'solver_statistics': {
                'solve_time': solution_data.solve_time,
                'states_explored': solution_data.states_explored,
                'states_generated': solution_data.states_generated,
                'deadlocks_pruned': solution_data.deadlocks_pruned,
                'algorithm_used': solution_data.algorithm_used.value,
                'search_mode': solution_data.search_mode.value,
                'memory_peak': solution_data.memory_peak,
                'heuristic_calls': solution_data.heuristic_calls,
                'macro_moves_used': solution_data.macro_moves_used
            }
        }
    
    # Méthodes d'export
    
    def _export_json_report(self, report: Dict[str, Any], report_id: str):
        """Exporte le rapport au format JSON."""
        json_path = self.output_dir / f"report_{report_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    def _export_html_report(self, report: Dict[str, Any], report_id: str):
        """Exporte le rapport au format HTML."""
        html_path = self.output_dir / f"report_{report_id}.html"
        html_content = self._generate_html_report(report)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_csv_features(self, ml_features: Dict[str, Any], report_id: str):
        """Exporte les features ML au format CSV."""
        csv_path = self.output_dir / f"features_{report_id}.csv"
        
        # Aplatir les features structurées
        flat_features = {}
        for category, features in ml_features.items():
            if isinstance(features, dict) and category != 'feature_metadata':
                for feature_name, value in features.items():
                    flat_features[f"{category}_{feature_name}"] = value
        
        # Écrire le CSV
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("feature_name,value\n")
            for feature_name, value in flat_features.items():
                f.write(f"{feature_name},{value}\n")
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Génère le contenu HTML du rapport."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sokoban AI Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #ecf0f1; border-radius: 5px; min-width: 150px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .metric-label { font-size: 12px; color: #7f8c8d; }
        .rating { padding: 5px 10px; border-radius: 15px; color: white; font-weight: bold; }
        .rating-excellent { background-color: #27ae60; }
        .rating-good { background-color: #f39c12; }
        .rating-poor { background-color: #e74c3c; }
        .recommendation { background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .progress-bar { width: 100%; height: 20px; background-color: #ecf0f1; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background-color: #3498db; transition: width 0.3s ease; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Sokoban AI Performance Report</h1>
            <p>Report ID: {report_id} | Generated: {timestamp}</p>
        </div>
        
        <div class="section">
            <h2>📊 Executive Summary</h2>
            <div class="feature-grid">
                <div class="metric">
                    <div class="metric-value">{overall_score:.1%}</div>
                    <div class="metric-label">Overall Performance</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{solve_time:.2f}s</div>
                    <div class="metric-label">Solve Time</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{moves_count}</div>
                    <div class="metric-label">Moves</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{states_explored:,}</div>
                    <div class="metric-label">States Explored</div>
                </div>
            </div>
            <p><strong>Performance Category:</strong> <span class="rating {performance_category_class}">{performance_category}</span></p>
        </div>
        
        <div class="section">
            <h2>🔍 Algorithm Analysis</h2>
            <p><strong>Algorithm Used:</strong> {algorithm_used}</p>
            <p><strong>Heuristic Effectiveness:</strong> <span class="rating {heuristic_rating_class}">{heuristic_effectiveness:.1%}</span></p>
            <p><strong>Pruning Efficiency:</strong> <span class="rating {pruning_rating_class}">{pruning_efficiency:.1%}</span></p>
        </div>
        
        <div class="section">
            <h2>📈 Performance Metrics</h2>
            <div class="feature-grid">
                <div>
                    <h4>Time Efficiency</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {time_efficiency:.0%}"></div>
                    </div>
                    <p>{time_efficiency:.1%}</p>
                </div>
                <div>
                    <h4>Space Efficiency</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {space_efficiency:.0%}"></div>
                    </div>
                    <p>{space_efficiency:.1%}</p>
                </div>
                <div>
                    <h4>Solution Quality</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {solution_quality:.0%}"></div>
                    </div>
                    <p>{solution_quality:.1%}</p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>💡 Recommendations</h2>
            {recommendations_html}
        </div>
        
        <div class="section">
            <h2>🎯 ML Features Summary</h2>
            <p><strong>Total Features:</strong> {total_features}</p>
            <p><strong>Feature Quality Score:</strong> {feature_quality:.1%}</p>
            <p><strong>Feature Completeness:</strong> {feature_completeness:.1%}</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Extraire les données nécessaires pour le template
        metadata = report.get('metadata', {})
        summary = report.get('executive_summary', {})
        performance = report.get('performance_analysis', {})
        algorithm = report.get('algorithm_analysis', {})
        recommendations = report.get('recommendations', {})
        ml_features = report.get('ml_features', {})
        
        # Préparer les données pour le template
        template_data = {
            'report_id': metadata.get('report_id', 'Unknown'),
            'timestamp': metadata.get('generation_timestamp', 'Unknown'),
            'overall_score': summary.get('overall_performance_score', 0),
            'solve_time': summary.get('key_metrics', {}).get('solve_time', 0),
            'moves_count': summary.get('key_metrics', {}).get('moves_count', 0),
            'states_explored': summary.get('key_metrics', {}).get('states_explored', 0),
            'performance_category': summary.get('performance_category', 'Unknown'),
            'performance_category_class': self._get_rating_class(summary.get('performance_category', 'Unknown')),
            'algorithm_used': summary.get('key_metrics', {}).get('algorithm_used', 'Unknown'),
            'heuristic_effectiveness': algorithm.get('heuristic_performance', {}).get('heuristic_effectiveness', 0),
            'heuristic_rating_class': self._get_rating_class_numeric(algorithm.get('heuristic_performance', {}).get('heuristic_effectiveness', 0)),
            'pruning_efficiency': performance.get('search_efficiency', {}).get('pruning_efficiency', 0),
            'pruning_rating_class': self._get_rating_class_numeric(performance.get('search_efficiency', {}).get('pruning_efficiency', 0)),
            'time_efficiency': report.get('efficiency_analysis', {}).get('time_efficiency', {}).get('score', 0),
            'space_efficiency': report.get('efficiency_analysis', {}).get('space_efficiency', {}).get('score', 0),
            'solution_quality': report.get('efficiency_analysis', {}).get('solution_efficiency', {}).get('score', 0),
            'recommendations_html': self._format_recommendations_html(recommendations),
            'total_features': ml_features.get('feature_metadata', {}).get('total_features', 0),
            'feature_quality': ml_features.get('feature_metadata', {}).get('feature_quality_score', 0),
            'feature_completeness': ml_features.get('feature_metadata', {}).get('feature_completeness', 0)
        }
        
        return html_template.format(**template_data)
    
    # Méthodes utilitaires
    
    def _generate_report_id(self, timestamp: datetime) -> str:
        """Génère un ID unique pour le rapport."""
        return timestamp.strftime("%Y%m%d_%H%M%S")
    
    def _calculate_efficiency_score(self, basic_metrics: Dict[str, Any]) -> float:
        """Calcule un score d'efficacité global."""
        solve_time = basic_metrics.get('solve_time', 1)
        exploration_efficiency = basic_metrics.get('exploration_efficiency', 0)
        pruning_efficiency = basic_metrics.get('pruning_efficiency', 0)
        
        # Normaliser le temps (plus c'est rapide, mieux c'est)
        time_score = 1.0 / (1.0 + solve_time / 10.0)  # 10s comme référence
        
        # Combiner les scores
        return (time_score + exploration_efficiency + pruning_efficiency) / 3
    
    def _categorize_performance(self, efficiency_score: float) -> str:
        """Catégorise la performance."""
        if efficiency_score >= 0.8:
            return "Excellent"
        elif efficiency_score >= 0.6:
            return "Good"
        elif efficiency_score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def _get_rating_class(self, category: str) -> str:
        """Obtient la classe CSS pour une catégorie de performance."""
        if category.lower() in ['excellent', 'good']:
            return 'rating-excellent'
        elif category.lower() in ['fair']:
            return 'rating-good'
        else:
            return 'rating-poor'
    
    def _get_rating_class_numeric(self, value: float) -> str:
        """Obtient la classe CSS pour une valeur numérique."""
        if value >= 0.7:
            return 'rating-excellent'
        elif value >= 0.4:
            return 'rating-good'
        else:
            return 'rating-poor'
    
    def _format_recommendations_html(self, recommendations: Dict[str, Any]) -> str:
        """Formate les recommandations en HTML."""
        html_parts = []
        
        for category, recs in recommendations.items():
            if recs:
                html_parts.append(f"<h4>{category.replace('_', ' ').title()}</h4>")
                for rec in recs:
                    if isinstance(rec, dict):
                        priority = rec.get('priority', 'medium')
                        recommendation = rec.get('recommendation', rec.get('optimization', rec.get('insight', 'No recommendation')))
                        html_parts.append(f'<div class="recommendation"><strong>[{priority.upper()}]</strong> {recommendation}</div>')
        
        return ''.join(html_parts) if html_parts else '<p>No specific recommendations available.</p>'
    
    def get_report_history_summary(self) -> Dict[str, Any]:
        """Obtient un résumé de l'historique des rapports."""
        if not self.report_history:
            return {'message': 'No reports generated yet'}
        
        return {
            'total_reports': len(self.report_history),
            'latest_report_id': self.report_history[-1].get('metadata', {}).get('report_id', 'Unknown'),
            'average_performance': self._calculate_historical_average(),
            'performance_trend': self._analyze_performance_trend()
        }
    
    def export_training_dataset(self, filepath: str):
        """Exporte un dataset d'entraînement à partir de tous les rapports."""
        training_data = []
        
        for report in self.report_history:
            ml_features = report.get('ml_features', {})
            performance = report.get('performance_analysis', {})
            
            if ml_features and performance:
                # Aplatir les features
                features = {}
                for category, cat_features in ml_features.items():
                    if isinstance(cat_features, dict) and category != 'feature_metadata':
                        for feature_name, value in cat_features.items():
                            features[f"{category}_{feature_name}"] = value
                
                # Extraire les targets
                targets = {
                    'solve_time': performance.get('timing_analysis', {}).get('solve_time', 0),
                    'efficiency_score': report.get('executive_summary', {}).get('efficiency_score', 0),
                    'algorithm_effectiveness': report.get('executive_summary', {}).get('algorithm_effectiveness', 0)
                }
                
                training_data.append({
                    'features': features,
                    'targets': targets,
                    'metadata': {
                        'report_id': report.get('metadata', {}).get('report_id'),
                        'algorithm_used': report.get('metadata', {}).get('solution_info', {}).get('algorithm_used')
                    }
                })
        
        # Exporter en JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        return len(training_data)