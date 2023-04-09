from celery import shared_task
from utils.sms import send_sms
from django.http import HttpResponse, JsonResponse

# send scheduled messages
@shared_task(name = "print_main")
def test_message(number, message):
    send_sms(number, message)
