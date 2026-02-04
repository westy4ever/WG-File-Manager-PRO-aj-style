"""
Action Map for EnigmaPlayer
Connects keymap.xml actions to player methods with subtitle support
"""

import logging

try:
    from ..utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


def setup_player_actions(player):
    """
    Setup complete action map for player with subtitle support
    
    Args:
        player: EnigmaPlayer instance
    
    Returns:
        dict: Action mapping dictionary
    """
    
    action_map = {
        # ===== SUBTITLE ACTIONS =====
        'toggle_subtitle': player.toggle_subtitle,
        'open_subtitle_menu': player.open_subtitle_menu,
        'open_subtitle_settings': player.open_subtitle_menu,
        'showSubtitleMenu': player.open_subtitle_menu,
        'open_subtitle_tools': lambda: player.open_subtitle_menu(),
        'subtitle_toggle_quick': player.toggle_subtitle,
        'subtitle_settings_quick': player.open_subtitle_menu,
        
        # Quick delay adjustments
        'subtitle_delay_minus_5': lambda: player.adjust_subtitle_delay(-5000),
        'subtitle_delay_minus_1': lambda: player.adjust_subtitle_delay(-1000),
        'subtitle_delay_minus_01': lambda: player.adjust_subtitle_delay(-100),
        'subtitle_delay_plus_01': lambda: player.adjust_subtitle_delay(100),
        'subtitle_delay_plus_1': lambda: player.adjust_subtitle_delay(1000),
        'subtitle_delay_plus_5': lambda: player.adjust_subtitle_delay(5000),
        
        # Subtitle style
        'toggle_subtitle_style': lambda: player.cycle_subtitle_style(),
        'toggle_subtitle_position': lambda: player.cycle_subtitle_position(),
        'cycle_font_size': lambda: player.cycle_font_size(),
        'cycle_font_color': lambda: player.cycle_font_color(),
        'cycle_subtitle_encoding': lambda: player.cycle_subtitle_encoding(),
        'cycle_subtitle_track': lambda: player.cycle_subtitle_track(),
        
        # ===== AUDIO ACTIONS =====
        'audio_menu': player.audio_menu_fixed,
        'audio_selection': player.audio_menu_fixed,
        'long_audio': lambda: player.seek_relative(-30),  # Jump back 30s
        'quick_jump_back': lambda: player.seek_relative(-30),
        'cycle_audio_track': lambda: player.cycle_audio_track(),
        
        # ===== PLAYBACK CONTROLS =====
        'play_pause': player.play_pause_fixed,
        'playpause': player.play_pause_fixed,
        'stop': player.stop,
        
        # ===== SEEK CONTROLS =====
        'seek_forward': lambda: player.seek_relative(10),    # +10 seconds
        'seek_backward': lambda: player.seek_relative(-10),  # -10 seconds
        'seek_forward_10': lambda: player.seek_relative(30),  # +30 seconds
        'seek_backward_10': lambda: player.seek_relative(-30), # -30 seconds
        'seek_forward_fast': lambda: player.seek_relative(60), # +1 minute
        'seek_backward_fast': lambda: player.seek_relative(-60), # -1 minute
        'fast_forward': lambda: player.seek_relative(60),
        'rewind': lambda: player.seek_relative(-60),
        
        # ===== CHANNEL CONTROLS =====
        'channel_up': player.channel_up_fixed,
        'channel_down': player.channel_down_fixed,
        'next': lambda: player.next_file(),
        'previous': lambda: player.previous_file(),
        'next_file': lambda: player.next_file(),
        'previous_file': lambda: player.previous_file(),
        
        # ===== INFO & SIGNAL =====
        'show_signal_monitor': player.show_signal_monitor_fixed,
        'signal_monitor': player.show_signal_monitor_fixed,
        'show_info': player.show_signal_monitor_fixed,
        'show_extended_info': lambda: player.show_extended_info(),
        
        # ===== CUTLIST & CATCHUP =====
        'show_cutlist': player.show_cutlist_fixed,
        'show_catchup': player.show_catchup_fixed,
        'mark_in_point': lambda: player.mark_position("in"),
        'mark_out_point': lambda: player.mark_position("out"),
        
        # ===== SERVICE MANAGEMENT =====
        'refresh_service': player.refresh_service_fixed,
        
        # ===== PLAYER UI =====
        'show_player_bar': lambda: player.toggle_player_bar(),
        'toggle_fullscreen': lambda: player.toggle_fullscreen(),
        'toggle_infobar': lambda: player.toggle_info_bar(),
        'open_player_menu': lambda: player.open_player_menu(),
        'open_player_settings': lambda: player.open_player_settings(),
        
        # ===== JUMP & CHAPTERS =====
        'open_jump_menu': lambda: player.open_jump_menu(),
        'open_chapter_menu': lambda: player.open_chapter_menu(),
        
        # ===== VOLUME =====
        'volume_up': lambda: player.adjust_volume(5),
        'volume_down': lambda: player.adjust_volume(-5),
        'toggle_mute': lambda: player.toggle_mute(),
        
        # ===== ASPECT RATIO & ZOOM =====
        'toggle_aspect_ratio': lambda: player.toggle_aspect_ratio(),
        'toggle_zoom': lambda: player.toggle_zoom(),
        
        # ===== RECORDING =====
        'toggle_record': lambda: player.toggle_record(),
        'open_recording_menu': lambda: player.open_recording_menu(),
        'toggle_timeshift': lambda: player.toggle_timeshift(),
        
        # ===== EPG & TELEVISION =====
        'show_epg': lambda: player.show_epg(),
        'switch_tv_radio': lambda: player.switch_tv_radio(),
        'toggle_teletext': lambda: player.toggle_teletext(),
        
        # ===== BOOKMARKS & SCREENSHOTS =====
        'toggle_bookmark': lambda: player.toggle_bookmark(),
        'take_screenshot': lambda: player.take_screenshot(),
        
        # ===== PLAYLIST & REPEAT =====
        'show_playlist': lambda: player.show_playlist(),
        'toggle_repeat': lambda: player.toggle_repeat(),
        'toggle_slow_motion': lambda: player.toggle_slow_motion(),
        
        # ===== FRAME ADVANCE & ANGLES =====
        'frame_advance': lambda: player.frame_advance(),
        'cycle_angle': lambda: player.cycle_angle(),
    }
    
    logger.info(f"Created action map with {len(action_map)} actions")
    return action_map


