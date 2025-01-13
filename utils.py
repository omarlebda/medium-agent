from supabase import create_client, Client
import config
import requests
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

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

def save_request(request_data: dict) -> bool:
    """
    Send a request to the specified API URL.

    Args:
        request_data (dict): A dictionary containing request details:
            {
                "name": str,
                "type": str,
                "from": str,
                "reply": str,
                "subject": str,
                "actAsType": str,
                "message": str
            }

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    # Validate input
    required_fields = ["name", "type", "from", "reply", "subject", "actAsType", "message"]
    if not all(field in request_data for field in required_fields):
        print("Validation Error: Missing required fields.")
        return False

    # Define API endpoint and headers
    api_url = "http://34.123.117.78:8080/api/v1/ticket"
    headers = {
        "Authorization": "Basic GKA2B24H1Q9WWNKTMSWSJ1QKTOGC8XN5SMBBUVEWDCTY16ZTE3ZZZKAOSMSPFSFD",
        "Content-Type": "application/json"
    }

    try:
        # Send POST request to the API
        response = requests.post(api_url, json=request_data, headers=headers)

        # Check for a successful response
        if response.status_code == 200:
            print("Request sent successfully:", response.json())
            return True
        else:
            print(f"Failed to send request. Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print("Error sending request:", str(e))
        return False