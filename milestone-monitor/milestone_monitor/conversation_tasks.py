from celery import shared_task
from django.http import HttpResponse, JsonResponse
from celery_once import QueueOnce

from utils.conversation_handler import chatbot_respond
from utils.sms import send_sms

import json
import redis


@shared_task
def chatbot_respond_async(request_msg, request_sndr):
    print(">>> CALLED chatbot_respond_async")
    r = redis.Redis(host="localhost", port=6379, db=0)

    """
    Needs to do the following:
    1. Check if an existing conversation is in progress
    2. If so, adds the user's message to the queue (to be immediately
        send to the chatbot after it responds)
    3. Otherwise, need to start a response from the chatbot using `chatbot_respond`
        which will handle the process of sending a text message back to the user
    """

    chat_msg_queue = f"pending-msgs-{request_sndr}"

    # Note that there will ONLY be pending messages if the bot is in the middle
    # of responding to the user, since if a message is sent while the bot is not responding,
    # it will just immediately respond to the user

    # Bot is in the middle of responding, so we need to queue up the message (and message type)
    r.srem("active-conversations", request_sndr)
    if r.sismember("active-conversations", request_sndr):
        print(">>> Conversation is currently active, queueing")
        to_queue_msg = json.dumps({"type": "user", "content": request_msg})
        r.lpush(chat_msg_queue, to_queue_msg)
    else:
        # This should NEVER be reached if the bot is in the middle
        # of responding, so the code here should only be running on one
        # worker at a time

        # No pending messages, so it is okay to respond immediately
        r.sadd("active-conversations", request_sndr)
        print(">>> Setting conversation as active")
        chatbot_respond(request_msg, request_sndr)

        # By this point, it is possible that messages have been queued up while that above
        # worker/function was running, so we need to compile all of those messages
        # and give them to the chatbot (in order to respond to)

        # Note that this will run in a loop (since if we run the chatbot again,
        # the user could send more messages, so we need to respond again, and so on)
        queued_msgs_list = r.lrange(chat_msg_queue, 0, -1)
        while queued_msgs_list:
            # Compile all messages and sort them
            user_msgs = []
            reminder_msgs = []
            for msg_raw in queued_msgs_list:
                msg_obj = json.loads(msg_raw.decode("utf-8"))
                if msg_obj["type"] == "user":
                    user_msgs.append(msg_obj["content"])
                elif msg_obj["type"] == "reminder":
                    reminder_msgs.append(msg_obj["content"])

            # Send all reminder messages (and add them to the chatbot context)
            for reminder in reminder_msgs:
                send_sms(reminder)

            # Queue chatbot with new messages and have it respond
            if user_msgs:
                compiled_user_msgs = "\n".join(user_msgs)
                chatbot_respond(compiled_user_msgs, request_sndr)

            # Remove all messages from the queue and
            # collect any new msgs that have been sent in the meantime
            queued_msgs_list = r.ltrim(chat_msg_queue, 1, 0)
            queued_msgs_list = r.lrange(chat_msg_queue, 0, -1)

        # By this point, there are no more messages left to be sent, so
        # we can remove the user from the list of active conversations
        r.srem("active-conversations", request_sndr)
        print(">>> Setting conversation as inactive")
