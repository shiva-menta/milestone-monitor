from .settings import *
from fakeredis import FakeStrictRedis

redis_url = FakeStrictRedis()
DATABASES['default'] = {
  'ENGINE': 'django.db.backends.sqlite3',
  'NAME': ':memory:',
}

CELERY_BROKER_URL = 'memory://'
CELERY_TASK_ALWAYS_EAGER = True