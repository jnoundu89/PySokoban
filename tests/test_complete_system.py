#!/usr/bin/env python3
"""
Test script pour vérifier le système complet.

Ce script teste :
1. Le parsing des collections de niveaux
2. Le sélecteur de niveau avec scroll
3. Le chargement des niveaux individuels depuis les collections
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_collection_parsing():
    """Test le parsing des collections."""
    print("=== Test du parsing des collections ===")
    
    from level_management.level_collection_parser import LevelCollectionParser
    
    try:
        collection = LevelCollectionParser.parse_file('levels/Original/Original.txt')
        print(f"✓ Collection parsée avec succès")
        print(f"  Titre: {collection.title}")
        print(f"  Auteur: {collection.author}")
        print(f"  Description: {collection.description}")
        print(f"  Nombre de niveaux: {collection.get_level_count()}")
        
        # Test d'un niveau spécifique
        if collection.get_level_count() > 0:
            level_title, level = collection.get_level(0)
            print(f"  Premier niveau: '{level_title}'")
            print(f"  Taille: {level.width}x{level.height}")
            print(f"  Boîtes: {len(level.boxes)}")
            print(f"  Cibles: {len(level.targets)}")
        
        return True
    except Exception as e:
        print(f"✗ Erreur lors du parsing: {e}")
        return False

def test_level_selector():
    """Test le sélecteur de niveau."""
    print("\n=== Test du sélecteur de niveau ===")
    
    try:
        from level_management.level_selector import LevelSelector
        import pygame
        
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        
        selector = LevelSelector(screen, 800, 600, 'levels')
        print(f"✓ Sélecteur créé avec succès")
        print(f"  Catégories trouvées: {len(selector.categories)}")
        
        for category in selector.categories:
            print(f"  - {category.display_name}: {len(category.levels)} niveaux")
            
            # Vérifier si c'est une collection
            if len(category.levels) > 0:
                first_level = category.levels[0]
                if hasattr(first_level, 'is_from_collection') and first_level.is_from_collection:
                    print(f"    (Collection détectée)")
        
        pygame.quit()
        return True
    except Exception as e:
        print(f"✗ Erreur avec le sélecteur: {e}")
        return False

def test_level_manager():
    """Test le gestionnaire de niveau."""
    print("\n=== Test du gestionnaire de niveau ===")
    
    try:
        from level_management.level_manager import LevelManager
        
        manager = LevelManager('levels')
        print(f"✓ Gestionnaire créé avec succès")
        print(f"  Fichiers de niveau: {len(manager.level_files)}")
        print(f"  Collections: {len(manager.level_collections)}")
        
        # Test des métadonnées
        if manager.current_level:
            metadata = manager.get_level_metadata()
            print(f"  Métadonnées du niveau actuel:")
            print(f"    Titre: {metadata.get('title', 'N/A')}")
            print(f"    Auteur: {metadata.get('author', 'N/A')}")
            print(f"    Description: {metadata.get('description', 'N/A')}")
            
            # Test des informations de collection
            collection_info = manager.get_current_collection_info()
            if collection_info:
                print(f"  Informations de collection:")
                print(f"    Titre: {collection_info['title']}")
                print(f"    Niveau actuel: {collection_info['current_level_index']} de {collection_info['level_count']}")
        
        return True
    except Exception as e:
        print(f"✗ Erreur avec le gestionnaire: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("Test du système complet de gestion des collections de niveaux")
    print("=" * 60)
    
    success = True
    success &= test_collection_parsing()
    success &= test_level_selector()
    success &= test_level_manager()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Tous les tests sont passés avec succès!")
        print("\nPour tester l'interface graphique complète:")
        print("  python src/enhanced_main.py")
        print("\nFonctionnalités disponibles:")
        print("  - Sélection de niveau avec collections")
        print("  - Navigation dans les collections (90 niveaux)")
        print("  - Scroll dans les listes de niveaux")
        print("  - Mouvement continu (maintenir les touches)")
        print("  - Affichage des métadonnées (titre, auteur, description)")
    else:
        print("✗ Certains tests ont échoué!")
    
    return success

if __name__ == "__main__":
    main()