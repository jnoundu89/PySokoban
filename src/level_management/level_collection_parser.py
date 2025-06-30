"""
Level Collection Parser module for the Sokoban game.

This module handles parsing level collection files that contain multiple levels
with metadata like Title, Description, and Author.

This module now uses the enhanced parser for better format support while
maintaining backward compatibility.
"""

import re
from typing import List, Dict, Optional, Tuple
from src.core.level import Level
from src.level_management.enhanced_level_collection_parser import (
    EnhancedLevelCollection,
    EnhancedLevelCollectionParser,
    LevelMetadata
)


class LevelCollection:
    """
    Class representing a collection of levels with metadata.
    Provides backward compatibility with the original interface.
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
    Parser for level collection files supporting multiple formats.
    Uses the enhanced parser internally while maintaining backward compatibility.
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
            # Use the enhanced parser
            enhanced_collection = EnhancedLevelCollectionParser.parse_file(filepath)
            
            # Convert to backward-compatible format
            collection = LevelCollection(
                title=enhanced_collection.title,
                description=enhanced_collection.description,
                author=enhanced_collection.author
            )
            
            # Add levels with titles from metadata
            for metadata, level in enhanced_collection.levels:
                level_title = metadata.title or "Untitled Level"
                collection.add_level(level_title, level)
            
            return collection
            
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
        # Use the enhanced parser
        enhanced_collection = EnhancedLevelCollectionParser.parse_string(content)
        
        # Convert to backward-compatible format
        collection = LevelCollection(
            title=enhanced_collection.title,
            description=enhanced_collection.description,
            author=enhanced_collection.author
        )
        
        # Add levels with titles from metadata
        for metadata, level in enhanced_collection.levels:
            level_title = metadata.title or "Untitled Level"
            collection.add_level(level_title, level)
        
        return collection
    
    @staticmethod
    def _create_level_from_lines(lines: List[str]) -> Optional[Level]:
        """
        Create a Level object from a list of lines.
        Kept for backward compatibility.
        
        Args:
            lines (List[str]): Lines representing the level
            
        Returns:
            Optional[Level]: Level object or None if invalid
        """
        return EnhancedLevelCollectionParser._create_level_from_lines(lines)
    
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
            # Use enhanced parser for better format support
            info = EnhancedLevelCollectionParser.get_collection_info(filepath)
            
            # Convert to backward-compatible format
            return {
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'author': info.get('author', ''),
                'level_count': info.get('level_count', 0)
            }
        except Exception as e:
            print(f"Warning: Failed to get collection info: {e}")
            return {'title': '', 'description': '', 'author': '', 'level_count': 0}