# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PySokoban is a Python Sokoban puzzle game (~24k lines across 59 source files + 27 test files). It features terminal and GUI (PyGame) modes, a graphical level editor, AI solvers (Sokolution with BFS/A*/IDA*/Greedy), procedural level generation, and a skin/sprite system. The README and docs are written in French.

## Common Commands

```bash
# Run the game (enhanced mode with menu system, default)
python -m src.main
python -m src.main --mode terminal|gui|editor
python -m src.main --levels path/to/levels --keyboard azerty

# Install dependencies
pip install -r requirements.txt
pip install -e .  # dev mode

# Tests (unittest-based, can also run with pytest)
python -m pytest tests/test_level_layout.py      # single test
python -m pytest tests/                           # all tests
python -m unittest tests.test_level_layout        # unittest runner

# Build executable
python build_exe.py
```

## Architecture

### Entry Points

`src/main.py` dispatches to four modes via `--mode`:
- **enhanced** (default) -> `EnhancedSokoban` in `src/enhanced_main.py` — full hub: menu, level selection, skins, editor, AI solver
- **gui** -> `GUIGame` in `src/gui_main.py` — direct PyGame gameplay
- **terminal** -> `TerminalGame` in `src/terminal_game.py` — console gameplay
- **editor** -> `src/editor_main.py` — graphical level editor

The **enhanced** mode is the main application. It composes `MenuSystem`, `LevelManager`, `EnhancedSkinManager`, `EnhancedLevelEditor`, `GUIGame`, and `UnifiedAIController`.

### Module Map

| Package | Purpose | Key classes |
|---|---|---|
| `src/core/` | Game logic & state | `Level`, `Game`, `SokobanState`, `ConfigManager`, `DeadlockDetector`, `AutoSolver`, `AudioManager` |
| `src/ai/` | AI solvers | `UnifiedAIController`, `AlgorithmSelector`, `EnhancedSokolutionSolver`, `VisualAISolver`, `MLMetricsCollector`, `MLReportGenerator` |
| `src/renderers/` | Display | `GUIRenderer` (PyGame), `TerminalRenderer` (ANSI) |
| `src/ui/` | UI components | `MenuSystem`, `GeneralSettingsDialog`, `KeybindingDialog`, `LevelPreview`, `MouseNavigationSystem`, `EnhancedSkinManager`, `SkinsMenu`, `widgets` (Button, ToggleButton, TextInput) |
| `src/editors/` | Level editor | `EnhancedLevelEditor` (orchestrator), `EditorRenderer`, `EditorEventHandler`, `EditorOperations` |
| `src/level_management/` | Level loading | `LevelManager`, `LevelCollectionParser`, `EnhancedLevelCollectionParser`, `LevelSelector` |
| `src/generation/` | Procedural generation | `ProceduralGenerator`, `LevelSolver` (BFS), `advanced/` ML |

### Key Patterns

**Imports**: Always absolute `src.` prefix (`from src.core.level import Level`). Entry points add parent dir to `sys.path`.

**Configuration**: Singleton `get_config_manager()` from `src.core.config_manager`. JSON file `config.json` with sections: `skin`, `display`, `game`, `keybindings`.

**Level format**: Standard Sokoban symbols: `#` wall, ` ` floor, `@` player, `$` box, `.` target, `+` player-on-target, `*` box-on-target. Collections = multiple levels in one .txt separated by blank lines with metadata (Title, Author, etc.).

**State**: `Level` holds mutable game state (map_data, player_pos, boxes list, targets, moves/pushes, history stack for undo). `SokobanState` (frozen dataclass in `sokoban_state.py`) is the immutable/hashable equivalent used by AI solvers.

**Game class hierarchy**: `Game` (base, abstract `_get_input`) -> `TerminalGame` / `GUIGame`. But `EnhancedSokoban` doesn't inherit from `Game` — it's a parallel implementation with its own event loop.

**AI solver pipeline**: `UnifiedAIController` -> `AlgorithmSelector` (picks BFS/A*/IDA*/Greedy by complexity score) -> `EnhancedSokolutionSolver` (core search). `VisualAISolver` integrates with GUI for animated solutions.

---

## Remaining Refactoring Opportunities

### Duplication

**1. Two level collection parsers**:
- `src/level_management/level_collection_parser.py` — base parser, used by `level_manager.py`
- `src/level_management/enhanced_level_collection_parser.py` — enhanced variant, imported by `level_collection_parser.py`

**2. ~~Solver duplication~~**: DONE — Deleted 3 redundant solvers (`advanced_solver.py`, `expert_solver.py`, `sokolution_solver.py` totaling ~2373 lines). `AutoSolver` now delegates to `AlgorithmSelector` + `EnhancedSokolutionSolver`. Only `src/generation/level_solver.py` (250 lines, lightweight BFS) remains for fast solvability testing in `ProceduralGenerator`.

### Known Bugs

**ConfigManager.reset_to_defaults()**: Uses `self.config = self.default_config.copy()` — shallow copy, nested dicts share references. Mutations to sections corrupt defaults.

**ConfigManager._save_config()**: Over-engineered with backup creation, read-back verification, 8+ print statements per save.

**DeadlockDetector corral check**: BFS with 0.1s hardcoded timeout can block the game loop.

**StateManager cache**: Never cleared — grows unbounded over long sessions.

