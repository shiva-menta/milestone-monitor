from celery import shared_task
from django.http import HttpResponse, JsonResponse
from celery_once import QueueOnce

import redis
import json
from .utils.sms import send_sms
from .utils.redis_user_data import update_user_msg_memory
from backend.redis import get_redis_client

r = get_redis_client()

# send scheduled messages
@shared_task(base=QueueOnce, name="send_periodic_reminder", once={"graceful": True})
def send_periodic_reminder(number, task_title):
    chat_msg_queue = f"pending-msgs-{number}"
    message = f"Hello! Sending a reminder about completing your goal, {task_title}."

    if r.sismember("active-conversations", number):
        to_queue_msg = json.dumps({
            "type": "reminder",
            "content": message
        })
        r.lpush(chat_msg_queue, to_queue_msg)
    else:
        update_user_msg_memory(number, "main", [{
            'type': 'ai',
            'data': {
                'content': message,
                'additional_kwargs': {},
                'example': False
            }
        }])
        send_sms(
            "+" + str(number),
            message
        )


@shared_task(name="send_final_task_message")
def send_final_task_message(number, task_title):
    chat_msg_queue = f"pending-msgs-{number}"
    message = f"Hello! Your deadline for your goal, {task_title}, is now complete."

    if r.sismember("active-conversations", number):
        to_queue_msg = json.dumps({
            "type": "reminder",
            "content": message
        })
        r.lpush(chat_msg_queue, to_queue_msg)
    else:
        update_user_msg_memory(number, "main", [{
            'type': 'ai',
            'data': {
                'content': message,
                'additional_kwargs': {},
                'example': False
            }
        }])
        send_sms(
            "+" + str(number),
            message
        )
