"""
Subtitle Delay Screen - Adjust subtitle timing
"""

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Slider import Slider
from enigma import eTimer
import time

try:
    from ..utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SubtitleDelayScreen(Screen):
    """Screen for adjusting subtitle delay"""
    
    def __init__(self, session, subtitle_manager=None, current_delay=0):
        Screen.__init__(self, session)
        
        self.subtitle_manager = subtitle_manager
        self.current_delay = current_delay
        self.original_delay = current_delay
        
        # Setup UI
        self.setupUI()
        
        # Setup actions
        self.setupActions()
        
        # Update timer
        self.update_timer = eTimer()
        self.update_timer.callback.append(self.update_display)
        
        logger.info(f"SubtitleDelayScreen initialized with delay: {current_delay}ms")
    
    def setupUI(self):
        """Setup user interface"""
        self.skin = """
        <screen position="center,center" size="600,400" title="Subtitle Delay Adjustment">
            <widget name="title" position="10,10" size="580,40" font="Regular;28" halign="center" />
            <widget name="delay_value" position="10,70" size="580,60" font="Regular;40" halign="center" />
            <widget name="slider" position="50,150" size="500,30" />
            <widget name="preview_text" position="10,200" size="580,80" font="Regular;24" halign="center" valign="center" />
            <widget name="help" position="10,300" size="580,40" font="Regular;20" halign="center" />
            <widget name="status" position="10,350" size="580,30" font="Regular;18" halign="center" />
        </screen>"""
        
        self["title"] = Label("Adjust Subtitle Delay")
        self["delay_value"] = Label("0 ms")
        self["slider"] = Slider(0, 100)  # Will be configured
        self["preview_text"] = Label("Subtitle preview will appear here")
        self["help"] = Label("LEFT/RIGHT: Adjust | OK: Apply | EXIT: Cancel")
        self["status"] = Label("")
        
        # Configure slider
        self["slider"].setRange(-5000, 5000)  # -5s to +5s
        self["slider"].setValue(self.current_delay)
        
        # Update display
        self.update_display()
    
    def setupActions(self):
        """Setup action map"""
        self["actions"] = ActionMap(["SetupActions", "DirectionActions", "ColorActions"], {
            "cancel": self.cancel,
            "ok": self.apply,
            "left": self.decrease_delay,
            "right": self.increase_delay,
            "up": self.increase_delay_fast,
            "down": self.decrease_delay_fast,
        }, -1)
    
    def update_display(self):
        """Update display with current delay"""
        # Format delay value
        if self.current_delay == 0:
            delay_text = "0 ms (No delay)"
        elif self.current_delay > 0:
            delay_text = f"+{self.current_delay} ms (+{self.current_delay/1000:.1f}s)"
        else:
            delay_text = f"{self.current_delay} ms ({self.current_delay/1000:.1f}s)"
        
        self["delay_value"].setText(delay_text)
        self["slider"].setValue(self.current_delay)
        
        # Update preview text
        preview = self.get_preview_text()
        self["preview_text"].setText(preview)
        
        # Update status
        if self.current_delay != self.original_delay:
            self["status"].setText("Modified - Press OK to apply")
        else:
            self["status"].setText("")
    
    def get_preview_text(self):
        """Get preview text based on current delay"""
        if self.current_delay == 0:
            return "Subtitles are synchronized with audio"
        elif self.current_delay > 0:
            return f"Subtitles appear {self.current_delay/1000:.1f}s AFTER audio"
        else:
            return f"Subtitles appear {abs(self.current_delay)/1000:.1f}s BEFORE audio"
    
    def increase_delay(self):
        """Increase delay by 100ms"""
        self.current_delay = min(5000, self.current_delay + 100)
        self.update_display()
        logger.debug(f"Increased delay to {self.current_delay}ms")
    
    def decrease_delay(self):
        """Decrease delay by 100ms"""
        self.current_delay = max(-5000, self.current_delay - 100)
        self.update_display()
        logger.debug(f"Decreased delay to {self.current_delay}ms")
    
    def increase_delay_fast(self):
        """Increase delay by 500ms"""
        self.current_delay = min(5000, self.current_delay + 500)
        self.update_display()
        logger.debug(f"Increased delay fast to {self.current_delay}ms")
    
    def decrease_delay_fast(self):
        """Decrease delay by 500ms"""
        self.current_delay = max(-5000, self.current_delay - 500)
        self.update_display()
        logger.debug(f"Decreased delay fast to {self.current_delay}ms")
    
    def apply(self):
        """Apply current delay"""
        try:
            if self.subtitle_manager:
                self.subtitle_manager.adjust_delay(self.current_delay)
                logger.info(f"Applied subtitle delay: {self.current_delay}ms")
            
            self.session.open(
                MessageBox,
                f"Subtitle delay applied: {self.current_delay}ms",
                MessageBox.TYPE_INFO,
                timeout=2
            )
            self.close()
            
        except Exception as e:
            logger.error(f"Error applying delay: {e}")
            self.session.open(
                MessageBox,
                f"Error applying delay: {e}",
                MessageBox.TYPE_ERROR
            )
    
    def cancel(self):
        """Cancel without applying"""
        if self.current_delay != self.original_delay:
            self.session.openWithCallback(
                self.confirm_cancel,
                MessageBox,
                "Discard changes to subtitle delay?",
                MessageBox.TYPE_YESNO
            )
        else:
            self.close()
    
    def confirm_cancel(self, result):
        """Confirm cancellation"""
        if result:
            self.close()
            logger.info("Cancelled delay adjustment")