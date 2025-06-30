#!/usr/bin/env python3
"""
Test rapide de validation FESS sur des niveaux simples.

Ce test valide que notre implémentation FESS authentique fonctionne
sur quelques niveaux faciles avant de passer aux 90 niveaux complets.
"""

import time
import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.level import Level
from ai.authentic_fess import FESSSearchEngine


def test_simple_levels():
    """Test FESS sur des niveaux simples."""
    
    print("🔬 TEST RAPIDE DE VALIDATION FESS AUTHENTIQUE")
    print("=" * 60)
    
    # Niveau 1 : très simple (micro-cosmos)
    level1_data = """
    ####
    #.@#
    #$ #
    ####
    """
    
    # Niveau 2 : simple avec 2 boxes
    level2_data = """
    #####
    #   #
    # $$#
    # ..#
    # @ #
    #####
    """
    
    # Niveau 3 : Le niveau 1 des 90 niveaux (premier vrai niveau)
    level3_data = """
    #####
    #   #
    #$  #
  ###  $##
  #  $ $ #
### # ## #   ######
#   # ## #####  ..#
# $  $          ..#
##### ### #@##  ..#
    #     #########
    #######
    """
    
    test_levels = [
        ("Micro-niveau", level1_data),
        ("Niveau simple", level2_data), 
        ("Niveau 1 Original", level3_data)
    ]
    
    total_solved = 0
    total_time = 0
    
    for i, (name, level_data) in enumerate(test_levels, 1):
        print(f"\n[{i}/3] Test: {name}")
        print("-" * 40)
        
        try:
            # Créer le niveau
            level = Level(level_data=level_data.strip())
            print(f"   ✅ Niveau créé: {level.width}x{level.height}")
            print(f"   📦 Boxes: {len(level.boxes)}, Targets: {len(level.targets)}")
            
            # Afficher le niveau
            print("   🗺️  Carte:")
            for line in level.get_state_string().split('\n'):
                print(f"      {line}")
            
            # Créer et lancer FESS
            fess_engine = FESSSearchEngine(
                level=level,
                max_states=10000,  # Limite réduite pour test rapide
                time_limit=10.0    # 10 secondes max par niveau
            )
            
            print(f"   🔬 Lancement FESS...")
            start_time = time.time()
            
            def progress_callback(message):
                print(f"      {message}")
            
            solution = fess_engine.search(progress_callback)
            solve_time = time.time() - start_time
            
            # Résultats
            stats = fess_engine.get_statistics()
            
            if solution:
                total_solved += 1
                total_time += solve_time
                print(f"   ✅ RÉSOLU en {solve_time:.2f}s!")
                print(f"   📋 Solution: {len(solution)} mouvements")
                print(f"   📊 États explorés: {stats['search_statistics']['states_explored']:,}")
                print(f"   🔧 Cellules FS: {stats['feature_space_statistics']['total_cells']}")
                
                # Afficher la solution (si courte)
                if len(solution) <= 20:
                    print(f"   🎯 Mouvements: {' '.join(solution)}")
                else:
                    print(f"   🎯 Mouvements: {' '.join(solution[:10])}... (+{len(solution)-10})")
                    
            else:
                print(f"   ❌ Échec après {solve_time:.2f}s")
                print(f"   📊 États explorés: {stats['search_statistics']['states_explored']:,}")
                print(f"   ⚠️  Limite atteinte")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    # Rapport final
    print("\n" + "=" * 60)
    print("🏆 RAPPORT DE VALIDATION FESS")
    print("=" * 60)
    print(f"✅ Niveaux résolus: {total_solved}/{len(test_levels)}")
    if total_solved > 0:
        print(f"⚡ Temps total: {total_time:.2f}s")
        print(f"📈 Temps moyen: {total_time/total_solved:.2f}s par niveau")
    
    if total_solved == len(test_levels):
        print("\n🎯 VALIDATION RÉUSSIE!")
        print("   L'implémentation FESS authentique fonctionne correctement.")
        print("   Prêt pour le benchmark complet des 90 niveaux!")
    elif total_solved > 0:
        print(f"\n⚠️  VALIDATION PARTIELLE ({total_solved}/{len(test_levels)})")
        print("   L'implémentation FESS fonctionne mais peut nécessiter des optimisations.")
    else:
        print("\n❌ VALIDATION ÉCHOUÉE")
        print("   L'implémentation FESS nécessite des corrections.")
    
    return total_solved == len(test_levels)


