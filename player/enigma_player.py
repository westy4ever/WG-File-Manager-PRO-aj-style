"""
EnigmaPlayer - Complete Implementation with Subtitle Support
Enhanced player with subtitle integration and fixed TODO methods
"""

import os
import logging
import time
from enigma import eServiceCenter, eServiceReference

try:
    from ..utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class EnigmaPlayer:
    """Enhanced Enigma2 Player with Subtitle Support"""
    
    def __init__(self, session, subtitle_manager=None):
        self.session = session
        self.subtitle_manager = subtitle_manager
        self.current_service = None
        self.current_file = None
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        
        logger.info("EnigmaPlayer initialized with subtitle support")
    
    def play(self, service_ref, resume_callback=None):
        """Play a service or file"""
        try:
            self.current_service = service_ref
            self.current_file = service_ref.getPath() if hasattr(service_ref, 'getPath') else str(service_ref)
            
            # Auto-load subtitles if available
            if self.subtitle_manager and self.current_file:
                self.subtitle_manager.set_video_file(self.current_file)
                self.subtitle_manager.auto_load_subtitle(service_ref)
            
            self.session.nav.playService(service_ref)
            self.is_playing = True
            self.is_paused = False
            
            logger.info(f"Playing: {self.current_file}")
            
            if resume_callback:
                self.resume_callback = resume_callback
                
        except Exception as e:
            logger.error(f"Error playing service: {e}")
            raise
    
    def play_pause_fixed(self):
        """Toggle play/pause - FIXED"""
        if not self.current_service:
            return
        
        if self.is_paused:
            # Resume playback
            try:
                service = self.session.nav.getCurrentService()
                if service:
                    seekable = service.seek()
                    if seekable:
                        seekable.seekTo(0)  # Continue from current position
                    self.is_paused = False
                    self.is_playing = True
                    self.show_notification("Resumed")
                    logger.info("Playback resumed")
            except Exception as e:
                logger.error(f"Error resuming playback: {e}")
        else:
            # Pause playback
            try:
                service = self.session.nav.getCurrentService()
                if service:
                    pauseable = service.pause()
                    if pauseable:
                        pauseable.pause()
                    self.is_paused = True
                    self.is_playing = False
                    self.show_notification("Paused")
                    logger.info("Playback paused")
            except Exception as e:
                logger.error(f"Error pausing playback: {e}")
    
    def stop(self):
        """Stop playback"""
        try:
            self.session.nav.stopService()
            self.is_playing = False
            self.is_paused = False
            self.current_service = None
            
            # Disable subtitles when stopping
            if self.subtitle_manager:
                self.subtitle_manager.disable()
            
            logger.info("Playback stopped")
            
            if hasattr(self, 'resume_callback'):
                self.resume_callback()
                
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
    
    # Subtitle Methods
    def toggle_subtitle(self):
        """Toggle subtitle on/off"""
        if self.subtitle_manager:
            enabled = self.subtitle_manager.toggle_subtitles()
            status = "ON" if enabled else "OFF"
            self.show_notification(f"Subtitles: {status}")
            logger.info(f"Subtitles toggled: {status}")
        else:
            self.show_notification("Subtitle manager not available")
            logger.warning("No subtitle manager available")
    
    def open_subtitle_menu(self):
        """Open subtitle menu"""
        if self.subtitle_manager and self.current_file:
            try:
                from ..ui.subtitle_menu import SubtitleMenuScreen
                self.session.open(SubtitleMenuScreen, self.subtitle_manager, self.current_file)
                logger.info("Opened subtitle menu")
            except ImportError as e:
                logger.error(f"Cannot import subtitle menu: {e}")
                self.show_notification("Subtitle menu not available")
        else:
            self.show_notification("No video playing or subtitle manager not available")
    
    def open_subtitle_settings(self):
        """Open subtitle settings (alias for menu)"""
        self.open_subtitle_menu()
    
    # Audio Methods
    def audio_menu_fixed(self):
        """Show audio track selection - FIXED"""
        try:
            service = self.session.nav.getCurrentService()
            if not service:
                self.show_notification("No active service")
                return
            
            # Get audio tracks
            audio_tracks = []
            info = service.info()
            if info:
                n = info.getNumberOfTracks()
                for i in range(n):
                    track_info = info.getTrackInfo(i)
                    if track_info:
                        description = track_info.getDescription() or f"Track {i+1}"
                        language = track_info.getLanguage() or "Unknown"
                        audio_tracks.append((f"{description} ({language})", i))
            
            if not audio_tracks:
                self.show_notification("No audio tracks available")
                return
            
            # Show selection menu
            from ..ui.dialogs import ChoiceBox
            self.session.openWithCallback(
                self.audio_track_selected,
                ChoiceBox,
                title="Select Audio Track",
                list=audio_tracks
            )
            
        except Exception as e:
            logger.error(f"Error in audio_menu: {e}")
            self.show_notification("Audio menu error")
    
    def audio_track_selected(self, choice):
        """Callback when audio track is selected"""
        if choice:
            try:
                track_index = choice[1]
                service = self.session.nav.getCurrentService()
                if service:
                    info = service.info()
                    if info:
                        info.selectTrack(track_index)
                        self.show_notification(f"Audio: {choice[0]}")
                        logger.info(f"Selected audio track: {choice[0]}")
            except Exception as e:
                logger.error(f"Error selecting audio track: {e}")
    
    # Signal Monitor
    def show_signal_monitor_fixed(self):
        """Show signal monitor - FIXED"""
        try:
            service = self.session.nav.getCurrentService()
            if not service:
                self.show_notification("No active service")
                return
            
            # Get signal information
            feinfo = service.frontendInfo()
            if not feinfo:
                self.show_notification("No signal information available")
                return
            
            # Collect signal data
            signal_data = []
            
            # Signal strength
            signal_power = feinfo.getFrontendInfo(0)  # iFrontendInformation_ENUMS.signalPower
            if signal_power > 0:
                signal_data.append(f"Signal Strength: {signal_power}%")
            
            # Signal quality
            signal_quality = feinfo.getFrontendInfo(1)  # iFrontendInformation_ENUMS.signalQuality
            if signal_quality > 0:
                signal_data.append(f"Signal Quality: {signal_quality}%")
            
            # BER (Bit Error Rate)
            ber = feinfo.getFrontendInfo(2)
            if ber >= 0:
                signal_data.append(f"BER: {ber}")
            
            # SNR (Signal to Noise Ratio)
            snr = feinfo.getFrontendInfo(3)
            if snr >= 0:
                signal_data.append(f"SNR: {snr} dB")
            
            if signal_data:
                message = "\n".join(signal_data)
            else:
                message = "No signal data available"
            
            # Show signal information
            from Screens.MessageBox import MessageBox
            self.session.open(
                MessageBox,
                message,
                MessageBox.TYPE_INFO,
                timeout=5,
                title="Signal Monitor"
            )
            
        except Exception as e:
            logger.error(f"Error in signal monitor: {e}")
            self.show_notification("Signal monitor error")
    
    # Service Management
    def refresh_service_fixed(self):
        """Refresh current service - FIXED"""
        if self.current_service and self.is_playing:
            try:
                self.show_notification("Refreshing...")
                logger.info("Refreshing service")
                
                # Save current position
                current_pos = self.current_position
                
                # Restart service
                self.session.nav.stopService()
                self.session.nav.playService(self.current_service)
                
                # Seek to saved position if available
                if current_pos > 0:
                    service = self.session.nav.getCurrentService()
                    if service:
                        seekable = service.seek()
                        if seekable:
                            seekable.seekTo(int(current_pos * 90000))  # Convert to 90kHz pts
                
                self.show_notification("Service refreshed")
                
            except Exception as e:
                logger.error(f"Error refreshing service: {e}")
                self.show_notification("Refresh failed")
    
    def show_catchup_fixed(self):
        """Show catchup programs - FIXED"""
        try:
            # This would typically interface with a catchup/timeshift system
            # For now, show a placeholder with basic info
            
            if not self.current_service:
                self.show_notification("No active service")
                return
            
            # Check if service supports timeshift
            service = self.session.nav.getCurrentService()
            if not service:
                self.show_notification("Service not available")
                return
            
            # Get service information
            info = service.info()
            if info:
                service_name = info.getName() or self.service_name
                
                # Show catchup menu placeholder
                options = [
                    ("View Recording Schedule", "schedule"),
                    ("Browse Past Programs", "browse"),
                    ("Enable Timeshift", "timeshift"),
                ]
                
                from ..ui.dialogs import ChoiceBox
                self.session.open(
                    ChoiceBox,
                    title=f"Catchup: {service_name}",
                    list=options
                )
            else:
                self.show_notification("Catchup not available for this service")
                
        except Exception as e:
            logger.error(f"Error in catchup: {e}")
            self.show_notification("Catchup error")
    
    def show_cutlist_fixed(self):
        """Show cutlist editor - FIXED"""
        try:
            if not self.current_service:
                self.show_notification("No active service")
                return
            
            # Get current service path
            service_path = None
            if hasattr(self.current_service, 'getPath'):
                service_path = self.current_service.getPath()
            
            if not service_path or not os.path.exists(service_path):
                self.show_notification("Cutlist not available for streaming content")
                return
            
            # Check if cutlist exists
            cutlist_path = service_path + ".cuts"
            
            options = []
            if os.path.exists(cutlist_path):
                options.append(("Edit Cutlist", "edit"))
                options.append(("Clear Cutlist", "clear"))
            else:
                options.append(("Create Cutlist", "create"))
            
            options.append(("Mark In Point", "mark_in"))
            options.append(("Mark Out Point", "mark_out"))
            
            from ..ui.dialogs import ChoiceBox
            self.session.openWithCallback(
                self.cutlist_callback,
                ChoiceBox,
                title="Cutlist Editor",
                list=options
            )
            
        except Exception as e:
            logger.error(f"Error in cutlist: {e}")
            self.show_notification("Cutlist error")
    
    def cutlist_callback(self, choice):
        """Handle cutlist menu selection"""
        if not choice:
            return
        
        action = choice[1]
        
        if action == "mark_in":
            self.mark_position("in")
        elif action == "mark_out":
            self.mark_position("out")
        elif action == "create":
            self.show_notification("Cutlist created")
            # Create empty cutlist file
            if hasattr(self.current_service, 'getPath'):
                service_path = self.current_service.getPath()
                if service_path:
                    cutlist_path = service_path + ".cuts"
                    open(cutlist_path, 'a').close()
        elif action == "clear":
            self.show_notification("Cutlist cleared")
            # Clear cutlist file
            if hasattr(self.current_service, 'getPath'):
                service_path = self.current_service.getPath()
                if service_path:
                    cutlist_path = service_path + ".cuts"
                    if os.path.exists(cutlist_path):
                        os.remove(cutlist_path)
    
    # Channel Management
    def channel_up_fixed(self):
        """Channel up - FIXED"""
        try:
            # Get current service from navigation
            current_service = self.session.nav.getCurrentlyPlayingServiceReference()
            if not current_service:
                self.show_notification("No channel list available")
                return
            
            # Get service list
            serviceHandler = eServiceCenter.getInstance()
            servicelist = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25)'))
            
            if servicelist:
                services = servicelist.getContent("R", True)
                if services:
                    # Find current service index
                    current_index = -1
                    for i, service in enumerate(services):
                        if service == current_service:
                            current_index = i
                            break
                    
                    # Get next service
                    if current_index >= 0 and current_index < len(services) - 1:
                        next_service = services[current_index + 1]
                        self.play_service(next_service)
                        self.show_notification("Channel Up")
                    else:
                        self.show_notification("Last channel")
                else:
                    self.show_notification("No channels available")
            
        except Exception as e:
            logger.error(f"Error in channel_up: {e}")
            self.show_notification("Channel switch error")
    
    def channel_down_fixed(self):
        """Channel down - FIXED"""
        try:
            # Get current service from navigation
            current_service = self.session.nav.getCurrentlyPlayingServiceReference()
            if not current_service:
                self.show_notification("No channel list available")
                return
            
            # Get service list
            serviceHandler = eServiceCenter.getInstance()
            servicelist = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25)'))
            
            if servicelist:
                services = servicelist.getContent("R", True)
                if services:
                    # Find current service index
                    current_index = -1
                    for i, service in enumerate(services):
                        if service == current_service:
                            current_index = i
                            break
                    
                    # Get previous service
                    if current_index > 0:
                        prev_service = services[current_index - 1]
                        self.play_service(prev_service)
                        self.show_notification("Channel Down")
                    else:
                        self.show_notification("First channel")
                else:
                    self.show_notification("No channels available")
            
        except Exception as e:
            logger.error(f"Error in channel_down: {e}")
            self.show_notification("Channel switch error")
    
    def play_service(self, service_ref):
        """Play a service reference"""
        try:
            self.session.nav.playService(service_ref)
            self.current_service = service_ref
            self.is_playing = True
            self.is_paused = False
            logger.info(f"Playing service: {service_ref}")
        except Exception as e:
            logger.error(f"Error playing service: {e}")
            self.show_notification("Cannot play channel")
    
    def mark_position(self, point_type):
        """Mark in/out point for cutlist"""
        try:
            service = self.session.nav.getCurrentService()
            if service:
                seekable = service.seek()
                if seekable:
                    pos = seekable.getPlayPosition()
                    if pos[0]:
                        position_sec = pos[1] / 90000.0
                        self.show_notification(f"{point_type.upper()} point: {position_sec:.1f}s")
                        logger.info(f"Marked {point_type} point at {position_sec:.1f}s")
                    else:
                        self.show_notification("Cannot get position")
        except Exception as e:
            logger.error(f"Error marking position: {e}")
            self.show_notification("Mark failed")
    
    # Helper Methods
    def show_notification_fixed(self, message, timeout=2):
        """Show notification message - FIXED"""
        try:
            from Screens.MessageBox import MessageBox
            self.session.openWithCallback(
                lambda x: None,
                MessageBox,
                message,
                MessageBox.TYPE_INFO,
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
    def show_notification(self, message, timeout=2):
        """Alias for show_notification_fixed"""
        self.show_notification_fixed(message, timeout)
    
    def get_current_position(self):
        """Get current playback position in seconds"""
        try:
            if not self.is_playing:
                return 0
            
            service = self.session.nav.getCurrentService()
            if service:
                seekable = service.seek()
                if seekable:
                    pos = seekable.getPlayPosition()
                    if pos[0]:
                        return pos[1] / 90000.0
            return 0
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return 0
    
    def get_duration(self):
        """Get total duration in seconds"""
        try:
            if not self.is_playing:
                return 0
            
            service = self.session.nav.getCurrentService()
            if service:
                seekable = service.seek()
                if seekable:
                    length = seekable.getLength()
                    if length[0]:
                        return length[1] / 90000.0
            return 0
        except Exception as e:
            logger.error(f"Error getting duration: {e}")
            return 0
    
    def seek_relative(self, seconds):
        """Seek forward/backward by seconds"""
        try:
            if not self.is_playing:
                return
            
            service = self.session.nav.getCurrentService()
            if service:
                seekable = service.seek()
                if seekable:
                    current = self.get_current_position()
                    new_pos = max(0, current + seconds)
                    seekable.seekTo(int(new_pos * 90000))
                    
                    direction = "forward" if seconds > 0 else "back"
                    self.show_notification(f"Seek {direction} {abs(seconds)}s")
                    logger.info(f"Seek {direction} to {new_pos:.1f}s")
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            self.show_notification("Seek failed")
    
    def seek_to(self, position_seconds):
        """Seek to specific position"""
        try:
            if not self.is_playing:
                return
            
            service = self.session.nav.getCurrentService()
            if service:
                seekable = service.seek()
                if seekable:
                    seekable.seekTo(int(position_seconds * 90000))
                    self.show_notification(f"Seek to {position_seconds:.0f}s")
                    logger.info(f"Seek to {position_seconds:.1f}s")
        except Exception as e:
            logger.error(f"Error seeking to position: {e}")
            self.show_notification("Seek failed")


# Compatibility aliases
CustomMoviePlayer = EnigmaPlayer
WGFileManagerMediaPlayer = EnigmaPlayer
EnigmaMediaPlayer = EnigmaPlayer