from supabase import create_client, Client
import config

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

def save_orders(order_details: str, client_address: str, client_phone: str) -> bool:
    """
    Save an order to the Supabase `orders` table.

    Args:
        order_details (str): Details about the order.
        client_address (str): Client's address.
        client_phone (str): Client's phone number.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    # Input validation
    if not all([order_details, client_address, client_phone]):
        print("Validation Error: All fields are required.")
        return False

    # Prepare the order dictionary
    order = {
        "orderDetails": order_details,
        "clientAddress": client_address,
        "clientPhone": client_phone,
    }

    try:
        # Insert the order into the `orders` table
        response = supabase.table("orders").insert(order).execute()
        # Successful insertion
        print("Order saved successfully:", response.data)
        return True

    except Exception as e:
        # Handle unexpected errors
        print("Unexpected error:", str(e))
        return False

def get_latest_order(client_phone: str) -> dict:
    """
    Get the latest order for a specific client.

    Args:
        client_phone (str): Client's phone number.

    Returns:
        dict: The latest order details or None if no order found.
    """
    try:
        response = supabase.table("orders") \
            .select("*") \
            .eq("clientPhone", client_phone) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    except Exception as e:
        print("Error fetching latest order:", str(e))
        return None

def update_order(order_id: str, order_details: str, client_address: str) -> bool:
    """
    Update an existing order in the Supabase `orders` table.

    Args:
        order_id (str): The ID of the order to update.
        order_details (str): New details about the order.
        client_address (str): New client's address.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    # Input validation
    if not all([order_id, order_details, client_address]):
        print("Validation Error: All fields are required.")
        return False

    # Prepare the update dictionary
    update_data = {
        "orderDetails": order_details,
        "clientAddress": client_address,
    }

    try:
        # Update the order in the `orders` table
        response = supabase.table("orders") \
            .update(update_data) \
            .eq("id", order_id) \
            .execute()
        
        # Successful update
        print("Order updated successfully:", response.data)
        return True

    except Exception as e:
        print("Error updating order:", str(e))
        return False

def delete_order(order_id: str) -> bool:
    """
    Delete an order from the Supabase `orders` table.

    Args:
        order_id (str): The ID of the order to delete.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    if not order_id:
        print("Validation Error: Order ID is required.")
        return False

    try:
        # Delete the order from the `orders` table
        response = supabase.table("orders") \
            .delete() \
            .eq("id", order_id) \
            .execute()
        
        # Successful deletion
        print("Order deleted successfully")
        return True

    except Exception as e:
        print("Error deleting order:", str(e))
        return False