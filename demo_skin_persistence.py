#!/usr/bin/env python3
"""
Démonstration du système de persistance des skins.

Ce script montre comment le système de skins persistantes fonctionne :
1. Lance le jeu avec les skins par défaut
2. Permet de changer les skins dans le menu
3. Vérifie que les skins persistent entre les sessions
"""

import os
import sys
import pygame

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.enhanced_main import EnhancedSokoban
from src.core.config_manager import get_config_manager
from src.ui.skins.enhanced_skin_manager import EnhancedSkinManager

def show_current_skin_settings():
    """Affiche les paramètres de skin actuels."""
    config = get_config_manager()
    skin_config = config.get_skin_config()
    
    print("=" * 50)
    print("PARAMÈTRES DE SKIN ACTUELS")
    print("=" * 50)
    print(f"Skin actuel: {skin_config['current_skin']}")
    print(f"Taille des tuiles: {skin_config['tile_size']}x{skin_config['tile_size']}")
    print("=" * 50)

def demonstrate_persistence():
    """Démontre la persistance des skins."""
    print("🎮 DÉMONSTRATION DE LA PERSISTANCE DES SKINS")
    print()
    
    # Afficher les paramètres actuels
    show_current_skin_settings()
    
    print("\nINSTRUCTIONS:")
    print("1. Le jeu va se lancer avec les paramètres actuels")
    print("2. Allez dans le menu 'Skins' pour changer les skins")
    print("3. Cliquez sur 'Appliquer' pour sauvegarder vos changements")
    print("4. Fermez le jeu et relancez ce script")
    print("5. Vos paramètres seront conservés!")
    print()
    
    input("Appuyez sur Entrée pour lancer le jeu...")
    
    try:
        # Lancer le jeu
        game = EnhancedSokoban()
        game.start()
        
    except KeyboardInterrupt:
        print("\nJeu fermé par l'utilisateur.")
    except Exception as e:
        print(f"Erreur lors du lancement du jeu: {e}")
    
    print("\nVérification des paramètres après fermeture du jeu:")
    show_current_skin_settings()

def test_skin_manager_directly():
    """Teste directement le gestionnaire de skins."""
    print("\n🔧 TEST DIRECT DU GESTIONNAIRE DE SKINS")
    print()
    
    # Créer un gestionnaire de skins
    skin_manager = EnhancedSkinManager()
    
    print("Skins disponibles:")
    available_skins = skin_manager.get_available_skins()
    for i, skin in enumerate(available_skins):
        current_marker = " (ACTUEL)" if skin == skin_manager.get_current_skin_name() else ""
        print(f"  {i+1}. {skin}{current_marker}")
    
    print(f"\nTailles de tuiles disponibles: {skin_manager.get_available_tile_sizes()}")
    print(f"Taille actuelle: {skin_manager.get_current_tile_size()}")
    
    print("\nVoulez-vous changer le skin? (o/n)")
    choice = input().lower()
    
    if choice == 'o':
        print("Choisissez un skin (numéro):")
        try:
            skin_index = int(input()) - 1
            if 0 <= skin_index < len(available_skins):
                new_skin = available_skins[skin_index]
                skin_manager.set_skin(new_skin)
                print(f"✓ Skin changé vers: {new_skin}")
                
                print("Choisissez une taille de tuiles:")
                tile_sizes = skin_manager.get_available_tile_sizes()
                for i, size in enumerate(tile_sizes):
                    current_marker = " (ACTUEL)" if size == skin_manager.get_current_tile_size() else ""
                    print(f"  {i+1}. {size}x{size}{current_marker}")
                
                tile_index = int(input()) - 1
                if 0 <= tile_index < len(tile_sizes):
                    new_tile_size = tile_sizes[tile_index]
                    skin_manager.set_tile_size(new_tile_size)
                    print(f"✓ Taille des tuiles changée vers: {new_tile_size}x{new_tile_size}")
                
                print("\nParamètres sauvegardés! Ils persisteront lors du prochain lancement.")
            else:
                print("Index invalide.")
        except ValueError:
            print("Entrée invalide.")

def main():
    """Fonction principale."""
    print("SYSTÈME DE PERSISTANCE DES SKINS - SOKOBAN")
    print("==========================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_skin_manager_directly()
    else:
        demonstrate_persistence()

if __name__ == "__main__":
    main()