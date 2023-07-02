# Generated by Django 4.2.2 on 2023-07-01 22:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("django_celery_beat", "0018_improve_crontab_helptext"),
        ("milestone_monitor", "0003_remove_recurringgoal_reminder_time_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Goal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100)),
                ("description", models.TextField(default="No description provided.")),
                (
                    "importance",
                    models.IntegerField(
                        choices=[(1, "Low"), (2, "Medium"), (3, "High")]
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed", models.BooleanField(default=False)),
                ("end_at", models.DateTimeField(null=True)),
                ("reminders_enabled", models.BooleanField(default=False)),
                ("reminder_start_time", models.DateTimeField(null=True)),
                (
                    "reminder_frequency",
                    models.IntegerField(
                        choices=[
                            (0, "Hourly"),
                            (1, "Daily"),
                            (2, "Weekly"),
                            (3, "Biweekly"),
                            (4, "Monthly"),
                            (99, "Minutely"),
                        ],
                        null=True,
                    ),
                ),
                ("final_task_enabled", models.BooleanField(default=False)),
                ("final_task_id", models.CharField(max_length=100, null=True)),
                (
                    "reminder_task",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="django_celery_beat.periodictask",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="milestone_monitor.user",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="recurringgoal",
            name="task",
        ),
        migrations.RemoveField(
            model_name="recurringgoal",
            name="user",
        ),
        migrations.DeleteModel(
            name="OneTimeGoal",
        ),
        migrations.DeleteModel(
            name="RecurringGoal",
        ),
    ]