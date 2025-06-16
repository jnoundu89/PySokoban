"""
FESS Solution Notation Module

This module implements the Feature Space Search (FESS) algorithm notation for Sokoban solutions.
Based on the research paper: "The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
by Yaron Shoham and Jonathan Schaeffer.

The FESS notation represents solutions as macro moves, where each macro move describes
the movement of a box from one position to another, conceptualizing the solution at a higher level.
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class MacroMoveType(Enum):
    """Types of macro moves based on their strategic purpose."""
    PREPARING_PATH = "preparing a path"
    OPENING_ROOM = "opening the room"
    OPENING_PATH = "opening a path"
    PACKING_BOX = "packing a box"
    CONNECTING_AREAS = "connecting areas"
    CLEARING_OBSTRUCTION = "clearing obstruction"

@dataclass
class MacroMove:
    """
    Represents a macro move in FESS notation.
    
    A macro move is a sequence of moves that push the same box from one position
    to another without pushing any other box in between.
    """
    start_pos: Tuple[int, int]  # (x, y) coordinates
    end_pos: Tuple[int, int]    # (x, y) coordinates
    move_type: MacroMoveType
    description: str
    push_count: int = 1  # Number of individual pushes in this macro move
    
    def to_coordinate_notation(self) -> str:
        """
        Convert positions to alphabetic coordinate notation (A1, B2, etc.).
        
        Returns:
            str: Coordinate notation like "(H,5)-(G,5)"
        """
        start_col = chr(65 + self.start_pos[0])  # Convert x to A, B, C, etc.
        start_row = self.start_pos[1] + 1        # Convert y to 1-based indexing
        end_col = chr(65 + self.end_pos[0])
        end_row = self.end_pos[1] + 1
        
        return f"({start_col},{start_row})-({end_col},{end_row})"
    
    def __str__(self) -> str:
        """String representation of the macro move."""
        return f"{self.to_coordinate_notation()}, {self.description}"
    
    def __eq__(self, other) -> bool:
        """Equality comparison for macro moves."""
        if not isinstance(other, MacroMove):
            return False
        return (self.start_pos == other.start_pos and
                self.end_pos == other.end_pos and
                self.move_type == other.move_type)
    
    def __hash__(self) -> int:
        """Hash function to make MacroMove hashable for use in sets."""
        return hash((self.start_pos, self.end_pos, self.move_type))
    
    def apply_to_state(self, state):
        """
        Applique ce macro move à un état et retourne le nouvel état.
        
        Args:
            state: État Sokoban actuel (SokobanState)
            
        Returns:
            SokobanState: Nouvel état après application du move
        """
        # Crée une copie de l'état
        new_box_positions = list(state.box_positions)
        
        # Trouve l'index de la boîte à déplacer
        try:
            box_index = new_box_positions.index(self.start_pos)
            # Déplace la boîte
            new_box_positions[box_index] = self.end_pos
        except ValueError:
            # La boîte n'est pas à la position de départ
            # Retourne l'état original
            return state
        
        # Calcule la nouvelle position du joueur
        # Le joueur finit à la position d'où la boîte a été poussée
        new_player_position = self.start_pos
        
        # Importe SokobanState ici pour éviter les imports circulaires
        from src.core.sokoban_state import SokobanState
        
        # Crée le nouvel état
        new_state = SokobanState(
            player_position=new_player_position,
            box_positions=tuple(new_box_positions)
        )
        
        return new_state

class FESSSolutionNotation:
    """
    Generates and manages FESS notation for Sokoban solutions.
    
    This class analyzes a sequence of moves and converts them into macro moves,
    providing a high-level strategic view of the solution.
    """
    
    def __init__(self, level_width: int, level_height: int):
        """
        Initialize the FESS notation system.
        
        Args:
            level_width (int): Width of the level
            level_height (int): Height of the level
        """
        self.level_width = level_width
        self.level_height = level_height
        self.macro_moves: List[MacroMove] = []
    
    def _get_column_label(self, col_index: int) -> str:
        """
        Convert a column index to an alphabetic label.
        
        Args:
            col_index (int): Column index (0-based)
            
        Returns:
            str: Alphabetic label (A, B, C, ..., Z, AA, AB, etc.)
        """
        if col_index <= 25:
            return chr(65 + col_index)  # A-Z
        else:
            # For columns beyond Z, use Excel-style labeling
            first_letter = chr(65 + ((col_index // 26) - 1))
            second_letter = chr(65 + (col_index % 26))
            return first_letter + second_letter
    
    def coordinate_to_notation(self, x: int, y: int) -> str:
        """
        Convert x,y coordinates to FESS notation.
        
        Args:
            x (int): X coordinate (0-based)
            y (int): Y coordinate (0-based)
            
        Returns:
            str: Coordinate in notation format (e.g., "H5")
        """
        col_label = self._get_column_label(x)
        row_label = str(y + 1)  # Convert to 1-based indexing
        return f"{col_label}{row_label}"
    
    def notation_to_coordinate(self, notation: str) -> Tuple[int, int]:
        """
        Convert FESS notation to x,y coordinates.
        
        Args:
            notation (str): Coordinate notation (e.g., "H5")
            
        Returns:
            Tuple[int, int]: (x, y) coordinates (0-based)
        """
        # Extract column letters and row number
        col_letters = ""
        row_str = ""
        
        for char in notation:
            if char.isalpha():
                col_letters += char
            else:
                row_str += char
        
        # Convert column letters to index
        if len(col_letters) == 1:
            x = ord(col_letters[0]) - 65  # A=0, B=1, etc.
        else:
            # Handle AA, AB, etc.
            x = (ord(col_letters[0]) - 64) * 26 + (ord(col_letters[1]) - 65)
        
        # Convert row to 0-based index
        y = int(row_str) - 1
        
        return (x, y)
    
    def add_macro_move(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                      move_type: MacroMoveType, description: str, push_count: int = 1):
        """
        Add a macro move to the solution notation.
        
        Args:
            start_pos: Starting position (x, y)
            end_pos: Ending position (x, y)
            move_type: Type of macro move
            description: Description of the move's purpose
            push_count: Number of individual pushes
        """
        macro_move = MacroMove(start_pos, end_pos, move_type, description, push_count)
        self.macro_moves.append(macro_move)
    
    def get_solution_notation(self, total_pushes: int, total_moves: int) -> str:
        """
        Generate the complete FESS solution notation.
        
        Args:
            total_pushes (int): Total number of pushes in the solution
            total_moves (int): Total number of player moves in the solution
            
        Returns:
            str: Complete solution notation
        """
        if not self.macro_moves:
            return "No macro moves recorded."
        
        lines = []
        lines.append(f"FESS Solution Notation ({total_pushes} pushes; {total_moves} player moves):")
        lines.append("=" * 60)
        
        for i, macro_move in enumerate(self.macro_moves, 1):
            lines.append(f"• {macro_move}")
        
        lines.append("")
        lines.append(f"Total macro moves: {len(self.macro_moves)}")
        lines.append(f"Average pushes per macro move: {total_pushes / len(self.macro_moves):.1f}")
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear all recorded macro moves."""
        self.macro_moves.clear()

