from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from django_celery_beat.models import IntervalSchedule, PeriodicTask
from backend.celery import app

import json
from milestone_monitor.tasks import send_final_task_message
from datetime import datetime


# Attribute Custom Fields
class Importance(models.IntegerChoices):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(models.IntegerChoices):
    HOURLY = 0
    DAILY = 1
    WEEKLY = 2
    BIWEEKLY = 3
    MONTHLY = 4
    MINUTELY = 99


class User(models.Model):
    """
    Represents an individual user of MM.
    """

    # Model Attributes
    name = models.CharField(max_length=100, blank=True)
    phone_number = models.BigIntegerField(
        editable=False,
        validators=[
            MinValueValidator(1_000_000_0000),
            MaxValueValidator(1_999_999_9999),
        ],
        unique=True,
    )

    # Model Functions
    def __str__(self) -> str:
        return f"{self.name} – {self.phone_number}"


class Goal(models.Model):
    """
    Represents individual goal that user will set, with customizability for reminder frequency and end date.
    """

    # ----- Model Attributes -----
    # Mandatory
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(default="No description provided.")
    importance = models.IntegerField(choices=Importance.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    # Optional
    end_at = models.DateTimeField(null=True, default=None)
    reminders_enabled = models.BooleanField(default=False)
    reminder_start_time = models.DateTimeField(null=True, default=None)  # 1
    reminder_frequency = models.IntegerField(
        choices=Frequency.choices, null=True, default=None
    )
    reminder_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    final_task_enabled = models.BooleanField(default=False)
    final_task_id = models.CharField(max_length=100, null=True, default="")

    @property
    def interval_schedule(self):
        if self.reminder_frequency == 0:
            return IntervalSchedule.objects.get_or_create(every=1, period="hours")
        if self.reminder_frequency == 1:
            return IntervalSchedule.objects.get_or_create(every=1, period="days")
        if self.reminder_frequency == 2:
            return IntervalSchedule.objects.get_or_create(every=7, period="days")
        if self.reminder_frequency == 3:
            return IntervalSchedule.objects.get_or_create(every=14, period="days")
        if self.reminder_frequency == 4:
            return IntervalSchedule.objects.get_or_create(every=30, period="days")
        if self.reminder_frequency == 99:
            return IntervalSchedule.objects.get_or_create(every=2, period="minutes")

        raise NotImplementedError(
            """Interval Schedule for {interval} is not added.""".format(
                interval=self.reminder_frequency.value
            )
        )

    # ----- Model Functions -----
    def __str__(self) -> str:
        return f"{self.title} – {self.end_at}"

    def setup_reminder_messages(self) -> None:
        if (
            not self.reminders_enabled
            and self.reminder_start_time != None
            and self.reminder_frequency != None
        ):
            interval_schedule, _ = self.interval_schedule
            task_kwargs = {
                "name": self.id,
                "task": "send_periodic_reminder",
                "interval": interval_schedule,
                "args": json.dumps([self.user.phone_number, self.title]),
                "start_time": self.reminder_start_time,
            }
            if self.end_at is not None:
                task_kwargs["expires"] = self.end_at
            self.reminder_task = PeriodicTask.objects.create(**task_kwargs)
            self.reminders_enabled = True
            self.save()

    def setup_final_message(self) -> None:
        if not self.final_task_enabled and self.end_at:
            task = send_final_task_message.apply_async(
                args=[self.user.phone_number, self.title], eta=self.end_at
            )
            self.final_task_id = task.id
            self.final_task_enabled = True
            self.save()

    def cancel_reminder_messages(self) -> None:
        if self.reminders_enabled:
            self.reminders_enabled = False
            self.reminder_task.delete()
            self.reminder_task.save()
            self.reminder_task = None
            self.save()

    def cancel_final_message(self) -> None:
        if self.final_task_enabled:
            self.final_task_enabled = False
            app.control.revoke(self.final_task_id)
            self.final_task_id = None
            self.save()

    @transaction.atomic
    def modify(self, data) -> None:
        # Can't Modify Completed Goal
        if self.completed:
            return

        # Change Goal Object Without Affecting Reminders
        if "importance" in data:
            if data["importance"] in Importance.values:
                self.importance = data["importance"]
            else:
                raise Exception("Invalid importance value.")
        if "description" in data:
            self.description = data["description"]

        # Change Goal Object With Reminder-Relevant Data
        if "reminder_start_time" in data:
            if (data["reminder_start_time"] - datetime.now()).total_seconds() > 0:
                self.reminder_start_time = data["reminder_start_time"]
                if self.reminders_enabled:
                    self.reminder_task.start_time = self.reminder_start_time
                    self.reminder_task.save()
            else:
                raise Exception("Invalid start time given.")
        if "reminder_frequency" in data:
            if (
                data["reminder_frequency"] in Frequency.values
                and data["reminder_frequency"] != self.reminder_frequency
            ):
                self.reminder_frequency = data["reminder_frequency"]
                if self.reminders_enabled:
                    interval_schedule, _ = self.interval_schedule
                    self.reminder_task.interval = interval_schedule
        if "end_at" in data:
            if (data["end_at"] - datetime.now()).total_seconds() > 300:
                self.end_at = data["end_at"]
                if self.reminders_enabled:
                    self.reminder_task.expires = self.end_at
                    self.reminder_task.save()
                if self.final_task_enabled:
                    app.control.revoke(self.final_task_id)
                    task = send_final_task_message.apply_async(
                        args=[self.user.phone_number, self.title], eta=self.end_at
                    )
                    self.final_task_id = task.id
            else:
                raise Exception("Invalid date given.")
        self.save()

        if (
            "reminders_enabled" in data
            and data["reminders_enabled"] != self.reminders_enabled
        ):
            if not data["reminders_enabled"]:
                self.cancel_reminder_messages()
            else:
                self.setup_reminder_messages()
        if (
            "final_task_enabled" in data
            and data["final_task_enabled"] != self.final_task_enabled
        ):
            if not data["final_task_enabled"]:
                self.cancel_final_message()
            else:
                self.setup_final_message()
        if "completed" in data:
            if not data["completed"]:
                raise Exception(
                    "Cannot make previous goal incomplete. Set a new goal instead."
                )
            self.completed = True
            self.end_at = datetime.now()
            self.cancel_reminder_messages()
            self.cancel_final_message()
