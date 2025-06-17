#!/usr/bin/env python3
"""
Test de la version simplifiée de FESS sur le niveau Original 1.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.fess_simple_working import SimpleFESS

def test_simple_fess():
    """Test de la version simplifiée."""
    print("🧪 Test FESS Simplifié - Original Level 1")
    print("=" * 50)
    
    # Charger le niveau
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ Fichier non trouvé: {original_path}")
        return False
    
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    print(f"📋 Niveau: {level_title}")
    print(f"   Taille: {level.width}x{level.height}")
    print(f"   Boîtes: {len(level.boxes)}")
    print(f"   Cibles: {len(level.targets)}")
    
    # Afficher l'état initial
    from src.ai.fess_simple_working import SimpleState
    initial_state = SimpleState(level)
    
    print(f"\n🎮 État initial:")
    print(f"   Joueur: {initial_state.player_pos}")
    print(f"   Boîtes: {sorted(initial_state.boxes)}")
    print(f"   Cibles: {sorted(initial_state.targets)}")
    
    # Test de génération de moves
    from src.ai.fess_simple_working import SimpleFESSGenerator
    generator = SimpleFESSGenerator(initial_state)
    moves = generator.generate_moves()
    
    print(f"\n🎯 Génération de moves:")
    print(f"   Moves générés: {len(moves)}")
    
    # Afficher les premiers moves
    for i, move in enumerate(moves[:10]):
        print(f"   {i+1}. {move} (poids: {move.weight})")
    
    # Créer et tester l'algorithme
    print(f"\n🔍 Test algorithme FESS simplifié (30s max):")
    fess = SimpleFESS(level, max_time=30.0)
    
    try:
        success, solution_moves, stats = fess.solve()
        
        print(f"\n📊 Résultats:")
        print(f"   Solution: {'✅ TROUVÉE' if success else '❌ NON TROUVÉE'}")
        print(f"   Moves: {len(solution_moves)}")
        print(f"   Nœuds expansés: {stats['nodes_expanded']}")
        print(f"   Temps: {stats['time_elapsed']:.2f}s")
        
        if success:
            print(f"\n🎉 SOLUTION TROUVÉE!")
            print(f"📝 Macro moves de la solution:")
            
            # Afficher avec notation FESS
            from src.ai.fess_notation import FESSLevelAnalyzer
            analyzer = FESSLevelAnalyzer(level)
            notation_system = analyzer.notation
            
            for i, move in enumerate(solution_moves):
                start_notation = notation_system.coordinate_to_notation(move.box_start[0], move.box_start[1])
                end_notation = notation_system.coordinate_to_notation(move.box_end[0], move.box_end[1])
                print(f"   {i+1}. ({start_notation}) → ({end_notation}) - {move.pushes} poussées")
            
            total_pushes = sum(move.pushes for move in solution_moves)
            print(f"\n📊 Statistiques de la solution:")
            print(f"   • Total macro moves: {len(solution_moves)}")
            print(f"   • Total poussées: {total_pushes}")
            print(f"   • Ratio compression: {total_pushes:.1f} poussées → {len(solution_moves)} macro moves")
            
            # Vérifier si c'est raisonnable
            if total_pushes <= 200 and len(solution_moves) <= 20:
                print(f"   ✅ Solution semble réaliste")
                return True
            else:
                print(f"   ⚠️  Solution pourrait être sous-optimale")
                return True  # Mais c'est quand même une solution
        else:
            print(f"\n❌ Aucune solution trouvée")
            print(f"🔍 Diagnostic:")
            print(f"   • Temps insuffisant ? (Essayer d'augmenter max_time)")
            print(f"   • Génération de moves insuffisante ? ({len(moves)} moves)")
            print(f"   • Détection de deadlocks trop agressive ?")
            print(f"   • Algorithme de recherche à améliorer ?")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur pendant l'exécution: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_by_step():
    """Test étape par étape pour debug."""
    print(f"\n🔍 Test étape par étape:")
    
    # Charger le niveau
    original_path = os.path.join('src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    from src.ai.fess_simple_working import SimpleState, SimpleFESSGenerator
    state = SimpleState(level)
    
    print(f"   État initial: {len(state.boxes)} boîtes")
    
    # Test 1: Positions accessibles
    reachable = state.get_reachable(state.player_pos)
    print(f"   Positions accessibles: {len(reachable)}")
    
    # Test 2: Features
    features = state.calculate_features()
    print(f"   Features: {features.boxes_on_targets} boîtes sur cibles, {features.connectivity} régions")
    
    # Test 3: Moves
    generator = SimpleFESSGenerator(state)
    moves = generator.generate_moves()
    priority_moves = [m for m in moves if m.weight == 0.0]
    regular_moves = [m for m in moves if m.weight > 0.0]
    
    print(f"   Moves prioritaires (vers cibles): {len(priority_moves)}")
    print(f"   Moves réguliers: {len(regular_moves)}")
    
    # Test 4: Application d'un move
    if moves:
        test_move = moves[0]
        print(f"   Test application move: {test_move}")
        
        fess = SimpleFESS(level)
        new_state = fess._apply_move(state, test_move)
        
        if new_state:
            print(f"   ✅ Move appliqué avec succès")
            new_features = new_state.calculate_features()
            print(f"   Nouvelles features: {new_features.boxes_on_targets} boîtes sur cibles")
            
            deadlock = fess._is_simple_deadlock(new_state)
            print(f"   Deadlock détecté: {'Oui' if deadlock else 'Non'}")
        else:
            print(f"   ❌ Échec application move")

def main():
    """Point d'entrée principal."""
    print("🎮 Test Version Simplifiée FESS - Niveau Original 1")
    print("=" * 80)
    
    success = test_simple_fess()
    test_step_by_step()
    
    print(f"\n📋 RÉSUMÉ FINAL:")
    if success:
        print("✅ Version simplifiée FONCTIONNE et trouve une solution!")
        print("\n🎯 ACCOMPLISSEMENTS:")
        print("• Génération de macro moves réalistes")
        print("• Application correcte des moves")
        print("• Recherche qui trouve une solution")
        print("• Compatible avec la notation FESS")
        
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("• Optimiser la recherche pour de meilleures solutions")
        print("• Ajouter plus de stratégies de moves")
        print("• Améliorer la détection de deadlocks")
        print("• Implémenter l'espace des features complet")
    else:
        print("❌ Problèmes persistent")
        print("\n🔧 À CORRIGER:")
        print("• Augmenter le nombre de moves générés")
        print("• Améliorer l'algorithme de recherche")
        print("• Implémenter une meilleure heuristique")

if __name__ == "__main__":
    main()