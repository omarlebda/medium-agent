from datetime import datetime
from supabase import create_client, Client
import config

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def update_messages(recipient_id: str, query: str, response: str) -> bool:
    '''Update messages for the user and reduce the messages_count by one

    Parameters:
        - recipient_id(str): user telegram id
        - response(str): response of the bot
        - query(str): query of the user

    Returns:
        - bool: True for success, False for failure
    '''
    message = {
        'query': query,
        'response': response,
        'createdAt': datetime.now().strftime('%d/%m/%Y, %H:%M')
    }
    response = supabase.table('users').update({'messages': supabase.func.array_append('messages', message)}).eq('recipient_id', recipient_id).execute()
    return response.status == 200

def create_user(user: dict) -> bool:
    '''Process the whole body and update the db

    Parameters:
        - user(dict): the incoming request from Telegram

    Returns:
        - bool: True for success, False for failure
    '''
    response = supabase.table('users').insert(user).execute()
    return response.status_code == 201

def get_user(recipient_id: str) -> dict[str, any] | None:
    '''Get user

    Parameters:
        - recipient_id(str): sender id of the user

    Returns:
        - dict: User document if found, None otherwise
    '''
    response = supabase.table('users').select('*').eq('recipient_id', recipient_id).execute()
    if response.data:
        return response.data[0]
    return None

def get_thread(recipient_id: str) -> dict[str, any] | None:
    '''Get a thread by recipient_id.

    Parameters:
        - recipient_id (str): Recipient ID to search for

    Returns:
        - dict: Thread document if found, None otherwise
    '''
    response = supabase.table('threads').select('*').eq('recipient_id', recipient_id).execute()
    if response.data:
        return response.data[0]
    return None

def create_thread(thread: dict) -> bool:
    '''Create a new thread for a recipient_id.

    Parameters:
        - thread (dict): Thread document to insert

    Returns:
        - bool: True if the insertion was successful, False otherwise
    '''
    response = supabase.table('threads').insert(thread).execute()
    return response.status_code == 201

def update_thread(recipient_id: str, thread_id: str) -> bool:
    '''Update an existing thread in the collection.

    Parameters:
        - recipient_id (str): Recipient ID of the thread to update
        - thread_id (str): New thread id to store against the recipient_id

    Returns:
        - bool: True if the update was successful, False otherwise
    '''
    response = supabase.table('threads').update({'thread_id': thread_id}).eq('recipient_id', recipient_id).execute()
    return response.status_code == 200

def get_page_token(page_id: str) -> dict[str, any] | None:
    '''Get Page token

    Parameters:
        - page_id(str): Facebook page id

    Returns:
        - dict: Page token document if found, None otherwise
    '''
    response = supabase.table('page_tokens').select('*').eq('page_id', page_id).execute()
    if response.data:
        return response.data[0]
    return None

def create_page_token(page_token: dict) -> bool:
    '''Create a new page token for a page_id.

    Parameters:
        - page_token(dict): Page token for the page_id

    Returns:
        - bool: True if the insertion was successful, False otherwise
    '''
    response = supabase.table('page_tokens').insert(page_token).execute()
    return response.status_code == 201