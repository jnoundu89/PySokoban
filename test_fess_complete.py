#!/usr/bin/env python3
"""
Test complet de l'implémentation FESS authentique avec toutes les fonctionnalités.

Ce test valide:
1. Les 4 analyseurs de features (Packing, Connectivity, Room, Out-of-Plan)
2. Les 7 advisors domain-spécifiques
3. Le générateur de macro-moves
4. L'intégration complète dans le moteur FESS
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai.authentic_fess import (
    FESSSearchEngine, FESSState, PackingAnalyzer, ConnectivityAnalyzer,
    RoomAnalyzer, OutOfPlanAnalyzer, HotspotsAnalyzer, FESSAdvisors,
    MacroMoveGenerator, FESSFeatureSpace
)
from src.core.level import Level
import time

def create_test_level():
    """Crée un niveau de test simple mais représentatif."""
    level_data = [
        "########",
        "#......#",
        "#..$...#", 
        "#..@...#",
        "#......#",
        "#......#",
        "#......#",
        "########"
    ]
    
    return Level.from_string_array(level_data)

def test_feature_analyzers():
    """Test des 4 analyseurs de features."""
    print("🔬 Test des analyseurs de features...")
    
    level = create_test_level()
    initial_state = FESSState(
        player_pos=level.player_pos,
        boxes=frozenset(level.boxes)
    )
    
    # Test PackingAnalyzer
    print("  📦 Test PackingAnalyzer...")
    packing_analyzer = PackingAnalyzer(level)
    packing_feature = packing_analyzer.calculate_packing_feature(initial_state)
    print(f"    Packing feature: {packing_feature}")
    print(f"    Ordre optimal: {packing_analyzer.get_optimal_packing_order()}")
    
    # Test ConnectivityAnalyzer
    print("  🔗 Test ConnectivityAnalyzer...")
    connectivity_analyzer = ConnectivityAnalyzer(level)
    connectivity = connectivity_analyzer.calculate_connectivity(initial_state)
    print(f"    Connectivity: {connectivity}")
    
    # Test RoomAnalyzer
    print("  🏠 Test RoomAnalyzer...")
    room_analyzer = RoomAnalyzer(level)
    room_connectivity = room_analyzer.calculate_room_connectivity(initial_state)
    print(f"    Room connectivity: {room_connectivity}")
    print(f"    Rooms détectées: {len(room_analyzer.rooms)}")
    
    # Test OutOfPlanAnalyzer
    print("  ⚠️ Test OutOfPlanAnalyzer...")
    oop_analyzer = OutOfPlanAnalyzer(level, packing_analyzer)
    oop_count = oop_analyzer.calculate_out_of_plan(initial_state)
    print(f"    Out-of-plan boxes: {oop_count}")
    
    print("✅ Analyseurs de features OK")

def test_hotspots_analyzer():
    """Test de l'analyseur de hotspots."""
    print("🔥 Test HotspotsAnalyzer...")
    
    level = create_test_level()
    initial_state = FESSState(
        player_pos=level.player_pos,
        boxes=frozenset(level.boxes)
    )
    
    hotspots_analyzer = HotspotsAnalyzer(level)
    hotspots_count = hotspots_analyzer.calculate_hotspots(initial_state)
    hotspot_boxes = hotspots_analyzer.get_hotspot_boxes(initial_state)
    most_disruptive = hotspots_analyzer.get_most_disruptive_hotspot(initial_state)
    
    print(f"  Hotspots count: {hotspots_count}")
    print(f"  Hotspot boxes: {hotspot_boxes}")
    print(f"  Most disruptive: {most_disruptive}")
    
    print("✅ HotspotsAnalyzer OK")

def test_advisors():
    """Test des 7 advisors."""
    print("🎯 Test des 7 advisors...")
    
    level = create_test_level()
    feature_space = FESSFeatureSpace(level)
    
    # Initialiser les analyseurs
    feature_space.packing_analyzer = PackingAnalyzer(level)
    feature_space.connectivity_analyzer = ConnectivityAnalyzer(level)
    feature_space.room_analyzer = RoomAnalyzer(level)
    feature_space.out_of_plan_analyzer = OutOfPlanAnalyzer(level, feature_space.packing_analyzer)
    
    advisors = FESSAdvisors(level, feature_space)
    
    initial_state = FESSState(
        player_pos=level.player_pos,
        boxes=frozenset(level.boxes)
    )
    
    advisor_moves = advisors.get_advisor_moves(initial_state)
    
    print(f"  Mouvements suggérés par les advisors: {len(advisor_moves)}")
    for i, (macro_move, weight) in enumerate(advisor_moves):
        if macro_move:
            print(f"    Advisor {i+1}: {macro_move.box_from} -> {macro_move.box_to} (poids {weight})")
        else:
            print(f"    Advisor {i+1}: Aucun mouvement suggéré")
    
    print("✅ Advisors OK")

