from celery import shared_task
from utils.sms import send_sms
from django.http import HttpResponse, JsonResponse

# send scheduled messages
@shared_task(name = "send_reminder_message")
def send_reminder_message(number, task_title):
    send_sms(
        '+' + str(number),
        f"""
        Hello! Just checking in about your goal: {task_title}.

        Have you made any progress on this goal yet?
        """
    )
