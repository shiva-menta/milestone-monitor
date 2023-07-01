import os
from celery import Celery

from backend.settings import redis_url

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

app.conf.beat_scheduler = "redbeat.schedulers:RedBeatScheduler"
app.conf.redbeat_redis_url = redis_url

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
