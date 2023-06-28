import os
from celery import Celery

from backend.settings import redis_url

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': redis_url+'1',
    'default_timeout': 60 * 60
  }
}

app.conf.beat_scheduler = "redbeat.schedulers:RedBeatScheduler"
app.conf.redbeat_redis_url = redis_url

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


