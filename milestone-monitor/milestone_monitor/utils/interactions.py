import os
import pytz
from django.conf import settings
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.utils.dateparse import parse_datetime, parse_time

import cohere
import pinecone

from milestone_monitor.models import User, RecurringGoal, OneTimeGoal
from .constants import str_to_frequency, str_to_importance
from datetime import datetime, timedelta

COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENV = os.environ.get("PINECONE_ENV")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX")
COHERE_EMBED_MODEL = "embed-english-light-v2.0"

def get_and_create_user(phone_number: str):
    user = None
    try:
        user = User.objects.get(phone_number)
    except:
        user = User(phone_number=phone_number)
        user.save()

    return user

def create_goal(goal_data: dict, phone_number: str):
    """
    Creates a goal based on input data for a specific user.

    NEED TIMEZONE FEATURE

    goal_data: – can we move this somewhere else potentially – looks kind of messy right here
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
    # Step 1: get current user
    parsed_user_number = int(phone_number[1:])
    user = get_and_create_user(parsed_user_number)
    # Step 2: format common necessary data for goal
    # Assume that the naive datetime is in a certain timezone (e.g., New York)
    # ny_tz = pytz.timezone("America/New_York")
    # aware_dt = ny_tz.localize(naive_dt)
    # utc_dt = aware_dt.astimezone(pytz.UTC)

    title = goal_data["name"]
    importance = str_to_importance.get(
        goal_data["estimatedImportance"], RecurringGoal.Importance.LOW
    )
    # Step 3: actually create goal
    g = None
    if goal_data["isRecurring"]:
        g = RecurringGoal(
            user=user,
            title=title,
            importance=importance,
            frequency=str_to_frequency.get(
                goal_data["reminderFrequency"], RecurringGoal.Frequency.DAILY
            ),
            end_at=goal_data["dueDate"],
            reminder_start_time=goal_data.get("reminderTime", datetime.now() + timedelta(minuutes=5)),
        )
    else:
        g = OneTimeGoal(
            user=user,
            title=title,
            importance=importance,
            end_at=goal_data["dueDate"],
        )
    g.save()
    return g

    # print(">>> Successfully added goal to the postgres database!")

    # create_goal_pinecone(
    #     goal_id=goal_data["name"], goal_description=goal_data["description"], user=user
    # )

def modify_goal(goal_type: int, goal_id: int, data=dict):
    """
    Modifies current goal based on a dict of information. Models' modify functions
    check against its attribute keys. Functions can handle almost any combination of
    inputs, allowing for flexible modify queries.
    """
    goal_instance = None
    if goal_type:
        goal_instance = RecurringGoal.objects.get(id=goal_id)
    else:
        goal_instance = OneTimeGoal.objects.get(id=goal_id)
    goal_instance.modify(data)


def create_goal_pinecone(goal_id: str, goal_description: str, user: str):
    """
    Adds the goal to pinecone
    """

    # Retrieve embedding from description via cohere
    co = cohere.Client(COHERE_API_KEY)
    embeds = co.embed(
        texts=[goal_description], model=COHERE_EMBED_MODEL, truncate="LEFT"
    ).embeddings

    # Open up pinecone connection (temp)
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    index = pinecone.Index(PINECONE_INDEX)

    # Set user as metadata
    metadata = {"user": user}
    vector_item = (goal_id, embeds[0], metadata)

    # Add goal to pinecone
    index.upsert(vectors=[vector_item])

    print(">>> Successfully added goal to Pinecone")

    return True
