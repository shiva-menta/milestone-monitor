from celery import shared_task
from django.http import HttpResponse, JsonResponse

from utils.sms import send_sms
from utils.conversation_handler import chatbot_respond
from utils.redis_user_data import (
    check_active_conversation,
    set_conversation_active,
    set_conversation_inactive,
    pend_user_message,
    pop_pending_messages,
)


# send scheduled messages
@shared_task(name="send_reminder_message")
def send_reminder_message(number, task_title):
    print("test")
    send_sms(
        "+" + str(number),
        f"""
        Hello! Just checking in about your goal: {task_title}.

        Have you made any progress on this goal yet?
        """,
    )


@shared_task
def chatbot_respond_async(request_msg, request_sndr):
    print(">>> CALLED chatbot_respond_async!!!")
    print("sndr:", request_sndr)
    print("msg:", request_msg)

    """
    Needs to do the following:
    1. Check if an existing conversation is in progress
    2. If so, adds the user's message to the queue (to be immediately
        send to the chatbot after it responds)
    3. Otherwise, need to start a response from the chatbot using `chatbot_respond`
        which will handle the process of sending a text message back to the user
    """

    # Note that there will ONLY be pending messages if the bot is in the middle
    # of responding to the user, since if a message is sent while the bot is not responding,
    # it will just immediately respond to the user

    # Bot is in the middle of responding, so we need to queue up the message (and message type)
    if False:  # check_active_conversation(request_sndr):
        print(">>> Conversation is currently active, queueing msg")
        pend_user_message(request_sndr, request_msg)
    else:
        # This should NEVER be reached if the bot is in the middle
        # of responding, so the code here should only be running on one
        # worker at a time

        # No pending messages, so it is okay to respond immediately
        # set_conversation_active(request_sndr)
        print(">>> Setting conversation as active")
        chatbot_respond(request_msg, request_sndr)

        # By this point, it is possible that messages have been queued up while that above
        # worker/function was running, so we need to compile all of those messages
        # and give them to the chatbot (in order to respond to)

        # Note that this will run in a loop (since if we run the chatbot again,
        # the user could send more messages, so we need to respond again, and so on)
        # user_msgs, reminder_msgs = pop_pending_messages(request_sndr)
        # print(user_msgs)
        # print(reminder_msgs)

        # while user_msgs or reminder_msgs:
        #     print(">>> Looping convo")
        #     # Send all reminder messages (and add them to the chatbot context)
        #     for reminder in reminder_msgs:
        #         send_sms(reminder)

        #     # Queue chatbot with new messages and have it respond
        #     if user_msgs:
        #         compiled_user_msgs = "\n".join(user_msgs)
        #         chatbot_respond(compiled_user_msgs, request_sndr)

        #     # Remove all messages from the queue and
        #     # collect any new msgs that have been sent in the meantime (and repeat!)
        #     user_msgs, reminder_msgs = pop_pending_messages(request_sndr)

        # # By this point, there are no more messages left to be sent, so
        # # we can remove the user from the list of active conversations
        # set_conversation_inactive(request_sndr)
        print(">>> Setting conversation as inactive")
