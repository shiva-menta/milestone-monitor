from milestone_monitor.models import User, RecurringGoal, OneTimeGoal

str_to_frequency = {
  "HOURLY": RecurringGoal.Frequency.HOURLY,
  "DAILY": RecurringGoal.Frequency.DAILY,
  "WEEKLY": RecurringGoal.Frequency.WEEKLY,
  "BIWEEKLY": RecurringGoal.Frequency.BIWEEKLY,
  "MONTHLY": RecurringGoal.Frequency.MONTHLY,
  "MINUTELY": RecurringGoal.Frequency.MINUTELY,
}

str_to_importance = {
  "LOW": RecurringGoal.Importance.LOW,
  "MEDIUM": RecurringGoal.Importance.MEDIUM,
  "HIGH": RecurringGoal.Importance.HIGH,
}