from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from passlib.hash import pbkdf2_sha256
from cryptography.fernet import Fernet
import random
import string
from cryptography.fernet import InvalidToken

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('chats', lazy=True))
    chat_list = db.Column(db.JSON, nullable=False, default=list)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(50), nullable=False, unique=True)
    messages = db.relationship('ChatMessage', backref='message', lazy=True)

    @staticmethod
    def generate_room_id():
        # Generate a random alphanumeric room ID
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(400))
    timestamp = db.Column(db.String(20), nullable=False)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_username = db.Column(db.String(50), nullable=False)
    room_id = db.Column(db.String(50), db.ForeignKey('messages.room_id'), nullable=False)
    encrypted_content = db.Column(db.Text)
    key = b'yV8RmnaiJ-f4o1kaGyYiJKjm2wSaqOJhRsjvzTD0Tv8='
    cipher_suite = Fernet(key)

    def encrypt_message(self, message):
        self.encrypted_content = self.cipher_suite.encrypt(message.encode()).decode()
        self.content = None

    def decrypt_message(self):
        try:
            if self.encrypted_content:
                #print(f"Attempting to decrypt: {self.encrypted_content}")
                decrypted_message = self.cipher_suite.decrypt(self.encrypted_content.encode()).decode()
                return decrypted_message
            else:
                return None
        except InvalidToken as e:
            print(f"Decryption failed for content: {self.encrypted_content} - Error: {e}")
            return "Decryption failed"
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()