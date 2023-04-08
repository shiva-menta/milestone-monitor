import json
import datetime
from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from milestone_monitor.models import User, RecurringGoal, OneTimeGoal
from django.utils.dateparse import parse_datetime

def create_goal(input):
    goal_type = input.type == 0
    u = User(name="MM", phone_number=10000000000)
    g = None
    if goal_type:
        g = RecurringGoal(
            user=u,
            title=input.title,
            end_at=parse_datetime(input.end_at),
            reminder_time=input.reminder_time,
            completed=False,
            frequency=input.frequency
        )
    else:
        g = OneTimeGoal(
            user=u,
            title=input.title,
            end_at=parse_datetime(input.end_at),
            completed=False
        )
    g.save()

