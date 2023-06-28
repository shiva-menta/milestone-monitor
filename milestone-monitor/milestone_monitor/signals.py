from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RecurringGoal, OneTimeGoal

@receiver(post_save, sender=RecurringGoal)
def create_or_update_periodic_task(sender, instance, created, **kwargs):
    if created:
        instance.setup_task()
    else:
        if instance.task is not None:
            instance.task.enabled = not instance.completed
            instance.task.save()

@receiver(post_save, sender=OneTimeGoal)
def create_or_update_periodic_task(sender, instance, created, **kwargs):
    if created:
        instance.setup_task()