#!/usr/bin/env python3
"""
Debug de l'algorithme de recherche FESS pour identifier pourquoi il n'explore pas d'états.
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.level import Level
from ai.authentic_fess import FESSSearchEngine, FESSState


def debug_fess_search():
    """Debug step-by-step de l'algorithme FESS."""
    
    print("🔍 DEBUG DE L'ALGORITHME DE RECHERCHE FESS")
    print("=" * 60)
    
    # Niveau ultra-simple pour debug
    level_data = """
    ####
    #.@#
    #$ #
    ####
    """
    
    try:
        # Créer le niveau et le moteur
        level = Level(level_data=level_data.strip())
        fess_engine = FESSSearchEngine(level, max_states=100, time_limit=5.0)
        
        print(f"📋 Niveau: {level.width}x{level.height}")
        print(f"📦 Boxes: {level.boxes}")
        print(f"🎯 Targets: {level.targets}")
        print(f"👤 Player: {level.player_pos}")
        
        # Debug étape par étape
        print("\n🔬 ÉTAPES DE L'ALGORITHME FESS:")
        print("-" * 40)
        
        # Étape 1: État initial
        print("1. Création de l'état initial...")
        initial_state = FESSState(level.player_pos, frozenset(level.boxes))
        print(f"   État initial: player={initial_state.player_pos}, boxes={initial_state.boxes}")
        
        # Étape 2: Projection dans l'espace de features
        print("2. Projection dans l'espace de features...")
        fs_coords = fess_engine.feature_space.project_state(initial_state)
        print(f"   Coordonnées FS: {fs_coords}")
        
        # Étape 3: Ajout à l'arbre et à l'espace de features
        print("3. Ajout à l'arbre de recherche...")
        fess_engine.search_tree.add_root(initial_state)
        fess_engine.feature_space.add_state_to_cell(initial_state)
        print(f"   États dans l'arbre: {fess_engine.search_tree.total_states}")
        print(f"   Cellules FS non-vides: {len(fess_engine.feature_space.non_empty_cells)}")
        
        # Étape 4: Assignment des poids aux mouvements
        print("4. Assignment des poids aux mouvements...")
        fess_engine._assign_move_weights(initial_state)
        print(f"   Mouvements disponibles: {initial_state.children_moves}")
        
        # Étape 5: Test du cycling des cellules
        print("5. Test du cycling des cellules...")
        for i in range(5):
            cell = fess_engine.feature_space.get_next_cell_for_cycling()
            print(f"   Cycle {i+1}: {cell}")
            if cell is None:
                print("   ❌ Aucune cellule retournée!")
                break
        
        # Étape 6: Test de la sélection de mouvements
        print("6. Test de la sélection de mouvements...")
        current_fs_cell = fess_engine.feature_space.get_next_cell_for_cycling()
        if current_fs_cell:
            states_in_cell = fess_engine.feature_space.get_states_in_cell(current_fs_cell)
            print(f"   États dans la cellule {current_fs_cell}: {len(states_in_cell)}")
            
            best_move_info = fess_engine._find_least_weight_unexpanded_move(states_in_cell)
            print(f"   Meilleur mouvement: {best_move_info}")
            
            if best_move_info:
                parent_state, move, weight = best_move_info
                print(f"   Parent: {parent_state.player_pos}")
                print(f"   Mouvement: {move} (poids: {weight})")
                
                # Étape 7: Test d'application du mouvement
                print("7. Test d'application du mouvement...")
                new_state = fess_engine._apply_move(parent_state, move, weight)
                if new_state:
                    print(f"   Nouvel état: player={new_state.player_pos}, boxes={new_state.boxes}")
                    print(f"   Poids accumulé: {new_state.accumulated_weight}")
                else:
                    print("   ❌ Mouvement invalide!")
        else:
            print("   ❌ Aucune cellule disponible pour le cycling!")
        
        # Étape 8: Simuler quelques itérations de la boucle principale
        print("\n8. Simulation de la boucle principale...")
        iterations = 0
        max_iterations = 10
        
        while iterations < max_iterations:
            current_fs_cell = fess_engine.feature_space.get_next_cell_for_cycling()
            if current_fs_cell is None:
                print(f"   Itération {iterations+1}: Aucune cellule disponible - ARRÊT")
                break
                
            states_in_cell = fess_engine.feature_space.get_states_in_cell(current_fs_cell)
            best_move_info = fess_engine._find_least_weight_unexpanded_move(states_in_cell)
            
            if best_move_info is None:
                print(f"   Itération {iterations+1}: Aucun mouvement disponible dans {current_fs_cell}")
                iterations += 1
                continue
                
            parent_state, move, weight = best_move_info
            new_state = fess_engine._apply_move(parent_state, move, weight)
            
            if new_state is None:
                print(f"   Itération {iterations+1}: Mouvement {move} invalide")
                iterations += 1
                continue
                
            new_state.accumulated_weight = parent_state.accumulated_weight + weight
            
            if fess_engine.search_tree.add_state(new_state):
                fess_engine.feature_space.add_state_to_cell(new_state)
                fess_engine._assign_move_weights(new_state)
                
                print(f"   Itération {iterations+1}: Nouvel état ajouté")
                print(f"      Mouvement: {move}")
                print(f"      Position: {new_state.player_pos}")
                print(f"      Poids: {new_state.accumulated_weight}")
                print(f"      Total états: {fess_engine.search_tree.total_states}")
                
                # Vérifier si c'est l'objectif
                if fess_engine._is_goal_state(new_state):
                    print(f"   🎯 OBJECTIF ATTEINT!")
                    break
            else:
                print(f"   Itération {iterations+1}: État déjà visité")
                
            iterations += 1
        
        print(f"\n📊 RÉSUMÉ DU DEBUG:")
        print(f"   Itérations: {iterations}")
        print(f"   États total: {fess_engine.search_tree.total_states}")
        print(f"   Cellules FS: {len(fess_engine.feature_space.non_empty_cells)}")
        
        # Diagnostiquer les problèmes potentiels
        print(f"\n🔧 DIAGNOSTIC:")
        if len(fess_engine.feature_space.non_empty_cells) == 0:
            print("   ❌ PROBLÈME: Aucune cellule FS non-vide")
        if initial_state.children_moves == []:
            print("   ❌ PROBLÈME: Aucun mouvement généré pour l'état initial")
        if iterations == 0:
            print("   ❌ PROBLÈME: Boucle principale ne démarre pas")
        elif iterations < 3:
            print("   ❌ PROBLÈME: Boucle principale se termine trop tôt")
        else:
            print("   ✅ Boucle principale fonctionne")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_fess_search()