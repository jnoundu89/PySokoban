"""
Learning Models for Sokoban.

This module provides machine learning models for improving Sokoban level generation
based on player feedback.
"""

import random
import numpy as np
from collections import defaultdict


class DifficultyPredictionModel:
    """
    Model to predict level difficulty based on features.
    
    This model uses a simple statistical approach initially, with the ability
    to upgrade to more sophisticated methods as more data becomes available.
    """
    
    def __init__(self):
        """Initialize the model."""
        self.model = None  # Will be initialized during training
        self.feature_weights = None
        self.bias = 0.5  # Default medium difficulty
        
    def train(self, processed_data):
        """
        Train the model with processed data.
        
        Args:
            processed_data (list): Processed training data.
        """
        if not processed_data:
            return
            
        # Extract features and labels
        features_list = []
        labels = []
        
        for entry in processed_data:
            features_list.append(entry['features'])
            labels.append(entry['label'])
            
        # Convert to numpy arrays for easier processing
        X = np.array(features_list)
        y = np.array(labels)
        
        # Simple linear regression for now
        # This will be replaced with more sophisticated models as needed
        self.feature_weights = self._simple_linear_regression(X, y)
        
    def predict(self, features):
        """
        Predict difficulty for a level.
        
        Args:
            features (list): Level features.
            
        Returns:
            float: Predicted difficulty (0-1).
        """
        if self.feature_weights is None:
            return self.bias  # Default medium difficulty
            
        # Convert features to numpy array
        X = np.array(features)
        
        # Make prediction
        prediction = np.dot(X, self.feature_weights) + self.bias
        
        # Clamp to [0, 1]
        return max(0, min(1, prediction))
    
    def _simple_linear_regression(self, X, y):
        """
        Simple linear regression implementation.
        
        Args:
            X (numpy.ndarray): Features.
            y (numpy.ndarray): Labels.
            
        Returns:
            numpy.ndarray: Feature weights.
        """
        # Add a small value to avoid division by zero
        epsilon = 1e-8
        
        # Calculate mean of X and y
        mean_X = np.mean(X, axis=0)
        mean_y = np.mean(y)
        
        # Calculate weights
        numerator = np.sum((X - mean_X) * (y - mean_y)[:, np.newaxis], axis=0)
        denominator = np.sum((X - mean_X) ** 2, axis=0) + epsilon
        
        weights = numerator / denominator
        
        # Update bias
        self.bias = mean_y - np.sum(weights * mean_X)
        
        return weights


class EngagementPredictionModel:
    """
    Model to predict player engagement with a level.
    
    This model uses a simple statistical approach initially, with the ability
    to upgrade to more sophisticated methods as more data becomes available.
    """
    
    def __init__(self):
        """Initialize the model."""
        self.model = None  # Will be initialized during training
        self.feature_weights = None
        self.bias = 0.5  # Default medium engagement
        
    def train(self, processed_data):
        """
        Train the model with processed data.
        
        Args:
            processed_data (list): Processed training data.
        """
        if not processed_data:
            return
            
        # Extract features and labels
        features_list = []
        labels = []
        
        for entry in processed_data:
            features_list.append(entry['features'])
            labels.append(entry['label'])
            
        # Convert to numpy arrays for easier processing
        X = np.array(features_list)
        y = np.array(labels)
        
        # Simple linear regression for now
        # This will be replaced with more sophisticated models as needed
        self.feature_weights = self._simple_linear_regression(X, y)
        
    def predict(self, features):
        """
        Predict engagement for a level.
        
        Args:
            features (list): Level features.
            
        Returns:
            float: Predicted engagement (0-1).
        """
        if self.feature_weights is None:
            return self.bias  # Default medium engagement
            
        # Convert features to numpy array
        X = np.array(features)
        
        # Make prediction
        prediction = np.dot(X, self.feature_weights) + self.bias
        
        # Clamp to [0, 1]
        return max(0, min(1, prediction))
    
    def _simple_linear_regression(self, X, y):
        """
        Simple linear regression implementation.
        
        Args:
            X (numpy.ndarray): Features.
            y (numpy.ndarray): Labels.
            
        Returns:
            numpy.ndarray: Feature weights.
        """
        # Add a small value to avoid division by zero
        epsilon = 1e-8
        
        # Calculate mean of X and y
        mean_X = np.mean(X, axis=0)
        mean_y = np.mean(y)
        
        # Calculate weights
        numerator = np.sum((X - mean_X) * (y - mean_y)[:, np.newaxis], axis=0)
        denominator = np.sum((X - mean_X) ** 2, axis=0) + epsilon
        
        weights = numerator / denominator
        
        # Update bias
        self.bias = mean_y - np.sum(weights * mean_X)
        
        return weights


