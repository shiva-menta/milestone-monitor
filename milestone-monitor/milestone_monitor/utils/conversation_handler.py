# Manages the actual flow of conversation for the chatbot, loading in user memory,
# the right chains, and taking other actions as necessary

from datetime import datetime

from django.http import HttpResponse

from .sms import send_sms
from .interactions import create_goal
from .chatbot import get_main_chatbot
from .memory_utils import dict_to_memory, memory_to_dict, create_main_memory
from .create_goal_chain import get_create_goal_chain
from .redis_user_data import (
    get_user_hist,
    update_user_convo_type,
    update_user_msg_memory,
    create_default_user_hist,
)
from .goal_tools import (
    parse_field_entries,
    format_text_fields,
    prettify_field_entries,
)


# Upon receiving a message from a user, this handles the message,
# and responds (as well as taking other relevant actions)
def chatbot_respond(query, user):
    print(">>> CHATBOT IS RESPONDING!!")
    # Get user data
    user_data = get_user_hist(user)

    # Main conversation chain:
    # - The user is currently not in the middle of discussing adding a goal
    # - But this could trigger adding a goal
    if user_data["current_convo_type"] == "main":
        # Load memory
        main_memory = dict_to_memory(user_data["main_memory"])

        if main_memory is None:
            main_memory = create_main_memory()

        # Load chatbot with memory
        chatbot = get_main_chatbot(user, main_memory, DEBUG=True)

        # Get output from the chatbot
        # if we entered the create goal convo, it automatically
        # uses that output
        print("Query:", query)
        print("Memory:", main_memory)
        output = chatbot.run(input=query)

        # Save memory
        update_user_msg_memory(user, "main", memory_to_dict(main_memory))

    # Create goal conversation chain:
    # - The user is currently in the middle of discussing creating a goal
    elif user_data["current_convo_type"] == "create_goal":
        # Load memory
        create_memory = dict_to_memory(user_data["create_goal_memory"])

        # Load chain for goal creation conversation
        chain = get_create_goal_chain(create_memory, DEBUG=True)

        # Get the output from the goal creator chain
        current_full_output = chain.predict(input=query, today=datetime.now())
        print(current_full_output)
        # Extract field entries and output
        current_field_entries = parse_field_entries(
            current_full_output.split("GoalDesigner: ")[0].strip()
        )
        current_conversational_output = current_full_output.split("GoalDesigner: ")[
            1
        ].strip()

        # Save memory
        update_user_msg_memory(user, "create_goal", memory_to_dict(create_memory))

        # Check if we've finished this conversation
        if current_field_entries["STATUS"] == "SUCCESS":
            update_user_convo_type(user, "main")

            # Parse current field entries here
            # and add them to the database
            formatted_text_fields = format_text_fields(current_field_entries)
            # goal_name_embedding = create_embedding(current_field_entries["name"])
            create_goal(formatted_text_fields, user)

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
            pretty_field_entries = prettify_field_entries(current_field_entries)
            output = f"{pretty_field_entries}\n\n{current_conversational_output}"

    # Send output as an SMS
    # send_sms(user, output)
    # print(output)
    send_sms(user, output)
    return HttpResponse("Text sent.")
