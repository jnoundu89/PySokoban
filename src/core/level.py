"""
Level module for the Sokoban game.

This module handles loading, parsing, and managing game levels.
"""

from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET


class Level:
    """
    Class representing a Sokoban level.

    This class handles loading levels from files, tracking game state,
    and managing player and box movements.
    """

    def __init__(self, level_data=None, level_file=None, title="", description="", author=""):
        """
        Initialize a new level either from string data or from a file.

        Args:
            level_data (str, optional): Level data as a string.
            level_file (str, optional): Path to a level file.
            title (str, optional): Level title.
            description (str, optional): Level description.
            author (str, optional): Level author.

        Raises:
            ValueError: If neither level_data nor level_file is provided.
        """
        self.map_data = []
        self.width = 0
        self.height = 0
        self.player_pos = (0, 0)
        self.boxes = []
        self.targets = []
        self.moves = 0
        self.pushes = 0
        self.history = []  # Stack to store game state for undo functionality

        # Metadata
        self.title = title
        self.description = description
        self.author = author

        if level_data:
            self.load_from_string(level_data)
        elif level_file:
            self.load_from_file(level_file)
        else:
            raise ValueError("Either level_data or level_file must be provided")

    def load_from_string(self, level_string):
        """
        Load level data from a string.

        Args:
            level_string (str): Level data as a string.
        """
        lines = level_string.split('\n')
        # Remove empty lines from the beginning and end, but preserve internal spacing
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        self._parse_level(lines)

    def load_from_file(self, filename):
        """
        Load level data from a file.

        Args:
            filename (str): Path to a level file.

        Raises:
            FileNotFoundError: If the level file cannot be found.
        """
        try:
            with open(filename, 'r') as file:
                lines = [line.rstrip() for line in file]
            self._parse_level(lines)
        except FileNotFoundError:
            raise FileNotFoundError(f"Level file not found: {filename}")

    def _parse_level(self, lines):
        """
        Parse level data from a list of strings.

        Args:
            lines (list): List of strings representing the level.
        """
        # Reset level data
        self.map_data = []
        self.boxes = []
        self.targets = []

        # Normalize line lengths while preserving original spacing
        max_width = max(len(line) for line in lines)
        # Only pad lines that are shorter than max_width, preserving original content
        normalized_lines = []
        for line in lines:
            if len(line) < max_width:
                # Pad with spaces to the right to reach max_width
                normalized_lines.append(line + ' ' * (max_width - len(line)))
            else:
                normalized_lines.append(line)
        lines = normalized_lines

        self.height = len(lines)
        self.width = max_width

        # Parse level data
        for y, line in enumerate(lines):
            row = []
            for x, char in enumerate(line):
                if char == PLAYER:
                    self.player_pos = (x, y)
                    row.append(FLOOR)
                elif char == PLAYER_ON_TARGET:
                    self.player_pos = (x, y)
                    self.targets.append((x, y))
                    row.append(TARGET)
                elif char == BOX:
                    self.boxes.append((x, y))
                    row.append(FLOOR)
                elif char == BOX_ON_TARGET:
                    self.boxes.append((x, y))
                    self.targets.append((x, y))
                    row.append(TARGET)
                elif char == TARGET:
                    self.targets.append((x, y))
                    row.append(TARGET)
                else:
                    row.append(char)
            self.map_data.append(row)

        # Reset game stats
        self.moves = 0
        self.pushes = 0
        self.history = []

    def get_cell(self, x, y):
        """
        Get the character at the specified coordinates.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.

        Returns:
            str: The character at the specified position.
        """
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.map_data[y][x]
        return WALL  # Default to wall for out-of-bounds

    def is_wall(self, x, y):
        """
        Check if the cell at the specified coordinates is a wall.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.

        Returns:
            bool: True if the cell is a wall, False otherwise.
        """
        return self.get_cell(x, y) == WALL

    def is_box(self, x, y):
        """
        Check if there is a box at the specified coordinates.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.

        Returns:
            bool: True if there is a box, False otherwise.
        """
        return (x, y) in self.boxes

    def is_target(self, x, y):
        """
        Check if the cell at the specified coordinates is a target.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.

        Returns:
            bool: True if the cell is a target, False otherwise.
        """
        return (x, y) in self.targets or self.get_cell(x, y) == TARGET

    def can_move(self, dx, dy):
        """
        Check if the player can move in the specified direction.

        Args:
            dx (int): X direction (-1, 0, or 1).
            dy (int): Y direction (-1, 0, or 1).

        Returns:
            bool: True if the move is valid, False otherwise.
        """
        x, y = self.player_pos
        new_x, new_y = x + dx, y + dy

        # Check if the new position is a wall
        if self.is_wall(new_x, new_y):
            return False

        # Check if the new position contains a box
        if self.is_box(new_x, new_y):
            # If there's a box, check if it can be pushed
            box_x, box_y = new_x + dx, new_y + dy

            # Can't push if the destination is a wall or another box
            if self.is_wall(box_x, box_y) or self.is_box(box_x, box_y):
                return False

        return True

    def move(self, dx, dy):
        """
        Move the player in the specified direction if possible.

        Args:
            dx (int): X direction (-1, 0, or 1).
            dy (int): Y direction (-1, 0, or 1).

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        if not self.can_move(dx, dy):
            return False

        # Save current state for undo
        self._save_state()

        x, y = self.player_pos
        new_x, new_y = x + dx, y + dy

        # Check if we're pushing a box
        pushing_box = False
        for i, (box_x, box_y) in enumerate(self.boxes):
            if (box_x, box_y) == (new_x, new_y):
                # Move the box
                self.boxes[i] = (box_x + dx, box_y + dy)
                pushing_box = True
                self.pushes += 1
                break

        # Move the player
        self.player_pos = (new_x, new_y)
        self.moves += 1

        return True

    def _save_state(self):
        """
        Save the current game state for undo functionality.
        """
        state = {
            'player_pos': self.player_pos,
            'boxes': self.boxes.copy(),
            'moves': self.moves,
            'pushes': self.pushes
        }
        self.history.append(state)

    def undo(self):
        """
        Undo the last move if possible.

        Returns:
            bool: True if the undo was successful, False otherwise.
        """
        if not self.history:
            return False

        state = self.history.pop()
        self.player_pos = state['player_pos']
        self.boxes = state['boxes']
        self.moves = state['moves']
        self.pushes = state['pushes']

        return True

    def is_completed(self):
        """
        Check if the level is completed (all boxes are on targets).

        Returns:
            bool: True if the level is completed, False otherwise.
        """
        if len(self.boxes) != len(self.targets):
            return False

        return all(box_pos in self.targets for box_pos in self.boxes)

    def get_display_char(self, x, y):
        """
        Get the display character at the specified coordinates.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.

        Returns:
            str: The display character at the specified position.
        """
        if (x, y) == self.player_pos:
            return PLAYER_ON_TARGET if self.is_target(x, y) else PLAYER
        elif (x, y) in self.boxes:
            return BOX_ON_TARGET if self.is_target(x, y) else BOX
        elif self.is_target(x, y):
            return TARGET
        else:
            return self.get_cell(x, y)

    def _get_column_label(self, col_index):
        """
        Convert a column index to an alphabetic label (A, B, C, ..., Z, AA, AB, etc.).

        Args:
            col_index (int): Column index (0-based).

        Returns:
            str: Alphabetic label for the column.
        """
        # For columns beyond Z (index 25), use AA, AB, AC, etc.
        if col_index <= 25:
            return chr(65 + col_index)  # A-Z
        else:
            # For columns beyond Z, use Excel-style labeling (AA, AB, AC, etc.)
            first_letter = chr(65 + ((col_index // 26) - 1))
            second_letter = chr(65 + (col_index % 26))
            return first_letter + second_letter

    def get_state_string(self):
        """
        Get a string representation of the current level state with coordinate labels.

        The coordinate system uses:
        - Columns labeled A-Z (and AA, BB, etc. for larger levels)
        - Rows numbered 1, 2, 3, etc.
        - Origin at the top-left corner

        Returns:
            str: String representation of the level with coordinate labels.
        """
        rows = []

        # Add column headers
        header = '   ' # Space for row numbers
        for x in range(self.width):
            header += self._get_column_label(x)
        rows.append(header)

        # Add a separator line
        separator = '  ' + '+' + '-' * self.width
        rows.append(separator)

        # Add rows with row numbers
        for y in range(self.height):
            row_num = f"{y+1:2d}|"  # Row number with padding and separator
            row_content = ''.join(self.get_display_char(x, y) for x in range(self.width))
            rows.append(row_num + row_content)

        return '\n'.join(rows)

    def reset(self):
        """
        Reset the level to its initial state.
        """
        if self.history:
            # Get the initial state (first move)
            initial_state = self.history[0]
            self.player_pos = initial_state['player_pos']
            self.boxes = initial_state['boxes'].copy()
            self.moves = 0
            self.pushes = 0
            self.history = []
