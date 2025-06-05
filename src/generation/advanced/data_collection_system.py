"""
Data Collection System for Sokoban.

This module provides functionality to collect and store player data and feedback
for machine learning purposes.
"""

import time
import json
import os
import random


class DataCollectionSystem:
    """
    Data collection system for Sokoban level generation.
    
    This class handles collecting and storing player data and feedback.
    """
    
    def __init__(self, data_dir="data"):
        """
        Initialize the data collection system.
        
        Args:
            data_dir (str, optional): Directory to store data. Defaults to "data".
        """
        self.data_dir = data_dir
        self.generations_db = {}  # Store generated levels and their metrics
        self.feedback_db = {}     # Store player feedback
        self.min_data_threshold = 50  # Minimum data points needed for learning
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data if available
        self._load_data()
        
    def record_generation(self, level, metrics, generation_params):
        """
        Record a generated level.
        
        Args:
            level (Level): The generated level.
            metrics (dict): Metrics for the level.
            generation_params (dict): Parameters used for generation.
        """
        level_id = self._generate_level_id(level)
        self.generations_db[level_id] = {
            'level_string': level.get_state_string(),
            'metrics': metrics,
            'generation_params': generation_params,
            'timestamp': time.time()
        }
        
        # Save to disk
        self._save_data()
        
    def record_feedback(self, level_id, feedback_data):
        """
        Record player feedback for a level.
        
        Args:
            level_id: Identifier for the level.
            feedback_data (dict): Player feedback data.
        """
        if level_id not in self.feedback_db:
            self.feedback_db[level_id] = []
            
        self.feedback_db[level_id].append({
            'feedback': feedback_data,
            'timestamp': time.time()
        })
        
        # Save to disk
        self._save_data()
        
    def has_sufficient_data(self):
        """
        Check if we have enough data for learning.
        
        Returns:
            bool: True if we have enough data, False otherwise.
        """
        return len(self.feedback_db) >= self.min_data_threshold
        
    def get_training_data(self):
        """
        Get data for training models.
        
        Returns:
            list: Training data.
        """
        training_data = []
        
        for level_id, generation_data in self.generations_db.items():
            if level_id in self.feedback_db:
                # Combine generation data with feedback
                for feedback_entry in self.feedback_db[level_id]:
                    training_data.append({
                        'level_string': generation_data['level_string'],
                        'metrics': generation_data['metrics'],
                        'generation_params': generation_data['generation_params'],
                        'feedback': feedback_entry['feedback']
                    })
                    
        return training_data
    
    def _generate_level_id(self, level):
        """
        Generate a unique ID for a level.
        
        Args:
            level (Level): The level to generate an ID for.
            
        Returns:
            str: A unique ID.
        """
        # Use the level string as the ID
        return level.get_state_string()
    
    def _save_data(self):
        """Save data to disk."""
        try:
            # Save generations
            with open(os.path.join(self.data_dir, 'generations.json'), 'w') as f:
                json.dump(self.generations_db, f)
            
            # Save feedback
            with open(os.path.join(self.data_dir, 'feedback.json'), 'w') as f:
                json.dump(self.feedback_db, f)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def _load_data(self):
        """Load data from disk."""
        try:
            # Load generations
            if os.path.exists(os.path.join(self.data_dir, 'generations.json')):
                with open(os.path.join(self.data_dir, 'generations.json'), 'r') as f:
                    self.generations_db = json.load(f)
            
            # Load feedback
            if os.path.exists(os.path.join(self.data_dir, 'feedback.json')):
                with open(os.path.join(self.data_dir, 'feedback.json'), 'r') as f:
                    self.feedback_db = json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")