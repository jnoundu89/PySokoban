"""
Player Feedback Analyzer for Sokoban.

This module provides functionality to analyze player feedback and prepare data
for machine learning models.
"""

import numpy as np


class PlayerFeedbackAnalyzer:
    """
    Player feedback analyzer for Sokoban level generation.
    
    This class analyzes player feedback and prepares data for machine learning models.
    """
    
    def __init__(self):
        """Initialize the player feedback analyzer."""
        pass
        
    def process_data(self, training_data):
        """
        Process training data for model training.
        
        Args:
            training_data (list): Raw training data.
            
        Returns:
            dict: Processed data for different models.
        """
        # Process data for difficulty prediction
        difficulty_data = self._process_for_difficulty(training_data)
        
        # Process data for engagement prediction
        engagement_data = self._process_for_engagement(training_data)
        
        # Process data for pattern effectiveness
        pattern_data = self._process_for_patterns(training_data)
        
        # Process data for style preferences
        style_data = self._process_for_style(training_data)
        
        return {
            'difficulty': difficulty_data,
            'engagement': engagement_data,
            'patterns': pattern_data,
            'style': style_data
        }
    
    def _process_for_difficulty(self, training_data):
        """
        Process data for difficulty prediction.
        
        Args:
            training_data (list): Raw training data.
            
        Returns:
            dict: Processed data for difficulty prediction.
        """
        processed_data = []
        
        for entry in training_data:
            if 'feedback' in entry and 'difficulty_rating' in entry['feedback']:
                # Extract features from metrics
                features = self._extract_difficulty_features(entry['metrics'])
                
                # Extract label from feedback
                label = entry['feedback']['difficulty_rating']
                
                processed_data.append({
                    'features': features,
                    'label': label
                })
        
        return processed_data
    
    def _process_for_engagement(self, training_data):
        """
        Process data for engagement prediction.
        
        Args:
            training_data (list): Raw training data.
            
        Returns:
            dict: Processed data for engagement prediction.
        """
        processed_data = []
        
        for entry in training_data:
            if 'feedback' in entry and 'enjoyment_rating' in entry['feedback']:
                # Extract features from metrics and generation parameters
                features = self._extract_engagement_features(entry['metrics'], entry['generation_params'])
                
                # Extract label from feedback
                label = entry['feedback']['enjoyment_rating']
                
                processed_data.append({
                    'features': features,
                    'label': label
                })
        
        return processed_data
    
    def _process_for_patterns(self, training_data):
        """
        Process data for pattern effectiveness evaluation.
        
        Args:
            training_data (list): Raw training data.
            
        Returns:
            dict: Processed data for pattern effectiveness.
        """
        processed_data = []
        
        for entry in training_data:
            if 'feedback' in entry and 'generation_params' in entry:
                # Check if patterns were used in generation
                if 'patterns' in entry['generation_params']:
                    patterns = entry['generation_params']['patterns']
                    
                    # For each pattern, create an entry
                    for pattern_id, pattern_info in patterns.items():
                        # Extract effectiveness from feedback
                        effectiveness = self._extract_pattern_effectiveness(entry['feedback'], pattern_id)
                        
                        processed_data.append({
                            'pattern_id': pattern_id,
                            'pattern_info': pattern_info,
                            'effectiveness': effectiveness
                        })
        
        return processed_data
    
    def _process_for_style(self, training_data):
        """
        Process data for style preference learning.
        
        Args:
            training_data (list): Raw training data.
            
        Returns:
            dict: Processed data for style preferences.
        """
        processed_data = []
        
        for entry in training_data:
            if 'feedback' in entry and 'generation_params' in entry:
                # Check if style parameters were used in generation
                if 'style' in entry['generation_params']:
                    style_params = entry['generation_params']['style']
                    
                    # Extract features from style parameters
                    features = self._extract_style_features(style_params)
                    
                    # Extract preference from feedback
                    preference = self._extract_style_preference(entry['feedback'])
                    
                    processed_data.append({
                        'features': features,
                        'preference': preference
                    })
        
        return processed_data
    
    def _extract_difficulty_features(self, metrics):
        """
        Extract features for difficulty prediction.
        
        Args:
            metrics (dict): Level metrics.
            
        Returns:
            list: Features for difficulty prediction.
        """
        features = []
        
        # Add basic metrics
        if 'box_count' in metrics:
            features.append(metrics['box_count'])
        else:
            features.append(0)
            
        if 'solution_length' in metrics:
            features.append(metrics['solution_length'])
        else:
            features.append(0)
            
        if 'difficulty' in metrics and 'overall_score' in metrics['difficulty']:
            features.append(metrics['difficulty']['overall_score'])
        else:
            features.append(0)
            
        # Add more features as needed
        
        return features
    
    def _extract_engagement_features(self, metrics, generation_params):
        """
        Extract features for engagement prediction.
        
        Args:
            metrics (dict): Level metrics.
            generation_params (dict): Generation parameters.
            
        Returns:
            list: Features for engagement prediction.
        """
        features = []
        
        # Add basic metrics
        if 'box_count' in metrics:
            features.append(metrics['box_count'])
        else:
            features.append(0)
            
        if 'solution_length' in metrics:
            features.append(metrics['solution_length'])
        else:
            features.append(0)
            
        if 'difficulty' in metrics and 'overall_score' in metrics['difficulty']:
            features.append(metrics['difficulty']['overall_score'])
        else:
            features.append(0)
            
        # Add style parameters
        if 'style' in generation_params:
            style = generation_params['style']
            
            if 'wall_style' in style and 'density' in style['wall_style']:
                features.append(style['wall_style']['density'])
            else:
                features.append(0)
                
            if 'space_style' in style and 'openness' in style['space_style']:
                features.append(style['space_style']['openness'])
            else:
                features.append(0)
        else:
            features.append(0)
            features.append(0)
            
        # Add more features as needed
        
        return features
    
    def _extract_pattern_effectiveness(self, feedback, pattern_id):
        """
        Extract pattern effectiveness from feedback.
        
        Args:
            feedback (dict): Player feedback.
            pattern_id: Pattern identifier.
            
        Returns:
            float: Pattern effectiveness score.
        """
        # For now, use enjoyment rating as a proxy for pattern effectiveness
        if 'enjoyment_rating' in feedback:
            return feedback['enjoyment_rating']
        else:
            return 0.5  # Neutral score
    
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
            
        # Extract object style features
        if 'object_style' in style_params:
            object_style = style_params['object_style']
            
            if 'box_clustering' in object_style:
                features.append(object_style['box_clustering'])
            else:
                features.append(0)
                
            if 'target_clustering' in object_style:
                features.append(object_style['target_clustering'])
            else:
                features.append(0)
        else:
            features.append(0)
            features.append(0)
            
        # Extract symmetry features
        if 'symmetry' in style_params:
            symmetry = style_params['symmetry']
            
            if 'horizontal' in symmetry:
                features.append(symmetry['horizontal'])
            else:
                features.append(0)
                
            if 'vertical' in symmetry:
                features.append(symmetry['vertical'])
            else:
                features.append(0)
                
            if 'radial' in symmetry:
                features.append(symmetry['radial'])
            else:
                features.append(0)
        else:
            features.append(0)
            features.append(0)
            features.append(0)
            
        # Add more features as needed
        
        return features
    
    def _extract_style_preference(self, feedback):
        """
        Extract style preference from feedback.
        
        Args:
            feedback (dict): Player feedback.
            
        Returns:
            float: Style preference score.
        """
        # For now, use enjoyment rating as a proxy for style preference
        if 'enjoyment_rating' in feedback:
            return feedback['enjoyment_rating']
        else:
            return 0.5  # Neutral score