#!/usr/bin/env python3
"""
Analyse de performance FESS sur les premiers niveaux pour calibrer les paramètres.
"""

import time
import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.level import Level
from ai.authentic_fess import FESSSearchEngine


def test_first_levels():
    """Test FESS sur les 5 premiers niveaux avec analyse de performance."""
    
    print("⚡ ANALYSE DE PERFORMANCE FESS - PREMIERS NIVEAUX")
    print("=" * 60)
    
    # Charger le fichier des niveaux
    levels_file = "../src/levels/Original & Extra/Original.txt"
    
    try:
        with open(levels_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {levels_file}")
        return
    
    # Parser les premiers niveaux
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
                    if len(levels) >= 5:  # Seulement les 5 premiers
                        break
            
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
    
    # Ajouter le dernier niveau
    if current_level is not None and current_map:
        current_level['map_data'] = [l for l in current_map if l.strip()]
        if current_level['map_data'] and len(levels) < 5:
            levels.append(current_level)
    
    print(f"📋 {len(levels)} niveaux chargés pour l'analyse")
    
    # Tester chaque niveau avec différents paramètres
    for i, level_data in enumerate(levels):
        print(f"\n[{i+1}/5] Niveau {level_data['level_number']}: {level_data['title']}")
        print("-" * 50)
        
        try:
            # Créer le niveau
            level_string = '\n'.join(level_data['map_data'])
            level = Level(level_data=level_string)
            
            print(f"   📐 Dimensions: {level.width}x{level.height}")
            print(f"   📦 Boxes: {len(level.boxes)}")
            print(f"   🎯 Targets: {len(level.targets)}")
            
            # Test rapide avec limites réduites
            print(f"   🔬 Test rapide (10s, 5k états)...")
            
            fess_engine = FESSSearchEngine(
                level=level,
                max_states=5000,
                time_limit=10.0
            )
            
            start_time = time.time()
            solution = fess_engine.search()
            solve_time = time.time() - start_time
            
            stats = fess_engine.get_statistics()
            
            if solution:
                print(f"   ✅ RÉSOLU en {solve_time:.2f}s!")
                print(f"   📋 Solution: {len(solution)} mouvements")
            else:
                print(f"   ⚠️  Limite atteinte en {solve_time:.2f}s")
            
            print(f"   📊 États explorés: {stats['search_statistics']['states_explored']:,}")
            print(f"   🔧 Cellules FS: {stats['feature_space_statistics']['total_cells']}")
            
            # Estimer le temps nécessaire pour une solution complète
            if stats['search_statistics']['states_explored'] > 0:
                states_per_second = stats['search_statistics']['states_explored'] / solve_time
                print(f"   ⚡ Vitesse: {states_per_second:,.0f} états/s")
                
                if not solution:
                    # Estimer combien de temps il faudrait avec plus d'états
                    estimated_states_needed = stats['search_statistics']['states_explored'] * 10
                    estimated_time = estimated_states_needed / states_per_second
                    print(f"   🔮 Estimation: {estimated_time:.1f}s pour {estimated_states_needed:,} états")
            
            # Analyser la complexité
            complexity_score = len(level.boxes) * level.width * level.height
            print(f"   🧮 Score complexité: {complexity_score}")
            
            if complexity_score > 5000:
                print(f"   ⚠️  NIVEAU TRÈS COMPLEXE - Paramètres spéciaux requis")
            elif complexity_score > 2000:
                print(f"   ⚠️  NIVEAU COMPLEXE - Temps étendu requis")
            else:
                print(f"   ✅ NIVEAU STANDARD")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    # Recommandations de paramètres
    print(f"\n" + "=" * 60)
    print(f"📊 RECOMMANDATIONS DE PARAMÈTRES")
    print(f"=" * 60)
    print(f"🎯 Pour le benchmark complet des 90 niveaux:")
    print(f"   • Limite de temps: 120s par niveau (plus sûr que 60s)")
    print(f"   • Limite d'états: 100,000 par niveau (équilibre performance/mémoire)")
    print(f"   • Niveaux complexes (>6 boxes): paramètres étendus")
    print(f"   • Timeout adaptatif selon la complexité")


def main():
    """Point d'entrée principal."""
    test_first_levels()


if __name__ == "__main__":
    main()