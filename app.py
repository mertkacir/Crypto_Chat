from myapp import create_app
from myapp.database import db, Message, ChatMessage
from flask_socketio import emit, join_room, leave_room
from cryptography.fernet import Fernet
import logging

logging.basicConfig(level=logging.DEBUG)
from flask_migrate import Migrate

app, socket = create_app()
migrate = Migrate(app, db)

# Specify the secret key directly
secret_key = b'yV8RmnaiJ-f4o1kaGyYiJKjm2wSaqOJhRsjvzTD0Tv8='
cipher_suite = Fernet(secret_key)

# COMMUNICATION ARCHITECTURE

# Join-chat event. Emit online message to other users and join the room
@socket.on("join-chat")
def join_private_chat(data):
    room_id = data['rid']
    join_room(room_id)
    messages = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.timestamp).all()
    decrypted_messages = []

    for chat_message in messages:
        if chat_message.encrypted_content is not None:
            #logging.debug(f"Attempting to decrypt: {chat_message.encrypted_content}")
            try:
                decrypted_content = cipher_suite.decrypt(chat_message.encrypted_content.encode()).decode()
            except Exception as e:
                logging.error(f"Decryption failed for content: {chat_message.encrypted_content} - Error: {e}")
                decrypted_content = "Decryption failed"
            decrypted_messages.append({
                'timestamp': chat_message.timestamp,
                'sender_username': chat_message.sender_username,
                'sender_id': chat_message.sender_id,
                'message': decrypted_content
            })
        else:
            logging.error(f"Encrypted content is None for message ID {chat_message.id}")
            decrypted_messages.append({
                'timestamp': chat_message.timestamp,
                'sender_username': chat_message.sender_username,
                'sender_id': chat_message.sender_id,
                'message': None
            })

    emit('joined-chat', {'messages': decrypted_messages}, room=room_id)

@socket.on("message")
def handle_message(json):
    room_id = json["rid"]
    sender_username = json["sender_username"]
    timestamp = json["timestamp"]
    
    # Decrypt the message before displaying it
    #logging.debug(f"Attempting to decrypt: {json['message']}")
    try:
        decrypted_message = cipher_suite.decrypt(json["message"].encode()).decode()
    except Exception as e:
        logging.error(f"Decryption failed for incoming message - Error: {e}")
        decrypted_message = "Decryption failed"

    # Emit the decrypted message to the client
    decrypted_json = {
        "rid": room_id,
        "sender_username": sender_username,
        "timestamp": timestamp,
        "message": decrypted_message
    }
    socket.emit("message", decrypted_json, room=room_id, include_self=False)

# Outgoing event handler
@socket.on("outgoing")
def chatting_event(json, methods=["GET", "POST"]):
    """
    handles saving messages and sending messages to all clients
    :param json: json
    :param methods: POST GET
    :return: None
    """
    room_id = json["rid"]
    timestamp = json["timestamp"]
    message = json["message"]
    sender_id = json["sender_id"]
    sender_username = json["sender_username"]

    # Get the message entry for the chat room
    message_entry = Message.query.filter_by(room_id=room_id).first()

    encrypted_message = cipher_suite.encrypt(message.encode()).decode()
    # Add the new message to the conversation
    chat_message = ChatMessage(
        encrypted_content=encrypted_message,
        timestamp=timestamp,
        sender_id=sender_id,
        sender_username=sender_username,
        room_id=room_id,
    )
    # Add the new chat message to the messages relationship of the message
    message_entry.messages.append(chat_message)

    # Updated the database with the new message
    try:
        chat_message.save_to_db()
        message_entry.save_to_db()
    except Exception as e:
        # Handle the database error, e.g., log the error or send an error response to the client.
        logging.error(f"Error saving message to the database: {e}")
        db.session.rollback()

    # Emit the message(s) sent to other users in the room
    socket.emit(
        "message",
        json,
        room=room_id,
        include_self=False,
    )

if __name__ == "__main__":
    socket.run(app, allow_unsafe_werkzeug=True, debug=True)