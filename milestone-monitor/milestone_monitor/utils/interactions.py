import json
import datetime

from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.utils.dateparse import parse_datetime

from milestone_monitor.models import User, RecurringGoal, OneTimeGoal

def create_goal(input):
    goal_type = input.goalType == 0
    u = User(name="MM", phone_number=10000000000)
    g = None

    if goal_type:
        g = RecurringGoal(
            user=u,
            title=input.name,
            end_at=parse_datetime(input.dueDate),
            reminder_time=input.reminderTime,
            completed=False,
            frequency=input.goalFrequency
        )
    else:
        g = OneTimeGoal(
            user=u,
            title=input.name,
            end_at=parse_datetime(input.dueDate),
            completed=False
        )
    
    g.save()