class PatternEffectivenessModel:
    """
    Model to evaluate the effectiveness of patterns.
    
    This model tracks the effectiveness of different patterns based on player feedback.
    """
    
    def __init__(self):
        """Initialize the model."""
        self.pattern_scores = {}  # Pattern ID -> effectiveness score
        
    def train(self, processed_data):
        """
        Update pattern effectiveness scores.
        
        Args:
            processed_data (list): Processed training data.
        """
        if not processed_data:
            return
            
        pattern_sums = defaultdict(float)
        pattern_counts = defaultdict(int)
        
        for entry in processed_data:
            pattern_id = entry['pattern_id']
            effectiveness = entry['effectiveness']
            
            pattern_sums[pattern_id] += effectiveness
            pattern_counts[pattern_id] += 1
            
        # Calculate average effectiveness for each pattern
        for pattern_id, count in pattern_counts.items():
            self.pattern_scores[pattern_id] = pattern_sums[pattern_id] / count
            
    def get_pattern_score(self, pattern_id):
        """
        Get the effectiveness score for a pattern.
        
        Args:
            pattern_id: Pattern identifier.
            
        Returns:
            float: Effectiveness score (0-1).
        """
        return self.pattern_scores.get(pattern_id, 0.5)  # Default to neutral


class StylePreferenceModel:
    """
    Model to learn style preferences.
    
    This model uses a simple statistical approach initially, with the ability
    to upgrade to more sophisticated methods as more data becomes available.
    """
    
    def __init__(self):
        """Initialize the model."""
        self.model = None  # Will be initialized during training
        self.feature_weights = None
        self.bias = 0.5  # Default neutral preference
        
    def train(self, processed_data):
        """
        Train the model with processed data.
        
        Args:
            processed_data (list): Processed training data.
        """
        if not processed_data:
            return
            
        # Extract features and preferences
        features_list = []
        preferences = []
        
        for entry in processed_data:
            features_list.append(entry['features'])
            preferences.append(entry['preference'])
            
        # Convert to numpy arrays for easier processing
        X = np.array(features_list)
        y = np.array(preferences)
        
        # Simple linear regression for now
        # This will be replaced with more sophisticated models as needed
        self.feature_weights = self._simple_linear_regression(X, y)
        
    def predict_preference(self, features):
        """
        Predict preference for a style.
        
        Args:
            features (list): Style features.
            
        Returns:
            float: Predicted preference (0-1).
        """
        if self.feature_weights is None:
            return self.bias  # Default neutral preference
            
        # Convert features to numpy array
        X = np.array(features)
        
        # Make prediction
        prediction = np.dot(X, self.feature_weights) + self.bias
        
        # Clamp to [0, 1]
        return max(0, min(1, prediction))
    
    def _simple_linear_regression(self, X, y):
        """
        Simple linear regression implementation.
        
        Args:
            X (numpy.ndarray): Features.
            y (numpy.ndarray): Labels.
            
        Returns:
            numpy.ndarray: Feature weights.
        """
        # Add a small value to avoid division by zero
        epsilon = 1e-8
        
        # Calculate mean of X and y
        mean_X = np.mean(X, axis=0)
        mean_y = np.mean(y)
        
        # Calculate weights
        numerator = np.sum((X - mean_X) * (y - mean_y)[:, np.newaxis], axis=0)
        denominator = np.sum((X - mean_X) ** 2, axis=0) + epsilon
        
        weights = numerator / denominator
        
        # Update bias
        self.bias = mean_y - np.sum(weights * mean_X)
        
        return weights