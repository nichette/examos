"""
views/instructions.py - Examination Instructions View

Displays exam rules, duration, and requirements.
Requires student to check "I have read..." before allowing exam to start.
"""

import logging
from gi.repository import Gtk

logger = logging.getLogger(__name__)


class InstructionsView(Gtk.Box):
    """View displaying examination instructions and requirements."""
    
    def __init__(self, exam_config=None, on_start_exam=None):
        """
        Initialize the instructions view.
        
        Args:
            exam_config: Dictionary with exam configuration (duration, rules, etc.)
            on_start_exam: Callback when student clicks "Start Exam" button
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.set_margin_top(30)
        self.set_margin_bottom(30)
        self.set_margin_start(50)
        self.set_margin_end(50)
        
        self.exam_config = exam_config or {}
        self.on_start_exam = on_start_exam
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the instructions form UI."""
        
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='24000' weight='bold'>Examination Instructions</span>")
        title.set_margin_bottom(20)
        self.append(title)
        
        # Get duration from config
        duration = self.exam_config.get('duration_minutes', 120)
        hours = duration // 60
        minutes = duration % 60
        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Duration info
        duration_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        duration_label = Gtk.Label(label="Examination Duration:")
        duration_label.set_weight(500)
        duration_value = Gtk.Label(label=duration_str)
        duration_box.append(duration_label)
        duration_box.append(duration_value)
        self.append(duration_box)
        
        # Scrollable instructions text
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.set_margin_bottom(20)
        
        instructions_text = Gtk.TextView()
        instructions_text.set_editable(False)
        instructions_text.set_cursor_visible(False)
        instructions_text.set_wrap_mode(Gtk.WrapMode.WORD)
        instructions_text.set_left_margin(15)
        instructions_text.set_right_margin(15)
        instructions_text.set_top_margin(15)
        instructions_text.set_bottom_margin(15)
        
        # Build instructions content
        rules = self.exam_config.get('rules', self._get_default_rules())
        instructions_buffer = instructions_text.get_buffer()
        instructions_buffer.set_text(rules)
        
        scroll.set_child(instructions_text)
        self.append(scroll)
        
        # Checkbox for acknowledgment
        checkbox_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        checkbox_box.set_margin_bottom(20)
        
        self.agree_checkbox = Gtk.CheckButton(
            label="I have read and understood the examination instructions"
        )
        self.agree_checkbox.connect("toggled", lambda w: self._update_button_sensitivity())
        checkbox_box.append(self.agree_checkbox)
        
        self.append(checkbox_box)
        
        # Start Exam button (disabled until checkbox is checked)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.start_button = Gtk.Button(label="Start Exam")
        self.start_button.set_size_request(250, 50)
        self.start_button.set_sensitive(False)
        self.start_button.connect("clicked", self._on_start_exam_clicked)
        
        button_box.append(self.start_button)
        self.append(button_box)
    
    def _update_button_sensitivity(self):
        """Enable/disable Start Exam button based on checkbox state."""
        is_checked = self.agree_checkbox.get_active()
        self.start_button.set_sensitive(is_checked)
    
    def _on_start_exam_clicked(self):
        """Handle Start Exam button click."""
        logger.info("Student confirmed instructions and started exam")
        if self.on_start_exam:
            self.on_start_exam()
    
    def _get_default_rules(self) -> str:
        """Return default examination rules if not provided in config."""
        return """EXAMINATION RULES AND INSTRUCTIONS

1. GENERAL RULES
   • This is a supervised examination. Cheating is strictly prohibited.
   • Your answers will be automatically saved every 30 seconds.
   • Do not refresh or close the examination window.
   • Do not attempt to access the system terminal or other applications.

2. ANSWERING QUESTIONS
   • Read each question carefully before attempting an answer.
   • Type your answers in the provided text fields.
   • You can navigate between questions using the Previous/Next buttons.
   • Ensure all your answers are complete before submitting.

3. TIMING
   • You have 120 minutes to complete the examination.
   • A countdown timer is displayed at the top of the screen.
   • When time expires, your answers will be automatically submitted.
   • Do not attempt to manipulate the system clock.

4. SUBMISSION
   • Click "Submit Examination" only when you are completely finished.
   • After submission, your examination cannot be modified.
   • Your encrypted answers will be securely collected by the administrator.

5. TECHNICAL SUPPORT
   • If you experience technical issues, raise your hand and inform the invigilator.
   • Do not attempt to restart or shut down the computer yourself.

6. CONSEQUENCES OF MALPRACTICE
   • Any attempt to cheat or bypass security measures will result in disqualification.
   • Evidence of malpractice will be reported to the examination authority.

By checking the acknowledgment box, you confirm that you have read, understood, and agree to follow these instructions."""
