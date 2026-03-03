"""
Solution Replay Controller for Sokoban Game.

Provides VCR-style controls for replaying solutions: play, pause, step
forward/backward, variable speed, and a progress bar.
"""

import copy
import pygame


DIRECTION_MAP = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0),
}


class SolutionReplayController:
    """
    Precomputes all intermediate states of a solution and provides VCR-style
    playback with full random-access to any point in the solution.
    """

    def __init__(self, level, solution_moves, renderer, skin_manager):
        """
        Args:
            level: The Level object (will be deep-copied for precomputation).
            solution_moves: List of move strings ('UP', 'DOWN', 'LEFT', 'RIGHT').
            renderer: GUIRenderer for rendering.
            skin_manager: Skin manager for player sprites.
        """
        self.renderer = renderer
        self.skin_manager = skin_manager
        self.solution_moves = list(solution_moves)

        # Precompute all states
        self.states = []  # [(player_pos, boxes_copy), ...]
        self._precompute_states(level)

        # Playback state
        self.current_index = 0
        self.playing = False
        self.speed_ms = 300  # ms per move
        self.last_step_time = 0
        self.finished = False

        # UI colors
        self._bar_bg = (40, 40, 60)
        self._bar_fg = (100, 180, 255)
        self._bar_handle = (255, 255, 255)
        self._text_color = (220, 220, 220)
        self._btn_color = (80, 80, 120)
        self._btn_hover = (100, 100, 160)
        self._bar_height = 60

    def _precompute_states(self, level):
        """Execute all moves on a deep copy and record each state."""
        lvl = copy.deepcopy(level)
        lvl.reset()

        # Record initial state
        self.states.append((lvl.player_pos, list(lvl.boxes)))

        for move in self.solution_moves:
            delta = DIRECTION_MAP.get(move)
            if delta:
                lvl.move(delta[0], delta[1])
            self.states.append((lvl.player_pos, list(lvl.boxes)))

    def play(self):
        """Start or resume playback."""
        self.playing = True

    def pause(self):
        """Pause playback."""
        self.playing = False

    def toggle_play(self):
        """Toggle play/pause."""
        if self.playing:
            self.pause()
        else:
            self.play()

    def step_forward(self):
        """Advance one step."""
        self.pause()
        if self.current_index < len(self.states) - 1:
            self.current_index += 1

    def step_backward(self):
        """Go back one step."""
        self.pause()
        if self.current_index > 0:
            self.current_index -= 1

    def jump_to(self, index):
        """Jump to a specific state index."""
        self.current_index = max(0, min(index, len(self.states) - 1))

    def set_speed(self, ms_per_move):
        """Set playback speed in milliseconds per move."""
        self.speed_ms = max(20, min(2000, ms_per_move))

    def speed_up(self):
        """Increase playback speed."""
        self.set_speed(self.speed_ms - 50)

    def speed_down(self):
        """Decrease playback speed."""
        self.set_speed(self.speed_ms + 50)

    def apply_state(self, level):
        """Apply the current replay state to the actual level object."""
        if 0 <= self.current_index < len(self.states):
            player_pos, boxes = self.states[self.current_index]
            level.player_pos = player_pos
            level.boxes = list(boxes)

    def update(self, current_time):
        """
        Update playback. Call every frame.

        Args:
            current_time: pygame.time.get_ticks()

        Returns:
            bool: True if the replay is still active (not finished/exited).
        """
        if self.finished:
            return False

        if self.playing and current_time - self.last_step_time >= self.speed_ms:
            if self.current_index < len(self.states) - 1:
                self.current_index += 1
                self.last_step_time = current_time
            else:
                self.playing = False

        return True

    def handle_event(self, event):
        """
        Handle a pygame event.

        Returns:
            bool: True if the event was consumed.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_play()
                return True
            elif event.key == pygame.K_RIGHT:
                self.step_forward()
                return True
            elif event.key == pygame.K_LEFT:
                self.step_backward()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.finished = True
                return True
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.speed_up()
                return True
            elif event.key == pygame.K_MINUS:
                self.speed_down()
                return True
            elif event.key == pygame.K_HOME:
                self.jump_to(0)
                return True
            elif event.key == pygame.K_END:
                self.jump_to(len(self.states) - 1)
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if click is on the progress bar
            screen = self.renderer.screen
            bar_y = screen.get_height() - self._bar_height
            if event.pos[1] >= bar_y:
                self._handle_bar_click(event.pos[0], screen.get_width())
                return True

        return False

    def _handle_bar_click(self, mouse_x, screen_width):
        """Handle click on progress bar to seek."""
        margin = 20
        bar_width = screen_width - 2 * margin
        rel_x = mouse_x - margin
        fraction = max(0.0, min(1.0, rel_x / bar_width))
        index = int(fraction * (len(self.states) - 1))
        self.jump_to(index)

    def render_controls(self, screen):
        """Render the VCR control overlay at the bottom of the screen."""
        sw, sh = screen.get_size()
        bar_y = sh - self._bar_height

        # Background bar
        bar_surface = pygame.Surface((sw, self._bar_height), pygame.SRCALPHA)
        bar_surface.fill((0, 0, 0, 200))
        screen.blit(bar_surface, (0, bar_y))

        # Progress bar
        margin = 20
        bar_width = sw - 2 * margin
        progress_bar_y = bar_y + 8
        progress_bar_h = 10

        # Bar background
        pygame.draw.rect(screen, self._bar_bg,
                         (margin, progress_bar_y, bar_width, progress_bar_h), 0, 5)

        # Bar fill
        if len(self.states) > 1:
            fill_width = int(bar_width * self.current_index / (len(self.states) - 1))
        else:
            fill_width = 0
        if fill_width > 0:
            pygame.draw.rect(screen, self._bar_fg,
                             (margin, progress_bar_y, fill_width, progress_bar_h), 0, 5)

        # Handle
        handle_x = margin + fill_width
        pygame.draw.circle(screen, self._bar_handle,
                           (handle_x, progress_bar_y + progress_bar_h // 2), 7)

        # Text info
        font = pygame.font.Font(None, 22)

        # Step counter
        total = len(self.states) - 1
        step_text = f"Move {self.current_index}/{total}"
        step_surface = font.render(step_text, True, self._text_color)
        screen.blit(step_surface, (margin, bar_y + 25))

        # Play/pause status
        status = "Playing" if self.playing else "Paused"
        status_surface = font.render(status, True, self._bar_fg if self.playing else (255, 200, 100))
        status_rect = status_surface.get_rect(center=(sw // 2, bar_y + 32))
        screen.blit(status_surface, status_rect)

        # Speed info
        speed_text = f"Speed: {self.speed_ms}ms"
        speed_surface = font.render(speed_text, True, self._text_color)
        speed_rect = speed_surface.get_rect(right=sw - margin, y=bar_y + 25)
        screen.blit(speed_surface, speed_rect)

        # Controls hint
        hint_font = pygame.font.Font(None, 18)
        hint = "SPACE: Play/Pause | LEFT/RIGHT: Step | +/-: Speed | HOME/END: Jump | ESC: Exit"
        hint_surface = hint_font.render(hint, True, (140, 140, 160))
        hint_rect = hint_surface.get_rect(center=(sw // 2, bar_y + 50))
        screen.blit(hint_surface, hint_rect)
