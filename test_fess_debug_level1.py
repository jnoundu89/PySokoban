#!/usr/bin/env python3
"""
Debug script pour identifier les problèmes critiques dans l'implémentation FESS
sur le premier niveau Original de Sokoban.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.authentic_fess_algorithm import FESSAlgorithm, SokobanState
from src.ai.fess_notation import FESSLevelAnalyzer

def debug_fess_problems():
    """Debug les problèmes dans l'implémentation FESS."""
    print("🔧 FESS Algorithm Debug - Niveau Original 1")
    print("=" * 60)
    
    # Charger le niveau
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    print(f"📋 Niveau chargé: {level_title}")
    print(f"   Taille: {level.width}x{level.height}")
    print(f"   Boîtes: {len(level.boxes)} | Cibles: {len(level.targets)}")
    print(f"   Joueur: {level.player_pos}")
    
    # Créer l'algorithme FESS
    fess = FESSAlgorithm(level, max_time=10.0)
    initial_state = fess.initial_state
    
    print(f"\n🧩 État initial analysé:")
    print(f"   Boîtes: {sorted(initial_state.boxes)}")
    print(f"   Cibles: {sorted(initial_state.targets)}")
    print(f"   Joueur: {initial_state.player_pos}")
    
    # Analyser les features initiales
    features = fess.feature_calculator.calculate_features(initial_state)
    print(f"\n📊 Features initiales:")
    print(f"   Packing: {features.packing}")
    print(f"   Connectivity: {features.connectivity}")
    print(f"   Room connectivity: {features.room_connectivity}")
    print(f"   Out of plan: {features.out_of_plan}")
    
    # Test de génération de macro moves
    print(f"\n🎯 Test de génération de macro moves:")
    try:
        advisor_moves = fess.advisor.get_advisor_moves(initial_state, features)
        print(f"   Advisor moves: {len(advisor_moves)}")
        for i, move in enumerate(advisor_moves[:3]):
            print(f"     {i+1}. {move.box_start} → {move.box_end} (weight: {move.weight})")
        
        all_moves = fess._generate_all_macro_moves(initial_state)
        print(f"   All macro moves: {len(all_moves)}")
        
        # Vérifier la faisabilité des moves
        feasible_count = 0
        for move in all_moves[:10]:  # Test sur les 10 premiers
            if fess.advisor._is_move_feasible(initial_state, move):
                feasible_count += 1
        print(f"   Moves faisables (sur 10 testés): {feasible_count}")
        
    except Exception as e:
        print(f"   ❌ Erreur génération moves: {e}")
        import traceback
        traceback.print_exc()
    
    # Test d'application d'un move
    print(f"\n🔄 Test d'application de move:")
    try:
        if advisor_moves:
            test_move = advisor_moves[0]
            print(f"   Test move: {test_move.box_start} → {test_move.box_end}")
            
            new_state = fess._apply_move(initial_state, test_move)
            if new_state:
                print(f"   ✅ Move appliqué avec succès")
                print(f"      Nouvelle position joueur: {new_state.player_pos}")
                print(f"      Boîtes avant: {sorted(initial_state.boxes)}")
                print(f"      Boîtes après: {sorted(new_state.boxes)}")
            else:
                print(f"   ❌ Move invalide")
        
    except Exception as e:
        print(f"   ❌ Erreur application move: {e}")
        import traceback
        traceback.print_exc()
    
    # Test de recherche courte
    print(f"\n🔍 Test de recherche FESS (5 secondes):")
    try:
        success, moves, stats = fess.solve()
        
        print(f"   Résultat: {'✅ SOLUTION TROUVÉE' if success else '❌ PAS DE SOLUTION'}")
        print(f"   Nœuds expansés: {stats.get('nodes_expanded', 0)}")
        print(f"   Temps écoulé: {stats.get('time_elapsed', 0):.2f}s")
        print(f"   Taille espace features: {stats.get('feature_space_size', 0)}")
        
        if success:
            print(f"   Moves trouvés: {len(moves)}")
            for i, move in enumerate(moves[:3]):
                print(f"     {i+1}. {move}")
        else:
            print(f"   ⚠️  Algorithme n'a pas trouvé de solution")
            
    except Exception as e:
        print(f"   ❌ Erreur pendant la recherche: {e}")
        import traceback
        traceback.print_exc()
    
    # Diagnostic des problèmes
    print(f"\n🔍 DIAGNOSTIC DES PROBLÈMES:")
    print(f"=" * 40)
    
    problems = []
    
    # Problème 1: Vérification de faisabilité
    try:
        test_box = list(initial_state.boxes)[0]
        test_target = (test_box[0] + 1, test_box[1])
        if initial_state.is_valid_position(test_target) and test_target not in initial_state.boxes:
            from src.ai.authentic_fess_algorithm import MacroMoveAction
            test_move = MacroMoveAction(test_box, test_target)
            feasible = fess.advisor._is_move_feasible(initial_state, test_move)
            if not feasible:
                problems.append("❌ Vérification de faisabilité trop restrictive")
            else:
                print("✅ Vérification de faisabilité fonctionne")
    except:
        problems.append("❌ Problème dans la vérification de faisabilité")
    
    # Problème 2: Génération excessive de moves
    if len(all_moves) > 100:
        problems.append(f"⚠️  Trop de macro moves générés: {len(all_moves)}")
    
    # Problème 3: Position du joueur
    if hasattr(fess, '_apply_move'):
        problems.append("⚠️  Mise à jour position joueur simpliste")
    
    # Problème 4: Pas de détection de deadlocks
    problems.append("❌ Pas de détection de deadlocks implémentée")
    
    # Problème 5: Pas de vérification de chemins
    problems.append("❌ Pas de vérification de chemins complets pour macro moves")
    
    if problems:
        print("PROBLÈMES IDENTIFIÉS:")
        for problem in problems:
            print(f"  {problem}")
    else:
        print("✅ Aucun problème majeur détecté")
    
    return len(problems) == 0

def main():
    """Point d'entrée principal."""
    print("🐛 FESS Debug Session - Original Level 1")
    print("=" * 80)
    
    success = debug_fess_problems()
    
    print(f"\n📋 RÉSUMÉ:")
    if success:
        print("✅ Implémentation semble correcte")
    else:
        print("❌ Problèmes identifiés nécessitant des corrections")
        print("\n🔧 CORRECTIONS NÉCESSAIRES:")
        print("1. Améliorer la vérification de faisabilité des macro moves")
        print("2. Implémenter la détection de deadlocks")
        print("3. Vérifier les chemins complets pour les macro moves")
        print("4. Corriger la mise à jour de la position du joueur")
        print("5. Optimiser la génération de macro moves")

if __name__ == "__main__":
    main()