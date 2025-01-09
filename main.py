import threading
from datetime import datetime
import asyncio
from flask import Flask, request
import queue
from threading import Thread, Lock
from functools import wraps

from mongodb_api import create_page_token, create_user, get_user, update_messages
from openai_api import ask_openai_assistant
from fb_graph_api import send_message_to_fb_messenger
from whatsapp_api import WhatsAppAPI
from instagram_api import send_message_to_instagram
import config
from utils import format_messages

app = Flask(__name__)

# Dictionary to store a queue for each user
user_queues = {}

# Lock to synchronize access to user_queues
user_queues_lock = Lock()

# Initialize messaging APIs
whatsapp = WhatsAppAPI()

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

@app.get("/")
def handle_home():
    print("Home endpoint called")
    return "Server is running!", 200

@app.route('/facebook', methods=['GET'])
def facebook_verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    try:
        if mode == 'subscribe' and token == config.VERIFY_TOKEN:
            print('WEBHOOK_VERIFIED')
            return challenge, 200
        else:
            return "BAD_REQUEST", 403
    except:
        return "BAD_REQUEST", 403

@app.route('/instagram', methods=['GET'])
def instagram_verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    try:
        if mode == 'subscribe' and token == config.VERIFY_TOKEN:
            print('INSTAGRAM_WEBHOOK_VERIFIED')
            return challenge, 200
        else:
            return "BAD_REQUEST", 403
    except:
        return "BAD_REQUEST", 403

@app.route('/instagram', methods=['POST'])
@async_route
async def instagram_webhook():
    try:
        print('=== INSTAGRAM WEBHOOK REQUEST ===')
        print('Headers:', request.headers)
        body = request.get_json()
        print('Raw webhook payload:', body)
        
        # Extract the message data
        if 'entry' in body and len(body['entry']) > 0:
            entry = body['entry'][0]
            print('Entry:', entry)
            
            # Handle messaging format (new Instagram format)
            if 'messaging' in entry:
                messaging = entry['messaging'][0]
                sender_id = messaging.get('sender', {}).get('id')
                message = messaging.get('message', {})
                message_text = message.get('text')
                
                if sender_id and message_text:
                    print(f"Processing Instagram message from {sender_id}: {message_text}")
                    try:
                        
                        # Process the message
                        print("Calling OpenAI assistant...")
                        await call_ask_openai_assistant_and_send_message(
                            query=message_text,
                            recipient_id=sender_id,
                            platform="instagram"
                        )
                        print("Message processing initiated successfully")
                    except Exception as e:
                        print(f"Error in message processing: {str(e)}")
                    return "OK", 200
                else:
                    print("Missing sender_id or message_text")
            
            # Handle changes format (old Instagram format)
            elif 'changes' in entry:
                change = entry['changes'][0]
                if change.get('field') == 'messages':
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    if messages:
                        message = messages[0]
                        from_id = message.get('from')
                        message_text = message.get('text', {}).get('body')
                        
                        if from_id and message_text:
                            print(f"Processing Instagram message from {from_id}: {message_text}")
                            try:
                                mark_message_as_seen(from_id)
                                await call_ask_openai_assistant_and_send_message(
                                    query=message_text,
                                    recipient_id=from_id,
                                    platform="instagram"
                                )
                            except Exception as e:
                                print(f"Error in message processing: {str(e)}")
                            return "OK", 200
            else:
                print("No recognized message format in entry")
        else:
            print("No valid entry found in webhook payload")
        
        print("=== END INSTAGRAM WEBHOOK REQUEST ===")
        return "OK", 200
    except Exception as e:
        print(f"Error processing Instagram webhook: {str(e)}")
        return "ERROR", 500

@app.route('/whatsapp', methods=['GET'])
def whatsapp_verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    try:
        if mode == 'subscribe' and token == config.VERIFY_TOKEN:
            print('WHATSAPP_WEBHOOK_VERIFIED')
            return challenge, 200
        else:
            return "BAD_REQUEST", 403
    except:
        return "BAD_REQUEST", 403

@app.route('/whatsapp', methods=['POST'])
@async_route
async def whatsapp_webhook():
    try:
        print('A new WhatsApp message request...')
        body = request.get_json()
        
        # Extract the message data
        if 'entry' in body and len(body['entry']) > 0:
            entry = body['entry'][0]
            if 'changes' in entry and len(entry['changes']) > 0:
                change = entry['changes'][0]
                if change.get('value', {}).get('messages'):
                    message = change['value']['messages'][0]
                    
                    # Extract message details
                    message_id = message['id']
                    recipient_phone = message['from']
                    if 'text' in message and 'body' in message['text']:
                        query = message['text']['body']                        
                        # Process the message
                        await call_ask_openai_assistant_and_send_message(
                            query=query,
                            recipient_id=recipient_phone,
                            platform="whatsapp"
                        )
                        
                        return "OK", 200
        
        return "OK", 200
    except Exception as e:
        print(f"Error processing WhatsApp webhook: {str(e)}")
        return "ERROR", 500

@app.route('/facebook', methods=['POST'])
@async_route
async def facebook_webhook():
    try:
        print('A new Facebook Messenger request...')
        body = request.get_json()
        
        # Extract the message data
        if 'entry' in body and len(body['entry']) > 0:
            entry = body['entry'][0]
            if 'messaging' in entry and len(entry['messaging']) > 0:
                message_data = entry['messaging'][0]
                
                # Extract message details
                recipient_id = message_data['sender']['id']
                if 'message' in message_data and 'text' in message_data['message']:
                    query = message_data['message']['text']
                    
                    print(query)
                    print(recipient_id)
                    print(entry.get('id'))
                    
                    # Process the message
                    await call_ask_openai_assistant_and_send_message(
                        query=query,
                        recipient_id=recipient_id,
                        platform="facebook",
                        page_id=entry.get('id')
                    )
                    
                    return "OK", 200
        
        return "OK", 200
    except Exception as e:
        print(f"Error processing Facebook webhook: {str(e)}")
        return "ERROR", 500

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