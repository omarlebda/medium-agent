from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import config


client = MongoClient(config.MONGODB_URI, server_api=ServerApi('1'))
db = client[config.MONGODB_DATABASE]

def get_thread(recipient_id: str) -> dict | None:
    thread = db.threads.find_one({"recipient_id": recipient_id})
    return thread

def create_thread(thread: dict) -> bool:
    result = db.threads.insert_one(thread)
    return bool(result.inserted_id)

def update_thread(recipient_id: str, thread_id: str) -> bool:
    result = db.threads.update_one(
        {"recipient_id": recipient_id},
        {"$set": {"thread_id": thread_id}}
    )
    return bool(result.modified_count)

def get_page_token(page_id: str) -> dict | None:
    token = db.page_tokens.find_one({"page_id": page_id})
    return token

def create_page_token(page_token: dict) -> bool:
    result = db.page_tokens.insert_one(page_token)
    return bool(result.inserted_id)

def update_messages(recipient_id: str, query: str, response_text: str) -> bool:
    result = db.users.update_one(
        {"recipient_id": recipient_id},
        {"$push": {"messages": {"query": query, "response": response_text}}}
    )
    return bool(result.modified_count)

def create_user(user: dict) -> bool:
    user['created_at'] = datetime.now()
    result = db.users.insert_one(user)
    return bool(result.inserted_id)

def create_user_chat(user_data: dict) -> dict:
    user_data['created_at'] = datetime.now()
    result = db.users.insert_one(user_data)
    return db.users.find_one({"_id": result.inserted_id})

def get_user(recipient_id: str) -> dict | None:
    user = db.users.find_one({"recipient_id": recipient_id})
    return user