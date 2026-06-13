"""
auth.py - PAM-based password authentication

Validates the student's username and password using the system PAM.
Never stores or logs the plaintext password.
Uses python-pam to securely verify credentials.
"""

import pam
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class Authenticator:
    """Handles secure password verification via PAM."""
    
    def __init__(self, max_attempts: int = 3):
        """
        Initialize the authenticator.
        
        Args:
            max_attempts: Maximum password attempts before lockout (default: 3)
        """
        self.max_attempts = max_attempts
        self.failed_attempts = 0
    
    def verify(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Verify username and password via PAM.
        
        Args:
            username: The system username (e.g., 'exam2026-042')
            password: The plaintext password (will NOT be stored)
        
        Returns:
            Tuple of (success: bool, message: str)
            - (True, "Success") if credentials are correct
            - (False, "Invalid credentials") if wrong
            - (False, "Account locked") if max attempts exceeded
        """
        
        # Check if already locked out
        if self.failed_attempts >= self.max_attempts:
            logger.warning(f"Authentication locked after {self.max_attempts} failed attempts")
            return False, f"Account locked after {self.max_attempts} failed attempts"
        
        try:
            # Use PAM to verify the password
            p = pam.pam()
            if p.authenticate(username, password):
                logger.info(f"Authentication successful for user: {username}")
                self.failed_attempts = 0  # Reset counter on success
                return True, "Success"
            else:
                self.failed_attempts += 1
                remaining = self.max_attempts - self.failed_attempts
                msg = f"Invalid credentials. {remaining} attempts remaining."
                logger.warning(f"Failed login attempt {self.failed_attempts} for {username}")
                return False, msg
        
        except Exception as e:
            logger.error(f"PAM authentication error: {e}")
            return False, "Authentication service error"
    
    def reset_attempts(self):
        """Reset the failed attempt counter."""
        self.failed_attempts = 0
