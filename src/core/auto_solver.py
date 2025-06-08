"""
Auto Solver for Sokoban levels.

This module provides functionality to automatically solve Sokoban levels
and animate the solution step by step using both basic BFS and advanced A* algorithms.
"""

import time
import pygame
from src.generation.level_solver import SokobanSolver
from src.generation.advanced_solver import AdvancedSokobanSolver
from src.generation.expert_solver import ExpertSokobanSolver


class AutoSolver:
    """
    Class for automatically solving Sokoban levels and animating the solution.
    """
    
    def __init__(self, level, renderer=None, skin_manager=None):
        """
        Initialize the auto solver.
        
        Args:
            level (Level): The level to solve.
            renderer (GUIRenderer, optional): Renderer for animation.
            skin_manager (EnhancedSkinManager, optional): Skin manager for sprites.
        """
        self.level = level
        self.renderer = renderer
        self.skin_manager = skin_manager
        
        # Automatically choose solver based on level complexity
        self.complexity_score = self._calculate_complexity_score(level)
        self.solver = self._create_appropriate_solver(level)
        
        self.solution = None
        self.is_solving = False
        self.is_animating = False
    
    def _calculate_complexity_score(self, level):
        """
        Calculate level complexity score.
        
        Args:
            level (Level): The level to analyze.
            
        Returns:
            float: Complexity score.
        """
        level_size = level.width * level.height
        box_count = len(level.boxes)
        target_count = len(level.targets)
        
        # Enhanced complexity calculation
        complexity_score = (level_size * 0.5) + (box_count * 15) + (target_count * 10)
        
        # Add penalty for large levels with many boxes
        if box_count > 5 and level_size > 150:
            complexity_score *= 1.5
        
        return complexity_score
    
    def _create_appropriate_solver(self, level):
        """
        Create the appropriate solver based on level complexity.
        
        Args:
            level (Level): The level to solve.
            
        Returns:
            Solver instance (either SokobanSolver or AdvancedSokobanSolver).
        """
        complexity_score = self.complexity_score
        
        # Determine complexity category and solver
        if complexity_score < 50:
            # Simple level - use basic BFS
            complexity = "Simple"
            max_states = 25000
            max_time = 5.0
            solver = SokobanSolver(max_states=max_states, max_time=max_time)
            solver_type = "Basic BFS"
        elif complexity_score < 80:
            # Medium level - use basic BFS with higher limits
            complexity = "Medium"
            max_states = 75000
            max_time = 10.0
            solver = SokobanSolver(max_states=max_states, max_time=max_time)
            solver_type = "Basic BFS"
        elif complexity_score < 200:
            # Complex level - use advanced A* solver
            complexity = "Complex"
            max_states = 1000000
            max_time = 120.0
            solver = AdvancedSokobanSolver(level, max_states=max_states, time_limit=max_time)
            solver_type = "Advanced A*"
        else:
            # Expert level - use IDA* expert solver
            complexity = "Expert"
            max_time = 300.0  # 5 minutes for expert levels
            solver = ExpertSokobanSolver(level, time_limit=max_time)
            solver_type = "Expert IDA*"
            max_states = "unlimited"
        
        print(f"Level complexity: {complexity} (score: {complexity_score:.1f})")
        print(f"Using {solver_type} solver")
        print(f"Solver limits: {max_states} states, {max_time}s timeout")
        
        return solver
        
    def solve_level(self, progress_callback=None):
        """
        Solve the current level.
        
        Args:
            progress_callback (callable, optional): Function to call with progress updates.
            
        Returns:
            bool: True if the level was solved, False otherwise.
        """
        if self.is_solving:
            return False
            
        self.is_solving = True
        self.solution = None
        
        try:
            # Report progress
            if progress_callback:
                progress_callback("Analyzing level...")
            
            # Use different solving approaches based on solver type
            if isinstance(self.solver, (AdvancedSokobanSolver, ExpertSokobanSolver)):
                # Advanced A* or Expert IDA* solver
                self.solution = self.solver.solve(progress_callback)
                success = self.solution is not None
            else:
                # Basic BFS solver
                level_copy = self._create_level_copy()
                success = self.solver.is_solvable(level_copy)
                if success:
                    self.solution = self.solver.get_solution()
            
            if success and self.solution:
                if progress_callback:
                    progress_callback(f"Solution found! {len(self.solution)} moves")
                
                self.is_solving = False
                return True
            else:
                if progress_callback:
                    progress_callback("No solution found")
                
                self.is_solving = False
                return False
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error during solving: {e}")
            
            self.is_solving = False
            return False
    
    def _create_level_copy(self):
        """
        Create a copy of the level for solving.
        
        Returns:
            Level: A copy of the current level.
        """
        from src.core.level import Level
        
        # Create level data string
        level_data = self.level.get_state_string()
        
        # Create new level from data
        return Level(level_data=level_data)
    
    def get_solution_info(self):
        """
        Get information about the current solution.
        
        Returns:
            dict: Dictionary containing solution information.
        """
        if not self.solution:
            return None
        
        solver_type = 'Basic BFS'
        if isinstance(self.solver, AdvancedSokobanSolver):
            solver_type = 'Advanced A*'
        elif isinstance(self.solver, ExpertSokobanSolver):
            solver_type = 'Expert IDA*'
        
        return {
            'moves': len(self.solution),
            'solution': self.solution.copy(),
            'complexity_score': self.complexity_score,
            'solver_type': solver_type
        }
    
    def execute_solution_live(self, move_delay=500, show_grid=False, zoom_level=1.0, 
                            scroll_x=0, scroll_y=0, level_manager=None):
        """
        Execute the solution by taking control of the level and animating moves.
        
        Args:
            move_delay (int): Delay between moves in milliseconds.
            show_grid (bool): Whether to show grid.
            zoom_level (float): Zoom level for rendering.
            scroll_x (int): Horizontal scroll offset.
            scroll_y (int): Vertical scroll offset.
            level_manager: Level manager for rendering context.
        """
        if not self.solution or not self.renderer:
            return
        
        self.is_animating = True
        
        try:
            print(f"🤖 AI executing solution: {len(self.solution)} moves")
            
            for i, move in enumerate(self.solution):
                # Check for quit events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.is_animating = False
                        return
                
                # Convert move to direction
                direction_map = {
                    'UP': (0, -1),
                    'DOWN': (0, 1),
                    'LEFT': (-1, 0),
                    'RIGHT': (1, 0)
                }
                
                if move in direction_map:
                    dx, dy = direction_map[move]
                    
                    # Execute the move
                    moved = self.level.move(dx, dy)
                    
                    print(f"🤖 AI Move {i+1}/{len(self.solution)}: {move} -> {'✅' if moved else '❌'}")
                    
                    # Render the current state
                    if self.renderer and level_manager:
                        self.renderer.render_level(
                            self.level, level_manager, show_grid, 
                            zoom_level, scroll_x, scroll_y, self.skin_manager
                        )
                        pygame.display.flip()
                    
                    # Wait before next move
                    pygame.time.wait(move_delay)
                    
                    # Check if level is completed
                    if self.level.is_completed():
                        print("🎉 Level solved by AI! Well done!")
                        break
            
        except Exception as e:
            print(f"Error during solution execution: {e}")
        finally:
            self.is_animating = False
    
    def stop_solving(self):
        """Stop the current solving process."""
        self.is_solving = False
        self.is_animating = False