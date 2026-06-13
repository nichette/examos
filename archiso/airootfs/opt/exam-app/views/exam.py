"""
views/exam.py - Main Examination View

Displays questions and answer fields.
Manages countdown timer and auto-save functionality.
Encrypts and saves answers periodically.
Handles exam submission and auto-submission on time expiry.
"""

import logging
import json
from typing import Dict, List, Optional
from gi.repository import Gtk, GLib, Pango
from utils.timer import ExamTimer, AutoSaveTimer
from utils.crypto import ExamCrypto

logger = logging.getLogger(__name__)


class ExamView(Gtk.Box):
    """Main examination view with questions, timer, and auto-save."""
    
    def __init__(self, questions_dict: Dict, exam_config: Dict = None, on_submit=None):
        """
        Initialize the exam view.
        
        Args:
            questions_dict: Dictionary with decrypted questions
            exam_config: Exam configuration (duration, paths, etc.)
            on_submit: Callback when exam is submitted
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.questions_dict = questions_dict
        self.exam_config = exam_config or {}
        self.on_submit = on_submit
        self.crypto = ExamCrypto()
        
        # Parse questions
        self.questions = questions_dict.get('questions', [])
        self.current_question_index = 0
        self.student_answers: Dict[int, str] = {}
        
        # Timers
        duration = self.exam_config.get('duration_minutes', 120)
        self.exam_timer = ExamTimer(duration_minutes=duration)
        self.exam_timer.on_tick = self._on_timer_tick
        self.exam_timer.on_finished = self._on_time_finished
        
        self.autosave_timer = AutoSaveTimer(interval_seconds=30)
        self.autosave_timer.on_save = self._autosave_answers
        
        # Build UI
        self._build_ui()
        
        # Start timers
        self.exam_timer.start()
        self.autosave_timer.start()
    
    def _build_ui(self):
        """Build the main exam UI."""
        
        # ─── HEADER with Timer ───
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_margin_start(20)
        header.set_margin_end(20)
        
        # Student info
        student_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        student_label = Gtk.Label(label="Student ID:")
        student_label.set_weight(500)
        student_box.append(student_label)
        
        student_id = self.exam_config.get('student_id', 'UNKNOWN')
        student_value = Gtk.Label(label=student_id)
        student_box.append(student_value)
        
        header.append(student_box)
        
        # Question counter
        counter_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        counter_label = Gtk.Label(label="Question:")
        counter_label.set_weight(500)
        counter_box.append(counter_label)
        
        self.question_counter_label = Gtk.Label(
            label=f"{self.current_question_index + 1}/{len(self.questions)}"
        )
        counter_box.append(self.question_counter_label)
        
        header.append(counter_box)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        
        # Timer display (prominent)
        timer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        timer_label = Gtk.Label(label="Time Remaining:")
        timer_label.set_weight(500)
        timer_box.append(timer_label)
        
        self.timer_display = Gtk.Label(label="00:00:00")
        timer_font = Pango.FontDescription.from_string("Monospace 32 Bold")
        self.timer_display.set_font_description(timer_font)
        self.timer_display.set_name("timer-label")  # CSS style hook
        timer_box.append(self.timer_display)
        
        header.append(timer_box)
        
        # Add header separator
        header_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header_box.append(header)
        header_box.append(header_sep)
        
        self.append(header_box)
        
        # ─── CONTENT AREA ───
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(30)
        content.set_margin_end(30)
        content.set_hexpand(True)
        content.set_vexpand(True)
        
        # Question text
        self.question_label = Gtk.Label()
        self.question_label.set_wrap(True)
        self.question_label.set_wrap_mode(Pango.WrapMode.WORD)
        self.question_label.set_halign(Gtk.Align.START)
        self.question_label.set_margin_bottom(15)
        content.append(self.question_label)
        
        # Answer input area
        answer_label = Gtk.Label(label="Your Answer:")
        answer_label.set_halign(Gtk.Align.START)
        answer_label.set_weight(500)
        content.append(answer_label)
        
        # Scrollable text view for answers
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        scroll.set_margin_bottom(15)
        
        self.answer_text_view = Gtk.TextView()
        self.answer_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.answer_text_view.set_left_margin(10)
        self.answer_text_view.set_right_margin(10)
        self.answer_text_view.set_top_margin(10)
        self.answer_text_view.set_bottom_margin(10)
        
        scroll.set_child(self.answer_text_view)
        content.append(scroll)
        
        # Navigation buttons
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        nav_box.set_halign(Gtk.Align.CENTER)
        
        self.prev_button = Gtk.Button(label="Previous")
        self.prev_button.set_size_request(120, 40)
        self.prev_button.connect("clicked", self._on_previous)
        nav_box.append(self.prev_button)
        
        self.next_button = Gtk.Button(label="Next")
        self.next_button.set_size_request(120, 40)
        self.next_button.connect("clicked", self._on_next)
        nav_box.append(self.next_button)
        
        content.append(nav_box)
        
        # Scrollable content area
        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_child(content)
        content_scroll.set_vexpand(True)
        content_scroll.set_hexpand(True)
        
        self.append(content_scroll)
        
        # ─── FOOTER with Submit button ───
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer.set_margin_top(10)
        footer.set_margin_bottom(10)
        footer.set_margin_start(20)
        footer.set_margin_end(20)
        footer.set_halign(Gtk.Align.CENTER)
        
        # Status label
        self.status_label = Gtk.Label()
        footer.append(self.status_label)
        
        # Spacer
        footer_spacer = Gtk.Box()
        footer_spacer.set_hexpand(True)
        footer.append(footer_spacer)
        
        # Submit button
        submit_button = Gtk.Button(label="Submit Examination")
        submit_button.set_size_request(180, 45)
        submit_button.set_name("submit-button")  # CSS style hook
        submit_button.connect("clicked", self._on_submit_clicked)
        footer.append(submit_button)
        
        footer_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        footer_box.append(footer_sep)
        footer_box.append(footer)
        
        self.append(footer_box)
        
        # Load first question
        self._load_question(0)
    
    def _load_question(self, index: int):
        """Load a specific question."""
        if index < 0 or index >= len(self.questions):
            return
        
        self.current_question_index = index
        question = self.questions[index]
        
        # Update question label
        q_num = index + 1
        q_text = question.get('text', 'Question text missing')
        self.question_label.set_markup(f"<b>Question {q_num}:</b> {q_text}")
        
        # Load answer (if previously entered)
        answer = self.student_answers.get(index, '')
        self.answer_text_view.get_buffer().set_text(answer)
        
        # Update counter
        self.question_counter_label.set_text(f"{q_num}/{len(self.questions)}")
        
        # Update button sensitivity
        self.prev_button.set_sensitive(index > 0)
        self.next_button.set_sensitive(index < len(self.questions) - 1)
    
    def _on_previous(self, widget):
        """Handle Previous button click."""
        if self.current_question_index > 0:
            # Save current answer
            self._save_current_answer()
            # Load previous question
            self._load_question(self.current_question_index - 1)
    
    def _on_next(self, widget):
        """Handle Next button click."""
        if self.current_question_index < len(self.questions) - 1:
            # Save current answer
            self._save_current_answer()
            # Load next question
            self._load_question(self.current_question_index + 1)
    
    def _save_current_answer(self):
        """Save the current answer from the text view."""
        text_buffer = self.answer_text_view.get_buffer()
        answer_text = text_buffer.get_text(
            text_buffer.get_start_iter(),
            text_buffer.get_end_iter(),
            False
        )
        self.student_answers[self.current_question_index] = answer_text
    
    def _on_timer_tick(self, remaining_seconds: int):
        """Called every second by the timer."""
        # Update display
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        self.timer_display.set_label(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Warning if less than 5 minutes
        if remaining_seconds == 300:  # 5 minutes
            self.status_label.set_markup("<span color='#BA7517'>⚠ 5 minutes remaining</span>")
        elif remaining_seconds == 60:  # 1 minute
            self.status_label.set_markup("<span color='#993C1D'>⚠⚠ 1 minute remaining</span>")
    
    def _on_time_finished(self):
        """Called when exam time expires."""
        logger.info("Exam time finished, auto-submitting...")
        self.status_label.set_markup("<span color='#E24B4A' weight='bold'>TIME FINISHED - SUBMITTING</span>")
        
        # Stop further interaction
        self.answer_text_view.set_editable(False)
        
        # Auto-submit
        self._submit_exam()
    
    def _autosave_answers(self):
        """Auto-save answers to encrypted file."""
        # Save current answer first
        self._save_current_answer()
        
        # Create answer packet
        answer_packet = {
            'answers': self.student_answers,
            'student_id': self.exam_config.get('student_id', 'unknown'),
            'timestamp': GLib.DateTime.new_now_local().format_iso8601(),
        }
        
        # Path for temporary encrypted file
        answers_path = self.exam_config.get(
            'answers_file',
            '/tmp/answers_temp.gpg'
        )
        
        success, message = self.crypto.encrypt_answers(answer_packet, answers_path)
        
        if success:
            logger.info(f"Auto-saved answers: {answers_path}")
        else:
            logger.error(f"Auto-save failed: {message}")
    
    def _on_submit_clicked(self, widget):
        """Handle Submit button click."""
        # Show confirmation dialog
        dialog = Gtk.AlertDialog()
        dialog.set_modal(True)
        dialog.set_message("Submit examination?")
        dialog.set_detail("Once submitted, your answers cannot be changed.")
        dialog.set_buttons(["Cancel", "Submit"])
        dialog.set_default_button(1)
        
        dialog.choose(self.get_root() if hasattr(self, 'get_root') else None, 
                     None, self._on_submit_confirmed)
    
    def _on_submit_confirmed(self, dialog, result):
        """Handle submission confirmation."""
        try:
            choice = dialog.choose_finish(result)
            if choice == 1:  # Submit was clicked
                self._submit_exam()
        except Exception as e:
            logger.error(f"Error getting dialog result: {e}")
    
    def _submit_exam(self):
        """Submit the examination."""
        # Stop timers
        self.exam_timer.stop()
        self.autosave_timer.stop()
        
        # Save current answer one final time
        self._save_current_answer()
        
        # Create final answer packet
        answer_packet = {
            'answers': self.student_answers,
            'student_id': self.exam_config.get('student_id', 'unknown'),
            'timestamp': GLib.DateTime.new_now_local().format_iso8601(),
            'submitted': True,
        }
        
        # Path to save encrypted answers
        answers_path = self.exam_config.get(
            'answers_file',
            '/media/examdrive/answers.gpg'
        )
        
        success, message = self.crypto.encrypt_answers(answer_packet, answers_path)
        
        if success:
            logger.info(f"Exam submitted and encrypted: {answers_path}")
            if self.on_submit:
                self.on_submit()
        else:
            logger.error(f"Submission failed: {message}")
            self.status_label.set_markup(f"<span color='#E24B4A'>Error: {message}</span>")
