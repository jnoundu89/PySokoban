"""
UI Layout System for Pygame

This module provides a responsive layout system for Pygame applications,
similar to Bootstrap's grid system. It allows for creating containers and
arranging UI elements in a responsive manner.
"""

import pygame

class UIElement:
    """Base class for all UI elements."""
    
    def __init__(self, x=0, y=0, width=0, height=0, padding=0, margin=0):
        """
        Initialize a UI element.
        
        Args:
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            padding (int or tuple): Padding inside the element (can be a single value or a tuple for top, right, bottom, left)
            margin (int or tuple): Margin outside the element (can be a single value or a tuple for top, right, bottom, left)
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Convert padding and margin to 4-value tuples (top, right, bottom, left)
        if isinstance(padding, int):
            self.padding = (padding, padding, padding, padding)
        else:
            self.padding = padding
            
        if isinstance(margin, int):
            self.margin = (margin, margin, margin, margin)
        else:
            self.margin = margin
            
        self.parent = None
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.content_rect = pygame.Rect(0, 0, 0, 0)
        
    def get_absolute_rect(self):
        """
        Calculate the absolute rectangle of this element based on parent dimensions.
        
        Returns:
            pygame.Rect: The absolute rectangle of this element
        """
        if self.parent is None:
            return self.rect
            
        parent_rect = self.parent.content_rect
        
        # Calculate position
        if 0 <= self.x <= 1:
            # Percentage
            x = parent_rect.x + int(parent_rect.width * self.x) + self.margin[3]
        else:
            # Absolute
            x = parent_rect.x + self.x + self.margin[3]
            
        if 0 <= self.y <= 1:
            # Percentage
            y = parent_rect.y + int(parent_rect.height * self.y) + self.margin[0]
        else:
            # Absolute
            y = parent_rect.y + self.y + self.margin[0]
            
        # Calculate size
        if 0 <= self.width <= 1:
            # Percentage
            width = int(parent_rect.width * self.width) - self.margin[1] - self.margin[3]
        else:
            # Absolute
            width = self.width - self.margin[1] - self.margin[3]
            
        if 0 <= self.height <= 1:
            # Percentage
            height = int(parent_rect.height * self.height) - self.margin[0] - self.margin[2]
        else:
            # Absolute
            height = self.height - self.margin[0] - self.margin[2]
            
        self.rect = pygame.Rect(x, y, width, height)
        
        # Calculate content rect (inside padding)
        self.content_rect = pygame.Rect(
            x + self.padding[3],
            y + self.padding[0],
            width - self.padding[1] - self.padding[3],
            height - self.padding[0] - self.padding[2]
        )
        
        return self.rect
        
    def update(self):
        """Update the element. Override in subclasses."""
        self.get_absolute_rect()
        
    def draw(self, surface):
        """
        Draw the element. Override in subclasses.
        
        Args:
            surface (pygame.Surface): Surface to draw on
        """
        pass


class Container(UIElement):
    """A container for UI elements."""
    
    def __init__(self, x=0, y=0, width=1, height=1, padding=0, margin=0, bg_color=None, border_radius=0):
        """
        Initialize a container.
        
        Args:
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            padding (int or tuple): Padding inside the container
            margin (int or tuple): Margin outside the container
            bg_color (tuple): Background color (r, g, b) or None for transparent
            border_radius (int): Border radius for rounded corners
        """
        super().__init__(x, y, width, height, padding, margin)
        self.children = []
        self.bg_color = bg_color
        self.border_radius = border_radius
        
    def add(self, element):
        """
        Add a child element to this container.
        
        Args:
            element (UIElement): Element to add
            
        Returns:
            UIElement: The added element (for chaining)
        """
        element.parent = self
        self.children.append(element)
        return element
        
    def update(self):
        """Update this container and all its children."""
        super().update()
        for child in self.children:
            child.update()
            
    def draw(self, surface):
        """
        Draw this container and all its children.
        
        Args:
            surface (pygame.Surface): Surface to draw on
        """
        # Draw background if specified
        if self.bg_color is not None:
            pygame.draw.rect(surface, self.bg_color, self.rect, 0, self.border_radius)
            
        # Draw children
        for child in self.children:
            child.draw(surface)


class Row(Container):
    """A row container that arranges children horizontally."""
    
    def __init__(self, x=0, y=0, width=1, height=None, padding=0, margin=0, bg_color=None, border_radius=0, spacing=5):
        """
        Initialize a row container.
        
        Args:
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            padding (int or tuple): Padding inside the container
            margin (int or tuple): Margin outside the container
            bg_color (tuple): Background color (r, g, b) or None for transparent
            border_radius (int): Border radius for rounded corners
            spacing (int): Spacing between children
        """
        super().__init__(x, y, width, height, padding, margin, bg_color, border_radius)
        self.spacing = spacing
        
    def update(self):
        """Update this row and arrange its children horizontally."""
        super().update()
        
        # Calculate total width of fixed-width children and count flexible children
        total_fixed_width = 0
        flexible_children = 0
        
        for child in self.children:
            if child.width > 1:  # Fixed width
                total_fixed_width += child.width + child.margin[1] + child.margin[3]
            else:  # Flexible width (percentage)
                flexible_children += 1
                
        # Calculate available width for flexible children
        available_width = self.content_rect.width - total_fixed_width - (len(self.children) - 1) * self.spacing
        
        # Position children
        x_offset = 0
        for child in self.children:
            # Set child's x position
            child.x = x_offset
            
            # Update child
            child.parent = self
            child.update()
            
            # Update x_offset for next child
            x_offset += child.rect.width + self.spacing


class Column(Container):
    """A column container that arranges children vertically."""
    
    def __init__(self, x=0, y=0, width=None, height=1, padding=0, margin=0, bg_color=None, border_radius=0, spacing=5):
        """
        Initialize a column container.
        
        Args:
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            padding (int or tuple): Padding inside the container
            margin (int or tuple): Margin outside the container
            bg_color (tuple): Background color (r, g, b) or None for transparent
            border_radius (int): Border radius for rounded corners
            spacing (int): Spacing between children
        """
        super().__init__(x, y, width, height, padding, margin, bg_color, border_radius)
        self.spacing = spacing
        
    def update(self):
        """Update this column and arrange its children vertically."""
        super().update()
        
        # Calculate total height of fixed-height children and count flexible children
        total_fixed_height = 0
        flexible_children = 0
        
        for child in self.children:
            if child.height > 1:  # Fixed height
                total_fixed_height += child.height + child.margin[0] + child.margin[2]
            else:  # Flexible height (percentage)
                flexible_children += 1
                
        # Calculate available height for flexible children
        available_height = self.content_rect.height - total_fixed_height - (len(self.children) - 1) * self.spacing
        
        # Position children
        y_offset = 0
        for child in self.children:
            # Set child's y position
            child.y = y_offset
            
            # Update child
            child.parent = self
            child.update()
            
            # Update y_offset for next child
            y_offset += child.rect.height + self.spacing


class Grid(Container):
    """A grid container that arranges children in a grid layout."""
    
    def __init__(self, x=0, y=0, width=1, height=1, rows=1, cols=1, padding=0, margin=0, 
                 bg_color=None, border_radius=0, h_spacing=5, v_spacing=5):
        """
        Initialize a grid container.
        
        Args:
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            rows (int): Number of rows in the grid
            cols (int): Number of columns in the grid
            padding (int or tuple): Padding inside the container
            margin (int or tuple): Margin outside the container
            bg_color (tuple): Background color (r, g, b) or None for transparent
            border_radius (int): Border radius for rounded corners
            h_spacing (int): Horizontal spacing between children
            v_spacing (int): Vertical spacing between children
        """
        super().__init__(x, y, width, height, padding, margin, bg_color, border_radius)
        self.rows = rows
        self.cols = cols
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        
    def update(self):
        """Update this grid and arrange its children in a grid layout."""
        super().update()
        
        # Calculate cell dimensions
        cell_width = (self.content_rect.width - (self.cols - 1) * self.h_spacing) / self.cols
        cell_height = (self.content_rect.height - (self.rows - 1) * self.v_spacing) / self.rows
        
        # Position children
        for i, child in enumerate(self.children):
            row = i // self.cols
            col = i % self.cols
            
            # Set child's position and size
            child.x = col * (cell_width + self.h_spacing)
            child.y = row * (cell_height + self.v_spacing)
            
            # If child has percentage width/height, it will be relative to the cell
            if child.width <= 1:
                child.width = cell_width * child.width
            if child.height <= 1:
                child.height = cell_height * child.height
                
            # Update child
            child.parent = self
            child.update()


class Text(UIElement):
    """A text element."""
    
    def __init__(self, text, x=0, y=0, width=None, height=None, font=None, font_size=24, 
                 color=(0, 0, 0), align="center", valign="middle", padding=0, margin=0):
        """
        Initialize a text element.
        
        Args:
            text (str): Text to display
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            font (pygame.font.Font): Font to use or None for default
            font_size (int): Font size
            color (tuple): Text color (r, g, b)
            align (str): Horizontal alignment ("left", "center", "right")
            valign (str): Vertical alignment ("top", "middle", "bottom")
            padding (int or tuple): Padding inside the element
            margin (int or tuple): Margin outside the element
        """
        super().__init__(x, y, width, height, padding, margin)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.align = align
        self.valign = valign
        
        # Create font
        if font is None:
            self.font = pygame.font.Font(None, font_size)
        else:
            self.font = font
            
        # Render text
        self.text_surface = self.font.render(text, True, color)
        self.text_rect = self.text_surface.get_rect()
        
        # If width or height is None, use text dimensions
        if width is None:
            self.width = self.text_rect.width + self.padding[1] + self.padding[3]
        if height is None:
            self.height = self.text_rect.height + self.padding[0] + self.padding[2]
            
    def update(self):
        """Update this text element."""
        super().update()
        
        # Position text within the element based on alignment
        if self.align == "left":
            self.text_rect.left = self.rect.left + self.padding[3]
        elif self.align == "center":
            self.text_rect.centerx = self.rect.centerx
        elif self.align == "right":
            self.text_rect.right = self.rect.right - self.padding[1]
            
        if self.valign == "top":
            self.text_rect.top = self.rect.top + self.padding[0]
        elif self.valign == "middle":
            self.text_rect.centery = self.rect.centery
        elif self.valign == "bottom":
            self.text_rect.bottom = self.rect.bottom - self.padding[2]
            
    def draw(self, surface):
        """
        Draw this text element.
        
        Args:
            surface (pygame.Surface): Surface to draw on
        """
        surface.blit(self.text_surface, self.text_rect)


class Button(UIElement):
    """A button element."""
    
    def __init__(self, text, x=0, y=0, width=None, height=None, action=None, 
                 color=(100, 100, 200), hover_color=(130, 130, 255), text_color=(255, 255, 255),
                 font=None, font_size=24, padding=10, margin=0, border_radius=5):
        """
        Initialize a button element.
        
        Args:
            text (str): Text to display
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            action (function): Function to call when button is clicked
            color (tuple): Button color (r, g, b)
            hover_color (tuple): Button color when hovered (r, g, b)
            text_color (tuple): Text color (r, g, b)
            font (pygame.font.Font): Font to use or None for default
            font_size (int): Font size
            padding (int or tuple): Padding inside the button
            margin (int or tuple): Margin outside the button
            border_radius (int): Border radius for rounded corners
        """
        super().__init__(x, y, width, height, padding, margin)
        self.text = text
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.text_color = text_color
        self.font_size = font_size
        self.border_radius = border_radius
        self.hovered = False
        
        # Create font
        if font is None:
            self.font = pygame.font.Font(None, font_size)
        else:
            self.font = font
            
        # Render text
        self.text_surface = self.font.render(text, True, text_color)
        self.text_rect = self.text_surface.get_rect()
        
        # If width or height is None, use text dimensions plus padding
        if width is None:
            self.width = self.text_rect.width + self.padding[1] + self.padding[3]
        if height is None:
            self.height = self.text_rect.height + self.padding[0] + self.padding[2]
            
    def update(self):
        """Update this button."""
        super().update()
        
        # Center text in button
        self.text_rect.center = self.rect.center
        
    def is_hovered(self, pos):
        """
        Check if the button is being hovered.
        
        Args:
            pos (tuple): Mouse position (x, y)
            
        Returns:
            bool: True if the button is being hovered, False otherwise
        """
        return self.rect.collidepoint(pos)
        
    def handle_event(self, event):
        """
        Handle pygame events.
        
        Args:
            event (pygame.event.Event): Event to handle
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.is_hovered(event.pos)
            self.current_color = self.hover_color if self.hovered else self.color
            return True
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered(event.pos) and self.action:
                self.action()
                return True
                
        return False
        
    def draw(self, surface):
        """
        Draw this button.
        
        Args:
            surface (pygame.Surface): Surface to draw on
        """
        # Draw button background
        pygame.draw.rect(surface, self.current_color, self.rect, 0, self.border_radius)
        
        # Draw text
        surface.blit(self.text_surface, self.text_rect)


