import os
import sys

from django.contrib import admin
from django.urls import path

curr_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(curr_dir)
sys.path.insert(0, parent_dir)

import milestone_monitor.views as views

urlpatterns = [
    # Production
    path("sms/", views.receive_sms, name="receive-message"),

    # Dev
    path("admin/", admin.site.urls),

    # Testing
    path("reset/", views.reset_user, name="test-message"),
    path("redis/", views.test_redis, name="redis-test"),
    # path("db/", views.print_goals_database, name="view-goals"),
    # path("resetgoals/", views.delete_goals_database, name="reset-goals")
]
