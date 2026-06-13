"""
views/submitted.py - Submitted Confirmation View

Shows after student submits the exam.
Displays confirmation message.
Handles copying encrypted answers to bootable drive.
Prepares for system shutdown.
"""

import logging
import shutil
import os
from typing import Dict
from gi.repository import Gtk, GLib

logger = logging.getLogger(__name__)


class SubmittedView(Gtk.Box):
    """View shown after exam submission."""
    
    def __init__(self, exam_config: Dict = None, on_ready_shutdown=None):
        """
        Initialize the submitted view.
        
        Args:
            exam_config: Exam configuration
            on_ready_shutdown: Callback when ready to shutdown
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_margin_top(60)
        self.set_margin_bottom(60)
        self.set_margin_start(80)
        self.set_margin_end(80)
        
        self.exam_config = exam_config or {}
        self.on_ready_shutdown = on_ready_shutdown
        
        # Build UI
        self._build_ui()
        
        # Start copying answers to bootable drive
        GLib.timeout_add(500, self._copy_answers_to_drive)
    
    def _build_ui(self):
        """Build the submitted confirmation UI."""
        
        # Success icon/title
        title = Gtk.Label()
        title.set_markup("<span size='32000' weight='bold' color='#639922'>✓</span>")
        title.set_margin_bottom(20)
        self.append(title)
        
        # Success message
        message = Gtk.Label()
        message.set_markup("<span size='24000' weight='bold'>Examination Submitted</span>")
        message.set_margin_bottom(20)
        self.append(message)
        
        # Details
        details = Gtk.Label()
        details.set_markup("""
<span size='14000'>
Your examination has been successfully submitted and encrypted.

Your answers are now being securely saved.

<b>What happens next:</b>
• Your encrypted answer file is being copied to the exam collection drive
• You will not be able to view or modify your answers
• The system will automatically shut down

Thank you for taking the examination.
</span>
""")
        details.set_justify(Gtk.Justification.CENTER)
        details.set_wrap(True)
        details.set_margin_bottom(40)
        self.append(details)
        
        # Status label for copying
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<span size='12000' color='#185FA5'>Preparing answer files...</span>")
        self.status_label.set_margin_bottom(20)
        self.append(self.status_label)
        
        # Progress indicator (spinner)
        spinner = Gtk.Spinner()
        spinner.set_spinning(True)
        spinner.set_margin_bottom(40)
        self.append(spinner)
        
        # Copyright/footer
        footer = Gtk.Label()
        footer.set_markup("<span size='10000' color='#5F5E5A'>Secure Examination System v1.0</span>")
        footer.set_margin_top(60)
        self.append(footer)
    
    def _copy_answers_to_drive(self) -> bool:
        """Copy encrypted answers to bootable drive."""
        try:
            # Source path (where the exam app saved the encrypted file)
            source_path = self.exam_config.get('answers_file', '/tmp/answers.gpg')
            
            # Destination path (on the bootable drive)
            drive_path = self.exam_config.get(
                'bootable_drive_path',
                '/media/examdrive'
            )
            dest_path = os.path.join(drive_path, 'answers.gpg')
            
            # Update status
            self.status_label.set_markup(
                "<span size='12000' color='#185FA5'>Copying encrypted answers to collection drive...</span>"
            )
            
            # Check if source exists
            if not os.path.exists(source_path):
                logger.warning(f"Answers file not found at {source_path}")
                self.status_label.set_markup(
                    "<span size='12000' color='#BA7517'>Note: Answers file location not found, skipping drive copy</span>"
                )
                # Continue anyway - answers might be on a temp mount
                GLib.timeout_add(2000, self._finalize_shutdown)
                return False
            
            # Check if drive is mounted
            if not os.path.exists(drive_path):
                logger.warning(f"Bootable drive not mounted at {drive_path}")
                self.status_label.set_markup(
                    "<span size='12000' color='#993C1D'>Warning: Collection drive not found. Answers will be collected from hard disk.</span>"
                )
                GLib.timeout_add(2000, self._finalize_shutdown)
                return False
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            logger.info(f"Successfully copied answers to {dest_path}")
            
            # Verify copy
            if os.path.exists(dest_path):
                file_size = os.path.getsize(dest_path)
                self.status_label.set_markup(
                    f"<span size='12000' color='#0F6E56'>✓ Answers saved to collection drive ({file_size} bytes)</span>"
                )
                logger.info(f"Answers file verified: {file_size} bytes")
            
            # Schedule shutdown preparation
            GLib.timeout_add(2000, self._finalize_shutdown)
            return False  # Stop repeating
        
        except PermissionError:
            logger.error(f"Permission denied copying to {dest_path}")
            self.status_label.set_markup(
                "<span size='12000' color='#993C1D'>Permission error accessing collection drive</span>"
            )
            GLib.timeout_add(2000, self._finalize_shutdown)
            return False
        
        except Exception as e:
            logger.error(f"Error copying answers: {e}")
            self.status_label.set_markup(
                f"<span size='12000' color='#993C1D'>Error: {str(e)}</span>"
            )
            GLib.timeout_add(2000, self._finalize_shutdown)
            return False
    
    def _finalize_shutdown(self) -> bool:
        """Finalize and prepare for shutdown."""
        if self.on_ready_shutdown:
            self.on_ready_shutdown()
        return False
