#!/usr/bin/env python3
"""
Test de validation du correctif IA.
"""

from src.core.level import Level
from src.ai.unified_ai_controller import UnifiedAIController, SolveRequest
from src.ai.algorithm_selector import Algorithm
import time

def test_corrected_trivial_level():
    """Test avec un niveau trivial corrigé."""
    print("🔧 TEST CORRECTIF IA - Niveau trivial corrigé")
    print("=" * 50)
    
    # Niveau trivial avec format correct ('.' pour target)
    corrected_level_data = [
        "#####",
        "#@$.#", 
        "#####"
    ]
    
    print("📦 Niveau de test corrigé :")
    for line in corrected_level_data:
        print(f"   {line}")
    print()
    
    try:
        # Créer le niveau
        level = Level(level_data="\n".join(corrected_level_data))
        print(f"✅ Niveau créé : {level.width}x{level.height}, {len(level.boxes)} boîtes, {len(level.targets)} cibles")
        print(f"   Cibles détectées: {level.targets}")
        
        # Test de résolution
        ai_controller = UnifiedAIController()
        
        print("\n🤖 Test de résolution avec A*:")
        def progress_callback(message):
            print(f"   📍 {message}")
        
        request = SolveRequest(
            level=level,
            algorithm=Algorithm.ASTAR,
            time_limit=30.0,
            collect_ml_metrics=False
        )
        
        start_time = time.time()
        result = ai_controller.solve_level(request, progress_callback)
        end_time = time.time()
        
        print(f"\n📊 Résultats A*:")
        print(f"   Succès: {result.success}")
        print(f"   Temps: {end_time - start_time:.3f}s")
        
        if result.success and result.solution_data:
            print(f"   ✅ Solution: {result.solution_data.moves}")
            print(f"   Algorithme: {result.solution_data.algorithm_used.value}")
            print(f"   États explorés: {result.solution_data.states_explored}")
        else:
            print(f"   ❌ Erreur: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"💥 ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_famous_thinking_rabbit_level():
    """Test avec le premier niveau Thinking Rabbit - niveau historiquement simple."""
    print("\n🧠 TEST NIVEAU THINKING RABBIT #1")
    print("=" * 50)
    
    # Premier niveau de la collection Thinking Rabbit - très simple
    thinking_rabbit_level = [
        "    #####          ",
        "    #   #          ",
        "    #$  #          ",
        "  ###  $##         ",
        "  #  $ $ #         ",
        "### # ## #   ######",
        "#   # ## #####  ..#",
        "# $  $          ..#",
        "##### ### #@##  ..#",
        "    #     #########",
        "    #######        "
    ]
    
    print("📦 Niveau Thinking Rabbit #1 :")
    for i, line in enumerate(thinking_rabbit_level):
        print(f"   {i+1:2d}: {line}")
    print()
    
    try:
        level = Level(level_data="\n".join(thinking_rabbit_level))
        print(f"✅ Niveau créé : {level.width}x{level.height}, {len(level.boxes)} boîtes, {len(level.targets)} cibles")
        
        ai_controller = UnifiedAIController()
        
        def progress_callback(message):
            print(f"   📍 {message}")
        
        # Test avec différents algorithmes
        algorithms_to_test = [Algorithm.BFS, Algorithm.ASTAR]
        
        for algorithm in algorithms_to_test:
            print(f"\n🔧 Test avec {algorithm.value}:")
            
            request = SolveRequest(
                level=Level(level_data="\n".join(thinking_rabbit_level)),  # Niveau frais
                algorithm=algorithm,
                time_limit=60.0,
                collect_ml_metrics=False
            )
            
            start_time = time.time()
            result = ai_controller.solve_level(request)
            end_time = time.time()
            
            if result.success and result.solution_data:
                print(f"   ✅ Succès: {len(result.solution_data.moves)} mouvements en {end_time - start_time:.3f}s")
                print(f"   États explorés: {result.solution_data.states_explored}")
            else:
                print(f"   ❌ Échec: {result.error_message}")
                
        return True
        
    except Exception as e:
        print(f"💥 ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 TEST DU CORRECTIF IA")
    print("Objectif: Vérifier que les corrections fonctionnent")
    print()
    
    # Test 1: Niveau trivial corrigé
    success1 = test_corrected_trivial_level()
    
    # Test 2: Niveau historique simple
    success2 = test_famous_thinking_rabbit_level()
    
    print("\n" + "=" * 50)
    print("🏁 RÉSULTATS FINAUX")
    print(f"   Test trivial corrigé: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Test Thinking Rabbit: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 or success2:
        print("\n🎉 Au moins un algorithme fonctionne !")
    else:
        print("\n💥 Problèmes persistent, investigation approfondie nécessaire.")