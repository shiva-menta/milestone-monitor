import json
import datetime

from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.utils.dateparse import parse_datetime

from milestone_monitor.models import User, RecurringGoal, OneTimeGoal

def create_goal(input: dict):
    u = User(name="MM", phone_number=10)
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
            title=input["name"],
            end_at=due_date,
            reminder_time=input["reminderTime"],
            completed=False,
            frequency=frequency_map[input["goalFrequency"]]
        )
    else:
        g = OneTimeGoal(
            user=u,
            title=input["name"],
            end_at=due_date,
            completed=False
        )
    
    g.save()

