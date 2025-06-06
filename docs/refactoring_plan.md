# PySokoban Refactoring Plan

This document outlines the plan for refactoring the PySokoban project to improve its architecture, making entry points more visible and organizing files into appropriate directories.

## Final Architecture

```
PySokoban/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── level.py
│   │   └── game.py
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── terminal_renderer.py
│   │   └── gui_renderer.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── menu_system.py
│   │   ├── button.py
│   │   ├── skins_menu.py
│   │   └── skins/
│   │       ├── __init__.py
│   │       ├── skin_manager.py
│   │       └── enhanced_skin_manager.py
│   ├── level_management/
│   │   ├── __init__.py
│   │   ├── level_manager.py
│   │   ├── level_selector.py
│   │   └── level_metrics.py
│   ├── editors/
│   │   ├── __init__.py
│   │   ├── level_editor.py
│   │   ├── enhanced_level_editor.py
│   │   └── graphical_level_editor.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── procedural_generator.py
│   │   ├── level_solver.py
│   │   └── advanced/
│   │       ├── __init__.py
│   │       ├── advanced_procedural_generator.py
│   │       ├── pattern_based_generator.py
│   │       ├── style_transfer_engine.py
│   │       ├── learning_models.py
│   │       ├── player_feedback_analyzer.py
│   │       ├── data_collection_system.py
│   │       ├── feedback_collection_ui.py
│   │       └── machine_learning_system.py
│   ├── __init__.py
│   ├── main.py
│   ├── gui_main.py
│   ├── enhanced_main.py
│   └── editor_main.py
├── levels/
│   ├── Classic/
│   ├── Generated/
│   ├── Procedural/
│   ├── Test/
│   └── Advanced generated/
├── skins/
│   └── default/
├── docs/
├── tests/
│   ├── __init__.py
│   ├── test_procedural_generation.py
│   ├── test_advanced_generation.py
│   ├── test_level_editor_ui.py
│   ├── test_enhancements.py
│   └── test_maximize.py
├── assets/
├── setup.py
└── README.md
```

## Implementation Plan

### Phase 1: Create Directory Structure

1. Create all the directories as outlined above
2. Create empty `__init__.py` files in each directory to make them proper Python packages

### Phase 2: Move and Refactor Core Files

1. Move core files to their appropriate directories:
   - Move `constants.py` to `src/core/`
   - Move `level.py` to `src/core/`
   - Create `src/core/game.py` by extracting the game logic from `SokobanGame` class

2. Create the new entry point files:
   - Create `src/main.py` based on `sokoban.py`
   - Create `src/gui_main.py` based on `sokoban_gui.py`
   - Create `src/enhanced_main.py` based on `enhanced_sokoban.py`
   - Create `src/editor_main.py` as an entry point for the level editors

3. Update imports in these files to reflect the new structure

### Phase 3: Move and Refactor Renderer Files

1. Move renderer files to their appropriate directory:
   - Move `terminal_renderer.py` to `src/renderers/`
   - Move `gui_renderer.py` to `src/renderers/`

2. Update imports in these files

### Phase 4: Refactor UI Components

1. Move UI-related files to their appropriate directories:
   - Move `menu_system.py` to `src/ui/`
   - Extract the `Button` class from `menu_system.py` into `src/ui/button.py`
   - Move `skins_menu.py` to `src/ui/`
   - Move `skin_manager.py` to `src/ui/skins/`
   - Move `enhanced_skin_manager.py` to `src/ui/skins/`

2. Update imports in these files

### Phase 5: Refactor Level Management

1. Move level management files to their appropriate directory:
   - Move `level_manager.py` to `src/level_management/`
   - Move `level_selector.py` to `src/level_management/`
   - Move `level_metrics.py` to `src/level_management/`

2. Update imports in these files

### Phase 6: Refactor Level Editors

1. Move editor files to their appropriate directory:
   - Move `level_editor.py` to `src/editors/`
   - Move `enhanced_level_editor.py` to `src/editors/`
   - Move `graphical_level_editor.py` to `src/editors/`

2. Update imports in these files

### Phase 7: Refactor Generation Components

1. Move generation files to their appropriate directories:
   - Move `procedural_generator.py` to `src/generation/`
   - Move `level_solver.py` to `src/generation/`
   - Move `advanced_procedural_generator.py` to `src/generation/advanced/`
   - Move `pattern_based_generator.py` to `src/generation/advanced/`
   - Move `style_transfer_engine.py` to `src/generation/advanced/`
   - Move `learning_models.py` to `src/generation/advanced/`
   - Move `player_feedback_analyzer.py` to `src/generation/advanced/`
   - Move `data_collection_system.py` to `src/generation/advanced/`
   - Move `feedback_collection_ui.py` to `src/generation/advanced/`
   - Move `machine_learning_system.py` to `src/generation/advanced/`

2. Update imports in these files

### Phase 8: Move Test Files

1. Move test files to the tests/ directory:
   - Move `test_procedural_generation.py` to `tests/`
   - Move `test_advanced_generation.py` to `tests/`
   - Move `test_level_editor_ui.py` to `tests/`
   - Move `test_enhancements.py` to `tests/`
   - Move `test_maximize.py` to `tests/`

2. Update imports in these files

### Phase 9: Create setup.py

Create a setup.py file in the root directory with the following content:

```python
from setuptools import setup, find_packages

setup(
    name="pysokoban",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pygame",
        "keyboard",
    ],
    entry_points={
        "console_scripts": [
            "pysokoban=src.main:main",
            "pysokoban-gui=src.gui_main:main",
            "pysokoban-enhanced=src.enhanced_main:main",
            "pysokoban-editor=src.editor_main:main",
        ],
    },
    python_requires=">=3.6",
    author="Yassine EL IDRISSI",
    description="A Python implementation of the classic Sokoban puzzle game",
    keywords="sokoban, game, puzzle",
    package_data={
        "": ["levels/*/*.txt", "skins/*/*.png"],
    },
)
```

Also, create a MANIFEST.in file to ensure all necessary data files are included:

```
include README.md
recursive-include levels *.txt
recursive-include skins *.png
recursive-include docs *.md
```

### Phase 10: Create Documentation

1. Update the README.md file in the root directory explaining the new structure
2. Update existing documentation to reflect the new structure
3. Create a simple diagram showing the architecture

## Benefits of This Refactoring

1. **Clear Entry Points**: The main entry points are now clearly visible in the src/ directory with standardized naming
2. **Logical Organization**: Files are organized by functionality into appropriate modules
3. **Better Maintainability**: Related files are grouped together, making maintenance easier
4. **Easier Navigation**: The directory structure makes it easier to find specific files
5. **Improved Modularity**: The code is now more modular and easier to understand
6. **Better Scalability**: New features can be added to the appropriate directories without cluttering the root
7. **Follows Python Conventions**: The structure follows common Python project conventions
8. **Installable Package**: The project can now be installed as a Python package, making it easier to run from anywhere

## Installation After Refactoring

After refactoring, the game can be installed and run as follows:

```bash
# Install in development mode
pip install -e .

# Run the terminal version
pysokoban

# Run the GUI version
pysokoban-gui

# Run the enhanced version
pysokoban-enhanced

# Run the level editor
pysokoban-editor