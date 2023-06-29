from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from django_celery_beat.models import IntervalSchedule, PeriodicTask
from backend.celery import app

import json
from milestone_monitor.tasks import send_onetime_reminder_message
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
    BI_MINUTELY = 99

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
    )

    # Model Functions
    def __str__(self):
        return f"{self.name} – {self.phone_number}"


# TODO: CONSIDER IF WE NEED A SPECIAL END MESSAGE FOR FINAL RECURRING MESSAGE – something like do you want to continue, etc.
class RecurringGoal(models.Model):
    """
    Represents all users' recurring goals (habits) they're trying to accomplish.
    """
    # Model Attributes
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    importance = models.IntegerField(choices=Importance.choices)
    frequency = models.IntegerField(choices=Frequency.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    end_at = models.DateTimeField(default=None, null=True)
    reminder_start_time = models.DateTimeField()
    is_running = models.BooleanField(default=True)
    completed = models.BooleanField(default=False)
    task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

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
            return IntervalSchedule.objects.get_or_create(every=2, period="minutes")

        raise NotImplementedError(
            """Interval Schedule for {interval} is not added.""".format(
                interval=self.time_interval.value
            )
        )

    # Model Functions
    # TODO: schedule one time task for end of recurring?
    def add_task(self):
        interval_schedule, _ = self.interval_schedule
        task_kwargs = {
            'name': self.title,
            'task': "send_recurring_reminder_message",
            'interval': interval_schedule,
            'args': json.dumps([self.user.phone_number, self.title]),
            'start_time': self.reminder_start_time,
        }
        if self.end_at is not None:
            task_kwargs['expires'] = self.end_at
        self.task = PeriodicTask.objects.create(**task_kwargs)
        self.save()

    def delete(self, *args, **kwargs):
        if self.task is not None:
            self.task.delete()

        return super(self.__class__, self).delete(*args, **kwargs)

    @transaction.atomic
    def modify(self, data):
        delete_curr_task = False
        issue_new_task = False  # issuing new task implies deleting current, but not vice versa

        if 'reminder_start_time' in data and 'end_at' in data:
            if (data['end_at'] - data['reminder_start_time']).total_seconds() < 3600:
                raise Exception("Invalid start and end times")

        if 'title' in data:
            if len(data['title']) <= 100 and data['title'] != self.title:
                issue_new_task = True
                self.title = data['title']
            else:
                raise Exception("Invalid title given.")
            
        if 'importance' in data:
            if data['importance'] in Importance.values and data['importance'] != self.importance:
                self.importance = data['importance']
            else:
                raise Exception("Invalid importance value.")
        
        if 'frequency' in data:
            if data['frequency'] in Frequency.values and data['frequency'] != self.frequency:
                issue_new_task = True
                self.frequency = data['frequency']
            else:
                raise Exception("Invalid frequency value.")
            
        if 'end_at' in data:
            if (data['end_at'] - datetime.now()).total_seconds() > 60:
                issue_new_task = True
                self.end_at = data['end_at']
            else:
                raise Exception("Invalid date given.")
        
        if 'reminder_start_time' in data:
            if (data['reminder_start_time'] - datetime.now()).total_seconds() > 0:
                issue_new_task = True
                self.end_at = data['end_at']
            else:
                raise Exception("Invalid start time given.")

        if 'is_running' in data:
            if data['is_running'] and not self.is_running:
                issue_new_task = True
                self.is_running = not self.is_running
            elif not data['is_running'] and self.is_running:
                issue_new_task = False
                delete_curr_task = True
                self.is_running = not self.is_running

        if 'completed' in data:
            if not data['completed']:
                raise Exception("Cannot make previous goal incomplete. Set a new goal instead.")
            if self.is_running:
                issue_new_task = False
                delete_curr_task = True
            self.completed = True
            self.task = None

        if issue_new_task:
            self.delete_task()
            self.add_task()
        elif delete_curr_task:
            self.delete_task()

        self.save()


class OneTimeGoal(models.Model):
    """
    Represents all users' one time goals (tasks) they're trying to accomplish.
    """
    # Model Attributes
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    importance = models.IntegerField(choices=Importance.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    end_at = models.DateTimeField()
    completed = models.BooleanField(default=False)
    task_id = models.CharField(max_length=100, null=True)

    # Model Functions
    def __str__(self):
        return f"{self.title} – {self.end_at}"

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
            if len(data['title']) <= 100 and data['title'] != self.title:
                issue_new_task = True
                self.title = data['title']
            else:
                raise Exception("Invalid title given.")
            
        if 'importance' in data:
            if data['importance'] in Importance.values:
                self.importance = data['importance']
            else:
                raise Exception("Invalid importance value.")

        if 'end_at' in data:
            if (data['end_at'] - datetime.now()).total_seconds() > 60:
                issue_new_task = True
                self.end_at = data['end_at']
            else:
                raise Exception("Invalid date given.")

        if 'completed' in data:
            if not data['completed']:
                raise Exception("Cannot make previous goal incomplete. Set a new goal instead.")
            if not self.completed and (datetime.now() - self.end_at) < 0:
                issue_new_task = False
                self.delete_task()
            self.completed = True
            self.task_id = None

        if issue_new_task:
            self.delete_task()
            self.add_task()

        self.save()
