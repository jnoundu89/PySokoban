#!/usr/bin/env python3
"""
Example script for using the Advanced Procedural Generation System.

This script demonstrates how to use the advanced procedural generation system
to generate Sokoban levels with pattern-based generation, style transfer,
and machine learning.
"""

import os
import time
from advanced_generation import AdvancedProceduralGenerator
from level import Level
from level_metrics import LevelMetrics
from level_solver import SokobanSolver


def main():
    """Main function to demonstrate the advanced procedural generation system."""
    print("=== Advanced Procedural Generation System Example ===\n")
    
    # Create the advanced generator
    print("Initializing advanced procedural generator...")
    generator = AdvancedProceduralGenerator()
    
    # Generate a level with default parameters
    print("\nGenerating level with default parameters...")
    start_time = time.time()
    try:
        level = generator.generate_level()
        generation_time = time.time() - start_time
        
        print(f"Level generated in {generation_time:.2f} seconds after {generator.generation_stats.get('attempts', 0)} attempts")
        print(f"Level dimensions: {level.width}x{level.height}")
        print(f"Number of boxes: {len(level.boxes)}")
        
        # Get solution
        solver = SokobanSolver()
        if solver.is_solvable(level):
            solution = solver.get_solution()
            print(f"Solution length: {len(solution)} moves")
        else:
            print("Level is not solvable (this should not happen)")
        
        # Calculate metrics
        metrics = LevelMetrics().calculate_metrics(level)
        print("\nLevel Metrics:")
        print(f"Difficulty score: {metrics['difficulty']['overall_score']:.1f}/100")
        print(f"Space efficiency: {metrics['space_efficiency']:.2f}")
        print(f"Box density: {metrics['box_density']:.2f}")
        
        # Print the level
        print("\nGenerated Level:")
        print(level.get_state_string())
        
        # Save the level
        save_level(level, "advanced_generated_level.txt")
        print("\nLevel saved to advanced_generated_level.txt")
        
    except Exception as e:
        print(f"Error generating level: {e}")
    
    # Generate a level with custom parameters
    print("\nGenerating level with custom parameters...")
    custom_params = {
        'min_width': 10,
        'max_width': 12,
        'min_height': 10,
        'max_height': 12,
        'min_boxes': 3,
        'max_boxes': 5,
        'wall_density': 0.25,
        'style': {
            'wall_style': {
                'density': 0.3,
                'distribution': 'clustered'
            },
            'space_style': {
                'openness': 0.6,
                'room_size': 'large'
            },
            'symmetry': {
                'horizontal': 0.7
            }
        }
    }
    
    start_time = time.time()
    try:
        level = generator.generate_level(custom_params)
        generation_time = time.time() - start_time
        
        print(f"Level generated in {generation_time:.2f} seconds after {generator.generation_stats.get('attempts', 0)} attempts")
        print(f"Level dimensions: {level.width}x{level.height}")
        print(f"Number of boxes: {len(level.boxes)}")
        
        # Get solution
        solver = SokobanSolver()
        if solver.is_solvable(level):
            solution = solver.get_solution()
            print(f"Solution length: {len(solution)} moves")
        else:
            print("Level is not solvable (this should not happen)")
        
        # Calculate metrics
        metrics = LevelMetrics().calculate_metrics(level)
        print("\nLevel Metrics:")
        print(f"Difficulty score: {metrics['difficulty']['overall_score']:.1f}/100")
        print(f"Space efficiency: {metrics['space_efficiency']:.2f}")
        print(f"Box density: {metrics['box_density']:.2f}")
        
        # Print the level
        print("\nGenerated Level:")
        print(level.get_state_string())
        
        # Save the level
        save_level(level, "advanced_generated_level_custom.txt")
        print("\nLevel saved to advanced_generated_level_custom.txt")
        
    except Exception as e:
        print(f"Error generating level: {e}")
    
    # Demonstrate style transfer
    print("\nDemonstrating style transfer...")
    try:
        # Load an existing level as a style source
        if os.path.exists("levels/level1.txt"):
            with open("levels/level1.txt", "r") as f:
                level_data = f.read()
                
            style_source = Level(level_data=level_data)
            
            # Extract style from the source level
            style_params = generator.style_transfer.extract_style(style_source)
            
            # Generate a level with the extracted style
            custom_params['style_source'] = style_source
            
            level = generator.generate_level(custom_params)
            
            print(f"Level generated with style transfer")
            print(f"Level dimensions: {level.width}x{level.height}")
            print(f"Number of boxes: {len(level.boxes)}")
            
            # Print the level
            print("\nGenerated Level with Style Transfer:")
            print(level.get_state_string())
            
            # Save the level
            save_level(level, "advanced_generated_level_style.txt")
            print("\nLevel saved to advanced_generated_level_style.txt")
        else:
            print("Could not find levels/level1.txt for style source")
    except Exception as e:
        print(f"Error with style transfer: {e}")
    
    print("\n=== Example Complete ===")


def save_level(level, filename):
    """
    Save a level to a file.
    
    Args:
        level (Level): The level to save.
        filename (str): The filename to save to.
    """
    # Create levels directory if it doesn't exist
    if not os.path.exists('levels'):
        os.makedirs('levels')
    
    # Save level
    with open(os.path.join('levels', filename), 'w') as file:
        file.write(level.get_state_string())


if __name__ == "__main__":
    main()