"""
Level Manager module for the Sokoban game.

This module handles loading multiple levels, keeping track of the current level,
and managing navigation between levels. It also provides functionality for
generating random levels using the procedural generator.
"""

import os
from src.core.level import Level
from src.generation.procedural_generator import ProceduralGenerator
from src.level_management.level_collection_parser import LevelCollectionParser, LevelCollection


class LevelManager:
    """
    Class for managing multiple Sokoban levels.

    This class is responsible for loading level files, tracking the current level,
    and providing methods to navigate between levels.
    """

    def __init__(self, levels_dir='levels'):
        """
        Initialize the level manager.

        Args:
            levels_dir (str, optional): Directory containing level files.
                                       Defaults to 'levels'.
        """
        self.levels_dir = levels_dir
        self.level_files = []
        self.level_collections = {}  # Dict: filepath -> LevelCollection
        self.current_level_index = -1
        self.current_level = None
        self.current_level_metrics = None
        self.current_collection = None
        self.current_collection_index = -1

        self._load_level_files()

        if self.level_files:
            self.load_level(0)

    def _load_level_files(self):
        """
        Load all level files from the levels directory and subdirectories.
        Also parse level collections.
        """
        if not os.path.exists(self.levels_dir):
            print(f"Warning: Levels directory '{self.levels_dir}' not found.")
            return

        self.level_files = []
        self.level_collections = {}

        # Get all .txt files in the levels directory and subdirectories
        for root, dirs, files in os.walk(self.levels_dir):
            for file in files:
                if file.endswith('.txt'):
                    filepath = os.path.join(root, file)
                    self.level_files.append(filepath)

                    # Try to parse as a level collection
                    try:
                        collection = LevelCollectionParser.parse_file(filepath)
                        if collection.get_level_count() > 1:
                            self.level_collections[filepath] = collection
                            print(f"Loaded collection '{collection.title}' with {collection.get_level_count()} levels")
                    except Exception as e:
                        # If it fails, treat as a single level file
                        pass

        # Sort level files alphabetically
        self.level_files.sort()

    def load_level(self, level_index):
        """
        Load a specific level by index.

        Args:
            level_index (int): Index of the level to load.

        Returns:
            bool: True if the level was loaded successfully, False otherwise.
        """
        if not self.level_files:
            print("No level files found.")
            return False

        if level_index < 0 or level_index >= len(self.level_files):
            print(f"Level index {level_index} out of range (0-{len(self.level_files) - 1}).")
            return False

        try:
            filepath = self.level_files[level_index]

            # Check if this is a level collection
            if filepath in self.level_collections:
                collection = self.level_collections[filepath]
                if collection.get_level_count() > 0:
                    # Load the first level from the collection
                    level_title, level = collection.get_level(0)
                    level.title = level_title
                    level.description = collection.description
                    level.author = collection.author
                    self.current_level = level
                    self.current_collection = collection
                    self.current_collection_index = 0
                else:
                    return False
            else:
                # Load as a single level
                self.current_level = Level(level_file=filepath)
                self.current_collection = None
                self.current_collection_index = -1

            self.current_level_index = level_index
            self.current_level_metrics = None  # Reset metrics for loaded levels
            return True
        except Exception as e:
            print(f"Failed to load level {level_index}: {e}")
            return False

    def next_level(self):
        """
        Load the next level if available.

        Returns:
            bool: True if the next level was loaded successfully, False otherwise.
        """
        if self.current_level_index < len(self.level_files) - 1:
            return self.load_level(self.current_level_index + 1)

        print("Already at the last level.")
        return False

    def prev_level(self):
        """
        Load the previous level if available.

        Returns:
            bool: True if the previous level was loaded successfully, False otherwise.
        """
        if self.current_level_index > 0:
            return self.load_level(self.current_level_index - 1)

        print("Already at the first level.")
        return False

    def reset_current_level(self):
        """
        Reset the current level to its initial state.

        Returns:
            bool: True if the level was reset successfully, False otherwise.
        """
        if self.current_level:
            self.current_level.reset()
            # If reset doesn't work (e.g., no history), reload the level
            if self.current_level.moves != 0:
                return self.load_level(self.current_level_index)
            return True

        return False

    def current_level_completed(self):
        """
        Check if the current level is completed.

        Returns:
            bool: True if the current level is completed, False otherwise.
        """
        return self.current_level and self.current_level.is_completed()

    def has_next_level(self):
        """
        Check if there is a next level available.

        Returns:
            bool: True if there is a next level, False otherwise.
        """
        return self.current_level_index < len(self.level_files) - 1

    def has_prev_level(self):
        """
        Check if there is a previous level available.

        Returns:
            bool: True if there is a previous level, False otherwise.
        """
        return self.current_level_index > 0

    def get_level_count(self):
        """
        Get the total number of levels.

        Returns:
            int: The total number of levels.
        """
        return len(self.level_files)

    def get_current_level_number(self):
        """
        Get the current level number (1-based).

        Returns:
            int: The current level number (1-based).
        """
        return self.current_level_index + 1

    def create_custom_level(self, level_data, filename):
        """
        Create a custom level from string data and save it to a file.

        Args:
            level_data (str): Level data as a string.
            filename (str): Name of the file to save the level to.

        Returns:
            bool: True if the level was created successfully, False otherwise.
        """
        if not os.path.exists(self.levels_dir):
            os.makedirs(self.levels_dir)

        level_path = os.path.join(self.levels_dir, filename)

        try:
            with open(level_path, 'w') as file:
                file.write(level_data)

            # Reload level files
            self._load_level_files()

            # Find the index of the new level
            if level_path in self.level_files:
                new_level_index = self.level_files.index(level_path)
                return self.load_level(new_level_index)

            return False
        except Exception as e:
            print(f"Failed to create custom level: {e}")
            return False

    def generate_random_level(self, params=None, progress_callback=None):
        """
        Generate a random level and load it.

        Args:
            params (dict, optional): Parameters for the procedural generator.
                                    Defaults to None.
            progress_callback (callable, optional): A function to call with progress updates.
                                                  If None, a default console progress display is used.

        Returns:
            bool: True if the level was generated successfully, False otherwise.
        """
        try:
            # Ensure params is a dictionary
            if params is None:
                params = {}
            else:
                params = params.copy()  # Create a copy to avoid modifying the original

            # Set a reasonable timeout if not provided
            if 'timeout' not in params:
                params['timeout'] = 30.0  # 30 seconds timeout for level generation
            
            # Debug logging (can be commented out for production)
            # print(f"DEBUG: Level generation parameters: {params}")

            # Create a generator with the parameters
            generator = ProceduralGenerator(**params)

            # Define a default progress callback if none provided
            if progress_callback is None:
                def default_progress_callback(progress_info):
                    status = progress_info.get('status', 'unknown')
                    attempts = progress_info.get('attempts', 0)
                    elapsed = progress_info.get('elapsed_time', 0)
                    percent = progress_info.get('percent', 0)

                    # Create a progress bar
                    bar_length = 30
                    filled_length = int(bar_length * percent / 100)
                    bar = '█' * filled_length + '░' * (bar_length - filled_length)

                    if status == 'generating':
                        width = progress_info.get('width', 0)
                        height = progress_info.get('height', 0)
                        boxes = progress_info.get('boxes', 0)
                        print(f"\rGenerating level... [{bar}] {percent:.1f}% | Attempts: {attempts} | Time: {elapsed:.1f}s | Current: {width}x{height} with {boxes} boxes", end='')

                    elif status == 'success':
                        solution_length = progress_info.get('solution_length', 0)
                        width = progress_info.get('width', 0)
                        height = progress_info.get('height', 0)
                        boxes = progress_info.get('boxes', 0)
                        print(f"\rGeneration complete! [{bar}] 100% | Attempts: {attempts} | Time: {elapsed:.1f}s | Size: {width}x{height} | Boxes: {boxes} | Solution: {solution_length} moves")

                    elif status == 'timeout':
                        print(f"\rGeneration timed out! [{bar}] 100% | Attempts: {attempts} | Time: {elapsed:.1f}s | Could not find a solvable level")

                progress_callback = default_progress_callback

            # Generate a level with progress reporting
            level = generator.generate_level(progress_callback)

            # Set as current level
            self.current_level = level
            self.current_level_index = -1  # Indicate this is not from a file

            # Store metrics for UI access
            self.current_level_metrics = generator.level_metrics

            # Print additional information for console output
            if generator.level_metrics:
                print(f"Difficulty score: {generator.level_metrics['difficulty']['overall_score']:.1f}/100")

            return True
        except Exception as e:
            print(f"\nFailed to generate random level: {e}")
            return False

    def save_generated_level(self, filename):
        """
        Save the current generated level to a file.

        Args:
            filename (str): Name of the file to save the level to.

        Returns:
            bool: True if the level was saved successfully, False otherwise.
        """
        if self.current_level:
            return self.create_custom_level(
                self.current_level.get_state_string(),
                filename
            )
        return False

    def next_level_in_collection(self):
        """
        Load the next level in the current collection if available.

        Returns:
            bool: True if the next level was loaded successfully, False otherwise.
        """
        if not self.current_collection:
            return False

        if self.current_collection_index < self.current_collection.get_level_count() - 1:
            try:
                self.current_collection_index += 1
                level_title, level = self.current_collection.get_level(self.current_collection_index)
                level.title = level_title
                level.description = self.current_collection.description
                level.author = self.current_collection.author
                self.current_level = level
                return True
            except Exception as e:
                print(f"Failed to load next level in collection: {e}")
                return False

        print("Already at the last level in the collection.")
        return False

    def prev_level_in_collection(self):
        """
        Load the previous level in the current collection if available.

        Returns:
            bool: True if the previous level was loaded successfully, False otherwise.
        """
        if not self.current_collection:
            return False

        if self.current_collection_index > 0:
            try:
                self.current_collection_index -= 1
                level_title, level = self.current_collection.get_level(self.current_collection_index)
                level.title = level_title
                level.description = self.current_collection.description
                level.author = self.current_collection.author
                self.current_level = level
                return True
            except Exception as e:
                print(f"Failed to load previous level in collection: {e}")
                return False

        print("Already at the first level in the collection.")
        return False

    def has_next_level_in_collection(self):
        """
        Check if there is a next level in the current collection.

        Returns:
            bool: True if there is a next level in the collection, False otherwise.
        """
        if not self.current_collection:
            return False
        return self.current_collection_index < self.current_collection.get_level_count() - 1

    def has_prev_level_in_collection(self):
        """
        Check if there is a previous level in the current collection.

        Returns:
            bool: True if there is a previous level in the collection, False otherwise.
        """
        if not self.current_collection:
            return False
        return self.current_collection_index > 0

    def get_current_collection_info(self):
        """
        Get information about the current collection.

        Returns:
            dict: Dictionary with collection information or None if no collection.
        """
        if not self.current_collection:
            return None

        return {
            'title': self.current_collection.title,
            'description': self.current_collection.description,
            'author': self.current_collection.author,
            'level_count': self.current_collection.get_level_count(),
            'current_level_index': self.current_collection_index + 1,
            'current_level_title': self.current_level.title if self.current_level else ""
        }

    def get_level_metadata(self):
        """
        Get metadata for the current level.

        Returns:
            dict: Dictionary with level metadata.
        """
        if not self.current_level:
            return {}

        return {
            'title': getattr(self.current_level, 'title', ''),
            'description': getattr(self.current_level, 'description', ''),
            'author': getattr(self.current_level, 'author', ''),
            'moves': self.current_level.moves,
            'pushes': self.current_level.pushes
        }
