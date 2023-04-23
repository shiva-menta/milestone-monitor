import sys
import os
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

# Create your views here.
# PROD: MAIN TEXTING ENDPOINT
@csrf_exempt
def receive_sms(request):
    if request.method == 'POST':
        request_msg = request.POST.get('Body', "")
        request_sndr = request.POST.get('From', "")

        create_goal({
            'number': request_sndr[1:],
            'type': 0,
            'title': request_msg,
            'end_at': "2023-03-28T12:00:00",
            'frequency': 'MINUTELY'
        })

        return HttpResponse("Goal created.")

# DEV: CHECK CURRENT GOAL DATABASE
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

