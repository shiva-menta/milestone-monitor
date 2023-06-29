from celery import shared_task
from django.http import HttpResponse, JsonResponse
from celery_once import QueueOnce

from .utils.sms import send_sms

# send scheduled messages
@shared_task(base=QueueOnce, name="send_recurring_reminder_message", once={'graceful': True})
def send_recurring_reminder_message(number, task_title):
    send_sms(
        "+" + str(number),
        f"""
        Hello! Just checking in about your goal: {task_title}.

        Have you made any progress on this goal yet?
        """,
    )

@shared_task(name="send_onetime_reminder_message")
def send_onetime_reminder_message(number, task_title):
    send_sms(
        "+" + str(number),
        f"""
        Hello! Just checking in about your goal: {task_title}.

        Have you completed this goal yet?
        """,
    )