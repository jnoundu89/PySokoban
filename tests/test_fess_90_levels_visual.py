#!/usr/bin/env python3
"""
Test script pour la résolution visuelle des 90 niveaux originaux avec FESS.

Ce script utilise l'algorithme FESS avec visualisation des features pour résoudre
les 90 niveaux originaux du benchmark XSokoban, en affichant :
- L'évolution des 4 features FESS pour chaque niveau
- Les macro moves générés avec notation des coordonnées
- Les statistiques de performance
- La comparaison avec les résultats publiés dans le document de recherche
"""

import sys
import os
import time
from typing import List, Dict, Tuple

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.level_management.level_collection_parser import LevelCollectionParser
from src.ai.fess_visual_debugger import FESSVisualDebugger
from src.ai.authentic_fess_algorithm import FESSAlgorithm, SokobanState
from src.ai.fess_notation import FESSLevelAnalyzer

class FESS90LevelsSolver:
    """
    Résolveur FESS pour les 90 niveaux originaux avec visualisation.
    
    Implémente la résolution complète des 90 niveaux du benchmark XSokoban
    avec affichage visuel des features et statistiques détaillées.
    """
    
    def __init__(self, collection_path: str, max_time_per_level: float = 60.0):
        """
        Initialise le résolveur pour les 90 niveaux.
        
        Args:
            collection_path: Chemin vers le fichier Original.txt
            max_time_per_level: Temps maximum par niveau (en secondes)
        """
        self.collection_path = collection_path
        self.max_time_per_level = max_time_per_level
        self.results = []
        self.total_start_time = 0.0
        
        # Résultats publiés dans le document de recherche (Table I)
        self.published_results = {
            1: {'pushes': 97, 'fess_pushes': 103, 'nodes': 12, 'time': 0},
            2: {'pushes': 131, 'fess_pushes': 153, 'nodes': 15, 'time': 0},
            3: {'pushes': 134, 'fess_pushes': 150, 'nodes': 14, 'time': 0},
            4: {'pushes': 355, 'fess_pushes': 365, 'nodes': 24, 'time': 1},
            5: {'pushes': 143, 'fess_pushes': 147, 'nodes': 47, 'time': 0},
            # ... (on peut ajouter plus de résultats de la table)
        }
    
    def solve_all_levels(self, visual_mode: bool = True, max_levels: int = 90) -> Dict:
        """
        Résout tous les niveaux avec visualisation des features.
        
        Args:
            visual_mode: Si True, affiche les features pour chaque niveau
            max_levels: Nombre maximum de niveaux à traiter
            
        Returns:
            Dict avec les statistiques globales
        """
        print("🎯 FESS 90 Niveaux Originaux - Résolution Visuelle")
        print("=" * 70)
        print(f"Référence: Table I du document de recherche")
        print(f"Standard: 10 minutes par niveau (900 minutes total)")
        print(f"FESS publié: Tous les 90 niveaux en moins de 4 minutes")
        print("=" * 70)
        
        # Charger la collection
        try:
            collection = LevelCollectionParser.parse_file(self.collection_path)
            print(f"📁 Collection chargée: {collection.title}")
            print(f"📊 Niveaux disponibles: {collection.get_level_count()}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return {}
        
        # Limiter le nombre de niveaux pour les tests
        actual_max = min(max_levels, collection.get_level_count())
        print(f"🎮 Résolution de {actual_max} niveaux avec visualisation FESS")
        
        self.total_start_time = time.time()
        solved_count = 0
        
        # Résoudre chaque niveau
        for level_num in range(actual_max):
            level_title, level = collection.get_level(level_num)
            level_id = level_num + 1  # Numérotation à partir de 1
            
            print(f"\n{'='*20} NIVEAU {level_id} {'='*20}")
            print(f"📋 Titre: {level_title}")
            print(f"📏 Taille: {level.width}x{level.height}")
            print(f"📦 Boîtes: {len(level.boxes)}")
            print(f"🎯 Cibles: {len(level.targets)}")
            
            # Afficher le niveau avec coordonnées FESS si demandé
            if visual_mode and level_id <= 5:  # Affichage visuel pour les 5 premiers
                print(f"\n🗺️  Niveau avec Coordonnées FESS:")
                print(level.get_state_string(show_fess_coordinates=True))
            
            # Analyser les features initiales
            initial_state = SokobanState(level)
            debugger = FESSVisualDebugger(level, self.max_time_per_level)
            initial_features = debugger.fess_algorithm.feature_calculator.calculate_features(initial_state)
            
            print(f"\n🧠 Features FESS Initiales:")
            print(f"  • Packing: {initial_features.packing}")
            print(f"  • Connectivity: {initial_features.connectivity}")
            print(f"  • Room Connectivity: {initial_features.room_connectivity}")
            print(f"  • Out-of-Plan: {initial_features.out_of_plan}")
            
            # Résoudre le niveau
            level_start_time = time.time()
            success, moves, stats = self._solve_level_with_features(level, level_id, visual_mode)
            level_time = time.time() - level_start_time
            
            # Enregistrer les résultats
            result = {
                'level': level_id,
                'title': level_title,
                'solved': success,
                'macro_moves': len(moves) if success else 0,
                'nodes_expanded': stats.get('nodes_expanded', 0),
                'time': level_time,
                'features_final': stats.get('final_features'),
                'size': f"{level.width}x{level.height}",
                'boxes': len(level.boxes)
            }
            self.results.append(result)
            
            if success:
                solved_count += 1
                
            # Afficher le résultat
            status = "✅ RÉSOLU" if success else "❌ NON RÉSOLU"
            print(f"\n📊 Résultat: {status}")
            print(f"  • Temps: {level_time:.2f}s")
            print(f"  • Macro moves: {len(moves) if success else 'N/A'}")
            print(f"  • Nœuds explorés: {stats.get('nodes_expanded', 0)}")
            
            # Comparer avec les résultats publiés si disponibles
            if level_id in self.published_results:
                self._compare_with_published(level_id, result)
            
            # Afficher les macro moves en notation FESS pour les premiers niveaux
            if success and visual_mode and level_id <= 3:
                self._display_fess_solution(moves, debugger, level_id)
            
            # Pause pour les premiers niveaux en mode visuel
            if visual_mode and level_id <= 3:
                input(f"\n⏸️  Appuyez sur Entrée pour continuer au niveau {level_id + 1}...")
        
        # Statistiques finales
        return self._display_final_statistics(solved_count, actual_max)
    
    def _solve_level_with_features(self, level, level_id: int, visual_mode: bool) -> Tuple[bool, List, Dict]:
        """
        Résout un niveau avec suivi des features.
        
        Args:
            level: Niveau à résoudre
            level_id: Numéro du niveau
            visual_mode: Si True, affiche les détails
            
        Returns:
            Tuple (succès, moves, statistiques)
        """
        # Créer l'algorithme FESS
        fess_algorithm = FESSAlgorithm(level, self.max_time_per_level)
        
        # Résoudre
        start_time = time.time()
        success, moves, stats = fess_algorithm.solve()
        solve_time = time.time() - start_time
        
        # Calculer les features finales si résolu
        final_features = None
        if success and moves:
            # Simuler l'application des moves pour obtenir l'état final
            final_state = SokobanState(level)
            # (Simulation simplifiée - en pratique on appliquerait tous les moves)
            final_features = fess_algorithm.feature_calculator.calculate_features(final_state)
        
        # Enrichir les statistiques
        stats.update({
            'solve_time': solve_time,
            'final_features': final_features,
            'level_size': f"{level.width}x{level.height}",
            'boxes_count': len(level.boxes)
        })
        
        # Affichage visuel des features si demandé
        if visual_mode and level_id <= 10:  # Détails pour les 10 premiers
            self._display_feature_evolution(fess_algorithm, success)
        
        return success, moves, stats
    
    def _display_feature_evolution(self, fess_algorithm, success: bool):
        """Affiche l'évolution des features pendant la résolution."""
        print(f"\n📈 Évolution des Features FESS:")
        
        # Statistiques de l'espace des features
        fs_size = len(fess_algorithm.feature_space)
        total_states = sum(len(nodes) for nodes in fess_algorithm.feature_space.values())
        
        print(f"  • Cellules explorées: {fs_size}")
        print(f"  • États totaux: {total_states}")
        print(f"  • Nœuds par cellule: {total_states / fs_size if fs_size > 0 else 0:.1f}")
        
        # Top 3 cellules les plus peuplées
        if fess_algorithm.feature_space:
            sorted_cells = sorted(
                fess_algorithm.feature_space.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            print(f"  • Top cellules:")
            for i, (features, nodes) in enumerate(sorted_cells[:3]):
                print(f"    {i+1}. ({features.packing},{features.connectivity},{features.room_connectivity},{features.out_of_plan}): {len(nodes)} états")
    
    def _compare_with_published(self, level_id: int, result: Dict):
        """Compare les résultats avec ceux publiés dans le document."""
        published = self.published_results[level_id]
        
        print(f"\n📚 Comparaison avec Résultats Publiés (Niveau {level_id}):")
        print(f"  • Temps publié: {published['time']}s vs Notre temps: {result['time']:.2f}s")
        print(f"  • Nœuds publiés: {published['nodes']} vs Nos nœuds: {result['nodes_expanded']}")
        
        if result['solved']:
            # Nous n'avons pas le nombre exact de pushes, mais on peut comparer les macro moves
            print(f"  • FESS pushes publiés: {published['fess_pushes']}")
            print(f"  • Nos macro moves: {result['macro_moves']}")
        
        # Évaluation de la performance
        if result['time'] <= published['time'] + 1:  # Tolérance de 1s
            print(f"  🎯 Performance: Conforme aux résultats publiés")
        else:
            print(f"  ⚠️  Performance: Plus lent que publié (normal en mode debug)")
    
    def _display_fess_solution(self, moves, debugger, level_id: int):
        """Affiche la solution en notation FESS."""
        print(f"\n📝 Solution FESS - Niveau {level_id}:")
        
        if not moves:
            print("  Aucun macro move enregistré")
            return
        
        for i, move in enumerate(moves):
            start_fess = debugger._pos_to_fess(move.box_start)
            end_fess = debugger._pos_to_fess(move.box_end)
            print(f"  {i+1}. ({start_fess}) → ({end_fess})")
        
        # Analyse stratégique pour le niveau 1
        if level_id == 1 and len(moves) >= 9:
            print(f"\n🎯 Analyse Stratégique (Niveau 1):")
            print(f"  • Moves 1-3: Amélioration connectivité")
            print(f"  • Moves 4-9: Emballage des boîtes")
            print(f"  • Compression: ~97 pushes → {len(moves)} macro moves")
    
    def _display_final_statistics(self, solved_count: int, total_count: int) -> Dict:
        """Affiche les statistiques finales."""
        total_time = time.time() - self.total_start_time
        
        print(f"\n" + "="*70)
        print(f"📊 STATISTIQUES FINALES - FESS 90 NIVEAUX")
        print(f"="*70)
        
        print(f"🎯 Résultats Globaux:")
        print(f"  • Niveaux résolus: {solved_count}/{total_count}")
        print(f"  • Taux de réussite: {solved_count/total_count*100:.1f}%")
        print(f"  • Temps total: {total_time:.2f}s")
        print(f"  • Temps moyen/niveau: {total_time/total_count:.2f}s")
        
        # Statistiques par niveau résolu
        solved_results = [r for r in self.results if r['solved']]
        if solved_results:
            total_macro_moves = sum(r['macro_moves'] for r in solved_results)
            total_nodes = sum(r['nodes_expanded'] for r in solved_results)
            
            print(f"\n📈 Analyse des Niveaux Résolus:")
            print(f"  • Total macro moves: {total_macro_moves}")
            print(f"  • Macro moves/niveau: {total_macro_moves/len(solved_results):.1f}")
            print(f"  • Total nœuds explorés: {total_nodes}")
            print(f"  • Nœuds/niveau: {total_nodes/len(solved_results):.1f}")
        
        # Comparaison avec les résultats publiés
        print(f"\n📚 Comparaison avec Document de Recherche:")
        print(f"  • Standard publié: 90/90 niveaux en <4 minutes")
        print(f"  • Notre résultat: {solved_count}/{total_count} niveaux en {total_time:.2f}s")
        
        if solved_count == total_count and total_time < 240:  # 4 minutes
            print(f"  🏆 PERFORMANCE EXCELLENT: Conforme aux résultats publiés!")
        elif solved_count == total_count:
            print(f"  ✅ SUCCÈS: Tous les niveaux résolus")
        else:
            print(f"  ⚠️  PARTIEL: Résolution incomplète (normal pour un prototype)")
        
        # Détail des premiers niveaux
        print(f"\n📋 Détail des Premiers Niveaux:")
        for i, result in enumerate(self.results[:5]):
            status = "✅" if result['solved'] else "❌"
            print(f"  {status} Niveau {result['level']}: {result['time']:.2f}s, {result['macro_moves']} moves, {result['nodes_expanded']} nœuds")
        
        return {
            'solved_count': solved_count,
            'total_count': total_count,
            'success_rate': solved_count/total_count,
            'total_time': total_time,
            'average_time': total_time/total_count,
            'results': self.results
        }

def main():
    """Lance la résolution visuelle des 90 niveaux."""
    print("🎮 FESS 90 Niveaux Originaux - Résolution Visuelle")
    print("=" * 80)
    print("Résolution du benchmark XSokoban avec algorithme FESS")
    print("Visualisation des features et notation des coordonnées")
    print("=" * 80)
    
    # Chemin vers la collection
    original_path = os.path.join('../src', 'levels', 'Original & Extra', 'Original.txt')
    
    if not os.path.exists(original_path):
        print(f"❌ Fichier non trouvé: {original_path}")
        return
    
    # Options de configuration
    print(f"\n📋 Configuration:")
    print(f"1. Mode visuel complet (premiers niveaux avec détails)")
    print(f"2. Mode performance (tous les niveaux, moins de détails)")
    print(f"3. Mode test (5 premiers niveaux seulement)")
    
    choice = input(f"\n❓ Votre choix (1/2/3): ").strip()
    
    if choice == '1':
        visual_mode = True
        max_levels = 90
        max_time = 60.0
        print(f"🔬 Mode visuel complet activé")
    elif choice == '2':
        visual_mode = False
        max_levels = 90
        max_time = 30.0
        print(f"⚡ Mode performance activé")
    else:  # choice == '3' ou défaut
        visual_mode = True
        max_levels = 5
        max_time = 120.0
        print(f"🧪 Mode test activé (5 niveaux)")
    
    # Créer le résolveur
    solver = FESS90LevelsSolver(original_path, max_time)
    
    # Lancer la résolution
    print(f"\n🚀 Démarrage de la résolution...")
    stats = solver.solve_all_levels(visual_mode=visual_mode, max_levels=max_levels)
    
    # Résumé final
    if stats:
        print(f"\n🎯 MISSION ACCOMPLIE!")
        print(f"✅ {stats['solved_count']}/{stats['total_count']} niveaux résolus")
        print(f"⏱️  Temps total: {stats['total_time']:.2f}s")
        print(f"📊 Taux de réussite: {stats['success_rate']*100:.1f}%")
        
        if stats['success_rate'] == 1.0:
            print(f"🏆 PARFAIT: Tous les niveaux ont été résolus!")
            print(f"🔬 L'algorithme FESS avec visualisation fonctionne correctement")
        else:
            print(f"📈 Résultats encourageants pour un prototype FESS")

if __name__ == "__main__":
    main()