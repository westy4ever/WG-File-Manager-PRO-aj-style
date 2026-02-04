"""
WG File Manager PRO - Professional File Manager for Enigma2
Main package initialization with subtitle support
"""

__version__ = "1.1.0"
__author__ = "WG Development Team"
__description__ = "Professional File Manager with Subtitle Support"

# Export main components
try:
    from .player.enigma_player import EnigmaPlayer
    from .player.subtitle_manager import SubtitleManager
    from .player.subtitle_factory import get_subtitle_manager
    from .ui.main_screen import WGFileManagerMain
    from .ui.subtitle_menu import SubtitleMenuScreen
    
    __all__ = [
        'EnigmaPlayer',
        'SubtitleManager', 
        'get_subtitle_manager',
        'WGFileManagerMain',
        'SubtitleMenuScreen',
    ]
    
except ImportError as e:
    # Graceful fallback for partial imports
    import sys
    import logging
    
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)
    logger.warning(f"Some imports failed during package init: {e}")
    
    __all__ = []

# Package metadata
PACKAGE_INFO = {
    'name': 'WGFileManager',
    'version': __version__,
    'description': __description__,
    'features': [
        'Dual pane file manager',
        'Media player with subtitle support',
        'Multi-format subtitle handling (SRT, SUB, ASS, VTT)',
        'Network access (FTP, SFTP, WebDAV, SMB)',
        'Archive support (ZIP, TAR, RAR)',
        'Hotkey configuration',
        'Auto-load subtitles',
        'Subtitle delay adjustment',
    ],
    'author': __author__,
    'license': 'GPLv2',
}

def get_package_info():
    """Get package information"""
    return PACKAGE_INFO

def check_subtitle_support():
    """Check if subtitle features are available"""
    try:
        from .player.subtitle_manager import SubtitleManager
        from .player.subtitle_bridge import SubtitleBridge
        return True, "Full subtitle support available"
    except ImportError as e:
        return False, f"Subtitle support limited: {e}"