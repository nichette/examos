"""
timer.py - Countdown timer and periodic callback utilities

Uses GLib.timeout_add for non-blocking async timers.
Provides countdown for exam duration and triggers for auto-save.
"""

import logging
from typing import Callable, Optional
from gi.repository import GLib

logger = logging.getLogger(__name__)


class ExamTimer:
    """Manages exam countdown timer."""
    
    def __init__(self, duration_minutes: int = 120):
        """
        Initialize the exam timer.
        
        Args:
            duration_minutes: Exam duration in minutes (default: 120 = 2 hours)
        """
        self.duration_seconds = duration_minutes * 60
        self.elapsed_seconds = 0
        self.is_running = False
        self.on_tick: Optional[Callable] = None
        self.on_finished: Optional[Callable] = None
        self.timeout_handle: Optional[int] = None
    
    def start(self):
        """Start the countdown timer."""
        if self.is_running:
            logger.warning("Timer already running")
            return
        
        self.is_running = True
        self.elapsed_seconds = 0
        self._tick()
        logger.info(f"Timer started: {self.duration_seconds} seconds")
    
    def _tick(self):
        """Internal tick function called every second."""
        if not self.is_running:
            return False
        
        self.elapsed_seconds += 1
        remaining = self.duration_seconds - self.elapsed_seconds
        
        # Call tick callback if provided
        if self.on_tick:
            self.on_tick(remaining)
        
        # Check if time is up
        if remaining <= 0:
            self.is_running = False
            if self.on_finished:
                self.on_finished()
            logger.info("Exam time finished")
            return False  # Stop the timeout
        
        # Schedule next tick in 1 second
        self.timeout_handle = GLib.timeout_add(1000, self._tick)
        return False  # Don't repeat (we schedule a new one)
    
    def pause(self):
        """Pause the timer."""
        if self.timeout_handle:
            GLib.source_remove(self.timeout_handle)
            self.timeout_handle = None
        self.is_running = False
        logger.info("Timer paused")
    
    def resume(self):
        """Resume the paused timer."""
        if not self.is_running and self.elapsed_seconds < self.duration_seconds:
            self.is_running = True
            self._tick()
            logger.info("Timer resumed")
    
    def stop(self):
        """Stop the timer completely."""
        if self.timeout_handle:
            GLib.source_remove(self.timeout_handle)
            self.timeout_handle = None
        self.is_running = False
        logger.info("Timer stopped")
    
    def get_remaining_formatted(self) -> str:
        """
        Get remaining time as formatted string (HH:MM:SS).
        
        Returns:
            Formatted time string
        """
        remaining = max(0, self.duration_seconds - self.elapsed_seconds)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_remaining_seconds(self) -> int:
        """Get remaining time in seconds."""
        return max(0, self.duration_seconds - self.elapsed_seconds)
    
    def is_time_running_out(self, threshold_minutes: int = 5) -> bool:
        """
        Check if time is running out (less than threshold remaining).
        
        Args:
            threshold_minutes: Threshold in minutes (default: 5)
        
        Returns:
            True if less than threshold remains
        """
        remaining_minutes = self.get_remaining_seconds() / 60
        return remaining_minutes < threshold_minutes


class AutoSaveTimer:
    """Manages periodic auto-save intervals."""
    
    def __init__(self, interval_seconds: int = 30):
        """
        Initialize the auto-save timer.
        
        Args:
            interval_seconds: Interval between saves (default: 30 seconds)
        """
        self.interval_seconds = interval_seconds
        self.is_running = False
        self.on_save: Optional[Callable] = None
        self.timeout_handle: Optional[int] = None
    
    def start(self):
        """Start the auto-save timer."""
        if self.is_running:
            logger.warning("Auto-save timer already running")
            return
        
        self.is_running = True
        self._trigger_save()
        logger.info(f"Auto-save timer started: {self.interval_seconds}s interval")
    
    def _trigger_save(self):
        """Trigger a save and schedule the next one."""
        if not self.is_running:
            return False
        
        # Call save callback
        if self.on_save:
            try:
                self.on_save()
            except Exception as e:
                logger.error(f"Error during auto-save: {e}")
        
        # Schedule next save
        self.timeout_handle = GLib.timeout_add(self.interval_seconds * 1000, self._trigger_save)
        return False
    
    def stop(self):
        """Stop the auto-save timer."""
        if self.timeout_handle:
            GLib.source_remove(self.timeout_handle)
            self.timeout_handle = None
        self.is_running = False
        logger.info("Auto-save timer stopped")
    
    def trigger_now(self):
        """Trigger a save immediately (not waiting for interval)."""
        if self.on_save:
            try:
                self.on_save()
                logger.info("Manual auto-save triggered")
            except Exception as e:
                logger.error(f"Error during manual save: {e}")
