"""
views/login.py - Login View

First screen shown to the student.
Pre-fills username from system environment.
Requires password authentication via PAM.
On success, decrypts the questions file from bootable drive.
"""

import os
import logging
from gi.repository import Gtk, Gio
from utils.auth import Authenticator
from utils.crypto import ExamCrypto

logger = logging.getLogger(__name__)


class LoginView(Gtk.Box):
    """Login view with PAM authentication and question decryption."""
    
    def __init__(self, on_success=None, exam_config=None):
        """
        Initialize the login view.
        
        Args:
            on_success: Callback function called when login succeeds
            exam_config: Dictionary with exam configuration (paths, etc.)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_margin_top(40)
        self.set_margin_bottom(40)
        self.set_margin_start(60)
        self.set_margin_end(60)
        
        self.on_success = on_success
        self.exam_config = exam_config or {}
        self.authenticator = Authenticator(max_attempts=3)
        self.crypto = ExamCrypto()
        
        # Get current system username
        self.current_user = os.environ.get('USER', 'student')
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the login form UI."""
        
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='28000' weight='bold'>Examination Portal</span>")
        title.set_margin_bottom(20)
        self.append(title)
        
        # Subtitle
        subtitle = Gtk.Label()
        subtitle.set_markup("<span size='14000'>Confirm your identity to begin</span>")
        subtitle.set_margin_bottom(40)
        self.append(subtitle)
        
        # Username field (pre-filled, read-only)
        username_label = Gtk.Label(label="Username:")
        username_label.set_halign(Gtk.Align.START)
        self.append(username_label)
        
        self.username_entry = Gtk.Entry()
        self.username_entry.set_text(self.current_user)
        self.username_entry.set_editable(False)
        self.username_entry.set_margin_bottom(20)
        self.append(self.username_entry)
        
        # Password field
        password_label = Gtk.Label(label="Password:")
        password_label.set_halign(Gtk.Align.START)
        self.append(password_label)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_margin_bottom(10)
        self.password_entry.connect("activate", lambda w: self._on_login_clicked())
        self.append(self.password_entry)
        
        # Error message label
        self.error_label = Gtk.Label()
        self.error_label.set_margin_bottom(20)
        self.error_label.set_wrap(True)
        self.append(self.error_label)
        
        # Login button
        login_button = Gtk.Button(label="Login")
        login_button.set_size_request(300, 50)
        login_button.connect("clicked", lambda w: self._on_login_clicked())
        self.append(login_button)
        
        # Focus on password field
        self.password_entry.grab_focus()
    
    def _on_login_clicked(self):
        """Handle login button click."""
        username = self.username_entry.get_text()
        password = self.password_entry.get_text()
        
        if not password:
            self._set_error("Please enter your password")
            return
        
        # Verify credentials
        success, message = self.authenticator.verify(username, password)
        
        if not success:
            self._set_error(message)
            self.password_entry.set_text("")
            return
        
        # Clear any previous errors
        self._set_error("")
        
        # Try to load GPG keys and decrypt questions
        logger.info("Authentication successful, loading exam data...")
        
        if not self.crypto.load_keyring():
            self._set_error("Failed to load encryption keys. Contact administrator.")
            return
        
        # Path to questions file on bootable drive
        questions_path = self.exam_config.get(
            'questions_file',
            '/media/examdrive/questions.gpg'
        )
        
        success, questions = self.crypto.decrypt_questions(questions_path)
        
        if not success:
            self._set_error("Failed to decrypt exam questions. Ensure questions.gpg is on the drive.")
            return
        
        # Success! Call the callback with decrypted questions
        logger.info("Login successful and questions decrypted")
        if self.on_success:
            self.on_success(questions=questions, username=username)
    
    def _set_error(self, message: str):
        """Display an error message to the user."""
        if message:
            self.error_label.set_markup(f"<span color='#E24B4A'>{message}</span>")
        else:
            self.error_label.set_markup("")
