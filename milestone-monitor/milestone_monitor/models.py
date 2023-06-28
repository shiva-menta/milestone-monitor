from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# from pgvector.django import VectorField
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from backend.celery import app
from datetime import datetime

import json
from milestone_monitor.tasks import send_onetime_reminder_message


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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    end_at = models.DateTimeField()
    completed = models.BooleanField(default=False)
    # embedding = VectorField(dimensions=384)
    task_id = models.CharField(max_length=100, null=True)

    def delete(self):
        if self.task_id:
            app.control.revoke(self.task_id)

    def setup_task(self):
        print('>>> Line hit')
        print(type(self.end_at), datetime.now())
        task = send_onetime_reminder_message.apply_async(args=[self.user.phone_number, self.title], eta=self.end_at)
        print(task)
        self.task_id = task.id
        self.save()