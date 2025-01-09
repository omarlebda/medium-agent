import requests
import asyncio

def send_message_to_instagram(recipient_id: str, message_text: str) -> None:
    try:
        url = f"https://graph.instagram.com/v21.0/me/messages?access_token=IGAAVsYZBGFNcBBZAFBFVl9yam12LVdNLVVnYU1PMVJ2bU9oOEoxVUp4Q29hdGgxOEg3bTZA1X29SVHFOZA1puRVNVVnJLUTROQkZALa201UmxQdUoteWJKM3kxTjFrMVhTTWlyOVhqcC15a00tV2dIZAEhINTJxTzJadXRibE54NVNtTQZDZD"
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        print("\nSending Instagram message...")
        print(f"URL: {url}")
        print(f"Recipient: {recipient_id}")
        print(f"Message: {message_text}")
        
        response = requests.post(url, json=data)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("INSTAGRAM MESSAGE SENT SUCCESSFULLY.")
        else:
            print(f"INSTAGRAM MESSAGE SENT FAILED. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print("EXCEPTION OCCURRED.")
        print(f"INSTAGRAM MESSAGE SENT FAILED: {str(e)}")