**GameplayHighlight.render_highlight()**: Returns immediately (disabled), dead code.

### Architectural Issues

**No base interfaces**: No abstract `Renderer`, `SkinManager`, `Editor`, or `Button` interface.

**`Game` vs `EnhancedSokoban`**: `Game` is an abstract base with `_get_input()` raising `NotImplementedError` (should use ABC). `EnhancedSokoban` doesn't inherit from `Game` — completely parallel implementation.

**Mixed concerns in renderers**: `GUIRenderer.render_level()` is 342 lines combining scaling, layer rendering, stats display, and completion messages.

**No event system**: Multiple independent `pygame.event.get()` loops in `MenuSystem`, `EnhancedLevelEditor`, `GUIGame`, `SkinsMenu`, `LevelPreview`.

**`EnhancedSkinManager` complexity**: 977 lines with dual sprite history tracking systems, extensive debug logging, nested state machines.

### Module Dependency Flow (Production Path)

```
src/main.py
  -> src/enhanced_main.py (EnhancedSokoban)
       -> src/ui/menu_system.py (MenuSystem)
            -> src/ui/settings_dialog.py (GeneralSettingsDialog)
            -> src/ui/keybinding_dialog.py (KeybindingDialog)
       -> src/level_management/level_manager.py (LevelManager)
            -> src/level_management/level_collection_parser.py
            -> src/core/level.py (Level)
            -> src/generation/procedural_generator.py
       -> src/ui/skins/enhanced_skin_manager.py (EnhancedSkinManager)
       -> src/renderers/gui_renderer.py (GUIRenderer)
       -> src/ui/mouse_navigation.py (MouseNavigationSystem)
       -> src/ui/level_preview.py (LevelPreview)
       -> src/ui/interactive_highlight.py (GameplayHighlight)
       -> src/editors/enhanced_level_editor.py (EnhancedLevelEditor)
            -> src/editors/editor_renderer.py (EditorRenderer)
            -> src/editors/editor_event_handler.py (EditorEventHandler)
            -> src/editors/editor_operations.py (EditorOperations)
       -> src/gui_main.py (GUIGame -> inherits Game)
       -> src/ai/unified_ai_controller.py (UnifiedAIController)
            -> src/ai/algorithm_selector.py
            -> src/ai/enhanced_sokolution_solver.py
            -> src/ai/ml_metrics_collector.py
            -> src/ai/ml_report_generator.py
       -> src/ai/visual_ai_solver.py (VisualAISolver)
       -> src/core/config_manager.py (singleton)
       -> src/core/auto_solver.py (AutoSolver)
            -> src/ai/algorithm_selector.py
            -> src/ai/enhanced_sokolution_solver.py
```

### Size Hotspots (largest files)

| File | Lines | Issue |
|---|---|---|
| `src/ui/menu_system.py` | ~1015 | Dialogs extracted to `settings_dialog.py` + `keybinding_dialog.py` |
| `src/renderers/gui_renderer.py` | ~958 | `render_level()` split into 10 submethods via `_RenderContext` |
| `src/editors/editor_renderer.py` | ~922 | Extracted from `EnhancedLevelEditor` |
| `src/editors/enhanced_level_editor.py` | ~646 | Orchestrator; delegates to 3 composition classes |
| `src/ai/enhanced_sokolution_solver.py` | ~1280 | Core solver — large but well-structured |
| `src/ui/skins/enhanced_skin_manager.py` | 977 | Over-complex, dual tracking systems |
| `src/ui/mouse_navigation.py` | 888 | Too many concerns in one class |
| `src/ai/ml_report_generator.py` | 735 | |

### Refactoring Priority Order

1. ~~**Extract shared UI components**~~: DONE — `src/ui/widgets.py` (Button, ToggleButton, TextInput). All modules import from widgets.
2. ~~**Split god classes**~~: DONE — `GUIRenderer.render_level()` split into 10 submethods via `_RenderContext` dataclass. `MenuSystem` dialogs extracted to `src/ui/settings_dialog.py` + `src/ui/keybinding_dialog.py` (~550 lines removed). `EnhancedLevelEditor` decomposed via composition into orchestrator (~646 lines) + `src/editors/editor_renderer.py` (~922 lines) + `src/editors/editor_event_handler.py` (~332 lines) + `src/editors/editor_operations.py` (~457 lines).
3. ~~**Consolidate solvers**~~: DONE — Deleted 3 redundant `generation/` solvers (~2373 lines). `AutoSolver` rewritten to delegate to `AlgorithmSelector` + `EnhancedSokolutionSolver`. Only `level_solver.py` (lightweight BFS) kept for `ProceduralGenerator`.
4. **Introduce interfaces**: `AbstractRenderer`, `AbstractSkinManager` to enable polymorphism.
5. **Fix config system**: Replace global singleton with dependency injection, fix shallow copy bug, remove verbose logging.
6. **Unify event handling**: Extract a common event dispatcher instead of N independent `pygame.event.get()` loops.

## Dependencies

Core: `pygame`, `pillow`, `numpy`, `keyboard`. Optional (ML generation): `matplotlib`, `scikit-learn`, `tensorflow`.

## Level Files

Located in `src/levels/` organized by collection subdirectories (e.g., `Original & Extra/`, `Boxxle 1/`, `Magic Sokoban/`). The `Original & Extra` collection has 90 classic levels.
