# Util functions for what actions should be taken by the chatbot in text conversations

import json
from datetime import datetime

from django.http import HttpResponse

from utils.sms import send_sms
from utils.interactions import create_goal
from utils.chatbot import get_main_chatbot
from utils.memory_utils import dict_to_memory, memory_to_dict, create_main_memory
from utils.create_goal_chain import get_create_goal_chain
from utils.msg_hist import get_user_hist, update_user_convo_type, update_user_msg_memory, create_default_user_hist
from utils.goal_tools import parse_field_entries, format_text_fields


# Upon receiving a message from a user, this handles the message, 
# and responds (as well as taking other relevant actions)
def chatbot_respond(query, user):

    # Get user data
    user_data = get_user_hist(user)

    # Main conversation chain
    if user_data["current_convo_type"] == "main":

        # Load memory
        print(user_data["main_memory"])
        main_memory = dict_to_memory(user_data["main_memory"])

        if main_memory is None:
            main_memory = create_main_memory()

        # Load chatbot with memory
        chatbot = get_main_chatbot(user, main_memory, DEBUG=True)

        # Get output from the chatbot
        # if we entered the create goal convo, it automatically
        # uses that output
        output = chatbot.run(input=query)

        # Save memory
        update_user_msg_memory(user, "main", memory_to_dict(main_memory))
    
    # Create goal conversation chain
    elif user_data["current_convo_type"] == "create_goal":

        # Load memory
        create_memory = dict_to_memory(user_data["create_goal_memory"])

        # Load chain for goal creation conversation
        chain = get_create_goal_chain(create_memory, DEBUG=True)
    
        # Get the output from the goal creator chain
        print("TEST")
        current_full_output = chain.predict(input=query, today=datetime.now())
        print("END TEST")

        # Extract field entries and output
        current_field_entries = parse_field_entries(current_full_output.split('END FIELD ENTRIES')[0].strip())
        current_conversational_output = current_full_output.split('END FIELD ENTRIES')[1].strip()
        print(f"Temp field entries: {current_field_entries}")
        print(f"Model: {current_conversational_output}")

        # Save memory
        update_user_msg_memory(user, "create_goal", memory_to_dict(create_memory))

        # Check if we've finished this conversation
        if current_field_entries["STATUS"] == "SUCCESS":
            update_user_convo_type(user, "main")

            # Parse current field entries here
            # and add them to the database
            formatted_text_fields = format_text_fields(current_field_entries)
            print(formatted_text_fields)
            # goal_name_embedding = create_embedding(current_field_entries["name"])
            create_goal(formatted_text_fields)

            # prev ex context:
            # human: I'd like to get groceries this week
            # bot (create, but as main output): ok, what time?
            # human: ...
            # bot (create): ...
            # human: ...
            # bot (create): ... ok, does this look good?
            # human: yep!
            # bot (create): "STATUS" == "SUCCESS" --(INTERCEPT OUTPUT)--> bot (main): awesome, i've created the goal for you!

            # in order for the main chatbot to give a coherent response, 
            # let's inject the second to last two lines of the context
            # into the memory of the main chatbot
            # and then re-input the user's final input
            extra_lines = user_data["create_goal_memory"][-2:]
            main_memory = dict_to_memory(user_data["main_memory"] + extra_lines)
            
            # Load chatbot with memory (should ideally confirm success)
            main_chatbot = get_main_chatbot(user, main_memory, DEBUG=True)
            output = main_chatbot.run(query)
        else:
            output = f"{current_field_entries}\n\n{current_conversational_output}"

    # Send output
    send_sms(user, output)
    return HttpResponse("Text sent.")