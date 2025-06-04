"""
Advanced Procedural Generation System for Sokoban.

This package provides an enhanced procedural generation system for Sokoban levels,
incorporating pattern-based generation, style transfer, and machine learning.
"""

from .advanced_procedural_generator import AdvancedProceduralGenerator, LevelGeneratorCore, LevelValidator
from .pattern_based_generator import PatternBasedGenerator, PatternLibrary, PatternDetector, PatternComposer
from .style_transfer_engine import StyleTransferEngine, StyleAnalyzer, StyleExtractor, StyleApplicator
from .machine_learning_system import MachineLearningSystem
from .data_collection_system import DataCollectionSystem
from .player_feedback_analyzer import PlayerFeedbackAnalyzer
from .learning_models import (
    DifficultyPredictionModel,
    EngagementPredictionModel,
    PatternEffectivenessModel,
    StylePreferenceModel
)

__all__ = [
    'AdvancedProceduralGenerator',
    'LevelGeneratorCore',
    'LevelValidator',
    'PatternBasedGenerator',
    'PatternLibrary',
    'PatternDetector',
    'PatternComposer',
    'StyleTransferEngine',
    'StyleAnalyzer',
    'StyleExtractor',
    'StyleApplicator',
    'MachineLearningSystem',
    'DataCollectionSystem',
    'PlayerFeedbackAnalyzer',
    'DifficultyPredictionModel',
    'EngagementPredictionModel',
    'PatternEffectivenessModel',
    'StylePreferenceModel'
]