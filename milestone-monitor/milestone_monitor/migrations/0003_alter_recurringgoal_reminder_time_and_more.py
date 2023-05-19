# Generated by Django 4.2 on 2023-04-09 05:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("milestone_monitor", "0002_recurringgoal_task_alter_recurringgoal_frequency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recurringgoal",
            name="reminder_time",
            field=models.TimeField(blank=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone_number",
            field=models.BigIntegerField(
                editable=False,
                validators=[
                    django.core.validators.MinValueValidator(10000000000),
                    django.core.validators.MaxValueValidator(19999999999),
                ],
            ),
        ),
    ]
