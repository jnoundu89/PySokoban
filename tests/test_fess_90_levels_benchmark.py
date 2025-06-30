#!/usr/bin/env python3
"""
Test de benchmark FESS authentique sur les 90 niveaux Original & Extra.

Ce test valide que notre implémentation du vrai FESS peut résoudre
tous les 90 niveaux de référence comme dans le paper de Shoham & Schaeffer [2020].

Selon le paper: "The FESS algorithm solved all 90 XSokoban levels in under 4 minutes."
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
    error_message: Optional[str] = None
    

class FESSBenchmarkRunner:
    """Gestionnaire de benchmark pour les 90 niveaux FESS."""
    
    def __init__(self, levels_file: str = "src/levels/Original & Extra/Original.txt"):
        self.levels_file = levels_file
        self.levels = []
        self.results = []
        self.total_start_time = 0
        
    def load_levels(self) -> int:
        """
        Charge tous les niveaux depuis le fichier.
        
        Returns:
            int: Nombre de niveaux chargés
        """
        print("📁 Chargement des 90 niveaux Original & Extra...")
        
        try:
            with open(self.levels_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {self.levels_file}")
            return 0
        
        # Parser le contenu pour extraire chaque niveau
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
            
            # Détecter le titre
            if line.startswith("Title:"):
                # Finaliser le niveau précédent s'il existe
                if current_level is not None and current_map:
                    current_level['map_data'] = [l for l in current_map if l.strip()]
                    if current_level['map_data']:  # Seulement ajouter si il y a une vraie carte
                        levels.append(current_level)
                
                # Commencer un nouveau niveau
                title = line[6:].strip()
                
                # Le premier niveau avec "Original & Extra" est le niveau 1
                # Les titres numériques sont les niveaux suivants
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
                # Après Author: ou Description:, tout le reste est la carte
                # ou lignes vides avant la carte
                if line.strip() == "":
                    if in_map_section:
                        # Ligne vide dans la carte
                        current_map.append(line)
                elif any(c in line for c in '#@$.*+ '):
                    # C'est une ligne de carte (contient des caractères Sokoban)
                    current_map.append(line)
                    in_map_section = True
        
        # Ajouter le dernier niveau
        if current_level is not None and current_map:
            current_level['map_data'] = [l for l in current_map if l.strip()]
            if current_level['map_data']:
                levels.append(current_level)
        
        return levels
    
    def run_benchmark(self, time_limit_per_level: float = 60.0, 
                     max_states_per_level: int = 100000) -> Dict[str, Any]:
        """
        Exécute le benchmark sur tous les niveaux.
        
        Args:
            time_limit_per_level: Limite de temps par niveau en secondes
            max_states_per_level: Limite d'états explorés par niveau
            
        Returns:
            Dict: Résultats complets du benchmark
        """
        if not self.levels:
            print("❌ Aucun niveau chargé. Appelez load_levels() d'abord.")
            return {}
        
        print(f"\n🔬 Démarrage du benchmark FESS sur {len(self.levels)} niveaux")
        print(f"⏱️  Limite: {time_limit_per_level}s par niveau, {max_states_per_level:,} états max")
        print("=" * 80)
        
        self.total_start_time = time.time()
        self.results = []
        
        solved_count = 0
        total_moves = 0
        total_time = 0
        
        for i, level_data in enumerate(self.levels, 1):
            print(f"\n[{i:2d}/90] Niveau {level_data['level_number']:2d}: {level_data['title']}")
            
            result = self._solve_single_level(
                level_data, 
                time_limit_per_level, 
                max_states_per_level
            )
            
            self.results.append(result)
            
            if result.solved:
                solved_count += 1
                total_moves += result.moves_count
                total_time += result.solve_time
                
                print(f"✅ Résolu en {result.solve_time:.2f}s "
                      f"({result.moves_count} mouvements, "
                      f"{result.states_explored:,} états explorés)")
            else:
                print(f"❌ Échec: {result.error_message}")
            
            # Afficher un résumé tous les 10 niveaux
            if i % 10 == 0:
                print(f"\n📊 Résumé après {i} niveaux:")
                print(f"   Résolus: {solved_count}/{i} ({solved_count/i*100:.1f}%)")
                if solved_count > 0:
                    print(f"   Temps moyen: {total_time/solved_count:.2f}s")
                    print(f"   Mouvements moyens: {total_moves/solved_count:.1f}")
        
        total_benchmark_time = time.time() - self.total_start_time
        
        # Générer le rapport final
        return self._generate_final_report(total_benchmark_time)
    
    def _solve_single_level(self, level_data: Dict[str, Any], 
                           time_limit: float, max_states: int) -> LevelResult:
        """Résout un niveau unique avec FESS."""
        try:
            # Créer l'objet Level
            level = self._create_level_from_data(level_data)
            
            if level is None:
                return LevelResult(
                    level_number=level_data['level_number'],
                    title=level_data['title'],
                    solved=False,
                    solve_time=0,
                    moves_count=0,
                    states_explored=0,
                    states_generated=0,
                    error_message="Impossible de créer le niveau"
                )
            
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
            
            if solution:
                return LevelResult(
                    level_number=level_data['level_number'],
                    title=level_data['title'],
                    solved=True,
                    solve_time=solve_time,
                    moves_count=len(solution),
                    states_explored=stats['search_statistics']['states_explored'],
                    states_generated=stats['search_statistics']['states_generated']
                )
            else:
                return LevelResult(
                    level_number=level_data['level_number'],
                    title=level_data['title'],
                    solved=False,
                    solve_time=solve_time,
                    moves_count=0,
                    states_explored=stats['search_statistics']['states_explored'],
                    states_generated=stats['search_statistics']['states_generated'],
                    error_message="Limite de temps/états atteinte"
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
                error_message=str(e)
            )
    
    def _create_level_from_data(self, level_data: Dict[str, Any]) -> Optional[Level]:
        """Crée un objet Level depuis les données parsées."""
        try:
            map_lines = level_data['map_data']
            if not map_lines:
                return None
            
            # Convertir les lignes de carte en une seule chaîne
            level_string = '\n'.join(map_lines)
            
            # Créer le niveau avec la chaîne de données
            level = Level(
                level_data=level_string,
                title=level_data.get('title', ''),
                description=level_data.get('description', ''),
                author=level_data.get('author', '')
            )
            
            return level
            
        except Exception as e:
            print(f"Erreur lors de la création du niveau: {e}")
            return None
    
    def _generate_final_report(self, total_time: float) -> Dict[str, Any]:
        """Génère le rapport final du benchmark."""
        solved_results = [r for r in self.results if r.solved]
        failed_results = [r for r in self.results if not r.solved]
        
        report = {
            'benchmark_info': {
                'algorithm': 'FESS_AUTHENTIC',
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
            'solved_levels': [
                {
                    'level': r.level_number,
                    'title': r.title,
                    'solve_time': r.solve_time,
                    'moves': r.moves_count,
                    'states_explored': r.states_explored,
                    'states_generated': r.states_generated
                }
                for r in solved_results
            ],
            'failed_levels': [
                {
                    'level': r.level_number,
                    'title': r.title,
                    'error': r.error_message,
                    'states_explored': r.states_explored
                }
                for r in failed_results
            ]
        }
        
        # Afficher le rapport
        self._print_final_report(report)
        
        return report
    
    def _print_final_report(self, report: Dict[str, Any]):
        """Affiche le rapport final."""
        print("\n" + "=" * 80)
        print("🏆 RAPPORT FINAL DU BENCHMARK FESS AUTHENTIQUE")
        print("=" * 80)
        
        overall = report['overall_performance']
        info = report['benchmark_info']
        
        print(f"\n📊 RÉSULTATS GLOBAUX:")
        print(f"   Niveaux résolus: {overall['levels_solved']}/90 ({overall['success_rate']:.1f}%)")
        print(f"   Temps total benchmark: {info['total_benchmark_time']:.1f}s")
        print(f"   Temps total résolution: {overall['total_solve_time']:.1f}s")
        
        if overall['levels_solved'] > 0:
            print(f"\n⚡ PERFORMANCES MOYENNES (niveaux résolus):")
            print(f"   Temps par niveau: {overall['average_solve_time']:.2f}s")
            print(f"   Mouvements par niveau: {overall['average_moves']:.1f}")
            print(f"   États explorés par niveau: {overall['average_states_explored']:,.0f}")
        
        # Comparaison avec le paper de Shoham & Schaeffer [2020]
        print(f"\n📖 COMPARAISON AVEC LE PAPER:")
        if overall['levels_solved'] == 90:
            if overall['total_solve_time'] < 240:  # 4 minutes
                print(f"   ✅ FESS authentique: VALIDÉ!")
                print(f"   ✅ Tous les 90 niveaux résolus en {overall['total_solve_time']:.1f}s < 240s")
            else:
                print(f"   ⚠️  Tous les niveaux résolus mais temps dépassé:")
                print(f"   ⚠️  {overall['total_solve_time']:.1f}s > 240s (limite du paper)")
        else:
            print(f"   ❌ Implémentation incomplète:")
            print(f"   ❌ {overall['levels_failed']} niveaux non résolus")
        
        # Top 5 des niveaux les plus difficiles
        solved_levels = report['solved_levels']
        if solved_levels:
            print(f"\n🔥 TOP 5 NIVEAUX LES PLUS DIFFICILES:")
            hardest = sorted(solved_levels, key=lambda x: x['solve_time'], reverse=True)[:5]
            for i, level in enumerate(hardest, 1):
                print(f"   {i}. Niveau {level['level']:2d}: {level['solve_time']:5.2f}s "
                      f"({level['states_explored']:,} états)")
        
        # Niveaux échoués
        if report['failed_levels']:
            print(f"\n❌ NIVEAUX ÉCHOUÉS ({len(report['failed_levels'])}):")
            for level in report['failed_levels'][:10]:  # Limiter l'affichage
                print(f"   Niveau {level['level']:2d}: {level['error']}")
            if len(report['failed_levels']) > 10:
                print(f"   ... et {len(report['failed_levels']) - 10} autres")
    
    def save_results(self, filename: str = "fess_benchmark_results.json"):
        """Sauvegarde les résultats en JSON."""
        if not self.results:
            print("❌ Aucun résultat à sauvegarder")
            return
        
        # Convertir les résultats en format sérialisable
        data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'algorithm': 'FESS_AUTHENTIC',
            'total_levels': len(self.results),
            'results': [
                {
                    'level_number': r.level_number,
                    'title': r.title,
                    'solved': r.solved,
                    'solve_time': r.solve_time,
                    'moves_count': r.moves_count,
                    'states_explored': r.states_explored,
                    'states_generated': r.states_generated,
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Résultats sauvegardés dans {filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")


def main():
    """Point d'entrée principal du benchmark."""
    print("🔬 BENCHMARK FESS AUTHENTIQUE - 90 NIVEAUX ORIGINAL & EXTRA")
    print("Algorithme de Shoham & Schaeffer [2020]")
    print("Objectif: Résoudre tous les 90 niveaux en moins de 4 minutes")
    print("=" * 80)
    
    # Créer le runner de benchmark
    runner = FESSBenchmarkRunner()
    
    # Charger les niveaux
    levels_count = runner.load_levels()
    if levels_count == 0:
        print("❌ Impossible de charger les niveaux")
        return
    
    # Paramètres du benchmark
    TIME_LIMIT_PER_LEVEL = 60.0  # 60s par niveau max (comme dans le paper)
    MAX_STATES_PER_LEVEL = 200000  # 200k états max par niveau
    
    print(f"\n⚙️  Configuration du benchmark:")
    print(f"   Limite de temps par niveau: {TIME_LIMIT_PER_LEVEL}s")
    print(f"   Limite d'états par niveau: {MAX_STATES_PER_LEVEL:,}")
    
    # Exécuter le benchmark
    results = runner.run_benchmark(TIME_LIMIT_PER_LEVEL, MAX_STATES_PER_LEVEL)
    
    # Sauvegarder les résultats
    runner.save_results("fess_90_levels_benchmark.json")
    
    print(f"\n🎯 BENCHMARK TERMINÉ!")


if __name__ == "__main__":
    main()