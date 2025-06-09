# Responsive UI Layout System for PySokoban

## Overview

This document describes the responsive UI layout system implemented for the PySokoban game. The system is designed to provide a flexible and responsive user interface that adapts to different screen sizes and resolutions.

## Design Goals

1. **Responsive Layout**: UI elements should adjust properly when the window is resized
2. **Relative Positioning**: Elements should be positioned relative to their parent containers
3. **Flexible Sizing**: Elements should be sized based on percentages of available space
4. **Consistent Styling**: UI elements should have a consistent look and feel
5. **Easy to Use**: The system should be easy to use for developers

## Implementation

### UI Layout Module

The core of the system is the `ui_layout.py` module, which provides the following classes:

- **UIElement**: Base class for all UI elements
- **Container**: A container for UI elements
- **Row**: A container that arranges children horizontally
- **Column**: A container that arranges children vertically
- **Grid**: A container that arranges children in a grid layout
- **Text**: A text element
- **Button**: A button element
- **Image**: An image element

### Responsive Positioning and Sizing

Elements can be positioned and sized using either:
- **Relative values** (0-1): Interpreted as a percentage of the parent container's dimensions
- **Absolute values** (>1): Interpreted as pixel values

For example:
```python
# Create a container that takes up the entire screen
main_container = Container(0, 0, screen_width, screen_height)

# Create a header that takes up 20% of the height
header = Container(0, 0, 1, 0.2)
main_container.add(header)

# Create a button that's 50% of the width and centered
button = Button("Click Me", 0.25, 0, 0.5, None)
header.add(button)
```

### Container Hierarchy

UI elements are organized in a hierarchy of containers:
1. **Main Container**: Covers the entire screen
2. **Section Containers**: Header, Content, Footer
3. **Element Containers**: Rows, Columns, Grids
4. **UI Elements**: Buttons, Text, Images

This hierarchy allows for complex layouts that automatically adjust to screen size changes.

### Window Resizing

When the window is resized:
1. The main container dimensions are updated
2. All child elements are recursively updated
3. The layout is redrawn

## Usage Examples

### Creating a Basic Layout

```python
# Create main container
main_container = Container(0, 0, screen_width, screen_height)

# Create header
header = Container(0, 0, 1, 0.2)
main_container.add(header)

# Add title to header
title = Text("My Game", 0, 0.5, 1, None, font, color=(255, 255, 255))
header.add(title)

# Create content area
content = Container(0, 0.2, 1, 0.7)
main_container.add(content)

# Create footer
footer = Container(0, 0.9, 1, 0.1)
main_container.add(footer)
```

### Creating a Button Grid

```python
# Create a grid with 3 rows and 4 columns
grid = Grid(0, 0, 1, 1, rows=3, cols=4, h_spacing=10, v_spacing=10)
content.add(grid)

# Add buttons to the grid
for i in range(12):
    button = Button(f"Button {i+1}", 0, 0, 1, 1)
    grid.add(button)
```

### Rendering the UI

```python
# Update all UI elements
main_container.update()

# Draw all UI elements
main_container.draw(screen)

# Update the display
pygame.display.flip()
```

## Refactored Components

The following components have been refactored to use the new UI layout system:

1. **Level Selector**: Displays available levels organized by categories
2. **Menu System**: Manages different menu screens (main menu, play menu, settings, etc.)

## Future Improvements

1. **Animation Support**: Add support for animating UI elements
2. **Theming System**: Implement a theming system for consistent styling
3. **More UI Elements**: Add more specialized UI elements (sliders, checkboxes, etc.)
4. **Accessibility Features**: Add support for keyboard navigation and screen readers

## Conclusion

The responsive UI layout system provides a solid foundation for building flexible and responsive user interfaces in Pygame. It makes it easier to create UIs that work well on different screen sizes and resolutions, improving the overall user experience.