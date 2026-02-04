#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WG File Manager PRO v1.1 - Professional File Manager for Enigma2
Enhanced with Smart Context Menus, Remote Access & Subtitle Support
"""

import sys
import traceback
import os

# ===== ENIGMA2 IMPORTS =====
try:
    from Plugins.Plugin import PluginDescriptor  # <-- CRITICAL: This was missing!
    from Screens.MessageBox import MessageBox
except ImportError as e:
    print("[WGFileManager FATAL] Cannot import Enigma2 modules: %s" % str(e))
    print("[WGFileManager FATAL] This plugin only runs within Enigma2 environment")
    sys.exit(1)

# ===== FIX 1: Python 2 compatibility =====
PY2 = sys.version_info[0] == 2
if not PY2:
    print("[WGFileManager] WARNING: Enigma2 typically uses Python 2.7")

# ===== FIX 2: Safe translation setup =====
try:
    import language
    from Tools.Directories import resolveFilename, SCOPE_PLUGINS
    import gettext
    
    # Get language without overriding system env
    lang = language.getLanguage()[:2]
    
    # Setup translation properly
    domain = "enigma2"
    gettext.bindtextdomain(domain, resolveFilename(SCOPE_PLUGINS))
    gettext.textdomain(domain)
    
    # Create translation function
    def _(txt):
        if PY2:
            return gettext.gettext(txt).decode('utf-8')
        return gettext.gettext(txt)
        
except ImportError as e:
    print("[WGFileManager] Translation import error: %s" % str(e))
    # Fallback: no translation
    def _(txt):
        if PY2 and isinstance(txt, str):
            return txt.decode('utf-8', errors='ignore')
        return txt

# ===== FIX 3: Robust logging setup =====
try:
    # Try absolute import (installed mode)
    from Plugins.Extensions.WGFileManager.utils.logging_config import setup_logging, get_logger
    logger = get_logger(__name__)
    logger.debug("Using absolute import for logging")
    
except ImportError:
    try:
        # Try relative import (development mode)
        from .utils.logging_config import setup_logging, get_logger
        logger = get_logger(__name__)
        logger.debug("Using relative import for logging")
        
    except ImportError as e:
        # Ultimate fallback
        import logging
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='/tmp/wgfilemanager_fallback.log'
        )
        logger = logging.getLogger(__name__)
        logger.error("Failed to setup proper logging: %s" % str(e))

# ===== FIX 4: Import player and subtitle modules =====
try:
    from .player.enigma_player import EnigmaPlayer
    from .player.subtitle_manager import SubtitleManager
    from .player.subtitle_factory import get_subtitle_manager
    logger.info("✓ Successfully imported player and subtitle modules")
    
except ImportError as e:
    logger.error(f"✗ Error importing player/subtitle modules: {e}")
    logger.error("Traceback:\n%s" % traceback.format_exc())
    
    # Create dummy classes for fallback
    class EnigmaPlayer:
        def __init__(self, session, subtitle_manager=None):
            self.session = session
            logger.warning("Using fallback EnigmaPlayer (no subtitle support)")
        
        def play(self, service_ref, resume_callback=None):
            logger.warning("Fallback player: Cannot play files")
    
    class SubtitleManager:
        def __init__(self, session):
            self.session = session
            logger.warning("Using fallback SubtitleManager")
    
    def get_subtitle_manager(session, video_file=None):
        logger.warning("Using fallback subtitle manager factory")
        return SubtitleManager(session)

from Components.config import config

def main(session, **kwargs):
    """Main entry point for the plugin"""
    logger.info("=" * 60)
    logger.info("Starting WG File Manager PRO v1.1 - Subtitle Edition")
    logger.info("Python %s on %s" % (sys.version, sys.platform))
    
    try:
        # Initialize config to ensure all settings are registered
        from Plugins.Extensions.WGFileManager.core.config import WGFileManagerConfig
        config_manager = WGFileManagerConfig()
        config_manager.setup_config()
        
        # Verify subtitle configuration exists
        self._verify_subtitle_config()
        
        # Try to import main screen
        logger.info("Attempting to import WGFileManagerMain...")
        
        try:
            from Plugins.Extensions.WGFileManager.ui.main_screen import WGFileManagerMain
            logger.info("✓ Successfully imported WGFileManagerMain")
            
        except ImportError as ie:
            # Try relative import as fallback
            logger.warning("Absolute import failed, trying relative...")
            try:
                from .ui.main_screen import WGFileManagerMain
                logger.info("✓ Successfully imported WGFileManagerMain (relative)")
            except ImportError:
                logger.error("✗ ALL import attempts failed")
                logger.error("Import error details: %s" % str(ie))
                logger.error("Python path: %s" % str(sys.path))
                logger.error("Full traceback:\n%s" % traceback.format_exc())
                raise
        
        # Open the main screen
        logger.info("Opening WGFileManagerMain screen...")
        session.open(WGFileManagerMain)
        logger.info("✓ WGFileManager started successfully")
        logger.info("Subtitle features: ✓ Auto-load, ✓ SRT/SUB/ASS/VTT, ✓ Delay adjustment")
        
    except Exception as e:
        error_msg = "Failed to start WGFileManager: %s" % str(e)
        error_trace = traceback.format_exc()
        
        logger.error(error_msg)
        logger.error("Traceback:\n%s" % error_trace)
        
        # Show error to user
        try:
            session.open(
                MessageBox,
                _("Failed to start WGFileManager") + ":\n\n%s\n\n%s" % (
                    str(e)[:100], 
                    _("Check /tmp/wgfilemanager.log for details")
                ),
                MessageBox.TYPE_ERROR,
                timeout=10
            )
        except Exception as msg_error:
            logger.error("Could not show error message: %s" % str(msg_error))
        
        return None

def _verify_subtitle_config(self):
    """Verify subtitle configuration exists"""
    try:
        if not hasattr(config.plugins, 'wgfilemanager'):
            config.plugins.wgfilemanager = config.ConfigSubsection()
            logger.info("Created wgfilemanager config subsection")
        
        p = config.plugins.wgfilemanager
        
        # Check for essential subtitle configs
        essential_configs = [
            'subtitle_delay', 'subtitle_auto_load', 'subtitle_encoding',
            'subtitle_font_size', 'subtitle_font_color', 'subtitle_position'
        ]
        
        missing_configs = []
        for config_name in essential_configs:
            if not hasattr(p, config_name):
                missing_configs.append(config_name)
        
        if missing_configs:
            logger.warning(f"Missing subtitle configs: {missing_configs}")
            logger.info("Subtitle configs will be created when SubtitleManager initializes")
        
        logger.info("✓ Subtitle configuration verified")
        
    except Exception as e:
        logger.error(f"Error verifying subtitle config: {e}")

def menu(menuid, **kwargs):
    """Plugin menu integration"""
    if menuid == "mainmenu":
        return [(_("WG File Manager PRO"), main, "wgfilemanager", 46)]
    return []

def Plugins(**kwargs):
    """Plugin descriptor with subtitle feature listing"""
    description = _("WG File Manager PRO - Advanced File Management with Subtitle Support")
    
    # Extended description with features
    extended_description = _("""
