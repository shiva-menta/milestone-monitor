import sys
import redis
from fakeredis import FakeStrictRedis
from backend.settings import redis_url

def get_redis_client():
  if 'test' in sys.argv:
    return FakeStrictRedis()
  else:
    return redis.Redis.from_url(redis_url)