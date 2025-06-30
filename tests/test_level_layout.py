#!/usr/bin/env python3
"""
Test script to verify the new level layout representation.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.level import Level

def test_level_layout():
    """Test the new level layout representation."""
    print("🎯 Testing Level Layout Representation")
    print("=" * 50)
    
    # Load the Original.txt collection
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ File not found: {original_path}")
        return False
    
    try:
        # Parse the collection
        collection = LevelCollectionParser.parse_file(original_path)
        print(f"📁 Collection: {collection.title}")
        print(f"📊 Total levels: {collection.get_level_count()}")
        
        # Get the first level
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"🎮 Testing Level: {level_title}")
            print(f"📏 Size: {level.width}x{level.height}")
            print(f"📦 Boxes: {len(level.boxes)}")
            print(f"🎯 Targets: {len(level.targets)}")
            
            # Display the level with the new coordinate system
            print("\n📋 Level layout with new coordinate system:")
            print(level.get_state_string())
            
            # Test with a larger level if available
            if collection.get_level_count() > 10:
                level_title, level = collection.get_level(10)
                print(f"\n🎮 Testing Larger Level: {level_title}")
                print(f"📏 Size: {level.width}x{level.height}")
                print(f"📦 Boxes: {len(level.boxes)}")
                print(f"🎯 Targets: {len(level.targets)}")
                
                # Display the level with the new coordinate system
                print("\n📋 Level layout with new coordinate system:")
                print(level.get_state_string())
            
            return True
                
        else:
            print("❌ No levels found in collection")
            return False
            
    except Exception as e:
        print(f"❌ Error loading collection: {e}")
        return False

if __name__ == "__main__":
    success = test_level_layout()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Level layout representation test completed successfully!")
    else:
        print("❌ Level layout representation test failed.")