
import config
import requests
from mongodb import client, db


def format_messages(messages: list[dict[str, any]]) -> list[dict[str, str]]:
    """Format messages for OpenAI conversation history"""
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            if "query" in msg and "response" in msg:
                formatted_messages.append({
                    "role": "user",
                    "content": str(msg['query'])
                })
                formatted_messages.append({
                    "role": "assistant",
                    "content": str(msg['response'])
                })
            elif "message" in msg and "role" in msg:
                formatted_messages.append({
                    "role": str(msg["role"]),
                    "content": str(msg["message"])
                })
            elif "text" in msg and "sender" in msg:
                role = "assistant" if msg["sender"] == "bot" else "user"
                formatted_messages.append({
                    "role": role,
                    "content": str(msg["text"])
                })
    return formatted_messages

def save_orders(order_details: str, client_address: str, client_phone: str) -> bool:
    if not all([order_details, client_address, client_phone]):
        print("Validation Error: All fields are required.")
        return False
        
    order = {
        "orderDetails": order_details,
        "clientAddress": client_address,
        "clientPhone": client_phone,
        "status": "pending"
    }
    
    try:
        result = db.orders.insert_one(order)
        print("Order saved successfully with ID:", result.inserted_id)
        return bool(result.inserted_id)

    except Exception as e:
        print("Unexpected error:", str(e))
        return False