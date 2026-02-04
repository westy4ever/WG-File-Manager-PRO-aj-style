# player/subtitle_bridge.py
import re
import os
from datetime import timedelta


class SubtitleLine:
    """Represents a single subtitle line"""
    
    def __init__(self, start_time, end_time, text, index=0):
        self.start_time = start_time  # in seconds
        self.end_time = end_time      # in seconds
        self.text = text
        self.index = index
    
    def is_active_at(self, time):
        """Check if line is active at given time"""
        return self.start_time <= time < self.end_time


class SubtitleBridge:
    """Bridge for handling different subtitle formats"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.lines = []
        self.encoding = "utf-8"
        self.format = ""
        self.is_loaded = False
        
        self.load()
    
    def load(self):
        """Load subtitle file"""
        if not os.path.exists(self.file_path):
            return False
        
        # Detect format by extension
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext == '.srt':
            return self.load_srt()
        elif ext == '.sub':
            return self.load_microdvd()
        elif ext in ['.ass', '.ssa']:
            return self.load_ass()
        elif ext == '.vtt':
            return self.load_vtt()
        
        return False
    
    def load_srt(self):
        """Load SRT format subtitle"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Parse SRT format
            pattern = re.compile(r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)\n\n', re.DOTALL)
            
            for match in pattern.finditer(content + "\n\n"):
                index = int(match.group(1))
                start_time = self.parse_srt_time(match.group(2))
                end_time = self.parse_srt_time(match.group(3))
                text = match.group(4).strip()
                
                line = SubtitleLine(start_time, end_time, text, index)
                self.lines.append(line)
            
            self.format = "srt"
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading SRT: {e}")
            return False
    
    def load_microdvd(self):
        """Load MicroDVD format subtitle"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.readlines()
            
            fps = 25  # Default FPS
            for line in content:
                line = line.strip()
                if line.startswith('{'):
                    # Parse MicroDVD format: {start}{end}text
                    match = re.match(r'\{(\d+)\}\{(\d+)\}(.*)', line)
                    if match:
                        start_frame = int(match.group(1))
                        end_frame = int(match.group(2))
                        text = match.group(3)
                        
                        start_time = start_frame / fps
                        end_time = end_frame / fps
                        
                        subtitle_line = SubtitleLine(start_time, end_time, text, len(self.lines) + 1)
                        self.lines.append(subtitle_line)
            
            self.format = "sub"
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading MicroDVD: {e}")
            return False
    
    def load_ass(self):
        """Load ASS/SSA format subtitle (simplified)"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Look for [Events] section
            if '[Events]' in content:
                events_section = content.split('[Events]')[1].split('\n\n')[0]
                
                # Parse dialogue lines
                for line in events_section.split('\n'):
                    if line.startswith('Dialogue:'):
                        parts = line.split(',', 9)
                        if len(parts) >= 10:
                            start_time = self.parse_ass_time(parts[1])
                            end_time = self.parse_ass_time(parts[2])
                            text = parts[9].strip()
                            
                            # Remove formatting tags (simplified)
                            text = re.sub(r'\{.*?\}', '', text)
                            
                            subtitle_line = SubtitleLine(start_time, end_time, text, len(self.lines) + 1)
                            self.lines.append(subtitle_line)
            
            self.format = "ass"
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading ASS: {e}")
            return False
    
    def load_vtt(self):
        """Load WebVTT format subtitle"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Skip WEBVTT header
            lines = content.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                i += 1
                
                # Skip empty lines and comments
                if not line or line.startswith('NOTE') or line == 'WEBVTT':
                    continue
                
                # Check if this is a timestamp line
                if '-->' in line:
                    # Parse timestamp
                    times = line.split('-->')
                    if len(times) == 2:
                        start_time = self.parse_vtt_time(times[0].strip())
                        end_time = self.parse_vtt_time(times[1].strip())
                        
                        # Collect text lines
                        text_lines = []
                        while i < len(lines) and lines[i].strip():
                            text_lines.append(lines[i].strip())
                            i += 1
                        
                        text = '\n'.join(text_lines)
                        
                        subtitle_line = SubtitleLine(start_time, end_time, text, len(self.lines) + 1)
                        self.lines.append(subtitle_line)
                
                i += 1
            
            self.format = "vtt"
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading VTT: {e}")
            return False
    
    def parse_srt_time(self, time_str):
        """Parse SRT time format (HH:MM:SS,mmm) to seconds"""
        try:
            h, m, s_ms = time_str.split(':')
            s, ms = s_ms.split(',')
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        except:
            return 0
    
    def parse_ass_time(self, time_str):
        """Parse ASS time format (H:MM:SS.cc) to seconds"""
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except:
            return 0
    
    def parse_vtt_time(self, time_str):
        """Parse WebVTT time format (HH:MM:SS.mmm) to seconds"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s)
        except:
            return 0
    
    def get_line_at_time(self, time):
        """Get subtitle line index at given time"""
        for i, line in enumerate(self.lines):
            if line.is_active_at(time):
                return i
        return -1
    
    def get_line(self, index):
        """Get subtitle line by index"""
        if 0 <= index < len(self.lines):
            return self.lines[index]
        return None
    
    def save(self, file_path=None):
        """Save subtitle to file"""
        # TODO: Implement save functionality
        pass
    
    def is_valid(self):
        """Check if subtitle is valid"""
        return self.is_loaded and len(self.lines) > 0
    
    def __len__(self):
        return len(self.lines)