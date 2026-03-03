"""
Audio Manager for PySokoban

This module provides functionality for loading and playing audio files in the game.
"""

import os
import pygame
from typing import Dict, Optional

class AudioManager:
    """
    Manages audio loading and playback for the game.
    
    This class handles loading sound effects and music, and provides methods
    for playing them during gameplay.
    """
    
    def __init__(self, audio_dir: str = 'assets/audio'):
        """
        Initialize the audio manager.
        
        Args:
            audio_dir (str): Directory containing audio files
        """
        # Initialize pygame mixer if it hasn't been initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self.audio_dir = audio_dir
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_file: Optional[str] = None
        self.volume = 1.0
        self.music_volume = 0.5
        self.sound_enabled = True
        self.music_enabled = True
        
        # Load sounds
        self._load_sounds()
    
    def _load_sounds(self):
        """Load all sound files from the audio directory."""
        # Check if the audio directory exists
        if not os.path.exists(self.audio_dir):
            print(f"Warning: Audio directory '{self.audio_dir}' not found.")
            return
        
        # Load sound effects
        sound_dir = os.path.join(self.audio_dir, 'sounds')
        if os.path.exists(sound_dir):
            for filename in os.listdir(sound_dir):
                if filename.endswith(('.wav', '.ogg', '.mp3')):
                    name = os.path.splitext(filename)[0]
                    self.sounds[name] = pygame.mixer.Sound(os.path.join(sound_dir, filename))
        
        # Find music file
        music_dir = os.path.join(self.audio_dir, 'music')
        if os.path.exists(music_dir):
            for filename in os.listdir(music_dir):
                if filename.endswith(('.wav', '.ogg', '.mp3')):
                    self.music_file = os.path.join(music_dir, filename)
                    break
    
    def play_sound(self, name: str):
        """
        Play a sound effect.
        
        Args:
            name (str): Name of the sound to play
        """
        if not self.sound_enabled:
            return
        
        if name in self.sounds:
            self.sounds[name].set_volume(self.volume)
            self.sounds[name].play()
        else:
            print(f"Warning: Sound '{name}' not found.")
    
    def play_music(self, loop: bool = True):
        """
        Play background music.
        
        Args:
            loop (bool): Whether to loop the music
        """
        if not self.music_enabled or not self.music_file:
            return
        
        pygame.mixer.music.load(self.music_file)
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1 if loop else 0)
    
    def stop_music(self):
        """Stop the currently playing music."""
        pygame.mixer.music.stop()
    
    def pause_music(self):
        """Pause the currently playing music."""
        pygame.mixer.music.pause()
    
    def unpause_music(self):
        """Unpause the currently paused music."""
        pygame.mixer.music.unpause()
    
    def set_volume(self, volume: float):
        """
        Set the volume for sound effects.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
    
    def set_music_volume(self, volume: float):
        """
        Set the volume for music.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def toggle_sound(self):
        """Toggle sound effects on/off."""
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled
    
    def toggle_music(self):
        """Toggle music on/off."""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            self.unpause_music()
        else:
            self.pause_music()
        return self.music_enabled