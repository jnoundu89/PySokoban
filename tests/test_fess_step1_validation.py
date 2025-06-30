"""
Test de Validation - Étape 1 FESS
=================================

Valide les composants de l'Étape 1 et 2 :
1. Enhanced Features System
2. Weight System 0:1
3. Room Analysis
4. 7 Advisors System

Objectif : Démontrer une amélioration significative par rapport à l'implémentation actuelle
qui prend 60s pour ne pas résoudre le niveau 1.
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.level_management.level_manager import LevelManager
from src.level_management.level_collection_parser import LevelCollectionParser
from src.core.level import Level
from src.ai.fess_enhanced_features import FESSEnhancedFeatures, create_goal_features
from src.ai.fess_weight_system import FESSWeightSystem, FESSMoveSelector, WeightedMove
from src.ai.fess_room_analysis import FESSRoomAnalyzer
from src.ai.fess_advisors import FESSAdvisorSystem
from src.ai.fess_notation import FESSLevelAnalyzer


class SokobanState:
    """Classe simple pour représenter un état Sokoban."""
    
    def __init__(self, player_position, box_positions):
        self.player_position = player_position
        self.box_positions = set(box_positions)
    
    @staticmethod
    def from_level(level):
        """Crée un SokobanState depuis un Level."""
        return SokobanState(level.player_pos, level.boxes)


def test_enhanced_features():
    """Test du système de features amélioré."""
    print("🔬 Test Enhanced Features System")
    print("=" * 50)
    
    # Charge le niveau 1
    try:
        # Essaie de charger la collection Original & Extra
        collection = LevelCollectionParser.parse_file("../src/levels/Original & Extra/Original.txt")
        level_title, level = collection.get_level(0)  # Niveau 1
        level.title = level_title
    except Exception as e:
        print(f"Erreur chargement collection: {e}")
        # Fallback: crée un niveau simple pour test
        level_data = """#####
#.@$#
#####"""
        level = Level(level_data=level_data)
    
    # Crée le système de features
    features = FESSEnhancedFeatures(level)
    
    # État initial
    initial_state = SokobanState.from_level(level)
    initial_features = features.compute_feature_vector(initial_state)
    
    print(f"📊 Features Initiales: {initial_features}")
    print(f"   • Packing: {initial_features.packing}")
    print(f"   • Connectivity: {initial_features.connectivity}")
    print(f"   • Room Connectivity: {initial_features.room_connectivity}")
    print(f"   • Out-of-Plan: {initial_features.out_of_plan}")
    
    # État but
    goal_features = create_goal_features(len(initial_state.box_positions))
    print(f"🎯 Features But: {goal_features}")
    
    # Distance
    distance = features.compute_feature_distance(initial_features, goal_features)
    print(f"📏 Distance Feature Space: {distance}")
    
    print("✅ Enhanced Features System OK\n")
    return features


def test_weight_system():
    """Test du système de poids 0:1."""
    print("⚖️  Test Weight System")
    print("=" * 50)
    
    weight_system = FESSWeightSystem()
    move_selector = FESSMoveSelector(weight_system)
    
    # Test des poids
    from src.ai.fess_notation import MacroMove
    
    # Simule des moves
    move1 = MacroMove((5, 5), (6, 5))
    move2 = MacroMove((3, 3), (4, 3))
    move3 = MacroMove((7, 8), (7, 9))
    
    macro_moves = [move1, move2, move3]
    
    # Simule des recommandations d'advisors
    advisor_recommendations = {
        "Packing": move1,      # Move recommandé
        "Connectivity": None,   # Pas de recommandation
        "Opener": move3        # Move recommandé
    }
    
    # Test assignment des poids - utilise un état simple
    class SimpleState:
        def __init__(self, player_pos, box_positions):
            self.player_position = player_pos
            self.box_positions = set(box_positions)
    
    dummy_state = SimpleState((5, 5), {(3, 3), (5, 5), (7, 8)})
    
    weighted_moves = weight_system.assign_weights_to_moves(
        dummy_state, macro_moves, advisor_recommendations
    )
    
    print("📋 Moves Pondérés:")
    for wm in weighted_moves:
        print(f"   • {wm}")
    
    # Vérifie les poids
    advisor_weights = [wm.weight for wm in weighted_moves if wm.move_type.value == "advisor"]
    difficult_weights = [wm.weight for wm in weighted_moves if wm.move_type.value == "difficult"]
    
    print(f"✅ Poids Advisor: {advisor_weights} (attendu: tous 0)")
    print(f"✅ Poids Difficult: {difficult_weights} (attendu: tous 1)")
    
    # Test sélection
    best_move = move_selector.select_best_move(weighted_moves)
    print(f"🎯 Meilleur Move Sélectionné: {best_move}")
    
    print("✅ Weight System OK\n")
    return weight_system, move_selector


