from django.apps import AppConfig


class MilestoneMonitorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "milestone_monitor"

    def ready(self):
        import milestone_monitor.signals