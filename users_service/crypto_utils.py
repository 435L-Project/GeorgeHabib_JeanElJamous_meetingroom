from cryptography.fernet import Fernet
import os

# Try to get the key from the environment (Docker way)
key = os.environ.get('ENCRYPTION_KEY')

# If no key is found (Local/Windows way), use this hardcoded backup key
if not key:
    print("Warning: No ENCRYPTION_KEY found. Using fallback key for local testing.")
    # This is a valid 32-byte URL-safe base64 key generated for testing
    key = b'8coS7-02q7v5dJ1_J9XyZ4T9xQ6r8m3n2b1v4c5x6z7='

cipher_suite = Fernet(key)

def encrypt_data(data):
    """Encrypts a string."""
    if not data:
        return ""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """Decrypts a string."""
    if not encrypted_data:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return "[Encrypted Data]"