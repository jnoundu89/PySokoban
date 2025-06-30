#!/usr/bin/env python3
"""
Test script pour le debug visuel du niveau 1 original avec l'algorithme FESS.

Ce script utilise le debugger visuel FESS pour analyser étape par étape
la résolution du niveau 1 original, en mettant en évidence :
- Le découpage du niveau par l'algorithme
- La logique des 4 features FESS
- Les macro moves et leur impact
- La notation des coordonnées FESS
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.fess_visual_debugger import FESSVisualDebugger
from src.ai.authentic_fess_algorithm import SokobanState

def debug_level1_step_by_step():
    """Debug du niveau 1 original étape par étape."""
    print("🔬 Debug Visuel FESS - Niveau 1 Original")
    print("=" * 60)
    print("Référence: Figure 4 du document de recherche")
    print("Solution attendue: 97 pushes; 250 player moves → 9 macro moves")
    print("=" * 60)
    
    # Charger le niveau 1 original
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ Fichier non trouvé: {original_path}")
        return False
    
    try:
        # Parser la collection et obtenir le niveau 1
        collection = LevelCollectionParser.parse_file(original_path)
        level_title, level = collection.get_level(0)  # Premier niveau (index 0)
        
        print(f"📋 Niveau: {level_title}")
        print(f"📏 Taille: {level.width}x{level.height}")
        print(f"📦 Boîtes: {len(level.boxes)}")
        print(f"🎯 Cibles: {len(level.targets)}")
        
        # Créer le debugger visuel
        debugger = FESSVisualDebugger(level, max_time=30.0)
        
        print(f"\n🎮 Mode Debug Interactif Activé")
        print(f"⏸️  Le debugger s'arrêtera à chaque étape importante")
        print(f"📊 Vous verrez l'évolution des 4 features FESS en temps réel")
        
        # Demander le mode de debug
        response = input("\n❓ Voulez-vous un debug étape par étape ? (o/n): ").lower().strip()
        step_by_step = response in ['o', 'oui', 'y', 'yes', '']
        
        # Lancer le debug
        success, moves, stats = debugger.debug_solve(step_by_step=step_by_step)
        
        # Résultats du debug
        print(f"\n" + "=" * 60)
        print(f"📊 RÉSULTATS DU DEBUG")
        print(f"=" * 60)
        
        if success:
            print(f"✅ Solution trouvée!")
            print(f"🎯 Macro moves: {len(moves)}")
            print(f"🔍 Étapes de debug: {stats.get('debug_steps', 0)}")
            print(f"🌳 Nœuds explorés: {stats.get('nodes_expanded', 0)}")
            print(f"🗺️  Taille espace features: {stats.get('feature_space_size', 0)}")
            
            # Afficher la solution en notation FESS
            print(f"\n📝 Solution en Notation FESS:")
            for i, move in enumerate(moves):
                start_fess = debugger._pos_to_fess(move.box_start)
                end_fess = debugger._pos_to_fess(move.box_end)
                print(f"  {i+1}. ({start_fess}) → ({end_fess})")
            
            # Comparer avec la solution attendue du document
            expected_moves = [
                ("H5", "G5", "preparing a path to the upper room"),
                ("H4", "H3", "opening the upper room"),
                ("F5", "F7", "opening a path to the left room"),
                ("F8", "R7", "packing a box"),
                ("C8", "R8", "packing a box"),
                ("F7", "R9", "packing a box"),
                ("G5", "Q7", "packing a box"),
                ("F3", "Q8", "packing a box"),
                ("H3", "Q9", "packing a box")
            ]
            
            print(f"\n📋 Comparaison avec le Document de Recherche:")
            if len(moves) == len(expected_moves):
                print(f"✅ Nombre de macro moves correct: {len(moves)}")
            else:
                print(f"⚠️  Nombre de macro moves différent: {len(moves)} vs {len(expected_moves)} attendus")
            
        else:
            print(f"❌ Pas de solution trouvée dans le temps imparti")
            print(f"🔍 Étapes de debug: {stats.get('debug_steps', 0)}")
            print(f"🌳 Nœuds explorés: {stats.get('nodes_expanded', 0)}")
            print(f"⏰ Peut-être augmenter le temps limite...")
        
        # Afficher les insights du debug
        if debugger.debug_steps:
            print(f"\n🧠 Insights du Debug:")
            _display_debug_insights(debugger.debug_steps)
        
        return success
        
    except Exception as e:
        print(f"❌ Erreur lors du debug du niveau 1: {e}")
        import traceback
        traceback.print_exc()
        return False

def _display_debug_insights(debug_steps):
    """Affiche les insights tirés des étapes de debug."""
    if not debug_steps:
        return
    
    print(f"  📈 Évolution des Features:")
    
    # Analyser l'évolution du packing
    packing_values = [step.features.packing for step in debug_steps]
    packing_max = max(packing_values)
    packing_final = packing_values[-1]
    print(f"    • Packing: 0 → {packing_max} (max) → {packing_final} (final)")
    
    # Analyser l'évolution de la connectivité
    connectivity_values = [step.features.connectivity for step in debug_steps]
    connectivity_min = min(connectivity_values)
    connectivity_final = connectivity_values[-1]
    print(f"    • Connectivity: {connectivity_values[0]} → {connectivity_min} (min) → {connectivity_final} (final)")
    
    # Compter les macro moves par type (si on peut les déterminer)
    macro_moves = [step.macro_move for step in debug_steps if step.macro_move]
    print(f"  🎯 Macro Moves Analysés: {len(macro_moves)}")
    
    # Analyser les recommandations des conseillers
    advisor_counts = []
    for step in debug_steps:
        if step.advisor_recommendations:
            advisor_counts.append(len(step.advisor_recommendations))
    
    if advisor_counts:
        avg_advisors = sum(advisor_counts) / len(advisor_counts)
        print(f"  🤖 Conseillers: {avg_advisors:.1f} recommandations en moyenne par étape")

def debug_level1_analysis():
    """Analyse détaillée du niveau 1 sans debug interactif."""
    print(f"\n🔍 Analyse Détaillée du Niveau 1 (Mode Non-Interactif)")
    print("-" * 50)
    
    # Charger le niveau
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    collection = LevelCollectionParser.parse_file(original_path)
    level_title, level = collection.get_level(0)
    
    # Créer le debugger
    debugger = FESSVisualDebugger(level, max_time=60.0)
    
    # Analyser l'état initial
    initial_state = SokobanState(level)
    initial_features = debugger.fess_algorithm.feature_calculator.calculate_features(initial_state)
    
    print(f"📊 Analyse des Features Initiales:")
    print(f"  • Packing: {initial_features.packing} (aucune boîte emballée)")
    print(f"  • Connectivity: {initial_features.connectivity} (régions déconnectées)")
    print(f"  • Room Connectivity: {initial_features.room_connectivity} (passages bloqués)")
    print(f"  • Out-of-Plan: {initial_features.out_of_plan} (boîtes problématiques)")
    
    # Analyser les recommandations des conseillers
    advisor_moves = debugger.fess_algorithm.advisor.get_advisor_moves(initial_state, initial_features)
    print(f"\n🤖 Recommandations Initiales des Conseillers:")
    for i, move in enumerate(advisor_moves):
        start_fess = debugger._pos_to_fess(move.box_start)
        end_fess = debugger._pos_to_fess(move.box_end)
        print(f"  {i+1}. {start_fess} → {end_fess} (poids: {move.weight})")
    
    # Analyser la connectivité en détail
    print(f"\n🔗 Analyse de Connectivité Détaillée:")
    connectivity_regions = _analyze_connectivity_regions(initial_state)
    print(f"  • Nombre de régions: {len(connectivity_regions)}")
    for i, region in enumerate(connectivity_regions):
        print(f"    Région {i+1}: {len(region)} positions accessibles")
    
    # Résolution rapide pour voir la stratégie globale
    print(f"\n⚡ Résolution Rapide (Mode Analyse):")
    success, moves, stats = debugger.debug_solve(step_by_step=False)
    
    if success:
        print(f"✅ Solution trouvée en {stats.get('debug_steps', 0)} étapes")
        print(f"🎯 Stratégie identifiée: {len(moves)} macro moves")
    else:
        print(f"⏰ Analyse partielle effectuée")

def _analyze_connectivity_regions(state: SokobanState):
    """Analyse les régions de connectivité."""
    # Positions libres (pas de murs ou boîtes)
    free_positions = set()
    for x in range(state.width):
        for y in range(state.height):
            pos = (x, y)
            if state.is_valid_position(pos) and pos not in state.boxes:
                free_positions.add(pos)
    
    # Grouper en régions connectées
    regions = []
    visited = set()
    
    for pos in free_positions:
        if pos not in visited:
            # Nouvelle région
            region = set()
            stack = [pos]
            
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                
                visited.add(current)
                region.add(current)
                
                # Vérifier les voisins
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    neighbor = (current[0] + dx, current[1] + dy)
                    if neighbor in free_positions and neighbor not in visited:
                        stack.append(neighbor)
            
            if region:
                regions.append(region)
    
    return regions

def main():
    """Lance le debug visuel du niveau 1."""
    print("🎮 FESS Visual Debug - Niveau 1 Original")
    print("=" * 70)
    print("Debug visuel de l'algorithme FESS sur le niveau 1 original")
    print("avec analyse des features et notation des coordonnées")
    print("=" * 70)
    
    # Menu de choix
    print(f"\n📋 Options de Debug:")
    print(f"1. Debug étape par étape (interactif)")
    print(f"2. Debug rapide avec analyse")
    print(f"3. Les deux modes")
    
    choice = input("\n❓ Votre choix (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        print(f"\n" + "="*50)
        success1 = debug_level1_step_by_step()
    else:
        success1 = True
    
    if choice in ['2', '3']:
        print(f"\n" + "="*50)
        debug_level1_analysis()
    
    print(f"\n" + "="*70)
    print(f"📊 DEBUG VISUEL TERMINÉ")
    print(f"="*70)
    
    if choice in ['1', '3']:
        if success1:
            print(f"✅ Debug étape par étape: Succès")
            print(f"🎯 Le niveau 1 a été résolu avec visualisation complète")
            print(f"📚 Les features FESS et macro moves ont été tracés")
        else:
            print(f"⚠️  Debug étape par étape: Partiellement réussi")
    
    print(f"\n💡 Insights Clés:")
    print(f"  • L'algorithme FESS utilise 4 features pour guider la recherche")
    print(f"  • Les macro moves permettent une abstraction efficace")
    print(f"  • La notation des coordonnées FESS facilite l'analyse")
    print(f"  • Les conseillers recommandent les mouvements prioritaires")

if __name__ == "__main__":
    main()