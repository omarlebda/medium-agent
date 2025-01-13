import threading
from datetime import datetime
import asyncio
from flask import Flask, request
import queue
from threading import Thread, Lock
from functools import wraps

from mongodb_api import create_page_token, create_user, get_user, update_messages
from openai_api import ask_openai_assistant
import config
from utils import format_messages
from mongodb_api import create_thread, get_thread
app = Flask(__name__)

# Dictionary to store a queue for each user
user_queues = {}

# Lock to synchronize access to user_queues
user_queues_lock = Lock()
def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

@app.get("/")
def handle_home():
    print("Home endpoint called")
    return "Server is running!", 200


@app.route('/chat', methods=['POST'])
@async_route
async def chat_api():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return {
                'error': 'Missing required field: message'
            }, 400
            
        query = data['message']
        recipient_id = data.get('recipient_id')
        
        # Generate a unique recipient_id if not provided
        if not recipient_id:
            from uuid import uuid4
            recipient_id = str(uuid4())

        # Process the message and get response
        response = await call_ask_openai_assistant_and_send_message(
            query=query,
            recipient_id=recipient_id,
            platform="api"
        )
        
        # Get thread info
        thread = get_thread(recipient_id=recipient_id)
        
        return {
            'recipient_id': recipient_id,
            'thread_id': thread['thread_id'] if thread else None,
            'message': query,
            'response': response
        }, 200
        
    except Exception as e:
        print(f"Error in chat API: {str(e)}")
        return {
            'error': str(e)
        }, 500

async def call_ask_openai_assistant_and_send_message(query: str, recipient_id: str, platform: str, page_id: str = None):
    """Call OpenAI assistant and send the response message"""
    try:
        print(f"\n=== PROCESSING MESSAGE ===")
        print(f"Platform: {platform}")
        print(f"Recipient: {recipient_id}")
        print(f"Query: {query}")
        
        # Get or create user
        user = get_user(recipient_id=recipient_id)
        if not user:
            print("Creating new user...")
            user = {
                'recipient_id': recipient_id,
                'messages': [],
                'channel': platform,
                'created_at': datetime.now().strftime('%d/%m/%Y, %H:%M')
            }
            create_user(user)
            user = get_user(recipient_id=recipient_id)
        print("User found:", user)
        
        # Format messages
        messages = []
        if user and user.get("messages"):
            try:
                # Get last 5 messages
                recent_messages = user["messages"][-5:]
                # Format each message, handling different message structures
                for msg in recent_messages:
                    if isinstance(msg, dict):
                        # Handle message format {"query": "...", "response": "..."}
                        if "query" in msg and "response" in msg:
                            messages.append({"role": "user", "content": msg["query"]})
                            messages.append({"role": "assistant", "content": msg["response"]})
                        # Handle message format {"message": "...", "role": "..."}
                        elif "message" in msg and "role" in msg:
                            messages.append({"role": msg["role"], "content": msg["message"]})
                        # Handle message format {"text": "...", "sender": "..."}
                        elif "text" in msg and "sender" in msg:
                            role = "assistant" if msg["sender"] == "bot" else "user"
                            messages.append({"role": role, "content": msg["text"]})
            except Exception as format_error:
                print(f"Error formatting messages: {format_error}")
                # Continue with empty message history if formatting fails
                messages = []
        
        print("Formatted messages:", messages)
        
        # Get response from OpenAI
        print("Getting response from OpenAI...")
        response = ask_openai_assistant(
            query=query,
            recipient_id=recipient_id,
            messages=messages
        )
        print("OpenAI response:", response)
        
        # Create new message entry
        new_message = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().strftime('%d/%m/%Y, %H:%M')
        }
        
        # Update messages in the database
        print("Updating messages in database...")
        update_messages(
            recipient_id=recipient_id,
            query=query,
            response_text=response
        )
        
        # Send the response based on platform
        print(f"Sending response via {platform}...")
        try:
            if platform == "facebook":
                send_message_to_fb_messenger(recipient_id, response, page_id)
            elif platform == "whatsapp":
                whatsapp.send_message(recipient_id, response)
            elif platform == "instagram":
                send_message_to_instagram(recipient_id, response)
            elif platform == "api":
                return response
            print(f"Message sent successfully via {platform}")
        except Exception as send_error:
            print(f"Error sending message via {platform}: {str(send_error)}")
            # Try to send error message
            error_msg = "I apologize, but I'm having trouble responding right now. Please try again in a moment."
            try:
                if platform == "facebook":
                    send_message_to_fb_messenger(recipient_id, error_msg, page_id)
                elif platform == "whatsapp":
                    whatsapp.send_message(recipient_id, error_msg)
                elif platform == "instagram":
                    send_message_to_instagram(recipient_id, error_msg)
            except:
                print("Failed to send error message")
        
        print("=== MESSAGE PROCESSING COMPLETE ===\n")
        
    except Exception as e:
        print(f"Error in call_ask_openai_assistant_and_send_message:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

if __name__ == '__main__':
    app.run(debug=True)