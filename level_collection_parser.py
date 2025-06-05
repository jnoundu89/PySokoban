"""
Level Collection Parser module for the Sokoban game.

This module provides functionality to parse level collection files that contain
multiple levels in a single file, such as Original.txt which contains 90 levels.
"""

import os


class LevelCollection:
    """
    Class representing a collection of levels from a single file.
    """
    
    def __init__(self, collection_file):
        """
        Initialize a level collection from a file.
        
        Args:
            collection_file (str): Path to a level collection file.
        """
        self.collection_file = collection_file
        self.levels = []
        self.level_titles = []
        self.collection_name = os.path.splitext(os.path.basename(collection_file))[0]
        self.collection_description = ""
        self.collection_author = ""
        
        self._parse_collection()
    
    def _parse_collection(self):
        """
        Parse the level collection file and extract individual levels.
        """
        try:
            with open(self.collection_file, 'r') as file:
                lines = [line.rstrip() for line in file]
            
            # Extract collection metadata from the first lines
            if lines and lines[0].startswith('Title:'):
                self.collection_name = lines[0][6:].strip()
                lines = lines[1:]
            
            if lines and lines[0].startswith('Description:'):
                self.collection_description = lines[0][12:].strip()
                lines = lines[1:]
            
            if lines and lines[0].startswith('Author:'):
                self.collection_author = lines[0][7:].strip()
                lines = lines[1:]
            
            # Parse individual levels
            current_level_lines = []
            current_level_title = "1"  # Default title for the first level
            
            for line in lines:
                if line.startswith('Title:'):
                    # Save the previous level if it exists
                    if current_level_lines:
                        self.levels.append('\n'.join(current_level_lines))
                        self.level_titles.append(current_level_title)
                        current_level_lines = []
                    
                    # Extract the new level title
                    current_level_title = line[6:].strip()
                else:
                    current_level_lines.append(line)
            
            # Add the last level
            if current_level_lines:
                self.levels.append('\n'.join(current_level_lines))
                self.level_titles.append(current_level_title)
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Level collection file not found: {self.collection_file}")
    
    def get_level_count(self):
        """
        Get the number of levels in the collection.
        
        Returns:
            int: The number of levels.
        """
        return len(self.levels)
    
    def get_level(self, index):
        """
        Get a specific level by index.
        
        Args:
            index (int): Index of the level to get.
            
        Returns:
            str: The level data as a string.
            
        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self.levels):
            raise IndexError(f"Level index {index} out of range (0-{len(self.levels) - 1}).")
        
        return self.levels[index]
    
    def get_level_title(self, index):
        """
        Get the title of a specific level by index.
        
        Args:
            index (int): Index of the level to get the title for.
            
        Returns:
            str: The level title.
            
        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self.level_titles):
            raise IndexError(f"Level index {index} out of range (0-{len(self.level_titles) - 1}).")
        
        return self.level_titles[index]


def is_level_collection_file(file_path):
    """
    Check if a file is a level collection file by examining its content.
    
    Args:
        file_path (str): Path to the file to check.
        
    Returns:
        bool: True if the file is a level collection file, False otherwise.
    """
    try:
        with open(file_path, 'r') as file:
            # Read the first few lines to check for collection metadata
            lines = [file.readline().strip() for _ in range(10)]
            
            # Check if the file contains Title: lines which indicate multiple levels
            title_lines = [line for line in lines if line.startswith('Title:')]
            
            # If there are multiple Title: lines, it's likely a collection file
            return len(title_lines) > 1
    except:
        return False
    
    return False