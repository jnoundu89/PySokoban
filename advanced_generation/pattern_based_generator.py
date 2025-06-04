"""
Pattern-Based Generator for Sokoban.

This module provides functionality to generate Sokoban levels using predefined patterns
for both puzzle elements (box-wall configurations) and structural elements (rooms, corridors).
"""

import random
import copy
from level import Level


class PatternBasedGenerator:
    """
    Pattern-based generator for Sokoban levels.
    
    This class handles the generation of levels using predefined patterns
    for both puzzle elements and structural elements.
    """
    
    def __init__(self, config=None):
        """
        Initialize the pattern-based generator.
        
        Args:
            config (dict, optional): Configuration for pattern generation.
                                    Defaults to None, which uses default configuration.
        """
        self.config = config or {}
        self.pattern_library = PatternLibrary()
        self.pattern_detector = PatternDetector()
        self.pattern_composer = PatternComposer()
        
    def get_patterns(self, params):
        """
        Get patterns based on the provided parameters.
        
        Args:
            params (dict): Parameters for pattern selection.
            
        Returns:
            dict: Selected patterns and their application parameters.
        """
        # Select patterns based on difficulty, size, etc.
        puzzle_patterns = self.pattern_library.select_puzzle_patterns(params)
        structural_patterns = self.pattern_library.select_structural_patterns(params)
        
        # Combine patterns with composition rules
        composition_plan = self.pattern_composer.create_composition_plan(
            puzzle_patterns, structural_patterns, params
        )
        
        return composition_plan
        
    def analyze_level(self, level):
        """
        Analyze a level to detect patterns.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            dict: Detected patterns in the level.
        """
        # Detect puzzle patterns (box configurations, etc.)
        puzzle_patterns = self.pattern_detector.detect_puzzle_patterns(level)
        
        # Detect structural patterns (rooms, corridors, etc.)
        structural_patterns = self.pattern_detector.detect_structural_patterns(level)
        
        # Return combined patterns
        return {
            'puzzle_patterns': puzzle_patterns,
            'structural_patterns': structural_patterns
        }
        
    def add_pattern_to_library(self, pattern, pattern_type, metadata=None):
        """
        Add a new pattern to the library.
        
        Args:
            pattern: The pattern to add.
            pattern_type (str): Type of pattern ('puzzle' or 'structural').
            metadata (dict, optional): Additional information about the pattern.
        """
        self.pattern_library.add_pattern(pattern, pattern_type, metadata)


class PatternLibrary:
    """
    Library of Sokoban level patterns.
    
    This class stores and manages patterns for both puzzle elements
    and structural elements.
    """
    
    def __init__(self):
        """Initialize the pattern library."""
        self.puzzle_patterns = self._initialize_puzzle_patterns()
        self.structural_patterns = self._initialize_structural_patterns()
        
    def add_pattern(self, pattern, pattern_type, metadata=None):
        """
        Add a pattern to the library.
        
        Args:
            pattern: The pattern to add.
            pattern_type (str): Type of pattern ('puzzle' or 'structural').
            metadata (dict, optional): Additional information about the pattern.
        """
        if pattern_type == 'puzzle':
            self.puzzle_patterns.append({
                'pattern': pattern,
                'metadata': metadata or {}
            })
        elif pattern_type == 'structural':
            self.structural_patterns.append({
                'pattern': pattern,
                'metadata': metadata or {}
            })
            
    def select_puzzle_patterns(self, params):
        """
        Select puzzle patterns based on parameters.
        
        Args:
            params (dict): Parameters for pattern selection.
            
        Returns:
            list: Selected puzzle patterns.
        """
        # For now, just return all puzzle patterns
        # This will be replaced with actual pattern selection based on parameters
        return copy.deepcopy(self.puzzle_patterns)
            
    def select_structural_patterns(self, params):
        """
        Select structural patterns based on parameters.
        
        Args:
            params (dict): Parameters for pattern selection.
            
        Returns:
            list: Selected structural patterns.
        """
        # For now, just return all structural patterns
        # This will be replaced with actual pattern selection based on parameters
        return copy.deepcopy(self.structural_patterns)
    
    def _initialize_puzzle_patterns(self):
        """
        Initialize the library with basic puzzle patterns.
        
        Returns:
            list: Basic puzzle patterns.
        """
        patterns = []
        
        # Simple box-target pattern
        patterns.append({
            'pattern': [
                '   ',
                ' $ ',
                ' . '
            ],
            'metadata': {
                'name': 'simple_box_target',
                'difficulty': 1,
                'description': 'Simple box and target'
            }
        })
        
        # Box in corner pattern
        patterns.append({
            'pattern': [
                '###',
                '#$ ',
                '#..'
            ],
            'metadata': {
                'name': 'box_in_corner',
                'difficulty': 2,
                'description': 'Box in corner with target'
            }
        })
        
        # Box in corridor pattern
        patterns.append({
            'pattern': [
                '###',
                ' $ ',
                '###'
            ],
            'metadata': {
                'name': 'box_in_corridor',
                'difficulty': 3,
                'description': 'Box in corridor'
            }
        })
        
        return patterns
    
    def _initialize_structural_patterns(self):
        """
        Initialize the library with basic structural patterns.
        
        Returns:
            list: Basic structural patterns.
        """
        patterns = []
        
        # Simple room pattern
        patterns.append({
            'pattern': [
                '#####',
                '#   #',
                '#   #',
                '#   #',
                '#####'
            ],
            'metadata': {
                'name': 'simple_room',
                'size': 'small',
                'description': 'Simple square room'
            }
        })
        
        # Corridor pattern
        patterns.append({
            'pattern': [
                '###',
                '   ',
                '###'
            ],
            'metadata': {
                'name': 'corridor',
                'size': 'small',
                'description': 'Simple corridor'
            }
        })
        
        # L-shaped room pattern
        patterns.append({
            'pattern': [
                '#####',
                '#   #',
                '#   ##',
                '#    #',
                '######'
            ],
            'metadata': {
                'name': 'l_shaped_room',
                'size': 'medium',
                'description': 'L-shaped room'
            }
        })
        
        return patterns


