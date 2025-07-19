# PySokoban Project Guidelines

## Project Overview

PySokoban is a comprehensive implementation of the classic Sokoban puzzle game developed in Python. The game features a modular architecture that separates game logic, rendering, and user input. It offers multiple play modes including terminal-based, GUI (using Pygame), and an enhanced version with additional features.

Key features include:
- Central menu system (hub) for navigating between different functionalities
- Terminal and GUI play modes
- Graphical level editor with drag-and-drop functionality
- Customizable skins/sprites system
- Level validation to ensure playability
- Support for different keyboard layouts (QWERTY and AZERTY)
- Advanced AI solver based on Sokolution techniques
- Procedural level generation

## Project Structure

The project follows a modular structure:

- `src/` - Main package containing all source code
  - `core/` - Core game logic, constants, and base classes
  - `renderers/` - Different rendering systems (terminal, GUI)
  - `level_management/` - Level loading, parsing, and management
  - `editors/` - Level editor implementation
  - `ui/` - User interface components and menu system
  - `generation/` - Procedural level generation
  - `ai/` - AI solver implementation
  - `main.py` - Single entry point for all game modes
- `levels/` - Directory containing level files
- `skins/` - Directory containing visual themes
- `tests/` - Comprehensive test suite
- `build_package.py` - Script to build Python package
- `build_exe.py` - Script to build standalone executable
- `config.json` - Game configuration file

## Running the Application

The game has a single entry point via `src.main` or the `launch_game.py` script. Different modes can be launched using command-line options:

```bash
# Enhanced mode (default, recommended)
python -m src.main

# Terminal mode
python -m src.main --mode terminal

# GUI mode
python -m src.main --mode gui

# Level editor
python -m src.main --mode editor
```

Additional options:
- `--levels` to specify a custom levels directory
- `--keyboard` to choose keyboard layout (qwerty/azerty)

## Running Tests

The project includes a comprehensive test suite in the `tests/` directory. Tests are organized by functionality and can be run individually:

```bash
# Run a specific test
python -m tests.test_complete_system

# Run all tests using unittest discovery
python -m unittest discover -s tests
```

Key test categories:
- Game functionality tests (test_complete_system.py, test_enhancements.py)
- AI and solver tests (test_advanced_solver.py, test_ai_control.py)
- Level management tests (test_level_collection_parser.py)
- UI tests (test_level_editor_ui.py, test_gui_metadata.py)
- Skin system tests (test_skin_import.py, test_skin_persistence.py)

## Building the Project

### Building a Python Package

To build a distributable Python package:

```bash
python build_package.py
```

This creates distribution files in the `dist/` directory that can be installed using pip:

```bash
pip install dist/pysokoban-*.whl
```

After installation, the game can be run using these commands:
- `pysokoban` (basic version)
- `pysokoban-gui` (GUI version)
- `pysokoban-enhanced` (enhanced version)
- `pysokoban-editor` (level editor)

### Building a Standalone Executable

To build a standalone executable:

```bash
python build_exe.py
```

This creates an executable in the `dist/` directory that can be run without Python installed.

## Code Style Guidelines

When contributing to the PySokoban project, please follow these guidelines:

1. **PEP 8**: Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
2. **Docstrings**: Use docstrings for all modules, classes, and functions following the [PEP 257](https://www.python.org/dev/peps/pep-0257/) conventions.
3. **Modular Design**: Maintain the modular architecture of the project. Keep game logic, rendering, and user input separate.
4. **Type Hints**: Use type hints where appropriate to improve code readability and enable better IDE support.
5. **Comments**: Add comments for complex logic, but prefer self-explanatory code where possible.
6. **Testing**: Add tests for new functionality in the appropriate test file or create a new test file if needed.

## Development Workflow

1. **Setup**: Install development dependencies with `pip install -r requirements.txt`
2. **Testing**: Run tests to ensure your changes don't break existing functionality
3. **Building**: Test both package and executable builds before submitting changes
4. **Documentation**: Update relevant documentation when adding or changing features

## Configuration

The game uses a `config.json` file for configuration, which includes:

- Skin settings (current skin, tile size)
- Display settings (window dimensions, fullscreen mode)
- Game settings (keyboard layout, grid display, zoom level)
- Keybindings

This file is created automatically with default values if it doesn't exist and can be modified to customize the game experience.