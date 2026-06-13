"""
views/shutdown.py - Shutdown Countdown View

Shown after exam submission.
Displays countdown before automatic system shutdown.
Prevents user interaction to complete the lockdown.
"""

import logging
import subprocess
from gi.repository import Gtk, GLib, Pango

logger = logging.getLogger(__name__)


class ShutdownView(Gtk.Box):
    """View shown before system shutdown."""
    
    def __init__(self, shutdown_delay_seconds: int = 60):
        """
        Initialize the shutdown view.
        
        Args:
            shutdown_delay_seconds: Delay before shutdown (default: 60 seconds)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.set_margin_top(80)
        self.set_margin_bottom(80)
        self.set_margin_start(100)
        self.set_margin_end(100)
        
        self.shutdown_delay = shutdown_delay_seconds
        self.remaining_seconds = shutdown_delay_seconds
        
        # Build UI
        self._build_ui()
        
        # Start countdown
        self._start_countdown()
    
    def _build_ui(self):
        """Build the shutdown view UI."""
        
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='28000' weight='bold'>Thank You</span>")
        title.set_margin_bottom(20)
        self.append(title)
        
        # Message
        message = Gtk.Label()
        message.set_markup("<span size='16000'>Your examination has been completed and submitted.</span>")
        message.set_margin_bottom(40)
        self.append(message)
        
        # Countdown display
        countdown_label = Gtk.Label()
        countdown_label.set_markup("<span size='14000'>The system will shut down in:</span>")
        self.append(countdown_label)
        
        self.countdown_display = Gtk.Label()
        countdown_font_desc = Pango.FontDescription.from_string("Monospace 64 Bold")
        self.countdown_display.set_font_description(countdown_font_desc)
        self.countdown_display.set_label("60")
        self.countdown_display.set_margin_top(20)
        self.countdown_display.set_margin_bottom(40)
        self.append(self.countdown_display)
        
        # Info message
        info = Gtk.Label()
        info.set_markup("""
<span size='12000' color='#5F5E5A'>
This system will automatically shut down.

Do not attempt to stop the shutdown or restart the computer.

Your encrypted answers have been safely collected.

Please inform the invigilator that you have finished.
</span>
""")
        info.set_justify(Gtk.Justification.CENTER)
        info.set_wrap(True)
        info.set_margin_top(40)
        self.append(info)
    
    def _start_countdown(self):
        """Start the countdown timer."""
        self._update_countdown()
    
    def _update_countdown(self) -> bool:
        """Update the countdown display."""
        # Update display
        self.countdown_display.set_label(str(self.remaining_seconds))
        
        self.remaining_seconds -= 1
        
        # Check if we should shut down
        if self.remaining_seconds < 0:
            logger.info("Initiating system shutdown")
            self._shutdown_system()
            return False  # Stop the timeout
        
        # Schedule next update in 1 second
        GLib.timeout_add(1000, self._update_countdown)
        return False
    
    def _shutdown_system(self):
        """Execute system shutdown."""
        try:
            logger.info("Executing: systemctl poweroff")
            subprocess.run(['systemctl', 'poweroff'], check=False)
        except Exception as e:
            logger.error(f"Error executing shutdown: {e}")
            # Fallback: try pkill to force shutdown
            try:
                subprocess.run(['pkill', '-9', 'python3'], check=False)
            except Exception as e2:
                logger.error(f"Fallback shutdown also failed: {e2}")
