"""
Level Metrics module for Sokoban.

This module provides functionality to calculate various metrics for Sokoban levels,
such as size, difficulty, and solution complexity.
"""

import math
from level import Level
from level_solver import SokobanSolver


class LevelMetrics:
    """
    Class for calculating metrics for Sokoban levels.
    
    This class provides methods to evaluate the quality and difficulty
    of Sokoban levels based on various metrics.
    """
    
    def __init__(self):
        """
        Initialize the metrics calculator.
        """
        self.solver = SokobanSolver()
    
    def calculate_metrics(self, level, solution=None):
        """
        Calculate various metrics for a level.
        
        Args:
            level (Level): The level to calculate metrics for.
            solution (list, optional): A pre-computed solution. If None, the solver
                                      will be used to find a solution.
                                      
        Returns:
            dict: A dictionary of metrics.
        """
        # If no solution is provided, try to solve the level
        if solution is None:
            if self.solver.is_solvable(level):
                solution = self.solver.get_solution()
            else:
                solution = []
        
        # Calculate metrics
        metrics = {
            'size': self._calculate_size(level),
            'box_count': len(level.boxes),
            'solution_length': len(solution),
            'difficulty': self._estimate_difficulty(level, solution),
            'space_efficiency': self._calculate_space_efficiency(level),
            'box_density': self._calculate_box_density(level),
            'patterns': self._identify_patterns(level)
        }
        
        return metrics
    
    def _calculate_size(self, level):
        """
        Calculate the effective size of the level.
        
        Args:
            level (Level): The level to calculate size for.
            
        Returns:
            dict: Width, height, and area of the level.
        """
        return {
            'width': level.width,
            'height': level.height,
            'area': level.width * level.height,
            'playable_area': self._calculate_playable_area(level)
        }
    
    def _calculate_playable_area(self, level):
        """
        Calculate the playable area of the level (non-wall tiles).
        
        Args:
            level (Level): The level to calculate for.
            
        Returns:
            int: The number of non-wall tiles.
        """
        playable_tiles = 0
        for y in range(level.height):
            for x in range(level.width):
                if not level.is_wall(x, y):
                    playable_tiles += 1
        return playable_tiles
    
    def _estimate_difficulty(self, level, solution):
        """
        Estimate the difficulty of the level.
        
        Args:
            level (Level): The level to estimate difficulty for.
            solution (list): The solution for the level.
            
        Returns:
            dict: Various difficulty metrics.
        """
        # Basic difficulty metrics
        difficulty = {
            'solution_length': len(solution),
            'box_count': len(level.boxes),
            'push_complexity': self._estimate_push_complexity(level, solution),
            'spatial_complexity': self._estimate_spatial_complexity(level)
        }
        
        # Calculate overall difficulty score (0-100)
        # This is a simple weighted sum of the individual metrics
        # In a real implementation, this would be more sophisticated
        overall_score = (
            difficulty['solution_length'] * 0.4 +
            difficulty['box_count'] * 15 +
            difficulty['push_complexity'] * 20 +
            difficulty['spatial_complexity'] * 25
        )
        
        # Cap at 100
        difficulty['overall_score'] = min(100, overall_score)
        
        return difficulty
    
    def _estimate_push_complexity(self, level, solution):
        """
        Estimate the complexity of box pushing in the solution.
        
        Args:
            level (Level): The level to estimate for.
            solution (list): The solution for the level.
            
        Returns:
            float: A score representing push complexity.
        """
        # In a real implementation, this would analyze the solution
        # to count box pushes, direction changes, etc.
        # For now, we'll use a simple heuristic based on solution length and box count
        if not solution:
            return 0
        
        # Estimate pushes as 1/3 of moves (very rough estimate)
        estimated_pushes = len(solution) / 3
        
        # Complexity increases with more pushes per box
        if len(level.boxes) > 0:
            return estimated_pushes / len(level.boxes)
        return 0
    
    def _estimate_spatial_complexity(self, level):
        """
        Estimate the spatial complexity of the level.
        
        Args:
            level (Level): The level to estimate for.
            
        Returns:
            float: A score representing spatial complexity.
        """
        # Calculate the ratio of walls to total area
        wall_count = 0
        for y in range(level.height):
            for x in range(level.width):
                if level.is_wall(x, y):
                    wall_count += 1
        
        total_area = level.width * level.height
        wall_ratio = wall_count / total_area if total_area > 0 else 0
        
        # More walls generally means more complex navigation
        # But too many walls can make the level too simple
        # Optimal complexity is around 30-40% walls
        complexity = 4 * wall_ratio * (1 - wall_ratio)  # Peaks at wall_ratio = 0.5
        
        return complexity * 10  # Scale to 0-10
    
    def _calculate_space_efficiency(self, level):
        """
        Calculate how efficiently the level uses space.
        
        Args:
            level (Level): The level to calculate for.
            
        Returns:
            float: A ratio of playable area to total area.
        """
        playable_area = self._calculate_playable_area(level)
        total_area = level.width * level.height
        
        return playable_area / total_area if total_area > 0 else 0
    
    def _calculate_box_density(self, level):
        """
        Calculate the density of boxes in the playable area.
        
        Args:
            level (Level): The level to calculate for.
            
        Returns:
            float: A ratio of boxes to playable area.
        """
        playable_area = self._calculate_playable_area(level)
        
        return len(level.boxes) / playable_area if playable_area > 0 else 0
    
    def _identify_patterns(self, level):
        """
        Identify interesting patterns in the level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            dict: Identified patterns and their counts.
        """
        patterns = {
            'corners': self._count_corners(level),
            'corridors': self._count_corridors(level),
            'rooms': self._count_rooms(level),
            'dead_ends': self._count_dead_ends(level)
        }
        
        return patterns
    
    def _count_corners(self, level):
        """
        Count the number of corner configurations in the level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            int: The number of corners.
        """
        corners = 0
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                # Skip walls
                if level.is_wall(x, y):
                    continue
                
                # Check for corner configurations (two adjacent walls)
                adjacent_walls = 0
                if level.is_wall(x - 1, y):
                    adjacent_walls += 1
                if level.is_wall(x + 1, y):
                    adjacent_walls += 1
                if level.is_wall(x, y - 1):
                    adjacent_walls += 1
                if level.is_wall(x, y + 1):
                    adjacent_walls += 1
                
                if adjacent_walls >= 2:
                    corners += 1
        
        return corners
    
    def _count_corridors(self, level):
        """
        Count the number of corridor tiles in the level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            int: The number of corridor tiles.
        """
        corridors = 0
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                # Skip walls
                if level.is_wall(x, y):
                    continue
                
                # Check for corridor configurations (exactly two opposite walls)
                if ((level.is_wall(x - 1, y) and level.is_wall(x + 1, y) and
                     not level.is_wall(x, y - 1) and not level.is_wall(x, y + 1)) or
                    (not level.is_wall(x - 1, y) and not level.is_wall(x + 1, y) and
                     level.is_wall(x, y - 1) and level.is_wall(x, y + 1))):
                    corridors += 1
        
        return corridors
    
    def _count_rooms(self, level):
        """
        Estimate the number of rooms in the level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            int: The estimated number of rooms.
        """
        # This is a very simple heuristic
        # In a real implementation, this would use flood fill to identify separate rooms
        open_spaces = 0
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                if not level.is_wall(x, y):
                    # Count tiles with at least 3 adjacent non-wall tiles
                    adjacent_open = 0
                    if not level.is_wall(x - 1, y):
                        adjacent_open += 1
                    if not level.is_wall(x + 1, y):
                        adjacent_open += 1
                    if not level.is_wall(x, y - 1):
                        adjacent_open += 1
                    if not level.is_wall(x, y + 1):
                        adjacent_open += 1
                    
                    if adjacent_open >= 3:
                        open_spaces += 1
        
        # Rough estimate: one room per 9 open spaces
        return max(1, open_spaces // 9)
    
    def _count_dead_ends(self, level):
        """
        Count the number of dead ends in the level.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            int: The number of dead ends.
        """
        dead_ends = 0
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                # Skip walls
                if level.is_wall(x, y):
                    continue
                
                # Check for dead end configurations (exactly three adjacent walls)
                adjacent_walls = 0
                if level.is_wall(x - 1, y):
                    adjacent_walls += 1
                if level.is_wall(x + 1, y):
                    adjacent_walls += 1
                if level.is_wall(x, y - 1):
                    adjacent_walls += 1
                if level.is_wall(x, y + 1):
                    adjacent_walls += 1
                
                if adjacent_walls == 3:
                    dead_ends += 1
        
        return dead_ends


def test_metrics():
    """
    Test the metrics calculator with a simple level.
    """
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
    
    # Create a metrics calculator
    metrics = LevelMetrics()
    
    # Calculate metrics
    result = metrics.calculate_metrics(level)
    
    # Print the results
    print("Level Metrics:")
    print(f"Size: {result['size']['width']}x{result['size']['height']}")
    print(f"Playable area: {result['size']['playable_area']} tiles")
    print(f"Box count: {result['box_count']}")
    print(f"Solution length: {result['solution_length']} moves")
    print(f"Difficulty score: {result['difficulty']['overall_score']:.1f}/100")
    print(f"Space efficiency: {result['space_efficiency']:.2f}")
    print(f"Box density: {result['box_density']:.2f}")
    print("Patterns:")
    print(f"  Corners: {result['patterns']['corners']}")
    print(f"  Corridors: {result['patterns']['corridors']}")
    print(f"  Rooms: {result['patterns']['rooms']}")
    print(f"  Dead ends: {result['patterns']['dead_ends']}")


if __name__ == "__main__":
    test_metrics()