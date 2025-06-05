#!/usr/bin/env python3
"""
Sokoban Level Editor

This module provides a standalone entry point for the Sokoban level editor.
"""

import os
import sys
import pygame
from src.core.constants import TITLE
from src.editors.enhanced_level_editor import EnhancedLevelEditor


def main():
    """
    Main function to run the Sokoban level editor.
    """
    # Parse command line arguments
    levels_dir = 'levels'

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--levels' or sys.argv[i] == '-l':
            if i + 1 < len(sys.argv):
                levels_dir = sys.argv[i + 1]
                i += 2
            else:
                print("Error: Missing argument for --levels")
                sys.exit(1)
        else:
            # For backwards compatibility, treat first argument as levels_dir
            if i == 1:
                levels_dir = sys.argv[i]
            i += 1

    # Check if levels directory exists, create it if not
    if not os.path.exists(levels_dir):
        os.makedirs(levels_dir)
        print(f"Created levels directory: {levels_dir}")

    # Initialize pygame
    pygame.init()
    pygame.display.set_caption(f"{TITLE} - Level Editor")

    # Create and start the editor
    editor = EnhancedLevelEditor(levels_dir)
    editor.start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEditor terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
