from dotenv import load_dotenv
from cryptography.fernet import Fernet
import base64
import os

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

def encrypt_key(api_key:str):
    key = ENCRYPTION_KEY
    f = Fernet(key)
    encrypted_bytes = f.encrypt(api_key.encode())
    # Convert the encrypted bytes to a Base64-encoded string
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def decrypt_key(encrypted_base64_string:str):
    key = ENCRYPTION_KEY
    f = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_base64_string.encode('utf-8'))
    return f.decrypt(encrypted_bytes).decode('utf-8')