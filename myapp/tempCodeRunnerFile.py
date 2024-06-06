from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken


key = b'yV8RmnaiJ-f4o1kaGyYiJKjm2wSaqOJhRsjvzTD0Tv8='
cipher_suite = Fernet(key)

# Encrypt a message
message = "This is a test message"
encrypted_message = cipher_suite.encrypt(message.encode()).decode()
print(f"Encrypted message: {encrypted_message}")

# Decrypt the message
try:
    decrypted_message = cipher_suite.decrypt(encrypted_message.encode()).decode()
    print(f"Decrypted message: {decrypted_message}")
except InvalidToken as e:
    print(f"Decryption failed: {e}")