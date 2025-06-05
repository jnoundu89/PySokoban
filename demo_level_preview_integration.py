"""
Démonstration de la nouvelle fonctionnalité de prévisualisation de niveaux intégrée au jeu.
"""

import sys
sys.path.append('src')

def main():
    """Démonstration de la prévisualisation de niveaux."""
    print("=" * 60)
    print("DÉMONSTRATION - PRÉVISUALISATION DE NIVEAUX")
    print("=" * 60)
    print()
    print("Nouvelle fonctionnalité ajoutée au sélecteur de niveaux !")
    print()
    print("🎮 COMMENT UTILISER LA PRÉVISUALISATION :")
    print()
    print("1. Lancez le jeu principal :")
    print("   python -m src.enhanced_main")
    print()
    print("2. Dans le menu principal, cliquez sur 'Play Game'")
    print()
    print("3. Sélectionnez une catégorie de niveaux")
    print()
    print("4. Cliquez sur un niveau pour voir sa PRÉVISUALISATION !")
    print()
    print("🔍 DANS LA POPUP DE PRÉVISUALISATION :")
    print("   • Vous voyez une miniature du niveau")
    print("   • Les statistiques : taille, nombre de boîtes/cibles")
    print("   • Bouton 'Play' pour jouer au niveau")
    print("   • Bouton 'Retour' pour revenir à la sélection")
    print()
    print("⌨️  RACCOURCIS CLAVIER DANS LA POPUP :")
    print("   • Échap : Fermer la popup")
    print("   • Entrée/Espace : Jouer au niveau")
    print("   • Clic à l'extérieur : Fermer la popup")
    print()
    print("✨ AVANTAGES :")
    print("   • Prévisualisation visuelle avant de jouer")
    print("   • Informations sur la difficulté du niveau")
    print("   • Interface intuitive et rapide")
    print("   • Prévisualisation de la même taille pour tous les niveaux")
    print()
    print("=" * 60)
    print()
    
    choice = input("Voulez-vous lancer le jeu maintenant ? (o/n): ").lower().strip()
    if choice in ['o', 'oui', 'y', 'yes']:
        print("\nLancement du jeu...")
        import subprocess
        subprocess.run([sys.executable, "-m", "src.enhanced_main"])
    else:
        print("\nVous pouvez lancer le jeu plus tard avec :")
        print("python -m src.enhanced_main")
    
    print("\nMerci d'avoir testé la nouvelle fonctionnalité ! 🎯")

if __name__ == "__main__":
    main()