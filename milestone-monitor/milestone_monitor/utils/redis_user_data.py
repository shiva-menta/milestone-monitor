# Functions for keeping track of user data

import redis
import json
from backend.settings import redis_url

r = redis.Redis.from_url("redis://localhost:6379")


# create message history object for a user if not there
def create_default_user_hist(number):
    key = number
    data = {
        "current_convo_type": "main",
        "main_memory": [],
        "create_goal_memory": [],
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


# update a user's message history ONLY
def update_user_msg_memory(number, convo_type, messages):
    if convo_type != "main" and convo_type != "create_goal":
        raise Exception("Invalid convo type.")
    if type(messages) is not list:
        raise Exception("Invalid type for messages.")

    key = number
    data = get_user_hist(key)

    if convo_type == "main":
        data["main_memory"] = messages
    else:
        data["create_goal_memory"] = messages

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
def pop_pending_messages(number) -> tuple[list[str], list[str]]:
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
