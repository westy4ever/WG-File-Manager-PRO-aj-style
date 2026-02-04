"""
Subtitle Manager - Complete Implementation for EnigmaPlayer
Full subtitle management with config, auto-load, and multi-format support
"""

import os
import re
import logging
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText

try:
    from ..utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class SubtitleManager:
    """Complete subtitle manager for EnigmaPlayer with full feature set"""
    
    def __init__(self, session):
        self.session = session
        self.current_subtitle = None
        self.video_file = None
        self.active = False
        self.auto_load = True
        self.subtitle_lines = []
        self.current_line_index = 0
        self.current_delay = 0  # milliseconds
        
        # Initialize configuration
        self._init_config()
        
        # Load current settings from config
        self._load_config()
        
        logger.info("SubtitleManager initialized with full feature set")
    
    def _init_config(self):
        """Initialize all subtitle configuration parameters"""
        try:
            if not hasattr(config.plugins, 'wgfilemanager'):
                config.plugins.wgfilemanager = ConfigSubsection()
                logger.info("Created wgfilemanager config subsection")
            
            p = config.plugins.wgfilemanager
            
            # Subtitle timing settings
            if not hasattr(p, 'subtitle_delay'):
                p.subtitle_delay = ConfigInteger(default=0, limits=(-3600000, 3600000))
                logger.debug("Created subtitle_delay config")
            
            # Appearance settings
            if not hasattr(p, 'subtitle_font_size'):
                p.subtitle_font_size = ConfigSelection(default="24", choices=[
                    ("20", "Small (20)"),
                    ("24", "Medium (24)"),
                    ("28", "Large (28)"),
                    ("32", "Extra Large (32)"),
                    ("36", "Huge (36)"),
                ])
            
            if not hasattr(p, 'subtitle_font_color'):
                p.subtitle_font_color = ConfigSelection(default="#FFFFFF", choices=[
                    ("#FFFFFF", "White"),
                    ("#FFFF00", "Yellow"),
                    ("#00FFFF", "Cyan"),
                    ("#00FF00", "Green"),
                    ("#FF0000", "Red"),
                    ("#FF00FF", "Magenta"),
                    ("#FFA500", "Orange"),
                    ("#ADD8E6", "Light Blue"),
                ])
            
            if not hasattr(p, 'subtitle_bg_enabled'):
                p.subtitle_bg_enabled = ConfigYesNo(default=True)
            
            if not hasattr(p, 'subtitle_bg_color'):
                p.subtitle_bg_color = ConfigSelection(default="#000000", choices=[
                    ("#000000", "Black"),
                    ("#333333", "Dark Gray"),
                    ("#666666", "Gray"),
                    ("#000080", "Dark Blue"),
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
            
            # Position settings
            if not hasattr(p, 'subtitle_position'):
                p.subtitle_position = ConfigSelection(default="bottom", choices=[
                    ("top", "Top"),
                    ("center_top", "Center Top"),
                    ("center", "Center"),
                    ("center_bottom", "Center Bottom"),
                    ("bottom", "Bottom"),
                ])
            
            # Encoding settings
            if not hasattr(p, 'subtitle_encoding'):
                p.subtitle_encoding = ConfigSelection(default="utf-8", choices=[
                    ("utf-8", "UTF-8"),
                    ("latin-1", "Latin-1"),
                    ("cp1252", "Western (CP1252)"),
                    ("cp1256", "Arabic (CP1256)"),
                    ("cp1251", "Cyrillic (CP1251)"),
                    ("gbk", "Chinese GBK"),
                    ("big5", "Traditional Chinese"),
                ])
            
            # Auto-load settings
            if not hasattr(p, 'subtitle_auto_load'):
                p.subtitle_auto_load = ConfigYesNo(default=True)
            
            if not hasattr(p, 'subtitle_preferred_lang'):
                p.subtitle_preferred_lang = ConfigText(default="", visible_width=20, fixed_size=False)
            
            # Advanced settings
            if not hasattr(p, 'subtitle_line_spacing'):
                p.subtitle_line_spacing = ConfigInteger(default=5, limits=(0, 50))
            
            if not hasattr(p, 'subtitle_max_lines'):
                p.subtitle_max_lines = ConfigInteger(default=2, limits=(1, 5))
            
            if not hasattr(p, 'subtitle_border'):
                p.subtitle_border = ConfigYesNo(default=False)
            
            if not hasattr(p, 'subtitle_shadow'):
                p.subtitle_shadow = ConfigYesNo(default=True)
            
            logger.info("All subtitle configuration parameters initialized")
            
        except Exception as e:
            logger.error(f"Error initializing subtitle config: {e}")
            raise
    
    def _load_config(self):
        """Load current configuration values"""
        try:
            p = config.plugins.wgfilemanager
            
            self.current_delay = p.subtitle_delay.value
            self.auto_load = p.subtitle_auto_load.value
            self.encoding = p.subtitle_encoding.value
            
            logger.debug(f"Loaded config: delay={self.current_delay}, auto_load={self.auto_load}")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Set defaults
            self.current_delay = 0
            self.auto_load = True
            self.encoding = "utf-8"
    
    # ===== Core Subtitle Methods =====
    
    def is_active(self):
        """Check if subtitle is active"""
        return self.active and self.current_subtitle is not None
    
    def enable(self):
        """Enable subtitle display"""
        if self.current_subtitle:
            self.active = True
            logger.info(f"Subtitle enabled: {os.path.basename(self.current_subtitle)}")
            return True
        else:
            logger.warning("No subtitle loaded to enable")
            return False
    
    def disable(self):
        """Disable subtitle display"""
        self.active = False
        logger.info("Subtitle disabled")
    
    def stop(self):
        """Stop subtitle (alias for disable)"""
        self.disable()
    
    def toggle_subtitles(self):
        """Toggle subtitle on/off"""
        if self.is_active():
            self.disable()
            logger.info("Subtitles toggled OFF")
            return False
        else:
            success = self.enable()
            logger.info(f"Subtitles toggled ON: {success}")
            return success
    
    # ===== File Management =====
    
    def auto_load_subtitle(self, service_ref):
        """Automatically load subtitle for service"""
        if not self.auto_load:
            logger.debug("Auto-load disabled in config")
            return False
        
        try:
            # Get file path from service reference
            if hasattr(service_ref, 'getPath'):
                file_path = service_ref.getPath()
            else:
                file_path = str(service_ref)
            
            if not file_path or not os.path.exists(file_path):
                logger.debug("No valid file path for auto-load")
                return False
            
            self.video_file = file_path
            logger.info(f"Auto-loading subtitles for: {os.path.basename(file_path)}")
            
            # Find matching subtitle files
            subtitles = self.find_local_subtitles(file_path)
            
            if subtitles:
                # Try to find preferred language
                preferred_lang = config.plugins.wgfilemanager.subtitle_preferred_lang.value.lower()
                selected_subtitle = None
                
                if preferred_lang:
                    for sub in subtitles:
                        sub_lang = sub.get('language', '').lower()
                        if preferred_lang in sub_lang:
                            selected_subtitle = sub['path']
                            logger.info(f"Found preferred language: {preferred_lang}")
                            break
                
                # Fallback to first subtitle
                if not selected_subtitle:
                    selected_subtitle = subtitles[0]['path']
                
                # Load the subtitle
                if self.load_subtitle(selected_subtitle):
                    logger.info(f"Auto-loaded subtitle: {os.path.basename(selected_subtitle)}")
                    
                    # Apply any existing delay
                    if self.current_delay != 0:
                        self._apply_delay_to_subtitle()
                    
                    return True
                else:
                    logger.error(f"Failed to load subtitle: {selected_subtitle}")
                    return False
            else:
                logger.debug(f"No subtitle files found for: {os.path.basename(file_path)}")
                return False
                
        except Exception as e:
            logger.error(f"Error in auto_load_subtitle: {e}")
            return False
    
    def find_local_subtitles(self, video_path):
        """Find subtitle files for video with language detection"""
        try:
            subtitles = []
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            
            if not os.path.isdir(video_dir):
                logger.warning(f"Video directory not found: {video_dir}")
                return []
            
            # Supported subtitle extensions
            subtitle_extensions = ['.srt', '.sub', '.ass', '.ssa', '.vtt']
            
            for file in os.listdir(video_dir):
                file_lower = file.lower()
                
                # Check if file is a subtitle
                if any(file_lower.endswith(ext) for ext in subtitle_extensions):
                    # Check if video name appears in subtitle filename
                    video_lower = video_name.lower()
                    file_without_ext = os.path.splitext(file_lower)[0]
                    
                    # Match patterns:
                    # 1. Exact match: video.srt
                    # 2. With language: video.en.srt, video.ar.srt
                    # 3. Contains video name
                    if (video_lower in file_without_ext or 
                        file_without_ext.startswith(video_lower)):
                        
                        full_path = os.path.join(video_dir, file)
                        language = self._detect_language(file)
                        
                        subtitles.append({
                            'path': full_path,
                            'name': file,
                            'language': language,
                            'size': os.path.getsize(full_path) if os.path.exists(full_path) else 0
                        })
            
            # Sort by language preference if set
            preferred_lang = config.plugins.wgfilemanager.subtitle_preferred_lang.value.lower()
            if preferred_lang and subtitles:
                # Move preferred language to front
                preferred = []
                others = []
                
                for sub in subtitles:
                    if preferred_lang in sub['language'].lower():
                        preferred.append(sub)
                    else:
                        others.append(sub)
                
                subtitles = preferred + others
            
            logger.info(f"Found {len(subtitles)} subtitle files for {os.path.basename(video_path)}")
            return subtitles
            
        except Exception as e:
            logger.error(f"Error finding local subtitles: {e}")
            return []
    
    def _detect_language(self, filename):
        """Detect language from filename"""
        try:
            filename_lower = filename.lower()
            
            language_patterns = {
                'Arabic': ['arabic', 'ara', '.ar.', 'arab', 'العربية'],
                'English': ['english', 'eng', '.en.', 'en_', '_en'],
                'French': ['french', 'fre', '.fr.', 'fr_', '_fr'],
                'Spanish': ['spanish', 'spa', '.es.', 'es_', '_es'],
                'German': ['german', 'ger', '.de.', 'de_', '_de'],
                'Italian': ['italian', 'ita', '.it.', 'it_', '_it'],
                'Turkish': ['turkish', 'tur', '.tr.', 'tr_', '_tr'],
                'Persian': ['persian', 'per', '.fa.', 'fa_', '_fa', 'فارسی'],
                'Hebrew': ['hebrew', 'heb', '.he.', 'he_', '_he', 'עברית'],
                'Russian': ['russian', 'rus', '.ru.', 'ru_', '_ru'],
                'Chinese': ['chinese', 'chi', '.zh.', 'zh_', '_zh', '.cn.'],
                'Japanese': ['japanese', 'jpn', '.ja.', 'ja_', '_ja'],
                'Korean': ['korean', 'kor', '.ko.', 'ko_', '_ko'],
            }
            
            for language, patterns in language_patterns.items():
                for pattern in patterns:
                    if pattern in filename_lower:
                        return language
            
            # Check for ISO language codes
            iso_codes = {
                'ar': 'Arabic', 'en': 'English', 'fr': 'French',
                'es': 'Spanish', 'de': 'German', 'it': 'Italian',
                'tr': 'Turkish', 'fa': 'Persian', 'he': 'Hebrew',
                'ru': 'Russian', 'zh': 'Chinese', 'ja': 'Japanese',
                'ko': 'Korean',
            }
            
            for code, language in iso_codes.items():
                pattern = f".{code}."
                if pattern in filename_lower:
                    return language
            
            return 'Unknown'
            
        except Exception as e:
            logger.debug(f"Language detection error: {e}")
            return 'Unknown'
    
    def load_subtitle(self, subtitle_path):
        """Load subtitle file with validation"""
        try:
            if not os.path.exists(subtitle_path):
                logger.error(f"Subtitle file not found: {subtitle_path}")
                return False
            
            # Validate file
            if os.path.getsize(subtitle_path) == 0:
                logger.error(f"Subtitle file is empty: {subtitle_path}")
                return False
            
            # Try to parse the subtitle
            success = self._parse_subtitle_file(subtitle_path)
            
            if success:
                self.current_subtitle = subtitle_path
                self.active = True
                logger.info(f"Loaded subtitle: {os.path.basename(subtitle_path)}")
                return True
            else:
                logger.error(f"Failed to parse subtitle: {subtitle_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading subtitle: {e}")
            return False
    
    def _parse_subtitle_file(self, file_path):
        """Parse subtitle file based on format"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            encoding = config.plugins.wgfilemanager.subtitle_encoding.value
            
            # Try multiple encodings
            encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252', 'cp1256']
            
            for enc in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    
                    # Parse based on format
                    if ext == '.srt':
                        self.subtitle_lines = self._parse_srt(content)
                    elif ext in ['.ass', '.ssa']:
                        self.subtitle_lines = self._parse_ass(content)
                    elif ext == '.sub':
                        self.subtitle_lines = self._parse_sub(content)
                    elif ext == '.vtt':
                        self.subtitle_lines = self._parse_vtt(content)
                    else:
                        # Try auto-detection
                        self.subtitle_lines = self._parse_auto(content)
                    
                    if self.subtitle_lines:
                        logger.info(f"Parsed {len(self.subtitle_lines)} lines with {enc} encoding")
                        return True
                        
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"Failed with {enc}: {e}")
                    continue
            
            # If all encodings fail, try with errors='ignore'
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                self.subtitle_lines = self._parse_auto(content)
                
                if self.subtitle_lines:
                    logger.info(f"Parsed {len(self.subtitle_lines)} lines (with errors ignored)")
                    return True
                    
            except Exception as e:
                logger.error(f"Failed with ignore errors: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error parsing subtitle file: {e}")
            return False
    
    def _parse_srt(self, content):
        """Parse SRT format content"""
        lines = []
        try:
            # Remove BOM if present
            content = content.lstrip('\ufeff')
            
            # Split into blocks
            blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in blocks:
                block_lines = block.strip().split('\n')
                if len(block_lines) >= 3:
                    try:
                        # Parse timestamp line
                        time_match = re.search(
                            r'(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})',
                            block_lines[1]
                        )
                        
                        if time_match:
                            start_time = time_match.group(1).replace('.', ',')
                            end_time = time_match.group(2).replace('.', ',')
                            
                            # Parse text lines
                            text_lines = []
                            for i in range(2, len(block_lines)):
                                line = block_lines[i].strip()
                                if line:
                                    # Remove HTML tags
                                    line = re.sub(r'<[^>]+>', '', line)
                                    text_lines.append(line)
                            
                            if text_lines:
                                text = ' '.join(text_lines)
                                
                                lines.append({
                                    'start': start_time,
                                    'end': end_time,
                                    'text': text,
                                    'start_ms': self._timestamp_to_ms(start_time),
                                    'end_ms': self._timestamp_to_ms(end_time)
                                })
                    except Exception as e:
                        logger.debug(f"Error parsing SRT block: {e}")
                        continue
            
            # Sort by start time
            lines.sort(key=lambda x: x['start_ms'])
            
        except Exception as e:
            logger.error(f"Error in SRT parsing: {e}")
        
        return lines
    
    def _parse_ass(self, content):
        """Parse ASS/SSA format content"""
        lines = []
        try:
            if '[Events]' in content:
                # Find events section
                events_start = content.find('[Events]')
                events_end = content.find('\n\n', events_start)
                if events_end == -1:
                    events_end = len(content)
                
                events_section = content[events_start:events_end]
                
                # Parse dialogue lines
                for line in events_section.split('\n'):
                    if line.lower().startswith('dialogue:'):
                        try:
                            parts = line.split(',', 9)
                            if len(parts) >= 10:
                                start_time = parts[1].strip()
                                end_time = parts[2].strip()
                                text = parts[9].strip()
                                
                                # Remove style tags
                                text = re.sub(r'\{[^}]*\}', '', text)
                                text = text.replace('\\N', '\n').replace('\\n', '\n')
                                text = text.replace('\\h', ' ')
                                
                                if text.strip():
                                    lines.append({
                                        'start': start_time,
                                        'end': end_time,
                                        'text': text,
                                        'start_ms': self._ass_timestamp_to_ms(start_time),
                                        'end_ms': self._ass_timestamp_to_ms(end_time)
                                    })
                        except Exception as e:
                            logger.debug(f"Error parsing ASS line: {e}")
                            continue
            
            # Sort by start time
            lines.sort(key=lambda x: x['start_ms'])
            
        except Exception as e:
            logger.error(f"Error in ASS parsing: {e}")
        
        return lines
    
    def _parse_sub(self, content):
        """Parse MicroDVD (SUB) format content"""
        lines = []
        try:
            fps = 25.0  # Default FPS
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('{'):
                    try:
                        # Format: {start_frame}{end_frame}text
                        match = re.match(r'\{(\d+)\}\{(\d+)\}(.+)', line)
                        if match:
                            start_frame = int(match.group(1))
                            end_frame = int(match.group(2))
                            text = match.group(3).strip()
                            
                            # Convert frames to time
                            start_ms = (start_frame / fps) * 1000
                            end_ms = (end_frame / fps) * 1000
                            
                            # Replace | with newlines
                            text = text.replace('|', '\n')
                            
                            if text:
                                lines.append({
                                    'start': self._ms_to_timestamp(start_ms),
                                    'end': self._ms_to_timestamp(end_ms),
                                    'text': text,
                                    'start_ms': start_ms,
                                    'end_ms': end_ms
                                })
                    except Exception as e:
                        logger.debug(f"Error parsing SUB line: {e}")
                        continue
            
            # Sort by start time
            lines.sort(key=lambda x: x['start_ms'])
            
        except Exception as e:
            logger.error(f"Error in SUB parsing: {e}")
        
        return lines
    
    def _parse_vtt(self, content):
        """Parse WebVTT format content"""
        lines = []
        try:
            # Skip WEBVTT header
            vtt_lines = content.split('\n')
            i = 0
            
            while i < len(vtt_lines):
                line = vtt_lines[i].strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('NOTE') or line == 'WEBVTT':
                    i += 1
                    continue
                
                # Check for timestamp line
                if '-->' in line:
                    try:
                        # Parse timestamp
                        times = line.split('-->')
                        if len(times) == 2:
                            start_time = times[0].strip()
                            end_time = times[1].strip()
                            
                            # Collect text lines
                            i += 1
                            text_lines = []
                            while i < len(vtt_lines) and vtt_lines[i].strip():
                                text_lines.append(vtt_lines[i].strip())
                                i += 1
                            
                            text = '\n'.join(text_lines)
                            
                            if text:
                                lines.append({
                                    'start': start_time,
                                    'end': end_time,
                                    'text': text,
                                    'start_ms': self._vtt_timestamp_to_ms(start_time),
                                    'end_ms': self._vtt_timestamp_to_ms(end_time)
                                })
                    except Exception as e:
                        logger.debug(f"Error parsing VTT line: {e}")
                        i += 1
                        continue
                
                i += 1
            
            # Sort by start time
            lines.sort(key=lambda x: x['start_ms'])
            
        except Exception as e:
            logger.error(f"Error in VTT parsing: {e}")
        
        return lines
    
    def _parse_auto(self, content):
        """Auto-detect and parse subtitle format"""
        # Try different formats
        if re.search(r'\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}', content):
            return self._parse_srt(content)
        elif '[Events]' in content and 'Dialogue:' in content:
            return self._parse_ass(content)
        elif re.search(r'^\{\d+\}\{\d+\}', content, re.MULTILINE):
            return self._parse_sub(content)
        elif 'WEBVTT' in content:
            return self._parse_vtt(content)
        else:
            # Try simple timestamp format
            return self._parse_simple(content)
    
    def _parse_simple(self, content):
        """Parse simple timestamped content"""
        lines = []
        try:
            pattern = r'(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s+(.+)'
            
            for line in content.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    h, m, s, ms = map(int, match.groups()[:4])
                    text = match.group(5).strip()
                    
                    start_ms = (h * 3600 + m * 60 + s) * 1000 + ms
                    end_ms = start_ms + 5000  # Assume 5 second duration
                    
                    lines.append({
                        'start': self._ms_to_timestamp(start_ms),
                        'end': self._ms_to_timestamp(end_ms),
                        'text': text,
                        'start_ms': start_ms,
                        'end_ms': end_ms
                    })
            
            # Sort by start time
            lines.sort(key=lambda x: x['start_ms'])
            
        except Exception as e:
            logger.error(f"Error in simple parsing: {e}")
        
        return lines
    
    # ===== Time Conversion Methods =====
    
    def _timestamp_to_ms(self, timestamp):
        """Convert SRT timestamp (HH:MM:SS,mmm) to milliseconds"""
        try:
            timestamp = timestamp.replace('.', ',')
            
            if ',' in timestamp:
                time_part, ms_part = timestamp.split(',', 1)
                ms = int(ms_part.ljust(3, '0')[:3])
            else:
                time_part = timestamp
                ms = 0
            
            parts = time_part.split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return (h * 3600 + m * 60 + s) * 1000 + ms
            else:
                return 0
        except:
            return 0
    
    def _ass_timestamp_to_ms(self, timestamp):
        """Convert ASS timestamp (H:MM:SS.cc) to milliseconds"""
        try:
            parts = timestamp.split(':')
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
        except:
            return 0
    
    def _vtt_timestamp_to_ms(self, timestamp):
        """Convert WebVTT timestamp to milliseconds"""
        try:
            # Remove optional settings
            timestamp = timestamp.split(' ')[0]
            
            parts = timestamp.split(':')
            if len(parts) == 3:
                h, m, s_ms = parts
                if '.' in s_ms:
                    s, ms = s_ms.split('.')
                    ms = int(ms.ljust(3, '0')[:3])
                else:
                    s = s_ms
                    ms = 0
                
                return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + ms
            elif len(parts) == 2:
                m, s_ms = parts
                if '.' in s_ms:
                    s, ms = s_ms.split('.')
                    ms = int(ms.ljust(3, '0')[:3])
                else:
                    s = s_ms
                    ms = 0
                
                return (int(m) * 60 + int(s)) * 1000 + ms
            return 0
        except:
            return 0
    
    def _ms_to_timestamp(self, ms):
        """Convert milliseconds to SRT timestamp (HH:MM:SS,mmm)"""
        try:
            ms = max(0, int(ms))
            
            hours = ms // 3600000
            minutes = (ms % 3600000) // 60000
            seconds = (ms % 60000) // 1000
            milliseconds = ms % 1000
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        except:
            return "00:00:00,000"
    
    # ===== Subtitle Manipulation =====
    
    def clear_subtitle(self):
        """Clear current subtitle"""
        self.current_subtitle = None
        self.subtitle_lines = []
        self.active = False
        self.current_line_index = 0
        logger.debug("Cleared current subtitle")
    
    def get_current_subtitle(self):
        """Get current subtitle path"""
        return self.current_subtitle
    
    def set_video_file(self, video_path):
        """Set current video file"""
        self.video_file = video_path
        logger.debug(f"Set video file: {os.path.basename(video_path)}")
    
    def update_position(self, position_ms):
        """Update playback position for subtitle sync"""
        if not self.active or not self.subtitle_lines:
            return None
        
        try:
            # Find current subtitle line
            current_line = None
            for i, line in enumerate(self.subtitle_lines):
                if line['start_ms'] <= position_ms <= line['end_ms']:
                    current_line = line
                    self.current_line_index = i
                    break
            
            return current_line
            
        except Exception as e:
            logger.error(f"Error updating subtitle position: {e}")
            return None
    
    def get_line_at_time(self, time_ms):
        """Get subtitle line at specific time"""
        try:
            for i, line in enumerate(self.subtitle_lines):
                if line['start_ms'] <= time_ms <= line['end_ms']:
                    return i, line
            return -1, None
        except:
            return -1, None
    
    def get_line(self, index):
        """Get subtitle line by index"""
        try:
            if 0 <= index < len(self.subtitle_lines):
                return self.subtitle_lines[index]
            return None
        except:
            return None
    
    def get_total_lines(self):
        """Get total number of subtitle lines"""
        return len(self.subtitle_lines) if self.subtitle_lines else 0
    
    # ===== Delay Management =====
    
    def adjust_delay(self, delay_ms):
        """Adjust subtitle delay"""
        try:
            self.current_delay = delay_ms
            
            # Update config
            config.plugins.wgfilemanager.subtitle_delay.value = delay_ms
            
            # Apply delay to subtitle lines
            self._apply_delay_to_subtitle()
            
            logger.info(f"Adjusted subtitle delay: {delay_ms}ms")
            return True
            
        except Exception as e:
            logger.error(f"Error adjusting delay: {e}")
            return False
    
    def _apply_delay_to_subtitle(self):
        """Apply current delay to subtitle lines"""
        if not self.subtitle_lines or self.current_delay == 0:
            return
        
        try:
            for line in self.subtitle_lines:
                line['start_ms'] = max(0, line['start_ms'] + self.current_delay)
                line['end_ms'] = max(0, line['end_ms'] + self.current_delay)
                
                # Update timestamps
                line['start'] = self._ms_to_timestamp(line['start_ms'])
                line['end'] = self._ms_to_timestamp(line['end_ms'])
            
            logger.debug(f"Applied {self.current_delay}ms delay to {len(self.subtitle_lines)} lines")
            
        except Exception as e:
            logger.error(f"Error applying delay: {e}")
    
    def reset_delay(self):
        """Reset subtitle delay to zero"""
        return self.adjust_delay(0)
    
    # ===== UI Integration Methods =====
    
    def open_delay_settings(self, video_file=None):
        """Open subtitle delay settings screen"""
        try:
            from .subtitle_delay_screen import SubtitleDelayScreen
            self.session.open(SubtitleDelayScreen, video_file or self.video_file)
            return True
        except ImportError as e:
            logger.error(f"Cannot import delay screen: {e}")
            return False
        except Exception as e:
            logger.error(f"Error opening delay settings: {e}")
            return False
    
    def open_style_settings(self):
        """Open subtitle style settings screen"""
        try:
            from .subtitle_style_screen import SubtitleStyleScreen
            self.session.open(SubtitleStyleScreen)
            return True
        except ImportError as e:
            logger.error(f"Cannot import style screen: {e}")
            return False
        except Exception as e:
            logger.error(f"Error opening style settings: {e}")
            return False
    
    def open_embedded_subtitle_tools(self, video_file=None):
        """Open embedded subtitle tools"""
        try:
            from .subtitle_tools_screen import SubtitleToolsScreen
            self.session.open(SubtitleToolsScreen, video_file or self.video_file)
            return True
        except ImportError as e:
            logger.error(f"Cannot import tools screen: {e}")
            return False
        except Exception as e:
            logger.error(f"Error opening subtitle tools: {e}")
            return False
    
    def open_subtitle_menu(self, video_file=None):
        """Open main subtitle menu"""
        try:
            from ..ui.subtitle_menu import SubtitleMenuScreen
            self.session.open(SubtitleMenuScreen, self, video_file or self.video_file)
            return True
        except ImportError as e:
            logger.error(f"Cannot import subtitle menu: {e}")
            return False
        except Exception as e:
            logger.error(f"Error opening subtitle menu: {e}")
            return False
    
    def reload_config(self):
        """Reload configuration from config"""
        self._load_config()
        logger.info("Subtitle configuration reloaded")
    
    # ===== Utility Methods =====
    
    def get_subtitle_info(self):
        """Get information about current subtitle"""
        if not self.current_subtitle:
            return "No subtitle loaded"
        
        info = []
        info.append(f"File: {os.path.basename(self.current_subtitle)}")
        info.append(f"Lines: {len(self.subtitle_lines)}")
        info.append(f"Active: {self.active}")
        info.append(f"Delay: {self.current_delay}ms")
        
        if self.video_file:
            info.append(f"Video: {os.path.basename(self.video_file)}")
        
        return "\n".join(info)
    
    def get_statistics(self):
        """Get subtitle statistics"""
        if not self.subtitle_lines:
            return {}
        
        total_chars = sum(len(line['text']) for line in self.subtitle_lines)
        total_words = sum(len(line['text'].split()) for line in self.subtitle_lines)
        
        if self.subtitle_lines:
            first_line = self.subtitle_lines[0]
            last_line = self.subtitle_lines[-1]
            duration_ms = last_line['end_ms'] - first_line['start_ms']
            duration_sec = duration_ms / 1000
        else:
            duration_sec = 0
        
        return {
            'total_lines': len(self.subtitle_lines),
            'total_chars': total_chars,
            'total_words': total_words,
            'duration_seconds': duration_sec,
            'words_per_minute': (total_words / duration_sec * 60) if duration_sec > 0 else 0,
            'active': self.active,
            'delay_ms': self.current_delay,
        }


# Keep SimpleSubtitleManager as an alias for backward compatibility
SimpleSubtitleManager = SubtitleManager