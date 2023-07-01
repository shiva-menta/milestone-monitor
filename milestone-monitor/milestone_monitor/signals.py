from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Goal

@receiver(post_save, sender=Goal)
def create_or_update_goal(sender, instance, created, **kwargs):
    if created:
        instance.setup_reminder_messages()
        instance.setup_final_message()