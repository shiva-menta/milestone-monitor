from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# from pgvector.django import VectorField

class User(models.Model):
    """
    Represents all user personal information.
    """
    name = models.CharField(max_length=100)
    phone_number = models.IntegerField(
        editable=False,
        validators=[MinValueValidator(10000000000), MaxValueValidator(19999999999)]
    )

    def __str__(self):
        return f"{self.name} – {self.phone_number}"

class RecurringGoal(models.Model):
    """
    Represents all users' recurring goals (habits) they're trying to accomplish.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    end_at = models.DateTimeField(blank=True, null=True)
    reminder_time = models.TimeField()
    completed = models.BooleanField(default=False)
    # embedding = VectorField(dimensions=384)

    class Frequency(models.IntegerChoices):
        HOURLY = 0
        DAILY = 1
        WEEKLY = 2
        BIWEEKLY = 3
        MONTLY = 4

    frequency = models.IntegerField(choices=Frequency.choices)

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