class FESSLevelAnalyzer:
    """
    Analyzes Sokoban levels to identify strategic macro moves.
    
    This class implements the feature-based analysis described in the FESS algorithm
    to identify and categorize macro moves based on their strategic purpose.
    """
    
    def __init__(self, level):
        """
        Initialize the analyzer with a level.
        
        Args:
            level: Sokoban level object
        """
        self.level = level
        self.notation = FESSSolutionNotation(level.width, level.height)
    
    def create_original_level1_notation(self) -> FESSSolutionNotation:
        """
        Create the FESS notation for Original Level 1 as described in the research paper.
        
        This represents the example solution from the paper:
        97 pushes; 250 player moves conceptualized as 9 macro moves.
        
        Returns:
            FESSSolutionNotation: The notation for Original Level 1
        """
        self.notation.clear()
        
        # According to the research paper, Original Level 1 solution:
        self.notation.add_macro_move(
            (7, 4), (6, 4),  # H5 to G5 (converting from 1-based to 0-based)
            MacroMoveType.PREPARING_PATH,
            "preparing a path to the upper room"
        )
        
        self.notation.add_macro_move(
            (7, 3), (7, 2),  # H4 to H3
            MacroMoveType.OPENING_ROOM,
            "opening the upper room"
        )
        
        self.notation.add_macro_move(
            (5, 4), (5, 6),  # F5 to F7
            MacroMoveType.OPENING_PATH,
            "opening a path to the left room"
        )
        
        self.notation.add_macro_move(
            (5, 7), (17, 6),  # F8 to R7
            MacroMoveType.PACKING_BOX,
            "packing a box"
        )
        
        self.notation.add_macro_move(
            (2, 7), (17, 7),  # C8 to R8
            MacroMoveType.PACKING_BOX,
            "packing a box"
        )
        
        self.notation.add_macro_move(
            (5, 6), (17, 8),  # F7 to R9
            MacroMoveType.PACKING_BOX,
            "packing a box"
        )
        
        self.notation.add_macro_move(
            (6, 4), (16, 6),  # G5 to Q7
            MacroMoveType.PACKING_BOX,
            "packing a box"
        )
        
        self.notation.add_macro_move(
            (5, 2), (16, 7),  # F3 to Q8
            MacroMoveType.PACKING_BOX,
            "packing a box"
        )
        
        self.notation.add_macro_move(
            (7, 2), (16, 8),  # H3 to Q9
            MacroMoveType.PACKING_BOX,
            "packing a box"
        )
        
        return self.notation
    
    def analyze_solution_moves(self, moves_history: List[Tuple[int, int]]) -> FESSSolutionNotation:
        """
        Analyze a sequence of moves and extract macro moves.
        
        Args:
            moves_history: List of (dx, dy) move directions
            
        Returns:
            FESSSolutionNotation: The analyzed solution notation
        """
        # This would implement the actual analysis of move sequences
        # to extract macro moves. For now, we return the notation object.
        return self.notation
    
    def get_features_analysis(self) -> Dict[str, int]:
        """
        Analyze the current level state using FESS features.
        
        Returns:
            Dict[str, int]: Feature values (packing, connectivity, room_connectivity, out_of_plan)
        """
        features = {
            'packing': len([box for box in self.level.boxes if box in self.level.targets]),
            'connectivity': self._calculate_connectivity(),
            'room_connectivity': self._calculate_room_connectivity(),
            'out_of_plan': self._calculate_out_of_plan()
        }
        return features
    
    def _calculate_connectivity(self) -> int:
        """
        Calculate the connectivity feature: number of disconnected regions.
        
        Returns:
            int: Number of regions the board is divided into by boxes
        """
        # Simplified implementation - in practice this would be more complex
        return 1
    
    def _calculate_room_connectivity(self) -> int:
        """
        Calculate room connectivity: number of room links obstructed by boxes.
        
        Returns:
            int: Number of obstructed room connections
        """
        # Simplified implementation
        return 0
    
    def _calculate_out_of_plan(self) -> int:
        """
        Calculate out-of-plan feature: boxes in soon-to-be-blocked areas.
        
        Returns:
            int: Number of boxes in problematic positions
        """
        # Simplified implementation
        return 0
    
    def generate_macro_moves(self, state) -> List[MacroMove]:
        """
        Génère les macro moves possibles depuis un état donné.
        
        Args:
            state: État Sokoban actuel (SokobanState)
            
        Returns:
            List[MacroMove]: Liste des macro moves possibles
        """
        macro_moves = []
        
        # Calcule les positions accessibles au joueur
        player_reachable = self._find_reachable_positions(
            state.player_position,
            set(state.box_positions) | self._get_walls()
        )
        
        # Pour chaque boîte, génère les macro moves possibles
        for box_pos in state.box_positions:
            x, y = box_pos
            
            # Directions possibles pour pousser la boîte
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                push_from_x, push_from_y = x - dx, y - dy
                
                # Vérifie si la destination est valide
                if not self._is_valid_position(new_x, new_y, state.box_positions):
                    continue
                
                # Vérifie si le joueur peut atteindre la position de poussée
                if not self._is_valid_position(push_from_x, push_from_y, state.box_positions):
                    continue
                
                if (push_from_x, push_from_y) not in player_reachable:
                    continue
                
                # Détermine le type de move
                move_type = self._determine_move_type(box_pos, (new_x, new_y))
                
                # Crée un macro move
                macro_move = MacroMove(
                    start_pos=box_pos,
                    end_pos=(new_x, new_y),
                    move_type=move_type,
                    description=f"push box {move_type.value}",
                    push_count=1
                )
                macro_moves.append(macro_move)
        
        return macro_moves
    
    def _find_reachable_positions(self, start_pos: Tuple[int, int],
                                 obstacles: set) -> set:
        """Trouve toutes les positions atteignables depuis une position de départ."""
        from collections import deque
        
        reachable = set()
        queue = deque([start_pos])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in reachable or (x, y) in obstacles:
                continue
            if not (0 <= x < self.level.width and 0 <= y < self.level.height):
                continue
            if self.level.is_wall(x, y):
                continue
            
            reachable.add((x, y))
            
            # Ajoute les voisins
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in reachable:
                    queue.append((nx, ny))
        
        return reachable
    
    def _get_walls(self) -> set:
        """Retourne l'ensemble des positions des murs."""
        walls = set()
        for y in range(self.level.height):
            for x in range(self.level.width):
                if self.level.is_wall(x, y):
                    walls.add((x, y))
        return walls
    
    def _is_valid_position(self, x: int, y: int, box_positions: tuple) -> bool:
        """Vérifie si une position est valide (pas mur, pas boîte, dans les limites)."""
        if not (0 <= x < self.level.width and 0 <= y < self.level.height):
            return False
        if self.level.is_wall(x, y):
            return False
        if (x, y) in box_positions:
            return False
        return True
    
    def _determine_move_type(self, start_pos: Tuple[int, int],
                           end_pos: Tuple[int, int]) -> MacroMoveType:
        """Détermine le type de macro move basé sur les positions."""
        # Si la destination est un target, c'est du packing
        if self.level.is_target(end_pos[0], end_pos[1]):
            return MacroMoveType.PACKING_BOX
        
        # Sinon, c'est probablement pour préparer un chemin
        return MacroMoveType.PREPARING_PATH

def demo_fess_notation():
    """Demonstrate the FESS notation system with Original Level 1."""
    # Create a dummy level analyzer
    class DummyLevel:
        def __init__(self):
            self.width = 20
            self.height = 15
            self.boxes = []
            self.targets = []
    
    level = DummyLevel()
    analyzer = FESSLevelAnalyzer(level)
    
    # Create the Original Level 1 notation
    notation = analyzer.create_original_level1_notation()
    
    # Display the notation
    print(notation.get_solution_notation(97, 250))
    
    # Display coordinate conversion examples
    print("\nCoordinate Conversion Examples:")
    print(f"(7,4) -> {notation.coordinate_to_notation(7, 4)}")
    print(f"H5 -> {notation.notation_to_coordinate('H5')}")

if __name__ == "__main__":
    demo_fess_notation()