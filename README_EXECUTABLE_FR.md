# Création d'un Exécutable pour PySokoban

Ce document explique comment créer un fichier exécutable autonome (.exe) pour PySokoban qui peut être exécuté sous Windows sans nécessiter l'installation de Python.

## Prérequis

- Système d'exploitation Windows
- Python 3.6 ou supérieur installé
- Code source de PySokoban

## Méthode 1 : Utilisation du script build_exe.py (Recommandée)

Nous avons fourni un script qui automatise le processus de création d'un exécutable à l'aide de PyInstaller.

### Étapes :

1. Ouvrez une invite de commande dans le répertoire PySokoban
2. Exécutez le script de construction :
   ```
   python build_exe.py
   ```
3. Attendez que le processus se termine (cela peut prendre plusieurs minutes)
4. Une fois terminé, vous trouverez l'exécutable dans le dossier `dist`
5. Pour lancer le jeu, double-cliquez simplement sur `PySokoban.exe` dans le dossier dist

## Méthode 2 : Configuration manuelle de PyInstaller

Si vous préférez exécuter PyInstaller manuellement ou si vous devez personnaliser le processus de construction :

### Étapes :

1. Installez PyInstaller si ce n'est pas déjà fait :
   ```
   pip install pyinstaller
   ```

2. Ouvrez une invite de commande dans le répertoire PySokoban

3. Exécutez PyInstaller avec la commande suivante :
   ```
   pyinstaller --name=PySokoban --onefile --windowed --add-data=levels;levels --add-data=skins;skins --add-data=config.json;. src\main.py
   ```

4. L'exécutable sera créé dans le dossier `dist`

## Exécution du Fichier Exécutable

- Double-cliquez sur `PySokoban.exe` dans le dossier dist pour démarrer le jeu
- L'exécutable contient tous les fichiers et dépendances nécessaires, il peut donc être partagé avec d'autres personnes qui n'ont pas Python installé
- Notez que le premier lancement peut prendre un peu plus de temps car l'exécutable décompresse ses ressources

## Dépannage

Si vous rencontrez des problèmes :

1. **Dépendances manquantes** : Assurez-vous que tous les packages requis sont installés :
   ```
   pip install -r requirements.txt
   ```

2. **Erreurs de fichier introuvable** : Assurez-vous que tous les chemins dans la commande de construction sont corrects pour votre système

3. **Blocage par l'antivirus** : Certains logiciels antivirus peuvent signaler les exécutables créés par PyInstaller. Vous devrez peut-être ajouter une exception.

4. **Écran noir ou fermeture immédiate** : Essayez d'exécuter l'exécutable depuis la ligne de commande pour voir les messages d'erreur :
   ```
   dist\PySokoban.exe
   ```

## Distribution

Pour partager votre exécutable avec d'autres :

1. Vous pouvez distribuer uniquement le fichier `PySokoban.exe` du dossier dist
2. Alternativement, créez un fichier zip contenant l'exécutable et tous les fichiers supplémentaires que vous souhaitez inclure
3. Le destinataire n'a qu'à extraire les fichiers et exécuter l'exécutable - aucune installation de Python n'est requise

## Remarques

- L'exécutable peut être assez volumineux (plus de 100 Mo) en raison de l'inclusion de Python et de toutes les dépendances
- L'option `--onefile` crée un exécutable unique qui est plus facile à distribuer mais prend plus de temps à démarrer
- Si vous préférez un temps de démarrage plus rapide, vous pouvez supprimer l'option `--onefile`, mais cela créera un dossier avec de nombreux fichiers au lieu d'un seul exécutable