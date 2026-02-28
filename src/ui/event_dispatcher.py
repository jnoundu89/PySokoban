"""
Centralized event dispatcher for the Sokoban game.

Calls pygame.event.get() once per frame, handles global events (QUIT, VIDEORESIZE,
F11 fullscreen toggle, ESC exit-fullscreen) via callbacks, and returns remaining
events for the active component to process.
"""

from typing import Callable, List, Optional

import pygame


class EventDispatcher:
    """Drains the pygame event queue once per frame and dispatches global events."""

    def __init__(
        self,
        on_quit: Optional[Callable[[], None]] = None,
        on_resize: Optional[Callable[[int, int], None]] = None,
        on_toggle_fullscreen: Optional[Callable[[], None]] = None,
        on_exit_fullscreen: Optional[Callable[[], None]] = None,
        is_fullscreen: Optional[Callable[[], bool]] = None,
    ):
        self._on_quit = on_quit
        self._on_resize = on_resize
        self._on_toggle_fullscreen = on_toggle_fullscreen
        self._on_exit_fullscreen = on_exit_fullscreen
        self._is_fullscreen = is_fullscreen or (lambda: False)
        self.quit_requested = False

    def pump(self) -> List[pygame.event.Event]:
        """Drain the event queue, handle globals, return remaining events."""
        remaining = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True
                if self._on_quit:
                    self._on_quit()
            elif event.type == pygame.VIDEORESIZE:
                if self._on_resize:
                    self._on_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                if self._on_toggle_fullscreen:
                    self._on_toggle_fullscreen()
            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
                and self._is_fullscreen()
            ):
                if self._on_exit_fullscreen:
                    self._on_exit_fullscreen()
            else:
                remaining.append(event)
        return remaining
