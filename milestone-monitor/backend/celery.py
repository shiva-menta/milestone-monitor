import os
from celery import Celery
from time import timezone

from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    #Scheduler Name
    'complete': {
        # Task Name (Name Specified in Decorator)
        'task': 'print_main',  
        # Schedule      
        'schedule': 20.0,
        # Function Arguments 
        'args': ('+16307308169', "Testing Celery.") 
    },
}  