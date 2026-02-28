# Renderers module for PySokoban
from abc import ABC, abstractmethod


class AbstractRenderer(ABC):
    """Base interface for all renderers (GUI, Terminal)."""

    @abstractmethod
    def render_level(self, level, level_manager=None, **kwargs):
        """Render the current level state."""
        ...

    @abstractmethod
    def render_welcome_screen(self, keybindings=None):
        """Render the welcome/title screen."""
        ...

    @abstractmethod
    def render_game_over_screen(self, completed_all=False):
        """Render the game over screen."""
        ...

    @abstractmethod
    def render_help(self, keybindings=None):
        """Render help information."""
        ...
