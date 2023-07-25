# Manages the actual flow of conversation for the chatbot, including managing user memory and language chains.

from django.http import HttpResponse
from datetime import datetime

from .sms import send_sms
from .interactions import create_goal
from .chatbot import get_main_chatbot
from .memory_utils import dict_to_memory, memory_to_dict, create_main_memory
from .create_goal_chain import get_create_goal_chain
from .redis_user_data import (
    get_user_hist,
    save_user_msg_memory,
    refresh_goal_creation_in_progress_bot_response,
)


# Upon rec
def chatbot_respond_ALT(query, user, is_responding_to_queue=False):
    user_data = get_user_hist(user)
    main_memory = dict_to_memory(user_data["main_memory"])
    is_creating_goal = len(user_data["current_field_entries"]) > 0

    if main_memory is None:
        main_memory = create_main_memory()

    print(">>> Current user data:")
    print(user_data)
    print("IS CREATING GOAL:", is_creating_goal)

    # Load chatbot with memory
    chatbot = get_main_chatbot(
        user, main_memory, is_creating_goal, is_responding_to_queue, DEBUG=True
    )

    # Get output from the chatbot
    # if we entered the create goal convo, it automatically
    # uses that output
    print("Query:", query)
    print("Memory:", main_memory)
    output = chatbot.run(input=query)

    # Save memory
    print(">>> Saving conversation to memory...")
    save_user_msg_memory(user, "main", memory_to_dict(main_memory))

    # Send output as an SMS
    if output != "You are already in the process of creating a goal!":
        send_sms(user, output)
        refresh_goal_creation_in_progress_bot_response(user)
    return HttpResponse("Text sent.")
