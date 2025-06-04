"""
Constants module for the Sokoban game.

This module defines all the constants used throughout the game,
including symbols, colors, and key mappings.
"""

# Game symbols
WALL = '#'
FLOOR = ' '
PLAYER = '@'
BOX = '$'
TARGET = '.'
PLAYER_ON_TARGET = '+'
BOX_ON_TARGET = '*'

# Display characters (for terminal mode)
DISPLAY_CHARS = {
    WALL: '█',
    FLOOR: ' ',
    PLAYER: '◉',
    BOX: '◼',
    TARGET: '·',
    PLAYER_ON_TARGET: '⊕',
    BOX_ON_TARGET: '✓'
}

# Colors (ANSI color codes for terminal mode)
COLORS = {
    'wall': '\033[90m',  # Dark gray
    'floor': '\033[0m',  # Default
    'player': '\033[93m',  # Yellow
    'box': '\033[33m',  # Orange
    'target': '\033[92m',  # Green
    'player_on_target': '\033[93m',  # Yellow
    'box_on_target': '\033[92m',  # Green
    'reset': '\033[0m'  # Reset to default
}

# Directions
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

# Keyboard layouts
QWERTY = 'qwerty'
AZERTY = 'azerty'

# Key bindings for different keyboard layouts
KEY_BINDINGS = {
    QWERTY: {
        'w': UP,
        's': DOWN,
        'a': LEFT,
        'd': RIGHT,
        'up': UP,
        'down': DOWN,
        'left': LEFT,
        'right': RIGHT,
        'r': 'reset',
        'q': 'quit',
        'n': 'next',
        'p': 'previous',
        'u': 'undo',
        'h': 'help',
        'f11': 'fullscreen'
    },
    AZERTY: {
        'z': UP,
        's': DOWN,
        'q': LEFT,
        'd': RIGHT,
        'up': UP,
        'down': DOWN,
        'left': LEFT,
        'right': RIGHT,
        'r': 'reset',
        'a': 'quit',
        'n': 'next',
        'p': 'previous',
        'u': 'undo',
        'h': 'help',
        'f11': 'fullscreen'
    }
}

# Default keyboard layout
DEFAULT_KEYBOARD = QWERTY

# Game settings
TITLE = "Sokoban"
CELL_SIZE = 64  # Pixel size of each cell (for GUI mode)