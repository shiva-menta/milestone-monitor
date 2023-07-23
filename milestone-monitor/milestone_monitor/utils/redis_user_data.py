# Functions for keeping track of user data

import redis
import json
import sys
from backend.settings import REDIS_QUEUE_LENGTH
from backend.redis import get_redis_client
from typing import Tuple, List
from datetime import datetime

r = get_redis_client()


# create message history object for a user if not there
def create_default_user_hist(number):
    key = number
    data = {
        "current_convo_type": "main",
        "main_memory": [],
        "create_goal_memory": [],
        "current_field_entries": {},
        "last_user_message_time": "",
        "current_field_entries_last_modified": ""
    }

    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


# get a user's stored data
def get_user_hist(number):
    key = number
    json_data_retrieved = r.hget(str(key), "data")

    if not json_data_retrieved:
        create_default_user_hist(number)
        json_data_retrieved = r.hget(str(key), "data")

    data_retrieved = json.loads(json_data_retrieved)

    return data_retrieved


# update a user's convo type ONLY
def update_user_convo_type(number, convo_type):
    if convo_type != "main" and convo_type != "create_goal":
        raise Exception("Invalid convo type.")

    key = number
    data = get_user_hist(key)

    data["current_convo_type"] = convo_type

    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


# Saves a user's message history with a new memory dict, keeping the max window of messages
# This should be used when providing a new memory dict to REPLACE the current memory,
# like with LangChain's API
def save_user_msg_memory(number, convo_type, memory_list):
    print(">>> Updating user msg memory (saving with new)")
    if convo_type not in ["main", "create_goal"]:
        raise Exception("Invalid convo type.")
    if type(memory_list) is not list:
        raise Exception("Invalid type for mem.")

    key = number
    data = get_user_hist(key)
    data["main_memory"] = memory_list[-REDIS_QUEUE_LENGTH:]
    print(data["main_memory"])

    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


# Extends the current message history by ADDING messages to it
# This should be used
def extend_user_msg_memory(number, convo_type, memory_list):
    print(">>> Updating user msg memory (adding extra messages)")
    if convo_type not in ["main", "create_goal"]:
        raise Exception("Invalid convo type.")
    if type(memory_list) is not list:
        raise Exception("Invalid type for mem.")

    key = number
    data = get_user_hist(key)
    data["main_memory"].extend(memory_list)
    data["main_memory"] = data["main_memory"][-REDIS_QUEUE_LENGTH:]
    print(data["main_memory"])

    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


def update_current_goal_creation_field_entries(number, field_entries, last_modified):
    key = number
    data = get_user_hist(key)

    data["current_field_entries"] = field_entries
    data["current_field_entries_last_modified"] = datetime.strftime(last_modified, "%m/%d/%Y %H:%M")
    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)

def update_last_modified(number, last_modified):
    key = number
    data = get_user_hist(key)

    data["last_user_message_time"] = datetime.strftime(last_modified, "%Y-%m-%d %H:%M:%S")
    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)

def reset_current_goal_creation_field_entries(number):
    key = number
    data = get_user_hist(key)

    data["current_field_entries"] = {}
    data["current_field_entries_last_modified"] = ""
    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


# checks whether or not the chatbot is currently responding (so we shouldn't)
# start another chain
def check_active_conversation(number):
    return r.sismember("active-conversations", number)


# sets a user's conversation as "active" (chatbot is responding)
def set_conversation_active(number):
    return r.sadd("active-conversations", number)


# sets a user's conversation as "inactive" (chatbot is done responding)
def set_conversation_inactive(number):
    return r.srem("active-conversations", number)


# enqueues a user message to be processed when chatbot is done responding
def pend_user_message(number, message):
    chat_msg_queue = f"pending-msgs-{number}"
    to_queue_msg = json.dumps({"type": "user", "content": message})
    return r.lpush(chat_msg_queue, to_queue_msg)


# pops all pending messages
def pop_pending_messages(number) -> Tuple[List[str], List[str]]:
    chat_msg_queue = f"pending-msgs-{number}"
    queued_msgs_list = r.lrange(chat_msg_queue, 0, -1)

    # Remove all messages right after we copy all of them
    r.ltrim(chat_msg_queue, 1, 0)

    user_msgs = []
    reminder_msgs = []
    for msg_raw in queued_msgs_list:
        msg_obj = json.loads(msg_raw.decode("utf-8"))
        if msg_obj["type"] == "user":
            user_msgs.append(msg_obj["content"])
        elif msg_obj["type"] == "reminder":
            reminder_msgs.append(msg_obj["content"])
    return user_msgs, reminder_msgs
