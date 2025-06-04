"""
Advanced Procedural Generator for Sokoban.

This module provides the main orchestration for the advanced procedural generation system,
integrating pattern-based generation, style transfer, and machine learning.
"""

import time
import copy
from level import Level
from level_solver import SokobanSolver
from level_metrics import LevelMetrics
from procedural_generator import ProceduralGenerator

# Import advanced generation components
from .pattern_based_generator import PatternBasedGenerator
from .style_transfer_engine import StyleTransferEngine
from .machine_learning_system import MachineLearningSystem


class AdvancedProceduralGenerator:
    """
    Advanced procedural generator for Sokoban levels.
    
    This class orchestrates the generation of Sokoban levels using three integrated approaches:
    1. Pattern-based generation
    2. Style transfer
    3. Machine learning
    """
    
    def __init__(self, config=None):
        """
        Initialize the advanced procedural generator.
        
        Args:
            config (dict, optional): Configuration parameters for the generator.
                                    Defaults to None, which uses default configuration.
        """
        # Load default configuration if none provided
        self.config = config or self._default_config()
        
        # Initialize sub-systems
        self.pattern_generator = PatternBasedGenerator(self.config.get('pattern', {}))
        self.style_transfer = StyleTransferEngine(self.config.get('style', {}))
        self.ml_system = MachineLearningSystem(self.config.get('ml', {}))
        
        # Initialize core components
        self.level_generator = LevelGeneratorCore()
        self.validator = LevelValidator()
        self.solver = SokobanSolver()
        self.metrics = LevelMetrics()
        
        # Statistics and state
        self.generation_stats = {}
        
    def generate_level(self, parameters=None):
        """
        Generate a level using the integrated approach.
        
        Args:
            parameters (dict, optional): Specific parameters for this generation.
                                        Defaults to None, which uses default parameters.
            
        Returns:
            Level: A generated level that meets the criteria.
            
        Raises:
            RuntimeError: If a suitable level could not be generated within constraints.
        """
        # Merge parameters with config
        params = self._merge_parameters(parameters)
        
        # Get pattern templates from pattern-based generator
        patterns = self.pattern_generator.get_patterns(params)
        
        # Get style parameters from style transfer engine
        style_params = self.style_transfer.get_style_parameters(params)
        
        # Get learning-based adjustments from ML system
        ml_adjustments = self.ml_system.get_generation_parameters(params)
        
        # Combine all inputs for the core generator
        generation_params = self._combine_parameters(patterns, style_params, ml_adjustments)
        
        # Generate level with integrated parameters
        level = self._generate_with_parameters(generation_params)
        
        # Calculate metrics for feedback
        metrics = self.metrics.calculate_metrics(level)
        
        # Record generation for learning
        self.ml_system.record_generation(level, metrics, generation_params)
        
        return level
        
    def _generate_with_parameters(self, params):
        """
        Generate a level using the combined parameters.
        
        Args:
            params (dict): Combined parameters from all subsystems.
            
        Returns:
            Level: A generated level.
            
        Raises:
            RuntimeError: If a suitable level could not be generated within constraints.
        """
        max_attempts = params.get('max_attempts', 100)
        timeout = params.get('timeout', 30)
        
        start_time = time.time()
        attempts = 0
        
        while attempts < max_attempts and time.time() - start_time < timeout:
            attempts += 1
            
            # Generate candidate level
            level = self.level_generator.generate(params)
            
            # Validate level
            if not self.validator.validate(level):
                continue
                
            # Check solvability
            if self.solver.is_solvable(level):
                # Record statistics
                self.generation_stats = {
                    'attempts': attempts,
                    'time': time.time() - start_time,
                    'solution': self.solver.get_solution()
                }
                return level
                
        # If we get here, we couldn't generate a suitable level
        raise RuntimeError(f"Could not generate a suitable level after {attempts} attempts and {time.time() - start_time:.2f} seconds")
    
    def _merge_parameters(self, parameters):
        """
        Merge provided parameters with default configuration.
        
        Args:
            parameters (dict, optional): Parameters to merge.
            
        Returns:
            dict: Merged parameters.
        """
        if parameters is None:
            return copy.deepcopy(self.config.get('default_params', {}))
            
        merged = copy.deepcopy(self.config.get('default_params', {}))
        merged.update(parameters)
        return merged
    
    def _combine_parameters(self, patterns, style_params, ml_adjustments):
        """
        Combine parameters from all three subsystems.
        
        Args:
            patterns (dict): Pattern-based generation parameters.
            style_params (dict): Style transfer parameters.
            ml_adjustments (dict): Machine learning adjustments.
            
        Returns:
            dict: Combined parameters for level generation.
        """
        combined = {}
        
        # Add pattern parameters
        combined['patterns'] = patterns
        
        # Add style parameters
        combined['style'] = style_params
        
        # Add machine learning adjustments
        for key, value in ml_adjustments.items():
            if key in combined:
                # If the key already exists, we need to merge intelligently
                if isinstance(combined[key], dict) and isinstance(value, dict):
                    combined[key].update(value)
                elif isinstance(combined[key], (list, tuple)) and isinstance(value, (list, tuple)):
                    combined[key] = list(combined[key]) + list(value)
                else:
                    # For scalar values, ML adjustments take precedence
                    combined[key] = value
            else:
                # If the key doesn't exist, just add it
                combined[key] = value
        
        return combined
    
    def _default_config(self):
        """
        Get the default configuration.
        
        Returns:
            dict: Default configuration.
        """
        return {
            'pattern': {
                'use_puzzle_patterns': True,
                'use_structural_patterns': True,
                'min_patterns': 1,
                'max_patterns': 5
            },
            'style': {
                'style_strength': 0.7,
                'preserve_difficulty': True
            },
            'ml': {
                'use_learning': True,
                'exploration_rate': 0.2,
                'continuous_learning': True
            },
            'default_params': {
                'min_width': 8,
                'max_width': 15,
                'min_height': 8,
                'max_height': 15,
                'min_boxes': 2,
                'max_boxes': 5,
                'wall_density': 0.2,
                'timeout': 30,
                'max_attempts': 100
            }
        }


