import json
import datetime

from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.utils.dateparse import parse_datetime

def create_goal(input):
    print(input)
    goal_type = input['type'] == 0
    u = User(name="MM", phone_number=int(input['number']))
    u.save()
    g = None

    due_date = parse_datetime(input["dueDate"]) if input["dueDate"] else None
    frequency_map = {
        "HOURLY": RecurringGoal.Frequency.HOURLY,
        "DAILY": RecurringGoal.Frequency.DAILY,
        "WEEKLY": RecurringGoal.Frequency.WEEKLY,
        "BIWEEKLY": RecurringGoal.Frequency.BIWEEKLY,
        "MONTHLY": RecurringGoal.Frequency.MONTLY,
    }

    if input["isRecurring"]:
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

