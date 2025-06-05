# Guide d'Importation de Skins Personnalisés

Ce guide explique comment utiliser la nouvelle fonctionnalité d'importation de skins personnalisés dans le jeu Sokoban.

## Vue d'ensemble

La fonctionnalité d'importation de skins permet aux utilisateurs d'ajouter leurs propres sprites personnalisés au format PNG pour tous les éléments du jeu :
- Sprites du personnage (avec support directionnel)
- Éléments de jeu (murs, sol, boîtes, cibles)
- Images d'arrière-plan

## Comment Importer un Skin

### 1. Accéder au Menu des Skins

1. Lancez le jeu Sokoban
2. Allez dans le menu "Skins & Sprites"
3. Vous verrez une interface avec trois sections :
   - **Skins** : Liste des skins disponibles
   - **Tile Size** : Sélection de la taille des tiles
   - **Preview** : Aperçu du skin sélectionné

### 2. Préparer vos Sprites

Avant d'importer, préparez vos fichiers PNG :

#### Sprites Requis (obligatoires)
- `wall.png` - Sprite du mur
- `floor.png` - Sprite du sol
- `player.png` - Sprite du personnage
- `box.png` - Sprite de la boîte
- `target.png` - Sprite de la cible
- `player_on_target.png` - Personnage sur une cible
- `box_on_target.png` - Boîte sur une cible

#### Sprites Optionnels (directionnels)
- `player_up.png` - Personnage regardant vers le haut
- `player_down.png` - Personnage regardant vers le bas
- `player_left.png` - Personnage regardant vers la gauche
- `player_right.png` - Personnage regardant vers la droite
- `player_push_up.png` - Personnage poussant vers le haut
- `player_push_down.png` - Personnage poussant vers le bas
- `player_push_left.png` - Personnage poussant vers la gauche
- `player_push_right.png` - Personnage poussant vers la droite
- `player_blocked.png` - Personnage bloqué

#### Image d'Arrière-plan (optionnelle)
- `background.png` - Image d'arrière-plan (n'importe quelle taille)

### 3. Spécifications Techniques

#### Taille des Sprites
- Les sprites doivent être **carrés** (même largeur et hauteur)
- La taille doit correspondre à la taille de tile sélectionnée :
  - 8x8 pixels
  - 16x16 pixels
  - 32x32 pixels
  - 64x64 pixels (par défaut)
  - 128x128 pixels

#### Format
- **Format** : PNG uniquement
- **Transparence** : Supportée (canal alpha)
- **Couleurs** : RGB ou RGBA

### 4. Processus d'Importation

1. **Sélectionner la Taille** : Choisissez d'abord la taille de tile désirée
2. **Cliquer sur "Import Skin"** : Le processus d'importation commence
3. **Nommer le Skin** : Entrez un nom pour votre skin personnalisé
4. **Sélectionner les Sprites Requis** : 
   - Une boîte de dialogue s'ouvre pour chaque sprite requis
   - Naviguez et sélectionnez le fichier PNG correspondant
   - Le système valide automatiquement la taille
5. **Sprites Optionnels** : 
   - Choisissez d'ajouter des sprites directionnels
   - Sélectionnez les fichiers pour chaque direction souhaitée
6. **Arrière-plan** : 
   - Optionnellement, ajoutez une image d'arrière-plan
7. **Confirmation** : Le skin est importé et disponible immédiatement

### 5. Validation Automatique

Le système effectue plusieurs validations :
- **Format** : Vérifie que le fichier est un PNG valide
- **Dimensions** : Vérifie que l'image est carrée
- **Taille** : Compare avec la taille de tile sélectionnée
- **Redimensionnement** : Propose de redimensionner si nécessaire

### 6. Utiliser le Skin Importé

1. Après l'importation, le nouveau skin apparaît dans la liste
2. Sélectionnez-le dans la section "Skins"
3. Visualisez l'aperçu dans la section "Preview"
4. Cliquez sur "Apply" pour l'utiliser dans le jeu

## Conseils et Astuces

### Création de Sprites
- Utilisez un éditeur d'images comme GIMP, Photoshop, ou Paint.NET
- Gardez un style cohérent entre tous les sprites
- Utilisez la transparence pour les zones vides
- Testez différentes tailles pour voir laquelle convient le mieux

### Performance
- Les sprites plus petits (8x8, 16x16) sont plus rapides à afficher
- Les sprites plus grands (64x64, 128x128) offrent plus de détails
- L'arrière-plan affecte les performances selon sa taille

### Organisation
- Créez un dossier pour chaque thème de skin
- Nommez vos fichiers de manière cohérente
- Gardez des sauvegardes de vos sprites originaux

## Dépannage

### Problèmes Courants

**"Image non carrée"**
- Assurez-vous que largeur = hauteur
- Redimensionnez l'image pour qu'elle soit carrée

**"Taille incorrecte"**
- Vérifiez la taille de tile sélectionnée
- Redimensionnez l'image à la bonne taille
- Utilisez l'option de redimensionnement automatique

**"Format non supporté"**
- Convertissez l'image en PNG
- Vérifiez que le fichier n'est pas corrompu

**"Erreur d'importation"**
- Vérifiez les permissions du dossier skins
- Assurez-vous d'avoir assez d'espace disque
- Redémarrez l'application si nécessaire

### Support

Si vous rencontrez des problèmes :
1. Vérifiez que tous les sprites requis sont fournis
2. Validez les dimensions et le format
3. Essayez avec des sprites plus simples d'abord
4. Consultez les logs d'erreur dans la console

## Exemples

### Skin Minimaliste
- Formes géométriques simples
- Couleurs unies
- Contours nets

### Skin Rétro
- Style pixel art 8-bit
- Palette de couleurs limitée
- Sprites 16x16

### Skin Moderne
- Dégradés et ombres
- Sprites 64x64 ou 128x128
- Effets de transparence

Le système d'importation de skins offre une flexibilité complète pour personnaliser l'apparence du jeu selon vos préférences !