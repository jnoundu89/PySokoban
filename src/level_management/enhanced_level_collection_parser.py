"""
Enhanced Level Collection Parser module for the Sokoban game.

This module handles parsing level collection files in various formats,
automatically detecting the structure and extracting levels with their metadata.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from src.core.level import Level


class LevelMetadata:
    """Class to store metadata for a single level."""
    
    def __init__(self):
        self.title = ""
        self.author = ""
        self.date = ""
        self.comment = ""
        self.extra_fields = {}  # For any additional metadata fields
    
    def add_field(self, key: str, value: str):
        """Add a metadata field."""
        key_lower = key.lower()
        if key_lower == "title":
            self.title = value
        elif key_lower == "author":
            self.author = value
        elif key_lower == "date":
            self.date = value
        elif key_lower == "comment":
            self.comment = value
        else:
            self.extra_fields[key] = value
    
    def to_dict(self) -> Dict[str, str]:
        """Convert metadata to dictionary."""
        result = {
            "title": self.title,
            "author": self.author,
            "date": self.date,
            "comment": self.comment
        }
        result.update(self.extra_fields)
        return result


class EnhancedLevelCollection:
    """Enhanced class representing a collection of levels with metadata."""
    
    def __init__(self, title: str = "", description: str = "", author: str = ""):
        self.title = title
        self.description = description
        self.author = author
        self.collection_metadata = {}  # Additional collection metadata
        self.levels = []  # List of tuples: (LevelMetadata, Level object)
    
    def add_level(self, metadata: LevelMetadata, level: Level):
        """Add a level with its metadata to the collection."""
        self.levels.append((metadata, level))
    
    def get_level_count(self) -> int:
        """Get the number of levels in the collection."""
        return len(self.levels)
    
    def get_level(self, index: int) -> Tuple[LevelMetadata, Level]:
        """Get a level by index."""
        if 0 <= index < len(self.levels):
            return self.levels[index]
        raise IndexError(f"Level index {index} out of range")


class EnhancedLevelCollectionParser:
    """Enhanced parser for level collection files supporting multiple formats."""
    
    # Sokoban game characters
    SOKOBAN_CHARS = set('#@$.*+ ')
    
    # Common metadata field patterns
    METADATA_PATTERNS = [
        r'^(Title|Author|Date|Comment|Description|Collection|Email|Blog|Copyright):\s*(.+)$',
    ]
    
    @staticmethod
    def parse_file(filepath: str) -> EnhancedLevelCollection:
        """Parse a level collection file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            return EnhancedLevelCollectionParser.parse_string(content)
        except FileNotFoundError:
            raise FileNotFoundError(f"Level collection file not found: {filepath}")
    
    @staticmethod
    def parse_string(content: str) -> EnhancedLevelCollection:
        """Parse a level collection from string content."""
        lines = content.split('\n')
        collection = EnhancedLevelCollection()
        
        # Step 1: Parse collection metadata and find where levels start
        level_start_index = EnhancedLevelCollectionParser._parse_collection_metadata(lines, collection)
        
        # Step 2: Find all level blocks using wall structure analysis
        level_blocks = EnhancedLevelCollectionParser._find_level_blocks(lines[level_start_index:])
        
        # Step 3: Parse each level block
        for level_lines, start_line_idx in level_blocks:
            # Look for metadata after this level
            metadata = EnhancedLevelCollectionParser._find_metadata_for_level(
                lines, level_start_index + start_line_idx, len(level_lines)
            )
            
            # Create level object
            level = EnhancedLevelCollectionParser._create_level_from_lines(level_lines)
            if level:
                collection.add_level(metadata, level)
        
        return collection
    
    @staticmethod
    def _parse_collection_metadata(lines: List[str], collection: EnhancedLevelCollection) -> int:
        """Parse collection-level metadata and return the index where levels start."""
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments (but not level lines that start with #)
            if not line or line.startswith(';'):
                i += 1
                continue
            
            # Skip comment lines that start with # but are clearly comments (not level content)
            if line.startswith('#') and not EnhancedLevelCollectionParser._looks_like_level_content(line):
                i += 1
                continue
            
            # Check if this line looks like level content first
            if EnhancedLevelCollectionParser._looks_like_level_content(line):
                return i
            
            # Check if this line contains metadata
            metadata_found = False
            for pattern in EnhancedLevelCollectionParser.METADATA_PATTERNS:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    field_name = match.group(1).strip()
                    field_value = match.group(2).strip()
                    
                    # Handle collection-level metadata
                    if field_name.lower() == "title" and not collection.title:
                        collection.title = field_value
                    elif field_name.lower() == "description":
                        collection.description = field_value
                    elif field_name.lower() == "author" and not collection.author:
                        collection.author = field_value
                    else:
                        collection.collection_metadata[field_name] = field_value
                    
                    metadata_found = True
                    break
            
            if metadata_found:
                i += 1
                continue
            
            # Check if this is a separator line (like ::::::::::)
            if re.match(r'^[:=\-#]{5,}$', line):
                i += 1
                continue
            
            # If we can't categorize this line, assume levels start here
            return i
        
        return i
    
    @staticmethod
    def _looks_like_level_content(line: str) -> bool:
        """Check if a line looks like it contains level content."""
        if not line:
            return False
        
        # Check if line contains sokoban characters
        sokoban_char_count = sum(1 for c in line if c in EnhancedLevelCollectionParser.SOKOBAN_CHARS)
        
        # If more than 30% of characters are sokoban characters, it's likely level content
        if len(line) > 0 and sokoban_char_count / len(line) > 0.3:
            return True
        
        # Check for typical level patterns (walls, etc.)
        if re.search(r'#{3,}', line):  # Multiple consecutive walls
            return True
        
        return False
    
    @staticmethod
    def _is_wall_line(line: str) -> bool:
        """Check if a line is composed exclusively of walls and spaces."""
        if not line.strip():
            return False
        # Line should contain only walls (#) and spaces
        return all(c in '# ' for c in line) and '#' in line
    
    @staticmethod
    def _find_level_blocks(lines: List[str]) -> List[Tuple[List[str], int]]:
        """Find all level blocks in the lines using wall structure analysis."""
        level_blocks = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and metadata
            if not line or EnhancedLevelCollectionParser._is_metadata_line(line):
                i += 1
                continue
            
            # Check if this looks like the start of a level (wall line)
            if EnhancedLevelCollectionParser._is_wall_line(line):
                level_start = i
                level_lines = [lines[i].rstrip()]
                i += 1
                
                # Collect all lines until we find the end wall line
                while i < len(lines):
                    current_line = lines[i]
                    current_line_stripped = current_line.strip()
                    
                    # If we hit metadata, this level is done
                    if EnhancedLevelCollectionParser._is_metadata_line(current_line_stripped):
                        break
                    
                    # If empty line, check if next line starts a new level
                    if not current_line_stripped:
                        # Look ahead to see if next non-empty line is a new level start
                        next_i = i + 1
                        while next_i < len(lines) and not lines[next_i].strip():
                            next_i += 1
                        
                        if (next_i < len(lines) and
                            EnhancedLevelCollectionParser._is_wall_line(lines[next_i].strip())):
                            # This empty line separates levels
                            break
                        
                        # Otherwise, add the empty line and continue
                        level_lines.append(current_line.rstrip())
                    else:
                        # Add non-empty line
                        level_lines.append(current_line.rstrip())
                    
                    i += 1
                
                # Clean up the level lines and validate
                level_lines = EnhancedLevelCollectionParser._clean_level_lines(level_lines)
                
                if level_lines and EnhancedLevelCollectionParser._is_valid_level(level_lines):
                    level_blocks.append((level_lines, level_start))
            else:
                i += 1
        
        return level_blocks
    
    @staticmethod
    def _is_metadata_line(line: str) -> bool:
        """Check if a line is a metadata line."""
        if not line:
            return False
        
        for pattern in EnhancedLevelCollectionParser.METADATA_PATTERNS:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _looks_like_new_level_start(line: str, current_level_lines: List[str]) -> bool:
        """Check if a line looks like the start of a new level."""
        if not current_level_lines:
            return True
        
        # Only consider it a new level if:
        # 1. The line starts with multiple walls (like ######)
        # 2. AND we have a substantial current level (at least 8 lines)
        # 3. AND the current level appears to be complete (ends with walls)
        if re.match(r'^#{4,}', line) and len(current_level_lines) >= 8:
            # Check if the last few lines of current level look like an ending
            last_lines = [l.strip() for l in current_level_lines[-3:] if l.strip()]
            if last_lines and any('#' in l for l in last_lines):
                # Check if current level has a reasonable rectangular structure
                non_empty_lines = [l for l in current_level_lines if l.strip()]
                if len(non_empty_lines) >= 5:
                    return True
        
        return False
    
    @staticmethod
    def _clean_level_lines(lines: List[str]) -> List[str]:
        """Clean level lines by removing empty lines from start and end."""
        if not lines:
            return []
        
        # Make a copy to avoid modifying the original
        cleaned = lines.copy()
        
        # Remove empty lines from the beginning
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        
        # Remove empty lines from the end
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()
        
        return cleaned
    
    @staticmethod
    def _is_valid_level(lines: List[str]) -> bool:
        """Check if the lines represent a valid level."""
        if not lines:
            return False
        
        level_content = '\n'.join(lines)
        
        # Must contain walls
        if '#' not in level_content:
            return False
        
        # Must have some sokoban characters
        sokoban_chars = sum(1 for c in level_content if c in EnhancedLevelCollectionParser.SOKOBAN_CHARS)
        if sokoban_chars < 5:  # Minimum threshold
            return False
        
        # Should have rectangular-ish structure
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) < 3:
            return False
        
        return True
    
    @staticmethod
    def _find_metadata_for_level(lines: List[str], level_start: int, level_length: int) -> LevelMetadata:
        """Find metadata associated with a level."""
        metadata = LevelMetadata()
        
        # Look for metadata after the level
        search_start = level_start + level_length
        search_end = min(search_start + 10, len(lines))  # Look at next 10 lines max
        
        for i in range(search_start, search_end):
            if i >= len(lines):
                break
            
            line = lines[i].strip()
            if not line:
                continue
            
            # If we hit another level, stop looking
            if EnhancedLevelCollectionParser._looks_like_level_content(line):
                break
            
            # Check if this is metadata
            for pattern in EnhancedLevelCollectionParser.METADATA_PATTERNS:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    field_name = match.group(1).strip()
                    field_value = match.group(2).strip()
                    metadata.add_field(field_name, field_value)
                    break
        
        return metadata
    
    @staticmethod
    def _create_level_from_lines(lines: List[str]) -> Optional[Level]:
        """Create a Level object from a list of lines."""
        if not lines:
            return None
        
        try:
            level_content = '\n'.join(lines)
            return Level(level_data=level_content)
        except Exception as e:
            print(f"Warning: Failed to parse level: {e}")
            return None
    
    @staticmethod
    def get_collection_info(filepath: str) -> Dict[str, Any]:
        """Get basic information about a level collection without parsing all levels."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            lines = content.split('\n')
            collection = EnhancedLevelCollection()
            
            # Parse collection metadata
            level_start_index = EnhancedLevelCollectionParser._parse_collection_metadata(lines, collection)
            
            # Count levels by finding level blocks
            level_blocks = EnhancedLevelCollectionParser._find_level_blocks(lines[level_start_index:])
            level_count = len(level_blocks)
            
            return {
                'title': collection.title,
                'description': collection.description,
                'author': collection.author,
                'level_count': level_count,
                'collection_metadata': collection.collection_metadata
            }
        except Exception as e:
            print(f"Warning: Failed to get collection info: {e}")
            return {'title': '', 'description': '', 'author': '', 'level_count': 0, 'collection_metadata': {}}


# Backward compatibility - create aliases for the original classes
LevelCollection = EnhancedLevelCollection
LevelCollectionParser = EnhancedLevelCollectionParser