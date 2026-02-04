"""
Add these classes to your existing ui/setup_screen.py file
"""

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigInteger, ConfigText
from enigma import getDesktop

# ============================================================================
# PLAYER SETTINGS SCREEN
# ============================================================================

class PlayerSettings(ConfigListScreen, Screen):
    """Player settings screen"""
    
    def __init__(self, session, player=None):
        Screen.__init__(self, session)
        self.player = player
        
        # Get screen dimensions
        desktop = getDesktop(0)
        width = desktop.size().width()
        height = desktop.size().height()
        
        # Setup skin
        self.skin = f"""
        <screen position="center,center" size="{min(width, 600)},{min(height, 400)}" title="Player Settings">
            <widget name="config" position="10,10" size="{min(width, 600)-20},{min(height, 400)-100}" />
            <widget name="red" position="10,{min(height, 400)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#9f1313" />
            <widget name="green" position="140,{min(height, 400)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#1f771f" />
        </screen>"""
        
        # Initialize config list
        self.setupConfigList()
        
        # Setup widgets
        self["red"] = Label("Cancel")
        self["green"] = Label("Save")
        
        # Setup actions
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.close,
                "save": self.save,
                "red": self.close,
                "green": self.save,
            })
    
    def setupConfigList(self):
        """Setup configuration list for player settings"""
        # Ensure config exists
        if not hasattr(config.plugins, 'wgfilemanager'):
            config.plugins.wgfilemanager = ConfigSubsection()
        
        p = config.plugins.wgfilemanager
        
        # Player bar settings
        if not hasattr(p, 'player_bar_position'):
            p.player_bar_position = ConfigSelection(default="0", choices=[
                ("0", "Bottom"),
                ("1", "Top"),
                ("2", "Left"),
                ("3", "Right"),
            ])
        
        if not hasattr(p, 'player_bar_auto_hide'):
            p.player_bar_auto_hide = ConfigYesNo(default=True)
        
        if not hasattr(p, 'player_bar_hide_timeout'):
            p.player_bar_hide_timeout = ConfigSelection(default="5", choices=[
                ("0", "Never"),
                ("3", "3 seconds"),
                ("5", "5 seconds"),
                ("10", "10 seconds"),
                ("15", "15 seconds"),
            ])
        
        if not hasattr(p, 'player_bar_height'):
            p.player_bar_height = ConfigSelection(default="80", choices=[
                ("60", "Small (60px)"),
                ("80", "Medium (80px)"),
                ("100", "Large (100px)"),
                ("120", "Extra Large (120px)"),
            ])
        
        # Playback settings
        if not hasattr(p, 'player_seek_interval'):
            p.player_seek_interval = ConfigSelection(default="30", choices=[
                ("10", "10 seconds"),
                ("30", "30 seconds"),
                ("60", "1 minute"),
                ("300", "5 minutes"),
                ("600", "10 minutes"),
            ])
        
        if not hasattr(p, 'player_auto_resume'):
            p.player_auto_resume = ConfigYesNo(default=True)
        
        if not hasattr(p, 'player_resume_threshold'):
            p.player_resume_threshold = ConfigInteger(default=10, limits=(1, 300))
        
        # Hotkey settings
        if not hasattr(p, 'player_hotkey_profile'):
            p.player_hotkey_profile = ConfigSelection(default="default", choices=[
                ("default", "Default"),
                ("simple", "Simple"),
                ("advanced", "Advanced"),
                ("custom", "Custom"),
            ])
        
        # Create config list
        self.list = [
            getConfigListEntry("Player Bar Position", p.player_bar_position),
            getConfigListEntry("Auto Hide Player Bar", p.player_bar_auto_hide),
            getConfigListEntry("Hide Timeout", p.player_bar_hide_timeout),
            getConfigListEntry("Player Bar Height", p.player_bar_height),
            getConfigListEntry("Seek Interval (seconds)", p.player_seek_interval),
            getConfigListEntry("Auto Resume Playback", p.player_auto_resume),
            getConfigListEntry("Resume Threshold (seconds)", p.player_resume_threshold),
            getConfigListEntry("Hotkey Profile", p.player_hotkey_profile),
        ]
        
        ConfigListScreen.__init__(self, self.list)
    
    def save(self):
        """Save player settings"""
        try:
            # Save config
            from Components.config import configfile
            configfile.save()
            
            # Apply settings to current player if available
            if self.player:
                self.apply_to_player()
            
            self.session.open(
                MessageBox,
                "✅ Player settings saved!",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            self.close()
        except Exception as e:
            self.session.open(
                MessageBox,
                f"❌ Error saving settings: {str(e)[:50]}",
                MessageBox.TYPE_ERROR,
                timeout=3
            )
    
    def apply_to_player(self):
        """Apply settings to player instance"""
        try:
            p = config.plugins.wgfilemanager
            
            # Apply player bar settings
            if hasattr(self.player, 'player_bar'):
                # Position
                position = int(p.player_bar_position.value)
                if hasattr(self.player.player_bar, 'bar_position'):
                    self.player.player_bar.bar_position = position
                
                # Auto-hide
                auto_hide = p.player_bar_auto_hide.value
                if hasattr(self.player.player_bar, 'auto_hide'):
                    self.player.player_bar.auto_hide = auto_hide
                
                # Timeout
                timeout = int(p.player_bar_hide_timeout.value)
                if hasattr(self.player.player_bar, 'timeout'):
                    self.player.player_bar.timeout = timeout
            
            # Apply seek interval
            if hasattr(self.player, 'seek_minutes'):
                seek_seconds = int(p.player_seek_interval.value)
                self.player.seek_minutes = seek_seconds / 60
            
            logger.info("Player settings applied")
        except Exception as e:
            logger.error(f"Error applying player settings: {e}")


# ============================================================================
# PLAYER BAR SETTINGS SCREEN
# ============================================================================

class PlayerBarSettings(ConfigListScreen, Screen):
    """Player bar specific settings"""
    
    def __init__(self, session):
        Screen.__init__(self, session)
        
        # Get screen dimensions
        desktop = getDesktop(0)
        width = desktop.size().width()
        height = desktop.size().height()
        
        # Setup skin
        self.skin = f"""
        <screen position="center,center" size="{min(width, 500)},{min(height, 350)}" title="Player Bar Settings">
            <widget name="config" position="10,10" size="{min(width, 500)-20},{min(height, 350)-100}" />
            <widget name="red" position="10,{min(height, 350)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#9f1313" />
            <widget name="green" position="140,{min(height, 350)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#1f771f" />
        </screen>"""
        
        # Initialize config list
        self.setupConfigList()
        
        # Setup widgets
        self["red"] = Label("Cancel")
        self["green"] = Label("Save")
        
        # Setup actions
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.close,
                "save": self.save,
                "red": self.close,
                "green": self.save,
            })
    
    def setupConfigList(self):
        """Setup configuration list for player bar"""
        # Ensure config exists
        if not hasattr(config.plugins, 'wgfilemanager'):
            config.plugins.wgfilemanager = ConfigSubsection()
        
        p = config.plugins.wgfilemanager
        
        # Player bar appearance
        if not hasattr(p, 'player_bar_color_mode'):
            p.player_bar_color_mode = ConfigSelection(default="auto", choices=[
                ("auto", "Auto (Based on content)"),
                ("dark", "Dark Theme"),
                ("light", "Light Theme"),
                ("custom", "Custom Color"),
            ])
        
        if not hasattr(p, 'player_bar_opacity'):
            p.player_bar_opacity = ConfigSelection(default="90", choices=[
                ("100", "100% (Solid)"),
                ("90", "90%"),
                ("80", "80%"),
                ("70", "70%"),
                ("60", "60%"),
            ])
        
        if not hasattr(p, 'player_bar_show_progress'):
            p.player_bar_show_progress = ConfigYesNo(default=True)
        
        if not hasattr(p, 'player_bar_show_time'):
            p.player_bar_show_time = ConfigYesNo(default=True)
        
        if not hasattr(p, 'player_bar_show_icons'):
            p.player_bar_show_icons = ConfigYesNo(default=True)
        
        if not hasattr(p, 'player_bar_show_filename'):
            p.player_bar_show_filename = ConfigYesNo(default=True)
        
        # Player bar behavior
        if not hasattr(p, 'player_bar_show_on_play'):
            p.player_bar_show_on_play = ConfigYesNo(default=True)
        
        if not hasattr(p, 'player_bar_hide_on_pause'):
            p.player_bar_hide_on_pause = ConfigYesNo(default=False)
        
        if not hasattr(p, 'player_bar_show_hotkeys'):
            p.player_bar_show_hotkeys = ConfigYesNo(default=True)
        
        # Create config list
        self.list = [
            getConfigListEntry("Color Theme", p.player_bar_color_mode),
            getConfigListEntry("Opacity", p.player_bar_opacity),
            getConfigListEntry("Show Progress Bar", p.player_bar_show_progress),
            getConfigListEntry("Show Time Info", p.player_bar_show_time),
            getConfigListEntry("Show Icons", p.player_bar_show_icons),
            getConfigListEntry("Show Filename", p.player_bar_show_filename),
            getConfigListEntry("Show on Play", p.player_bar_show_on_play),
            getConfigListEntry("Hide on Pause", p.player_bar_hide_on_pause),
            getConfigListEntry("Show Hotkey Help", p.player_bar_show_hotkeys),
        ]
        
        ConfigListScreen.__init__(self, self.list)
    
    def save(self):
        """Save player bar settings"""
        try:
            from Components.config import configfile
            configfile.save()
            
            self.session.open(
                MessageBox,
                "✅ Player bar settings saved!",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            self.close()
        except Exception as e:
            self.session.open(
                MessageBox,
                f"❌ Error saving: {str(e)[:50]}",
                MessageBox.TYPE_ERROR,
                timeout=3
            )


# ============================================================================
# SUBTITLE SETTINGS SCREEN
# ============================================================================

class SubtitleSettings(ConfigListScreen, Screen):
    """Subtitle settings screen"""
    
    def __init__(self, session):
        Screen.__init__(self, session)
        
        # Get screen dimensions
        desktop = getDesktop(0)
        width = desktop.size().width()
        height = desktop.size().height()
        
        # Setup skin
        self.skin = f"""
        <screen position="center,center" size="{min(width, 600)},{min(height, 450)}" title="Subtitle Settings">
            <widget name="config" position="10,10" size="{min(width, 600)-20},{min(height, 450)-100}" />
            <widget name="red" position="10,{min(height, 450)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#9f1313" />
            <widget name="green" position="140,{min(height, 450)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#1f771f" />
        </screen>"""
        
        # Initialize config list
        self.setupConfigList()
        
        # Setup widgets
        self["red"] = Label("Cancel")
        self["green"] = Label("Save")
        
        # Setup actions
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.close,
                "save": self.save,
                "red": self.close,
                "green": self.save,
            })
    
    def setupConfigList(self):
        """Setup configuration list for subtitle settings"""
        # Ensure config exists
        if not hasattr(config.plugins, 'wgfilemanager'):
            config.plugins.wgfilemanager = ConfigSubsection()
        
        p = config.plugins.wgfilemanager
        
        # Subtitle appearance
        if not hasattr(p, 'subtitle_font_size'):
            p.subtitle_font_size = ConfigSelection(default="medium", choices=[
                ("small", "Small (20)"),
                ("medium", "Medium (24)"),
                ("large", "Large (28)"),
                ("xlarge", "Extra Large (32)"),
                ("xxlarge", "Huge (36)"),
            ])
        
        if not hasattr(p, 'subtitle_font_color'):
            p.subtitle_font_color = ConfigSelection(default="white", choices=[
                ("white", "White"),
                ("yellow", "Yellow"),
                ("cyan", "Cyan"),
                ("green", "Green"),
                ("red", "Red"),
                ("blue", "Blue"),
                ("magenta", "Magenta"),
                ("orange", "Orange"),
            ])
        
        if not hasattr(p, 'subtitle_bg_enabled'):
            p.subtitle_bg_enabled = ConfigYesNo(default=True)
        
        if not hasattr(p, 'subtitle_bg_color'):
            p.subtitle_bg_color = ConfigSelection(default="black", choices=[
                ("black", "Black"),
                ("dark_gray", "Dark Gray"),
                ("gray", "Gray"),
                ("blue", "Blue"),
                ("red", "Red"),
                ("green", "Green"),
                ("transparent", "Transparent"),
            ])
        
        if not hasattr(p, 'subtitle_bg_opacity'):
            p.subtitle_bg_opacity = ConfigSelection(default="80", choices=[
                ("100", "100% (Solid)"),
                ("80", "80%"),
                ("60", "60%"),
                ("40", "40%"),
                ("20", "20%"),
                ("0", "0% (Transparent)"),
            ])
        
        if not hasattr(p, 'subtitle_position'):
            p.subtitle_position = ConfigSelection(default="bottom", choices=[
                ("top", "Top"),
                ("center_top", "Center Top"),
                ("center", "Center"),
                ("center_bottom", "Center Bottom"),
                ("bottom", "Bottom"),
            ])
        
        # Subtitle behavior
        if not hasattr(p, 'subtitle_auto_load'):
            p.subtitle_auto_load = ConfigYesNo(default=True)
        
        if not hasattr(p, 'subtitle_auto_download'):
            p.subtitle_auto_download = ConfigYesNo(default=False)
        
        if not hasattr(p, 'subtitle_encoding'):
            p.subtitle_encoding = ConfigSelection(default="utf-8", choices=[
                ("utf-8", "UTF-8"),
                ("latin1", "Latin-1"),
                ("cp1256", "Arabic (CP1256)"),
                ("cp1252", "Western (CP1252)"),
                ("utf-16", "UTF-16"),
                ("gbk", "Chinese GBK"),
            ])
        
        if not hasattr(p, 'subtitle_delay'):
            p.subtitle_delay = ConfigInteger(default=0, limits=(-3600, 3600))
        
        # Advanced subtitle settings
        if not hasattr(p, 'subtitle_outline'):
            p.subtitle_outline = ConfigYesNo(default=True)
        
        if not hasattr(p, 'subtitle_shadow'):
            p.subtitle_shadow = ConfigYesNo(default=True)
        
        if not hasattr(p, 'subtitle_bold'):
            p.subtitle_bold = ConfigYesNo(default=False)
        
        if not hasattr(p, 'subtitle_italic'):
            p.subtitle_italic = ConfigYesNo(default=False)
        
        # Create config list
        self.list = [
            getConfigListEntry("Font Size", p.subtitle_font_size),
            getConfigListEntry("Font Color", p.subtitle_font_color),
            getConfigListEntry("Background", p.subtitle_bg_enabled),
            getConfigListEntry("Background Color", p.subtitle_bg_color),
            getConfigListEntry("Background Opacity", p.subtitle_bg_opacity),
            getConfigListEntry("Position", p.subtitle_position),
            getConfigListEntry("Auto Load Subtitles", p.subtitle_auto_load),
            getConfigListEntry("Auto Download", p.subtitle_auto_download),
            getConfigListEntry("Default Encoding", p.subtitle_encoding),
            getConfigListEntry("Default Delay (seconds)", p.subtitle_delay),
            getConfigListEntry("Text Outline", p.subtitle_outline),
            getConfigListEntry("Text Shadow", p.subtitle_shadow),
            getConfigListEntry("Bold Text", p.subtitle_bold),
            getConfigListEntry("Italic Text", p.subtitle_italic),
        ]
        
        ConfigListScreen.__init__(self, self.list)
    
    def save(self):
        """Save subtitle settings"""
        try:
            from Components.config import configfile
            configfile.save()
            
            self.session.open(
                MessageBox,
                "✅ Subtitle settings saved!",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            self.close()
        except Exception as e:
            self.session.open(
                MessageBox,
                f"❌ Error saving: {str(e)[:50]}",
                MessageBox.TYPE_ERROR,
                timeout=3
            )


# ============================================================================
# HOTKEY SETTINGS SCREEN
# ============================================================================

class HotkeySettings(ConfigListScreen, Screen):
    """Hotkey settings screen"""
    
    def __init__(self, session):
        Screen.__init__(self, session)
        
        # Get screen dimensions
        desktop = getDesktop(0)
        width = desktop.size().width()
        height = desktop.size().height()
        
        # Setup skin
        self.skin = f"""
        <screen position="center,center" size="{min(width, 700)},{min(height, 500)}" title="Hotkey Settings">
            <widget name="config" position="10,10" size="{min(width, 700)-20},{min(height, 500)-100}" />
            <widget name="red" position="10,{min(height, 500)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#9f1313" />
            <widget name="green" position="140,{min(height, 500)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#1f771f" />
            <widget name="yellow" position="270,{min(height, 500)-40}" size="120,30" font="Regular;20" halign="center" backgroundColor="#a08500" />
        </screen>"""
        
        # Initialize config list
        self.setupConfigList()
        
        # Setup widgets
        self["red"] = Label("Cancel")
        self["green"] = Label("Save")
        self["yellow"] = Label("Reset")
        
        # Setup actions
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.close,
                "save": self.save,
                "red": self.close,
                "green": self.save,
                "yellow": self.reset_defaults,
            })
    
    def setupConfigList(self):
        """Setup configuration list for hotkey settings"""
        # Ensure config exists
        if not hasattr(config.plugins, 'wgfilemanager'):
            config.plugins.wgfilemanager = ConfigSubsection()
        
        p = config.plugins.wgfilemanager
        
        # Hotkey profiles
        if not hasattr(p, 'hotkey_profile'):
            p.hotkey_profile = ConfigSelection(default="default", choices=[
                ("default", "Default"),
                ("simple", "Simple"),
                ("advanced", "Advanced"),
                ("expert", "Expert"),
                ("custom", "Custom"),
            ])
        
        # Player hotkeys
        if not hasattr(p, 'hotkey_play_pause'):
            p.hotkey_play_pause = ConfigSelection(default="play", choices=[
                ("play", "PLAY Button"),
                ("ok", "OK Button"),
                ("pause", "PAUSE Button"),
            ])
        
        if not hasattr(p, 'hotkey_stop'):
            p.hotkey_stop = ConfigSelection(default="stop", choices=[
                ("stop", "STOP Button"),
                ("exit", "EXIT Button"),
                ("cancel", "CANCEL Button"),
            ])
        
        if not hasattr(p, 'hotkey_subtitle_toggle'):
            p.hotkey_subtitle_toggle = ConfigSelection(default="subtitle", choices=[
                ("subtitle", "SUBTITLE Button"),
                ("text", "TEXT Button"),
                ("yellow", "YELLOW Button"),
            ])
        
        if not hasattr(p, 'hotkey_subtitle_menu'):
            p.hotkey_subtitle_menu = ConfigSelection(default="long_subtitle", choices=[
                ("long_subtitle", "Long SUBTITLE"),
                ("green", "GREEN Button"),
                ("menu", "MENU Button"),
            ])
        
        if not hasattr(p, 'hotkey_player_bar'):
            p.hotkey_player_bar = ConfigSelection(default="ok", choices=[
                ("ok", "OK Button"),
                ("info", "INFO Button"),
                ("epg", "EPG Button"),
            ])
        
        # Seek hotkeys
        if not hasattr(p, 'hotkey_seek_forward'):
            p.hotkey_seek_forward = ConfigSelection(default="right", choices=[
                ("right", "RIGHT Arrow"),
                ("fastforward", "FASTFORWARD"),
                ("next", "NEXT Button"),
            ])
        
        if not hasattr(p, 'hotkey_seek_backward'):
            p.hotkey_seek_backward = ConfigSelection(default="left", choices=[
                ("left", "LEFT Arrow"),
                ("rewind", "REWIND"),
                ("previous", "PREVIOUS Button"),
            ])
        
        # Color button assignments
        if not hasattr(p, 'hotkey_red_button'):
            p.hotkey_red_button = ConfigSelection(default="signal", choices=[
                ("signal", "Signal Monitor"),
                ("bookmark", "Add Bookmark"),
                ("screenshot", "Take Screenshot"),
                ("repeat", "Repeat Mode"),
            ])
        
        if not hasattr(p, 'hotkey_green_button'):
            p.hotkey_green_button = ConfigSelection(default="subtitle_settings", choices=[
                ("subtitle_settings", "Subtitle Settings"),
                ("audio", "Audio Menu"),
                ("aspect", "Aspect Ratio"),
                ("zoom", "Zoom Mode"),
            ])
        
        if not hasattr(p, 'hotkey_yellow_button'):
            p.hotkey_yellow_button = ConfigSelection(default="toggle_subtitle", choices=[
                ("toggle_subtitle", "Toggle Subtitle"),
                ("download", "Download Subtitle"),
                ("search", "Search Subtitles"),
                ("convert", "Convert Format"),
            ])
        
        if not hasattr(p, 'hotkey_blue_button'):
            p.hotkey_blue_button = ConfigSelection(default="jump_menu", choices=[
                ("jump_menu", "Jump Menu"),
                ("chapters", "Chapters"),
                ("favorites", "Favorites"),
                ("playlist", "Playlist"),
            ])
        
        # Long press settings
        if not hasattr(p, 'hotkey_long_press_delay'):
            p.hotkey_long_press_delay = ConfigSelection(default="500", choices=[
                ("300", "300 ms"),
                ("500", "500 ms"),
                ("700", "700 ms"),
                ("1000", "1 second"),
            ])
        
        # Create config list
        self.list = [
            getConfigListEntry("Hotkey Profile", p.hotkey_profile),
            getConfigListEntry("Play/Pause", p.hotkey_play_pause),
            getConfigListEntry("Stop", p.hotkey_stop),
            getConfigListEntry("Toggle Subtitle", p.hotkey_subtitle_toggle),
            getConfigListEntry("Subtitle Menu", p.hotkey_subtitle_menu),
            getConfigListEntry("Player Bar", p.hotkey_player_bar),
            getConfigListEntry("Seek Forward", p.hotkey_seek_forward),
            getConfigListEntry("Seek Backward", p.hotkey_seek_backward),
            getConfigListEntry("RED Button", p.hotkey_red_button),
            getConfigListEntry("GREEN Button", p.hotkey_green_button),
            getConfigListEntry("YELLOW Button", p.hotkey_yellow_button),
            getConfigListEntry("BLUE Button", p.hotkey_blue_button),
            getConfigListEntry("Long Press Delay", p.hotkey_long_press_delay),
        ]
        
        ConfigListScreen.__init__(self, self.list)
    
    def save(self):
        """Save hotkey settings"""
        try:
            from Components.config import configfile
            configfile.save()
            
            self.session.open(
                MessageBox,
                "✅ Hotkey settings saved!\n\nRestart player for changes to take effect.",
                MessageBox.TYPE_INFO,
                timeout=3
            )
            self.close()
        except Exception as e:
            self.session.open(
                MessageBox,
                f"❌ Error saving: {str(e)[:50]}",
                MessageBox.TYPE_ERROR,
                timeout=3
            )
    
    def reset_defaults(self):
        """Reset hotkeys to defaults"""
        self.session.openWithCallback(
            self.reset_confirmed,
            MessageBox,
            "Reset all hotkeys to default settings?",
            MessageBox.TYPE_YESNO
        )
    
    def reset_confirmed(self, confirmed):
        """Handle reset confirmation"""
        if confirmed:
            try:
                # Reset all hotkey settings to defaults
                p = config.plugins.wgfilemanager
                
                p.hotkey_profile.value = "default"
                p.hotkey_play_pause.value = "play"
                p.hotkey_stop.value = "stop"
                p.hotkey_subtitle_toggle.value = "subtitle"
                p.hotkey_subtitle_menu.value = "long_subtitle"
                p.hotkey_player_bar.value = "ok"
                p.hotkey_seek_forward.value = "right"
                p.hotkey_seek_backward.value = "left"
                p.hotkey_red_button.value = "signal"
                p.hotkey_green_button.value = "subtitle_settings"
                p.hotkey_yellow_button.value = "toggle_subtitle"
                p.hotkey_blue_button.value = "jump_menu"
                p.hotkey_long_press_delay.value = "500"
                
                # Save
                from Components.config import configfile
                configfile.save()
                
                # Update UI
                self.setupConfigList()
                
                self.session.open(
                    MessageBox,
                    "✅ Hotkeys reset to defaults!",
                    MessageBox.TYPE_INFO,
                    timeout=2
                )
            except Exception as e:
                self.session.open(
                    MessageBox,
                    f"❌ Error resetting: {str(e)[:50]}",
                    MessageBox.TYPE_ERROR,
                    timeout=3
                )


# ============================================================================
# FACTORY FUNCTIONS FOR INTEGRATION
# ============================================================================

def show_player_settings(session, player=None):
    """Show player settings screen"""
    session.open(PlayerSettings, player)

def show_player_bar_settings(session):
    """Show player bar settings screen"""
    session.open(PlayerBarSettings)

def show_subtitle_settings(session):
    """Show subtitle settings screen"""
    session.open(SubtitleSettings)

def show_hotkey_settings(session):
    """Show hotkey settings screen"""
    session.open(HotkeySettings)


# ============================================================================
# MAIN SETUP MENU INTEGRATION
# ============================================================================

def add_player_settings_to_menu(menu_list):
    """
    Add player-related settings to main setup menu
    
    Args:
        menu_list: Existing menu list to extend
    
    Returns:
        Extended menu list with player settings
    """
    player_menu_items = [
        ("🎮 Player Settings", show_player_settings),
        ("📊 Player Bar Settings", show_player_bar_settings),
        ("📝 Subtitle Settings", show_subtitle_settings),
        ("🎯 Hotkey Settings", show_hotkey_settings),
    ]
    
    # Insert after existing items or at appropriate position
    menu_list.extend(player_menu_items)
    return menu_list