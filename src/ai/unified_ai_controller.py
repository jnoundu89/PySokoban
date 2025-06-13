"""
Contrôleur IA unifié pour PySokoban.

Ce module fournit l'interface principale pour interagir avec le système IA
refactorisé, incluant la sélection automatique d'algorithme, la collection
de métriques ML, et l'intégration avec l'interface graphique.
"""

import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass

from .algorithm_selector import AlgorithmSelector, Algorithm
from .enhanced_sokolution_solver import EnhancedSokolutionSolver, SolutionData, SearchMode
from .ml_metrics_collector import MLMetricsCollector
from .ml_report_generator import MLReportGenerator


@dataclass
class SolveRequest:
    """Requête de résolution avec paramètres."""
    level: Any
    algorithm: Optional[Algorithm] = None  # Si None, sélection automatique
    mode: SearchMode = SearchMode.FORWARD
    max_states: int = 1000000
    time_limit: float = 120.0
    collect_ml_metrics: bool = True
    generate_report: bool = False


@dataclass
class SolveResult:
    """Résultat complet d'une résolution."""
    success: bool
    solution_data: Optional[SolutionData]
    ml_metrics: Optional[Dict[str, Any]]
    ml_report: Optional[Dict[str, Any]]
    algorithm_recommendation: Optional[Dict[str, Any]]
    error_message: Optional[str] = None


