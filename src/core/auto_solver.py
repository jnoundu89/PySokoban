"""
Auto Solver for Sokoban levels.

This module provides functionality to automatically solve Sokoban levels
and animate the solution step by step.
"""

import time
import pygame
from src.generation.level_solver import SokobanSolver


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
        self.solver = SokobanSolver(max_states=100000, max_time=10.0)
        self.solution = None
        self.is_solving = False
        self.is_animating = False
        
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
            # Create a copy of the level to solve
            level_copy = self._create_level_copy()
            
            # Report progress
            if progress_callback:
                progress_callback("Analyzing level...")
            
            # Solve the level
            if self.solver.is_solvable(level_copy):
                self.solution = self.solver.get_solution()
                
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
                progress_callback(f"Error solving level: {e}")
            
            self.is_solving = False
            return False
    
    def execute_solution_live(self, move_delay=300, show_grid=False, zoom_level=1.0,
                             scroll_x=0, scroll_y=0, level_manager=None):
        """
        Execute the solution live on the actual level, taking control and solving it automatically.
        
        Args:
            move_delay (int): Delay between moves in milliseconds.
            show_grid (bool): Whether to show grid during execution.
            zoom_level (float): Zoom level for rendering.
            scroll_x (int): Horizontal scroll offset.
            scroll_y (int): Vertical scroll offset.
            level_manager (LevelManager): Level manager for rendering context.
            
        Returns:
            bool: True if solution executed successfully, False if interrupted.
        """
        if not self.solution or self.is_animating:
            return False
            
        self.is_animating = True
        
        try:
            # Don't reset the level - work with current state
            # The solution should work from the current position
            
            if self.renderer:
                try:
                    # Render initial state with AI control message
                    self.renderer.render_level(self.level, level_manager, show_grid,
                                             zoom_level, scroll_x, scroll_y, self.skin_manager)
                    self._render_solving_overlay("AI taking control... Press ESC to cancel")
                    pygame.display.flip()
                    pygame.time.wait(1000)
                except Exception as e:
                    print(f"Renderer error (continuing without graphics): {e}")
                    self.renderer = None  # Disable renderer if it fails
            
            print(f"🤖 AI executing solution: {len(self.solution)} moves")
            
            # Execute each move in the solution
            for i, move in enumerate(self.solution):
                # Check for interruption (ESC key) only if pygame is available
                if self.renderer:
                    try:
                        for event in pygame.event.get():
                            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                self.is_animating = False
                                self._render_solving_overlay("AI control cancelled by user")
                                pygame.display.flip()
                                pygame.time.wait(1000)
                                return False
                            elif event.type == pygame.QUIT:
                                self.is_animating = False
                                return False
                    except:
                        pass  # Ignore pygame errors
                
                # Convert move to direction
                dx, dy = self._move_to_direction(move)
                
                # Update player state in skin manager if available
                if self.skin_manager:
                    try:
                        player_x, player_y = self.level.player_pos
                        new_x, new_y = player_x + dx, player_y + dy
                        is_pushing = (new_x, new_y) in self.level.boxes
                        self.skin_manager.update_player_state(move, is_pushing, False)
                    except:
                        pass  # Ignore skin manager errors
                
                # Execute the move on the actual level
                moved = self.level.move(dx, dy)
                
                print(f"🤖 AI Move {i + 1}/{len(self.solution)}: {move.upper()} -> {'✅' if moved else '❌'}")
                
                if not moved:
                    # Move failed - solution might be invalid for current state
                    self.is_animating = False
                    print("❌ AI control failed - invalid move")
                    if self.renderer:
                        try:
                            self._render_solving_overlay("AI control failed - invalid move")
                            pygame.display.flip()
                            pygame.time.wait(2000)
                        except:
                            pass
                    return False
                
                # Render the updated level if renderer available
                if self.renderer:
                    try:
                        self.renderer.render_level(self.level, level_manager, show_grid,
                                                 zoom_level, scroll_x, scroll_y, self.skin_manager)
                        
                        # Add progress overlay
                        progress_text = f"AI Move {i + 1}/{len(self.solution)}: {move.upper()}"
                        if self.level.is_completed():
                            progress_text = "Level completed by AI!"
                        self._render_solving_overlay(progress_text)
                        
                        pygame.display.flip()
                    except Exception as e:
                        print(f"Rendering error (continuing): {e}")
                
                # Check if level is completed
                if self.level.is_completed():
                    self.is_animating = False
                    print("🎉 Level solved by AI! Well done!")
                    if self.renderer:
                        try:
                            self._render_solving_overlay("🎉 Level solved by AI! Well done!")
                            pygame.display.flip()
                            pygame.time.wait(2000)
                        except:
                            pass
                    return True
                
                # Wait between moves (only if we have pygame)
                if self.renderer:
                    try:
                        pygame.time.wait(move_delay)
                    except:
                        import time
                        time.sleep(move_delay / 1000.0)  # Fallback to regular sleep
                else:
                    import time
                    time.sleep(move_delay / 1000.0)  # Use regular sleep if no pygame
            
            # Solution executed but level not completed (shouldn't happen)
            self.is_animating = False
            print("⚠️ AI finished moves but level not completed")
            if self.renderer:
                try:
                    self._render_solving_overlay("AI finished moves but level not completed")
                    pygame.display.flip()
                    pygame.time.wait(2000)
                except:
                    pass
            return False
            
        except Exception as e:
            print(f"Error during AI execution: {e}")
            self.is_animating = False
            if self.renderer:
                try:
                    self._render_solving_overlay(f"AI error: {str(e)}")
                    pygame.display.flip()
                    pygame.time.wait(2000)
                except:
                    pass
            return False

    def animate_solution(self, move_delay=500, show_grid=False, zoom_level=1.0,
                        scroll_x=0, scroll_y=0, level_manager=None):
        """
        Animate the solution step by step (legacy method for demonstration purposes).
        
        Args:
            move_delay (int): Delay between moves in milliseconds.
            show_grid (bool): Whether to show grid during animation.
            zoom_level (float): Zoom level for rendering.
            scroll_x (int): Horizontal scroll offset.
            scroll_y (int): Vertical scroll offset.
            level_manager (LevelManager): Level manager for rendering context.
            
        Returns:
            bool: True if animation completed, False if interrupted.
        """
        # For backward compatibility, redirect to live execution
        return self.execute_solution_live(move_delay, show_grid, zoom_level, scroll_x, scroll_y, level_manager)
    
    def get_solution_info(self):
        """
        Get information about the current solution.
        
        Returns:
            dict: Dictionary with solution information or None if no solution.
        """
        if not self.solution:
            return None
            
        return {
            'moves': len(self.solution),
            'solution': self.solution.copy(),
            'moves_breakdown': self._analyze_solution()
        }
    
    def _create_level_copy(self):
        """
        Create a copy of the current level for solving.
        
        Returns:
            Level: A copy of the current level.
        """
        from src.core.level import Level
        level_string = self.level.get_state_string()
        return Level(level_data=level_string)
    
    def _move_to_direction(self, move):
        """
        Convert move string to direction coordinates.
        
        Args:
            move (str): Move direction ('up', 'down', 'left', 'right').
            
        Returns:
            tuple: (dx, dy) coordinates.
        """
        move_map = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }
        return move_map.get(move, (0, 0))
    
    def _analyze_solution(self):
        """
        Analyze the solution to provide statistics.
        
        Returns:
            dict: Dictionary with solution statistics.
        """
        if not self.solution:
            return {}
            
        move_counts = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        for move in self.solution:
            if move in move_counts:
                move_counts[move] += 1
                
        return move_counts
    
    def _render_solving_overlay(self, text):
        """
        Render an overlay with solving progress text.
        
        Args:
            text (str): Text to display.
        """
        if not self.renderer or not hasattr(self.renderer, 'screen'):
            return
            
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.renderer.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.renderer.screen.blit(overlay, (0, 0))
        
        # Render text
        font = pygame.font.Font(None, 36)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.renderer.screen.get_width() // 2,
                                                 self.renderer.screen.get_height() // 2))
        self.renderer.screen.blit(text_surface, text_rect)
        
        # Add instruction text
        instruction_font = pygame.font.Font(None, 24)
        instruction_text = "Press ESC to cancel"
        instruction_surface = instruction_font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(self.renderer.screen.get_width() // 2,
                                                              text_rect.bottom + 30))
        self.renderer.screen.blit(instruction_surface, instruction_rect)


def test_auto_solver():
    """
    Test the auto solver with a simple level.
    """
    from src.core.level import Level
    
    # Create a simple test level
    level_string = """
#####
#   #
# $ #
# . #
# @ #
#####
"""
    level = Level(level_data=level_string)
    
    # Create auto solver
    auto_solver = AutoSolver(level)
    
    # Solve the level
    def progress_callback(message):
        print(f"Progress: {message}")
    
    success = auto_solver.solve_level(progress_callback)
    
    if success:
        solution_info = auto_solver.get_solution_info()
        print(f"Solution found: {solution_info}")
    else:
        print("No solution found")


if __name__ == "__main__":
    test_auto_solver()