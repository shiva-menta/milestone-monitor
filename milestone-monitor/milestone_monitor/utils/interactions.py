# Utils for interacting with the database

from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.utils.dateparse import parse_datetime, parse_time

from milestone_monitor.models import User, RecurringGoal, OneTimeGoal


def create_goal(goal_data, user):
    """
    goal_data:
      - name: string
      - description: string
      - estimatedImportance: 'HIGH' | 'MEDIUM' | 'LOW'
      - estimatedDurationHours: int
      - goalFrequency: 'DAILY' | 'WEEKLY' | None
      - reminderFrequency: 'HOURLY' | 'DAILY' | 'WEEKLY' | 'BIWEEKLY' | 'MONTHLY' | None
      - reminderTime: HH:MM
      - status: 'SUCCESS'
      - dueDate: datetime
      - isRecurring: 0 | 1
    user: string (of the form "+12345678901")
    """
    print(goal_data)

    # TODO: validate `status`

    # Create and save user (TODO: why are we doing this every time?)
    parsed_user_number = int(user[1:])  # assumes valid US format
    u = User(name="MM", phone_number=parsed_user_number)
    u.save()

    reminder_frequency_map = {
        "HOURLY": RecurringGoal.Frequency.HOURLY,
        "DAILY": RecurringGoal.Frequency.DAILY,
        "WEEKLY": RecurringGoal.Frequency.WEEKLY,
        "BIWEEKLY": RecurringGoal.Frequency.BIWEEKLY,
        "MONTHLY": RecurringGoal.Frequency.MONTHLY,
    }

    importance_map = {
        "LOW": RecurringGoal.Importance.LOW,
        "MEDIUM": RecurringGoal.Importance.MEDIUM,
        "HIGH": RecurringGoal.Importance.HIGH,
    }

    # Create and save goal
    g = None
    if goal_data["isRecurring"]:
        g = RecurringGoal(
            user=u,
            title=goal_data["name"],
            end_at=goal_data["dueDate"],
            reminder_time=(
                parse_time(goal_data["reminderTime"])
                if goal_data["reminderTime"]
                else None
            ),
            completed=False,
            # frequency=RecurringGoal.Frequency.MINUTELY,
            frequency=reminder_frequency_map.get(
                goal_data["reminderFrequency"], RecurringGoal.Frequency.DAILY
            ),
            importance=importance_map.get(
                goal_data["estimatedImportance"], RecurringGoal.Importance.LOW
            ),
        )
    else:
        g = OneTimeGoal(
            user=u,
            title=goal_data["name"],
            end_at=goal_data["dueDate"],
            reminder_time=(
                parse_time(goal_data["reminderTime"])
                if goal_data["reminderTime"]
                else None
            ),
            completed=False,
            importance=importance_map.get(goal_data["estimatedImportance"], 1),
        )
    g.save()

    print(">>> Successfully added goal to the database!")
