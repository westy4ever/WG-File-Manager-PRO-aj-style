from .dialogs import Dialogs
from .context_menu import ContextMenuHandler
from .setup_screen import WGFileManagerSetup
from .subtitle_menu import SubtitleMenuScreen
from .hotkey_setup import HotkeySetupScreen  # FIXED: HotkeySetupScreen not SubtitleHotkeySetupScreen

__all__ = [
    'Dialogs',
    'ContextMenuHandler',
    'WGFileManagerSetup',
    'SubtitleMenuScreen',
    'HotkeySetupScreen'  # FIXED: HotkeySetupScreen not SubtitleHotkeySetupScreen
]