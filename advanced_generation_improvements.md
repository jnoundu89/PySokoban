# Advanced Procedural Generation System - Improvement Plan

Based on our testing, we've identified several areas that need improvement in our implementation:

## 1. Level Complexity

**Issue**: All generated levels are very simple, with just a box, a target, and the player in an empty room.

**Solution**:
- Enhance the `LevelGeneratorCore._create_structure()` method to create more complex structures
- Implement actual pattern composition in `PatternComposer.create_composition_plan()`
- Add more diverse patterns to the pattern library

```python
def _create_structure(self, structure):
    """
    Create the basic structure of the level.
    
    Args:
        structure (dict): Structure parameters.
        
    Returns:
        Level: A level with basic structure.
    """
    # Get dimensions from structure or use defaults
    width = structure.get('width', 10)
    height = structure.get('height', 10)
    wall_density = structure.get('wall_density', 0.2)
    
    # Create an empty grid with walls around the perimeter
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                row.append(WALL)  # Wall
            else:
                row.append(FLOOR)  # Floor
        grid.append(row)
    
    # Add internal walls based on wall density
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if random.random() < wall_density:
                grid[y][x] = WALL
    
    # Ensure the level is connected (all floor tiles are reachable)
    # This is a placeholder - a real implementation would check connectivity
    # and fix disconnected areas
    
    # Convert grid to string
    level_string = '\n'.join(''.join(row) for row in grid)
    
    # Create and return the level
    return Level(level_data=level_string)
```

## 2. Box Count

**Issue**: Despite specifying min_boxes=3, max_boxes=5 in the custom parameters, all generated levels have only 1 box.

**Solution**:
- Update `LevelGeneratorCore._place_elements()` to respect the box count parameters

```python
def _place_elements(self, level, placement, params):
    """
    Place puzzle elements in the level.
    
    Args:
        level (Level): The level to modify.
        placement (dict): Placement parameters.
        params (dict): Generation parameters.
        
    Returns:
        Level: The modified level.
    """
    # Get box count from parameters
    min_boxes = params.get('min_boxes', 1)
    max_boxes = params.get('max_boxes', 3)
    num_boxes = random.randint(min_boxes, max_boxes)
    
    # Find all floor positions
    floor_positions = []
    for y in range(1, level.height - 1):
        for x in range(1, level.width - 1):
            if not level.is_wall(x, y):
                floor_positions.append((x, y))
    
    # Shuffle positions
    random.shuffle(floor_positions)
    
    # Make sure we have enough floor positions
    if len(floor_positions) < num_boxes * 2 + 1:
        num_boxes = (len(floor_positions) - 1) // 2
        if num_boxes < 1:
            num_boxes = 1
    
    # Create a new grid
    grid = []
    for y in range(level.height):
        row = []
        for x in range(level.width):
            if level.is_wall(x, y):
                row.append(WALL)
            else:
                row.append(FLOOR)
        grid.append(row)
    
    # Place player
    player_pos = floor_positions.pop()
    grid[player_pos[1]][player_pos[0]] = PLAYER
    
    # Place boxes and targets
    for _ in range(num_boxes):
        if len(floor_positions) < 2:
            break
            
        # Place box
        box_pos = floor_positions.pop()
        grid[box_pos[1]][box_pos[0]] = BOX
        
        # Place target
        target_pos = floor_positions.pop()
        grid[target_pos[1]][target_pos[0]] = TARGET
    
    # Convert grid to string
    level_string = '\n'.join(''.join(row) for row in grid)
    
    # Create and return the level
    return Level(level_data=level_string)
```

## 3. Pattern Usage

**Issue**: The pattern-based generation doesn't seem to be using any of the patterns from the pattern library.

**Solution**:
- Enhance `PatternComposer.create_composition_plan()` to actually use the patterns
- Implement pattern placement in `LevelGeneratorCore._place_elements()`

```python
def create_composition_plan(self, puzzle_patterns, structural_patterns, params):
    """
    Create a plan for composing patterns into a level.
    
    Args:
        puzzle_patterns (list): Selected puzzle patterns.
        structural_patterns (list): Selected structural patterns.
        params (dict): Generation parameters.
        
    Returns:
        dict: A composition plan for the level generator.
    """
    # Select a structural pattern based on parameters
    selected_structural = None
    if structural_patterns and random.random() < 0.7:  # 70% chance to use a pattern
        selected_structural = random.choice(structural_patterns)
    
    # Select puzzle patterns based on parameters
    selected_puzzles = []
    num_puzzles = random.randint(1, 3)
    if puzzle_patterns:
        for _ in range(num_puzzles):
            if puzzle_patterns:
                selected_puzzles.append(random.choice(puzzle_patterns))
    
    # Create structure parameters
    width = random.randint(params.get('min_width', 8), params.get('max_width', 15))
    height = random.randint(params.get('min_height', 8), params.get('max_height', 15))
    wall_density = params.get('wall_density', 0.2)
    
    structure = {
        'width': width,
        'height': height,
        'wall_density': wall_density,
        'pattern': selected_structural
    }
    
    # Create placement parameters
    min_boxes = params.get('min_boxes', 1)
    max_boxes = params.get('max_boxes', 3)
    
    placement = {
        'min_boxes': min_boxes,
        'max_boxes': max_boxes,
        'patterns': selected_puzzles
    }
    
    # Create connection parameters
    connections = {
        'connect_all': True
    }
    
    return {
        'structure': structure,
        'placement': placement,
        'connections': connections
    }
```

## 4. Style Transfer

**Issue**: The style transfer doesn't seem to be capturing the essence of the source level.

**Solution**:
- Improve `StyleAnalyzer.analyze()` to better capture style characteristics
- Enhance `StyleApplicator.apply()` to apply style more effectively

```python
def _apply_wall_style(self, level, wall_style):
    """
    Apply wall style to a level.
    
    Args:
        level (Level): The level to modify.
        wall_style (dict): Wall style parameters.
        
    Returns:
        Level: The modified level.
    """
    # Get wall density from style
    density = wall_style.get('density', 0.2)
    
    # Create a new grid
    grid = []
    for y in range(level.height):
        row = []
        for x in range(level.width):
            if level.is_wall(x, y):
                row.append(WALL)
            else:
                row.append(FLOOR)
        grid.append(row)
    
    # Adjust internal walls based on density
    for y in range(1, level.height - 1):
        for x in range(1, level.width - 1):
            # Skip tiles with objects
            if level.is_box(x, y) or level.is_target(x, y) or level.is_player(x, y):
                continue
                
            # Adjust walls based on density
            if level.is_wall(x, y) and random.random() > density:
                grid[y][x] = FLOOR
            elif not level.is_wall(x, y) and random.random() < density:
                grid[y][x] = WALL
    
    # Convert grid to string
    level_string = '\n'.join(''.join(row) for row in grid)
    
    # Create and return the level
    return Level(level_data=level_string)
```

## 5. Internal Walls

**Issue**: None of the generated levels have any internal walls, despite setting wall_density=0.25.

**Solution**:
- Update `LevelGeneratorCore._create_structure()` to add internal walls based on the wall density parameter (see solution for issue #1)

## Implementation Plan

1. Extract the `LevelGeneratorCore` class from `advanced_procedural_generator.py` into its own file
2. Implement the improvements for box count and internal walls
3. Enhance the pattern composition and style transfer
4. Add more patterns to the pattern library
5. Test the improved implementation

These improvements will make the generated levels more complex, diverse, and interesting, while better respecting the specified parameters.