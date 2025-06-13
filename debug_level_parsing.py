#!/usr/bin/env python3
"""
Script de debug pour analyser le parsing des niveaux.
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_parsing():
    """Debug le parsing des niveaux."""
    levels_file = "src/levels/Original & Extra/Original.txt"
    
    print("🔍 DEBUG: Analyse du fichier de niveaux")
    print(f"Fichier: {levels_file}")
    print("=" * 60)
    
    try:
        with open(levels_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {levels_file}")
        return
    
    lines = content.strip().split('\n')
    print(f"Total de lignes dans le fichier: {len(lines)}")
    
    # Analyser les 50 premières lignes pour voir la structure
    print("\n📝 Premières 50 lignes:")
    for i, line in enumerate(lines[:50], 1):
        line_repr = repr(line)
        if len(line_repr) > 80:
            line_repr = line_repr[:77] + "..."
        print(f"{i:3d}: {line_repr}")
    
    # Essayer de parser manuellement le premier niveau
    print("\n🎯 Tentative de parsing du premier niveau:")
    
    current_level = None
    current_map = []
    level_number = 0
    in_map_section = False
    
    for i, line in enumerate(lines[:100]):  # Analyser les 100 premières lignes
        line = line.rstrip()
        print(f"Ligne {i+1:2d}: {repr(line)}")
        
        if line.startswith("Title:"):
            if current_level is not None and current_map:
                print(f"   → Finalisant niveau précédent avec {len(current_map)} lignes de carte")
                break
            
            title = line[6:].strip()
            print(f"   → Nouveau titre détecté: {repr(title)}")
            
            if title == "Original & Extra":
                level_number = 1
            elif title.isdigit():
                level_number = int(title)
            else:
                level_number += 1
                
            current_level = {
                'level_number': level_number,
                'title': title,
                'description': "",
                'author': ""
            }
            current_map = []
            in_map_section = False
            print(f"   → Niveau {level_number} créé")
            
        elif line.startswith("Description:"):
            if current_level:
                current_level['description'] = line[12:].strip()
                print(f"   → Description: {repr(current_level['description'])}")
                
        elif line.startswith("Author:"):
            if current_level:
                current_level['author'] = line[7:].strip()
                print(f"   → Auteur: {repr(current_level['author'])}")
                
        elif current_level is not None:
            if line.strip() == "":
                if in_map_section:
                    current_map.append(line)
                    print(f"   → Ligne vide ajoutée à la carte")
            elif any(c in line for c in '#@$.*+ '):
                current_map.append(line)
                in_map_section = True
                print(f"   → Ligne de carte ajoutée: {repr(line)}")
    
    if current_level and current_map:
        print(f"\n📋 Premier niveau parsé:")
        print(f"   Numéro: {current_level['level_number']}")
        print(f"   Titre: {repr(current_level['title'])}")
        print(f"   Description: {repr(current_level['description'])}")
        print(f"   Auteur: {repr(current_level['author'])}")
        print(f"   Lignes de carte: {len(current_map)}")
        
        print(f"\n🗺️  Carte (type de chaque ligne):")
        for i, map_line in enumerate(current_map):
            print(f"   {i:2d}: {type(map_line)} - {repr(map_line)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    debug_parsing()