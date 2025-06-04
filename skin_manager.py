"""
Skin Manager for the Sokoban game.

This module provides functionality for managing different visual themes (skins)
for the game elements, allowing players to customize the game's appearance.
"""

import os
import pygame
from constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET, CELL_SIZE

class SkinManager:
    """
    Class for managing different visual themes (skins) for the game.
    
    This class handles loading, switching between, and applying different visual themes
    to the game elements.
    """
    
    def __init__(self):
        """
        Initialize the skin manager.
        """
        self.skins = {}
        self.current_skin = 'default'
        self.load_available_skins()
        
    def load_available_skins(self):
        """
        Load all available skins from the skins directory.
        """
        # Check if skins directory exists, create it if not
        skins_dir = os.path.join(os.path.dirname(__file__), 'skins')
        if not os.path.exists(skins_dir):
            os.makedirs(skins_dir)
            self._create_default_skin()
            
        # Load each skin directory
        for skin_name in os.listdir(skins_dir):
            skin_path = os.path.join(skins_dir, skin_name)
            if os.path.isdir(skin_path):
                self.skins[skin_name] = self._load_skin(skin_path)
                
        # If no skins were loaded, create and load the default skin
        if not self.skins:
            self._create_default_skin()
            default_skin_path = os.path.join(skins_dir, 'default')
            self.skins['default'] = self._load_skin(default_skin_path)
            
    def _load_skin(self, skin_path):
        """
        Load a skin from the specified directory.
        
        Args:
            skin_path (str): Path to the skin directory.
            
        Returns:
            dict: Dictionary containing the skin's assets.
        """
        skin = {}
        
        # Define the elements to load
        elements = {
            'wall': WALL,
            'floor': FLOOR,
            'player': PLAYER,
            'box': BOX,
            'target': TARGET,
            'player_on_target': PLAYER_ON_TARGET,
            'box_on_target': BOX_ON_TARGET
        }
        
        # Try to load each element's image
        for element_name, element_char in elements.items():
            image_path = os.path.join(skin_path, f"{element_name}.png")
            
            try:
                if os.path.exists(image_path):
                    image = pygame.image.load(image_path)
                    skin[element_char] = pygame.transform.scale(image, (CELL_SIZE, CELL_SIZE))
                else:
                    # If image doesn't exist, use a default colored surface
                    skin[element_char] = self._create_default_element(element_name)
            except pygame.error:
                # If loading fails, use a default colored surface
                skin[element_char] = self._create_default_element(element_name)
                
        return skin
        
    def _create_default_element(self, element_name):
        """
        Create a default surface for an element.
        
        Args:
            element_name (str): Name of the element.
            
        Returns:
            pygame.Surface: Surface for the element.
        """
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
        
        # Define colors for different elements
        colors = {
            'wall': (100, 100, 100),
            'floor': (200, 200, 200),
            'player': (0, 0, 255),
            'box': (139, 69, 19),
            'target': (255, 0, 0),
            'player_on_target': (0, 0, 255),
            'box_on_target': (0, 255, 0)
        }
        
        # Fill with the appropriate color
        if element_name in colors:
            surface.fill(colors[element_name])
        else:
            surface.fill((128, 128, 128))  # Default gray
            
        return surface
        
    def _create_default_skin(self):
        """
        Create the default skin if it doesn't exist.
        """
        default_skin_dir = os.path.join(os.path.dirname(__file__), 'skins', 'default')
        if not os.path.exists(default_skin_dir):
            os.makedirs(default_skin_dir)
            
        # Create default images for each element
        elements = ['wall', 'floor', 'player', 'box', 'target', 'player_on_target', 'box_on_target']
        
        for element in elements:
            surface = self._create_default_element(element)
            image_path = os.path.join(default_skin_dir, f"{element}.png")
            pygame.image.save(surface, image_path)
            
    def get_skin(self, skin_name=None):
        """
        Get a specific skin or the current skin.
        
        Args:
            skin_name (str, optional): Name of the skin to get. Defaults to None (current skin).
            
        Returns:
            dict: Dictionary containing the skin's assets.
        """
        if skin_name is None:
            skin_name = self.current_skin
            
        if skin_name in self.skins:
            return self.skins[skin_name]
        else:
            return self.skins['default']
            
    def set_current_skin(self, skin_name):
        """
        Set the current skin.
        
        Args:
            skin_name (str): Name of the skin to set as current.
            
        Returns:
            bool: True if the skin was set successfully, False otherwise.
        """
        if skin_name in self.skins:
            self.current_skin = skin_name
            return True
        return False
        
    def get_available_skins(self):
        """
        Get a list of available skins.
        
        Returns:
            list: List of available skin names.
        """
        return list(self.skins.keys())
        
    def create_new_skin(self, skin_name):
        """
        Create a new skin based on the default skin.
        
        Args:
            skin_name (str): Name of the new skin.
            
        Returns:
            bool: True if the skin was created successfully, False otherwise.
        """
        if skin_name in self.skins:
            return False  # Skin already exists
            
        # Create new skin directory
        new_skin_dir = os.path.join(os.path.dirname(__file__), 'skins', skin_name)
        if not os.path.exists(new_skin_dir):
            os.makedirs(new_skin_dir)
            
        # Copy default skin images
        default_skin_dir = os.path.join(os.path.dirname(__file__), 'skins', 'default')
        for element in ['wall', 'floor', 'player', 'box', 'target', 'player_on_target', 'box_on_target']:
            default_image_path = os.path.join(default_skin_dir, f"{element}.png")
            new_image_path = os.path.join(new_skin_dir, f"{element}.png")
            
            try:
                if os.path.exists(default_image_path):
                    # Load and save the image to create a copy
                    image = pygame.image.load(default_image_path)
                    pygame.image.save(image, new_image_path)
                else:
                    # Create a default element if the default image doesn't exist
                    surface = self._create_default_element(element)
                    pygame.image.save(surface, new_image_path)
            except pygame.error:
                # Create a default element if loading fails
                surface = self._create_default_element(element)
                pygame.image.save(surface, new_image_path)
                
        # Load the new skin
        self.skins[skin_name] = self._load_skin(new_skin_dir)
        return True