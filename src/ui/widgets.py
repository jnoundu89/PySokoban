"""
Shared UI widget components for PySokoban.

This module provides reusable UI elements: Button, ToggleButton, TextInput.
"""

import pygame


class Button:
    """A clickable button with hover and press-state tracking."""

    def __init__(self, text, x, y, width, height, action=None, color=(100, 100, 200),
                 hover_color=(130, 130, 255), text_color=(255, 255, 255), font_size=None):
        """
        Initialize a button.

        Args:
            text (str): The text to display on the button.
            x (int): X position of the button.
            y (int): Y position of the button.
            width (int): Width of the button.
            height (int): Height of the button.
            action: Function to call when the button is clicked.
            color: RGB color tuple for the button.
            hover_color: RGB color tuple when hovered.
            text_color: RGB color tuple for the text.
            font_size: Font size. If None, auto-calculated from button dimensions.
        """
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = self.color
        self.is_pressed = False

        if font_size is None:
            font_size = min(max(16, height // 2), min(36, width // (len(text) // 2 + 1)))

        self.font = pygame.font.Font(None, font_size)

    def draw(self, screen):
        """Draw the button on the screen."""
        pygame.draw.rect(screen, self.current_color, (self.x, self.y, self.width, self.height), 0, 10)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        """Check if the mouse is hovering over the button."""
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

    def update(self, mouse_pos):
        """Update the button's appearance based on mouse position."""
        if self.is_hovered(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

    def handle_event(self, event):
        """
        Handle mouse events for the button.

        Returns:
            bool: True if the button was clicked (action fired), False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered(pygame.mouse.get_pos()):
                self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.is_hovered(pygame.mouse.get_pos()):
                self.is_pressed = False
                if self.action:
                    self.action()
                return True
            self.is_pressed = False
        return False


class ToggleButton(Button):
    """A toggle button that switches between two states."""

    def __init__(self, text_on, text_off, x, y, width, height, is_on=False, action=None,
                 color_on=(100, 180, 100), color_off=(180, 100, 100),
                 hover_color_on=(120, 220, 120), hover_color_off=(220, 120, 120),
                 text_color=(255, 255, 255), font_size=None):
        self.text_on = text_on
        self.text_off = text_off
        self.is_on = is_on
        self.color_on = color_on
        self.color_off = color_off
        self.hover_color_on = hover_color_on
        self.hover_color_off = hover_color_off

        current_text = text_on if is_on else text_off
        current_color = color_on if is_on else color_off
        current_hover_color = hover_color_on if is_on else hover_color_off

        super().__init__(current_text, x, y, width, height, action,
                         current_color, current_hover_color, text_color, font_size)

    def toggle(self):
        """Toggle the button state."""
        self.is_on = not self.is_on
        self.text = self.text_on if self.is_on else self.text_off
        self.color = self.color_on if self.is_on else self.color_off
        self.hover_color = self.hover_color_on if self.is_on else self.hover_color_off
        self.current_color = self.color

        if self.action:
            self.action(self.is_on)

    def handle_event(self, event):
        """Handle mouse events — toggles state on click."""
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_hovered(pygame.mouse.get_pos()):
                self.toggle()
                return True
        return False


class TextInput:
    """A text input component for entering numerical values."""

    def __init__(self, x, y, width, height, min_value, max_value, current_value, label="",
                 color=(100, 100, 200), text_color=(0, 0, 0), bg_color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.label = label
        self.color = color
        self.text_color = text_color
        self.bg_color = bg_color
        self.active = False
        self.text = str(current_value)

        font_size = min(max(14, height - 4), 24)
        self.font = pygame.font.Font(None, font_size)

        self.cursor_visible = True
        self.cursor_blink_time = 500
        self.last_blink_time = pygame.time.get_ticks()

    def update(self, mouse_pos):
        """Update (no-op, exists for interface compatibility)."""
        pass

    def draw(self, screen):
        """Draw the text input on the screen."""
        if self.label:
            label_surface = self.font.render(self.label, True, self.text_color)
            screen.blit(label_surface, (self.x, self.y - 25))

        border_color = (150, 150, 255) if self.active else self.color
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height), 0, 5)
        pygame.draw.rect(screen, border_color, (self.x, self.y, self.width, self.height), 2, 5)

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

        if self.active:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_blink_time > self.cursor_blink_time:
                self.cursor_visible = not self.cursor_visible
                self.last_blink_time = current_time

            if self.cursor_visible:
                cursor_x = text_rect.right + 2
                if cursor_x > self.x + self.width - 5:
                    cursor_x = self.x + self.width - 5
                pygame.draw.line(screen, self.text_color,
                                (cursor_x, self.y + 5),
                                (cursor_x, self.y + self.height - 5), 2)

        range_text = f"Range: {self.min_value}-{self.max_value}"
        range_surface = pygame.font.Font(None, 18).render(range_text, True, (100, 100, 100))
        range_rect = range_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height + 15))
        screen.blit(range_surface, range_rect)

    def handle_event(self, event):
        """
        Handle events for the text input.

        Returns:
            bool: True if the value changed and is valid, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (self.x <= event.pos[0] <= self.x + self.width and
                self.y <= event.pos[1] <= self.y + self.height):
                self.active = True
                return False
            else:
                if self.active:
                    self.active = False
                    return self._validate_and_update()

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self.active = False
                return self._validate_and_update()
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.active = False
                self.text = str(self.current_value)
            else:
                if event.unicode.isdigit():
                    self.text += event.unicode

        return False

    def _validate_and_update(self):
        """Validate the entered text and update the current value if valid."""
        if not self.text:
            self.text = str(self.current_value)
            return False

        try:
            new_value = int(self.text)
            if self.min_value <= new_value <= self.max_value:
                old_value = self.current_value
                self.current_value = new_value
                return old_value != new_value
            else:
                self.text = str(self.current_value)
        except ValueError:
            self.text = str(self.current_value)

        return False
