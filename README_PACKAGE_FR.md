# Création d'un Package Python pour PySokoban

Ce document explique comment créer un package Python pour PySokoban qui peut être installé à l'aide de pip et distribué à d'autres utilisateurs.

## Prérequis

- Python 3.6 ou supérieur installé
- pip (installateur de packages Python)
- packages setuptools et wheel installés
- Code source de PySokoban

## Méthode 1 : Utilisation du script build_package.py (Recommandée)

Nous avons fourni un script qui automatise le processus de création d'un package Python.

### Étapes :

1. Ouvrez une invite de commande dans le répertoire PySokoban
2. Exécutez le script de construction :
   ```
   python build_package.py
   ```
3. Attendez que le processus se termine
4. Une fois terminé, vous trouverez les fichiers du package dans le dossier `dist`

## Méthode 2 : Construction manuelle du package

Si vous préférez construire le package manuellement ou si vous devez personnaliser le processus de construction :

### Étapes :

1. Installez les outils de construction requis si ce n'est pas déjà fait :
   ```
   pip install --upgrade setuptools wheel
   ```

2. Ouvrez une invite de commande dans le répertoire PySokoban

3. Construisez le package :
   ```
   python setup.py sdist bdist_wheel
   ```

4. Les fichiers du package seront créés dans le dossier `dist` :
   - Une distribution source (.tar.gz)
   - Une distribution wheel (.whl)

## Installation du Package

### Installation locale

Pour installer le package localement à partir des fichiers construits :

```
pip install dist/pysokoban-1.0.0-py3-none-any.whl
```

Ou directement à partir du code source :

```
pip install -e .
```

### Installation depuis PyPI (si publié)

Si le package a été publié sur l'Index des Packages Python (PyPI) :

```
pip install pysokoban
```

## Utilisation du Package Installé

Après l'installation, vous pouvez exécuter PySokoban en utilisant les commandes suivantes :

- Version basique : `pysokoban`
- Version GUI : `pysokoban-gui`
- Version améliorée : `pysokoban-enhanced`
- Éditeur de niveaux : `pysokoban-editor`

Vous pouvez également importer le package dans votre code Python :

```python
from pysokoban import main
main()
```

## Publication du Package sur PyPI

Si vous souhaitez partager votre package avec la communauté Python plus large :

1. Créez un compte sur PyPI (https://pypi.org)

2. Installez twine :
   ```
   pip install twine
   ```

3. Téléchargez votre package :
   ```
   twine upload dist/*
   ```

4. Entrez votre nom d'utilisateur et mot de passe PyPI lorsque vous y êtes invité

## Dépannage

Si vous rencontrez des problèmes :

1. **Dépendances manquantes** : Assurez-vous que tous les packages requis sont installés :
   ```
   pip install -r requirements.txt
   ```

2. **Erreurs d'importation après l'installation** : Assurez-vous que la structure de votre package est correcte et que les fichiers `__init__.py` sont présents dans tous les répertoires nécessaires

3. **Package introuvable après l'installation** : Vérifiez que le package a été correctement installé en utilisant `pip list | grep pysokoban`

## Remarques

- Le package inclut tous les fichiers de jeu nécessaires (niveaux, skins, assets, etc.)
- Les utilisateurs qui installent votre package pourront exécuter le jeu sans télécharger le code source
- Pensez à mettre à jour le numéro de version dans setup.py lorsque vous apportez des modifications au package