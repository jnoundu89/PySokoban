#!/usr/bin/env python3
"""
Test script for the enhanced level editor UI improvements.
This script demonstrates the improved interface layout.
"""

import pygame
import sys
import os

from src.editors.enhanced_level_editor import EnhancedLevelEditor

def test_level_editor_ui():
    """Test the enhanced level editor with improved UI layout."""
    print("Testing Enhanced Level Editor UI Improvements...")
    print("=" * 50)
    print("UI Improvements:")
    print("• Panneau gauche élargi (280px) pour éviter les chevauchements")
    print("• Nouveau panneau droit (200px) pour les contrôles de vue")
    print("• Espace de dessin central agrandi")
    print("• Panneau inférieur réduit (80px) pour plus d'espace de carte")
    print("• Meilleure répartition des boutons et éléments")
    print("• Espacement amélioré entre les éléments")
    print("=" * 50)
    print("\nControls:")
    print("• Left Panel: File operations, Tools, Element palette")
    print("• Right Panel: View controls, Zoom, Size sliders")
    print("• Center: Large drawing area for level editing")
    print("• Bottom: Status information and main controls")
    print("=" * 50)
    print("\nLaunching Enhanced Level Editor...")
    
    try:
        # Initialize the enhanced level editor
        editor = EnhancedLevelEditor()
        
        # Print layout information
        print(f"Screen size: {editor.screen_width}x{editor.screen_height}")
        print(f"Left panel width: {editor.tool_panel_width}px")
        print(f"Right panel width: {editor.right_panel_width}px")
        print(f"Map area: {editor.map_area_width}x{editor.map_area_height}px")
        print(f"Bottom panel height: {editor.bottom_panel_height}px")
        
        # Start the editor
        editor.start()
        
    except Exception as e:
        print(f"Error running level editor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_level_editor_ui()