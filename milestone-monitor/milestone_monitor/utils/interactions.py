import json
import datetime

from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from milestone_monitor.models import User, RecurringGoal, OneTimeGoal
from django.utils.dateparse import parse_datetime

def create_goal(input):
    print(input)
    goal_type = input['type'] == 0
    u = User(name="MM", phone_number=int(input['number']))
    u.save()
    g = None
    if goal_type:
        g = RecurringGoal(
            user=u,
            title=input['title'],
            end_at=parse_datetime(input['end_at']),
            completed=False,
            frequency=RecurringGoal.Frequency.MINUTELY
        )
    else:
        g = OneTimeGoal(
            user=u,
            title=input['title'],
            end_at=parse_datetime(input['end_at']),
            completed=False
        )
    g.save()