class UnifiedAIController:
    """
    Contrôleur principal du système IA unifié.
    
    Cette classe orchestre tous les composants du système IA :
    - Sélection automatique d'algorithme
    - Résolution avec le SokolutionSolver
    - Collection de métriques ML
    - Génération de rapports
    - Interface avec le système de rendu
    """
    
    def __init__(self):
        self.algorithm_selector = AlgorithmSelector()
        self.ml_metrics_collector = None  # Sera initialisé à la demande
        self.ml_report_generator = None   # Sera initialisé à la demande
        
        # Historique des résolutions
        self.solve_history: List[SolveResult] = []
        
        # Statistiques globales
        self.total_solves = 0
        self.successful_solves = 0
        self.failed_solves = 0
        
        # État actuel
        self.current_solver: Optional[EnhancedSokolutionSolver] = None
        self.is_solving = False
        self.current_solution = None
    
    def solve_level(self, request: SolveRequest,
                   progress_callback: Optional[Callable[[str], None]] = None) -> SolveResult:
        """
        Résout un niveau avec les paramètres spécifiés.
        
        Args:
            request: Paramètres de la requête de résolution
            progress_callback: Callback optionnel pour les mises à jour de progression
            
        Returns:
            SolveResult: Résultat complet de la résolution
        """
        if self.is_solving:
            return SolveResult(
                success=False,
                solution_data=None,
                ml_metrics=None,
                ml_report=None,
                algorithm_recommendation=None,
                error_message="Une résolution est déjà en cours"
            )
        
        self.is_solving = True
        self.total_solves += 1
        
        try:
            # 1. Sélection d'algorithme (automatique ou manuel)
            algorithm_recommendation = None
            if request.algorithm is None:
                algorithm_recommendation = self.algorithm_selector.get_algorithm_recommendation(request.level)
                selected_algorithm = algorithm_recommendation['recommended_algorithm']
                
                if progress_callback:
                    complexity_score = algorithm_recommendation['complexity_score']
                    category = algorithm_recommendation['complexity_category']
                    progress_callback(f"🎯 Niveau {category} (score: {complexity_score:.1f}) → Algorithme sélectionné: {selected_algorithm.value}")
            else:
                selected_algorithm = request.algorithm
                
                if progress_callback:
                    progress_callback(f"🔧 Utilisation de l'algorithme spécifié: {selected_algorithm.value}")
            
            # 2. Initialisation du solver
            self.current_solver = EnhancedSokolutionSolver(
                level=request.level,
                max_states=request.max_states,
                time_limit=request.time_limit
            )
            
            if progress_callback:
                solver_info = f"Limites: {request.max_states:,} états max, {request.time_limit:.0f}s timeout"
                progress_callback(f"⚙️ Initialisation solver {selected_algorithm.value} - {solver_info}")
            
            # 3. Résolution avec fallback pour FESS
            if progress_callback:
                progress_callback(f"🚀 Démarrage de l'analyse algorithmique...")
            
            solution_data = self._solve_with_fallback(
                selected_algorithm=selected_algorithm,
                request=request,
                progress_callback=progress_callback
            )
            
            # 4. Collection de métriques ML (si demandée)
            ml_metrics = None
            if request.collect_ml_metrics and solution_data:
                if progress_callback:
                    progress_callback("Collection des métriques ML...")
                
                if self.ml_metrics_collector is None:
                    self._initialize_ml_components()
                
                ml_metrics = self.ml_metrics_collector.collect_solving_metrics(
                    level=request.level,
                    solution_data=solution_data,
                    solver_stats=self.current_solver.get_comprehensive_statistics()
                )
            
            # 5. Génération de rapport (si demandée)
            ml_report = None
            if request.generate_report and solution_data and ml_metrics:
                if progress_callback:
                    progress_callback("Génération du rapport ML...")
                
                if self.ml_report_generator is None:
                    self._initialize_ml_components()
                
                ml_report = self.ml_report_generator.generate_comprehensive_report(
                    level=request.level,
                    solution_data=solution_data,
                    metrics=ml_metrics
                )
            
            # 6. Préparation du résultat
            success = solution_data is not None
            if success:
                self.successful_solves += 1
                self.current_solution = solution_data.moves
                
                if progress_callback:
                    moves_count = len(solution_data.moves)
                    solve_time = solution_data.solve_time
                    states_explored = solution_data.states_explored
                    progress_callback(f"✅ Solution trouvée: {moves_count} coups, {states_explored} états explorés en {solve_time:.2f}s")
            else:
                self.failed_solves += 1
                self.current_solution = None
                
                if progress_callback:
                    progress_callback("❌ Aucune solution trouvée dans les limites spécifiées")
            
            result = SolveResult(
                success=success,
                solution_data=solution_data,
                ml_metrics=ml_metrics,
                ml_report=ml_report,
                algorithm_recommendation=algorithm_recommendation
            )
            
            # Ajouter à l'historique
            self.solve_history.append(result)
            
            return result
            
        except Exception as e:
            self.failed_solves += 1
            error_message = f"Erreur lors de la résolution: {str(e)}"
            
            if progress_callback:
                progress_callback(f"❌ {error_message}")
            
            return SolveResult(
                success=False,
                solution_data=None,
                ml_metrics=None,
                ml_report=None,
                algorithm_recommendation=None,
                error_message=error_message
            )
        
        finally:
            self.is_solving = False
    
    def _solve_with_fallback(self, selected_algorithm: Algorithm, request: SolveRequest,
                           progress_callback: Optional[Callable[[str], None]] = None) -> Optional[SolutionData]:
        """
        Résout avec fallback automatique si FESS échoue.
        
        Args:
            selected_algorithm: Algorithme principal à utiliser
            request: Requête de résolution
            progress_callback: Callback pour les mises à jour
            
        Returns:
            SolutionData si solution trouvée, None sinon
        """
        # Essayer l'algorithme principal
        solution_data = self.current_solver.solve(
            algorithm=selected_algorithm,
            mode=request.mode,
            progress_callback=progress_callback
        )
        
        # Si FESS échoue, essayer l'algorithme de fallback
        if solution_data is None and selected_algorithm == Algorithm.FESS:
            if progress_callback:
                progress_callback("🔄 FESS n'a pas trouvé de solution, passage au fallback...")
            
            # Obtenir l'algorithme de fallback
            fallback_algorithm = self.algorithm_selector.get_fallback_algorithm(request.level)
            
            if progress_callback:
                progress_callback(f"🔧 Tentative avec algorithme de fallback: {fallback_algorithm.value}")
            
            # Réinitialiser le solver pour le fallback
            self.current_solver = EnhancedSokolutionSolver(
                level=request.level,
                max_states=request.max_states,
                time_limit=request.time_limit
            )
            
            # Essayer avec l'algorithme de fallback
            solution_data = self.current_solver.solve(
                algorithm=fallback_algorithm,
                mode=request.mode,
                progress_callback=progress_callback
            )
            
            if solution_data and progress_callback:
                progress_callback(f"✅ Solution trouvée avec fallback {fallback_algorithm.value}!")
        
        return solution_data
    
    def solve_level_auto(self, level, progress_callback: Optional[Callable[[str], None]] = None,
                        collect_ml_metrics: bool = True, generate_report: bool = False) -> SolveResult:
        """
        Résout un niveau avec la configuration automatique recommandée.
        
        Args:
            level: Niveau à résoudre
            progress_callback: Callback optionnel pour les mises à jour
            collect_ml_metrics: Si collecter les métriques ML
            generate_report: Si générer un rapport ML
            
        Returns:
            SolveResult: Résultat de la résolution
        """
        request = SolveRequest(
            level=level,
            algorithm=None,  # Sélection automatique
            collect_ml_metrics=collect_ml_metrics,
            generate_report=generate_report
        )
        
        return self.solve_level(request, progress_callback)
    
    def solve_level_with_algorithm(self, level, algorithm: Algorithm,
                                  progress_callback: Optional[Callable[[str], None]] = None) -> SolveResult:
        """
        Résout un niveau avec un algorithme spécifique.
        
        Args:
            level: Niveau à résoudre
            algorithm: Algorithme à utiliser
            progress_callback: Callback optionnel pour les mises à jour
            
        Returns:
            SolveResult: Résultat de la résolution
        """
        request = SolveRequest(
            level=level,
            algorithm=algorithm,
            collect_ml_metrics=True
        )
        
        return self.solve_level(request, progress_callback)
    
    def get_algorithm_recommendation(self, level) -> Dict[str, Any]:
        """
        Obtient une recommandation d'algorithme pour un niveau.
        
        Args:
            level: Niveau à analyser
            
        Returns:
            Dict: Recommandation d'algorithme détaillée
        """
        return self.algorithm_selector.get_algorithm_recommendation(level)
    
    def get_current_solution(self) -> Optional[List[str]]:
        """
        Obtient la solution actuellement disponible.
        
        Returns:
            List[str]: Liste des mouvements, ou None si pas de solution
        """
        return self.current_solution
    
    def get_solve_statistics(self) -> Dict[str, Any]:
        """
        Obtient les statistiques globales de résolution.
        
        Returns:
            Dict: Statistiques détaillées
        """
        success_rate = 0.0
        if self.total_solves > 0:
            success_rate = (self.successful_solves / self.total_solves) * 100
        
        # Statistiques par algorithme
        algorithm_stats = self.algorithm_selector.get_selection_statistics()
        
        # Statistiques de performance moyennes
        avg_stats = self._calculate_average_performance_stats()
        
        return {
            'global_statistics': {
                'total_solves': self.total_solves,
                'successful_solves': self.successful_solves,
                'failed_solves': self.failed_solves,
                'success_rate': success_rate
            },
            'algorithm_selection': algorithm_stats,
            'performance_averages': avg_stats,
            'recent_history_count': len(self.solve_history[-10:])  # 10 dernières résolutions
        }
    
    def _calculate_average_performance_stats(self) -> Dict[str, float]:
        """Calcule les statistiques de performance moyennes."""
        successful_solves = [r for r in self.solve_history if r.success and r.solution_data]
        
        if not successful_solves:
            return {
                'avg_solve_time': 0.0,
                'avg_moves_count': 0.0,
                'avg_states_explored': 0.0,
                'avg_states_generated': 0.0
            }
        
        total_time = sum(r.solution_data.solve_time for r in successful_solves)
        total_moves = sum(len(r.solution_data.moves) for r in successful_solves)
        total_states_explored = sum(r.solution_data.states_explored for r in successful_solves)
        total_states_generated = sum(r.solution_data.states_generated for r in successful_solves)
        
        count = len(successful_solves)
        
        return {
            'avg_solve_time': total_time / count,
            'avg_moves_count': total_moves / count,
            'avg_states_explored': total_states_explored / count,
            'avg_states_generated': total_states_generated / count
        }
    
    def get_recent_solve_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Obtient l'historique récent des résolutions.
        
        Args:
            count: Nombre de résolutions récentes à retourner
            
        Returns:
            List[Dict]: Historique des résolutions récentes
        """
        recent_history = []
        
        for result in self.solve_history[-count:]:
            history_item = {
                'success': result.success,
                'error_message': result.error_message
            }
            
            if result.solution_data:
                history_item.update({
                    'algorithm_used': result.solution_data.algorithm_used.value,
                    'moves_count': len(result.solution_data.moves),
                    'solve_time': result.solution_data.solve_time,
                    'states_explored': result.solution_data.states_explored
                })
            
            if result.algorithm_recommendation:
                history_item['complexity_score'] = result.algorithm_recommendation['complexity_score']
                history_item['complexity_category'] = result.algorithm_recommendation['complexity_category']
            
            recent_history.append(history_item)
        
        return recent_history
    
    def export_solve_history(self, filepath: str):
        """
        Exporte l'historique complet des résolutions.
        
        Args:
            filepath: Chemin du fichier d'export
        """
        import json
        from datetime import datetime
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'statistics': self.get_solve_statistics(),
            'solve_history': []
        }
        
        for i, result in enumerate(self.solve_history):
            history_item = {
                'solve_id': i,
                'success': result.success,
                'error_message': result.error_message
            }
            
            if result.solution_data:
                history_item['solution_data'] = {
                    'moves': result.solution_data.moves,
                    'solve_time': result.solution_data.solve_time,
                    'states_explored': result.solution_data.states_explored,
                    'states_generated': result.solution_data.states_generated,
                    'deadlocks_pruned': result.solution_data.deadlocks_pruned,
                    'algorithm_used': result.solution_data.algorithm_used.value,
                    'search_mode': result.solution_data.search_mode.value,
                    'memory_peak': result.solution_data.memory_peak,
                    'heuristic_calls': result.solution_data.heuristic_calls,
                    'macro_moves_used': result.solution_data.macro_moves_used
                }
            
            if result.ml_metrics:
                history_item['ml_metrics'] = result.ml_metrics
            
            if result.algorithm_recommendation:
                history_item['algorithm_recommendation'] = result.algorithm_recommendation
            
            export_data['solve_history'].append(history_item)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def clear_history(self):
        """Efface l'historique des résolutions."""
        self.solve_history.clear()
        self.algorithm_selector.reset_statistics()
    
    def stop_current_solve(self):
        """Arrête la résolution actuelle."""
        self.is_solving = False
        if self.current_solver:
            # Le solver vérifiera _within_limits() et s'arrêtera
            pass
    
    def _initialize_ml_components(self):
        """Initialise les composants ML à la demande."""
        if self.ml_metrics_collector is None:
            from .ml_metrics_collector import MLMetricsCollector
            self.ml_metrics_collector = MLMetricsCollector()
        
        if self.ml_report_generator is None:
            from .ml_report_generator import MLReportGenerator
            self.ml_report_generator = MLReportGenerator()
    
    def benchmark_algorithms(self, level, algorithms: Optional[List[Algorithm]] = None,
                           progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Compare les performances de différents algorithmes sur un niveau.
        
        Args:
            level: Niveau à tester
            algorithms: Liste d'algorithmes à tester (par défaut: tous)
            progress_callback: Callback pour les mises à jour
            
        Returns:
            Dict: Résultats du benchmark
        """
        if algorithms is None:
            algorithms = [Algorithm.FESS, Algorithm.BFS, Algorithm.ASTAR, Algorithm.GREEDY, Algorithm.IDA_STAR]
        
        benchmark_results = {
            'level_info': {
                'width': level.width,
                'height': level.height,
                'boxes_count': len(level.boxes),
                'targets_count': len(level.targets)
            },
            'algorithm_results': {},
            'best_algorithm': None,
            'fastest_algorithm': None
        }
        
        if progress_callback:
            progress_callback(f"Démarrage du benchmark sur {len(algorithms)} algorithmes...")
        
        best_moves = float('inf')
        fastest_time = float('inf')
        
        for algorithm in algorithms:
            if progress_callback:
                progress_callback(f"Test de l'algorithme {algorithm.value}...")
            
            request = SolveRequest(
                level=level,
                algorithm=algorithm,
                time_limit=60.0,  # Limite plus courte pour le benchmark
                collect_ml_metrics=False
            )
            
            result = self.solve_level(request)
            
            if result.success and result.solution_data:
                moves_count = len(result.solution_data.moves)
                solve_time = result.solution_data.solve_time
                
                benchmark_results['algorithm_results'][algorithm.value] = {
                    'success': True,
                    'moves_count': moves_count,
                    'solve_time': solve_time,
                    'states_explored': result.solution_data.states_explored,
                    'states_generated': result.solution_data.states_generated,
                    'deadlocks_pruned': result.solution_data.deadlocks_pruned
                }
                
                if moves_count < best_moves:
                    best_moves = moves_count
                    benchmark_results['best_algorithm'] = algorithm.value
                
                if solve_time < fastest_time:
                    fastest_time = solve_time
                    benchmark_results['fastest_algorithm'] = algorithm.value
            else:
                benchmark_results['algorithm_results'][algorithm.value] = {
                    'success': False,
                    'error': result.error_message or "Aucune solution trouvée"
                }
        
        if progress_callback:
            if benchmark_results['best_algorithm']:
                progress_callback(f"✅ Benchmark terminé. Meilleur: {benchmark_results['best_algorithm']} ({best_moves} coups)")
            else:
                progress_callback("❌ Aucun algorithme n'a trouvé de solution")
        
        return benchmark_results