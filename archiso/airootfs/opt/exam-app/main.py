#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class ExamLogin(Gtk.Window):
    def __init__(self):
        super().__init__(title="Exam Login")
        
        # Force the app to be completely full screen
        self.fullscreen()
        
        # Create a layout box to center everything
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        self.add(box)
        
        # Add a large, bold title
        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>Secure Exam Portal</span>")
        box.pack_start(title, False, False, 0)
        
        # Student ID Input
        self.username_entry = Gtk.Entry()
        self.username_entry.set_placeholder_text("Enter Student ID")
        box.pack_start(self.username_entry, False, False, 0)
        
        # Password Input (Text is hidden as dots)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_placeholder_text("Enter Password")
        self.password_entry.set_visibility(False) 
        box.pack_start(self.password_entry, False, False, 0)
        
        # Login Button
        login_btn = Gtk.Button(label="Login & Start Exam")
        login_btn.connect("clicked", self.on_login_clicked)
        box.pack_start(login_btn, False, False, 0)

    # What happens when the button is clicked
    def on_login_clicked(self, button):
        student_id = self.username_entry.get_text()
        print(f"Attempting login for: {student_id}")

# Start the application
window = ExamLogin()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
