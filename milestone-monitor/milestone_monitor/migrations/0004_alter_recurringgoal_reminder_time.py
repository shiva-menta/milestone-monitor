# Generated by Django 4.2 on 2023-04-09 06:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("milestone_monitor", "0003_alter_recurringgoal_reminder_time_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recurringgoal",
            name="reminder_time",
            field=models.TimeField(null=True),
        ),
    ]