from celery import shared_task
from django.http import HttpResponse, JsonResponse
from celery_once import QueueOnce

from .utils.sms import send_sms

# send scheduled messages
@shared_task(base=QueueOnce, name="send_recurring_reminder_message", once={'graceful': True})
def send_periodic_reminder(number, task_title):
    send_sms(
        "+" + str(number),
        f"Hello! Sending a reminder about completing your goal, {task_title}."
    )

@shared_task(name="send_final_task_message")
def send_final_task_message(number, task_title):
    send_sms(
        "+" + str(number),
        f"Hello! Your deadline for your goal, {task_title}, is now complete.",
    )
