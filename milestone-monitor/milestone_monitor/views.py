import os
import sys
import json
from twilio.request_validator import RequestValidator

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from backend.decorators import validate_twilio_request

from milestone_monitor.models import Goal

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)

from conversation_tasks import chatbot_respond_async

from utils.sms import send_sms
from utils.redis_user_data import (
    update_user_convo_type,
    create_default_user_hist,
    set_conversation_inactive,
    pop_pending_messages,
)


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
    - We will remove the "+" from it
    """

    if request.method == "POST":
        # logging.info("Received SMS message from user")
        print(">>> Received message from user")
        # TODO: validate user phone number here (or add international support)

        request_msg = request.POST.get("Body", "")
        request_sndr = request.POST.get("From", "")

        chatbot_respond_async.s(request_msg, request_sndr).apply_async()
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
    Goal.objects.all().delete()
    return HttpResponse("Goals deleted")


# DEV: CHECK CURRENT GOAL DATABASE
@csrf_exempt
def print_goals_database(request):
    goals = Goal.objects.all()
    goal_list = [model_to_dict(item) for item in goals]
    context = {"goals": goal_list}

    return JsonResponse(context)


def test_redis(request):
    number = "6307308169"
    data = update_user_convo_type(number, "create_goal")

    # return JsonResponse(data)
    return HttpResponse("Completed.")
