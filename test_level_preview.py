"""
Test script for the new level preview functionality.
"""

import pygame
import sys
import os

# Add the src directory to the path
sys.path.append('src')

from src.level_management.level_selector import LevelSelector

def test_level_preview():
    """Test the level preview functionality."""
    pygame.init()
    
    # Set up the display
    screen_width = 1024
    screen_height = 768
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Test Prévisualisation de Niveau - Sokoban")
    
    # Create level selector
    level_selector = LevelSelector(screen, screen_width, screen_height)
    
    print("Démarrage du test de prévisualisation des niveaux...")
    print("Instructions:")
    print("1. Sélectionnez une catégorie de niveaux")
    print("2. Cliquez sur un niveau pour voir la prévisualisation")
    print("3. Dans la popup, vous pouvez:")
    print("   - Cliquer 'Play' pour jouer au niveau")
    print("   - Cliquer 'Retour' pour revenir à la sélection")
    print("   - Appuyer sur Échap pour fermer la popup")
    print("   - Appuyer sur Entrée/Espace pour jouer")
    print("   - Cliquer à l'extérieur de la popup pour fermer")
    
    # Start the level selector
    selected_level = level_selector.start()
    
    if selected_level:
        print(f"\nNiveau sélectionné: {selected_level['title']}")
        print(f"Type: {selected_level['type']}")
        if selected_level['type'] == 'collection_level':
            print(f"Fichier collection: {selected_level['collection_file']}")
            print(f"Index du niveau: {selected_level['level_index']}")
        else:
            print(f"Fichier: {selected_level['file_path']}")
        print("\nLa fonctionnalité de prévisualisation fonctionne correctement !")
    else:
        print("\nAucun niveau sélectionné - Test terminé.")
    
    pygame.quit()

if __name__ == "__main__":
    test_level_preview()