#!/usr/bin/env python3
"""
Test de debugging pour les problèmes IA identifiés.
"""

from src.core.level import Level
from src.ai.unified_ai_controller import UnifiedAIController, SolveRequest
from src.ai.algorithm_selector import Algorithm
import time

def test_trivial_level():
    """Test avec un niveau trivial pour diagnostiquer les problèmes IA."""
    print("🔍 DIAGNOSTIC IA - Test avec niveau trivial")
    print("=" * 50)
    
    # Niveau trivial : juste pousser une boîte sur une cible
    trivial_level_data = [
        "#####",
        "#@$·#", 
        "#####"
    ]
    
    print("📦 Niveau de test :")
    for line in trivial_level_data:
        print(f"   {line}")
    print()
    
    try:
        # Créer le niveau
        level = Level(level_data="\n".join(trivial_level_data))
        print(f"✅ Niveau créé : {level.width}x{level.height}, {len(level.boxes)} boîtes, {len(level.targets)} cibles")
        
        # Initialiser le contrôleur IA
        ai_controller = UnifiedAIController()
        
        # Test 1: Recommandation d'algorithme
        print("\n🧠 Test 1: Analyse de complexité")
        recommendation = ai_controller.get_algorithm_recommendation(level)
        print(f"   Score de complexité: {recommendation['complexity_score']:.1f}")
        print(f"   Catégorie: {recommendation['complexity_category']}")
        print(f"   Algorithme recommandé: {recommendation['recommended_algorithm'].value}")
        print(f"   Justification: {recommendation['reasoning']}")
        
        # Test 2: Résolution automatique
        print("\n🤖 Test 2: Résolution automatique")
        def progress_callback(message):
            print(f"   📍 {message}")
        
        start_time = time.time()
        result = ai_controller.solve_level_auto(level, progress_callback)
        end_time = time.time()
        
        print(f"\n📊 Résultats:")
        print(f"   Succès: {result.success}")
        print(f"   Temps total: {end_time - start_time:.3f}s")
        print(f"   Message d'erreur: {result.error_message}")
        
        if result.solution_data:
            print(f"   Solution trouvée: {len(result.solution_data.moves)} mouvements")
            print(f"   Algorithme utilisé: {result.solution_data.algorithm_used.value}")
            print(f"   Temps de résolution: {result.solution_data.solve_time:.3f}s")
            print(f"   États explorés: {result.solution_data.states_explored}")
            print(f"   Mouvements: {result.solution_data.moves}")
        else:
            print("   ❌ Aucune solution trouvée")
        
        # Test 3: Essayer chaque algorithme individuellement
        print("\n🔧 Test 3: Test individuel des algorithmes")
        algorithms_to_test = [Algorithm.FESS, Algorithm.BFS, Algorithm.ASTAR, Algorithm.GREEDY]
        
        for algorithm in algorithms_to_test:
            print(f"\n   Test avec {algorithm.value}:")
            try:
                # Créer un nouveau niveau pour chaque test
                test_level = Level(level_data="\n".join(trivial_level_data))
                
                request = SolveRequest(
                    level=test_level,
                    algorithm=algorithm,
                    time_limit=30.0,
                    collect_ml_metrics=False
                )
                
                alg_result = ai_controller.solve_level(request)
                
                if alg_result.success and alg_result.solution_data:
                    print(f"     ✅ Succès: {len(alg_result.solution_data.moves)} mouvements en {alg_result.solution_data.solve_time:.3f}s")
                    print(f"     Mouvements: {alg_result.solution_data.moves}")
                else:
                    print(f"     ❌ Échec: {alg_result.error_message}")
                    
            except Exception as e:
                print(f"     💥 Erreur: {str(e)}")
        
        # Test 4: Vérification manuelle du niveau
        print("\n🔍 Test 4: Vérification manuelle")
        print(f"   Position joueur: {level.player_pos}")
        print(f"   Boîtes: {level.boxes}")
        print(f"   Cibles: {level.targets}")
        print(f"   Niveau résolu: {level.is_completed()}")
        
        # Essayer la solution manuelle évidente
        print("\n   🎯 Test de la solution évidente:")
        manual_level = Level(level_data="\n".join(trivial_level_data))
        print(f"   État initial - Boîtes: {manual_level.boxes}, Cibles: {manual_level.targets}")
        
        # Pour ce niveau, la solution devrait être un mouvement vers la droite
        success = manual_level.move(1, 0)  # Droite
        print(f"   Mouvement droite réussi: {success}")
        print(f"   État après mouvement - Boîtes: {manual_level.boxes}, Cibles: {manual_level.targets}")
        print(f"   Niveau résolu manuellement: {manual_level.is_completed()}")
        
    except Exception as e:
        print(f"💥 ERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()

def test_ai_features_menu():
    """Test des fonctionnalités du menu IA."""
    print("\n🎮 DIAGNOSTIC IA - Test du menu AI Features")
    print("=" * 50)
    
    try:
        from src.enhanced_main import EnhancedSokoban
        import pygame
        
        # Initialiser pygame sans affichage
        pygame.init()
        
        # Créer l'instance du jeu
        game = EnhancedSokoban()
        
        print("✅ EnhancedSokoban initialisé")
        
        # Tester si l'AI controller existe et fonctionne
        if hasattr(game, 'ai_controller'):
            print("✅ AI Controller disponible")
            
            # Test basique de fonctionnalité
            stats = game.ai_controller.get_solve_statistics()
            print(f"   Statistiques IA: {stats}")
        else:
            print("❌ AI Controller manquant")
        
        # Tester les méthodes IA du menu
        methods_to_test = [
            '_show_ai_features',
            '_show_ai_system_info', 
            '_run_ai_validation_tests',
            '_run_algorithm_benchmark',
            '_show_ai_statistics'
        ]
        
        for method_name in methods_to_test:
            if hasattr(game, method_name):
                print(f"✅ Méthode {method_name} disponible")
            else:
                print(f"❌ Méthode {method_name} manquante")
        
        pygame.quit()
        
    except Exception as e:
        print(f"💥 ERREUR lors du test des fonctionnalités IA: {str(e)}")

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DU DIAGNOSTIC IA")
    print("Objectif: Identifier pourquoi l'IA dit toujours que les niveaux sont trop difficiles")
    print()
    
    # Test du niveau trivial
    test_trivial_level()
    
    # Test des fonctionnalités du menu
    test_ai_features_menu()
    
    print("\n" + "=" * 50)
    print("🏁 DIAGNOSTIC TERMINÉ")
    print("Vérifiez les résultats ci-dessus pour identifier les problèmes.")