class LevelGeneratorCore:
    """
    Core level generation functionality.
    
    This class handles the actual generation of levels based on parameters
    from the pattern-based generator, style transfer engine, and machine learning system.
    """
    
    def __init__(self):
        """Initialize the level generator core."""
        pass
        
    def generate(self, params):
        """
        Generate a level using the provided parameters.
        
        Args:
            params (dict): Parameters for generation.
            
        Returns:
            Level: A generated level.
        """
        # Extract parameters
        structure = params.get('patterns', {}).get('structure', {})
        placement = params.get('patterns', {}).get('placement', {})
        connections = params.get('patterns', {}).get('connections', {})
        style = params.get('style', {})
        
        # Create the basic structure
        level = self._create_structure(structure)
        
        # Place puzzle elements
        level = self._place_elements(level, placement)
        
        # Create connections
        level = self._create_connections(level, connections)
        
        # Apply style
        level = self._apply_style(level, style)
        
        return level
    
    def _create_structure(self, structure):
        """
        Create the basic structure of the level.
        
        Args:
            structure (dict): Structure parameters.
            
        Returns:
            Level: A level with basic structure.
        """
        # For now, create a simple empty level with walls around the perimeter
        # This will be replaced with actual structure generation based on patterns
        width = structure.get('width', 10)
        height = structure.get('height', 10)
        
        # Create an empty grid with walls around the perimeter
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    row.append('#')  # Wall
                else:
                    row.append(' ')  # Floor
            grid.append(row)
        
        # Convert grid to string
        level_string = '\n'.join(''.join(row) for row in grid)
        
        # Create and return the level
        return Level(level_data=level_string)
    
    def _place_elements(self, level, placement):
        """
        Place puzzle elements in the level.
        
        Args:
            level (Level): The level to modify.
            placement (dict): Placement parameters.
            
        Returns:
            Level: The modified level.
        """
        # For now, just place a player, a box, and a target
        # This will be replaced with actual element placement based on patterns
        
        # Find a position for the player (center of the level)
        player_x = level.width // 2
        player_y = level.height // 2
        
        # Find a position for the box (to the right of the player)
        box_x = player_x + 1
        box_y = player_y
        
        # Find a position for the target (to the left of the player)
        target_x = player_x - 1
        target_y = player_y
        
        # Create a new level with these elements
        grid = []
        for y in range(level.height):
            row = []
            for x in range(level.width):
                if x == player_x and y == player_y:
                    row.append('@')  # Player
                elif x == box_x and y == box_y:
                    row.append('$')  # Box
                elif x == target_x and y == target_y:
                    row.append('.')  # Target
                elif level.is_wall(x, y):
                    row.append('#')  # Wall
                else:
                    row.append(' ')  # Floor
            grid.append(row)
        
        # Convert grid to string
        level_string = '\n'.join(''.join(row) for row in grid)
        
        # Create and return the level
        return Level(level_data=level_string)
    
    def _create_connections(self, level, connections):
        """
        Create connections between different parts of the level.
        
        Args:
            level (Level): The level to modify.
            connections (dict): Connection parameters.
            
        Returns:
            Level: The modified level.
        """
        # For now, just return the level unchanged
        # This will be replaced with actual connection creation based on patterns
        return level
    
    def _apply_style(self, level, style):
        """
        Apply style parameters to the level.
        
        Args:
            level (Level): The level to modify.
            style (dict): Style parameters.
            
        Returns:
            Level: The modified level.
        """
        # For now, just return the level unchanged
        # This will be replaced with actual style application
        return level


class LevelValidator:
    """
    Validator for generated levels.
    
    This class checks if a generated level meets basic requirements.
    """
    
    def __init__(self):
        """Initialize the level validator."""
        pass
    
    def validate(self, level):
        """
        Validate a level.
        
        Args:
            level (Level): The level to validate.
            
        Returns:
            bool: True if the level is valid, False otherwise.
        """
        # Check if level has a player
        if level.player_pos == (0, 0):
            return False
        
        # Check if level has at least one box and target
        if not level.boxes or not level.targets:
            return False
        
        # Check if number of boxes matches number of targets
        if len(level.boxes) != len(level.targets):
            return False
        
        # Check if level is too small
        if level.width < 5 or level.height < 5:
            return False
        
        # Check if level is connected (all floor tiles are reachable)
        if not self._is_connected(level):
            return False
        
        return True
    
    def _is_connected(self, level):
        """
        Check if all floor tiles in the level are connected.
        
        Args:
            level (Level): The level to check.
            
        Returns:
            bool: True if all floor tiles are connected, False otherwise.
        """
        # For now, assume all levels are connected
        # This will be replaced with actual connectivity checking
        return True