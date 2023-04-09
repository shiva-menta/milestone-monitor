import sys
import os

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.forms.models import model_to_dict

from milestone_monitor.models import RecurringGoal, OneTimeGoal

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from utils.sms import send_sms
from utils.interactions import create_goal

# Create your views here.
def test(request):
    # test_message('+16307308169', "Testing Celery.")
    return HttpResponse("Text sent.")

def receive_test(request):
    send_sms('+16109456312', 'Testing Webhook.')
    return HttpResponse("Text sent.")

def make_goal(request):
    create_goal({
        'type': 0,
        'title': 'Testing.',
        'end_at': "2023-03-28T12:00:00",
        'frequency': 'MINUTELY',
    })
    return HttpResponse("Goal created.")

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

