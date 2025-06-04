# Advanced Procedural Generation System for Sokoban

This package provides an enhanced procedural generation system for Sokoban levels, incorporating:

1. **Pattern-Based Generation**: Uses predefined patterns for both puzzle elements and structural elements
2. **Style Transfer**: Analyzes and applies style from existing levels to new ones
3. **Machine Learning**: Learns from player feedback to improve generation over time

## System Architecture

The system consists of several integrated components:

- **Advanced Procedural Generator**: Main orchestration module
- **Pattern-Based Generator**: Handles pattern detection, storage, and composition
- **Style Transfer Engine**: Analyzes, extracts, and applies style
- **Machine Learning System**: Collects data, analyzes feedback, and learns to improve generation

## Usage

### Basic Usage

```python
from advanced_generation import AdvancedProceduralGenerator

# Create the generator
generator = AdvancedProceduralGenerator()

# Generate a level with default parameters
level = generator.generate_level()

# Print the level
print(level.get_state_string())
```

### Advanced Usage

```python
# Generate a level with custom parameters
custom_params = {
    'min_width': 10,
    'max_width': 12,
    'min_height': 10,
    'max_height': 12,
    'min_boxes': 3,
    'max_boxes': 5,
    'wall_density': 0.25,
    'style': {
        'wall_style': {
            'density': 0.3,
            'distribution': 'clustered'
        },
        'space_style': {
            'openness': 0.6,
            'room_size': 'large'
        },
        'symmetry': {
            'horizontal': 0.7
        }
    }
}

level = generator.generate_level(custom_params)
```

### Style Transfer

```python
# Load an existing level as a style source
with open("levels/level1.txt", "r") as f:
    level_data = f.read()
    
style_source = Level(level_data=level_data)

# Extract style from the source level
style_params = generator.style_transfer.extract_style(style_source)

# Generate a level with the extracted style
custom_params['style_source'] = style_source
level = generator.generate_level(custom_params)
```

### Collecting Player Feedback

```python
import pygame
from advanced_generation import MachineLearningSystem, FeedbackCollectionUI

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))

# Create ML system and feedback UI
ml_system = MachineLearningSystem()
feedback_ui = FeedbackCollectionUI(screen, ml_system)

# Show feedback UI for a level
level_id = level.get_state_string()
completion_time = 120.5  # seconds
move_count = 45
feedback_ui.show(level_id, completion_time, move_count)

# In your game loop:
feedback_ui.render()
for event in pygame.event.get():
    feedback_ui.handle_event(event)
```

## Components

### Pattern-Based Generator

The pattern-based generator uses a library of patterns for both puzzle elements (box-wall configurations) and structural elements (rooms, corridors). It can:

- Detect patterns in existing levels
- Store patterns in a library
- Compose patterns to create coherent level structures

### Style Transfer Engine

The style transfer engine analyzes the style of existing levels and applies it to new ones. It can:

- Analyze wall density, space characteristics, object placement, symmetry, and aesthetics
- Extract style parameters from analysis results
- Apply style parameters to new levels

### Machine Learning System

The machine learning system learns from player feedback to improve generation over time. It can:

- Collect player feedback on levels
- Analyze feedback to create training data
- Train models to predict difficulty, engagement, pattern effectiveness, and style preferences
- Adjust generation parameters based on learning

## Future Improvements

1. **Enhanced Pattern Detection**: Implement more sophisticated algorithms for detecting patterns in existing levels
2. **Advanced Style Analysis**: Develop more detailed style analysis techniques
3. **Neural Network Models**: Replace simple statistical models with neural networks for better learning
4. **Reinforcement Learning**: Implement reinforcement learning for optimizing generation parameters
5. **Community Pattern Sharing**: Create a system for sharing and rating patterns