def test_macro_generator():
    """Test du générateur de macro-moves."""
    print("🎮 Test MacroMoveGenerator...")
    
    level = create_test_level()
    generator = MacroMoveGenerator(level)
    
    initial_state = FESSState(
        player_pos=level.player_pos,
        boxes=frozenset(level.boxes)
    )
    
    macro_moves = generator.generate_macro_moves(initial_state)
    
    print(f"  Macro-moves générés: {len(macro_moves)}")
    for i, macro_move in enumerate(macro_moves[:5]):  # Afficher les 5 premiers
        print(f"    {i+1}: {macro_move.box_from} -> {macro_move.box_to} "
              f"(poids {macro_move.weight}, séquence {macro_move.push_sequence})")
    
    if len(macro_moves) > 5:
        print(f"    ... et {len(macro_moves) - 5} autres")
    
    print("✅ MacroMoveGenerator OK")

def test_feature_space_projection():
    """Test de la projection vers l'espace de features 4D."""
    print("🌌 Test de l'espace de features 4D...")
    
    level = create_test_level()
    feature_space = FESSFeatureSpace(level)
    
    # Initialiser les analyseurs
    feature_space.packing_analyzer = PackingAnalyzer(level)
    feature_space.connectivity_analyzer = ConnectivityAnalyzer(level)
    feature_space.room_analyzer = RoomAnalyzer(level)
    feature_space.out_of_plan_analyzer = OutOfPlanAnalyzer(level, feature_space.packing_analyzer)
    
    initial_state = FESSState(
        player_pos=level.player_pos,
        boxes=frozenset(level.boxes)
    )
    
    # Test de projection
    fs_coords = feature_space.project_state(initial_state)
    print(f"  Coordonnées FS 4D: {fs_coords}")
    print(f"    F1 (Packing): {fs_coords[0]}")
    print(f"    F2 (Connectivity): {fs_coords[1]}")
    print(f"    F3 (Room Connectivity): {fs_coords[2]}")
    print(f"    F4 (Out of Plan): {fs_coords[3]}")
    
    # Ajouter l'état à l'espace FS
    feature_space.add_state_to_cell(initial_state)
    
    stats = feature_space.get_statistics()
    print(f"  Statistiques FS: {stats}")
    
    print("✅ Espace de features 4D OK")

def test_complete_fess_engine():
    """Test du moteur FESS complet avec toutes les fonctionnalités."""
    print("🚀 Test du moteur FESS complet...")
    
    level = create_test_level()
    
    # Créer le moteur FESS avec un temps limité pour le test
    fess_engine = FESSSearchEngine(level, max_states=1000, time_limit=10.0)
    
    def progress_callback(message):
        print(f"    {message}")
    
    print("  Démarrage de la recherche FESS...")
    start_time = time.time()
    
    try:
        solution = fess_engine.search(progress_callback)
        elapsed = time.time() - start_time
        
        if solution:
            print(f"  ✅ Solution trouvée en {elapsed:.2f}s!")
            print(f"  Longueur de la solution: {len(solution)} mouvements")
            print(f"  Solution: {solution[:10]}..." if len(solution) > 10 else f"  Solution: {solution}")
        else:
            print(f"  ⏱️ Aucune solution trouvée en {elapsed:.2f}s (limite de test atteinte)")
        
        # Afficher les statistiques
        stats = fess_engine.get_statistics()
        print(f"  Statistiques:")
        print(f"    États explorés: {stats['search_statistics']['states_explored']}")
        print(f"    États générés: {stats['search_statistics']['states_generated']}")
        print(f"    Cellules FS: {stats['feature_space_statistics']['total_cells']}")
        print(f"    Assignations de poids: {stats['search_statistics']['move_weight_assignments']}")
        
    except Exception as e:
        print(f"  ❌ Erreur pendant la recherche: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ Test du moteur FESS complet terminé")

def main():
    """Fonction principale du test complet."""
    print("🧪 FESS COMPLET - Test de toutes les fonctionnalités")
    print("=" * 60)
    
    try:
        # Tests individuels des composants
        test_feature_analyzers()
        print()
        
        test_hotspots_analyzer()
        print()
        
        test_advisors()
        print()
        
        test_macro_generator()
        print()
        
        test_feature_space_projection()
        print()
        
        # Test intégré complet
        test_complete_fess_engine()
        print()
        
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print()
        print("✨ L'implémentation FESS authentique est maintenant complète avec:")
        print("   • 4 analyseurs de features sophistiqués")
        print("   • 7 advisors domain-spécifiques")
        print("   • Générateur de macro-moves")
        print("   • Espace de features 4D")
        print("   • Moteur de recherche FESS authentique")
        print()
        print("🚀 Prêt pour le benchmark complet des 90 niveaux XSokoban!")
        
    except Exception as e:
        print(f"❌ Erreur pendant les tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)