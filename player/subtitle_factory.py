"""
Subtitle Factory - Factory functions for subtitle management
"""

from .subtitle_manager import SubtitleManager


class SubtitleFactory:
    """Factory for creating subtitle parsers"""
    
    def create_subtitle(self, file_path):
        """Create subtitle parser based on file type"""
        if not file_path or not os.path.exists(file_path):
            return None
        
        ext = os.path.splitext(file_path)[1].lower()
        
        # Use SubtitleBridge to handle different formats
        from .subtitle_bridge import SubtitleBridge
        subtitle = SubtitleBridge(file_path)
        
        if subtitle.is_valid():
            return subtitle
        
        return None
    
    def create_from_text(self, text, format="srt"):
        """Create subtitle from text"""
        # TODO: Implement text-based subtitle creation
        pass


def get_subtitle_manager(session, video_file=None):
    """Factory function to get subtitle manager instance"""
    try:
        manager = SubtitleManager(session)
        if video_file:
            manager.set_video_file(video_file)
        return manager
    except Exception as e:
        # Fallback to basic logger
        import logging
        logging.error(f"Error creating subtitle manager: {e}")
        
        # Return a basic manager even if there's an error
        class FallbackSubtitleManager:
            def __init__(self, session):
                self.session = session
                self.current_subtitle = None
                self.video_file = None
                self.active = False
            
            def set_video_file(self, video_path):
                self.video_file = video_path
            
            def toggle_subtitles(self):
                self.active = not self.active
                return self.active
            
            def is_active(self):
                return self.active
            
            def auto_load_subtitle(self, service_ref):
                return False
        
        return FallbackSubtitleManager(session)