def test_fess_components():
    """Test des composants individuels de FESS."""
    
    print("\n🔧 TEST DES COMPOSANTS FESS")
    print("=" * 40)
    
    # Créer un niveau simple pour tester
    level_data = """
    ####
    #.@#
    #$ #
    ####
    """
    
    try:
        level = Level(level_data=level_data.strip())
        
        # Test 1: Création du moteur FESS
        print("1. Création du moteur FESS...")
        fess_engine = FESSSearchEngine(level, max_states=1000, time_limit=5.0)
        print("   ✅ Moteur FESS créé")
        
        # Test 2: Analyseurs de features
        print("2. Test des analyseurs de features...")
        fs = fess_engine.feature_space
        
        # Test PackingAnalyzer
        print("   📦 PackingAnalyzer...")
        packing_stats = fs.packing_analyzer.get_statistics()
        print(f"      Targets: {packing_stats['total_targets']}")
        print(f"      Ordre optimal: {packing_stats['optimal_order']}")
        
        # Test ConnectivityAnalyzer  
        print("   🔗 ConnectivityAnalyzer...")
        conn_stats = fs.connectivity_analyzer.get_statistics()
        print(f"      Espaces libres: {conn_stats['total_free_spaces']}")
        
        # Test RoomAnalyzer
        print("   🏠 RoomAnalyzer...")
        room_stats = fs.room_analyzer.get_statistics()
        print(f"      Rooms détectées: {room_stats['total_rooms']}")
        
        # Test OutOfPlanAnalyzer
        print("   ⚠️  OutOfPlanAnalyzer...")
        oop_stats = fs.out_of_plan_analyzer.get_statistics()
        print(f"      Zones de risque: {oop_stats['total_risk_zones']}")
        
        print("   ✅ Tous les analyseurs fonctionnent")
        
        # Test 3: Projection d'état
        print("3. Test de projection d'état...")
        from ai.authentic_fess import FESSState
        initial_state = FESSState(level.player_pos, frozenset(level.boxes))
        fs_coords = fs.project_state(initial_state)
        print(f"   État initial projeté vers: {fs_coords}")
        print("   ✅ Projection d'état fonctionne")
        
        # Test 4: Arbre de recherche
        print("4. Test de l'arbre de recherche...")
        tree = fess_engine.search_tree
        tree.add_root(initial_state)
        print(f"   États dans l'arbre: {tree.total_states}")
        print("   ✅ Arbre de recherche fonctionne")
        
        print("\n✅ TOUS LES COMPOSANTS FONCTIONNENT!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR DANS LES COMPOSANTS: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal."""
    
    print("🔬 VALIDATION RAPIDE DE L'IMPLÉMENTATION FESS AUTHENTIQUE")
    print("Algorithme de Shoham & Schaeffer [2020]")
    print("=" * 70)
    
    # Test des composants
    components_ok = test_fess_components()
    
    if not components_ok:
        print("\n❌ Tests des composants échoués. Arrêt.")
        return
    
    # Test sur niveaux simples
    validation_ok = test_simple_levels()
    
    if validation_ok:
        print("\n🚀 PRÊT POUR LE BENCHMARK COMPLET!")
        print("Exécutez: python test_fess_90_levels_benchmark.py")
    else:
        print("\n🔧 Optimisations nécessaires avant le benchmark complet.")


if __name__ == "__main__":
    main()