class Image(UIElement):
    """An image element."""
    
    def __init__(self, image, x=0, y=0, width=None, height=None, padding=0, margin=0, scale_mode="fit"):
        """
        Initialize an image element.
        
        Args:
            image (pygame.Surface or str): Image to display or path to image file
            x (float): X position as a percentage of parent width (0-1) or absolute value (>1)
            y (float): Y position as a percentage of parent height (0-1) or absolute value (>1)
            width (float): Width as a percentage of parent width (0-1) or absolute value (>1)
            height (float): Height as a percentage of parent height (0-1) or absolute value (>1)
            padding (int or tuple): Padding inside the element
            margin (int or tuple): Margin outside the element
            scale_mode (str): How to scale the image ("fit", "fill", "stretch", "none")
        """
        super().__init__(x, y, width, height, padding, margin)
        
        # Load image if it's a string
        if isinstance(image, str):
            self.original_image = pygame.image.load(image).convert_alpha()
        else:
            self.original_image = image
            
        self.image = self.original_image
        self.scale_mode = scale_mode
        
        # If width or height is None, use image dimensions
        if width is None:
            self.width = self.original_image.get_width()
        if height is None:
            self.height = self.original_image.get_height()
            
    def update(self):
        """Update this image element."""
        super().update()
        
        # Scale image based on scale_mode
        content_width = self.content_rect.width
        content_height = self.content_rect.height
        
        if self.scale_mode == "stretch":
            # Stretch to fill content rect
            self.image = pygame.transform.scale(self.original_image, (content_width, content_height))
            self.image_rect = self.image.get_rect(topleft=self.content_rect.topleft)
            
        elif self.scale_mode == "fit":
            # Scale to fit while maintaining aspect ratio
            orig_width = self.original_image.get_width()
            orig_height = self.original_image.get_height()
            
            # Calculate scale factor
            scale_x = content_width / orig_width
            scale_y = content_height / orig_height
            scale = min(scale_x, scale_y)
            
            # Scale image
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            self.image = pygame.transform.scale(self.original_image, (new_width, new_height))
            
            # Center image in content rect
            self.image_rect = self.image.get_rect(center=self.content_rect.center)
            
        elif self.scale_mode == "fill":
            # Scale to fill while maintaining aspect ratio
            orig_width = self.original_image.get_width()
            orig_height = self.original_image.get_height()
            
            # Calculate scale factor
            scale_x = content_width / orig_width
            scale_y = content_height / orig_height
            scale = max(scale_x, scale_y)
            
            # Scale image
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            self.image = pygame.transform.scale(self.original_image, (new_width, new_height))
            
            # Center image in content rect
            self.image_rect = self.image.get_rect(center=self.content_rect.center)
            
        else:  # "none"
            # Don't scale, just center
            self.image = self.original_image
            self.image_rect = self.image.get_rect(center=self.content_rect.center)
            
    def draw(self, surface):
        """
        Draw this image element.
        
        Args:
            surface (pygame.Surface): Surface to draw on
        """
        surface.blit(self.image, self.image_rect)