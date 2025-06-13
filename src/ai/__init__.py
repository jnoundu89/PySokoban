"""
Module IA unifié pour PySokoban.

Ce module contient le système IA refactorisé basé sur le SokolutionSolver
avec des capacités ML et d'analyse avancées.
"""

from .unified_ai_controller import UnifiedAIController
from .enhanced_sokolution_solver import EnhancedSokolutionSolver
from .algorithm_selector import AlgorithmSelector, Algorithm
from .ml_metrics_collector import MLMetricsCollector
from .ml_report_generator import MLReportGenerator
from .visual_ai_solver import VisualAISolver

__all__ = [
    'UnifiedAIController',
    'EnhancedSokolutionSolver', 
    'AlgorithmSelector',
    'Algorithm',
    'MLMetricsCollector',
    'MLReportGenerator',
    'VisualAISolver'
]

__version__ = "2.0.0"