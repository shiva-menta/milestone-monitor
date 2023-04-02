import sys
import os

from django.shortcuts import render
from django.http import HttpResponse

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from utils.sms import send_sms

# Create your views here.
def test(request):
    send_sms('+13028678414', 'Testing HTTP Message.')
    return HttpResponse("Text sent.")

def receive_test(request):
    send_sms('+16109456312', 'Testing Webhook.')
    return HttpResponse("Text sent.")