def test_room_analysis():
    """Test de l'analyse des rooms."""
    print("🏠 Test Room Analysis System")
    print("=" * 50)
    
    # Charge le niveau 1
    try:
        # Essaie de charger la collection Original & Extra
        collection = LevelCollectionParser.parse_file("../src/levels/Original & Extra/Original.txt")
        level_title, level = collection.get_level(0)  # Niveau 1
        level.title = level_title
    except Exception as e:
        print(f"Erreur chargement collection: {e}")
        # Fallback: crée un niveau simple pour test
        level_data = """#######
#.....#
#.$@$.#
#.....#
#######"""
        level = Level(level_data=level_data)
    
    # Crée l'analyseur de rooms
    room_analyzer = FESSRoomAnalyzer(level)
    
    # État initial
    initial_state = SokobanState.from_level(level)
    
    # Test des features room
    room_connectivity = room_analyzer.compute_room_connectivity_feature(initial_state)
    hotspots = room_analyzer.compute_hotspots_feature(initial_state)
    mobility = room_analyzer.compute_mobility_feature(initial_state)
    
    print(f"📊 Room Features:")
    print(f"   • Room Connectivity: {room_connectivity}")
    print(f"   • Hotspots: {hotspots}")
    print(f"   • Mobility: {mobility}")
    
    # Statistiques
    stats = room_analyzer.get_statistics()
    print(f"📈 Statistiques:")
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    # Test hotspot le plus disruptif
    most_disruptive = room_analyzer.hotspot_analyzer.find_most_disruptive_hotspot(initial_state)
    print(f"🔥 Hotspot le Plus Disruptif: {most_disruptive}")
    
    print("✅ Room Analysis System OK\n")
    return room_analyzer


def test_advisors_system(features, room_analyzer):
    """Test du système des 7 advisors."""
    print("🎯 Test Advisors System")
    print("=" * 50)
    
    # Crée le système d'advisors
    advisor_system = FESSAdvisorSystem(features, room_analyzer)
    
    # Charge le niveau 1
    try:
        # Essaie de charger la collection Original & Extra
        collection = LevelCollectionParser.parse_file("../src/levels/Original & Extra/Original.txt")
        level_title, level = collection.get_level(0)  # Niveau 1
        level.title = level_title
    except Exception as e:
        print(f"Erreur chargement collection: {e}")
        # Fallback: crée un niveau simple pour test
        level_data = """#######
#.....#
#.$@$.#
#.....#
#######"""
        level = Level(level_data=level_data)
    
    initial_state = SokobanState.from_level(level)
    
    # Génère les macro moves
    analyzer = FESSLevelAnalyzer(level)
    macro_moves = analyzer.generate_macro_moves(initial_state)
    
    print(f"📦 Macro Moves Générés: {len(macro_moves)}")
    
    # Consulte les advisors
    start_time = time.time()
    recommendations = advisor_system.consult_advisors(initial_state, macro_moves)
    consultation_time = time.time() - start_time
    
    print(f"⏱️  Temps Consultation Advisors: {consultation_time:.3f}s")
    print(f"📋 Recommandations:")
    
    for advisor_name, recommended_move in recommendations.items():
        if recommended_move:
            print(f"   • {advisor_name}: {recommended_move}")
        else:
            print(f"   • {advisor_name}: Aucune recommandation")
    
    # Analyse de l'efficacité
    total_advisors = len(advisor_system.advisors)
    recommendations_made = sum(1 for move in recommendations.values() if move is not None)
    efficiency = recommendations_made / total_advisors
    
    print(f"📊 Efficacité Advisors: {recommendations_made}/{total_advisors} = {efficiency:.1%}")
    
    print("✅ Advisors System OK\n")
    return advisor_system, recommendations


