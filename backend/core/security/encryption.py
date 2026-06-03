import base64
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken
from core.config import settings

logger = logging.getLogger(__name__)

class KeyVault:
    """
    Cryptographic vault for securing user API keys and sensitive credentials.
    Uses Fernet symmetric encryption derived from the system's root SECRET_KEY.
    """
    def __init__(self):
        # 1. Take the raw secret key from .env
        raw_key = settings.SECRET_KEY.get_secret_value().encode('utf-8')
        
        # 2. Hash it with SHA-256 to guarantee it is exactly 32 bytes long
        hashed_key = hashlib.sha256(raw_key).digest()
        
        # 3. Encode to url-safe base64 as required by the Fernet specification
        self._fernet_key = base64.urlsafe_b64encode(hashed_key)
        
        # 4. Initialize the cipher
        self._cipher = Fernet(self._fernet_key)

    def encrypt(self, plaintext_string: str) -> str:
        """Encrypts a plaintext string (like an API key) for secure database storage."""
        if not plaintext_string:
            return ""
        try:
            # Fernet requires bytes, so we encode the string, encrypt it, and decode back to a string
            encrypted_bytes = self._cipher.encrypt(plaintext_string.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("System failed to encrypt the provided data.")

    def decrypt(self, encrypted_string: str) -> str:
        """Decrypts a stored string back to plaintext for use by the LangGraph agents."""
        if not encrypted_string:
            return ""
        try:
            decrypted_bytes = self._cipher.decrypt(encrypted_string.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            logger.error("Decryption failed: Token is invalid, corrupted, or the SECRET_KEY changed.")
            raise ValueError("Decryption integrity check failed.")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("System failed to decrypt the provided data.")

# Create a single global vault instance
vault = KeyVault()