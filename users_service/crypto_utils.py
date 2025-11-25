from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = b'WiSMOi0a4KYxgVUV8hRhYGhSMXOuGeFnKLEg6Xc6rqg='

cipher_suite = Fernet(ENCRYPTION_KEY)

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