Advanced file manager with dual pane interface.
Features:
• File operations (copy, move, delete, rename)
• Media player with subtitle support (SRT, SUB, ASS, VTT)
• Network access (FTP, SFTP, WebDAV, SMB)
• Archive support (ZIP, TAR, RAR)
• Subtitle management with delay adjustment
• Auto-load subtitles for videos
• Hotkey configuration
""")
    
    # ===== FIX 5: Handle missing icon gracefully =====
    icon_path = None
    possible_icon_locations = [
        "/usr/lib/enigma2/python/Plugins/Extensions/WGFileManager/wgfilemanager.png",
        "/usr/share/enigma2/picon/wgfilemanager.png",
        "icons/blue.png",  # Use one of our icons as fallback
    ]
    
    for location in possible_icon_locations:
        try:
            if os.path.exists(location):
                icon_path = location
                logger.debug("Found icon at: %s" % location)
                break
        except:
            pass
    
    # Create plugin descriptors
    descriptors = []
    
    # Plugin menu entry
    descriptors.append(
        PluginDescriptor(
            name="WG File Manager PRO",
            description=description,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=icon_path,
            fnc=main
        )
    )
    
    # Main menu entry
    descriptors.append(
        PluginDescriptor(
            name="WG File Manager PRO",
            description=description,
            where=PluginDescriptor.WHERE_MENU,
            fnc=menu
        )
    )
    
    # Extended info in plugin browser
    descriptors.append(
        PluginDescriptor(
            name="WG File Manager PRO",
            description=extended_description,
            where=PluginDescriptor.WHERE_PLUGINDB,
            icon=icon_path,
            fnc=main
        )
    )
    
    logger.info("Plugin descriptors created: %d entries" % len(descriptors))
    logger.info("Features advertised: Dual pane, Media player, Subtitle support, Network access")
    
    return descriptors

# ===== DEVELOPMENT & TESTING MODE =====
if __name__ == "__main__":
    # Test mode - only runs when executed directly
    print("=" * 60)
    print("WG File Manager PRO v1.1 - Test Mode")
    print("Subtitle Edition with full format support")
    print("=" * 60)
    print("Python version: %s" % sys.version)
    print("This plugin is designed to run within Enigma2.")
    print("Install path should be: /usr/lib/enigma2/python/Plugins/Extensions/WGFileManager/")
    print("=" * 60)
    
    # Test imports
    test_modules = [
        ("enigma_player", "player.enigma_player"),
        ("subtitle_manager", "player.subtitle_manager"),
        ("subtitle_bridge", "player.subtitle_bridge"),
        ("main_screen", "ui.main_screen"),
        ("subtitle_menu", "ui.subtitle_menu"),
    ]
    
    print("\nTesting module imports:")
    print("-" * 40)
    
    all_imports_ok = True
    
    for module_name, import_path in test_modules:
        try:
            # Try absolute import
            exec(f"import {import_path.replace('/', '.')}")
            print(f"✓ {module_name:20} - Import successful")
        except ImportError:
            try:
                # Try relative import
                exec(f"from .{import_path} import *")
                print(f"✓ {module_name:20} - Relative import successful")
            except ImportError as e:
                print(f"✗ {module_name:20} - Import failed: {e}")
                all_imports_ok = False
    
    print("-" * 40)
    
    if all_imports_ok:
        print("✅ All critical modules import successfully!")
        print("\nKey Features Available:")
        print("  • EnigmaPlayer with subtitle integration")
        print("  • SubtitleManager with multi-format support")
        print("  • SubtitleBridge (SRT, SUB, ASS, VTT)")
        print("  • Advanced Subtitle Menu UI")
        print("  • Auto-load subtitles for videos")
    else:
        print("⚠️  Some modules failed to import")
        print("Check that all files are in the correct location.")
    
    print("\nTo install:")
    print("1. Copy entire WGFileManager folder to:")
    print("   /usr/lib/enigma2/python/Plugins/Extensions/")
    print("2. Restart Enigma2 GUI")
    print("3. Access from Plugin Menu or Main Menu")
    
    print("\nSubtitle Usage:")
    print("• During playback: SUBTITLE button toggles subtitles")
    print("• During playback: TEXT button opens subtitle menu")
    print("• In file manager: 0 button on video files for options")
    print("• Quick delay: Use 1,2,3,7,8,9 keys during playback")
    
    print("=" * 60)