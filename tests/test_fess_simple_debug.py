#!/usr/bin/env python3
"""
Test simple de l'algorithme FESS avec debug basique.

Ce script teste l'algorithme FESS de manière plus directe pour identifier
et corriger les problèmes de boucle infinie observés dans le debug visuel.
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess_algorithm import FESSAlgorithm, SokobanState
from src.ai.fess_notation import FESSLevelAnalyzer

def test_fess_algorithm_basic():
    """Test basique de l'algorithme FESS."""
    print("🔬 Test Basique de l'Algorithme FESS")
    print("=" * 50)
    
    # Charger le niveau 1 original
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ Fichier non trouvé: {original_path}")
        return False
    
    try:
        # Parser la collection et obtenir le niveau 1
        collection = LevelCollectionParser.parse_file(original_path)
        level_title, level = collection.get_level(0)
        
        print(f"📋 Niveau: {level_title}")
        print(f"📏 Taille: {level.width}x{level.height}")
        print(f"📦 Boîtes: {len(level.boxes)}")
        print(f"🎯 Cibles: {len(level.targets)}")
        
        # Afficher le niveau
        print(f"\n🗺️  Niveau avec Coordonnées FESS:")
        print(level.get_state_string(show_fess_coordinates=True))
        
        # Analyser l'état initial
        initial_state = SokobanState(level)
        print(f"\n📊 État Initial:")
        print(f"  • Joueur: {initial_state.player_pos}")
        print(f"  • Boîtes: {sorted(initial_state.boxes)}")
        print(f"  • Cibles: {sorted(initial_state.targets)}")
        
        # Créer l'analyseur FESS
        analyzer = FESSLevelAnalyzer(level)
        
        # Tester les features
        features = analyzer.get_features_analysis()
        print(f"\n🧠 Features FESS:")
        for feature_name, value in features.items():
            print(f"  • {feature_name}: {value}")
        
        # Tester l'algorithme FESS avec un temps court
        print(f"\n🚀 Test de l'Algorithme FESS (10s)...")
        fess = FESSAlgorithm(level, max_time=10.0)
        
        start_time = time.time()
        success, moves, stats = fess.solve()
        elapsed_time = time.time() - start_time
        
        print(f"\n📊 Résultats:")
        print(f"  • Succès: {'✅' if success else '❌'}")
        print(f"  • Temps: {elapsed_time:.2f}s")
        print(f"  • Macro moves: {len(moves) if success else 0}")
        print(f"  • Nœuds explorés: {stats.get('nodes_expanded', 0)}")
        print(f"  • Taille espace features: {stats.get('feature_space_size', 0)}")
        
        # Afficher la solution si trouvée
        if success and moves:
            print(f"\n📝 Solution Trouvée:")
            for i, move in enumerate(moves):
                start_coord = analyzer.notation.coordinate_to_notation(move.box_start[0], move.box_start[1])
                end_coord = analyzer.notation.coordinate_to_notation(move.box_end[0], move.box_end[1])
                print(f"  {i+1}. {start_coord} → {end_coord}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_macro_moves_generation():
    """Test de la génération des macro moves."""
    print(f"\n🎯 Test de Génération des Macro Moves")
    print("-" * 40)
    
    # Charger le niveau
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    # Créer l'état initial
    initial_state = SokobanState(level)
    
    # Créer l'algorithme FESS
    fess = FESSAlgorithm(level, max_time=5.0)
    
    # Tester la génération de macro moves
    print(f"📦 Génération des Macro Moves:")
    macro_moves = fess._generate_all_macro_moves(initial_state)
    print(f"  • Nombre total: {len(macro_moves)}")
    
    # Afficher les premiers macro moves
    analyzer = FESSLevelAnalyzer(level)
    print(f"  • Premiers 10 macro moves:")
    for i, move in enumerate(macro_moves[:10]):
        start_coord = analyzer.notation.coordinate_to_notation(move.box_start[0], move.box_start[1])
        end_coord = analyzer.notation.coordinate_to_notation(move.box_end[0], move.box_end[1])
        print(f"    {i+1}. {start_coord} → {end_coord} (poids: {move.weight})")
    
    # Tester les conseillers
    advisor_moves = fess.advisor.get_advisor_moves(initial_state, fess.feature_calculator.calculate_features(initial_state))
    print(f"\n🤖 Conseillers:")
    print(f"  • Nombre de recommandations: {len(advisor_moves)}")
    for i, move in enumerate(advisor_moves):
        start_coord = analyzer.notation.coordinate_to_notation(move.box_start[0], move.box_start[1])
        end_coord = analyzer.notation.coordinate_to_notation(move.box_end[0], move.box_end[1])
        print(f"    {i+1}. {start_coord} → {end_coord} (poids: {move.weight})")

def test_state_transitions():
    """Test des transitions d'état."""
    print(f"\n🔄 Test des Transitions d'État")
    print("-" * 40)
    
    # Charger le niveau
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    # État initial
    initial_state = SokobanState(level)
    fess = FESSAlgorithm(level, max_time=5.0)
    analyzer = FESSLevelAnalyzer(level)
    
    print(f"📊 État Initial:")
    print(f"  • Features: {fess.feature_calculator.calculate_features(initial_state).to_tuple()}")
    
    # Tester un macro move
    advisor_moves = fess.advisor.get_advisor_moves(initial_state, fess.feature_calculator.calculate_features(initial_state))
    if advisor_moves:
        move = advisor_moves[0]
        start_coord = analyzer.notation.coordinate_to_notation(move.box_start[0], move.box_start[1])
        end_coord = analyzer.notation.coordinate_to_notation(move.box_end[0], move.box_end[1])
        
        print(f"\n🎯 Test du Mouvement: {start_coord} → {end_coord}")
        
        # Appliquer le mouvement
        new_state = fess._apply_move(initial_state, move)
        
        if new_state:
            new_features = fess.feature_calculator.calculate_features(new_state)
            print(f"✅ Mouvement appliqué avec succès")
            print(f"  • Nouvelles features: {new_features.to_tuple()}")
            print(f"  • Nouvelle position joueur: {new_state.player_pos}")
            print(f"  • Nouvelles positions boîtes: {sorted(new_state.boxes)}")
        else:
            print(f"❌ Mouvement invalide")

def test_expected_solution():
    """Test avec la solution attendue du document de recherche."""
    print(f"\n📚 Test avec Solution Attendue du Document")
    print("-" * 50)
    
    # Charger le niveau
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    # Créer l'analyseur
    analyzer = FESSLevelAnalyzer(level)
    
    # Créer la notation attendue
    notation = analyzer.create_original_level1_notation()
    
    print(f"📝 Solution Attendue (Document de Recherche):")
    solution_text = notation.get_solution_notation(97, 250)
    print(solution_text)
    
    # Vérifier que les coordonnées sont correctes
    print(f"\n✅ Vérification des Coordonnées:")
    for i, macro_move in enumerate(notation.macro_moves):
        start_coord = analyzer.notation.coordinate_to_notation(macro_move.start_pos[0], macro_move.start_pos[1])
        end_coord = analyzer.notation.coordinate_to_notation(macro_move.end_pos[0], macro_move.end_pos[1])
        print(f"  {i+1}. ({start_coord}) → ({end_coord}) - {macro_move.description}")

def main():
    """Lance les tests de debug de l'algorithme FESS."""
    print("🔬 FESS Algorithm Debug Tests")
    print("=" * 60)
    print("Tests pour identifier et corriger les problèmes de l'algorithme FESS")
    print("=" * 60)
    
    tests = [
        ("Solution Attendue", test_expected_solution),
        ("Génération Macro Moves", test_macro_moves_generation),
        ("Transitions d'État", test_state_transitions),
        ("Algorithme FESS Basique", test_fess_algorithm_basic),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result if result is not None else True))
        except Exception as e:
            print(f"❌ {test_name} a échoué: {e}")
            results.append((test_name, False))
    
    # Résumé
    print(f"\n" + "="*60)
    print(f"📊 RÉSUMÉ DES TESTS")
    print(f"="*60)
    
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status:<12} {test_name}")
    
    successful_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    print(f"\n🎯 Résultat Global: {successful_tests}/{total_tests} tests réussis")
    
    if successful_tests == total_tests:
        print(f"🎉 Tous les tests sont passés!")
        print(f"🔧 L'algorithme FESS semble fonctionner correctement")
    else:
        print(f"⚠️  Certains tests ont échoué")
        print(f"🔍 Il faut continuer le debug")

if __name__ == "__main__":
    main()