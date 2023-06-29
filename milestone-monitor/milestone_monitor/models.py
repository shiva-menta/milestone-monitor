from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from django_celery_beat.models import IntervalSchedule, PeriodicTask
from backend.celery import app

import json
from milestone_monitor.tasks import send_onetime_reminder_message
from datetime import datetime


class User(models.Model):
    """
    Represents all user personal information.
    """

    name = models.CharField(max_length=100)
    phone_number = models.BigIntegerField(
        editable=False,
        validators=[
            MinValueValidator(1_000_000_0000),  # e.g. +1 234 567 8901
            MaxValueValidator(1_999_999_9999),
        ],
    )

    def __str__(self):
        return f"{self.name} – {self.phone_number}"

# TODO: clean up any unnecessary features, add custom modify function (what form should I assume this comes in)
class RecurringGoal(models.Model):
    """
    Represents all users' recurring goals (habits) they're trying to accomplish.
    """

    class Frequency(models.IntegerChoices):
        HOURLY = 0
        DAILY = 1
        WEEKLY = 2
        BIWEEKLY = 3
        MONTHLY = 4

        MINUTELY = 99  # for debugging purposes

    class Importance(models.IntegerChoices):
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    end_at = models.DateTimeField(blank=True, null=True)
    reminder_time = models.TimeField(null=True)
    completed = models.BooleanField(default=False)
    # embedding = VectorField(dimensions=384)
    frequency = models.IntegerField(choices=Frequency.choices)
    importance = models.IntegerField(choices=Importance.choices)
    task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    

    def delete(self, *args, **kwargs):
        if self.task is not None:
            self.task.delete()

        return super(self.__class__, self).delete(*args, **kwargs)

    def setup_task(self):
        interval_schedule, created = self.interval_schedule
        self.task = PeriodicTask.objects.create(
            name=self.title,
            task="send_recurring_reminder_message",
            interval=interval_schedule,
            args=json.dumps([self.user.phone_number, self.title]),
            start_time=self.created_at,
        )
        self.save()

    @property
    def interval_schedule(self):
        if self.frequency == 0:
            return IntervalSchedule.objects.get_or_create(every=1, period="hours")
        if self.frequency == 1:
            return IntervalSchedule.objects.get_or_create(every=1, period="days")
        if self.frequency == 2:
            return IntervalSchedule.objects.get_or_create(every=7, period="days")
        if self.frequency == 3:
            return IntervalSchedule.objects.get_or_create(every=14, period="days")
        if self.frequency == 4:
            return IntervalSchedule.objects.get_or_create(every=30, period="days")
        if self.frequency == 99:
            return IntervalSchedule.objects.get_or_create(every=1, period="minutes")

        raise NotImplementedError(
            """Interval Schedule for {interval} is not added.""".format(
                interval=self.time_interval.value
            )
        )

class OneTimeGoal(models.Model):
    """
    Represents all users' one time goals (tasks) they're trying to accomplish.
    """
    # Model Attributes
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    end_at = models.DateTimeField()
    completed = models.BooleanField(default=False)
    task_id = models.CharField(max_length=100, null=True)

    # Model Functions
    def add_task(self):
        task = send_onetime_reminder_message.apply_async(args=[self.user.phone_number, self.title], eta=self.end_at)
        self.task_id = task.id
        self.save()
    
    def delete_task(self):
        if self.task_id:
            try:
                app.control.revoke(self.task_id)
            except:
                print('Task has previously been deleted.')
    
    @transaction.atomic
    def modify(self, data):
        issue_new_task = False

        if 'title' in data:
            issue_new_task = True
            if len(data['title']) <= 100:
                self.title = data['title']
            else:
                raise Exception("Invalid title given.")

        if 'end_at' in data:
            issue_new_task = True
            if (data['end_at'] - self.end_at).total_seconds() > 60:
                self.end_at = data['end_at']
            else:
                raise Exception("Invalid date given.")

        if 'completed' in data:
            if not data['completed']:
                raise Exception("Cannot make previous goal incomplete. Set a new goal instead.")
            if (datetime.now() - self.end_at) < 0:
                issue_new_task = False
                self.delete_task()
            self.completed = True
            self.task_id = None

        if issue_new_task:
            self.delete_task()
            self.add_task()

        self.updated_at = datetime.now()
        self.save()
