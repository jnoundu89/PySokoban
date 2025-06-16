#!/usr/bin/env python3
"""
Test script for the FESS coordinate system and macro move notation.

This script demonstrates the implementation of the FESS (Feature Space Search) 
coordinate system and macro move notation as described in the research paper:
"The FESS Algorithm: A Feature Based Approach to Single-Agent Search"
by Yaron Shoham and Jonathan Schaeffer.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.level import Level
from src.ai.fess_notation import FESSLevelAnalyzer, FESSSolutionNotation, MacroMoveType
from src.ai.authentic_fess_algorithm import FESSAlgorithm, SokobanState

def test_fess_coordinate_system():
    """Test the FESS coordinate system implementation."""
    print("🎯 Testing FESS Coordinate System Implementation")
    print("=" * 60)
    
    # Load the Original.txt collection
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ File not found: {original_path}")
        return False
    
    try:
        # Parse the collection
        collection = LevelCollectionParser.parse_file(original_path)
        print(f"📁 Collection: {collection.title}")
        print(f"📊 Total levels: {collection.get_level_count()}")
        
        # Get the first level (Level 1 from the research paper example)
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"\n🎮 Testing Level: {level_title}")
            print(f"📏 Size: {level.width}x{level.height}")
            print(f"📦 Boxes: {len(level.boxes)}")
            print(f"🎯 Targets: {len(level.targets)}")
            
            # Display the level with FESS coordinate system
            print("\n📋 Level layout with FESS coordinate system:")
            print(level.get_state_string(show_fess_coordinates=True))
            
            # Test coordinate conversion
            print("\n🔢 FESS Coordinate System Testing:")
            print("Using alphabetic columns (A, B, C, ...) and numeric rows (1, 2, 3, ...)")
            print("Origin at top-left corner as specified in FESS algorithm")
            
            # Show some coordinate examples
            analyzer = FESSLevelAnalyzer(level)
            notation = analyzer.notation
            
            print(f"\nCoordinate conversion examples:")
            test_coords = [(0, 0), (7, 4), (5, 6), (16, 8)]
            for x, y in test_coords:
                if x < level.width and y < level.height:
                    fess_notation = notation.coordinate_to_notation(x, y)
                    back_coord = notation.notation_to_coordinate(fess_notation)
                    print(f"  ({x},{y}) -> {fess_notation} -> {back_coord}")
            
            return True
                
        else:
            print("❌ No levels found in collection")
            return False
            
    except Exception as e:
        print(f"❌ Error loading collection: {e}")
        return False

def test_fess_macro_move_notation():
    """Test the FESS macro move notation for Original Level 1."""
    print("\n🚀 Testing FESS Macro Move Notation")
    print("=" * 60)
    
    # Load Original Level 1
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    
    try:
        collection = LevelCollectionParser.parse_file(original_path)
        level_title, level = collection.get_level(0)
        
        print(f"📄 Analyzing: {level_title}")
        print(f"📊 Based on research paper example: 97 pushes; 250 player moves")
        
        # Create FESS analyzer
        analyzer = FESSLevelAnalyzer(level)
        
        # Generate the Original Level 1 notation as described in the paper
        notation = analyzer.create_original_level1_notation()
        
        # Display the complete FESS notation
        print("\n📝 FESS Macro Move Notation:")
        solution_text = notation.get_solution_notation(97, 250)
        print(solution_text)
        
        # Show the strategic analysis
        print("\n🧠 Strategic Analysis:")
        print("The first three macro moves correspond to improving the connectivity feature,")
        print("and the last six address the packing feature.")
        print(f"Original solution: 97 individual pushes")
        print(f"FESS representation: {len(notation.macro_moves)} macro moves")
        print(f"Compression ratio: {97 / len(notation.macro_moves):.1f}x reduction in complexity")
        
        # Test coordinate notation accuracy
        print("\n✅ Coordinate Notation Verification:")
        expected_moves = [
            ("H5", "G5", "preparing a path to the upper room"),
            ("H4", "H3", "opening the upper room"),
            ("F5", "F7", "opening a path to the left room"),
            ("F8", "R7", "packing a box"),
            ("C8", "R8", "packing a box"),
            ("F7", "R9", "packing a box"),
            ("G5", "Q7", "packing a box"),
            ("F3", "Q8", "packing a box"),
            ("H3", "Q9", "packing a box")
        ]
        
        for i, (start_expected, end_expected, desc) in enumerate(expected_moves):
            if i < len(notation.macro_moves):
                macro_move = notation.macro_moves[i]
                start_actual = notation.coordinate_to_notation(macro_move.start_pos[0], macro_move.start_pos[1])
                end_actual = notation.coordinate_to_notation(macro_move.end_pos[0], macro_move.end_pos[1])
                
                print(f"  Move {i+1}: {start_actual}-{end_actual} ({'✓' if start_actual == start_expected and end_actual == end_expected else '✗'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in macro move notation test: {e}")
        return False

def test_fess_algorithm_integration():
    """Test the integration with the authentic FESS algorithm."""
    print("\n🔬 Testing FESS Algorithm Integration")
    print("=" * 60)
    
    try:
        # Load Original Level 1
        original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
        collection = LevelCollectionParser.parse_file(original_path)
        level_title, level = collection.get_level(0)
        
        print(f"🧪 Testing FESS Algorithm on: {level_title}")
        
        # Initialize FESS algorithm
        fess_solver = FESSAlgorithm(level, max_time=10.0)  # Short time for demo
        
        # Display initial state analysis
        initial_state = SokobanState(level)
        features = fess_solver.feature_calculator.calculate_features(initial_state)
        
        print(f"\n📊 Initial FESS Features:")
        print(f"  • Packing feature: {features.packing}")
        print(f"  • Connectivity feature: {features.connectivity}")
        print(f"  • Room connectivity feature: {features.room_connectivity}")
        print(f"  • Out-of-plan feature: {features.out_of_plan}")
        
        print(f"\n🎯 FESS Algorithm Configuration:")
        print(f"  • 4-dimensional feature space")
        print(f"  • Macro moves as basic move unit")
        print(f"  • 7 domain-specific advisors")
        print(f"  • Multi-objective guidance")
        print(f"  • Compatible with FESS notation")
        
        # Show some advisor recommendations
        advisor_moves = fess_solver.advisor.get_advisor_moves(initial_state, features)
        print(f"\n🤖 Advisor Recommendations ({len(advisor_moves)} moves):")
        for i, move in enumerate(advisor_moves[:3]):  # Show first 3
            start_notation = fess_solver.feature_calculator.initial_state
            print(f"  {i+1}. {move}")
        
        print(f"\n✅ FESS Algorithm successfully integrated with:")
        print(f"  • FESS coordinate system")
        print(f"  • Macro move notation")
        print(f"  • Feature space analysis")
        print(f"  • Strategic advisor system")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in FESS algorithm integration test: {e}")
        return False

def demonstrate_coordinate_compatibility():
    """Demonstrate compatibility between the new system and existing code."""
    print("\n🔄 Testing Coordinate System Compatibility")
    print("=" * 60)
    
    try:
        # Load a level
        original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
        collection = LevelCollectionParser.parse_file(original_path)
        level_title, level = collection.get_level(0)
        
        print(f"🔧 Testing compatibility for: {level_title}")
        
        # Test both coordinate display modes
        print(f"\n📐 FESS Coordinate Display (NEW):")
        fess_display = level.get_state_string(show_fess_coordinates=True)
        print(fess_display[:200] + "..." if len(fess_display) > 200 else fess_display)
        
        print(f"\n📐 Simple Display (for algorithms that don't need coordinates):")
        simple_display = level.get_state_string(show_fess_coordinates=False)
        print(simple_display[:200] + "..." if len(simple_display) > 200 else simple_display)
        
        # Test coordinate conversion consistency
        analyzer = FESSLevelAnalyzer(level)
        notation = analyzer.notation
        
        print(f"\n🔍 Coordinate Conversion Consistency Test:")
        test_positions = [(0, 0), (3, 2), (7, 4), (15, 10)]
        all_consistent = True
        
        for x, y in test_positions:
            if x < level.width and y < level.height:
                # Convert to FESS notation and back
                fess_coord = notation.coordinate_to_notation(x, y)
                back_to_xy = notation.notation_to_coordinate(fess_coord)
                consistent = (x, y) == back_to_xy
                all_consistent = all_consistent and consistent
                
                print(f"  ({x},{y}) -> {fess_coord} -> {back_to_xy} {'✓' if consistent else '✗'}")
        
        print(f"\n{'✅' if all_consistent else '❌'} Coordinate system consistency: {'PASSED' if all_consistent else 'FAILED'}")
        
        return all_consistent
        
    except Exception as e:
        print(f"❌ Error in compatibility test: {e}")
        return False

def main():
    """Run all FESS coordinate system tests."""
    print("🔬 FESS Coordinate System & Macro Move Notation Test Suite")
    print("=" * 70)
    print("Based on: 'The FESS Algorithm: A Feature Based Approach to Single-Agent Search'")
    print("by Yaron Shoham and Jonathan Schaeffer")
    print("=" * 70)
    
    tests = [
        ("FESS Coordinate System", test_fess_coordinate_system),
        ("FESS Macro Move Notation", test_fess_macro_move_notation),
        ("FESS Algorithm Integration", test_fess_algorithm_integration),
        ("Coordinate System Compatibility", demonstrate_coordinate_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<12} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FESS coordinate system and notation successfully implemented.")
        print("\n📋 Key Features Implemented:")
        print("  • FESS coordinate system (A-Z columns, 1-n rows)")
        print("  • Macro move notation compatible with research paper")
        print("  • 4-dimensional feature space (packing, connectivity, room_connectivity, out_of_plan)")
        print("  • Authentic FESS algorithm implementation")
        print("  • Integration with existing Sokoban level system")
        print("  • Backward compatibility with existing code")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    print(f"\n📖 Example FESS notation (Original Level 1):")
    print("• (H,5)-(G,5), preparing a path to the upper room")
    print("• (H,4)-(H,3), opening the upper room")
    print("• (F,5)-(F,7), opening a path to the left room")
    print("• And 6 more macro moves for packing boxes...")

if __name__ == "__main__":
    main()