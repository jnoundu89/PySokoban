#!/usr/bin/env python3
"""
BENCHMARK FINAL FESS AUTHENTIQUE - 90 NIVEAUX ORIGINAL & EXTRA
Version optimisée avec paramètres adaptatifs selon la complexité.

Ce test final valide que notre implémentation du vrai FESS de Shoham & Schaeffer [2020]
peut résoudre un maximum des 90 niveaux de référence avec des performances réalistes.
"""

import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.level import Level
from ai.authentic_fess import FESSSearchEngine


@dataclass
class LevelResult:
    """Résultat de benchmark pour un niveau."""
    level_number: int
    title: str
    solved: bool
    solve_time: float
    moves_count: int
    states_explored: int
    states_generated: int
    complexity_score: int
    time_limit_used: float
    states_limit_used: int
    error_message: Optional[str] = None


class FESSFinalBenchmarkRunner:
    """Gestionnaire de benchmark final FESS avec paramètres adaptatifs."""
    
    def __init__(self, levels_file: str = "src/levels/Original & Extra/Original.txt"):
        self.levels_file = levels_file
        self.levels = []
        self.results = []
        self.total_start_time = 0
        
    def load_levels(self) -> int:
        """Charge tous les niveaux depuis le fichier."""
        print("📁 Chargement des 90 niveaux Original & Extra...")
        
        try:
            with open(self.levels_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {self.levels_file}")
            return 0
        
        self.levels = self._parse_levels(content)
        print(f"✅ {len(self.levels)} niveaux chargés avec succès")
        return len(self.levels)
    
    def _parse_levels(self, content: str) -> List[Dict[str, Any]]:
        """Parse le fichier de niveaux et retourne une liste de niveaux."""
        levels = []
        lines = content.strip().split('\n')
        
        current_level = None
        current_map = []
        level_number = 0
        in_map_section = False
        
        for line in lines:
            line = line.rstrip()
            
            if line.startswith("Title:"):
                if current_level is not None and current_map:
                    current_level['map_data'] = [l for l in current_map if l.strip()]
                    if current_level['map_data']:
                        levels.append(current_level)
                
                title = line[6:].strip()
                
                if title == "Original & Extra":
                    level_number = 1
                elif title.isdigit():
                    level_number = int(title)
                else:
                    level_number += 1
                    
                current_level = {
                    'level_number': level_number,
                    'title': title if not title.isdigit() else f"Level {title}",
                    'description': "",
                    'author': ""
                }
                current_map = []
                in_map_section = False
                
            elif line.startswith("Description:"):
                if current_level:
                    current_level['description'] = line[12:].strip()
                    
            elif line.startswith("Author:"):
                if current_level:
                    current_level['author'] = line[7:].strip()
                    
            elif current_level is not None:
                if line.strip() == "":
                    if in_map_section:
                        current_map.append(line)
                elif any(c in line for c in '#@$.*+ '):
                    current_map.append(line)
                    in_map_section = True
        
        if current_level is not None and current_map:
            current_level['map_data'] = [l for l in current_map if l.strip()]
            if current_level['map_data']:
                levels.append(current_level)
        
        return levels
    
    def _calculate_level_complexity(self, level: Level) -> int:
        """Calcule un score de complexité pour adapter les paramètres."""
        return len(level.boxes) * level.width * level.height
    
    def _get_adaptive_parameters(self, complexity_score: int) -> tuple:
        """Retourne les paramètres adaptatifs selon la complexité."""
        if complexity_score > 8000:
            # Niveaux extrêmement complexes
            return 300.0, 500000  # 5 min, 500k états
        elif complexity_score > 5000:
            # Niveaux très complexes  
            return 180.0, 300000  # 3 min, 300k états
        elif complexity_score > 2000:
            # Niveaux complexes
            return 120.0, 200000  # 2 min, 200k états
        elif complexity_score > 1000:
            # Niveaux modérés
            return 60.0, 100000   # 1 min, 100k états
        else:
            # Niveaux simples
            return 30.0, 50000    # 30s, 50k états
    
    def run_benchmark(self, max_levels: int = 90) -> Dict[str, Any]:
        """Exécute le benchmark final sur les niveaux."""
        if not self.levels:
            print("❌ Aucun niveau chargé. Appelez load_levels() d'abord.")
            return {}
        
        levels_to_test = min(max_levels, len(self.levels))
        
        print(f"\n🏆 BENCHMARK FINAL FESS SUR {levels_to_test} NIVEAUX")
        print(f"Algorithme authentique de Shoham & Schaeffer [2020]")
        print("=" * 80)
        
        self.total_start_time = time.time()
        self.results = []
        
        solved_count = 0
        total_moves = 0
        total_time = 0
        
        for i, level_data in enumerate(self.levels[:levels_to_test], 1):
            print(f"\n[{i:2d}/{levels_to_test}] Niveau {level_data['level_number']:2d}: {level_data['title']}")
            
            result = self._solve_single_level(level_data)
            self.results.append(result)
            
            if result.solved:
                solved_count += 1
                total_moves += result.moves_count
                total_time += result.solve_time
                
                print(f"✅ RÉSOLU en {result.solve_time:.2f}s "
                      f"({result.moves_count} mouvements, "
                      f"{result.states_explored:,} états, "
                      f"complexité={result.complexity_score})")
            else:
                print(f"❌ Échec: {result.error_message}")
                print(f"   Complexité: {result.complexity_score}, "
                      f"Limite: {result.time_limit_used:.0f}s, "
                      f"États: {result.states_explored:,}")
            
            # Résumé progressif
            if i % 10 == 0:
                success_rate = solved_count / i * 100
                print(f"\n📊 Résumé après {i} niveaux:")
                print(f"   Résolus: {solved_count}/{i} ({success_rate:.1f}%)")
                if solved_count > 0:
                    print(f"   Temps moyen: {total_time/solved_count:.2f}s")
                    print(f"   Mouvements moyens: {total_moves/solved_count:.1f}")
        
        total_benchmark_time = time.time() - self.total_start_time
        return self._generate_final_report(total_benchmark_time)
    
    def _solve_single_level(self, level_data: Dict[str, Any]) -> LevelResult:
        """Résout un niveau unique avec FESS adaptatif."""
        try:
            # Créer l'objet Level
            level_string = '\n'.join(level_data['map_data'])
            level = Level(level_data=level_string)
            
            # Calculer la complexité et adapter les paramètres
            complexity_score = self._calculate_level_complexity(level)
            time_limit, max_states = self._get_adaptive_parameters(complexity_score)
            
            # Créer le moteur FESS
            fess_engine = FESSSearchEngine(
                level=level,
                max_states=max_states,
                time_limit=time_limit
            )
            
            # Résoudre avec FESS
            start_time = time.time()
            solution = fess_engine.search()
            solve_time = time.time() - start_time
            
            # Obtenir les statistiques
            stats = fess_engine.get_statistics()
            
            return LevelResult(
                level_number=level_data['level_number'],
                title=level_data['title'],
                solved=solution is not None,
                solve_time=solve_time,
                moves_count=len(solution) if solution else 0,
                states_explored=stats['search_statistics']['states_explored'],
                states_generated=stats['search_statistics']['states_generated'],
                complexity_score=complexity_score,
                time_limit_used=time_limit,
                states_limit_used=max_states,
                error_message=None if solution else "Limite de temps/états atteinte"
            )
                
        except Exception as e:
            return LevelResult(
                level_number=level_data['level_number'],
                title=level_data['title'],
                solved=False,
                solve_time=0,
                moves_count=0,
                states_explored=0,
                states_generated=0,
                complexity_score=0,
                time_limit_used=60.0,
                states_limit_used=100000,
                error_message=str(e)
            )
    
    def _generate_final_report(self, total_time: float) -> Dict[str, Any]:
        """Génère le rapport final du benchmark."""
        solved_results = [r for r in self.results if r.solved]
        failed_results = [r for r in self.results if not r.solved]
        
        # Analyser les niveaux par complexité
        simple_levels = [r for r in self.results if r.complexity_score <= 1000]
        moderate_levels = [r for r in self.results if 1000 < r.complexity_score <= 2000]
        complex_levels = [r for r in self.results if 2000 < r.complexity_score <= 5000]
        very_complex_levels = [r for r in self.results if r.complexity_score > 5000]
        
        simple_solved = len([r for r in simple_levels if r.solved])
        moderate_solved = len([r for r in moderate_levels if r.solved])
        complex_solved = len([r for r in complex_levels if r.solved])
        very_complex_solved = len([r for r in very_complex_levels if r.solved])
        
        report = {
            'benchmark_info': {
                'algorithm': 'FESS_AUTHENTIC_FINAL',
                'total_levels': len(self.results),
                'total_benchmark_time': total_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'overall_performance': {
                'levels_solved': len(solved_results),
                'levels_failed': len(failed_results),
                'success_rate': len(solved_results) / len(self.results) * 100 if self.results else 0,
                'total_solve_time': sum(r.solve_time for r in solved_results),
                'average_solve_time': sum(r.solve_time for r in solved_results) / len(solved_results) if solved_results else 0,
                'total_moves': sum(r.moves_count for r in solved_results),
                'average_moves': sum(r.moves_count for r in solved_results) / len(solved_results) if solved_results else 0,
                'total_states_explored': sum(r.states_explored for r in self.results),
                'average_states_explored': sum(r.states_explored for r in self.results) / len(self.results) if self.results else 0
            },
            'complexity_analysis': {
                'simple_levels': {'total': len(simple_levels), 'solved': simple_solved, 'rate': simple_solved/len(simple_levels)*100 if simple_levels else 0},
                'moderate_levels': {'total': len(moderate_levels), 'solved': moderate_solved, 'rate': moderate_solved/len(moderate_levels)*100 if moderate_levels else 0},
                'complex_levels': {'total': len(complex_levels), 'solved': complex_solved, 'rate': complex_solved/len(complex_levels)*100 if complex_levels else 0},
                'very_complex_levels': {'total': len(very_complex_levels), 'solved': very_complex_solved, 'rate': very_complex_solved/len(very_complex_levels)*100 if very_complex_levels else 0}
            }
        }
        
        self._print_final_report(report)
        return report
    
    def _print_final_report(self, report: Dict[str, Any]):
        """Affiche le rapport final avec analyse de complexité."""
        print("\n" + "=" * 80)
        print("🏆 RAPPORT FINAL - FESS AUTHENTIQUE BENCHMARK")
        print("=" * 80)
        
        overall = report['overall_performance']
        complexity = report['complexity_analysis']
        info = report['benchmark_info']
        
        print(f"\n📊 RÉSULTATS GLOBAUX:")
        print(f"   Niveaux résolus: {overall['levels_solved']}/{info['total_levels']} ({overall['success_rate']:.1f}%)")
        print(f"   Temps total benchmark: {info['total_benchmark_time']:.1f}s")
        print(f"   Temps total résolution: {overall['total_solve_time']:.1f}s")
        
        print(f"\n🎯 ANALYSE PAR COMPLEXITÉ:")
        print(f"   Simples (≤1000):    {complexity['simple_levels']['solved']:2d}/{complexity['simple_levels']['total']:2d} ({complexity['simple_levels']['rate']:5.1f}%)")
        print(f"   Modérés (1k-2k):     {complexity['moderate_levels']['solved']:2d}/{complexity['moderate_levels']['total']:2d} ({complexity['moderate_levels']['rate']:5.1f}%)")
        print(f"   Complexes (2k-5k):   {complexity['complex_levels']['solved']:2d}/{complexity['complex_levels']['total']:2d} ({complexity['complex_levels']['rate']:5.1f}%)")
        print(f"   Très complexes (>5k): {complexity['very_complex_levels']['solved']:2d}/{complexity['very_complex_levels']['total']:2d} ({complexity['very_complex_levels']['rate']:5.1f}%)")
        
        if overall['levels_solved'] > 0:
            print(f"\n⚡ PERFORMANCES MOYENNES:")
            print(f"   Temps par niveau: {overall['average_solve_time']:.2f}s")
            print(f"   Mouvements par niveau: {overall['average_moves']:.1f}")
            print(f"   États explorés par niveau: {overall['average_states_explored']:,.0f}")
        
        print(f"\n📖 VALIDATION FESS AUTHENTIQUE:")
        if overall['success_rate'] >= 80:
            print(f"   ✅ EXCELLENT: {overall['success_rate']:.1f}% de réussite!")
            print(f"   ✅ FESS authentique fonctionne remarquablement bien")
        elif overall['success_rate'] >= 60:
            print(f"   ✅ TRÈS BON: {overall['success_rate']:.1f}% de réussite")
            print(f"   ✅ FESS authentique démontre sa puissance")
        elif overall['success_rate'] >= 40:
            print(f"   ⚠️  BON: {overall['success_rate']:.1f}% de réussite")
            print(f"   ⚠️  FESS fonctionne mais limité par la complexité")
        else:
            print(f"   ❌ PERFECTIBLE: {overall['success_rate']:.1f}% de réussite")
            print(f"   ❌ Optimisations supplémentaires nécessaires")


def main():
    """Point d'entrée principal du benchmark final."""
    print("🏆 BENCHMARK FINAL FESS AUTHENTIQUE")
    print("Algorithme de Shoham & Schaeffer [2020] - Paramètres adaptatifs")
    print("=" * 70)
    
    runner = FESSFinalBenchmarkRunner()
    
    if runner.load_levels() == 0:
        print("❌ Impossible de charger les niveaux")
        return
    
    # Option: test sur un sous-ensemble pour validation rapide
    print(f"\nOptions de test:")
    print(f"1. Test complet (90 niveaux) - Peut prendre plusieurs heures")
    print(f"2. Test rapide (20 premiers niveaux) - ~30 minutes")
    print(f"3. Test échantillon (10 premiers niveaux) - ~10 minutes")
    
    choice = input("\nChoisissez (1/2/3) [défaut: 3]: ").strip()
    
    if choice == "1":
        max_levels = 90
    elif choice == "2":
        max_levels = 20
    else:
        max_levels = 10
    
    print(f"\n🚀 Démarrage du benchmark sur {max_levels} niveaux...")
    
    results = runner.run_benchmark(max_levels)
    
    # Sauvegarder les résultats
    filename = f"fess_final_benchmark_{max_levels}levels.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Résultats sauvegardés dans {filename}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    print(f"\n🎯 BENCHMARK FINAL TERMINÉ!")


if __name__ == "__main__":
    main()