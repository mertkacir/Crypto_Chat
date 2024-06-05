from cryptography.fernet import Fernet
import base64

# Generate a new key
key = Fernet.generate_key()

# Convert the key to a URL-safe base64-encoded string
encoded_key = base64.urlsafe_b64encode(key)

print("Generated key:", encoded_key.decode())