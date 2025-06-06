# PySokoban

A Python implementation of the classic Sokoban puzzle game with multiple interfaces and advanced features.

## Features

- Terminal-based interface
- GUI interface with pygame
- Enhanced version with additional features:
  - Menu system (hub)
  - Graphical level editor
  - Skin/sprite system
  - Level validation
  - Live testing of levels
- Procedural level generation
- Advanced level generation with machine learning
- Multiple level editors

## Project Structure

The project is organized into the following directories:

```
PySokoban/
├── src/                  # Source code
│   ├── core/             # Core game logic
│   ├── renderers/        # Terminal and GUI renderers
│   ├── ui/               # User interface components
│   ├── level_management/ # Level loading and management
│   ├── editors/          # Level editors
│   ├── generation/       # Procedural generation
│   └── main entry points:
│       ├── main.py           # Terminal version
│       ├── gui_main.py       # GUI version
│       ├── enhanced_main.py  # Enhanced version
│       └── editor_main.py    # Level editor
├── levels/               # Level files
├── skins/                # Skin/sprite files
├── docs/                 # Documentation
├── tests/                # Test files
└── assets/               # Other assets
```

## Installation

You can install PySokoban as a Python package:

```bash
# Clone the repository
git clone https://github.com/yourusername/PySokoban.git
cd PySokoban

# Install the package
pip install -e .
```

## Usage

After installation, you can run the game using the following commands:

```bash
# Run the terminal version
pysokoban

# Run the GUI version
pysokoban-gui

# Run the enhanced version
pysokoban-enhanced

# Run the level editor
pysokoban-editor
```

Alternatively, you can run the Python modules directly:

```bash
# Run the terminal version
python -m src.main

# Run the GUI version
python -m src.gui_main

# Run the enhanced version
python -m src.enhanced_main

# Run the level editor
python -m src.editor_main
```

## Game Controls

### Terminal Version
- Arrow keys or WASD: Move the player
- R: Reset level
- Q: Quit game
- N: Next level
- P: Previous level
- U: Undo move
- H: Help

### GUI Version
- Arrow keys or WASD: Move the player
- R: Reset level
- Escape: Return to level selector
- F11: Toggle fullscreen
- G: Toggle grid
- U: Undo move
- H: Help

## Creating Custom Levels

You can create custom levels using the level editor or by creating text files in the `levels/` directory. The level format uses the following characters:

- `#`: Wall
- ` `: Floor (space)
- `@`: Player
- `$`: Box
- `.`: Target
- `+`: Player on target
- `*`: Box on target

## Development

To contribute to the project, follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run the tests (`python -m unittest discover tests`)
5. Commit your changes (`git commit -am 'Add your feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Original Sokoban game concept by Hiroyuki Imabayashi
- This implementation by Yassine EL IDRISSI