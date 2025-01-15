from supabase import create_client, Client
import config
import requests

def format_messages(messages: list[dict[str, any]]) -> list[dict[str, str]]:
    """Format messages for OpenAI conversation history"""
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            # Handle message format {"query": "...", "response": "..."}
            if "query" in msg and "response" in msg:
                formatted_messages.append({
                    "role": "user",
                    "content": str(msg['query'])
                })
                formatted_messages.append({
                    "role": "assistant",
                    "content": str(msg['response'])
                })
            # Handle message format {"message": "...", "role": "..."}
            elif "message" in msg and "role" in msg:
                formatted_messages.append({
                    "role": str(msg["role"]),
                    "content": str(msg["message"])
                })
            # Handle message format {"text": "...", "sender": "..."}
            elif "text" in msg and "sender" in msg:
                role = "assistant" if msg["sender"] == "bot" else "user"
                formatted_messages.append({
                    "role": role,
                    "content": str(msg["text"])
                })
    return formatted_messages

