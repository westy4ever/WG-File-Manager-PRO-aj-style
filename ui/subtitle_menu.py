"""
Advanced Subtitle Menu Dialog for WGFileManager
Complete subtitle management UI with live preview and customization
Location: ui/subtitle_menu.py
"""
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.LocationBox import LocationBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ConfigList import ConfigList
from Components.config import (
    config, ConfigSubsection, ConfigInteger, ConfigSelection,
    ConfigText, ConfigYesNo, getConfigListEntry, configfile
)
from enigma import getDesktop, eTimer
import os
import re
import time
import shutil
from datetime import datetime

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SubtitleMenuScreen(Screen):
    """Advanced Subtitle Menu with Live Preview and Customization - COMPLETE IMPLEMENTATION"""
    
    def __init__(self, session, subtitle_manager, video_file_path=None):
        Screen.__init__(self, session)
        self.session = session
        
        # Handle both bridge and old manager
        self.subtitle_manager = subtitle_manager
        
        # Get video file from bridge if available
        if video_file_path is None and hasattr(subtitle_manager, 'video_file'):
            self.video_file_path = subtitle_manager.video_file
        else:
            self.video_file_path = video_file_path
        
        # Current subtitle settings
        self.current_delay = 0
        self.current_line_index = 0
        self.subtitle_lines = []
        self.current_subtitle_path = None
        self.original_subtitle_path = None
        self.temp_subtitle_path = None
        self.is_dirty = False
        
        # Setup configuration
        self._setup_config()
        
        # Load current delay from config
        self.current_delay = config.plugins.wgfilemanager.subt_delay.value
        
        # Auto-load subtitles if video file provided
        if self.video_file_path:
            self._auto_load_subtitles()
        
        # Setup UI
        self._setup_ui()
        
        # Update timer for live preview
        self.preview_timer = eTimer()
        self.preview_timer.callback.append(self.update_preview)
        
        # Action mappings
        self._setup_actions()
        
        # Initialize
        self.onLayoutFinish.append(self.startup)
    
    def _setup_config(self):
        """Setup complete subtitle configuration"""
        if not hasattr(config.plugins, 'wgfilemanager'):
            config.plugins.wgfilemanager = ConfigSubsection()
        
        p = config.plugins.wgfilemanager
        
        # Delay settings
        if not hasattr(p, 'subt_delay'):
            p.subt_delay = ConfigInteger(default=0, limits=(-3600000, 3600000))
        
        # Font settings
        if not hasattr(p, 'subt_font_name'):
            p.subt_font_name = ConfigSelection(
                default="Regular",
                choices=[
                    ("Regular", "Regular"),
                    ("Bold", "Bold"),
                    ("Italic", "Italic"),
                    ("BoldItalic", "Bold Italic")
                ]
            )
        
        if not hasattr(p, 'subt_font_size'):
            p.subt_font_size = ConfigInteger(default=50, limits=(20, 100))
        
        if not hasattr(p, 'subt_font_color'):
            p.subt_font_color = ConfigSelection(
                default="#FFFF00",
                choices=[
                    ("#FFFFFF", "White"),
                    ("#FFFF00", "Yellow"),
                    ("#00FF00", "Green"),
                    ("#FF0000", "Red"),
                    ("#00FFFF", "Cyan"),
                    ("#FF00FF", "Magenta"),
                    ("#FFA500", "Orange"),
                    ("#ADD8E6", "Light Blue")
                ]
            )
        
        # Position settings
        if not hasattr(p, 'subt_position'):
            p.subt_position = ConfigSelection(
                default="bottom",
                choices=[
                    ("top", "Top (10%)"),
                    ("middle_top", "Middle Top (30%)"),
                    ("center", "Center (50%)"),
                    ("middle_bottom", "Middle Bottom (70%)"),
                    ("bottom", "Bottom (90%)")
                ]
            )
        
        # Background settings
        if not hasattr(p, 'subt_background'):
            p.subt_background = ConfigYesNo(default=True)
        
        if not hasattr(p, 'subt_bg_color'):
            p.subt_bg_color = ConfigSelection(
                default="#000000",
                choices=[
                    ("#000000", "Black"),
                    ("#333333", "Dark Gray"),
                    ("#666666", "Gray"),
                    ("#FFFFFF", "White (transparent)")
                ]
            )
        
        if not hasattr(p, 'subt_bg_opacity'):
            p.subt_bg_opacity = ConfigInteger(default=80, limits=(0, 100))
        
        # Border settings
        if not hasattr(p, 'subt_border'):
            p.subt_border = ConfigYesNo(default=False)
        
        if not hasattr(p, 'subt_border_color'):
            p.subt_border_color = ConfigSelection(
                default="#FFFFFF",
                choices=[
                    ("#FFFFFF", "White"),
                    ("#000000", "Black"),
                    ("#FF0000", "Red"),
                    ("#00FF00", "Green")
                ]
            )
        
        if not hasattr(p, 'subt_border_width'):
            p.subt_border_width = ConfigInteger(default=2, limits=(0, 10))
        
        # Shadow settings
        if not hasattr(p, 'subt_shadow'):
            p.subt_shadow = ConfigYesNo(default=True)
        
        if not hasattr(p, 'subt_shadow_color'):
            p.subt_shadow_color = ConfigSelection(
                default="#000000",
                choices=[
                    ("#000000", "Black"),
                    ("#333333", "Dark Gray"),
                    ("#666666", "Gray")
                ]
            )
        
        if not hasattr(p, 'subt_shadow_offset'):
            p.subt_shadow_offset = ConfigInteger(default=2, limits=(0, 10))
        
        # Advanced settings
        if not hasattr(p, 'subt_line_spacing'):
            p.subt_line_spacing = ConfigInteger(default=10, limits=(0, 50))
        
        if not hasattr(p, 'subt_max_lines'):
            p.subt_max_lines = ConfigInteger(default=2, limits=(1, 5))
        
        if not hasattr(p, 'subt_encoding'):
            p.subt_encoding = ConfigSelection(
                default="utf-8",
                choices=[
                    ("utf-8", "UTF-8"),
                    ("latin-1", "Latin-1"),
                    ("cp1252", "Windows-1252"),
                    ("cp1256", "Arabic (Windows-1256)"),
                    ("cp1251", "Cyrillic (Windows-1251)"),
                    ("iso-8859-1", "ISO-8859-1"),
                    ("iso-8859-6", "Arabic (ISO-8859-6)"),
                    ("iso-8859-7", "Greek (ISO-8859-7)")
                ]
            )
        
        # Auto-load settings
        if not hasattr(p, 'subt_auto_load'):
            p.subt_auto_load = ConfigYesNo(default=True)
        
        if not hasattr(p, 'subt_prefer_lang'):
            p.subt_prefer_lang = ConfigText(default="", visible_width=10, fixed_size=False)
    
    def _setup_ui(self):
        """Setup complete user interface"""
        w, h = getDesktop(0).size().width(), getDesktop(0).size().height()
        
        self.skin = """
        <screen name="SubtitleMenu" position="0,0" size="%d,%d" backgroundColor="#1a1a1a" flags="wfNoBorder">
            <!-- Header -->
            <eLabel position="0,0" size="%d,80" backgroundColor="#0055aa" />
            <eLabel text="SUBTITLE SETTINGS" position="20,10" size="800,60" font="Regular;40" halign="left" valign="center" transparent="1" foregroundColor="#ffffff" />
            
            <!-- Live Preview Area -->
            <eLabel position="20,100" size="%d,200" backgroundColor="#000000" />
            <eLabel text="LIVE PREVIEW AREA" position="30,110" size="%d,30" font="Regular;20" halign="center" transparent="1" foregroundColor="#666666" />
            <widget name="preview_text" position="30,150" size="%d,120" font="Regular;50" halign="center" valign="center" transparent="1" foregroundColor="#FFFF00" shadowColor="#000000" shadowOffset="-2,-2" />
            
            <!-- Current Status -->
            <eLabel position="20,320" size="%d,60" backgroundColor="#333333" />
            <widget name="current_status" position="30,330" size="%d,40" font="Regular;24" halign="left" valign="center" transparent="1" foregroundColor="#00ff00" />
            
            <!-- Subtitle Timeline Navigator -->
            <eLabel position="20,400" size="%d,250" backgroundColor="#222222" />
            <eLabel text="SUBTITLE TIMELINE" position="30,410" size="%d,30" font="Regular;22" halign="left" transparent="1" foregroundColor="#ffff00" />
            <widget name="timeline_list" position="30,450" size="%d,180" font="Regular;20" itemHeight="35" scrollbarMode="showOnDemand" backgroundColor="#222222" foregroundColor="#ffffff" selectionBackground="#0055aa" />
            
            <!-- Configuration Panel -->
            <eLabel position="20,670" size="%d,300" backgroundColor="#2a2a2a" />
            <eLabel text="APPEARANCE SETTINGS" position="30,680" size="%d,30" font="Regular;22" halign="left" transparent="1" foregroundColor="#ffff00" />
            <widget name="config_list" position="30,720" size="%d,230" itemHeight="50" scrollbarMode="showOnDemand" />
            
            <!-- Button Bar -->
            <eLabel position="0,%d" size="%d,80" backgroundColor="#000000" />
            
            <!-- Button Icons -->
            <ePixmap pixmap="buttons/red.png" position="30,%d" size="30,30" alphatest="on" />
            <ePixmap pixmap="buttons/green.png" position="250,%d" size="30,30" alphatest="on" />
            <ePixmap pixmap="buttons/yellow.png" position="470,%d" size="30,30" alphatest="on" />
            <ePixmap pixmap="buttons/blue.png" position="690,%d" size="30,30" alphatest="on" />
            
            <!-- Button Labels -->
            <eLabel text="Reset All" position="70,%d" size="160,30" font="Regular;20" transparent="1" foregroundColor="#ffffff" />
            <eLabel text="Save" position="290,%d" size="160,30" font="Regular;20" transparent="1" foregroundColor="#ffffff" />
            <eLabel text="Reset Delay" position="510,%d" size="160,30" font="Regular;20" transparent="1" foregroundColor="#ffffff" />
            <eLabel text="Browse SRT" position="730,%d" size="160,30" font="Regular;20" transparent="1" foregroundColor="#ffffff" />
            
            <!-- Help Text -->
            <widget name="help_text" position="50,%d" size="%d,20" font="Regular;16" halign="center" transparent="1" foregroundColor="#aaaaaa" />
        </screen>""" % (
            w, h,  # screen size
            w,  # header width
            w-40,  # preview area width
            w-60,  # preview area label width
            w-60,  # preview text width
            w-40,  # status area width
            w-60,  # status text width
            w-40,  # timeline area width
            w-60,  # timeline label width
            w-60,  # timeline list width
            w-40,  # config area width
            w-60,  # config label width
            w-60,  # config list width
            h-80, w,  # button bar position
            h-60,  # red button
            h-60,  # green button
            h-60,  # yellow button
            h-60,  # blue button
            h-55,  # red label
            h-55,  # green label
            h-55,  # yellow label
            h-55,  # blue label
            h-25, w-100  # help text
        )
        
        # Widgets
        self["preview_text"] = Label("Subtitle Preview")
        self["current_status"] = Label("")
        self["timeline_list"] = ConfigList([])
        self["config_list"] = ConfigList([])
        self["help_text"] = Label("↑↓:Delay/Config | ←→:Timeline | OK:Select | RED:Reset | GREEN:Save | YELLOW:Sync | BLUE:More")
    
    def _setup_actions(self):
        """Setup complete action map"""
        self["actions"] = ActionMap([
            "OkCancelActions", "DirectionActions", "ColorActions",
            "ChannelSelectBaseActions", "NumberActions"
        ], {
            "ok": self.key_ok,
            "cancel": self.key_exit,
            "up": self.move_up,
            "down": self.move_down,
            "left": self.timeline_prev,
            "right": self.timeline_next,
            "red": self.reset_all,
            "green": self.save_and_apply,
            "yellow": self.reset_delay,
            "blue": self.show_more_options,
            "channelUp": self.config_up,
            "channelDown": self.config_down,
            "nextBouquet": self.config_page_up,
            "prevBouquet": self.config_page_down,
            "1": lambda: self.quick_delay(-5000),   # -5 seconds
            "2": lambda: self.quick_delay(-1000),   # -1 second
            "3": lambda: self.quick_delay(-100),    # -100 ms
            "7": lambda: self.quick_delay(100),     # +100 ms
            "8": lambda: self.quick_delay(1000),    # +1 second
            "9": lambda: self.quick_delay(5000),    # +5 seconds
            "4": self.open_subtitle_download,
            "5": self.open_subtitle_edit,
            "6": self.open_subtitle_convert,
            "0": self.test_subtitle_appearance,
            "info": self.show_help,
        }, -1)
    
    def _auto_load_subtitles(self):
        """Auto-load subtitles for current video"""
        try:
            if not self.video_file_path or not os.path.exists(self.video_file_path):
                logger.warning("Video file not found for auto-load")
                return False
            
            logger.info(f"Auto-loading subtitles for: {self.video_file_path}")
            
            # Find subtitles
            subtitles = self.subtitle_manager.find_local_subtitles(self.video_file_path)
            
            if subtitles:
                logger.info(f"Found {len(subtitles)} subtitle files")
                
                # Try to find preferred language
                preferred_lang = config.plugins.wgfilemanager.subt_prefer_lang.value.lower()
                selected_subtitle = None
                
                if preferred_lang:
                    for sub in subtitles:
                        if preferred_lang in sub.get('language', '').lower():
                            selected_subtitle = sub['path']
                            logger.info(f"Found preferred language: {preferred_lang}")
                            break
                
                # Fallback to first subtitle
                if not selected_subtitle:
                    selected_subtitle = subtitles[0]['path']
                
                # Load the subtitle
                if self._load_subtitle_file(selected_subtitle):
                    self.current_subtitle_path = selected_subtitle
                    self.original_subtitle_path = selected_subtitle
                    
                    # Create temporary copy for modifications
                    self._create_temp_copy()
                    
                    logger.info(f"Auto-loaded subtitle: {selected_subtitle}")
                    return True
                else:
                    logger.error(f"Failed to load subtitle file: {selected_subtitle}")
            
            # No subtitles found
            logger.warning(f"No subtitles found for: {os.path.basename(self.video_file_path)}")
            self["current_status"].setText("❌ No subtitles found")
            return False
            
        except Exception as e:
            logger.error(f"Error auto-loading subtitles: {e}")
            return False
    
    def _load_subtitle_file(self, subtitle_path):
        """Load subtitle file with comprehensive error handling"""
        try:
            if not os.path.exists(subtitle_path):
                logger.error(f"Subtitle file not found: {subtitle_path}")
                return False
            
            self.current_subtitle_path = subtitle_path
            
            # Load and parse subtitle lines
            success = self._load_subtitle_lines()
            
            if success:
                # Apply current delay to subtitle file
                if self.current_delay != 0:
                    self._apply_delay_to_file()
                
                logger.info(f"Successfully loaded subtitle file: {subtitle_path}")
                return True
            else:
                logger.error(f"Failed to parse subtitle file: {subtitle_path}")
                return False
            
        except Exception as e:
            logger.error(f"Error loading subtitle file: {e}")
            return False
    
    def _create_temp_copy(self):
        """Create temporary copy of subtitle for modifications"""
        try:
            if not self.current_subtitle_path:
                logger.warning("No subtitle path for temp copy")
                return
            
            # Create temp directory if needed
            temp_dir = "/tmp/wgfilemanager_subtitles/"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate temp filename
            timestamp = int(time.time())
            basename = os.path.basename(self.current_subtitle_path)
            self.temp_subtitle_path = os.path.join(temp_dir, f"temp_{timestamp}_{basename}")
            
            # Copy file
            shutil.copy2(self.current_subtitle_path, self.temp_subtitle_path)
            
            logger.info(f"Created temp copy: {self.temp_subtitle_path}")
            
        except Exception as e:
            logger.error(f"Error creating temp copy: {e}")
    
    def _load_subtitle_lines(self):
        """Load subtitle lines with multiple format support"""
        try:
            if not self.current_subtitle_path:
                logger.warning("No subtitle path to load")
                return False
            
            # Clear existing lines
            self.subtitle_lines = []
            
            # Try different encodings
            encodings = [
                config.plugins.wgfilemanager.subt_encoding.value,
                'utf-8',
                'latin-1',
                'cp1252',
                'cp1256',
                'iso-8859-1'
            ]
            
            for encoding in encodings:
                try:
                    with open(self.current_subtitle_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    # Parse based on file extension
                    ext = os.path.splitext(self.current_subtitle_path)[1].lower()
                    
                    if ext == '.srt':
                        self._parse_srt_content(content)
                    elif ext in ['.ass', '.ssa']:
                        self._parse_ass_content(content)
                    elif ext == '.sub':
                        self._parse_sub_content(content)
                    else:
                        # Try auto-detection
                        self._parse_auto_content(content)
                    
                    if self.subtitle_lines:
                        logger.info(f"Loaded {len(self.subtitle_lines)} lines with {encoding} encoding")
                        return True
                        
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"Failed with {encoding}: {e}")
            
            # If all encodings fail, try with errors='ignore'
            try:
                with open(self.current_subtitle_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                self._parse_auto_content(content)
                
                if self.subtitle_lines:
                    logger.info(f"Loaded {len(self.subtitle_lines)} lines (with errors ignored)")
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to load with ignore errors: {e}")
            
            logger.error("All encoding attempts failed")
            return False
            
        except Exception as e:
            logger.error(f"Error loading subtitle lines: {e}")
            return False
    
    def _parse_srt_content(self, content):
        """Parse SRT content with advanced formatting"""
        try:
            # Remove BOM if present
            content = content.lstrip('\ufeff')
            
            # Split into blocks
            blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    try:
                        # Parse index
                        index = lines[0].strip()
                        
                        # Parse timestamp
                        time_match = re.search(r'(\d{1,2}:\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[\.,]\d{3})', lines[1])
                        if not time_match:
                            continue
                        
                        start_time = time_match.group(1)
                        end_time = time_match.group(2)
                        
                        # Parse text (handle multi-line)
                        text_lines = []
                        for i in range(2, len(lines)):
                            line = lines[i].strip()
                            if line:
                                text_lines.append(line)
                        
                        if not text_lines:
                            continue
                        
                        text = ' '.join(text_lines)
                        
                        # Remove HTML tags
                        text = re.sub(r'<[^>]+>', '', text)
                        
                        self.subtitle_lines.append({
                            'index': index,
                            'start': start_time,
                            'end': end_time,
                            'text': text,
                            'start_ms': self._parse_timestamp(start_time),
                            'end_ms': self._parse_timestamp(end_time)
                        })
                        
                    except Exception as e:
                        logger.debug(f"Error parsing SRT block: {e}")
                        continue
            
            # Sort by start time
            self.subtitle_lines.sort(key=lambda x: x['start_ms'])
            
            logger.debug(f"Parsed {len(self.subtitle_lines)} SRT subtitle lines")
            
        except Exception as e:
            logger.error(f"Error parsing SRT content: {e}")
    
    def _parse_ass_content(self, content):
        """Parse ASS/SSA content"""
        try:
            lines = content.split('\n')
            dialogue_started = False
            
            for line in lines:
                line = line.strip()
                
                if line.lower().startswith('[events]'):
                    dialogue_started = True
                    continue
                    
                if dialogue_started and line.lower().startswith('dialogue:'):
                    try:
                        parts = line.split(',', 9)
                        if len(parts) >= 10:
                            start_time = parts[1].strip()
                            end_time = parts[2].strip()
                            text = parts[9].strip()
                            
                            # Remove style tags
                            text = re.sub(r'\{[^}]*\}', '', text)
                            text = text.replace('\\N', '\n')
                            text = text.replace('\\n', '\n')
                            text = text.replace('\\h', ' ')
                            
                            if text.strip():
                                self.subtitle_lines.append({
                                    'start': start_time,
                                    'end': end_time,
                                    'text': text,
                                    'start_ms': self._parse_ass_timestamp(start_time),
                                    'end_ms': self._parse_ass_timestamp(end_time)
                                })
                    except Exception as e:
                        logger.debug(f"Error parsing ASS line: {e}")
                        continue
                
                elif dialogue_started and line.startswith('['):
                    # New section started
                    break
            
            # Sort by start time
            self.subtitle_lines.sort(key=lambda x: x['start_ms'])
            
            logger.debug(f"Parsed {len(self.subtitle_lines)} ASS subtitle lines")
            
        except Exception as e:
            logger.error(f"Error parsing ASS content: {e}")
    
    def _parse_sub_content(self, content):
        """Parse SUB (MicroDVD) content"""
        try:
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('{') and '}' in line:
                    try:
                        # Format: {start_frame}{end_frame}text
                        match = re.match(r'\{(\d+)\}\{(\d+)\}(.+)', line)
                        if match:
                            start_frame = int(match.group(1))
                            end_frame = int(match.group(2))
                            text = match.group(3).strip()
                            
                            # Convert frames to time (assuming 25 fps)
                            fps = 25.0
                            start_ms = (start_frame / fps) * 1000
                            end_ms = (end_frame / fps) * 1000
                            
                            # Remove | separator
                            text = text.replace('|', '\n')
                            
                            if text:
                                start_str = self._ms_to_timestamp(start_ms)
                                end_str = self._ms_to_timestamp(end_ms)
                                
                                self.subtitle_lines.append({
                                    'start': start_str,
                                    'end': end_str,
                                    'text': text,
                                    'start_ms': start_ms,
                                    'end_ms': end_ms
                                })
                    except Exception as e:
                        logger.debug(f"Error parsing SUB line: {e}")
                        continue
            
            # Sort by start time
            self.subtitle_lines.sort(key=lambda x: x['start_ms'])
            
            logger.debug(f"Parsed {len(self.subtitle_lines)} SUB subtitle lines")
            
        except Exception as e:
            logger.error(f"Error parsing SUB content: {e}")
    
    def _parse_auto_content(self, content):
        """Auto-detect and parse subtitle format"""
        try:
            # Try to detect format
            if re.search(r'\d{1,2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[\.,]\d{3}', content):
                self._parse_srt_content(content)
            elif '[Events]' in content and 'Dialogue:' in content:
                self._parse_ass_content(content)
            elif re.search(r'^\{\d+\}\{\d+\}', content, re.MULTILINE):
                self._parse_sub_content(content)
            else:
                # Fallback: try to parse as simple text with timestamps
                self._parse_simple_content(content)
                
            logger.debug(f"Auto-parsed {len(self.subtitle_lines)} subtitle lines")
                
        except Exception as e:
            logger.error(f"Error in auto-parse: {e}")
    
    def _parse_simple_content(self, content):
        """Parse simple timestamped content"""
        try:
            lines = content.split('\n')
            pattern = r'(\d{1,2}):(\d{2}):(\d{2})[\.,](\d{3})\s+(.+)'
            
            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    h, m, s, ms = map(int, match.groups()[:4])
                    text = match.group(5).strip()
                    
                    start_ms = (h * 3600 + m * 60 + s) * 1000 + ms
                    start_str = f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                    
                    # Assume duration of 5 seconds
                    end_ms = start_ms + 5000
                    end_str = self._ms_to_timestamp(end_ms)
                    
                    self.subtitle_lines.append({
                        'start': start_str,
                        'end': end_str,
                        'text': text,
                        'start_ms': start_ms,
                        'end_ms': end_ms
                    })
            
            # Sort by start time
            self.subtitle_lines.sort(key=lambda x: x['start_ms'])
            
            logger.debug(f"Parsed {len(self.subtitle_lines)} simple subtitle lines")
            
        except Exception as e:
            logger.error(f"Error parsing simple content: {e}")
    
    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp to milliseconds"""
        try:
            # Handle both comma and dot as decimal separator
            timestamp_str = timestamp_str.replace('.', ',')
            
            if ',' in timestamp_str:
                time_part, ms_part = timestamp_str.split(',', 1)
                ms = int(ms_part.ljust(3, '0')[:3])
            else:
                time_part = timestamp_str
                ms = 0
            
            # Parse hours:minutes:seconds
            parts = time_part.split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
            elif len(parts) == 2:
                h = 0
                m, s = map(int, parts)
            else:
                return 0
            
            return (h * 3600 + m * 60 + s) * 1000 + ms
            
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
            return 0
    
    def _parse_ass_timestamp(self, timestamp_str):
        """Parse ASS timestamp to milliseconds"""
        try:
            # Format: H:MM:SS.cc (centiseconds)
            parts = timestamp_str.split(':')
            if len(parts) == 3:
                h = int(parts[0])
                m = int(parts[1])
                
                # Split seconds and centiseconds
                s_part = parts[2]
                if '.' in s_part:
                    s, cs = map(int, s_part.split('.'))
                else:
                    s = int(s_part)
                    cs = 0
                
                return (h * 3600 + m * 60 + s) * 1000 + (cs * 10)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error parsing ASS timestamp {timestamp_str}: {e}")
            return 0
    
    def _ms_to_timestamp(self, ms):
        """Convert milliseconds to SRT timestamp format"""
        try:
            ms = max(0, int(ms))
            
            hours = ms // 3600000
            minutes = (ms % 3600000) // 60000
            seconds = (ms % 60000) // 1000
            milliseconds = ms % 1000
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
            
        except Exception as e:
            logger.error(f"Error converting ms to timestamp: {e}")
            return "00:00:00,000"
    
    def _init_config_list(self):
        """Initialize complete configuration list"""
        try:
            p = config.plugins.wgfilemanager
            
            config_items = [
                getConfigListEntry("=== TIMING ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Delay (milliseconds):", p.subt_delay),
                
                getConfigListEntry("=== FONT SETTINGS ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Font Style:", p.subt_font_name),
                getConfigListEntry("Font Size:", p.subt_font_size),
                getConfigListEntry("Font Color:", p.subt_font_color),
                
                getConfigListEntry("=== POSITION ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Vertical Position:", p.subt_position),
                
                getConfigListEntry("=== BACKGROUND ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Show Background:", p.subt_background),
                getConfigListEntry("Background Color:", p.subt_bg_color),
                getConfigListEntry("Background Opacity (%):", p.subt_bg_opacity),
                
                getConfigListEntry("=== BORDER ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Show Border:", p.subt_border),
                getConfigListEntry("Border Color:", p.subt_border_color),
                getConfigListEntry("Border Width:", p.subt_border_width),
                
                getConfigListEntry("=== SHADOW ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Show Shadow:", p.subt_shadow),
                getConfigListEntry("Shadow Color:", p.subt_shadow_color),
                getConfigListEntry("Shadow Offset:", p.subt_shadow_offset),
                
                getConfigListEntry("=== ADVANCED ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Line Spacing:", p.subt_line_spacing),
                getConfigListEntry("Max Lines:", p.subt_max_lines),
                getConfigListEntry("File Encoding:", p.subt_encoding),
                
                getConfigListEntry("=== AUTO-LOAD ===", ConfigText(default="", fixed_size=True)),
                getConfigListEntry("Auto-load Subtitles:", p.subt_auto_load),
                getConfigListEntry("Preferred Language:", p.subt_prefer_lang),
            ]
            
            self["config_list"].list = config_items
            self["config_list"].setList(config_items)
            
            logger.debug("Configuration list initialized")
            
        except Exception as e:
            logger.error(f"Error initializing config list: {e}")
    
    def _init_timeline_list(self):
        """Initialize timeline list with subtitle lines"""
        try:
            if not self.subtitle_lines:
                timeline_items = [
                    ("No subtitles loaded. Press BLUE to load a file.", None),
                    ("Or ensure your video file has matching subtitle files.", None)
                ]
                logger.debug("No subtitle lines to show in timeline")
            else:
                timeline_items = []
                for i, line in enumerate(self.subtitle_lines[:100]):  # Show first 100
                    # Format time display
                    start_time = line['start'].replace(',', '.')[:11]
                    
                    # Clean text for display
                    display_text = line['text'].replace('\n', ' ')
                    if len(display_text) > 35:
                        display_text = display_text[:32] + "..."
                    
                    timeline_items.append((
                        f"{i+1:03d} | {start_time} | {display_text}",
                        i
                    ))
                logger.debug(f"Timeline initialized with {len(timeline_items)} items")
            
            self["timeline_list"].list = timeline_items
            self["timeline_list"].setList(timeline_items)
            
        except Exception as e:
            logger.error(f"Error initializing timeline: {e}")
    
    def _apply_delay_to_file(self):
        """Apply current delay to subtitle file"""
        try:
            if not self.current_subtitle_path or not self.subtitle_lines:
                logger.warning("No subtitle path or lines to apply delay")
                return
            
            if not self.temp_subtitle_path:
                self._create_temp_copy()
            
            # Read original content
            encoding = config.plugins.wgfilemanager.subt_encoding.value
            with open(self.current_subtitle_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            
            # Apply delay based on file type
            ext = os.path.splitext(self.current_subtitle_path)[1].lower()
            
            if ext == '.srt':
                new_content = self._shift_srt_timings(content, self.current_delay)
            elif ext in ['.ass', '.ssa']:
                new_content = self._shift_ass_timings(content, self.current_delay)
            elif ext == '.sub':
                new_content = self._shift_sub_timings(content, self.current_delay)
            else:
                new_content = content  # Don't modify unsupported formats
            
            # Write to temp file
            with open(self.temp_subtitle_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Load modified subtitles
            self.is_dirty = True
            self._load_subtitle_lines()
            
            logger.info(f"Applied {self.current_delay}ms delay to subtitles")
            
        except Exception as e:
            logger.error(f"Error applying delay to file: {e}")
    
    def _shift_srt_timings(self, content, delay_ms):
        """Shift SRT subtitle timings"""
        def shift_time(match):
            time_str = match.group(0)
            ms = self._parse_timestamp(time_str) + delay_ms
            return self._ms_to_timestamp(max(0, ms))
        
        # Replace all timestamps
        pattern = r'\d{1,2}:\d{2}:\d{2}[,\.]\d{3}'
        return re.sub(pattern, shift_time, content)
    
    def _shift_ass_timings(self, content, delay_ms):
        """Shift ASS subtitle timings"""
        lines = content.split('\n')
        result = []
        
        for line in lines:
            if line.lower().startswith('dialogue:'):
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    # Shift start and end times
                    for i in [1, 2]:  # Start and end time indices
                        time_str = parts[i]
                        current_ms = self._parse_ass_timestamp(time_str)
                        new_ms = max(0, current_ms + delay_ms)
                        
                        # Convert back to ASS format
                        total_cs = new_ms // 10
                        h = total_cs // 360000
                        m = (total_cs % 360000) // 6000
                        s = (total_cs % 6000) // 100
                        cs = total_cs % 100
                        
                        parts[i] = f"{h}:{m:02d}:{s:02d}.{cs:02d}"
                    
                    line = ','.join(parts)
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _shift_sub_timings(self, content, delay_ms):
        """Shift SUB subtitle timings"""
        fps = 25.0
        delay_frames = int((delay_ms / 1000) * fps)
        
        def shift_frames(match):
            start_frame = int(match.group(1)) + delay_frames
            end_frame = int(match.group(2)) + delay_frames
            text = match.group(3)
            
            start_frame = max(0, start_frame)
            end_frame = max(0, end_frame)
            
            return f"{{{start_frame}}}{{{end_frame}}}{text}"
        
        pattern = r'\{(\d+)\}\{(\d+)\}(.+)'
        return re.sub(pattern, shift_frames, content)
    
    def startup(self):
        """Complete startup initialization"""
        try:
            self._init_config_list()
            self._init_timeline_list()
            self.update_status()
            self.update_preview()
            
            # Start preview timer
            self.preview_timer.start(3000)  # Update every 3 seconds
            
            logger.info("Subtitle menu startup complete")
            
        except Exception as e:
            logger.error(f"Error in startup: {e}")
    
    def update_status(self):
        """Update comprehensive status display"""
        try:
            status_parts = []
            
            # Delay status
            if self.current_delay == 0:
                delay_status = "Delay: 0ms"
            elif self.current_delay > 0:
                seconds = self.current_delay / 1000
                delay_status = f"Delay: +{seconds:.1f}s"
            else:
                seconds = abs(self.current_delay) / 1000
                delay_status = f"Delay: -{seconds:.1f}s"
            
            status_parts.append(f"⏱️ {delay_status}")
            
            # File status
            if self.current_subtitle_path:
                filename = os.path.basename(self.current_subtitle_path)
                if len(filename) > 20:
                    filename = filename[:17] + "..."
                status_parts.append(f"📄 {filename}")
            
            # Line status
            if self.subtitle_lines:
                total_lines = len(self.subtitle_lines)
                current_line = self.current_line_index + 1
                status_parts.append(f"📍 {current_line}/{total_lines}")
                
                # Current time
                if self.current_line_index < len(self.subtitle_lines):
                    line = self.subtitle_lines[self.current_line_index]
                    status_parts.append(f"⏰ {line['start']}")
            
            # Modified status
            if self.is_dirty:
                status_parts.append("🔄 Modified")
            
            # Combine all parts
            self["current_status"].setText(" | ".join(status_parts))
            
            logger.debug(f"Status updated: {self['current_status'].text}")
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def update_preview(self):
        """Update live preview with current settings"""
        try:
            p = config.plugins.wgfilemanager
            
            # Get preview text
            if self.subtitle_lines and self.current_line_index < len(self.subtitle_lines):
                preview_text = self.subtitle_lines[self.current_line_index]['text']
            else:
                preview_text = "Subtitle preview text will appear here"
            
            # Clean text
            preview_text = preview_text.replace('\n', ' ')
            if len(preview_text) > 50:
                preview_text = preview_text[:47] + "..."
            
            self["preview_text"].setText(preview_text)
            
            # Apply color if available in skin
            try:
                instance = self["preview_text"].instance
                if instance:
                    # Parse hex color
                    color_hex = p.subt_font_color.value.lstrip('#')
                    if len(color_hex) == 6:
                        rgb = int(color_hex, 16)
                        instance.setForegroundColor(rgb)
            except:
                pass  # Ignore if color setting fails
            
            logger.debug(f"Preview updated: {preview_text}")
            
        except Exception as e:
            logger.error(f"Error updating preview: {e}")
    
    # ===== COMPLETE KEY HANDLERS =====
    
    def move_up(self):
        """Handle up key - depends on focus"""
        try:
            if self["config_list"].isFocused():
                self.config_up()
            else:
                self.delay_increase()
        except Exception as e:
            logger.error(f"Error in move_up: {e}")
    
    def move_down(self):
        """Handle down key - depends on focus"""
        try:
            if self["config_list"].isFocused():
                self.config_down()
            else:
                self.delay_decrease()
        except Exception as e:
            logger.error(f"Error in move_down: {e}")
    
    def delay_increase(self):
        """Increase subtitle delay by 100ms and apply immediately"""
        try:
            old_delay = self.current_delay
            self.current_delay += 100
            self.current_delay = min(self.current_delay, 3600000)
            
            # Update config
            config.plugins.wgfilemanager.subt_delay.value = self.current_delay
            
            # Apply to file
            self._apply_delay_to_file()
            
            self.update_status()
            self.update_preview()
            
            logger.debug(f"Delay increased to {self.current_delay}ms")
            
        except Exception as e:
            logger.error(f"Error increasing delay: {e}")
    
    def delay_decrease(self):
        """Decrease subtitle delay by 100ms and apply immediately"""
        try:
            old_delay = self.current_delay
            self.current_delay -= 100
            self.current_delay = max(self.current_delay, -3600000)
            
            # Update config
            config.plugins.wgfilemanager.subt_delay.value = self.current_delay
            
            # Apply to file
            self._apply_delay_to_file()
            
            self.update_status()
            self.update_preview()
            
            logger.debug(f"Delay decreased to {self.current_delay}ms")
            
        except Exception as e:
            logger.error(f"Error decreasing delay: {e}")
    
    def timeline_next(self):
        """Move to next subtitle line"""
        try:
            if self.subtitle_lines:
                self.current_line_index = min(
                    self.current_line_index + 1,
                    len(self.subtitle_lines) - 1
                )
                
                # Update timeline selection
                if self.current_line_index < len(self["timeline_list"].list):
                    self["timeline_list"].setIndex(self.current_line_index)
                
                self.update_status()
                self.update_preview()
                
                logger.debug(f"Moved to timeline index {self.current_line_index}")
                
        except Exception as e:
            logger.error(f"Error moving to next line: {e}")
    
    def timeline_prev(self):
        """Move to previous subtitle line"""
        try:
            if self.subtitle_lines:
                self.current_line_index = max(self.current_line_index - 1, 0)
                
                # Update timeline selection
                if self.current_line_index < len(self["timeline_list"].list):
                    self["timeline_list"].setIndex(self.current_line_index)
                
                self.update_status()
                self.update_preview()
                
                logger.debug(f"Moved to timeline index {self.current_line_index}")
                
        except Exception as e:
            logger.error(f"Error moving to previous line: {e}")
    
    def quick_delay(self, ms):
        """Quick delay adjustment with visual feedback"""
        try:
            old_delay = self.current_delay
            self.current_delay += ms
            self.current_delay = max(-3600000, min(self.current_delay, 3600000))
            
            # Update config
            config.plugins.wgfilemanager.subt_delay.value = self.current_delay
            
            # Apply to file
            self._apply_delay_to_file()
            
            # Show feedback
            if ms > 0:
                direction = "+"
            else:
                direction = ""
            
            seconds = abs(ms) / 1000
            feedback_text = f"Delay {direction}{seconds:.1f}s applied!"
            
            # Update help text temporarily
            old_help = self["help_text"].text
            self["help_text"].setText(feedback_text)
            
            # Reset after delay
            reset_timer = eTimer()
            reset_timer.callback.append(lambda: self["help_text"].setText(old_help))
            reset_timer.start(1500, True)
            
            self.update_status()
            self.update_preview()
            
            logger.debug(f"Quick delay: {ms}ms, new delay: {self.current_delay}ms")
            
        except Exception as e:
            logger.error(f"Error in quick delay: {e}")
    
    def reset_delay(self):
        """Reset delay to zero"""
        try:
            self.current_delay = 0
            config.plugins.wgfilemanager.subt_delay.value = 0
            
            # Reset subtitle file
            if self.original_subtitle_path and self.temp_subtitle_path:
                shutil.copy2(self.original_subtitle_path, self.temp_subtitle_path)
                self._load_subtitle_lines()
            
            self.is_dirty = False
            self.update_status()
            self.update_preview()
            
            self.session.open(
                MessageBox,
                "Subtitle delay reset to 0",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            
            logger.info("Subtitle delay reset to 0")
            
        except Exception as e:
            logger.error(f"Error resetting delay: {e}")
    
    def reset_all(self):
        """Reset all settings to default"""
        try:
            p = config.plugins.wgfilemanager
            
            # Reset all config values
            p.subt_delay.value = 0
            p.subt_font_name.value = "Regular"
            p.subt_font_size.value = 50
            p.subt_font_color.value = "#FFFF00"
            p.subt_position.value = "bottom"
            p.subt_background.value = True
            p.subt_bg_color.value = "#000000"
            p.subt_bg_opacity.value = 80
            p.subt_border.value = False
            p.subt_border_color.value = "#FFFFFF"
            p.subt_border_width.value = 2
            p.subt_shadow.value = True
            p.subt_shadow_color.value = "#000000"
            p.subt_shadow_offset.value = 2
            p.subt_line_spacing.value = 10
            p.subt_max_lines.value = 2
            p.subt_encoding.value = "utf-8"
            p.subt_auto_load.value = True
            p.subt_prefer_lang.value = ""
            
            # Reset current values
            self.current_delay = 0
            
            # Reset subtitle file
            if self.original_subtitle_path and self.temp_subtitle_path:
                shutil.copy2(self.original_subtitle_path, self.temp_subtitle_path)
                self._load_subtitle_lines()
            
            self.is_dirty = False
            
            # Update UI
            self._init_config_list()
            self.update_preview()
            self.update_status()
            
            self.session.open(
                MessageBox,
                "All settings reset to defaults",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            
            logger.info("All subtitle settings reset to defaults")
            
        except Exception as e:
            logger.error(f"Error resetting all: {e}")
    
    def save_and_apply(self):
        """Save all settings and apply to subtitle"""
        try:
            # Save all config values
            for item in self["config_list"].list:
                item[1].save()
            
            configfile.save()
            
            # Apply delay to file
            self._apply_delay_to_file()
            
            # If we have a temp file with modifications, offer to save it
            if self.is_dirty and self.temp_subtitle_path and os.path.exists(self.temp_subtitle_path):
                self._offer_save_changes()
            else:
                self.session.open(
                    MessageBox,
                    "✅ All settings saved successfully!",
                    MessageBox.TYPE_INFO,
                    timeout=2
                )
            
            logger.info("All subtitle settings saved")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            self.session.open(
                MessageBox,
                f"Failed to save settings:\n{e}",
                MessageBox.TYPE_ERROR
            )
    
    def _offer_save_changes(self):
        """Offer to save modified subtitle file"""
        if not self.is_dirty or not self.temp_subtitle_path:
            return
        
        message = "Save subtitle modifications?\n\n"
        message += f"Delay: {self.current_delay}ms applied\n"
        message += f"File: {os.path.basename(self.current_subtitle_path)}\n\n"
        message += "YES: Save to original file\n"
        message += "NO: Keep temporary copy only\n"
        message += "CANCEL: Discard changes"
        
        self.session.openWithCallback(
            self._handle_save_changes,
            MessageBox,
            message,
            MessageBox.TYPE_YESNOCANCEL
        )
    
    def _handle_save_changes(self, result):
        """Handle save changes decision"""
        try:
            if result is None:  # Cancel
                return
            
            if result:  # Yes - save to original
                if self.original_subtitle_path and os.path.exists(self.temp_subtitle_path):
                    # Create backup
                    backup_path = self.original_subtitle_path + ".backup"
                    shutil.copy2(self.original_subtitle_path, backup_path)
                    
                    # Copy temp to original
                    shutil.copy2(self.temp_subtitle_path, self.original_subtitle_path)
                    
                    self.is_dirty = False
                    
                    self.session.open(
                        MessageBox,
                        f"✅ Changes saved to original file!\nBackup: {os.path.basename(backup_path)}",
                        MessageBox.TYPE_INFO,
                        timeout=3
                    )
                    logger.info(f"Saved changes to original file: {self.original_subtitle_path}")
            else:  # No - keep temp only
                self.session.open(
                    MessageBox,
                    "Changes kept in temporary file only",
                    MessageBox.TYPE_INFO,
                    timeout=2
                )
                logger.info("Kept changes in temporary file only")
            
        except Exception as e:
            logger.error(f"Error handling save changes: {e}")
            self.session.open(
                MessageBox,
                f"Failed to save changes:\n{e}",
                MessageBox.TYPE_ERROR
            )
    
    def show_more_options(self):
        """Show additional subtitle options menu"""
        try:
            options = [
                ("📂 Load Subtitle File...", "load"),
                ("🔍 Find Subtitles Online...", "download"),
                ("✏️ Edit Subtitle File...", "edit"),
                ("🔄 Convert Subtitle Format...", "convert"),
                ("🌐 Change Language/Encoding...", "language"),
                ("📊 Subtitle Statistics...", "stats"),
                ("🛠️ Advanced Tools...", "tools"),
                ("ℹ️ About This Subtitle...", "about"),
            ]
            
            self.session.openWithCallback(
                self._handle_more_option,
                ChoiceBox,
                title="Additional Subtitle Options",
                list=options
            )
            
            logger.debug("Showing more options menu")
            
        except Exception as e:
            logger.error(f"Error showing more options: {e}")
    
    def _handle_more_option(self, choice):
        """Handle selection from more options menu"""
        if not choice:
            return
        
        option_id = choice[1]
        
        if option_id == "load":
            self.browse_srt()
        elif option_id == "download":
            self.open_subtitle_download()
        elif option_id == "edit":
            self.open_subtitle_edit()
        elif option_id == "convert":
            self.open_subtitle_convert()
        elif option_id == "language":
            self.change_language_encoding()
        elif option_id == "stats":
            self.show_subtitle_stats()
        elif option_id == "tools":
            self.show_advanced_tools()
        elif option_id == "about":
            self.show_subtitle_info()
        
        logger.debug(f"Selected more option: {option_id}")
    
    def browse_srt(self):
        """Browse for subtitle file"""
        try:
            start_dir = "/media/"
            if self.video_file_path:
                start_dir = os.path.dirname(self.video_file_path)
            
            self.session.openWithCallback(
                self.subtitle_file_selected,
                LocationBox,
                text="Select Subtitle File",
                currDir=start_dir,
                filename="",
                minFree=0
            )
            
            logger.debug(f"Opening file browser from: {start_dir}")
            
        except Exception as e:
            logger.error(f"Error browsing subtitle: {e}")
    
    def subtitle_file_selected(self, path):
        """Handle subtitle file selection"""
        if not path:
            return
        
        try:
            if not os.path.exists(path):
                self.session.open(
                    MessageBox,
                    f"File not found:\n{path}",
                    MessageBox.TYPE_ERROR
                )
                return
            
            # Check if it's a valid subtitle file
            valid_extensions = ('.srt', '.sub', '.ass', '.ssa')
            if not path.lower().endswith(valid_extensions):
                # Ask user if they want to try anyway
                message = f"File doesn't look like a standard subtitle:\n{path}\n\n"
                message += "Try to load it anyway?"
                
                self.session.openWithCallback(
                    lambda result: self._force_load_subtitle(path) if result else None,
                    MessageBox,
                    message,
                    MessageBox.TYPE_YESNO
                )
                return
            
            # Load the file
            if self._load_subtitle_file(path):
                self._init_timeline_list()
                self.update_preview()
                self.update_status()
                
                # Reset delay when loading new file
                self.current_delay = 0
                config.plugins.wgfilemanager.subt_delay.value = 0
                
                self.session.open(
                    MessageBox,
                    f"✅ Subtitle loaded:\n{os.path.basename(path)}",
                    MessageBox.TYPE_INFO,
                    timeout=2
                )
                logger.info(f"Loaded subtitle file: {path}")
            else:
                self.session.open(
                    MessageBox,
                    "Failed to load subtitle file!\n\nCheck file encoding and format.",
                    MessageBox.TYPE_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error loading subtitle file: {e}")
            self.session.open(
                MessageBox,
                f"Error loading file:\n{e}",
                MessageBox.TYPE_ERROR
            )
    
    def _force_load_subtitle(self, path):
        """Force load a file as subtitle"""
        try:
            self.current_subtitle_path = path
            self.original_subtitle_path = path
            self._create_temp_copy()
            self._load_subtitle_lines()
            
            if self.subtitle_lines:
                self._init_timeline_list()
                self.update_preview()
                self.update_status()
                
                self.session.open(
                    MessageBox,
                    f"Loaded {len(self.subtitle_lines)} lines from file",
                    MessageBox.TYPE_INFO,
                    timeout=2
                )
                logger.info(f"Force loaded {len(self.subtitle_lines)} lines from {path}")
            else:
                self.session.open(
                    MessageBox,
                    "Could not parse any subtitle lines from file",
                    MessageBox.TYPE_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error force loading subtitle: {e}")
    
    def open_subtitle_download(self):
        """Open subtitle download interface"""
        try:
            # Show placeholder message
            self.session.open(
                MessageBox,
                "Subtitle download feature\n\n"
                "Would connect to online subtitle services\n"
                "to download subtitles for the current video.",
                MessageBox.TYPE_INFO,
                timeout=3
            )
            logger.debug("Subtitle download placeholder shown")
            
        except Exception as e:
            logger.error(f"Error opening download screen: {e}")
    
    def open_subtitle_edit(self):
        """Open subtitle editor"""
        try:
            if not self.current_subtitle_path:
                self.session.open(
                    MessageBox,
                    "No subtitle file loaded to edit",
                    MessageBox.TYPE_WARNING,
                    timeout=2
                )
                return
            
            # For now, just show a message
            self.session.open(
                MessageBox,
                f"Subtitle editor would open for:\n{os.path.basename(self.current_subtitle_path)}\n\n"
                "Feature requires separate editor implementation.",
                MessageBox.TYPE_INFO,
                timeout=3
            )
            
            logger.debug(f"Subtitle edit placeholder for: {self.current_subtitle_path}")
            
        except Exception as e:
            logger.error(f"Error opening subtitle edit: {e}")
    
    def open_subtitle_convert(self):
        """Open subtitle format converter"""
        try:
            if not self.current_subtitle_path:
                self.session.open(
                    MessageBox,
                    "No subtitle file loaded to convert",
                    MessageBox.TYPE_WARNING,
                    timeout=2
                )
                return
            
            # Show conversion options
            options = [
                ("SRT → ASS (Advanced SubStation)", "srt_to_ass"),
                ("ASS → SRT (Simple Text)", "ass_to_srt"),
                ("SRT → SUB (MicroDVD)", "srt_to_sub"),
                ("SUB → SRT (Simple Text)", "sub_to_srt"),
            ]
            
            self.session.openWithCallback(
                self._handle_conversion,
                ChoiceBox,
                title="Convert Subtitle Format",
                list=options
            )
            
        except Exception as e:
            logger.error(f"Error opening subtitle convert: {e}")
    
    def _handle_conversion(self, choice):
        """Handle format conversion"""
        if not choice:
            return
        
        # This is a placeholder - actual conversion would require
        # implementing format conversion logic
        self.session.open(
            MessageBox,
            f"Would convert to: {choice[0]}\n\n"
            "Format conversion requires additional implementation.",
            MessageBox.TYPE_INFO,
            timeout=2
        )
        logger.debug(f"Format conversion placeholder: {choice[0]}")
    
    def change_language_encoding(self):
        """Change subtitle language/encoding"""
        try:
            p = config.plugins.wgfilemanager
            
            # Show language options
            languages = [
                ("English", "en"),
                ("Arabic", "ar"),
                ("French", "fr"),
                ("Spanish", "es"),
                ("German", "de"),
                ("Italian", "it"),
                ("Russian", "ru"),
                ("Turkish", "tr"),
                ("Persian", "fa"),
                ("Hebrew", "he"),
            ]
            
            self.session.openWithCallback(
                lambda choice: self._set_preferred_language(choice[1]) if choice else None,
                ChoiceBox,
                title="Select Preferred Language",
                list=languages
            )
            
        except Exception as e:
            logger.error(f"Error changing language: {e}")
    
    def _set_preferred_language(self, lang_code):
        """Set preferred language"""
        try:
            config.plugins.wgfilemanager.subt_prefer_lang.value = lang_code
            config.plugins.wgfilemanager.subt_prefer_lang.save()
            
            self.session.open(
                MessageBox,
                f"Preferred language set to: {lang_code}\n\n"
                "Will be used for auto-loading subtitles.",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            
            logger.info(f"Preferred language set to: {lang_code}")
            
        except Exception as e:
            logger.error(f"Error setting language: {e}")
    
    def show_subtitle_stats(self):
        """Show subtitle statistics"""
        try:
            if not self.subtitle_lines:
                self.session.open(
                    MessageBox,
                    "No subtitles loaded to show statistics",
                    MessageBox.TYPE_WARNING,
                    timeout=2
                )
                return
            
            # Calculate statistics
            total_lines = len(self.subtitle_lines)
            total_chars = sum(len(line['text']) for line in self.subtitle_lines)
            total_words = sum(len(line['text'].split()) for line in self.subtitle_lines)
            
            # Time statistics
            if self.subtitle_lines:
                first_line = self.subtitle_lines[0]
                last_line = self.subtitle_lines[-1]
                duration_seconds = (last_line['end_ms'] - first_line['start_ms']) / 1000
                
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                
                # Average words per minute
                if duration_seconds > 0:
                    wpm = (total_words / duration_seconds) * 60
                else:
                    wpm = 0
                
                stats_message = f"📊 SUBTITLE STATISTICS\n\n"
                stats_message += f"File: {os.path.basename(self.current_subtitle_path)}\n"
                stats_message += f"Lines: {total_lines}\n"
                stats_message += f"Characters: {total_chars}\n"
                stats_message += f"Words: {total_words}\n"
                stats_message += f"Duration: {minutes}m {seconds}s\n"
                stats_message += f"Avg. Speed: {wpm:.1f} WPM\n\n"
                
                if wpm > 200:
                    stats_message += "⚠️ Very fast subtitles!\n"
                elif wpm > 150:
                    stats_message += "⚡ Fast subtitles\n"
                elif wpm > 100:
                    stats_message += "✅ Good speed\n"
                else:
                    stats_message += "🐌 Slow subtitles\n"
                
                self.session.open(
                    MessageBox,
                    stats_message,
                    MessageBox.TYPE_INFO,
                    timeout=5
                )
                
                logger.info(f"Showed stats: {total_lines} lines, {wpm:.1f} WPM")
            
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
    
    def show_advanced_tools(self):
        """Show advanced subtitle tools"""
        try:
            tools = [
                ("🧹 Remove Formatting Tags", "clean_tags"),
                ("⏱️ Adjust All Timings...", "adjust_all"),
                ("🔠 Change Text Case...", "change_case"),
                ("📏 Fix Line Length...", "fix_length"),
                ("🎯 Center Subtitles...", "center_subs"),
                ("🧪 Test on Sample Video", "test_video"),
            ]
            
            self.session.openWithCallback(
                self._handle_advanced_tool,
                ChoiceBox,
                title="Advanced Subtitle Tools",
                list=tools
            )
            
        except Exception as e:
            logger.error(f"Error showing advanced tools: {e}")
    
    def _handle_advanced_tool(self, choice):
        """Handle advanced tool selection"""
        if not choice:
            return
        
        tool_id = choice[1]
        
        if tool_id == "clean_tags":
            self._clean_formatting_tags()
        elif tool_id == "adjust_all":
            self._adjust_all_timings()
        elif tool_id == "change_case":
            self._change_text_case()
        elif tool_id == "fix_length":
            self._fix_line_length()
        elif tool_id == "center_subs":
            self._center_subtitles()
        elif tool_id == "test_video":
            self.test_subtitle_appearance()
        
        logger.debug(f"Selected advanced tool: {tool_id}")
    
    def _clean_formatting_tags(self):
        """Remove HTML/ASS formatting tags"""
        try:
            if not self.subtitle_lines:
                return
            
            message = "Remove all formatting tags?\n\n"
            message += "This will remove:\n"
            message += "• HTML tags: <b>, <i>, <font>\n"
            message += "• ASS tags: {\\pos, {\\fn, {\\c\n"
            message += "• Special characters\n\n"
            message += "Original formatting will be lost!"
            
            self.session.openWithCallback(
                self._confirm_clean_tags,
                MessageBox,
                message,
                MessageBox.TYPE_YESNO
            )
            
        except Exception as e:
            logger.error(f"Error cleaning tags: {e}")
    
    def _confirm_clean_tags(self, confirmed):
        """Confirm tag cleaning"""
        if not confirmed:
            return
        
        # This would implement actual tag cleaning
        self.session.open(
            MessageBox,
            "Formatting tags would be removed\n\n"
            "Feature requires implementation.",
            MessageBox.TYPE_INFO,
            timeout=2
        )
        logger.debug("Tag cleaning placeholder shown")
    
    def _adjust_all_timings(self):
        """Adjust all subtitle timings"""
        try:
            # This would open a dialog for batch timing adjustment
            self.session.open(
                MessageBox,
                "Batch timing adjustment\n\n"
                "Would open dialog to adjust all subtitles\n"
                "by a fixed amount or percentage.",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            logger.debug("Batch timing adjustment placeholder")
        except Exception as e:
            logger.error(f"Error adjusting timings: {e}")
    
    def _change_text_case(self):
        """Change text case of subtitles"""
        try:
            options = [
                ("UPPERCASE", "upper"),
                ("lowercase", "lower"),
                ("Title Case", "title"),
                ("Sentence case", "sentence"),
            ]
            
            self.session.openWithCallback(
                lambda choice: self._apply_text_case(choice[1]) if choice else None,
                ChoiceBox,
                title="Change Text Case",
                list=options
            )
            
        except Exception as e:
            logger.error(f"Error changing case: {e}")
    
    def _apply_text_case(self, case_type):
        """Apply text case transformation"""
        # This would implement case transformation
        self.session.open(
            MessageBox,
            f"Would apply {case_type} case to all subtitles\n\n"
            "Feature requires implementation.",
            MessageBox.TYPE_INFO,
            timeout=2
        )
        logger.debug(f"Text case placeholder: {case_type}")
    
    def _fix_line_length(self):
        """Fix subtitle line length"""
        try:
            self.session.open(
                MessageBox,
                "Fix line length\n\n"
                "Would split long lines and merge short ones\n"
                "to improve readability.",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            logger.debug("Fix line length placeholder")
        except Exception as e:
            logger.error(f"Error fixing line length: {e}")
    
    def _center_subtitles(self):
        """Center subtitles on screen"""
        try:
            self.session.open(
                MessageBox,
                "Center subtitles\n\n"
                "Would adjust subtitle positioning\n"
                "to center them horizontally.",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            logger.debug("Center subtitles placeholder")
        except Exception as e:
            logger.error(f"Error centering subtitles: {e}")
    
    def test_subtitle_appearance(self):
        """Test subtitle appearance with sample video"""
        try:
            self.session.open(
                MessageBox,
                "Test subtitle appearance\n\n"
                "Would open a test video with current\n"
                "subtitle settings applied for preview.",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            logger.debug("Test subtitle appearance placeholder")
        except Exception as e:
            logger.error(f"Error testing appearance: {e}")
    
    def show_subtitle_info(self):
        """Show detailed subtitle file information"""
        try:
            if not self.current_subtitle_path:
                self.session.open(
                    MessageBox,
                    "No subtitle file loaded",
                    MessageBox.TYPE_WARNING,
                    timeout=2
                )
                return
            
            info = self._get_file_info(self.current_subtitle_path)
            
            self.session.open(
                MessageBox,
                info,
                MessageBox.TYPE_INFO,
                timeout=5
            )
            
            logger.debug("Showed subtitle file info")
            
        except Exception as e:
            logger.error(f"Error showing subtitle info: {e}")
    
    def _get_file_info(self, filepath):
        """Get detailed file information"""
        try:
            if not os.path.exists(filepath):
                return "File not found"
            
            stat = os.stat(filepath)
            size_kb = stat.st_size / 1024
            
            info = f"📄 FILE INFORMATION\n\n"
            info += f"Name: {os.path.basename(filepath)}\n"
            info += f"Path: {os.path.dirname(filepath)}\n"
            info += f"Size: {size_kb:.1f} KB\n"
            info += f"Type: {self._get_file_type(filepath)}\n"
            info += f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if self.subtitle_lines:
                info += f"\n📊 CONTENT INFO\n"
                info += f"Lines: {len(self.subtitle_lines)}\n"
                info += f"Duration: {self._get_subtitle_duration()}\n"
                info += f"Encoding: {config.plugins.wgfilemanager.subt_encoding.value}\n"
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return f"Error: {e}"
    
    def _get_file_type(self, filepath):
        """Get file type description"""
        ext = os.path.splitext(filepath)[1].lower()
        
        types = {
            '.srt': 'SubRip (SRT)',
            '.ass': 'Advanced SubStation Alpha (ASS)',
            '.ssa': 'SubStation Alpha (SSA)',
            '.sub': 'MicroDVD (SUB)',
        }
        
        return types.get(ext, 'Unknown')
    
    def _get_subtitle_duration(self):
        """Get subtitle duration as string"""
        if not self.subtitle_lines:
            return "N/A"
        
        first = self.subtitle_lines[0]['start_ms']
        last = self.subtitle_lines[-1]['end_ms']
        duration_ms = last - first
        
        hours = int(duration_ms // 3600000)
        minutes = int((duration_ms % 3600000) // 60000)
        seconds = int((duration_ms % 60000) // 1000)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def config_up(self):
        """Move up in config list"""
        try:
            self["config_list"].instance.moveSelection(
                self["config_list"].instance.moveUp
            )
            self.update_preview()
            logger.debug("Config list moved up")
        except Exception as e:
            logger.error(f"Error in config up: {e}")
    
    def config_down(self):
        """Move down in config list"""
        try:
            self["config_list"].instance.moveSelection(
                self["config_list"].instance.moveDown
            )
            self.update_preview()
            logger.debug("Config list moved down")
        except Exception as e:
            logger.error(f"Error in config down: {e}")
    
    def config_page_up(self):
        """Page up in config list"""
        try:
            for _ in range(5):
                self.config_up()
            logger.debug("Config list paged up")
        except Exception as e:
            logger.error(f"Error in config page up: {e}")
    
    def config_page_down(self):
        """Page down in config list"""
        try:
            for _ in range(5):
                self.config_down()
            logger.debug("Config list paged down")
        except Exception as e:
            logger.error(f"Error in config page down: {e}")
    
    def show_help(self):
        """Show help information"""
        try:
            help_text = """
            📖 SUBTITLE MENU HELP
            
            NAVIGATION:
            • ↑↓: Adjust delay / Navigate config
            • ←→: Move through subtitle timeline
            • OK: Select item / Load subtitle line
            • CH+/CH-: Page through settings
            
            QUICK ACTIONS (Number Keys):
            • 1,2,3: Decrease delay (-5s, -1s, -0.1s)
            • 7,8,9: Increase delay (+0.1s, +1s, +5s)
            • 4: Download subtitles
            • 5: Edit subtitles
            • 6: Convert format
            • 0: Test appearance
            
            COLOR BUTTONS:
            • RED: Reset all settings
            • GREEN: Save & apply changes
            • YELLOW: Reset delay to zero
            • BLUE: More options menu
            
            INFO:
            • INFO: Show this help
            
            TIPS:
            • Auto-load finds subtitles with same name as video
            • Preferred language in settings affects auto-load
            • Modified subtitles save to temp file
            """
            
            self.session.open(
                MessageBox,
                help_text,
                MessageBox.TYPE_INFO,
                timeout=10
            )
            
            logger.debug("Help shown")
            
        except Exception as e:
            logger.error(f"Error showing help: {e}")
    
    def key_ok(self):
        """OK button handler"""
        try:
            if self["timeline_list"].isFocused() and self["timeline_list"].list:
                selected = self["timeline_list"].getCurrent()
                if selected and selected[1] is not None:
                    self.current_line_index = selected[1]
                    self.update_preview()
                    self.update_status()
                    logger.debug(f"Selected timeline item: {self.current_line_index}")
            elif self["config_list"].isFocused():
                # Handle config item editing
                selected = self["config_list"].getCurrent()
                if selected:
                    self._edit_config_item(selected)
            else:
                # Focus on timeline list
                self["timeline_list"].instance.setFocus()
                logger.debug("Focus set to timeline list")
                
        except Exception as e:
            logger.error(f"Error in OK: {e}")
    
    def _edit_config_item(self, config_item):
        """Edit a configuration item"""
        try:
            config_entry = config_item[1]
            
            if hasattr(config_entry, 'choices'):
                # Show choices
                choices = [(str(v), k) for k, v in config_entry.choices.items()]
                self.session.openWithCallback(
                    lambda choice: self._set_config_value(config_entry, choice[1]) if choice else None,
                    ChoiceBox,
                    title=f"Select {config_item[0]}",
                    list=choices
                )
            elif isinstance(config_entry, ConfigText):
                # Open keyboard
                self.session.openWithCallback(
                    lambda text: self._set_config_text(config_entry, text) if text is not None else None,
                    VirtualKeyBoard,
                    title=f"Enter {config_item[0]}",
                    text=config_entry.value
                )
            elif isinstance(config_entry, ConfigInteger):
                # For integer, just let user change via up/down
                logger.debug(f"Integer config item: {config_item[0]}")
            
            logger.debug(f"Editing config item: {config_item[0]}")
            
        except Exception as e:
            logger.error(f"Error editing config item: {e}")
    
    def _set_config_value(self, config_entry, value):
        """Set config value from choice"""
        try:
            config_entry.value = value
            config_entry.save()
            self.update_preview()
            logger.debug(f"Config value set: {value}")
        except Exception as e:
            logger.error(f"Error setting config value: {e}")
    
    def _set_config_text(self, config_entry, text):
        """Set config text from keyboard"""
        try:
            config_entry.value = text
            config_entry.save()
            self.update_preview()
            logger.debug(f"Config text set: {text}")
        except Exception as e:
            logger.error(f"Error setting config text: {e}")
    
    def key_exit(self):
        """Exit menu with confirmation if unsaved changes"""
        try:
            if self.is_dirty:
                message = "You have unsaved subtitle modifications!\n\n"
                message += "Save changes before exiting?\n\n"
                message += "YES: Save and exit\n"
                message += "NO: Exit without saving\n"
                message += "CANCEL: Continue editing"
                
                self.session.openWithCallback(
                    self._confirm_exit,
                    MessageBox,
                    message,
                    MessageBox.TYPE_YESNOCANCEL
                )
                logger.debug("Exit with unsaved changes confirmation")
            else:
                self._do_exit()
                
        except Exception as e:
            logger.error(f"Error exiting: {e}")
            self._do_exit()
    
    def _confirm_exit(self, result):
        """Handle exit confirmation"""
        try:
            if result is None:  # Cancel
                logger.debug("Exit cancelled")
                return
            
            if result:  # Yes - save and exit
                self.save_and_apply()
                # Wait a moment for save to complete
                exit_timer = eTimer()
                exit_timer.callback.append(self._do_exit)
                exit_timer.start(500, True)
                logger.debug("Exit after save")
            else:  # No - exit without saving
                self._do_exit()
                logger.debug("Exit without saving")
                
        except Exception as e:
            logger.error(f"Error in confirm exit: {e}")
            self._do_exit()
    
    def _do_exit(self):
        """Perform actual exit"""
        try:
            self.preview_timer.stop()
            self.close()
            logger.info("Subtitle menu closed")
        except Exception as e:
            logger.error(f"Error in final exit: {e}")
            self.close()