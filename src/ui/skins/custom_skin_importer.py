"""
Custom Skin Importer for the Sokoban game.

This module provides functionality to import custom skins from PNG files:
- File selection for each sprite type
- Validation of image dimensions
- Background image support
- Automatic skin folder creation
"""

import os
import shutil
import pygame
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image
from src.core.constants import WALL, FLOOR, PLAYER, BOX, TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET

class CustomSkinImporter:
    """
    Class for importing custom skins from PNG files.
    """
    
    def __init__(self, skins_directory='skins', screen=None):
        """
        Initialize the custom skin importer.
        
        Args:
            skins_directory (str): Directory where skins are stored.
            screen: Pygame screen for displaying progress.
        """
        self.skins_directory = skins_directory
        self.screen = screen
        
        # Required sprite files mapping
        self.required_sprites = {
            'wall': {'key': WALL, 'filename': 'wall.png', 'description': 'Wall sprite'},
            'floor': {'key': FLOOR, 'filename': 'floor.png', 'description': 'Floor sprite'},
            'player': {'key': PLAYER, 'filename': 'player.png', 'description': 'Player sprite'},
            'box': {'key': BOX, 'filename': 'box.png', 'description': 'Box sprite'},
            'target': {'key': TARGET, 'filename': 'target.png', 'description': 'Target sprite'},
            'player_on_target': {'key': PLAYER_ON_TARGET, 'filename': 'player_on_target.png', 'description': 'Player on target sprite'},
            'box_on_target': {'key': BOX_ON_TARGET, 'filename': 'box_on_target.png', 'description': 'Box on target sprite'}
        }
        
        # Optional directional sprites
        self.optional_sprites = {
            'player_up': {'filename': 'player_up.png', 'description': 'Player facing up'},
            'player_down': {'filename': 'player_down.png', 'description': 'Player facing down'},
            'player_left': {'filename': 'player_left.png', 'description': 'Player facing left'},
            'player_right': {'filename': 'player_right.png', 'description': 'Player facing right'},
            'player_push_up': {'filename': 'player_push_up.png', 'description': 'Player pushing up'},
            'player_push_down': {'filename': 'player_push_down.png', 'description': 'Player pushing down'},
            'player_push_left': {'filename': 'player_push_left.png', 'description': 'Player pushing left'},
            'player_push_right': {'filename': 'player_push_right.png', 'description': 'Player pushing right'},
            'player_blocked': {'filename': 'player_blocked.png', 'description': 'Player blocked'},
        }
        
        # Background sprite (optional)
        self.background_sprite = {
            'background': {'filename': 'background.png', 'description': 'Background image (optional)'}
        }
        
    def import_skin(self, tile_size):
        """
        Start the skin import process.
        
        Args:
            tile_size (int): Expected tile size for validation.
            
        Returns:
            str: Name of the imported skin or None if cancelled.
        """
        try:
            # Hide pygame window temporarily
            if self.screen:
                pygame.display.iconify()
            
            # Initialize tkinter
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Get skin name
            skin_name = simpledialog.askstring(
                "Skin Name", 
                "Enter a name for your custom skin:",
                initialvalue="my_custom_skin"
            )
            
            if not skin_name:
                return None
                
            # Validate skin name
            skin_name = self._sanitize_filename(skin_name)
            
            # Check if skin already exists
            skin_path = os.path.join(self.skins_directory, skin_name)
            if os.path.exists(skin_path):
                if not messagebox.askyesno("Skin Exists", f"Skin '{skin_name}' already exists. Overwrite?"):
                    return None
                shutil.rmtree(skin_path)
            
            # Create skin directory
            os.makedirs(skin_path, exist_ok=True)
            
            # Import required sprites
            imported_files = {}
            
            messagebox.showinfo("Import Process", 
                              f"You will now select PNG files for each sprite.\n"
                              f"Expected tile size: {tile_size}x{tile_size} pixels\n\n"
                              f"First, select the required sprites.")
            
            # Import required sprites
            for sprite_name, sprite_info in self.required_sprites.items():
                file_path = self._select_sprite_file(sprite_name, sprite_info['description'], tile_size)
                if not file_path:
                    messagebox.showerror("Import Cancelled", f"Import cancelled. {sprite_info['description']} is required.")
                    if os.path.exists(skin_path):
                        shutil.rmtree(skin_path)
                    return None
                
                # Copy and validate file
                target_path = os.path.join(skin_path, sprite_info['filename'])
                if self._copy_and_validate_sprite(file_path, target_path, tile_size):
                    imported_files[sprite_name] = target_path
                else:
                    if os.path.exists(skin_path):
                        shutil.rmtree(skin_path)
                    return None
            
            # Ask for optional sprites
            if messagebox.askyesno("Optional Sprites", 
                                 "Would you like to add optional directional player sprites?\n"
                                 "These provide better visual feedback for player movement."):
                self._import_optional_sprites(skin_path, tile_size)
            
            # Ask for background
            if messagebox.askyesno("Background Image", 
                                 "Would you like to add a background image?\n"
                                 "This will be displayed behind the game."):
                self._import_background(skin_path)
            
            messagebox.showinfo("Import Complete", 
                              f"Skin '{skin_name}' has been imported successfully!\n"
                              f"Location: {skin_path}")
            
            return skin_name
            
        except Exception as e:
            messagebox.showerror("Import Error", f"An error occurred during import: {str(e)}")
            return None
        finally:
            # Restore pygame window
            if self.screen:
                pygame.display.iconify()  # This should restore the window
            try:
                root.destroy()
            except:
                pass
    
    def _select_sprite_file(self, sprite_name, description, tile_size):
        """
        Select a sprite file using file dialog.
        
        Args:
            sprite_name (str): Name of the sprite.
            description (str): Description to show in dialog.
            tile_size (int): Expected tile size.
            
        Returns:
            str: Selected file path or None.
        """
        return filedialog.askopenfilename(
            title=f"Select {description} (should be {tile_size}x{tile_size})",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
    
    def _copy_and_validate_sprite(self, source_path, target_path, expected_size):
        """
        Copy and validate a sprite file.
        
        Args:
            source_path (str): Source file path.
            target_path (str): Target file path.
            expected_size (int): Expected sprite size.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Open and validate image
            with Image.open(source_path) as img:
                width, height = img.size
                
                # Check if image is square
                if width != height:
                    if messagebox.askyesno("Non-square Image", 
                                         f"Image is {width}x{height}, but sprites should be square.\n"
                                         f"Resize to {expected_size}x{expected_size}?"):
                        img = img.resize((expected_size, expected_size), Image.Resampling.LANCZOS)
                    else:
                        return False
                
                # Check if size matches expected
                elif width != expected_size:
                    if messagebox.askyesno("Size Mismatch", 
                                         f"Image is {width}x{height}, but expected {expected_size}x{expected_size}.\n"
                                         f"Resize to match tile size?"):
                        img = img.resize((expected_size, expected_size), Image.Resampling.LANCZOS)
                    else:
                        return False
                
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Save the processed image
                img.save(target_path, 'PNG')
                
            return True
            
        except Exception as e:
            messagebox.showerror("File Error", f"Error processing {source_path}: {str(e)}")
            return False
    
    def _import_optional_sprites(self, skin_path, tile_size):
        """
        Import optional directional sprites.
        
        Args:
            skin_path (str): Path to the skin directory.
            tile_size (int): Expected tile size.
        """
        for sprite_name, sprite_info in self.optional_sprites.items():
            if messagebox.askyesno("Optional Sprite", 
                                 f"Add {sprite_info['description']}?"):
                file_path = self._select_sprite_file(sprite_name, sprite_info['description'], tile_size)
                if file_path:
                    target_path = os.path.join(skin_path, sprite_info['filename'])
                    self._copy_and_validate_sprite(file_path, target_path, tile_size)
    
    def _import_background(self, skin_path):
        """
        Import background image.
        
        Args:
            skin_path (str): Path to the skin directory.
        """
        file_path = filedialog.askopenfilename(
            title="Select Background Image (any size)",
            filetypes=[("PNG files", "*.png"), ("JPG files", "*.jpg"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            target_path = os.path.join(skin_path, 'background.png')
            try:
                with Image.open(file_path) as img:
                    # Convert to RGBA and save as PNG
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(target_path, 'PNG')
            except Exception as e:
                messagebox.showerror("Background Error", f"Error processing background: {str(e)}")
    
    def _sanitize_filename(self, filename):
        """
        Sanitize filename to be safe for file system.
        
        Args:
            filename (str): Original filename.
            
        Returns:
            str: Sanitized filename.
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 50:
            filename = filename[:50]
        
        # Ensure it's not empty
        if not filename:
            filename = "custom_skin"
            
        return filename

    def import_single_sprite(self, sprite_type, tile_size, skin_name=None):
        """
        Import a single sprite file for quick customization.
        
        Args:
            sprite_type (str): Type of sprite to import.
            tile_size (int): Expected tile size.
            skin_name (str): Optional skin name, will create temp skin if not provided.
            
        Returns:
            str: Path to imported sprite or None.
        """
        try:
            # Initialize tkinter
            root = tk.Tk()
            root.withdraw()
            
            # Select file
            sprite_info = self.required_sprites.get(sprite_type, self.optional_sprites.get(sprite_type))
            if not sprite_info:
                return None
                
            file_path = self._select_sprite_file(sprite_type, sprite_info['description'], tile_size)
            if not file_path:
                return None
            
            # Create temporary skin if needed
            if not skin_name:
                skin_name = "temp_custom"
            
            skin_path = os.path.join(self.skins_directory, skin_name)
            os.makedirs(skin_path, exist_ok=True)
            
            # Copy sprite
            target_path = os.path.join(skin_path, sprite_info['filename'])
            if self._copy_and_validate_sprite(file_path, target_path, tile_size):
                return target_path
            
            return None
            
        except Exception as e:
            if messagebox:
                messagebox.showerror("Import Error", f"Error importing sprite: {str(e)}")
            return None
        finally:
            try:
                root.destroy()
            except:
                pass