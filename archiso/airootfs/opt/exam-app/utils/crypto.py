"""
crypto.py - GPG encryption and decryption utilities

Handles all encryption/decryption operations:
- Decrypt questions.gpg (encrypted question file from bootable drive)
- Encrypt answers.gpg (student responses)
- Uses python-gnupg for secure operations
"""

import gnupg
import json
import logging
import os
from typing import Tuple, Dict, Optional
import json

logger = logging.getLogger(__name__)


class ExamCrypto:
    """Manages GPG encryption/decryption for exam data."""
    
    def __init__(self, gpg_home: str = "/etc/exam-gnupg"):
        """
        Initialize GPG wrapper.
        
        Args:
            gpg_home: Path to GPG home directory (default: /etc/exam-gnupg)
        """
        self.gpg_home = gpg_home
        self.gpg = gnupg.GPG(gnupghome=gpg_home)
        self.question_key_id = None
        self.answer_key_id = None
    
    def load_keyring(self) -> bool:
        """
        Load GPG keys from the system.
        
        Returns:
            True if keys loaded successfully, False otherwise
        """
        try:
            # List available keys
            keys = self.gpg.list_keys()
            if not keys:
                logger.error("No GPG keys found in keyring")
                return False
            
            # For now, use the first available key
            # In production, you would select keys by specific criteria
            if len(keys) >= 1:
                self.question_key_id = keys[0]['keyid']
                logger.info(f"Loaded GPG key: {self.question_key_id}")
            
            if len(keys) >= 2:
                self.answer_key_id = keys[1]['keyid']
            else:
                # Use same key for both if only one available
                self.answer_key_id = self.question_key_id
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to load GPG keyring: {e}")
            return False
    
    def decrypt_questions(self, encrypted_file: str) -> Tuple[bool, Optional[Dict]]:
        """
        Decrypt the questions file from the bootable drive.
        
        Args:
            encrypted_file: Path to questions.gpg file
        
        Returns:
            Tuple of (success: bool, questions_dict: Optional[Dict])
        """
        try:
            if not os.path.exists(encrypted_file):
                logger.error(f"Questions file not found: {encrypted_file}")
                return False, None
            
            # Read encrypted file
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted = self.gpg.decrypt(encrypted_data)
            
            if not decrypted.ok:
                logger.error(f"Decryption failed: {decrypted.status}")
                return False, None
            
            # Parse JSON
            questions_dict = json.loads(str(decrypted))
            logger.info(f"Successfully decrypted questions file with {len(questions_dict.get('questions', []))} questions")
            return True, questions_dict
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in decrypted questions: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error decrypting questions: {e}")
            return False, None
    
    def encrypt_answers(self, answers_data: Dict, output_file: str) -> Tuple[bool, str]:
        """
        Encrypt student answers and save to file.
        
        Args:
            answers_data: Dictionary containing student responses
            output_file: Path where to save answers.gpg
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Convert to JSON string
            json_string = json.dumps(answers_data, indent=2)
            
            # Encrypt using public key
            encrypted = self.gpg.encrypt(json_string, self.answer_key_id, always_trust=True)
            
            if not encrypted.ok:
                logger.error(f"Encryption failed: {encrypted.status}")
                return False, f"Encryption failed: {encrypted.status}"
            
            # Write encrypted file
            with open(output_file, 'wb') as f:
                f.write(bytes(encrypted))
            
            # Securely delete plaintext from memory (best effort)
            del json_string
            
            logger.info(f"Successfully encrypted answers to {output_file}")
            return True, f"Answers encrypted successfully"
        
        except Exception as e:
            logger.error(f"Error encrypting answers: {e}")
            return False, f"Encryption error: {str(e)}"
    
    def export_public_key(self, output_file: str) -> bool:
        """
        Export the public key to a file (used by admin for creating questions).
        
        Args:
            output_file: Path where to save the public key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = self.gpg.export_keys(self.answer_key_id)
            with open(output_file, 'w') as f:
                f.write(key)
            logger.info(f"Exported public key to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export public key: {e}")
            return False
