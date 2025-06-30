#!/usr/bin/env python3
"""
Test de la version corrigée de l'algorithme FESS sur le niveau Original 1.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.fess_fixed_algorithm import FESSFixedAlgorithm
from src.ai.fess_notation import FESSLevelAnalyzer

def test_fess_fixed_algorithm():
    """Test la version corrigée de l'algorithme FESS."""
    print("🔧 Test FESS Fixed Algorithm - Niveau Original 1")
    print("=" * 60)
    
    # Charger le niveau
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    print(f"📋 Niveau: {level_title}")
    print(f"   Taille: {level.width}x{level.height}")
    print(f"   Boîtes: {len(level.boxes)} | Cibles: {len(level.targets)}")
    
    # Créer l'algorithme FESS corrigé
    fess = FESSFixedAlgorithm(level, max_time=30.0)
    
    print(f"\n🎯 Test de génération de macro moves corrigés:")
    initial_state = fess.initial_state
    
    # Test la génération de moves réalistes
    from src.ai.fess_fixed_algorithm import FESSMacroMoveGenerator
    generator = FESSMacroMoveGenerator(initial_state)
    moves = generator.generate_feasible_macro_moves()
    
    print(f"   Macro moves générés: {len(moves)}")
    print(f"   Premier move: {moves[0] if moves else 'Aucun'}")
    
    # Afficher quelques moves pour vérification
    for i, move in enumerate(moves[:5]):
        print(f"   {i+1}. {move.box_start} → {move.box_end} (pushes: {move.pushes})")
    
    # Test des features
    features = fess.feature_calculator.calculate_features(initial_state)
    print(f"\n📊 Features initiales:")
    print(f"   Packing: {features.packing}")
    print(f"   Connectivity: {features.connectivity}")
    print(f"   Room connectivity: {features.room_connectivity}")
    print(f"   Out of plan: {features.out_of_plan}")
    
    # Test de l'algorithme de recherche
    print(f"\n🔍 Recherche FESS (30 secondes max):")
    print("   Démarrage de la recherche...")
    
    try:
        success, solution_moves, stats = fess.solve()
        
        print(f"\n📊 Résultats:")
        print(f"   Solution trouvée: {'✅ OUI' if success else '❌ NON'}")
        print(f"   Nœuds expansés: {stats.get('nodes_expanded', 0)}")
        print(f"   Temps écoulé: {stats.get('time_elapsed', 0):.2f}s")
        print(f"   Taille espace features: {stats.get('feature_space_size', 0)}")
        
        if success:
            print(f"\n🎉 SOLUTION TROUVÉE!")
            print(f"   Nombre de macro moves: {len(solution_moves)}")
            
            # Calculer le total de poussées
            total_pushes = sum(move.pushes for move in solution_moves)
            print(f"   Total poussées: {total_pushes}")
            
            # Afficher la solution
            print(f"\n📝 Solution détaillée:")
            analyzer = FESSLevelAnalyzer(level)
            notation_system = analyzer.notation
            
            for i, move in enumerate(solution_moves):
                start_notation = notation_system.coordinate_to_notation(move.box_start[0], move.box_start[1])
                end_notation = notation_system.coordinate_to_notation(move.box_end[0], move.box_end[1])
                print(f"   {i+1}. ({start_notation}) → ({end_notation}) - {move.pushes} poussées")
            
            # Vérifier si on peut valider la solution
            if total_pushes <= 150:  # Limite raisonnable
                print(f"\n✅ Solution semble réaliste (≤150 poussées)")
                return True
            else:
                print(f"\n⚠️  Solution trop longue ({total_pushes} poussées)")
                return False
        else:
            print(f"\n❌ Pas de solution trouvée")
            print(f"   Possibles causes:")
            print(f"   • Temps insuffisant")
            print(f"   • Génération de moves incomplète")
            print(f"   • Détection de deadlocks trop agressive")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur pendant la recherche: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_moves():
    """Test de moves spécifiques pour debug."""
    print(f"\n🔍 Test de moves spécifiques:")
    
    # Charger le niveau
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    fess = FESSFixedAlgorithm(level, max_time=5.0)
    initial_state = fess.initial_state
    
    print(f"   Position joueur: {initial_state.player_pos}")
    print(f"   Boîtes: {sorted(initial_state.boxes)}")
    
    # Test si le joueur peut atteindre certaines positions
    reachable = initial_state.get_reachable_positions(initial_state.player_pos)
    print(f"   Positions accessibles: {len(reachable)}")
    
    # Test move simple
    from src.ai.fess_fixed_algorithm import FESSMacroMoveGenerator
    generator = FESSMacroMoveGenerator(initial_state)
    moves = generator.generate_feasible_macro_moves()
    
    if moves:
        test_move = moves[0]
        print(f"   Test move: {test_move}")
        
        # Appliquer le move
        new_state = fess._apply_move(initial_state, test_move)
        if new_state:
            print(f"   ✅ Move appliqué avec succès")
            print(f"   Nouvelle position joueur: {new_state.player_pos}")
            print(f"   Deadlock: {'Oui' if new_state.is_deadlock() else 'Non'}")
        else:
            print(f"   ❌ Move invalide")

def main():
    """Point d'entrée principal."""
    print("🧪 Test Version Corrigée FESS Algorithm")
    print("=" * 80)
    
    success1 = test_fess_fixed_algorithm()
    test_specific_moves()
    
    print(f"\n📋 RÉSUMÉ:")
    if success1:
        print("✅ Version corrigée fonctionne et trouve une solution")
        print("\n🎯 AMÉLIORATIONS RÉALISÉES:")
        print("• Macro moves réalistes (1-3 poussées max)")
        print("• Vérification correcte des chemins")
        print("• Position du joueur mise à jour correctement")
        print("• Détection de deadlocks basique")
        print("• Génération optimisée de moves")
    else:
        print("❌ Problèmes persistent - nécessite plus de debugging")
        print("\n🔧 ACTIONS SUIVANTES:")
        print("• Analyser la génération de moves plus en détail")
        print("• Améliorer la détection de deadlocks")
        print("• Optimiser l'heuristique de recherche")

if __name__ == "__main__":
    main()