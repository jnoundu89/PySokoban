#!/usr/bin/env python3
"""
Test script for the level collection parser.

This script tests the parsing of the Original.txt file to ensure
the parser correctly extracts metadata and individual levels.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from level_management.level_collection_parser import LevelCollectionParser


def test_original_file():
    """Test parsing the Original.txt file."""
    print("Testing Original.txt file parsing...")
    
    try:
        # Parse the Original.txt file
        collection = LevelCollectionParser.parse_file('levels/Original/Original.txt')
        
        print(f"Collection Title: {collection.title}")
        print(f"Collection Description: {collection.description}")
        print(f"Collection Author: {collection.author}")
        print(f"Number of levels: {collection.get_level_count()}")
        print()
        
        # Test first few levels
        for i in range(min(5, collection.get_level_count())):
            level_title, level = collection.get_level(i)
            print(f"Level {i+1}: {level_title}")
            print(f"  Size: {level.width}x{level.height}")
            print(f"  Boxes: {len(level.boxes)}")
            print(f"  Targets: {len(level.targets)}")
            print(f"  Player position: {level.player_pos}")
            print()
        
        # Test a specific level (level 1)
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print("First level state:")
            print(level.get_state_string())
            print()
        
        return True
        
    except Exception as e:
        print(f"Error parsing Original.txt: {e}")
        return False


def test_collection_info():
    """Test getting collection info without full parsing."""
    print("Testing collection info extraction...")
    
    try:
        info = LevelCollectionParser.get_collection_info('levels/Original/Original.txt')
        print(f"Quick info - Title: {info['title']}")
        print(f"Quick info - Description: {info['description']}")
        print(f"Quick info - Author: {info['author']}")
        print(f"Quick info - Level count: {info['level_count']}")
        print()
        
        return True
        
    except Exception as e:
        print(f"Error getting collection info: {e}")
        return False


def main():
    """Main test function."""
    print("Level Collection Parser Test")
    print("=" * 40)
    
    # Check if Original.txt exists
    if not os.path.exists('../levels/Original/Original.txt'):
        print("Error: levels/Original/Original.txt not found!")
        return False
    
    # Run tests
    success = True
    success &= test_collection_info()
    success &= test_original_file()
    
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    
    return success


if __name__ == "__main__":
    main()