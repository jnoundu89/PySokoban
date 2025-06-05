"""
Machine Learning System for Sokoban.

This module provides functionality to collect player data, analyze feedback,
and learn to improve level generation over time.
"""

import time
import random
import copy
import os

from .data_collection_system import DataCollectionSystem
from .player_feedback_analyzer import PlayerFeedbackAnalyzer
from .learning_models import (
    DifficultyPredictionModel,
    EngagementPredictionModel,
    PatternEffectivenessModel,
    StylePreferenceModel
)


class MachineLearningSystem:
    """
    Machine learning system for Sokoban level generation.
    
    This class handles collecting player data, analyzing feedback,
    and learning to improve generation over time.
    """
    
    def __init__(self, config=None):
        """
        Initialize the machine learning system.
        
        Args:
            config (dict, optional): Configuration for the ML system.
                                    Defaults to None, which uses default configuration.
        """
        self.config = config or {}
        self.data_collector = DataCollectionSystem()
        self.feedback_analyzer = PlayerFeedbackAnalyzer()
        self.models = self._initialize_models()
        
    def get_generation_parameters(self, params):
        """
        Get generation parameters based on learning.
        
        Args:
            params (dict): Base parameters for generation.
            
        Returns:
            dict: Adjusted parameters based on learning.
        """
        # If we have enough data, use the models to adjust parameters
        if self.data_collector.has_sufficient_data():
            return self._generate_parameters_from_models(params)
        else:
            # Otherwise, use statistical defaults or random exploration
            return self._generate_exploration_parameters(params)
            
    def record_generation(self, level, metrics, generation_params):
        """
        Record a generated level for learning.
        
        Args:
            level (Level): The generated level.
            metrics (dict): Metrics for the level.
            generation_params (dict): Parameters used for generation.
        """
        self.data_collector.record_generation(level, metrics, generation_params)
        
    def record_player_feedback(self, level_id, feedback_data):
        """
        Record player feedback for a level.
        
        Args:
            level_id: Identifier for the level.
            feedback_data (dict): Player feedback data.
        """
        self.data_collector.record_feedback(level_id, feedback_data)
        
        # Analyze new feedback and update models if needed
        if self.config.get('continuous_learning', True):
            self._update_models_with_feedback(level_id, feedback_data)
            
    def train_models(self):
        """Train or update the machine learning models."""
        # Get all collected data
        training_data = self.data_collector.get_training_data()
        
        # Analyze feedback to create training examples
        processed_data = self.feedback_analyzer.process_data(training_data)
        
        # Train each model
        for model_name, model in self.models.items():
            model.train(processed_data.get(model_name, []))
            
    def _initialize_models(self):
        """
        Initialize the machine learning models.
        
        Returns:
            dict: Dictionary of models.
        """
        models = {
            'difficulty': DifficultyPredictionModel(),
            'engagement': EngagementPredictionModel(),
            'patterns': PatternEffectivenessModel(),
            'style': StylePreferenceModel()
        }
        
        return models
    
    def _generate_parameters_from_models(self, params):
        """
        Generate parameters based on model predictions.
        
        Args:
            params (dict): Base parameters.
            
        Returns:
            dict: Adjusted parameters.
        """
        adjusted_params = {}
        
        # Adjust difficulty parameters
        difficulty_features = self._extract_difficulty_features(params)
        target_difficulty = params.get('target_difficulty', 0.5)
        
        # Predict current difficulty
        predicted_difficulty = self.models['difficulty'].predict(difficulty_features)
        
        # Adjust parameters to move towards target difficulty
        difficulty_adjustment = target_difficulty - predicted_difficulty
        adjusted_params['difficulty_adjustment'] = difficulty_adjustment
        
        # Adjust pattern selection based on pattern effectiveness
        if 'patterns' in params:
            pattern_scores = {}
            for pattern_id in params['patterns']:
                pattern_scores[pattern_id] = self.models['patterns'].get_pattern_score(pattern_id)
                
            adjusted_params['pattern_scores'] = pattern_scores
        
        # Adjust style parameters based on style preferences
        if 'style' in params:
            style_features = self._extract_style_features(params['style'])
            style_preference = self.models['style'].predict_preference(style_features)
            
            # If preference is low, adjust style parameters
            if style_preference < 0.5:
                adjusted_params['style_adjustment'] = 0.5 - style_preference
        
        return adjusted_params
    
    def _generate_exploration_parameters(self, params):
        """
        Generate exploration parameters when insufficient data is available.
        
        Args:
            params (dict): Base parameters.
            
        Returns:
            dict: Exploration parameters.
        """
        exploration_rate = self.config.get('exploration_rate', 0.2)
        
        # Add random variations to parameters for exploration
        exploration_params = {}
        
        # Randomly adjust difficulty
        exploration_params['difficulty_adjustment'] = (random.random() - 0.5) * exploration_rate
        
        # Randomly adjust pattern selection
        if 'patterns' in params:
            pattern_scores = {}
            for pattern_id in params['patterns']:
                pattern_scores[pattern_id] = 0.5 + (random.random() - 0.5) * exploration_rate
                
            exploration_params['pattern_scores'] = pattern_scores
        
        # Randomly adjust style parameters
        exploration_params['style_adjustment'] = (random.random() - 0.5) * exploration_rate
        
        return exploration_params
    
    def _update_models_with_feedback(self, level_id, feedback_data):
        """
        Update models with new feedback.
        
        Args:
            level_id: Identifier for the level.
            feedback_data (dict): Player feedback data.
        """
        # Get the level data
        level_data = None
        for id, data in self.data_collector.generations_db.items():
            if id == level_id:
                level_data = data
                break
                
        if level_data is None:
            return
            
        # Create a mini training dataset with just this feedback
        mini_training_data = [{
            'level_string': level_data['level_string'],
            'metrics': level_data['metrics'],
            'generation_params': level_data['generation_params'],
            'feedback': feedback_data
        }]
        
        # Process the data
        processed_data = self.feedback_analyzer.process_data(mini_training_data)
        
        # Update each model
        for model_name, model in self.models.items():
            model.train(processed_data.get(model_name, []))
    
    def _extract_difficulty_features(self, params):
        """
        Extract features for difficulty prediction from parameters.
        
        Args:
            params (dict): Generation parameters.
            
        Returns:
            list: Difficulty features.
        """
        features = []
        
        # Add basic parameters
        features.append(params.get('min_boxes', 1))
        features.append(params.get('max_boxes', 5))
        features.append(params.get('wall_density', 0.2))
        
        # Add more features as needed
        
        return features
    
    def _extract_style_features(self, style_params):
        """
        Extract features from style parameters.
        
        Args:
            style_params (dict): Style parameters.
            
        Returns:
            list: Style features.
        """
        features = []
        
        # Extract wall style features
        if 'wall_style' in style_params:
            wall_style = style_params['wall_style']
            
            if 'density' in wall_style:
                features.append(wall_style['density'])
            else:
                features.append(0)
        else:
            features.append(0)
            
        # Extract space style features
        if 'space_style' in style_params:
            space_style = style_params['space_style']
            
            if 'openness' in space_style:
                features.append(space_style['openness'])
            else:
                features.append(0)
        else:
            features.append(0)
            
        # Add more features as needed
        
        return features