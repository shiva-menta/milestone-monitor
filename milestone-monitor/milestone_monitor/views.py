import os
import sys
import json
from datetime import datetime
from twilio.request_validator import RequestValidator

import logging

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from backend.decorators import validate_twilio_request

from milestone_monitor.models import RecurringGoal, OneTimeGoal

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)

from conversation_tasks import chatbot_respond_async

from utils.sms import send_sms
from utils.interactions import create_goal
from utils.chatbot import get_main_chatbot
from utils.memory_utils import dict_to_memory, memory_to_dict, create_main_memory
from utils.create_goal_chain import get_create_goal_chain
from utils.redis_user_data import (
    get_user_hist,
    update_user_convo_type,
    update_user_msg_memory,
    create_default_user_hist,
    set_conversation_inactive,
    pop_pending_messages,
)
from utils.goal_tools import parse_field_entries, format_text_fields
from utils.conversation_handler import chatbot_respond

@csrf_exempt
# @validate_twilio_request
def receive_sms(request):
    print(">>> Hit `receive_sms` endpoint!!!")
    """
    Main texting endpoint for prod (receives an SMS message)

    Receives the message and sender, and calls the async task for
    the chatbot to respond (or queues up a message to eventually respond to)

    Twilio sends POST requests: https://www.twilio.com/docs/messaging/guides/webhook-request
    - Phone number will look like "+14017122661"
    """
    
    
    if request.method == "POST":
        # logging.info("Received SMS message from user")
        print(">>> Received message from user")
        # TODO: validate user phone number here (or add international support)

        request_msg = request.POST.get("Body", "")
        request_sndr = request.POST.get("From", "")

        chatbot_respond_async.s(request_msg, request_sndr).apply_async()

        # return HttpResponse("Goal created.")
        return HttpResponse("Queued chatbot respond job to Celery.")


##
# Dev views
##


# Create your views here.
@csrf_exempt
def test_sms(request):
    # Get user data
    body_unicode = request.body.decode("utf-8")
    body_data = json.loads(body_unicode)

    query = body_data["input"]
    user = body_data["user"]

    send_sms(user, query)

    return HttpResponse("Text sent.")


@csrf_exempt
def reset_user(request):
    # Get user data
    body_unicode = request.body.decode("utf-8")
    body_data = json.loads(body_unicode)

    user = body_data["user"]
    create_default_user_hist(user)
    set_conversation_inactive(user)
    pop_pending_messages(user)

    return HttpResponse("User data reset.")


def delete_goals_database(request):
    RecurringGoal.objects.all().delete()
    OneTimeGoal.objects.all().delete()
    return HttpResponse("Goals deleted")


# DEV: CHECK CURRENT GOAL DATABASE
def print_goals_database(request):
    recurring = RecurringGoal.objects.all()
    one_time = OneTimeGoal.objects.all()

    recurring_list = [model_to_dict(item) for item in recurring]
    one_time_list = [model_to_dict(item) for item in one_time]

    context = {"recurring": recurring_list, "one_time": one_time_list}

    return JsonResponse(context)


def test_redis(request):
    number = "6307308169"
    data = update_user_convo_type(number, "create_goal")

    # return JsonResponse(data)
    return HttpResponse("Completed.")


# For interacting with the model
# TODO: remove csrf exemption
# @csrf_exempt
# def chatbot_send_msg(request):
#     # Get user data
#     body_unicode = request.body.decode("utf-8")
#     body_data = json.loads(body_unicode)
#     user_data = get_user_hist(body_data["user"])

#     query = body_data["input"]
#     user = body_data["user"]

#     # Main conversation chain
#     if user_data["current_convo_type"] == "main":
#         # Load memory
#         print(user_data["main_memory"])
#         main_memory = dict_to_memory(user_data["main_memory"])

#         if main_memory is None:
#             main_memory = create_main_memory()

#         # Load chatbot with memory
#         chatbot = get_main_chatbot(user, main_memory, DEBUG=True)

#         # Get output from the chatbot
#         # if we entered the create goal convo, it automatically
#         # uses that output
#         output = chatbot.run(input=query)

#         # Save memory
#         update_user_msg_memory(user, "main", memory_to_dict(main_memory))

#     # Create goal conversation chain
#     elif user_data["current_convo_type"] == "create_goal":
#         # Load memory
#         create_memory = dict_to_memory(user_data["create_goal_memory"])

#         # Load chain for goal creation conversation
#         chain = get_create_goal_chain(create_memory, DEBUG=True)

#         # Get the output from the goal creator chain
#         print("TEST")
#         current_full_output = chain.predict(input=query, today=datetime.now())
#         print("END TEST")

#         # Extract field entries and output
#         current_field_entries = parse_field_entries(
#             current_full_output.split("END FIELD ENTRIES")[0].strip()
#         )
#         current_conversational_output = current_full_output.split("END FIELD ENTRIES")[
#             1
#         ].strip()
#         print(f"Temp field entries: {current_field_entries}")
#         print(f"Model: {current_conversational_output}")

#         # Save memory
#         update_user_msg_memory(user, "create_goal", memory_to_dict(create_memory))

#         # Check if we've finished this conversation
#         if current_field_entries["STATUS"] == "SUCCESS":
#             update_user_convo_type(user, "main")

#             # Parse current field entries here
#             # and add them to the database
#             formatted_text_fields = format_text_fields(current_field_entries)
#             print(formatted_text_fields)
#             # goal_name_embedding = create_embedding(current_field_entries["name"])
#             create_goal(formatted_text_fields)

#             # prev ex context:
#             # human: I'd like to get groceries this week
#             # bot (create, but as main output): ok, what time?
#             # human: ...
#             # bot (create): ...
#             # human: ...
#             # bot (create): ... ok, does this look good?
#             # human: yep!
#             # bot (create): "STATUS" == "SUCCESS" --(INTERCEPT OUTPUT)--> bot (main): awesome, i've created the goal for you!

#             # in order for the main chatbot to give a coherent response,
#             # let's inject the second to last two lines of the context
#             # into the memory of the main chatbot
#             # and then re-input the user's final input
#             extra_lines = user_data["create_goal_memory"][-2:]
#             main_memory = dict_to_memory(user_data["main_memory"] + extra_lines)

#             # Load chatbot with memory (should ideally confirm success)
#             main_chatbot = get_main_chatbot(user, main_memory, DEBUG=True)
#             output = main_chatbot.run(query)
#         else:
#             output = f"{current_field_entries}\n\n{current_conversational_output}"

#     # Send output
#     send_sms(body_data["user"], output)
#     return HttpResponse("Text sent.")
