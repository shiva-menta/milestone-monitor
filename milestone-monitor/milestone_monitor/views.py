import os
import sys
import json

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt

from milestone_monitor.models import RecurringGoal, OneTimeGoal

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)

from utils.sms import send_sms
from utils.interactions import create_goal
from utils.chatbot import get_chatbot
from utils.msg_hist import get_user_hist, update_user_convo_type

# Create your views here.
def test(request):
    send_sms('+13028678414', 'Testing HTTP Message.')
    return HttpResponse("Text sent.")

def receive_test(request):
    send_sms('+16109456312', 'Testing Webhook.')
    return HttpResponse("Text sent.")

def print_goals_database(request):
    recurring = RecurringGoal.objects.all()
    one_time = OneTimeGoal.objects.all()

    recurring_list = [model_to_dict(item) for item in recurring]
    one_time_list = [model_to_dict(item) for item in one_time]

    context = {
        "recurring": recurring_list,
        "one_time": one_time_list
    }

    return JsonResponse(context)

def test_redis(request):
    number = "6307308169"
    data = update_user_convo_type(number, 'create_goal')

    # return JsonResponse(data)
    return HttpResponse("Completed.")


# For interacting with the model
# TODO: remove this
@csrf_exempt
def chatbot_send_msg(request):
    chatbot = get_chatbot("USER HERE", DEBUG=True)

    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)

    output = chatbot.run(body_data["input"])
    send_sms('+16109456312', output)

    return HttpResponse("Text sent.")
