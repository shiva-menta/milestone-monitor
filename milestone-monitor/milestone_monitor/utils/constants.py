from milestone_monitor.models import Frequency, Importance

str_to_frequency = {
    "HOURLY": Frequency.HOURLY,
    "DAILY": Frequency.DAILY,
    "WEEKLY": Frequency.WEEKLY,
    "BIWEEKLY": Frequency.BIWEEKLY,
    "MONTHLY": Frequency.MONTHLY,
    "MINUTELY": Frequency.MINUTELY,
}

str_to_importance = {
    "LOW": Importance.LOW,
    "MEDIUM": Importance.MEDIUM,
    "HIGH": Importance.HIGH,
}

frequency_to_str = {v: k for k, v in str_to_frequency.items()}
importance_to_str = {v: k for k, v in str_to_importance.items()}
