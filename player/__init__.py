"""
WGFileManager Player Module with Subtitle Support
Complete player implementation for Enigma2
"""

# First, import the core player
from .enigma_player import (
    EnigmaPlayer,
    CustomMoviePlayer,
    WGFileManagerMediaPlayer,
    EnigmaMediaPlayer
)

# Import subtitle components
from .subtitle_manager import (
    SubtitleManager,
    SimpleSubtitleManager  # Alias for backward compatibility
)

from .subtitle_bridge import (
    SubtitleBridge,
    SubtitleLine
)

from .subtitle_factory import (
    get_subtitle_manager,
    SubtitleFactory
)

# Action map for key bindings
try:
    from .action_map import setup_player_actions, bind_actions_to_player
except ImportError:
    # Fallback if action_map doesn't exist yet
    def setup_player_actions(player):
        return {}
    
    def bind_actions_to_player(player, session):
        return False

__all__ = [
    # Player classes
    'EnigmaPlayer',
    'CustomMoviePlayer', 
    'WGFileManagerMediaPlayer',
    'EnigmaMediaPlayer',
    
    # Subtitle management
    'SubtitleManager',
    'SimpleSubtitleManager',
    'SubtitleBridge',
    'SubtitleLine',
    'get_subtitle_manager',
    'SubtitleFactory',
    
    # Action mapping
    'setup_player_actions',
    'bind_actions_to_player',
]

# Version info for player module
PLAYER_VERSION = "1.1.0"
PLAYER_FEATURES = [
    "Play/pause with subtitle sync",
    "Audio track selection",
    "Signal monitor",
    "Channel switching",
    "Subtitle toggle and menu",
    "Subtitle delay adjustment",
    "Multi-format subtitle support",
    "Auto-load subtitles",
]

def get_player_info():
    """Get information about the player module"""
    return {
        'version': PLAYER_VERSION,
        'features': PLAYER_FEATURES,
        'subtitle_formats': ['SRT', 'SUB', 'ASS/SSA', 'VTT'],
        'audio_formats': ['MP3', 'AAC', 'AC3', 'DTS', 'FLAC', 'WAV'],
        'video_formats': ['MP4', 'MKV', 'AVI', 'TS', 'M2TS', 'MOV'],
    }