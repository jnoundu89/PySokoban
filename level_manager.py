"""
Level Manager module for the Sokoban game.

This module handles loading multiple levels, keeping track of the current level,
and managing navigation between levels. It also provides functionality for
generating random levels using the procedural generator.
"""

import os
from level import Level
from procedural_generator import ProceduralGenerator


class LevelManager:
    """
    Class for managing multiple Sokoban levels.
    
    This class is responsible for loading level files, tracking the current level,
    and providing methods to navigate between levels.
    """
    
    def __init__(self, levels_dir='levels'):
        """
        Initialize the level manager.
        
        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
        """
        self.levels_dir = levels_dir
        self.level_files = []
        self.current_level_index = -1
        self.current_level = None
        self.current_level_metrics = None
        
        self._load_level_files()
        
        if self.level_files:
            self.load_level(0)
    
    def _load_level_files(self):
        """
        Load all level files from the levels directory and subdirectories.
        """
        if not os.path.exists(self.levels_dir):
            print(f"Warning: Levels directory '{self.levels_dir}' not found.")
            return
        
        self.level_files = []
        
        # Get all .txt files in the levels directory and subdirectories
        for root, dirs, files in os.walk(self.levels_dir):
            for file in files:
                if file.endswith('.txt'):
                    self.level_files.append(os.path.join(root, file))
        
        # Sort level files alphabetically
        self.level_files.sort()
    
    def load_level(self, level_index):
        """
        Load a specific level by index.
        
        Args:
            level_index (int): Index of the level to load.
            
        Returns:
            bool: True if the level was loaded successfully, False otherwise.
        """
        if not self.level_files:
            print("No level files found.")
            return False
        
        if level_index < 0 or level_index >= len(self.level_files):
            print(f"Level index {level_index} out of range (0-{len(self.level_files) - 1}).")
            return False
        
        try:
            self.current_level = Level(level_file=self.level_files[level_index])
            self.current_level_index = level_index
            self.current_level_metrics = None  # Reset metrics for loaded levels
            return True
        except Exception as e:
            print(f"Failed to load level {level_index}: {e}")
            return False
    
    def next_level(self):
        """
        Load the next level if available.
        
        Returns:
            bool: True if the next level was loaded successfully, False otherwise.
        """
        if self.current_level_index < len(self.level_files) - 1:
            return self.load_level(self.current_level_index + 1)
        
        print("Already at the last level.")
        return False
    
    def prev_level(self):
        """
        Load the previous level if available.
        
        Returns:
            bool: True if the previous level was loaded successfully, False otherwise.
        """
        if self.current_level_index > 0:
            return self.load_level(self.current_level_index - 1)
        
        print("Already at the first level.")
        return False
    
    def reset_current_level(self):
        """
        Reset the current level to its initial state.
        
        Returns:
            bool: True if the level was reset successfully, False otherwise.
        """
        if self.current_level:
            self.current_level.reset()
            # If reset doesn't work (e.g., no history), reload the level
            if self.current_level.moves != 0:
                return self.load_level(self.current_level_index)
            return True
        
        return False
    
    def current_level_completed(self):
        """
        Check if the current level is completed.
        
        Returns:
            bool: True if the current level is completed, False otherwise.
        """
        return self.current_level and self.current_level.is_completed()
    
    def has_next_level(self):
        """
        Check if there is a next level available.
        
        Returns:
            bool: True if there is a next level, False otherwise.
        """
        return self.current_level_index < len(self.level_files) - 1
    
    def has_prev_level(self):
        """
        Check if there is a previous level available.
        
        Returns:
            bool: True if there is a previous level, False otherwise.
        """
        return self.current_level_index > 0
    
    def get_level_count(self):
        """
        Get the total number of levels.
        
        Returns:
            int: The total number of levels.
        """
        return len(self.level_files)
    
    def get_current_level_number(self):
        """
        Get the current level number (1-based).
        
        Returns:
            int: The current level number (1-based).
        """
        return self.current_level_index + 1
    
    def create_custom_level(self, level_data, filename):
        """
        Create a custom level from string data and save it to a file.
        
        Args:
            level_data (str): Level data as a string.
            filename (str): Name of the file to save the level to.
            
        Returns:
            bool: True if the level was created successfully, False otherwise.
        """
        if not os.path.exists(self.levels_dir):
            os.makedirs(self.levels_dir)
        
        level_path = os.path.join(self.levels_dir, filename)
        
        try:
            with open(level_path, 'w') as file:
                file.write(level_data)
            
            # Reload level files
            self._load_level_files()
            
            # Find the index of the new level
            if level_path in self.level_files:
                new_level_index = self.level_files.index(level_path)
                return self.load_level(new_level_index)
            
            return False
        except Exception as e:
            print(f"Failed to create custom level: {e}")
            return False
    
    def generate_random_level(self, params=None):
        """
        Generate a random level and load it.
        
        Args:
            params (dict, optional): Parameters for the procedural generator.
                                    Defaults to None.
                                    
        Returns:
            bool: True if the level was generated successfully, False otherwise.
        """
        try:
            # Create a generator with default or provided parameters
            generator = ProceduralGenerator(**(params or {}))
            
            # Generate a level
            level = generator.generate_level()
            
            # Set as current level
            self.current_level = level
            self.current_level_index = -1  # Indicate this is not from a file
            
            # Store metrics for UI access
            self.current_level_metrics = generator.level_metrics
            
            print(f"Generated level with {len(level.boxes)} boxes after {generator.attempts} attempts.")
            print(f"Solution length: {len(generator.solver.get_solution())} moves.")
            
            if generator.level_metrics:
                print(f"Difficulty score: {generator.level_metrics['difficulty']['overall_score']:.1f}/100")
            
            return True
        except Exception as e:
            print(f"Failed to generate random level: {e}")
            return False
    
    def save_generated_level(self, filename):
        """
        Save the current generated level to a file.
        
        Args:
            filename (str): Name of the file to save the level to.
            
        Returns:
            bool: True if the level was saved successfully, False otherwise.
        """
        if self.current_level:
            return self.create_custom_level(
                self.current_level.get_state_string(),
                filename
            )
        return False