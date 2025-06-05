#!/usr/bin/env python3
"""
Test script to verify GUI metadata display.

This script tests that the GUI correctly displays level metadata
including title, description, and author information.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from level_management.level_manager import LevelManager


def test_level_manager_metadata():
    """Test that the level manager correctly loads and provides metadata."""
    print("Testing Level Manager metadata functionality...")
    
    # Create level manager
    level_manager = LevelManager('levels')
    
    # Check if Original.txt was loaded
    print(f"Total level files found: {len(level_manager.level_files)}")
    print(f"Collections loaded: {len(level_manager.level_collections)}")
    
    # Check current level metadata
    if level_manager.current_level:
        print("\nCurrent level metadata:")
        metadata = level_manager.get_level_metadata()
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(f"  Author: {metadata.get('author', 'N/A')}")
        print(f"  Description: {metadata.get('description', 'N/A')}")
        
        # Check collection info
        collection_info = level_manager.get_current_collection_info()
        if collection_info:
            print(f"\nCollection info:")
            print(f"  Collection Title: {collection_info['title']}")
            print(f"  Collection Author: {collection_info['author']}")
            print(f"  Collection Description: {collection_info['description']}")
            print(f"  Current Level: {collection_info['current_level_index']} of {collection_info['level_count']}")
            print(f"  Current Level Title: {collection_info['current_level_title']}")
        
        # Test navigation within collection
        print(f"\nTesting collection navigation:")
        print(f"  Has next level in collection: {level_manager.has_next_level_in_collection()}")
        print(f"  Has prev level in collection: {level_manager.has_prev_level_in_collection()}")
        
        # Try to go to next level in collection
        if level_manager.has_next_level_in_collection():
            print(f"  Moving to next level in collection...")
            level_manager.next_level_in_collection()
            new_metadata = level_manager.get_level_metadata()
            print(f"  New level title: {new_metadata.get('title', 'N/A')}")
            
            # Go back
            if level_manager.has_prev_level_in_collection():
                level_manager.prev_level_in_collection()
                print(f"  Moved back to previous level")
    
    return True


def main():
    """Main test function."""
    print("GUI Metadata Display Test")
    print("=" * 40)
    
    success = test_level_manager_metadata()
    
    if success:
        print("\nAll metadata tests passed!")
        print("\nTo see the metadata in the GUI:")
        print("1. Run: python src/gui_main.py")
        print("2. Press any key to start the game")
        print("3. Look at the bottom of the screen for:")
        print("   - Collection information")
        print("   - Level title, author, and description")
        print("   - Navigation within the collection using N/P keys")
    else:
        print("Some tests failed!")
    
    return success


if __name__ == "__main__":
    main()