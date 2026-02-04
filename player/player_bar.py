"""
Player Bar implementation for AJPanel-style player
"""

from Screens.Screen import Screen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ActionMap import ActionMap
from enigma import getDesktop, eTimer, ePoint, eSize
import os
import time

try:
    from ..constants import *
except ImportError:
    PLAYER_BAR_POSITION_BOTTOM = 0
    PLAYER_BAR_POSITION_TOP = 1

class PlayerBar(Screen):
    """AJPanel-style player bar"""
    
    def __init__(self, session, player_instance):
        Screen.__init__(self, session)
        self.player_instance = player_instance
        
        # Setup
        self.setup_dimensions()
        self.setup_skin()
        self.init_widgets()
        self.setup_actions()
        self.setup_timers()
        
        # Initial update
        self.update_timer.start(1000)
        self.update_display()
    
    def setup_dimensions(self):
        """Setup player bar dimensions"""
        desktop = getDesktop(0)
        self.screen_width = desktop.size().width()
        self.screen_height = desktop.size().height()
        
        # Load config
        self.bar_height = 80  # Default
        self.position = PLAYER_BAR_POSITION_BOTTOM
        self.auto_hide = True
        self.hide_timeout = 5
        
        try:
            if hasattr(config.plugins, 'wgfilemanager'):
                p = config.plugins.wgfilemanager
                if hasattr(p, 'player_bar_height'):
                    self.bar_height = int(p.player_bar_height.value)
                if hasattr(p, 'player_bar_position'):
                    self.position = int(p.player_bar_position.value)
                if hasattr(p, 'player_bar_auto_hide'):
                    self.auto_hide = p.player_bar_auto_hide.value
                if hasattr(p, 'player_bar_hide_timeout'):
                    self.hide_timeout = int(p.player_bar_hide_timeout.value)
        except:
            pass
    
    # ... rest of PlayerBar implementation from enigma_player.py ...