from supabase import create_client, Client
from datetime import datetime
import config
import asyncio
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def get_thread(recipient_id: str) -> dict | None:
    response = supabase.table('threads').select('*').eq('recipient_id', recipient_id).execute()
    if response.data:
        return response.data[0]
    return None

def create_thread(thread: dict) -> bool:
    response = supabase.table('threads').insert(thread).execute()
    return True

def update_thread(recipient_id: str, thread_id: str) -> bool:
    response = supabase.table('threads').update({'thread_id': thread_id}).eq('recipient_id', recipient_id).execute()
    return True

def get_page_token(page_id: str) -> dict | None:
    print('------hii--------')
    response = supabase.table('page_tokens').select('*').eq('page_id', page_id).execute()
    print('------------------')
    print(response)
    if response.data:
        return response.data[0]
    return None

def create_page_token(page_token: dict) -> bool:
    response = supabase.table('page_tokens').insert(page_token).execute()
    return True

def update_messages(recipient_id: str, query: str, response_text: str) -> bool:
    # Fetch the current messages
    user_data = supabase.table('users').select('messages').eq('recipient_id', recipient_id).execute()
    
    if not user_data.data:
        print(f"No user found with recipient_id: {recipient_id}")
        return False
    
    # Update the messages
    messages = user_data.data[0]['messages']
    messages.append({'query': query, 'response': response_text})
    response = supabase.table('users').update({'messages': messages}).eq('recipient_id', recipient_id).execute()
    return True

def create_user(user: dict) -> bool:
    user['created_at'] = datetime.now().isoformat()
    response = supabase.table('users').insert(user).execute()
    return True

def create_user_chat(user_data):
    user_data['created_at'] = datetime.now().isoformat()
    response = supabase.table('users').insert(user_data).execute()
    return response.data


def get_user(recipient_id: str) -> dict | None:
    response = supabase.table('users').select('*').eq('recipient_id', recipient_id).execute()
    if response.data:
        return response.data[0]
    return None