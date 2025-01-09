from typing import Dict, Any
import json
import requests
import os
from dotenv import load_dotenv

class WhatsAppAPI:
    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.base_url = "https://graph.facebook.com/v17.0"
        
        print(f"Initialized WhatsApp API with phone_number_id: {self.phone_number_id}")

    def send_message(self, recipient_phone: str, message_text: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message to a recipient
        """
        try:
            # Construct the API endpoint for sending messages using phone_number_id
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Prepare headers with access token
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare the message payload according to WhatsApp Cloud API format
            data = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": "text",
                "text": {
                    "body": message_text.strip('"')  # Remove quotes that might cause issues
                }
            }
            
            print(f"\nSending WhatsApp message...")
            print(f"Phone Number ID: {self.phone_number_id}")
            print(f"URL: {url}")
            print(f"To: {recipient_phone}")
            print(f"Message: {message_text}")
            
            # Make the API request
            response = requests.post(url, headers=headers, json=data)
            
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"error": "Invalid JSON response", "text": response.text}
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200:
                print("WhatsApp message sent successfully")
                return response_json
            else:
                error_msg = response_json.get('error', {})
                if error_msg.get('code') == 131030:
                    print("\nERROR: Phone number not in allowed test recipients")
                    print("Please add this number to your WhatsApp test recipients in Meta Developer Console")
                    print("1. Go to developers.facebook.com")
                    print("2. Navigate to your app")
                    print("3. Go to WhatsApp > Getting Started")
                    print("4. Add phone number to test recipients")
                elif error_msg.get('code') == 100:
                    print("\nERROR: Invalid access token or permissions")
                    print("Please check your WhatsApp access token and permissions")
                else:
                    print(f"\nERROR: Failed to send WhatsApp message")
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text}")
                return response_json
                
        except Exception as e:
            error_msg = f"Error sending WhatsApp message: {str(e)}"
            print(error_msg)
            return {"error": error_msg}

    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a WhatsApp message as read
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"error": "Invalid JSON response", "text": response.text}
            
            if response.status_code == 200:
                print("Message marked as read successfully")
            else:
                print(f"Failed to mark message as read: {response.text}")
                
            return response_json
            
        except Exception as e:
            error_msg = f"Error marking message as read: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
