from cryptography.fernet import Fernet
import os

key = os.environ.get('ENCRYPTION_KEY')

if not key:
    raise ValueError("No ENCRYPTION_KEY found in environment variables!")

cipher_suite = Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_data(plain_text):
    """Encrypts a string"""
    if not plain_text:
        return None
    encrypted_bytes = cipher_suite.encrypt(plain_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_data(encrypted_text):
    """Decrypts a string"""
    if not encrypted_text:
        return None
    decrypted_bytes = cipher_suite.decrypt(encrypted_text.encode('utf-8'))
    return decrypted_bytes.decode('utf-8')