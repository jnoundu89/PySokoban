"""
Feedback Collection UI for Sokoban.

This module provides a UI component for collecting player feedback on generated levels.
"""

import pygame
import time


class FeedbackCollectionUI:
    """
    UI component for collecting player feedback on levels.
    
    This class provides a graphical interface for players to rate levels
    and provide feedback that can be used for machine learning.
    """
    
    def __init__(self, screen, ml_system):
        """
        Initialize the feedback UI.
        
        Args:
            screen: Pygame screen to render on.
            ml_system: Machine learning system to send feedback to.
        """
        self.screen = screen
        self.ml_system = ml_system
        self.visible = False
        self.current_level_id = None
        
        # UI state
        self.difficulty_rating = 0.5  # 0-1 scale
        self.enjoyment_rating = 0.5   # 0-1 scale
        self.comments = ""
        self.completion_time = 0
        self.move_count = 0
        
        # UI elements
        self.buttons = []
        self.sliders = []
        self.text_inputs = []
        
        # Colors
        self.bg_color = (0, 0, 0, 180)  # Semi-transparent black
        self.text_color = (255, 255, 255)
        self.button_color = (100, 100, 200)
        self.button_hover_color = (120, 120, 220)
        self.slider_bg_color = (80, 80, 80)
        self.slider_fg_color = (200, 200, 100)
        
        # Font
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 20)
        self.title_font = pygame.font.SysFont('Arial', 24, bold=True)
        
    def show(self, level_id, completion_time=0, move_count=0):
        """
        Show the feedback UI for a level.
        
        Args:
            level_id: Identifier for the level.
            completion_time (float, optional): Time taken to complete the level.
            move_count (int, optional): Number of moves taken.
        """
        self.visible = True
        self.current_level_id = level_id
        self.completion_time = completion_time
        self.move_count = move_count
        self._create_ui_elements()
        
    def hide(self):
        """Hide the feedback UI."""
        self.visible = False
        
    def render(self):
        """Render the feedback UI."""
        if not self.visible:
            return
            
        # Render background
        self._render_background()
        
        # Render title
        title = self.title_font.render("Level Feedback", True, self.text_color)
        self.screen.blit(title, (self.screen.get_width() // 2 - title.get_width() // 2, 50))
        
        # Render difficulty rating
        self._render_rating("Difficulty", self.difficulty_rating, 120)
        
        # Render enjoyment rating
        self._render_rating("Enjoyment", self.enjoyment_rating, 200)
        
        # Render completion info
        completion_text = f"Completion Time: {self.completion_time:.1f}s | Moves: {self.move_count}"
        completion_surface = self.font.render(completion_text, True, self.text_color)
        self.screen.blit(completion_surface, (self.screen.get_width() // 2 - completion_surface.get_width() // 2, 280))
        
        # Render buttons
        for button in self.buttons:
            self._render_button(button)
        
    def handle_event(self, event):
        """
        Handle UI events.
        
        Args:
            event: Pygame event.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if not self.visible:
            return False
            
        # Handle button clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check difficulty slider
            if 100 <= mouse_pos[1] <= 140:
                slider_x = self.screen.get_width() // 2
                slider_width = 200
                slider_left = slider_x - slider_width // 2
                slider_right = slider_x + slider_width // 2
                
                if slider_left <= mouse_pos[0] <= slider_right:
                    self.difficulty_rating = (mouse_pos[0] - slider_left) / slider_width
                    return True
            
            # Check enjoyment slider
            if 180 <= mouse_pos[1] <= 220:
                slider_x = self.screen.get_width() // 2
                slider_width = 200
                slider_left = slider_x - slider_width // 2
                slider_right = slider_x + slider_width // 2
                
                if slider_left <= mouse_pos[0] <= slider_right:
                    self.enjoyment_rating = (mouse_pos[0] - slider_left) / slider_width
                    return True
            
            # Check submit button
            submit_rect = pygame.Rect(self.screen.get_width() // 2 - 100, 350, 200, 40)
            if submit_rect.collidepoint(mouse_pos):
                self.submit_feedback()
                return True
                
            # Check cancel button
            cancel_rect = pygame.Rect(self.screen.get_width() // 2 - 100, 400, 200, 40)
            if cancel_rect.collidepoint(mouse_pos):
                self.hide()
                return True
                
        # Check for close events
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.hide()
            return True
            
        return False
        
    def submit_feedback(self):
        """Submit the collected feedback."""
        feedback_data = {
            'difficulty_rating': self.difficulty_rating,
            'enjoyment_rating': self.enjoyment_rating,
            'completion_time': self.completion_time,
            'move_count': self.move_count,
            'comments': self.comments,
            'timestamp': time.time()
        }
        
        # Send feedback to ML system
        self.ml_system.record_player_feedback(self.current_level_id, feedback_data)
        
        # Hide the UI
        self.hide()
    
    def _create_ui_elements(self):
        """Create UI elements."""
        # Reset UI elements
        self.buttons = []
        self.sliders = []
        self.text_inputs = []
        
        # Create submit button
        self.buttons.append({
            'rect': pygame.Rect(self.screen.get_width() // 2 - 100, 350, 200, 40),
            'text': 'Submit Feedback',
            'action': self.submit_feedback
        })
        
        # Create cancel button
        self.buttons.append({
            'rect': pygame.Rect(self.screen.get_width() // 2 - 100, 400, 200, 40),
            'text': 'Cancel',
            'action': self.hide
        })
    
    def _render_background(self):
        """Render the UI background."""
        # Create a semi-transparent surface
        bg_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        self.screen.blit(bg_surface, (0, 0))
        
        # Draw a panel
        panel_rect = pygame.Rect(
            self.screen.get_width() // 2 - 250,
            30,
            500,
            450
        )
        pygame.draw.rect(bg_surface, (50, 50, 50, 220), panel_rect, border_radius=10)
        self.screen.blit(bg_surface, (0, 0))
    
    def _render_rating(self, label, value, y_pos):
        """
        Render a rating slider.
        
        Args:
            label (str): Label for the rating.
            value (float): Current value (0-1).
            y_pos (int): Y position on screen.
        """
        # Render label
        label_surface = self.font.render(label, True, self.text_color)
        self.screen.blit(label_surface, (self.screen.get_width() // 2 - 200, y_pos))
        
        # Render slider
        slider_x = self.screen.get_width() // 2
        slider_width = 200
        slider_height = 20
        slider_rect = pygame.Rect(slider_x - slider_width // 2, y_pos, slider_width, slider_height)
        pygame.draw.rect(self.screen, self.slider_bg_color, slider_rect, border_radius=5)
        
        # Render slider value
        value_width = int(slider_width * value)
        value_rect = pygame.Rect(slider_x - slider_width // 2, y_pos, value_width, slider_height)
        pygame.draw.rect(self.screen, self.slider_fg_color, value_rect, border_radius=5)
        
        # Render value text
        value_text = f"{int(value * 100)}%"
        value_surface = self.font.render(value_text, True, self.text_color)
        self.screen.blit(value_surface, (slider_x + slider_width // 2 + 10, y_pos))
    
    def _render_button(self, button):
        """
        Render a button.
        
        Args:
            button (dict): Button data.
        """
        # Check if mouse is over button
        mouse_pos = pygame.mouse.get_pos()
        hover = button['rect'].collidepoint(mouse_pos)
        
        # Draw button
        color = self.button_hover_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button['rect'], border_radius=5)
        
        # Draw text
        text_surface = self.font.render(button['text'], True, self.text_color)
        text_rect = text_surface.get_rect(center=button['rect'].center)
        self.screen.blit(text_surface, text_rect)