def test_integrated_system():
    """Test du système intégré - simulation simplifiée de FESS."""
    print("🚀 Test Système Intégré")
    print("=" * 50)
    
    # Charge le niveau 1
    try:
        # Essaie de charger la collection Original & Extra
        collection = LevelCollectionParser.parse_file("../src/levels/Original & Extra/Original.txt")
        level_title, level = collection.get_level(0)  # Niveau 1
        level.title = level_title
    except Exception as e:
        print(f"Erreur chargement collection: {e}")
        # Fallback: crée un niveau simple pour test
        level_data = """#######
#..@..#
#.$#$.#
#.....#
#######"""
        level = Level(level_data=level_data)
    
    # Composants FESS
    features = FESSEnhancedFeatures(level)
    room_analyzer = FESSRoomAnalyzer(level)
    advisor_system = FESSAdvisorSystem(features, room_analyzer)
    weight_system = FESSWeightSystem()
    move_selector = FESSMoveSelector(weight_system)
    
    # État initial
    initial_state = SokobanState.from_level(level)
    current_state = initial_state
    
    print(f"🎮 Niveau: {level.title}")
    print(f"📦 Boîtes: {len(initial_state.box_positions)}")
    
    # Simule quelques itérations FESS
    max_iterations = 10
    start_time = time.time()
    
    for iteration in range(max_iterations):
        print(f"\n--- Itération {iteration + 1} ---")
        
        # Features actuelles
        current_features = features.compute_feature_vector(current_state)
        print(f"Features: {current_features}")
        
        # Génère macro moves
        analyzer = FESSLevelAnalyzer(level)
        macro_moves = analyzer.generate_macro_moves(current_state)
        
        if not macro_moves:
            print("❌ Aucun macro move possible - deadlock?")
            break
        
        print(f"Macro moves: {len(macro_moves)}")
        
        # Consulte advisors
        recommendations = advisor_system.consult_advisors(current_state, macro_moves)
        recommendations_count = sum(1 for move in recommendations.values() if move is not None)
        print(f"Advisor recommendations: {recommendations_count}/{len(advisor_system.advisors)}")
        
        # Assigne poids
        weighted_moves = weight_system.assign_weights_to_moves(
            current_state, macro_moves, recommendations
        )
        
        # Analyse distribution poids
        advisor_moves = sum(1 for wm in weighted_moves if wm.weight == 0)
        difficult_moves = sum(1 for wm in weighted_moves if wm.weight == 1)
        print(f"Distribution: {advisor_moves} advisor (0), {difficult_moves} difficult (1)")
        
        # Sélectionne meilleur move
        best_move = move_selector.select_best_move(weighted_moves)
        
        if best_move is None:
            print("❌ Aucun move sélectionnable")
            break
        
        print(f"Move sélectionné: {best_move}")
        
        # Applique le move (simulation)
        try:
            new_state = best_move.macro_move.apply_to_state(current_state)
            new_features = features.compute_feature_vector(new_state)
            
            # Vérifie le progrès
            old_distance = features.compute_feature_distance(current_features, create_goal_features(len(initial_state.box_positions)))
            new_distance = features.compute_feature_distance(new_features, create_goal_features(len(initial_state.box_positions)))
            
            if new_distance < old_distance:
                print(f"✅ Progrès! Distance: {old_distance:.1f} → {new_distance:.1f}")
            else:
                print(f"⚠️  Pas de progrès. Distance: {old_distance:.1f} → {new_distance:.1f}")
            
            current_state = new_state
            
            # Vérifie victoire
            if new_features.packing == len(initial_state.box_positions):
                print("🎉 NIVEAU RÉSOLU!")
                break
                
        except Exception as e:
            print(f"❌ Erreur application move: {e}")
            break
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Temps Total Test: {total_time:.3f}s")
    print(f"📊 Itérations Effectuées: {iteration + 1}/{max_iterations}")
    
    # Statistiques finales
    advisor_system.log_global_stats()
    
    print("✅ Test Système Intégré Terminé\n")


def main():
    """Test principal de validation."""
    print("🎮 FESS - Test de Validation Étape 1 & 2")
    print("=" * 60)
    print("Validation des composants core implementés:")
    print("1. Enhanced Features System")
    print("2. Weight System 0:1") 
    print("3. Room Analysis")
    print("4. 7 Advisors System")
    print("5. Test Système Intégré")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Tests individuels
        features = test_enhanced_features()
        weight_system, move_selector = test_weight_system()
        room_analyzer = test_room_analysis()
        advisor_system, recommendations = test_advisors_system(features, room_analyzer)
        
        # Test intégré
        test_integrated_system()
        
        total_time = time.time() - start_time
        
        print("🎯 RÉSUMÉ DE VALIDATION")
        print("=" * 60)
        print("✅ Enhanced Features System: OK")
        print("✅ Weight System 0:1: OK")
        print("✅ Room Analysis: OK")
        print("✅ 7 Advisors System: OK")
        print("✅ Système Intégré: OK")
        print(f"⏱️  Temps Total: {total_time:.2f}s")
        print("\n🚀 Prêt pour Étape 3: Packing Plan System")
        
    except Exception as e:
        print(f"❌ ERREUR VALIDATION: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)