def bind_actions_to_player(player, session):
    """
    Bind action map to player session
    
    Args:
        player: EnigmaPlayer instance
        session: Enigma2 session
    
    Returns:
        bool: True if successful
    """
    try:
        from Components.ActionMap import ActionMap
        
        # Get action map
        actions_dict = setup_player_actions(player)
        
        # Create ActionMap instance
        actions = ActionMap(
            ["MoviePlayer", "InfobarShowHideActions", "SubtitleActions"],
            actions_dict,
            -1  # Priority
        )
        
        # Store in player
        player.session = session
        player["actions"] = actions
        
        logger.info("Successfully bound actions to player")
        return True
        
    except ImportError as e:
        logger.error(f"Cannot import ActionMap: {e}")
        return False
    except Exception as e:
        logger.error(f"Error binding actions to player: {e}")
        return False


def get_action_description(action_name):
    """
    Get description for an action
    
    Args:
        action_name: Name of the action
    
    Returns:
        str: Action description
    """
    descriptions = {
        'toggle_subtitle': "Toggle subtitle display on/off",
        'open_subtitle_menu': "Open subtitle settings menu",
        'audio_menu': "Open audio track selection",
        'play_pause': "Play/pause playback",
        'stop': "Stop playback",
        'seek_forward': "Seek forward 10 seconds",
        'seek_backward': "Seek backward 10 seconds",
        'channel_up': "Switch to next channel",
        'channel_down': "Switch to previous channel",
        'show_signal_monitor': "Show signal information",
        'show_cutlist': "Open cutlist editor",
        'show_catchup': "Show catchup programs",
        'refresh_service': "Refresh current service",
    }
    
    return descriptions.get(action_name, "No description available")


def list_all_actions():
    """
    List all available actions
    
    Returns:
        list: List of action names
    """
    # Test player to get actions
    class TestPlayer:
        def toggle_subtitle(self): pass
        def open_subtitle_menu(self): pass
        def audio_menu_fixed(self): pass
        def play_pause_fixed(self): pass
        def stop(self): pass
        def seek_relative(self, seconds): pass
        def channel_up_fixed(self): pass
        def channel_down_fixed(self): pass
        def show_signal_monitor_fixed(self): pass
        def show_cutlist_fixed(self): pass
        def show_catchup_fixed(self): pass
        def refresh_service_fixed(self): pass
        def mark_position(self, point): pass
    
    test_player = TestPlayer()
    actions = setup_player_actions(test_player)
    
    return sorted(list(actions.keys()))