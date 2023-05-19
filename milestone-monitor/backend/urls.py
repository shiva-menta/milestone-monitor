"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
import sys

from django.contrib import admin
from django.urls import path

curr_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(curr_dir)
sys.path.insert(0, parent_dir)

import milestone_monitor.views as views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sms/", views.test_sms, name="send-message"),
    path("reset/", views.reset_user, name="test-message"),
    path("api/", views.print_goals_database, name="print-output"),
    path("chatbot/", views.chatbot_send_msg, name="chatbot-send-message"),
    path("redis/", views.test_redis, name="redis-test"),
    path("sms/", views.receive_sms, name="receive-message"),
    path("db/", views.print_goals_database, name="view-goals")
]
