#!/usr/bin/env python3
"""
Test script for the Advanced Procedural Generation System.

This script tests the basic functionality of the advanced procedural generation system.
"""

import unittest
import os
import sys
from advanced_generation import (
    AdvancedProceduralGenerator,
    PatternBasedGenerator,
    StyleTransferEngine,
    MachineLearningSystem
)
from level import Level


class TestAdvancedGeneration(unittest.TestCase):
    """Test cases for the advanced procedural generation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create data directory for testing
        os.makedirs('test_data', exist_ok=True)
        
        # Create the generator
        self.generator = AdvancedProceduralGenerator()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up test data
        if os.path.exists('test_data'):
            for file in os.listdir('test_data'):
                os.remove(os.path.join('test_data', file))
            os.rmdir('test_data')
    
    def test_generator_initialization(self):
        """Test that the generator initializes correctly."""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.pattern_generator)
        self.assertIsNotNone(self.generator.style_transfer)
        self.assertIsNotNone(self.generator.ml_system)
    
    def test_pattern_based_generator(self):
        """Test the pattern-based generator."""
        pattern_generator = PatternBasedGenerator()
        self.assertIsNotNone(pattern_generator)
        
        # Test getting patterns
        patterns = pattern_generator.get_patterns({})
        self.assertIsNotNone(patterns)
        self.assertIn('structure', patterns)
        self.assertIn('placement', patterns)
        self.assertIn('connections', patterns)
    
    def test_style_transfer_engine(self):
        """Test the style transfer engine."""
        style_engine = StyleTransferEngine()
        self.assertIsNotNone(style_engine)
        
        # Test getting style parameters
        style_params = style_engine.get_style_parameters({})
        self.assertIsNotNone(style_params)
        self.assertIn('wall_style', style_params)
        self.assertIn('space_style', style_params)
        self.assertIn('object_style', style_params)
        self.assertIn('symmetry', style_params)
        self.assertIn('aesthetics', style_params)
    
    def test_machine_learning_system(self):
        """Test the machine learning system."""
        ml_system = MachineLearningSystem()
        self.assertIsNotNone(ml_system)
        
        # Test getting generation parameters
        params = ml_system.get_generation_parameters({})
        self.assertIsNotNone(params)
    
    def test_level_generation(self):
        """Test generating a level."""
        try:
            level = self.generator.generate_level()
            self.assertIsNotNone(level)
            self.assertIsInstance(level, Level)
            self.assertTrue(level.width > 0)
            self.assertTrue(level.height > 0)
            self.assertTrue(len(level.boxes) > 0)
            self.assertTrue(len(level.targets) > 0)
            self.assertEqual(len(level.boxes), len(level.targets))
        except Exception as e:
            self.fail(f"Level generation failed: {e}")
    
    def test_custom_parameters(self):
        """Test generating a level with custom parameters."""
        custom_params = {
            'min_width': 10,
            'max_width': 12,
            'min_height': 10,
            'max_height': 12,
            'min_boxes': 3,
            'max_boxes': 5,
            'wall_density': 0.25
        }
        
        try:
            level = self.generator.generate_level(custom_params)
            self.assertIsNotNone(level)
            self.assertIsInstance(level, Level)
            self.assertTrue(10 <= level.width <= 12)
            self.assertTrue(10 <= level.height <= 12)
            self.assertTrue(3 <= len(level.boxes) <= 5)
        except Exception as e:
            self.fail(f"Level generation with custom parameters failed: {e}")


if __name__ == '__main__':
    unittest.main()