class PatternDetector:
    """
    Detector for Sokoban level patterns.
    
    This class analyzes levels to detect both puzzle patterns
    and structural patterns.
    """
    
    def __init__(self):
        """Initialize the pattern detector."""
        pass
        
    def detect_puzzle_patterns(self, level):
        """
        Detect puzzle patterns in a level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            list: Detected puzzle patterns.
        """
        patterns = []
        
        # Detect box-wall configurations
        box_wall_patterns = self._detect_box_wall_patterns(level)
        patterns.extend(box_wall_patterns)
        
        # Detect box-target relationships
        box_target_patterns = self._detect_box_target_patterns(level)
        patterns.extend(box_target_patterns)
        
        return patterns
        
    def detect_structural_patterns(self, level):
        """
        Detect structural patterns in a level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            list: Detected structural patterns.
        """
        patterns = []
        
        # Detect rooms
        rooms = self._detect_rooms(level)
        patterns.extend(rooms)
        
        # Detect corridors
        corridors = self._detect_corridors(level)
        patterns.extend(corridors)
        
        # Detect connectivity patterns
        connectivity = self._detect_connectivity(level)
        patterns.extend(connectivity)
        
        return patterns
    
    def _detect_box_wall_patterns(self, level):
        """
        Detect box-wall patterns in a level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            list: Detected box-wall patterns.
        """
        # For now, return an empty list
        # This will be replaced with actual pattern detection
        return []
    
    def _detect_box_target_patterns(self, level):
        """
        Detect box-target patterns in a level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            list: Detected box-target patterns.
        """
        # For now, return an empty list
        # This will be replaced with actual pattern detection
        return []
    
    def _detect_rooms(self, level):
        """
        Detect rooms in a level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            list: Detected rooms.
        """
        # For now, return an empty list
        # This will be replaced with actual room detection
        return []
    
    def _detect_corridors(self, level):
        """
        Detect corridors in a level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            list: Detected corridors.
        """
        # For now, return an empty list
        # This will be replaced with actual corridor detection
        return []
    
    def _detect_connectivity(self, level):
        """
        Detect connectivity patterns in a level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            list: Detected connectivity patterns.
        """
        # For now, return an empty list
        # This will be replaced with actual connectivity detection
        return []


class PatternComposer:
    """
    Composer for Sokoban level patterns.
    
    This class combines patterns to create coherent level structures.
    """
    
    def __init__(self):
        """Initialize the pattern composer."""
        pass
        
    def create_composition_plan(self, puzzle_patterns, structural_patterns, params):
        """
        Create a plan for composing patterns into a level.
        
        Args:
            puzzle_patterns (list): Selected puzzle patterns.
            structural_patterns (list): Selected structural patterns.
            params (dict): Generation parameters.
            
        Returns:
            dict: A composition plan for the level generator.
        """
        # Determine level structure based on structural patterns
        structure = self._create_structure(structural_patterns, params)
        
        # Place puzzle patterns within the structure
        placement = self._place_puzzle_patterns(puzzle_patterns, structure, params)
        
        # Create connections between components
        connections = self._create_connections(structure, params)
        
        return {
            'structure': structure,
            'placement': placement,
            'connections': connections
        }
    
    def _create_structure(self, structural_patterns, params):
        """
        Create a level structure based on structural patterns.
        
        Args:
            structural_patterns (list): Selected structural patterns.
            params (dict): Generation parameters.
            
        Returns:
            dict: Structure parameters.
        """
        # For now, just create a simple structure
        # This will be replaced with actual structure creation based on patterns
        width = random.randint(params.get('min_width', 8), params.get('max_width', 15))
        height = random.randint(params.get('min_height', 8), params.get('max_height', 15))
        
        return {
            'width': width,
            'height': height,
            'patterns': structural_patterns
        }
    
    def _place_puzzle_patterns(self, puzzle_patterns, structure, params):
        """
        Place puzzle patterns within the level structure.
        
        Args:
            puzzle_patterns (list): Selected puzzle patterns.
            structure (dict): Level structure.
            params (dict): Generation parameters.
            
        Returns:
            dict: Placement parameters.
        """
        # For now, just create a simple placement
        # This will be replaced with actual pattern placement
        num_boxes = random.randint(params.get('min_boxes', 1), params.get('max_boxes', 5))
        
        return {
            'num_boxes': num_boxes,
            'patterns': puzzle_patterns
        }
    
    def _create_connections(self, structure, params):
        """
        Create connections between components in the level structure.
        
        Args:
            structure (dict): Level structure.
            params (dict): Generation parameters.
            
        Returns:
            dict: Connection parameters.
        """
        # For now, just create simple connections
        # This will be replaced with actual connection creation
        return {
            'connect_all': True
        }