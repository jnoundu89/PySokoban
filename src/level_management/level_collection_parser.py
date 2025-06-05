"""
Level Collection Parser module for the Sokoban game.

This module handles parsing level collection files that contain multiple levels
with metadata like Title, Description, and Author.
"""

import re
from typing import List, Dict, Optional, Tuple
from src.core.level import Level


class LevelCollection:
    """
    Class representing a collection of levels with metadata.
    """
    
    def __init__(self, title: str = "", description: str = "", author: str = ""):
        """
        Initialize a level collection.
        
        Args:
            title (str): Collection title
            description (str): Collection description  
            author (str): Collection author
        """
        self.title = title
        self.description = description
        self.author = author
        self.levels = []  # List of tuples: (level_title, Level object)
    
    def add_level(self, level_title: str, level: Level):
        """
        Add a level to the collection.
        
        Args:
            level_title (str): Title of the level
            level (Level): Level object
        """
        self.levels.append((level_title, level))
    
    def get_level_count(self) -> int:
        """
        Get the number of levels in the collection.
        
        Returns:
            int: Number of levels
        """
        return len(self.levels)
    
    def get_level(self, index: int) -> Tuple[str, Level]:
        """
        Get a level by index.
        
        Args:
            index (int): Level index
            
        Returns:
            Tuple[str, Level]: Level title and Level object
            
        Raises:
            IndexError: If index is out of range
        """
        if 0 <= index < len(self.levels):
            return self.levels[index]
        raise IndexError(f"Level index {index} out of range")


class LevelCollectionParser:
    """
    Parser for level collection files in the Original.txt format.
    """
    
    @staticmethod
    def parse_file(filepath: str) -> LevelCollection:
        """
        Parse a level collection file.
        
        Args:
            filepath (str): Path to the level collection file
            
        Returns:
            LevelCollection: Parsed level collection
            
        Raises:
            FileNotFoundError: If the file cannot be found
            ValueError: If the file format is invalid
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return LevelCollectionParser.parse_string(content)
        except FileNotFoundError:
            raise FileNotFoundError(f"Level collection file not found: {filepath}")
    
    @staticmethod
    def parse_string(content: str) -> LevelCollection:
        """
        Parse a level collection from string content.
        
        Args:
            content (str): File content as string
            
        Returns:
            LevelCollection: Parsed level collection
        """
        lines = content.split('\n')
        collection = LevelCollection()
        
        # Parse collection metadata from the beginning
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('Title:'):
                collection.title = line[6:].strip()
            elif line.startswith('Description:'):
                collection.description = line[12:].strip()
            elif line.startswith('Author:'):
                collection.author = line[7:].strip()
            elif line == '' or line.startswith('#'):
                # Found the start of the first level
                break
            
            i += 1
        
        # Parse individual levels
        current_level_lines = []
        current_level_title = ""
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a level title line
            title_match = re.match(r'^Title:\s*(.+)$', line.strip())
            if title_match:
                # Save previous level if it exists
                if current_level_lines:
                    level = LevelCollectionParser._create_level_from_lines(current_level_lines)
                    if level:
                        collection.add_level(current_level_title, level)
                
                # Start new level
                current_level_title = title_match.group(1).strip()
                current_level_lines = []
            else:
                # Add line to current level (skip empty lines at the start)
                if line.strip() or current_level_lines:
                    # Preserve leading spaces but remove trailing spaces
                    current_level_lines.append(line.rstrip())
            
            i += 1
        
        # Add the last level
        if current_level_lines:
            level = LevelCollectionParser._create_level_from_lines(current_level_lines)
            if level:
                collection.add_level(current_level_title, level)
        
        return collection
    
    @staticmethod
    def _create_level_from_lines(lines: List[str]) -> Optional[Level]:
        """
        Create a Level object from a list of lines.
        
        Args:
            lines (List[str]): Lines representing the level
            
        Returns:
            Optional[Level]: Level object or None if invalid
        """
        # Remove empty lines from the beginning and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        
        if not lines:
            return None
        
        # Check if this looks like a valid level (contains game characters)
        level_chars = set('#@$.*+ ')
        has_level_chars = any(any(c in level_chars for c in line) for line in lines)
        
        if not has_level_chars:
            return None
        
        try:
            # Join lines preserving original spacing
            level_string = '\n'.join(lines)
            return Level(level_data=level_string)
        except Exception as e:
            print(f"Warning: Failed to parse level: {e}")
            return None
    
    @staticmethod
    def get_collection_info(filepath: str) -> Dict[str, str]:
        """
        Get basic information about a level collection without parsing all levels.
        
        Args:
            filepath (str): Path to the level collection file
            
        Returns:
            Dict[str, str]: Dictionary with title, description, author, and level_count
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            info = {
                'title': '',
                'description': '',
                'author': '',
                'level_count': 0
            }
            
            lines = content.split('\n')
            
            # Parse metadata
            for line in lines:
                line = line.strip()
                if line.startswith('Title:'):
                    info['title'] = line[6:].strip()
                elif line.startswith('Description:'):
                    info['description'] = line[12:].strip()
                elif line.startswith('Author:'):
                    info['author'] = line[7:].strip()
            
            # Count levels by counting "Title: " lines (excluding the first collection title)
            title_lines = [line for line in lines if re.match(r'^Title:\s*\d+', line.strip())]
            info['level_count'] = len(title_lines)
            
            return info
        except Exception as e:
            print(f"Warning: Failed to get collection info: {e}")
            return {'title': '', 'description': '', 'author': '', 'level_count': 0}