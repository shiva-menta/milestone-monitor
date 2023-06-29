# Utils for interacting with the databases

import os
from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.utils.dateparse import parse_datetime, parse_time

import cohere
import pinecone

from milestone_monitor.models import User, RecurringGoal, OneTimeGoal

COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENV = os.environ.get("PINECONE_ENV")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX")
COHERE_EMBED_MODEL = "embed-english-light-v2.0"


def create_goal(goal_data, user: str):
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

    # Create and save goal in postgres
    g = None
    if goal_data["isRecurring"]:
        g = RecurringGoal(
            user=u,
            title=goal_data["name"],
            end_at=goal_data["dueDate"],
            # reminder_time=(
            #     parse_time(goal_data["reminderTime"])
            #     if goal_data["reminderTime"]
            #     else None
            # ),
            reminder_time=None,
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
            # reminder_time=(
            #     parse_time(goal_data["reminderTime"])
            #     if goal_data["reminderTime"]
            #     else None
            # ),
            reminder_time=None,
            completed=False,
            importance=importance_map.get(goal_data["estimatedImportance"], 1),
        )
    g.save()
    goal_id = g.id

    print(">>> Successfully added goal to the postgres database!")

    create_goal_pinecone(
        goal_id=goal_id,
        is_recurring=goal_data["isRecurring"],
        goal_description=goal_data["description"],
        user=user,
    )


def create_goal_pinecone(
    goal_id: int, is_recurring: 0, goal_description: str, user: str
):
    """
    Adds the goal to pinecone

    goal_id: django id for the goal
    goal_type:
    """

    # Retrieve embedding from description via cohere
    co = cohere.Client(COHERE_API_KEY)
    embeds = co.embed(
        texts=[goal_description], model=COHERE_EMBED_MODEL, truncate="LEFT"
    ).embeddings

    # Open up pinecone connection (temp)
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    index = pinecone.Index(PINECONE_INDEX)

    # Set metadata
    metadata = {
        "user": user,
        "is_recurring": is_recurring,
    }
    vector_item = (goal_id, embeds[0], metadata)

    # Add goal to pinecone
    index.upsert(vectors=[vector_item])

    print(">>> Successfully added goal to Pinecone")

    return True
