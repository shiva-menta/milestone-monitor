from celery import shared_task
from django.http import HttpResponse, JsonResponse
from celery_once import QueueOnce
from datetime import datetime

from backend.redis import get_redis_client
from utils.conversation_handler import chatbot_respond_ALT
from utils.sms import send_sms
from utils.redis_user_data import (
    get_user_hist,
    update_user_convo_type,
    extend_user_msg_memory,
    create_default_user_hist,
    update_last_modified
)

import json

r = get_redis_client()


@shared_task
def chatbot_respond_async(request_msg, request_sndr):
    print(">>> CALLED chatbot_respond_async")
    """
    Needs to do the following:
    1. Check if an existing conversation is in progress
    2. If so, adds the user's message to the queue (to be immediately
        send to the chatbot after it responds)
    3. Otherwise, need to start a response from the chatbot using `chatbot_respond`
        which will handle the process of sending a text message back to the user
    """
    chat_msg_queue = f"pending-msgs-{request_sndr}"
    

    # Reset the user's conversation type (for testing)
    # r.srem("active-conversations", request_sndr)

    if r.sismember("active-conversations", request_sndr):
        # Conversation is currently active, so we need to queue up the message
        print(">>> Conversation is currently active, queueing")

        # queue up the message
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M")
        to_queue_msg = json.dumps({"type": "user", "content": request_msg, "timestamp": timestamp})
        r.lpush(chat_msg_queue, to_queue_msg)
    else:
        # Conversation is not currently active, so we can respond immediately
        print(">>> Setting conversation as active")

        # Set the conversation as active
        r.sadd("active-conversations", request_sndr)

        # Initiate chatbot conversation
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M")
        update_last_modified(request_sndr, timestamp)
        chatbot_respond_ALT(request_msg, request_sndr)

        # Get messages in queue
        pipe = r.pipeline()
        pipe.lrange(chat_msg_queue, 0, -1)
        pipe.ltrim(chat_msg_queue, 1, 0)
        queued_msgs_list, _ = pipe.execute()

        # Handle incoming messages
        while queued_msgs_list:
            print(">>> Handling queued messages...")
            # Sort messages into user messages and reminder messages
            user_msgs = []
            reminder_msgs = []
            timestamp_set = False
            for msg_raw in queued_msgs_list:
                msg_obj = json.loads(msg_raw.decode("utf-8"))
                if msg_obj["type"] == "user":
                    if not timestamp_set:
                        update_last_modified(request_sndr, msg_obj["timestamp"])
                        timestamp_set = True
                    user_msgs.append(msg_obj["content"])
                elif msg_obj["type"] == "reminder":
                    reminder_msgs.append(msg_obj["content"])

            # Send all reminder messages (and add them to the chatbot context)
            if reminder_msgs:
                compiled_reminder_msgs = "\n".join(reminder_msgs)
                extend_user_msg_memory(
                    request_sndr,
                    "main",
                    [
                        {
                            "type": "ai",
                            "data": {
                                "content": compiled_reminder_msgs,
                                "additional_kwargs": {},
                                "example": False,
                            },
                        }
                    ],
                )
                send_sms(
                    "+" + str(request_sndr),
                    f"By the way, you wanted me to remind you about these goals. \n\n{compiled_reminder_msgs}",
                )

            # Queue chatbot with new messages and have it respond (this will auto handle adding to context)
            # We should also indicate to the chatbot that the last message WE sent was sent AFTER all of these
            # messages we are responding to. In other words, the user is responding to the second-to-last
            # message the chatbot sent, and not the very last one (which was being written as the user was sending messages).
            if user_msgs:
                compiled_user_msgs = "\n".join(user_msgs)
                chatbot_respond_ALT(
                    compiled_user_msgs, request_sndr, is_responding_to_queue=True
                )

            # Get any new messages in the queue
            pipe = r.pipeline()
            pipe.lrange(chat_msg_queue, 0, -1)
            pipe.ltrim(chat_msg_queue, 1, 0)
            queued_msgs_list, _ = pipe.execute()

        # Remove user from active conversations
        r.srem("active-conversations", request_sndr)
        print(">>> Setting conversation as inactive")
