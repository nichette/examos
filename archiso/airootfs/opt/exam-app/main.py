#!/usr/bin/env python3
"""
main.py - Secure Examination GTK4 Application

Main entry point for the examination system.
Manages view switching, configuration, and application lifecycle.

Usage:
    python3 main.py [--config /path/to/config.json]

Configuration file (JSON) should contain:
    {
        "duration_minutes": 120,
        "student_id": "exam2026-042",
        "questions_file": "/media/examdrive/questions.gpg",
        "answers_file": "/media/examdrive/answers.gpg",
        "bootable_drive_path": "/media/examdrive",
        "rules": "Custom exam rules here..."
    }
"""

import sys
import os
import json
import argparse
import logging
from typing import Optional, Dict

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk

# Import all views
from views.login import LoginView
from views.instructions import InstructionsView
from views.exam import ExamView
from views.submitted import SubmittedView
from views.shutdown import ShutdownView

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/examapp.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ExamApplication(Gtk.ApplicationWindow):
    """Main application window managing all exam views."""
    
    def __init__(self, app, exam_config: Optional[Dict] = None):
        """
        Initialize the application window.
        
        Args:
            app: The Gtk.Application instance
            exam_config: Examination configuration dictionary
        """
        super().__init__(application=app)
        self.set_title("Examination System")
        self.set_default_size(1024, 768)
        
        self.exam_config = exam_config or {}
        self.questions_data = None
        self.student_username = None
        
        # Stack for view switching
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(300)
        
        # Create views
        self._create_login_view()
        self.set_child(self.stack)
        
        # Apply CSS styling
        self._apply_css()
        
        # For kiosk mode: remove decorations (will be re-enabled in production)
        # self.set_decorated(False)
        # self.fullscreen()
        
        logger.info("Application window initialized")
    
    def _apply_css(self):
        """Apply CSS styling from assets/style.css"""
        try:
            css_path = os.path.join(
                os.path.dirname(__file__),
                'assets', 'style.css'
            )
            
            if os.path.exists(css_path):
                css_provider = Gtk.CssProvider()
                css_provider.load_from_path(css_path)
                
                display = Gdk.Display.get_default()
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                logger.info(f"CSS styling loaded from {css_path}")
            else:
                logger.warning(f"CSS file not found: {css_path}")
        except Exception as e:
            logger.error(f"Error loading CSS: {e}")
    
    def _create_login_view(self):
        """Create and add the login view."""
        login_view = LoginView(
            on_success=self._on_login_success,
            exam_config=self.exam_config
        )
        self.stack.add_named(login_view, "login")
        self.stack.set_visible_child_name("login")
        logger.info("Login view created")
    
    def _on_login_success(self, questions: Dict, username: str):
        """
        Handle successful login.
        
        Args:
            questions: Decrypted questions dictionary
            username: Student username
        """
        self.questions_data = questions
        self.student_username = username
        
        logger.info(f"Login successful for {username}")
        
        # Create instructions view
        self._create_instructions_view()
    
    def _create_instructions_view(self):
        """Create and add the instructions view."""
        instructions_view = InstructionsView(
            exam_config=self.exam_config,
            on_start_exam=self._on_start_exam
        )
        self.stack.add_named(instructions_view, "instructions")
        self.stack.set_visible_child_name("instructions")
        logger.info("Instructions view created and displayed")
    
    def _on_start_exam(self):
        """Handle exam start."""
        if not self.questions_data:
            logger.error("Questions data not available")
            return
        
        # Add student_id and username to config for the exam view
        exam_config = self.exam_config.copy()
        exam_config['student_id'] = self.student_username
        
        # Create exam view
        exam_view = ExamView(
            questions_dict=self.questions_data,
            exam_config=exam_config,
            on_submit=self._on_exam_submit
        )
        self.stack.add_named(exam_view, "exam")
        self.stack.set_visible_child_name("exam")
        logger.info("Exam view created and displayed")
    
    def _on_exam_submit(self):
        """Handle exam submission."""
        logger.info("Exam submitted, moving to submitted view")
        
        exam_config = self.exam_config.copy()
        exam_config['student_id'] = self.student_username
        
        # Create submitted view
        submitted_view = SubmittedView(
            exam_config=exam_config,
            on_ready_shutdown=self._on_ready_shutdown
        )
        self.stack.add_named(submitted_view, "submitted")
        self.stack.set_visible_child_name("submitted")
    
    def _on_ready_shutdown(self):
        """Handle transition to shutdown view."""
        logger.info("Moving to shutdown view")
        
        # Create shutdown view
        shutdown_view = ShutdownView(shutdown_delay_seconds=60)
        self.stack.add_named(shutdown_view, "shutdown")
        self.stack.set_visible_child_name("shutdown")


class ExamApplicationMain(Gtk.Application):
    """Main GTK Application."""
    
    def __init__(self, exam_config: Optional[Dict] = None):
        """Initialize the application."""
        super().__init__(
            application_id='org.exam.portal',
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.exam_config = exam_config or {}
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        """Activate the application."""
        window = ExamApplication(app, exam_config=self.exam_config)
        window.present()


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Load examination configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    default_config = {
        'duration_minutes': 120,
        'student_id': os.environ.get('USER', 'UNKNOWN'),
        'questions_file': '/media/examdrive/questions.gpg',
        'answers_file': '/media/examdrive/answers.gpg',
        'bootable_drive_path': '/media/examdrive',
    }
    
    if not config_path:
        logger.info("No config file specified, using defaults")
        return default_config
    
    try:
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            # Merge with defaults (file config overrides)
            default_config.update(file_config)
            logger.info(f"Configuration loaded from {config_path}")
            return default_config
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return default_config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}, using defaults")
        return default_config


def main():
    """Application entry point."""
    parser = argparse.ArgumentParser(
        description='Secure Examination System'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration JSON file'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Secure Examination Application Starting")
    logger.info("=" * 60)
    
    # Load configuration
    exam_config = load_config(args.config)
    logger.info(f"Configuration: {exam_config}")
    
    # Create and run application
    app = ExamApplicationMain(exam_config=exam_config)
    exit_status = app.run(sys.argv)
    
    logger.info("Application terminated with status: " + str(exit_status))
    return exit_status


if __name__ == '__main__':
    sys.exit(main())
