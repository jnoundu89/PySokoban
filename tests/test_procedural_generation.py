#!/usr/bin/env python3
"""
Test script for the procedural level generation system.

This script demonstrates the procedural level generation system by generating
random levels, solving them, and displaying metrics.
"""

import time
import os
from procedural_generator import ProceduralGenerator
from level_solver import SokobanSolver
from level_metrics import LevelMetrics
from level import Level


def test_generation(count=5, params=None):
    """
    Generate and test a number of random levels.
    
    Args:
        count (int, optional): Number of levels to generate. Defaults to 5.
        params (dict, optional): Parameters for the generator. Defaults to None.
    """
    # Default parameters
    default_params = {
        'min_width': 8,
        'max_width': 12,
        'min_height': 8,
        'max_height': 12,
        'min_boxes': 2,
        'max_boxes': 4,
        'wall_density': 0.2,
        'timeout': 30
    }
    
    # Use provided parameters or defaults
    params = params or default_params
    
    # Create generator
    generator = ProceduralGenerator(**params)
    
    # Create metrics calculator
    metrics = LevelMetrics()
    
    # Generate levels
    print(f"Generating {count} random levels with parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()
    
    successful = 0
    total_time = 0
    total_attempts = 0
    
    for i in range(count):
        print(f"Generating level {i+1}/{count}...")
        start_time = time.time()
        
        try:
            # Generate level
            level = generator.generate_level()
            generation_time = time.time() - start_time
            total_time += generation_time
            total_attempts += generator.attempts
            successful += 1
            
            # Get solution
            solution = generator.solver.get_solution()
            
            # Calculate metrics
            level_metrics = metrics.calculate_metrics(level, solution)
            
            # Print statistics
            print(f"  Generated in {generation_time:.2f} seconds after {generator.attempts} attempts")
            print(f"  Size: {level.width}x{level.height}")
            print(f"  Boxes: {len(level.boxes)}")
            print(f"  Solution length: {len(solution)} moves")
            print(f"  Difficulty score: {level_metrics['difficulty']['overall_score']:.1f}/100")
            
            # Save level to file
            save_level(level, f"generated_level_{i+1}.txt")
            
            print(f"  Level saved to generated_level_{i+1}.txt")
            print()
            
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    # Print summary
    if successful > 0:
        print(f"Successfully generated {successful}/{count} levels")
        print(f"Average generation time: {total_time/successful:.2f} seconds")
        print(f"Average attempts per level: {total_attempts/successful:.1f}")
    else:
        print("Failed to generate any levels")


def save_level(level, filename):
    """
    Save a level to a file.
    
    Args:
        level (Level): The level to save.
        filename (str): The filename to save to.
    """
    # Create levels directory if it doesn't exist
    if not os.path.exists('../levels'):
        os.makedirs('../levels')
    
    # Save level
    with open(os.path.join('../levels', filename), 'w') as file:
        file.write(level.get_state_string())


def test_solver():
    """
    Test the solver with a simple level.
    """
    print("Testing solver with a simple level...")
    
    # Create a simple level
    level_string = """
    #####
    #   #
    # $ #
    # . #
    # @ #
    #####
    """
    level = Level(level_data=level_string)
    
    # Create a solver
    solver = SokobanSolver()
    
    # Time the solving process
    start_time = time.time()
    is_solvable = solver.is_solvable(level)
    solve_time = time.time() - start_time
    
    # Print results
    print(f"Level is solvable: {is_solvable}")
    if is_solvable:
        print(f"Solution length: {len(solver.get_solution())} moves")
        print(f"States explored: {solver.states_explored}")
        print(f"Solving time: {solve_time:.4f} seconds")
    
    print()


def test_metrics():
    """
    Test the metrics calculator with a simple level.
    """
    print("Testing metrics calculator with a simple level...")
    
    # Create a simple level
    level_string = """
    #######
    #     #
    # $.$ #
    # .@. #
    # $.$ #
    #     #
    #######
    """
    level = Level(level_data=level_string)
    
    # Create a solver and solve the level
    solver = SokobanSolver()
    is_solvable = solver.is_solvable(level)
    solution = solver.get_solution() if is_solvable else None
    
    # Create a metrics calculator
    metrics = LevelMetrics()
    
    # Calculate metrics
    level_metrics = metrics.calculate_metrics(level, solution)
    
    # Print metrics
    print(f"Level size: {level_metrics['size']['width']}x{level_metrics['size']['height']}")
    print(f"Playable area: {level_metrics['size']['playable_area']} tiles")
    print(f"Box count: {level_metrics['box_count']}")
    print(f"Solution length: {level_metrics['solution_length']} moves")
    print(f"Difficulty score: {level_metrics['difficulty']['overall_score']:.1f}/100")
    print(f"Space efficiency: {level_metrics['space_efficiency']:.2f}")
    print(f"Box density: {level_metrics['box_density']:.2f}")
    print("Patterns:")
    print(f"  Corners: {level_metrics['patterns']['corners']}")
    print(f"  Corridors: {level_metrics['patterns']['corridors']}")
    print(f"  Rooms: {level_metrics['patterns']['rooms']}")
    print(f"  Dead ends: {level_metrics['patterns']['dead_ends']}")
    
    print()


def main():
    """
    Main function to run the tests.
    """
    print("=== Sokoban Procedural Generation Test ===\n")
    
    # Test the solver
    test_solver()
    
    # Test the metrics calculator
    test_metrics()
    
    # Test level generation
    test_generation(count=3)


if __name__ == "__main__":
    main()